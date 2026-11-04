"""Build offline aircraft page data and its isolated player-only viewer.

Usage: python tools/build_aircraft_1194.py AIRCRAFT.docx [--preview-dir DIR]
The JSON owns bilingual prose and ordered module slots; the read-only DOCX
supplies verified image bytes. Document instructions and links are not run.
Event-shaped source files live under tools/page_sources, outside engine paths.
"""

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile

from PIL import Image, ImageFont

from build_tank_1194 import event, fit, font_path, option, stack_crops
from build_infantry_1194 import menu_card, note_card


RETIRED_IDS = {300, 301, 302, 303, 600, 601, 602, 603, 604,
               6012, 6013, 6042, 6043, 6044, 6045}
PREFIX = 'MMG_air1194_'


def retire_legacy(root):
    """Remove only old aircraft/air-doctrine definitions; preserve naval pages."""
    for filename in ('MMG_guide_pages.mmg', 'MMG_design_gallery_pages.mmg'):
        path = root / 'tools/page_sources' / filename
        old = path.read_text(encoding='utf-8')
        text = old
        for match in reversed(list(re.finditer(r'^country_event\s*=\s*\{.*?^\}', old, re.M | re.S))):
            ident = int(re.search(r'^\s*id\s*=\s*MMG_guide\.(\d+)', match[0], re.M)[1])
            if ident in RETIRED_IDS:
                text = text[:match.start()] + text[match.end():]
        text = re.sub(r'# ---------------------------------------------------------------------------\n# (?:AIR DOCTRINES|PLANE DESIGN):[^\n]*\n# ---------------------------------------------------------------------------\n',
                      '# Air doctrine and aircraft designs are owned by MMG_aircraft_1194_pages.mmg.\n', text)
        if filename == 'MMG_design_gallery_pages.mmg':
            text = re.sub(r'(add_namespace = MMG_guide)\n+', r'\1\n\n', text, count=1)
        if text != old:
            path.write_text(text, encoding='utf-8', newline='\n')
    for filename in ('MMG_eventpictures.gfx', 'MMG_design_gallery.gfx'):
        path = root / 'interface' / filename
        old = path.read_text(encoding='utf-8')
        text = re.sub(r'^\tSpriteType\s*=\s*\{\n\t\tname\s*=\s*"GFX_MMG_(?:air|plane)_[^"]*".*?^\t}\n', '', old, flags=re.M | re.S)
        if text != old:
            path.write_text(text, encoding='utf-8', newline='\n')
    for language in ('simp_chinese', 'english'):
        for stem in ('MMG_guide', 'MMG_design_gallery'):
            path = root / f'localisation/{language}/{stem}_l_{language}.yml'
            old = path.read_text(encoding='utf-8-sig')
            text = ''.join(line for line in old.splitlines(keepends=True)
                           if not re.match(r' MMG_(?:air|plane)_', line)
                           and not (re.match(r' MMG_gallery_(\d+)_', line)
                                    and int(re.match(r' MMG_gallery_(\d+)_', line)[1]) in RETIRED_IDS))
            if text != old:
                path.write_text(text, encoding='utf-8-sig', newline='\n')
    for pattern in ('mmg_air_*.dds', 'mmg_plane_*.dds'):
        for path in (root / 'gfx/event_pictures').glob(pattern):
            path.unlink()


def module_list(slots, modules, code):
    """Count module groups, without confusing a four-gun module with one gun."""
    counted = Counter(key for key in slots if key)
    parts = []
    for key, count in counted.items():
        label = modules[key][code]
        parts.append(label if count == 1 else
                     (f'{count}组{label}' if code == 'zh' else f'{count} x [{label}]'))
    return ('、' if code == 'zh' else ', ').join(parts)


def description(item, modules, code):
    weapons = module_list(item['weapons'], modules, code)
    engine = modules[item['engine']][code]
    special = module_list(item['special'], modules, code)
    if code == 'zh':
        config = f'{weapons}；{engine}' + (f'；{special}' if special else '') + '。'
        stats = f'图示航程{item["range"]}km；重量{item["weight"]}；推力{item["thrust"]}；造价{item["cost"]}。'
    else:
        config = f'{weapons}; {engine}' + (f'; {special}' if special else '') + '.'
        stats = f'Range {item["range"]} km; weight {item["weight"]}; thrust {item["thrust"]}; cost {item["cost"]}.'
    return '\n'.join((config, item[f'note_{code}'], stats))


def build(root, docx, preview_dir=None):
    content = json.loads((root / 'tools/aircraft_1194_content.json').read_text(encoding='utf-8'))
    if root.name != content['canonical_target']:
        raise ValueError('This workflow updates MengXin_Armaments_Guide only.')
    if hashlib.sha256(docx.read_bytes()).hexdigest() != content['source_sha256']:
        raise ValueError('Review changed Word image ordering and prose before rebuilding.')
    designs = {item['id']: item for item in content['designs']}
    assert sorted(designs) == list(range(1, 37))
    assert sorted(n for group in content['groups'] for n in group['designs']) == sorted(designs)
    originals = {}
    with ZipFile(docx) as archive:
        expected = {item['source_member'] for item in designs.values()}
        actual = {name for name in archive.namelist() if name.startswith('word/media/')}
        assert actual == expected and len(actual) == 36
        for item in designs.values():
            raw = archive.read(item['source_member'])
            assert hashlib.sha256(raw).hexdigest() == item['source_sha256'], item['source_member']
            originals[item['id']] = Image.open(io.BytesIO(raw)).convert('RGBA')
    # Complete source validation precedes removal of the retired chapter.
    retire_legacy(root)
    fonts = {n: ImageFont.truetype(font_path(), n) for n in (14, 15, 16, 20, 21, 26)}
    texts = {'simp_chinese': {}, 'english': {}}
    events, pictures, records = [], {}, []

    def localize(key, zh, en):
        texts['simp_chinese'][key] = zh
        texts['english'][key] = en

    def add(ident, name, zh, en, dz, de, asset, choices):
        key = PREFIX + name
        localize(key + '_t', zh, en)
        localize(key + '_d', dz, de)
        events.append(event(ident, key, 'GFX_MMG_aircraft1194_' + asset, choices))
        records.append({'event': ident, 'picture': asset, 'key': key})

    common = {
        'close': ('了解了', 'Understood'),
        'index': ('返回飞机总目录', 'Back to Aircraft Index'),
        'group': ('返回本组目录', 'Back to Airframe Group'),
        'rules': ('任务、配件与科技说明', 'Missions, Modules and Research'),
        'rules_back': ('返回说明目录', 'Back to Reference Menu'),
        'air': ('返回空军学说', 'Back to Air Doctrine'),
        'prev': ('上一设计', 'Previous Design'), 'next': ('下一设计', 'Next Design'),
        'menu_prev': ('上一页目录', 'Previous Menu Page'),
        'menu_next': ('下一页目录', 'Next Menu Page'),
        'full': ('返回完整设计', 'Back to Full Design'),
        'modules': ('放大查看武器与配件', 'Enlarge Weapons and Modules'),
        'stats': ('放大查看属性与造价', 'Enlarge Stats and Cost'),
    }
    for name, pair in common.items():
        localize(PREFIX + name, *pair)
    localize('MMG_plane_design_decision', '飞机设计 · 1.19.4', 'Aircraft Designs: 1.19.4')
    localize('MMG_plane_design_decision_desc', '查看36套飞机完整设计、武器配件与属性造价，按机身年代分组。',
             'Browse 36 aircraft designs by airframe generation, with complete weapon, module and stat views.')
    localize('MMG_air_doctrine_decision', '空军学说 · 1.19.4', 'Air Doctrine: 1.19.4')
    localize('MMG_air_doctrine_decision_desc', '按制空、CAS、重战和战略轰炸任务选择学说，并核对效率与设计分类。',
             'Choose doctrines for air superiority, CAS, heavy fighters or strategic bombing; review efficiency and design roles.')
    opt = lambda name, target=None: option(PREFIX + name, target)

    pictures['index'] = menu_card('飞机设计 · 1.19.4', '36 complete designs / 108 design views',
        [(g['zh'] + f' · {len(g["designs"])}套', g['en']) for g in content['groups']], fonts)
    choices = []
    for group in content['groups']:
        localize(PREFIX + f'group_{group["id"]}', group['zh'], group['en'])
        choices.append(opt(f'group_{group["id"]}', f'MMG_aircraft.{group["id"]}'))
    choices += [opt('rules', 'MMG_aircraft.1'), opt('air', 'MMG_guide.300'), opt('close')]
    add('MMG_guide.600', 'index', '飞机设计 · 1.19.4', 'Aircraft Designs: 1.19.4',
        '按机身年代选择36套方案。每套可看完整设计、武器配件放大与属性造价放大。年份指机身，配件仍需对应研究；数值随任务、国家和学说变化。',
        'Choose 36 designs by airframe generation. Each has full, module and stat/cost views. Airframe year does not unlock every module; research, missions, doctrines and national bonuses affect results.',
        'index', choices)

    notes = content['notes']
    pictures['rules'] = menu_card('任务、配件与科技说明', 'Missions, Modules and Research',
        [(n['zh'], n['en']) for n in notes], fonts)
    choices = []
    for note in notes:
        name = f'note_{note["id"]}'
        localize(PREFIX + name + '_label', note['zh'], note['en'])
        choices.append(opt(name + '_label', f'MMG_aircraft.{note["id"]}'))
        pictures[name] = note_card(note['zh'], note['en'], note['desc_zh'], note['desc_en'], fonts)
        add(f'MMG_aircraft.{note["id"]}', name, note['zh'], note['en'], note['desc_zh'], note['desc_en'], name,
            [opt('rules_back', 'MMG_aircraft.1'), opt('index', 'MMG_guide.600'), opt('close')])
    choices += [opt('index', 'MMG_guide.600'), opt('close')]
    add('MMG_aircraft.1', 'rules', '任务、配件与科技说明', 'Missions, Modules and Research',
        '先确认武器模块数量、机型分类、任务效果和科技条件，再比较造价与性能。',
        'Check module counts, design roles, mission effects and research requirements before comparing performance and cost.', 'rules', choices)

    for item in content['doctrines']:
        ident = item['id']
        name = f'doctrine_{ident}'
        pictures[name] = note_card(item['zh'], item['en'], item['desc_zh'], item['desc_en'], fonts)
        choices = []
        if ident == 300:
            for child in content['doctrines'][1:]:
                key = f'doctrine_{child["id"]}_label'
                localize(PREFIX + key, child['zh'], child['en'])
                choices.append(opt(key, f'MMG_guide.{child["id"]}'))
        else:
            choices.append(opt('air', 'MMG_guide.300'))
        choices += [opt('index', 'MMG_guide.600'), opt('rules', 'MMG_aircraft.1'), opt('close')]
        add(f'MMG_guide.{ident}', name, item['zh'], item['en'], item['desc_zh'], item['desc_en'], name, choices)

    for group in content['groups']:
        ids = group['designs']
        pages = [ids[n:n+4] for n in range(0, len(ids), 4)]
        for i, page in enumerate(pages):
            ident = group['id'] + i
            name = f'menu_{ident}'
            choices = []
            for n in page:
                key = f'design_{n:02}_label'
                localize(PREFIX + key, designs[n]['zh'], designs[n]['en'])
                choices.append(opt(key, f'MMG_aircraft.{100+n}'))
            if i:
                choices.append(opt('menu_prev', f'MMG_aircraft.{ident-1}'))
            if i + 1 < len(pages):
                choices.append(opt('menu_next', f'MMG_aircraft.{ident+1}'))
            choices += [opt('index', 'MMG_guide.600'), opt('close')]
            pictures[name] = menu_card(group['zh'], f'{group["en"]} / {i+1} of {len(pages)}',
                                      [(designs[n]['zh'], designs[n]['en']) for n in page], fonts)
            add(f'MMG_aircraft.{ident}', name, f'{group["zh"]}（{i+1}/{len(pages)}）',
                f'{group["en"]} ({i+1}/{len(pages)})',
                '选择一套设计，可连续查看本组方案。配件页放大武器、引擎与特殊模块；属性页保留原始数据和生产造价。',
                'Select a design and browse this airframe group. Module views enlarge weapons, engines and special modules; stat views preserve the original values and production cost.', name, choices)
        for i, n in enumerate(ids):
            item = designs[n]
            source = originals[n]
            pictures[f'design_{n:02}_full'] = fit(source)
            # Two original slot strips, with no icons or numeric stats redrawn.
            pictures[f'design_{n:02}_modules'] = stack_crops(source, [(0, .26, .49, .36), (0, .82, .49, .925)])
            pictures[f'design_{n:02}_stats'] = stack_crops(source, [(.49, .08, .995, .435), (.49, .928, .995, .999)])
            menu = group['id'] + i // 4
            for offset, view, sz, se in ((100, 'full', '', ''), (200, 'modules', ' · 武器与配件', ' / Modules'),
                                          (300, 'stats', ' · 属性与造价', ' / Stats and Cost')):
                name = f'design_{n:02}_{view}'
                choices = []
                if view == 'full':
                    choices += [opt('modules', f'MMG_aircraft.{200+n}'), opt('stats', f'MMG_aircraft.{300+n}')]
                    if i:
                        choices.append(opt('prev', f'MMG_aircraft.{100+ids[i-1]}'))
                    if i + 1 < len(ids):
                        choices.append(opt('next', f'MMG_aircraft.{100+ids[i+1]}'))
                else:
                    choices.append(opt('full', f'MMG_aircraft.{100+n}'))
                    other = 'stats' if view == 'modules' else 'modules'
                    choices.append(opt(other, f'MMG_aircraft.{(300 if other == "stats" else 200)+n}'))
                choices += [opt('group', f'MMG_aircraft.{menu}'), opt('index', 'MMG_guide.600'), opt('close')]
                add(f'MMG_aircraft.{offset+n}', name, item['zh'] + f'（{i+1}/{len(ids)}）' + sz,
                    item['en'] + f' ({i+1}/{len(ids)})' + se, description(item, content['modules'], 'zh'),
                    description(item, content['modules'], 'en'), name, choices)

    assert len(events) == len(pictures) == 130
    header = ('# OFFLINE guide page data; tools/build_viewer.py compiles the player UI.\n'
              '# Stable decision entry points: MMG_guide.300 and MMG_guide.600.\n'
              'add_namespace = MMG_guide\nadd_namespace = MMG_aircraft\n\n')
    (root / 'tools/page_sources/MMG_aircraft_1194_pages.mmg').write_text(header + ''.join(events), encoding='utf-8', newline='\n')
    gfx = ['# Reviewed Word aircraft pictures and bilingual reference cards.\nspriteTypes = {\n']
    for name, picture in pictures.items():
        path = f'gfx/event_pictures/mmg_aircraft_1194_{name}.dds'
        picture.save(root / path)
        gfx.append('\tSpriteType = {\n' + f'\t\tname = "GFX_MMG_aircraft1194_{name}"\n'
                   + f'\t\ttexturefile = "{path}"\n' + '\t}\n')
        if preview_dir:
            preview_dir.mkdir(parents=True, exist_ok=True)
            picture.save(preview_dir / f'{name}.png')
    (root / 'interface/MMG_aircraft_1194.gfx').write_text(''.join(gfx) + '}\n', encoding='utf-8', newline='\n')
    for language, entries in texts.items():
        lines = [f'l_{language}:\n']
        for key, value in entries.items():
            value = value.replace('"', "'").replace('\n', r'\n')
            lines.append(f' {key}: "{value}"\n')
        (root / f'localisation/{language}/MMG_aircraft_1194_l_{language}.yml').write_text(''.join(lines), encoding='utf-8-sig', newline='\n')
    manifest = {'source_name': content['source_name'], 'source_sha256': content['source_sha256'],
                'designs': 36, 'events': len(events), 'textures': len(pictures), 'objects': records,
                'design_sources': [{'id': n, 'member': item['source_member'], 'sha256': item['source_sha256'],
                                    'full': f'MMG_aircraft.{100+n}', 'modules': f'MMG_aircraft.{200+n}',
                                    'stats': f'MMG_aircraft.{300+n}'} for n, item in designs.items()]}
    (root / 'tools/aircraft_1194_source_map.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    # The legacy event shape is source data only; player UI owns navigation.
    from guide_model import compile_viewer
    compile_viewer(root)
    print(f'{root.name}: 36 aircraft designs, 108 design views, {len(events)} air source pages, {len(pictures)} textures; Chinese/English.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('docx', type=Path)
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    build(Path(__file__).resolve().parents[1], args.docx, args.preview_dir)


if __name__ == '__main__':
    main()
