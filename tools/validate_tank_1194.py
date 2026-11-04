"""Check tank navigation, source coverage, text bounds and GFX/localisation links.

These are offline checks. They do not certify engine rendering or mouse input.
Usage: python tools/validate_tank_1194.py [--root MOD_ROOT]
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image, ImageFont


def wrap(text, font, width):
    result = []
    for paragraph in text.replace(r'\n', '\n').split('\n'):
        line = ''
        for char in paragraph:
            if line and font.getlength(line + char) > width:
                result.append(line)
                line = ''
            line += char
        result.append(line)
    return result


def validate(root):
    content = json.loads((root / 'tools/tank_1194_content.json').read_text(encoding='utf-8'))
    designs = {d['image']: d for d in content['designs']}
    menu_count = sum((len(g['images']) + 3) // 4 for g in content['groups'])
    expected_events = len(designs) * 3 + menu_count + 3
    expected_textures = len(designs) * 3 + menu_count + 1
    events, sources = {}, {}
    errors = []
    for path in sorted((root / 'tools/page_sources').glob('*.mmg')):
        text = path.read_text(encoding='utf-8')
        namespaces = set(re.findall(r'^add_namespace\s*=\s*(\w+)', text, re.M))
        for match in re.finditer(r'^country_event\s*=\s*\{.*?^\}', text, re.M | re.S):
            block = match[0]
            event_id = re.search(r'^\s*id\s*=\s*(\w+\.\d+)\b', block, re.M)[1]
            if event_id in events:
                errors.append(f'Duplicate event: {event_id}')
            if event_id.split('.')[0] not in namespaces:
                errors.append(f'Unregistered namespace: {path.name}: {event_id}')
            events[event_id] = block
            sources[event_id] = path.name

    tank = {key: value for key, value in events.items() if key.startswith('MMG_tank.') or key == 'MMG_guide.500'}
    if len(tank) != expected_events:
        errors.append(f'Expected {expected_events} tank source pages, got {len(tank)}')
    legacy = [key for key in events if re.fullmatch(r'MMG_guide\.50[1-7](?:[23])?', key)]
    if legacy:
        errors.append(f'Old tank source pages remain: {legacy}')
    links = {key: re.findall(r'country_event\s*=\s*\{\s*id\s*=\s*(\w+\.\d+)', block) for key, block in events.items()}
    for key, targets in links.items():
        for target in targets:
            if target not in events:
                errors.append(f'Missing target: {key} -> {target}')
    visited, pending = set(), ['MMG_guide.500']
    while pending:
        key = pending.pop()
        if key in visited:
            continue
        visited.add(key)
        pending.extend(links.get(key, []))
    if set(tank) != visited:
        errors.append(f'Unreachable or escaping tank source pages: {sorted(set(tank) ^ visited)}')

    sprites = {}
    for path in (root / 'interface').glob('*.gfx'):
        text = path.read_text(encoding='utf-8')
        for name, texture in re.findall(r'name\s*=\s*"(GFX_MMG_[^"]+)"\s*\n\s*texturefile\s*=\s*"([^"]+)"', text):
            if name in sprites:
                errors.append(f'Duplicate sprite: {name}')
            sprites[name] = texture
    for key, block in events.items():
        name = re.search(r'^\s*picture\s*=\s*(GFX_MMG_\w+)', block, re.M)
        if not name:
            continue
        if name[1] not in sprites:
            errors.append(f'Missing sprite: {key}: {name[1]}')
        elif not (root / sprites[name[1]]).is_file():
            errors.append(f'Missing texture: {key}: {sprites[name[1]]}')
    new_textures = list((root / 'gfx/event_pictures').glob('mmg_tank_1194_*.dds'))
    if len(new_textures) != expected_textures:
        errors.append(f'Expected {expected_textures} tank textures, got {len(new_textures)}')
    for path in new_textures:
        with Image.open(path) as im:
            if im.size != (720, 450) or im.mode != 'RGBA':
                errors.append(f'Wrong texture format: {path.name}: {im.size}, {im.mode}')
            im.load()
    old_textures = [p.name for p in (root / 'gfx/event_pictures').glob('mmg_tank_*.dds') if not p.name.startswith('mmg_tank_1194_')]
    if old_textures:
        errors.append(f'Legacy tank textures: {old_textures}')

    manifest = json.loads((root / 'tools/tank_1194_source_map.json').read_text(encoding='utf-8'))
    if sorted(s['image'] for s in manifest['sources']) != sorted(designs):
        errors.append('Source image coverage does not match the stable design IDs')
    if len(set(s['sha256'] for s in manifest['sources'])) != len(designs):
        errors.append('A source image was duplicated or omitted')
    for source in manifest['sources']:
        design = designs[source['image']]
        if source['source_member'] != design['source_member'] or source['sha256'] != design['source_image_sha256']:
            errors.append(f'Word source mapping changed: design {source["image"]}')
        full, modules, stats, menu = (source[k] for k in ('full_event', 'modules_event', 'stats_event', 'menu'))
        if modules not in links.get(full, []) or stats not in links.get(full, []) or menu not in links.get(full, []):
            errors.append(f'Broken design entry: {full}')
        for detail in (modules, stats):
            if full not in links.get(detail, []) or menu not in links.get(detail, []):
                errors.append(f'Broken enlargement return: {detail}')

    # The existing GUI is intentionally reused: native-size 720x450 artwork,
    # 20px gap, eight 352x56 slots. Conservative Windows font approximations.
    cjk = Path('C:/Windows/Fonts/msyh.ttc')
    if not cjk.exists():
        cjk = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    fonts = {size: ImageFont.truetype(str(cjk), size) for size in (18, 22)}
    layout = []
    for language_dir in sorted((root / 'localisation').iterdir()):
        if not language_dir.is_dir():
            continue
        loc = {}
        for path in language_dir.glob('*.yml'):
            if not path.read_bytes().startswith(b'\xef\xbb\xbf'):
                errors.append(f'Missing localisation BOM: {path.name}')
            text = path.read_text(encoding='utf-8-sig')
            for key, value in re.findall(r'^ (\w+): "(.*)"$', text, re.M):
                if key in loc:
                    errors.append(f'Duplicate {language_dir.name} key: {key}')
                loc[key] = value
        required = {'MMG_tank_design_decision', 'MMG_tank_design_decision_desc'}
        for block in events.values():
            required.update(re.findall(r'^\s*(?:title|desc|name)\s*=\s*(MMG_\w+)', block, re.M))
        for key in sorted(required - set(loc)):
            errors.append(f'Missing {language_dir.name} key: {key}')
        for key, block in tank.items():
            title_key = re.search(r'^\s*title\s*=\s*(\w+)', block, re.M)[1]
            desc_key = re.search(r'^\s*desc\s*=\s*(\w+)', block, re.M)[1]
            option_keys = re.findall(r'^\s*name\s*=\s*(\w+)', block, re.M)
            if len(option_keys) > 8:
                errors.append(f'Too many options: {key}: {len(option_keys)}')
            title_width = fonts[22].getlength(loc.get(title_key, ''))
            desc_lines = wrap(loc.get(desc_key, ''), fonts[18], 1080)
            option_lines = [len(wrap(loc.get(k, ''), fonts[18], 332)) for k in option_keys]
            if title_width > 1050 or len(desc_lines) * 20 > 100 or max(option_lines, default=0) > 2:
                errors.append(f'Text overflow: {language_dir.name} {key}: title={title_width:.0f}, desc_lines={len(desc_lines)}, option_lines={option_lines}')
            layout.append({'language': language_dir.name, 'event': key, 'title_width': round(title_width, 1),
                'description_lines': len(desc_lines), 'options': len(option_keys), 'max_option_lines': max(option_lines, default=0)})
    for error in errors:
        print('ERROR:', error)
    print(f'{root.name}: {len(events)} total source pages; {len(tank)} tank source pages; {len(designs)} source panels; {len(new_textures)} tank RGBA textures; {len(layout)} localized layouts; {len(errors)} errors.')
    return {'root': root.name, 'total_events': len(events), 'tank_events': len(tank),
        'tank_textures': len(new_textures), 'localized_layouts': len(layout), 'errors': errors, 'layout': layout}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(bool(result['errors']))


if __name__ == '__main__':
    main()
