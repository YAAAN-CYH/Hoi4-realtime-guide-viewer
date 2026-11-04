"""Check aircraft source/module coverage, navigation, resources and text bounds.

Usage: python tools/validate_aircraft_1194.py [--game-root DIR] [--report FILE]
These are offline checks, not engine rendering, combat or mouse-input tests.
"""

import argparse
import json
from pathlib import Path
import re

from PIL import Image, ImageFont

from build_aircraft_1194 import PREFIX, RETIRED_IDS
from build_infantry_1194 import card_wrap
from build_tank_1194 import font_path


def validate(root, game_root=None):
    content = json.loads((root / 'tools/aircraft_1194_content.json').read_text(encoding='utf-8'))
    manifest = json.loads((root / 'tools/aircraft_1194_source_map.json').read_text(encoding='utf-8'))
    errors, events = [], {}
    for path in (root / 'tools/page_sources').glob('*.mmg'):
        text = path.read_text(encoding='utf-8')
        namespaces = set(re.findall(r'^add_namespace\s*=\s*(\w+)', text, re.M))
        for block in re.findall(r'^country_event\s*=\s*\{.*?^\}', text, re.M | re.S):
            ident = re.search(r'^\s*id\s*=\s*(\w+\.\d+)', block, re.M)[1]
            if ident in events:
                errors.append('Duplicate event: ' + ident)
            if ident.split('.')[0] not in namespaces:
                errors.append('Unregistered namespace: ' + ident)
            events[ident] = block
    roots = {'MMG_guide.600'} | {f'MMG_guide.{n}' for n in range(300, 304)}
    owned = {k: v for k, v in events.items() if k.startswith('MMG_aircraft.') or k in roots}
    if len(owned) != 130 or manifest['events'] != 130:
        errors.append(f'Expected 130 air source pages, got {len(owned)}')
    for n in RETIRED_IDS - {300, 301, 302, 303, 600}:
        if f'MMG_guide.{n}' in events:
            errors.append('Retired aircraft event remains: ' + str(n))
    links = {k: re.findall(r'country_event\s*=\s*\{\s*id\s*=\s*(\w+\.\d+)', v) for k, v in events.items()}
    for ident, targets in links.items():
        for target in targets:
            if target not in events:
                errors.append(f'Missing event: {ident} -> {target}')
    seen, pending = set(), ['MMG_guide.600']
    while pending:
        ident = pending.pop()
        if ident in seen:
            continue
        seen.add(ident)
        pending.extend(links.get(ident, []))
    if seen != set(owned):
        errors.append('Unreachable/escaping air source pages: ' + str(sorted(seen ^ set(owned))))
    for group in content['groups']:
        ids = group['designs']
        for i, n in enumerate(ids):
            full, modules, stats = (f'MMG_aircraft.{offset+n}' for offset in (100, 200, 300))
            menu = f'MMG_aircraft.{group["id"] + i // 4}'
            for ident in (full, modules, stats):
                required = {menu, 'MMG_guide.600'} | ({modules, stats} if ident == full else {full})
                if not required <= set(links.get(ident, [])):
                    errors.append('Broken aircraft navigation: ' + ident)
            for j in (i-1, i+1):
                if 0 <= j < len(ids) and f'MMG_aircraft.{100+ids[j]}' not in links.get(full, []):
                    errors.append('Broken adjacent design link: ' + full)

    designs = content['designs']
    if sorted(t['id'] for t in designs) != list(range(1, 37)):
        errors.append('Expected 36 unique aircraft designs')
    if len(set(t['source_member'] for t in designs)) != 36:
        errors.append('Missing or duplicate original Word panel')
    for source, item in zip(manifest['design_sources'], designs):
        if (source['id'], source['member'], source['sha256']) != (item['id'], item['source_member'], item['source_sha256']):
            errors.append('Incorrect Word panel mapping: ' + str(item['id']))
    used_modules = set()
    for item in designs:
        modules = item['weapons'] + [item['engine']] + item['special']
        used_modules.update(k for k in modules if k)
        if not item['weapons'] or not item['engine'] or len(item['weapons']) > 5 or len(item['special']) > 6:
            errors.append('Incomplete module slots: ' + str(item['id']))
        if not item['note_zh'] or not item['note_en'] or item['weight'] > item['thrust']:
            errors.append('Missing prose or overweight reference: ' + str(item['id']))
        for key in modules:
            if key and (key not in content['modules'] or not all(content['modules'][key].get(c) for c in ('zh', 'en'))):
                errors.append('Untranslated or unknown module: ' + str(key))
    if used_modules != set(content['modules']):
        errors.append('Module glossary does not match the aircraft roster')
    if game_root:
        source = (game_root / 'common/units/equipment/modules/00_plane_modules.txt').read_text(encoding='utf-8-sig')
        definitions = set(re.findall(r'^\t(\w+)\s*=\s*\{', source, re.M))
        if used_modules - definitions:
            errors.append('Modules absent from installed game: ' + str(sorted(used_modules - definitions)))

    gfx = (root / 'interface/MMG_aircraft_1194.gfx').read_text(encoding='utf-8')
    sprites = dict(re.findall(r'name\s*=\s*"([^"]+)"\s*\n\s*texturefile\s*=\s*"([^"]+)"', gfx))
    used_sprites = set()
    for ident, block in owned.items():
        sprite = re.search(r'^\s*picture\s*=\s*(\w+)', block, re.M)[1]
        used_sprites.add(sprite)
        if sprite not in sprites or not (root / sprites[sprite]).is_file():
            errors.append('Missing air sprite/texture: ' + ident)
    if used_sprites != set(sprites):
        errors.append('Unused or missing air sprite definition')
    textures = list((root / 'gfx/event_pictures').glob('mmg_aircraft_1194_*.dds'))
    if len(textures) != 130 or manifest['textures'] != 130:
        errors.append('Expected 130 air textures')
    for path in textures:
        with Image.open(path) as im:
            if im.size != (720, 450) or im.mode != 'RGBA':
                errors.append('Incorrect air DDS format: ' + path.name)
            im.load()
    for pattern in ('mmg_air_*.dds', 'mmg_plane_*.dds'):
        if list((root / 'gfx/event_pictures').glob(pattern)):
            errors.append('Retired textures remain: ' + pattern)

    fonts = {n: ImageFont.truetype(font_path(), n) for n in (18, 22)}
    layouts, language_keys = [], {}
    for language in ('simp_chinese', 'english'):
        loc = {}
        for path in (root / 'localisation' / language).glob('*.yml'):
            raw = path.read_bytes()
            if not raw.startswith(b'\xef\xbb\xbf'):
                errors.append('Missing localisation BOM: ' + path.name)
            for k, v in re.findall(r'^ (\w+): "(.*)"$', raw.decode('utf-8-sig'), re.M):
                if k in loc:
                    errors.append('Duplicate key: ' + language + ' ' + k)
                if language == 'english' and k.startswith(PREFIX) and re.search(r'[\u3400-\u9fff]', v):
                    errors.append('Untranslated English text: ' + k)
                loc[k] = v
        language_keys[language] = set(loc)
        required = {f'MMG_{stem}_decision{suffix}' for stem in ('plane_design', 'air_doctrine') for suffix in ('', '_desc')}
        for ident, block in owned.items():
            required.update(re.findall(r'^\s*(?:title|desc|name)\s*=\s*(MMG_\w+)', block, re.M))
            title = re.search(r'^\s*title\s*=\s*(\w+)', block, re.M)[1]
            desc = re.search(r'^\s*desc\s*=\s*(\w+)', block, re.M)[1]
            choices = re.findall(r'^\s*name\s*=\s*(\w+)', block, re.M)
            lines = len(card_wrap(loc.get(desc, '').replace(r'\n', '\n'), fonts[18], 1080))
            title_width = fonts[22].getlength(loc.get(title, ''))
            opt_lines = max((len(card_wrap(loc.get(k, ''), fonts[18], 332)) for k in choices), default=0)
            if lines > 5 or title_width > 1050 or len(choices) > 8 or opt_lines > 2:
                errors.append(f'Air text overflow: {language} {ident}: lines={lines}, title={title_width:.0f}, options={len(choices)}, option_lines={opt_lines}')
            layouts.append({'event': ident, 'language': language, 'description_lines': lines,
                            'title_width': round(title_width, 1), 'choices': len(choices), 'max_option_lines': opt_lines})
        if required - set(loc):
            errors.append('Missing ' + language + ' keys: ' + str(sorted(required - set(loc))))
    if language_keys['english'] != language_keys['simp_chinese']:
        errors.append('Global Chinese/English key sets differ')
    for error in errors:
        print('ERROR:', error)
    print(f'{root.name}: {len(events)} total source pages, {len(owned)} air source pages, 36 designs, {len(used_modules)} modules, {len(textures)} air textures, {len(layouts)} layouts; {len(errors)} errors.')
    return {'total_events': len(events), 'air_events': len(owned), 'designs': 36, 'module_types': len(used_modules),
            'textures': len(textures), 'layouts': layouts, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = validate(Path(__file__).resolve().parents[1], args.game_root)
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(bool(result['errors']))


if __name__ == '__main__':
    main()
