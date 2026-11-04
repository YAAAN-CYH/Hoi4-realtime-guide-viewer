"""Prove the viewer's static isolation contract and simulate every UI transition.

Usage: python tools/validate_viewer_isolation.py --game-root GAME [--report FILE]
Only two private UI variables may change, solely from player button callbacks.
This is a source/resource check; it cannot establish engine or supply outcomes.
"""

import argparse
import json
from pathlib import Path
import re

from PIL import Image, ImageFont

from build_infantry_1194 import card_wrap
from build_tank_1194 import font_path
from guide_model import load_pages, parse, read_localisation


PRIVATE = {'MMG_UI_page', 'MMG_UI_choices'}
ALLOWED_COMMON = {'common/scripted_guis/MMG_viewer.txt', 'common/scripted_localisation/MMG_viewer.txt'}


def run(root, game_root):
    errors = []
    pages = load_pages(root)
    by_id = {p['id']: p for p in pages}
    manifest = json.loads((root / 'tools/viewer_source_map.json').read_text(encoding='utf-8'))
    if manifest['pages'] != pages or set(manifest['private_variables']) != PRIVATE:
        errors.append('Viewer manifest is stale')
    loaded_common = {p.relative_to(root).as_posix() for p in (root / 'common').rglob('*') if p.is_file()}
    if loaded_common != ALLOWED_COMMON:
        errors.append('Unexpected engine common files: ' + str(sorted(loaded_common ^ ALLOWED_COMMON)))
    for folder in ('events', 'history', 'map'):
        if any(p.is_file() for p in (root / folder).rglob('*')):
            errors.append('Unexpected gameplay files under ' + folder)
    if re.search(r'\breplace_path\s*=', (root / 'descriptor.mod').read_text(encoding='utf-8')):
        errors.append('replace_path is not permitted')
    overrides = []
    for path in root.rglob('*'):
        if path.is_file() and '.git' not in path.parts and path.name != 'descriptor.mod':
            rel = path.relative_to(root)
            if (game_root / rel).is_file():
                overrides.append(rel.as_posix())
    if overrides:
        errors.append('Vanilla file overrides: ' + str(overrides))

    gui_path = root / 'interface/MMG_viewer.gui'
    gui = gui_path.read_text(encoding='utf-8')
    gui_names = set(re.findall(r'\bname\s*=\s*"([^"]+)"', gui))
    if not all(name.startswith('MMG_UI_') for name in gui_names):
        errors.append('Viewer defines non-private GUI elements')
    all_gui = list((root / 'interface').glob('*.gui'))
    if all_gui != [gui_path]:
        errors.append('Unexpected GUI files: ' + str([p.name for p in all_gui]))
    sg_text = (root / 'common/scripted_guis/MMG_viewer.txt').read_text(encoding='utf-8')
    top = parse(sg_text)
    if len(top) != 1 or top[0][0] != 'scripted_gui':
        raise ValueError('Unexpected scripted GUI root')
    panels = dict(top[0][1])
    expected_panels = {'MMG_UI_launcher': 'MMG_UI_Launcher', 'MMG_UI_viewer': 'MMG_UI_Viewer'}
    if set(panels) != set(expected_panels):
        errors.append('Missing or unexpected scripted GUI panels')
    # A resource/callback match alone does not establish a visible entry point.
    # Bind both windows explicitly to the documented, full-screen in-game layer;
    # do not add a vanilla topbar override to create that attachment.
    mounts = {}
    callbacks = {}
    for name, fields in panels.items():
        panel = dict(fields)
        permitted = {'context_type', 'window_name', 'visible', 'ai_enabled',
                     'effects', 'dirty', 'properties', 'triggers', 'parent_window_token'}
        if len(panel) != len(fields) or set(panel) - permitted:
            errors.append('Unexpected scripted GUI fields: ' + name)
        if panel.get('context_type') != 'player_context' or panel.get('ai_enabled') != [('always', 'no')]:
            errors.append('Non-player/AI-enabled UI context: ' + name)
        if ('is_ai', 'no') not in panel.get('visible', []):
            errors.append('Missing player visibility guard: ' + name)
        if panel.get('window_name') not in gui_names:
            errors.append('Missing GUI container: ' + name)
        if panel.get('window_name') != expected_panels.get(name):
            errors.append('Wrong GUI container binding: ' + name)
        mounts[name] = panel.get('parent_window_token')
        if mounts[name] != 'top_bar':
            errors.append('Missing explicit in-game topbar mount: ' + name)
        if name == 'MMG_UI_viewer':
            if panel.get('dirty') != 'MMG_UI_page' or ('has_variable', 'MMG_UI_page') not in panel['visible']:
                errors.append('Viewer is not gated/dirty-updated by its own page')
        callbacks.update(dict(panel.get('effects', [])))
        for key, condition in panel.get('triggers', []):
            if not key.endswith('_visible') or key[:-8] not in gui_names:
                errors.append('Unbound UI visibility trigger: ' + key)
            if len(condition) != 1 or condition[0][0] != 'check_variable':
                raise ValueError('Unexpected UI visibility expression')
            pred = dict(condition[0][1])
            if pred.get('var') != 'MMG_UI_choices' or pred.get('compare') != 'greater_than_or_equals':
                raise ValueError('Visibility must read only the private choice count')
    expected = {'MMG_UI_Open_click', 'MMG_UI_Home_click', 'MMG_UI_Close_click'} | {f'MMG_UI_Option_{i}_click' for i in range(1, 9)}
    if set(callbacks) != expected:
        errors.append('Unexpected button effects: ' + str(set(callbacks) ^ expected))

    def effect_audit(items):
        for key, value in items:
            if key == 'set_variable':
                if len(value) != 1 or value[0][0] not in PRIVATE or not str(value[0][1]).isdigit():
                    raise ValueError('Non-private or non-literal variable write')
            elif key == 'clear_variable':
                if value not in PRIVATE:
                    raise ValueError('Non-private variable clear')
            elif key in ('if', 'else_if'):
                if not value or value[0][0] != 'limit':
                    raise ValueError('Unexpected callback branch')
                test = value[0][1]
                if len(test) != 1 or test[0][0] != 'check_variable':
                    raise ValueError('Unexpected callback predicate')
                pred = dict(test[0][1])
                if pred.get('var') != 'MMG_UI_page' or pred.get('compare') != 'equals':
                    raise ValueError('Callback reads gameplay state')
                effect_audit(value[1:])
            else:
                raise ValueError('Disallowed GUI effect: ' + key)

    for effects in callbacks.values():
        effect_audit(effects)

    def matches(condition, state):
        if not condition:
            return True
        pred = dict(condition[0][1])
        return state.get(pred['var']) == int(pred['value'])

    def execute(items, state):
        handled = False
        for key, value in items:
            if key == 'set_variable':
                for var, num in value:
                    state[var] = int(num)
            elif key == 'clear_variable':
                state.pop(value, None)
            elif key in ('if', 'else_if') and not handled and matches(value[0][1], state):
                execute(value[1:], state)
                handled = True
        return state

    transitions = 0
    for page in pages:
        initial = {'MMG_UI_page': page['number'], 'MMG_UI_choices': len(page['choices'])}
        for i in range(1, 9):
            result = execute(callbacks[f'MMG_UI_Option_{i}_click'], initial.copy())
            if len(page['choices']) < i:
                expected_state = initial
            else:
                target = page['choices'][i-1]['target']
                expected_state = ({'MMG_UI_page': by_id[target]['number'], 'MMG_UI_choices': len(by_id[target]['choices'])}
                                  if target else {})
            if result != expected_state:
                errors.append(f'Wrong button transition: {page["id"]} option {i}')
            transitions += 1
        if execute(callbacks['MMG_UI_Close_click'], initial.copy()):
            errors.append('Close leaves private state behind: ' + page['id'])
        if execute(callbacks['MMG_UI_Home_click'], initial.copy()) != {'MMG_UI_page': 1, 'MMG_UI_choices': 8}:
            errors.append('Home link is broken: ' + page['id'])
        transitions += 2
    if execute(callbacks['MMG_UI_Open_click'], {}) != {'MMG_UI_page': 1, 'MMG_UI_choices': 8}:
        errors.append('Launcher does not initialize the UI')

    selectors = {}
    for kind, fields in parse((root / 'common/scripted_localisation/MMG_viewer.txt').read_text(encoding='utf-8')):
        if kind != 'defined_text':
            raise ValueError('Unsupported scripted localisation object')
        name = next(v for k, v in fields if k == 'name')
        if name in selectors or any(k not in {'name', 'text'} for k, _ in fields):
            raise ValueError('Duplicate/invalid scripted localisation selector')
        selectors[name] = [dict(v) for k, v in fields if k == 'text']
        for row in selectors[name]:
            if set(row) - {'trigger', 'localization_key'}:
                raise ValueError('Unexpected scripted text payload')
            if 'trigger' in row:
                condition = row['trigger']
                if len(condition) != 1 or condition[0][0] != 'check_variable':
                    raise ValueError('Unexpected scripted text predicate')
                pred = dict(condition[0][1])
                if pred.get('var') != 'MMG_UI_page' or pred.get('compare') != 'equals':
                    raise ValueError('Scripted text must only read the private page')
    if set(selectors) != {'MMG_UI_GetTitle', 'MMG_UI_GetDescription', 'MMG_UI_GetImage'} | {f'MMG_UI_GetOption{i}' for i in range(1, 9)}:
        errors.append('Missing or extra dynamic UI selectors')

    def resolve(name, state):
        for row in selectors[name]:
            if matches(row.get('trigger'), state):
                return row['localization_key']
        raise ValueError('Missing selector fallback: ' + name)

    gfx = '\n'.join(p.read_text(encoding='utf-8') for p in (root / 'interface').glob('*.gfx'))
    sprites = dict(re.findall(r'name\s*=\s*"([^"]+)"\s*\n\s*texturefile\s*=\s*"([^"]+)"', gfx))
    for page in pages:
        state = {'MMG_UI_page': page['number']}
        for suffix, field in (('Title', 'title'), ('Description', 'description'), ('Image', 'picture')):
            if resolve('MMG_UI_Get' + suffix, state) != page[field]:
                errors.append('Wrong dynamic ' + field + ': ' + page['id'])
        for i in range(1, 9):
            key = page['choices'][i-1]['label'] if i <= len(page['choices']) else 'MMG_UI_blank'
            if resolve(f'MMG_UI_GetOption{i}', state) != key:
                errors.append('Wrong dynamic option: ' + page['id'])
        if page['picture'] not in sprites or not (root / sprites[page['picture']]).is_file():
            errors.append('Missing viewer picture: ' + page['id'])
    if not all(key.startswith('GFX_MMG_') for key in sprites):
        errors.append('Vanilla sprite names are defined by the mod')

    fonts = {n: ImageFont.truetype(font_path(), n) for n in (18, 22)}
    key_sets, layouts = {}, []
    for language in ('simp_chinese', 'english'):
        loc = read_localisation(root, language)
        key_sets[language] = set(loc)
        if any(not k.startswith('MMG_') for k in loc):
            errors.append('Non-private localisation keys: ' + language)
        for path in (root / 'localisation' / language).glob('*.yml'):
            if not path.read_bytes().startswith(b'\xef\xbb\xbf'):
                errors.append('Missing BOM: ' + path.name)
        for page in pages:
            title, desc = loc[page['title']], loc[page['description']]
            width = fonts[22].getlength(title)
            lines = len(card_wrap(desc.replace(r'\n', '\n'), fonts[18], 1080))
            choices = max(len(card_wrap(loc[c['label']], fonts[18], 332)) for c in page['choices'])
            if width > 1050 or lines > 5 or choices > 2:
                errors.append('Text overflow: ' + language + ' ' + page['id'])
            layouts.append({'language': language, 'page': page['id'], 'description_lines': lines,
                            'title_width': round(width, 1), 'max_option_lines': choices})
    if key_sets['simp_chinese'] != key_sets['english']:
        errors.append('Chinese/English key mismatch')
    for name, size in [('gfx/interface/mmg_ui_option.dds', (1056, 50)),
                       ('gfx/interface/mmg_eventwindow_background.dds', (1140, 680)),
                       ('gfx/event_pictures/mmg_ui_home.dds', (720, 450))]:
        with Image.open(root / name) as im:
            if im.size != size or im.mode != 'RGBA':
                errors.append('Wrong UI asset format: ' + name)
            im.load()
    for error in errors:
        print('ERROR:', error)
    result = {'pages': len(pages), 'source_pages': len(pages)-1, 'transitions_simulated': transitions+1,
              'localized_layouts': len(layouts), 'localisation_keys_per_language': len(key_sets['english']),
              'private_variables': sorted(PRIVATE), 'vanilla_overrides': overrides,
              'parent_window_tokens': mounts,
              'runtime_events': 0, 'runtime_decisions': 0, 'errors': errors, 'layouts': layouts}
    print(f'{len(pages)} GUI pages, {transitions+1} UI transitions, {len(layouts)} localized layouts; '
          f'{len(overrides)} vanilla overrides; {len(errors)} errors.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = run(Path(__file__).resolve().parents[1], args.game_root)
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(bool(result['errors']))


if __name__ == '__main__':
    main()
