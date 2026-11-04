"""Build offline tank page data and the isolated player-only guide viewer.

Usage: python tools/build_tank_1194.py SOURCE.docx [--preview-dir DIR]
The JSON owns reviewed prose and stable design IDs. Explicit source members
and image hashes prevent Word media renumbering from changing existing designs.
No commands, macros, or authoring instructions in the document are executed.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageFont


SIZE = (720, 450)
TEXT = {
    'simp_chinese': {
        'index_t': '1.19.4 坦克设计 · 底盘目录',
        'index_d': '按底盘年代选择方案，每项可查看完整设计、模块放大和属性放大。数值来自全科技参考环境，实际属性会随已解锁科技、设计商及加成变化。无甲或0甲指不加装甲升级，并非装甲厚度为零。',
        'version_t': '1.19.4 · 版本与读图说明',
        'version_d': '炮兵与坦歼加成削弱，小加农炮的收益需重新比较；重机枪和轻机枪可用于补输出。自动装弹机另加2%软攻、2%对空，为百分比修正。\n全科技图例不等于该底盘解锁时即可完整照搬；后期武器、配件仍需对应科技。图中角色和数值优先，文字已据此校正。',
        'principles_t': '1.19.4 · 选型与投入',
        'principles_d': '作战中坦可优先比较不加装甲升级的成本；装甲优势必须结合敌方穿甲和整师属性判断。\n蹲坑与防守坦歼优先推土铲；各组末尾的高难防守坦歼在常规进攻中优先级低。\n先进轻坦方案暂缺；改进中坦0甲版、现代坦歼改型只有文字建议，不补造未提供的设计图或数值。',
        'version': '版本、科技与数值说明', 'principles': '选型思路与适用场景',
        'close': '了解了', 'index': '返回坦克总目录', 'group': '返回本底盘目录',
        'next': '下一方案', 'prev': '上一方案',
        'menu_next': '下一页目录', 'menu_prev': '上一页目录',
        'modules': '放大查看模块', 'stats': '放大查看属性与造价',
        'full': '返回完整设计', 'modules_suffix': ' · 模块放大',
        'stats_suffix': ' · 属性与造价',
        'group_d': '选择一项查看完整设计；可在设计页连续翻看本组全部方案，也可放大模块和属性。',
        'card_hint': '完整设计 / 模块放大 / 属性与造价',
        'card_version': '全科技参考 · 按当前科技核对配件',
        'card_principles': '按角色、敌方穿甲和生产投入选择',
    },
    'english': {
        'index_t': '1.19.4 Tank Designs: Chassis Index',
        'index_d': 'Choose a chassis generation, then inspect the full design, modules or stats. These are all-tech reference values; research, designers and bonuses change actual results. Armor 0 means no armor upgrades, not zero armor thickness.',
        'version_t': '1.19.4: Version and Technology Notes',
        'version_d': 'Artillery and TD bonuses were reduced. Reassess small cannons; heavy and light MGs can supplement attack. Autoloaders add 2% soft attack and 2% air attack, not flat attack values.\nAll-tech examples can use equipment unlocked much later than their chassis. Match modules to current research. Displayed roles and values take precedence; descriptions have been corrected accordingly.',
        'principles_t': '1.19.4: Roles and Production Priorities',
        'principles_d': 'Compare armor-0 combat mediums first when cost matters. Armor advantages depend on enemy piercing and division-level stats.\nPrioritize dozer blades for entrenched defensive TDs. Difficult-AI defensive TDs have low priority for normal offensives.\nAdvanced light designs are absent. The armor-0 improved TD and modern TD conversion have advice only, without invented panels or exact stats.',
        'version': 'Version, Research and Reference Values', 'principles': 'Roles and Production Priorities',
        'close': 'Understood', 'index': 'Tank Index', 'group': 'Chassis Menu',
        'next': 'Next Design', 'prev': 'Previous Design',
        'menu_next': 'Next Menu Page', 'menu_prev': 'Previous Menu Page',
        'modules': 'Enlarge Modules', 'stats': 'Enlarge Stats and Cost',
        'full': 'Return to Full Design', 'modules_suffix': ' / Modules',
        'stats_suffix': ' / Stats and Cost',
        'group_d': 'Select a full design. Design pages can browse every example in this chassis group, with separate module and stat enlargements.',
        'card_hint': 'Full design / Modules / Stats and cost',
        'card_version': 'All-tech reference: check your current research',
        'card_principles': 'Choose for role, enemy piercing and production cost',
    },
}


def event_blocks(text):
    # Only top-level country-event blocks; indented option braces are retained.
    return list(re.finditer(r'^country_event\s*=\s*\{.*?^\}', text, re.M | re.S))


def remove_legacy(root):
    """Remove old tank ownership only; preserve unrelated blocks byte for byte."""
    for path in sorted((root / 'tools/page_sources').glob('*.mmg')):
        if path.name == 'MMG_tank_1194_pages.mmg':
            continue
        old = path.read_text(encoding='utf-8')
        text = old
        for match in reversed(event_blocks(old)):
            token = re.search(r'^\s*id\s*=\s*MMG_guide\.(\d+)\b', match[0], re.M)
            if token and (500 <= int(token[1]) <= 507 or 5000 <= int(token[1]) < 5080):
                text = text[:match.start()] + text[match.end():]
        # Replace the obsolete tank section heading, never an adjacent chapter.
        text = re.sub(
            r'# ---------------------------------------------------------------------------\n# TANK DESIGN:.*?(?=# ---------------------------------------------------------------------------\n# (?:AIRCRAFT|PLANE))',
            '# Tank designs are owned by MMG_tank_1194_pages.mmg.\n\n',
            text, flags=re.S,
        )
        if text != old:
            path.write_text(text, encoding='utf-8', newline='\n')

    for path in sorted((root / 'interface').glob('*.gfx')):
        if path.name == 'MMG_tank_1194.gfx':
            continue
        old = path.read_text(encoding='utf-8')
        text = re.sub(
            r'^\tSpriteType\s*=\s*\{\n\t\tname\s*=\s*"GFX_MMG_tank_[^"]*".*?^\t}\n',
            '', old, flags=re.M | re.S,
        )
        if text != old:
            path.write_text(text, encoding='utf-8', newline='\n')

    for path in sorted((root / 'localisation').glob('*/*.yml')):
        if path.name.startswith('MMG_tank_1194_'):
            continue
        old = path.read_text(encoding='utf-8-sig')
        lines = []
        for line in old.splitlines(keepends=True):
            if re.match(r' MMG_tank_', line):
                continue
            if re.match(r' MMG_gallery_50\d', line):
                continue
            if re.match(r' MMG_tank_design_decision(?:_desc)?:', line):
                continue
            lines.append(line)
        text = ''.join(lines)
        if text != old:
            path.write_text(text, encoding='utf-8-sig', newline='\n')

    # Exact ownership patterns; no recursive deletion or broad source cleanup.
    for path in (root / 'gfx/event_pictures').glob('mmg_tank_*.dds'):
        if not path.name.startswith('mmg_tank_1194_'):
            path.unlink()
    obsolete_source = root / 'tools/sources/tank_medium.png'
    if obsolete_source.exists():
        obsolete_source.unlink()


def option(key, target=None):
    lines = ['\toption = {', f'\t\tname = {key}']
    if target:
        lines.append(f'\t\tcountry_event = {{ id = {target} }}')
    return '\n'.join([*lines, '\t}'])


def event(event_id, key, sprite, options):
    return '\n'.join([
        'country_event = {', f'\tid = {event_id}', f'\ttitle = {key}_t',
        f'\tdesc = {key}_d', f'\tpicture = {sprite}', '\tis_triggered_only = yes',
        '', *options, '}', '',
    ])


def fit(image):
    image = image.convert('RGBA')
    scale = min(SIZE[0] / image.width, SIZE[1] / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', SIZE, (0, 0, 0, 0))
    canvas.alpha_composite(image, ((SIZE[0] - image.width) // 2, (SIZE[1] - image.height) // 2))
    return canvas


def crop(image, bounds):
    return image.crop(tuple(round(v * (image.width if i % 2 == 0 else image.height)) for i, v in enumerate(bounds)))


def stack_crops(image, bounds):
    # Module slots and engine/armor controls, or stats and cost, remain separate
    # strips in reading order. Never stretch or redraw numbers from a reference.
    strips = [crop(image, b).convert('RGBA') for b in bounds]
    width = max(p.width for p in strips)
    canvas = Image.new('RGBA', (width, sum(p.height for p in strips) + 14 * (len(strips) - 1)), (0, 0, 0, 0))
    y = 0
    for strip in strips:
        canvas.alpha_composite(strip, ((width - strip.width) // 2, y))
        y += strip.height + 14
    return fit(canvas)


def font_path():
    # Menu artwork is bilingual; Windows and common Linux CJK installs work.
    candidates = [Path('C:/Windows/Fonts/msyh.ttc'), Path('C:/Windows/Fonts/simhei.ttf'),
                  Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')]
    found = next((p for p in candidates if p.exists()), None)
    if found is None:
        raise FileNotFoundError('A CJK font is required to render bilingual tank menus.')
    return str(found)


def card(title, subtitle, lines, cjk_font):
    canvas = Image.new('RGBA', SIZE, '#d7ceb5')
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((8, 8, 711, 441), 12, outline='#665c43', width=2)
    f_title = ImageFont.truetype(cjk_font, 28)
    f_sub = ImageFont.truetype(cjk_font, 16)
    f_body = ImageFont.truetype(cjk_font, 22)
    draw.text((28, 22), title, font=f_title, fill='#282b22')
    draw.text((28, 65), subtitle, font=f_sub, fill='#49493b')
    for i, (zh, en) in enumerate(lines):
        y = 110 + i * 62
        draw.text((30, y), zh, font=f_body, fill='#252a23')
        draw.text((30, y + 29), en, font=f_sub, fill='#49493b')
    return canvas


def build(root, docx, preview_dir=None):
    if root.name != 'MengXin_Armaments_Guide':
        raise ValueError('Only the canonical mod is maintained by this workflow.')
    content = json.loads((root / 'tools/tank_1194_content.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(docx.read_bytes()).hexdigest()
    if digest != content['source_sha256']:
        raise ValueError('The source DOCX changed. Review image ordering and prose before rebuilding.')
    groups = content['groups']
    # `image` is the stable design ID, not the current Word media filename.
    designs = {d['image']: d for d in content['designs']}
    assert len(designs) == len(content['designs'])
    assert sorted(designs) == list(range(1, len(designs) + 1))
    assert sorted(i for g in groups for i in g['images']) == sorted(designs)
    menu_count = sum((len(g['images']) + 3) // 4 for g in groups)
    event_count = len(designs) * 3 + menu_count + 3
    languages = [language for language in TEXT if (root / 'localisation' / language).is_dir()]
    remove_legacy(root)
    events = [
        '# OFFLINE tank page data; tools/build_viewer.py compiles the player UI.\n',
        '# Chapter source key: MMG_guide.500; never installed as engine events.\n',
        '# Legacy namespace declarations are retained only for the source format.\n',
        'add_namespace = MMG_guide\nadd_namespace = MMG_tank\n\n',
    ]
    loc = {language: {} for language in languages}
    pictures = {}
    source_map = []
    cjk_font = font_path()

    def register_text(key, fields):
        for language in languages:
            code = 'zh' if language == 'simp_chinese' else 'en'
            loc[language][key] = fields[code]

    for language in languages:
        for key, value in TEXT[language].items():
            loc[language]['MMG_tank1194_' + key] = value
        loc[language]['MMG_tank_design_decision'] = '坦克设计 · 1.19.4' if language == 'simp_chinese' else 'Tank Designs: 1.19.4'
        loc[language]['MMG_tank_design_decision_desc'] = (
            f'按战间期、基础、改进、先进、陆巡与现代底盘查看{len(designs)}张设计图，含喷火支援和叠甲防空。每项可放大模块、属性与造价；数值为全科技参考。'
            if language == 'simp_chinese' else
            f'Browse {len(designs)} design panels, including flame support and armored SPAA, with module and stat enlargements. Values are all-tech references.'
        )

    pictures['index'] = card('1.19.4 坦克设计', 'Tank Designs / Chassis Index',
        [(f'{g["zh"]} · {len(g["images"])}张设计图', f'{g["en"]} / {len(g["images"])} panels') for g in groups], cjk_font)
    root_options = [option('MMG_tank1194_version', 'MMG_tank.1'), option('MMG_tank1194_principles', 'MMG_tank.2')]
    for g in groups:
        register_text(f'MMG_tank1194_group_{g["key"]}', {'zh': g['zh'], 'en': g['en']})
        root_options.append(option(f'MMG_tank1194_group_{g["key"]}', f'MMG_tank.{g["menu"]}'))
    root_options.append(option('MMG_tank1194_close'))
    assert len(root_options) <= 8
    events.append(event('MMG_guide.500', 'MMG_tank1194_index', 'GFX_MMG_tank1194_index', root_options))
    for i, name in enumerate(('version', 'principles'), 1):
        events.append(event(f'MMG_tank.{i}', f'MMG_tank1194_{name}', 'GFX_MMG_tank1194_index', [
            option('MMG_tank1194_' + ('principles' if i == 1 else 'version'), f'MMG_tank.{3 - i}'),
            option('MMG_tank1194_index', 'MMG_guide.500'), option('MMG_tank1194_close'),
        ]))

    with ZipFile(docx) as archive:
        members = {d['source_member'] for d in designs.values()}
        actual_images = {name for name in archive.namelist() if name.startswith('word/media/') and name.lower().endswith('.png')}
        assert members == actual_images and len(members) == len(designs), 'Review missing or duplicated Word image mappings'
        for group in groups:
            images = group['images']
            menu_pages = [images[i:i + 4] for i in range(0, len(images), 4)]
            for page_index, menu_images in enumerate(menu_pages):
                menu_id = group['menu'] + page_index
                menu_key = f'MMG_tank1194_menu_{menu_id}'
                register_text(menu_key + '_t', {
                    'zh': f'{group["zh"]} · 目录（{page_index + 1}/{len(menu_pages)}）',
                    'en': f'{group["en"]}: Menu ({page_index + 1}/{len(menu_pages)})',
                })
                for language in languages:
                    loc[language][menu_key + '_d'] = TEXT[language]['group_d']
                picture_name = f'menu_{menu_id}'
                pictures[picture_name] = card(group['zh'], f'{group["en"]} / {page_index + 1} of {len(menu_pages)}',
                    [(designs[n]['zh'], designs[n]['en']) for n in menu_images], cjk_font)
                opts = [option(f'MMG_tank1194_design_{n:02}_label', f'MMG_tank.{100 + n}') for n in menu_images]
                if page_index:
                    opts.append(option('MMG_tank1194_menu_prev', f'MMG_tank.{menu_id - 1}'))
                if page_index + 1 < len(menu_pages):
                    opts.append(option('MMG_tank1194_menu_next', f'MMG_tank.{menu_id + 1}'))
                opts.extend([option('MMG_tank1194_index', 'MMG_guide.500'), option('MMG_tank1194_close')])
                assert len(opts) <= 8
                events.append(event(f'MMG_tank.{menu_id}', menu_key, 'GFX_MMG_tank1194_' + picture_name, opts))

            for pos, n in enumerate(images):
                design = designs[n]
                base_key = f'MMG_tank1194_design_{n:02}'
                menu_id = group['menu'] + pos // 4
                member = design['source_member']
                raw = archive.read(member)
                image_digest = hashlib.sha256(raw).hexdigest()
                assert image_digest == design['source_image_sha256'], f'Source image changed: {member}'
                original = Image.open(io.BytesIO(raw)).convert('RGBA')
                # Main view retains the whole original panel, including costs.
                pictures[f'{n:02}_full'] = fit(original)
                pictures[f'{n:02}_modules'] = stack_crops(original, [(0, .075, .495, .39), (0, .825, .495, .93)])
                pictures[f'{n:02}_stats'] = stack_crops(original, [(.495, .078, .998, .455), (.495, .928, .998, .998)])
                source_map.append({'image': n, 'source_member': member,
                    'sha256': image_digest, 'size': list(original.size),
                    'full_event': f'MMG_tank.{100+n}', 'modules_event': f'MMG_tank.{200+n}',
                    'stats_event': f'MMG_tank.{300+n}', 'menu': f'MMG_tank.{menu_id}'})
                for language in languages:
                    code = 'zh' if language == 'simp_chinese' else 'en'
                    title = design[code] + f' ({pos + 1}/{len(images)})'
                    desc = '\n'.join(design[f'{field}_{code}'] for field in ('config', 'note', 'stats'))
                    loc[language][base_key + '_label'] = design[code]
                    for view in ('full', 'modules', 'stats'):
                        suffix = '' if view == 'full' else TEXT[language][view + '_suffix']
                        loc[language][base_key + '_' + view + '_t'] = title + suffix
                        loc[language][base_key + '_' + view + '_d'] = desc
                opts = [option('MMG_tank1194_modules', f'MMG_tank.{200+n}'), option('MMG_tank1194_stats', f'MMG_tank.{300+n}')]
                if pos:
                    opts.append(option('MMG_tank1194_prev', f'MMG_tank.{100+images[pos-1]}'))
                if pos + 1 < len(images):
                    opts.append(option('MMG_tank1194_next', f'MMG_tank.{100+images[pos+1]}'))
                opts.extend([option('MMG_tank1194_group', f'MMG_tank.{menu_id}'),
                    option('MMG_tank1194_index', 'MMG_guide.500'), option('MMG_tank1194_close')])
                events.append(event(f'MMG_tank.{100+n}', base_key + '_full', f'GFX_MMG_tank1194_{n:02}_full', opts))
                for offset, view, other, other_offset in ((200, 'modules', 'stats', 300), (300, 'stats', 'modules', 200)):
                    events.append(event(f'MMG_tank.{offset+n}', base_key + '_' + view, f'GFX_MMG_tank1194_{n:02}_{view}', [
                        option('MMG_tank1194_full', f'MMG_tank.{100+n}'),
                        option('MMG_tank1194_' + other, f'MMG_tank.{other_offset+n}'),
                        option('MMG_tank1194_group', f'MMG_tank.{menu_id}'),
                        option('MMG_tank1194_index', 'MMG_guide.500'), option('MMG_tank1194_close'),
                    ]))

    (root / 'tools/page_sources/MMG_tank_1194_pages.mmg').write_text(''.join(events), encoding='utf-8', newline='\n')
    sprites = ['# Tank 1.19.4 pictures: full panels and reversible detail views.\nspriteTypes = {\n']
    for name, canvas in pictures.items():
        texture = f'gfx/event_pictures/mmg_tank_1194_{name}.dds'
        sprites.append('\tSpriteType = {\n' + f'\t\tname = "GFX_MMG_tank1194_{name}"\n' + f'\t\ttexturefile = "{texture}"\n' + '\t}\n')
        canvas.save(root / texture)
        if preview_dir:
            preview_dir.mkdir(parents=True, exist_ok=True)
            canvas.save(preview_dir / f'{name}.png')
    (root / 'interface/MMG_tank_1194.gfx').write_text(''.join(sprites) + '}\n', encoding='utf-8', newline='\n')
    for language, entries in loc.items():
        lines = [f'l_{language}:\n']
        for key, value in entries.items():
            value = value.replace('"', "'").replace('\n', r'\n')
            lines.append(f' {key}: "{value}"\n')
        (root / f'localisation/{language}/MMG_tank_1194_l_{language}.yml').write_text(''.join(lines), encoding='utf-8-sig', newline='\n')
    manifest = {'source': content['source'], 'sha256': digest, 'canvas': list(SIZE),
        'design_panels': len(designs), 'events': event_count, 'textures': len(pictures), 'sources': source_map,
        'module_crops': [[0, .075, .495, .39], [0, .825, .495, .93]],
        'stat_crops': [[.495, .078, .998, .455], [.495, .928, .998, .998]]}
    (root / 'tools/tank_1194_source_map.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    # Event-shaped files are offline page data; only the isolated UI is loaded.
    from guide_model import compile_viewer
    compile_viewer(root)
    print(f'{root.name}: {len(designs)} panels, {len(designs)*3} design views, {menu_count+3} menus/notes, {len(pictures)} textures; languages: {", ".join(languages)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('docx', type=Path)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    build(args.root.resolve(), args.docx, args.preview_dir)


if __name__ == '__main__':
    main()
