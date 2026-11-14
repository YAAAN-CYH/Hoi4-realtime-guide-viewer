"""Build the 1.19.4.1 naval designs from reviewed Word screenshots and text.

Usage: python tools/build_naval_11941.py SOURCE.docx [--preview-dir DIR]
The DOCX supplies image bytes. The content JSON owns all displayed text and
pins the document and image hashes. Generated .mmg pages are offline UI data.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageFont

from build_infantry_1194 import menu_card, note_card
from build_tank_1194 import event, fit, font_path, option, stack_crops
from guide_model import compile_viewer


INDEX = 'MMG_guide.700'
PREFIX = 'MMG_naval11941_'
SPRITE = 'GFX_MMG_naval11941_'
LANGUAGES = ('simp_chinese', 'english')
VIEWS = {'full': 100, 'modules': 200, 'stats': 300}
MODULE_CROPS = ((0, .075, .485, .145), (0, .255, .485, .36),
                (0, .818, .485, .925))
STAT_CROPS = ((.493, .075, .995, .628), (.575, .932, 1, 1))

LABELS = {
    'index': ('返回舰船总目录', 'Ship Design Index'),
    'group': ('返回本舰种目录', 'Back to Ship Class Menu'),
    'close': ('关闭', 'Close'),
    'prev': ('上一方案', 'Previous Design'),
    'next': ('下一方案', 'Next Design'),
    'menu_prev': ('上一页目录', 'Previous Menu Page'),
    'menu_next': ('下一页目录', 'Next Menu Page'),
    'full': ('返回完整设计', 'Return to Full Design'),
    'modules': ('放大查看模块', 'Enlarge Modules'),
    'stats': ('放大查看属性与造价', 'Enlarge Stats and Cost'),
    'aircraft': ('查看舰载机设计', 'Browse Carrier Aircraft'),
}


def read_screenshots(docx, content):
    if hashlib.sha256(docx.read_bytes()).hexdigest() != content['source_sha256']:
        raise ValueError('Review the changed Word source before rebuilding.')
    originals = {}
    with ZipFile(docx) as archive:
        members = {entry['source_member'] for entry in content['designs']}
        actual = {name for name in archive.namelist()
                  if name.startswith('word/media/') and name.endswith('.png')}
        if members != actual or len(members) != 46:
            raise ValueError('Expected exactly the 46 reviewed Word panels.')
        for entry in content['designs']:
            raw = archive.read(entry['source_member'])
            if hashlib.sha256(raw).hexdigest() != entry['source_sha256']:
                raise ValueError('Changed image: ' + entry['source_member'])
            with Image.open(io.BytesIO(raw)) as picture:
                originals[entry['id']] = picture.convert('RGBA')
    return originals


def build(root, docx, preview_dir=None):
    content = json.loads((root / 'tools/naval_11941_content.json').read_text(encoding='utf-8'))
    if root.name != 'MengXin_Armaments_Guide':
        raise ValueError('This builder targets MengXin_Armaments_Guide.')
    designs = {entry['id']: entry for entry in content['designs']}
    sequence = [ident for group in content['groups'] for ident in group['designs']]
    if sequence != list(range(1, 47)) or set(designs) != set(sequence):
        raise ValueError('The five ship class menus must cover all 46 designs in order.')
    originals = read_screenshots(docx, content)
    fonts = {size: ImageFont.truetype(font_path(), size) for size in (14, 15, 16, 20, 21, 26)}
    texts = {language: {} for language in LANGUAGES}
    pages, pictures = [], {}

    def localize(key, pair):
        for language, value in zip(LANGUAGES, pair):
            texts[language][key] = value

    def add(ident, name, title, description, picture, choices):
        localize(PREFIX + name + '_t', title)
        localize(PREFIX + name + '_d', description)
        pages.append(event(ident, PREFIX + name, SPRITE + name, choices))
        pictures[name] = picture

    def opt(label, target=None):
        return option(PREFIX + label, target)

    for label, pair in LABELS.items():
        localize(PREFIX + label, pair)
    title = ('舰船设计 · 1.19.4.1', 'Ship Designs: 1.19.4.1')
    localize('MMG_ship_design_decision', title)
    root_choices, root_items = [], []
    for group in content['groups']:
        label = f'group_{group["id"]}'
        localize(PREFIX + label, group['title'])
        root_choices.append(opt(label, f'MMG_naval.{group["id"]}'))
        root_items.append(group['title'])
    for note in content['notes']:
        name = f'note_{note["id"]}'
        localize(PREFIX + name, note['title'])
        root_choices.append(opt(name, f'MMG_naval.{note["id"]}'))
        choices = [opt('index', INDEX), opt('close')]
        if note['id'] == 2:
            choices.insert(0, opt('aircraft', 'MMG_guide.600'))
        add(f'MMG_naval.{note["id"]}', name, note['title'], note['description'],
            note_card(*note['title'], *note['description'], fonts), choices)
    add(INDEX, 'index', title, (
        '按舰种浏览46套不带制造商的设计。每套提供完整图、模块放大、属性与造价。解锁条件和实战数值随国家、科技及加成变化。',
        'Browse 46 designs without manufacturers. Each has a full panel, enlarged modules, and stats and cost. Check research, country and bonuses before building.',
    ), menu_card(*title, root_items, fonts), [*root_choices, opt('close')])

    for group in content['groups']:
        ids = group['designs']
        menus = [ids[n:n+4] for n in range(0, len(ids), 4)]
        for index, members in enumerate(menus):
            menu_id = group['id'] + index
            heading = tuple(f'{label} ({index+1}/{len(menus)})' for label in group['title'])
            choices = []
            for ident in members:
                label = f'design_{ident:02}'
                localize(PREFIX + label, designs[ident]['title'])
                choices.append(opt(label, f'MMG_naval.{VIEWS["full"]+ident}'))
            if index:
                choices.append(opt('menu_prev', f'MMG_naval.{menu_id-1}'))
            if index+1 < len(menus):
                choices.append(opt('menu_next', f'MMG_naval.{menu_id+1}'))
            add(f'MMG_naval.{menu_id}', f'menu_{menu_id}', heading, (
                '选择一套设计，或翻页查看本舰种的其他方案。',
                'Select a design or turn the page to browse this ship class.',
            ), menu_card(*heading, [designs[n]['title'] for n in members], fonts),
                [*choices, opt('index', INDEX), opt('close')])

        for index, ident in enumerate(ids):
            entry = designs[ident]
            panel = originals[ident]
            views = {'full': fit(panel), 'modules': stack_crops(panel, MODULE_CROPS),
                     'stats': stack_crops(panel, STAT_CROPS)}
            cost = entry['cost']
            description = (f'{entry["description"][0]} 图示生产造价{cost}。',
                           f'{entry["description"][1]} Shown production cost: {cost:,}.')
            for view, offset in VIEWS.items():
                view_title = entry['title']
                if view != 'full':
                    suffix = ('模块放大', 'Modules') if view == 'modules' else ('属性与造价', 'Stats and Cost')
                    view_title = [f'{label} / {detail}' for label, detail in zip(view_title, suffix)]
                choices = [opt(other, f'MMG_naval.{other_offset+ident}')
                           for other, other_offset in VIEWS.items() if other != view]
                if index:
                    choices.append(opt('prev', f'MMG_naval.{VIEWS["full"]+ids[index-1]}'))
                if index+1 < len(ids):
                    choices.append(opt('next', f'MMG_naval.{VIEWS["full"]+ids[index+1]}'))
                choices += [opt('group', f'MMG_naval.{group["id"]+index//4}'),
                            opt('index', INDEX), opt('close')]
                add(f'MMG_naval.{offset+ident}', f'{ident:02}_{view}', view_title,
                    description, views[view], choices)

    header = ('# Offline page data. The viewer compiler owns all in-game navigation.\n'
              'add_namespace = MMG_guide\nadd_namespace = MMG_naval\n\n')
    (root / 'tools/page_sources/MMG_naval_11941_pages.mmg').write_text(
        header + '\n'.join(pages), encoding='utf-8', newline='\n')
    sprites = ['# 1.19.4.1 ship designs and bilingual index cards.\nspriteTypes = {\n']
    if preview_dir:
        preview_dir.mkdir(parents=True, exist_ok=True)
    for name, picture in pictures.items():
        relative = f'gfx/event_pictures/mmg_naval11941_{name}.dds'
        picture.save(root / relative)
        sprites.append(f'\tSpriteType = {{\n\t\tname = "{SPRITE + name}"\n'
                       f'\t\ttexturefile = "{relative}"\n\t}}\n')
        if preview_dir:
            picture.save(preview_dir / f'{name}.png')
    (root / 'interface/MMG_naval_11941.gfx').write_text(
        ''.join(sprites) + '}\n', encoding='utf-8', newline='\n')
    for language, entries in texts.items():
        lines = [f'l_{language}:\n']
        for key, value in entries.items():
            value = value.replace('"', "'").replace('\n', r'\n')
            lines.append(f' {key}: "{value}"\n')
        (root / f'localisation/{language}/MMG_naval_11941_l_{language}.yml').write_text(
            ''.join(lines), encoding='utf-8-sig', newline='\n')
    compile_viewer(root)
    print(f'{len(designs)} ship designs, {len(pages)} naval design pages, {len(pictures)} textures.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('docx', type=Path)
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    build(Path(__file__).resolve().parents[1], args.docx, args.preview_dir)


if __name__ == '__main__':
    main()
