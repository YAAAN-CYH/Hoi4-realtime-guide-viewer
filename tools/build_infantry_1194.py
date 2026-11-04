"""Build offline infantry/army page data and the isolated player-only viewer.

Usage: python tools/build_infantry_1194.py INFANTRY.docx GUIDE.pptx [--preview-dir DIR]
Only MengXin_Armaments_Guide is maintained by this workflow. Source documents
are read as data; their instructions, macros and external links are not run.
The content JSON owns prose and evidence; sources supply verified image bytes.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageFont

from build_tank_1194 import fit, stack_crops, font_path, option, event, TEXT as TANK_TEXT
from validate_tank_1194 import wrap


def remove_old_chapters(root):
    """Retire old land/formation objects without touching other chapters."""
    path = root / 'tools/page_sources/MMG_guide_pages.mmg'
    old = path.read_text(encoding='utf-8')
    text = old
    for match in reversed(list(re.finditer(r'^country_event\s*=\s*\{.*?^\}', old, re.M | re.S))):
        ident = int(re.search(r'^\s*id\s*=\s*MMG_guide\.(\d+)', match[0], re.M)[1])
        if 100 <= ident <= 106 or 400 <= ident <= 406:
            text = text[:match.start()] + text[match.end():]
    text = re.sub(r'# ---------------------------------------------------------------------------\n# LAND DOCTRINES:.*?(?=# ---------------------------------------------------------------------------\n# NAVAL)',
                  '# Army doctrine and spirits are owned by MMG_infantry_1194_pages.mmg.\n\n', text, flags=re.S)
    text = re.sub(r'# ---------------------------------------------------------------------------\n# ARMY ORGANIZATION:.*?(?=# Tank designs)',
                  '# Division templates and army support are owned by MMG_infantry_1194_pages.mmg.\n\n', text, flags=re.S)
    if text != old:
        path.write_text(text, encoding='utf-8', newline='\n')
    path = root / 'interface/MMG_eventpictures.gfx'
    old = path.read_text(encoding='utf-8')
    text = re.sub(r'^\tSpriteType\s*=\s*\{\n\t\tname\s*=\s*"GFX_MMG_(?:land|army)_[^"]*".*?^\t}\n', '', old, flags=re.M | re.S)
    if text != old:
        path.write_text(text, encoding='utf-8', newline='\n')
    for language in ('simp_chinese', 'english'):
        path = root / f'localisation/{language}/MMG_guide_l_{language}.yml'
        old = path.read_text(encoding='utf-8-sig')
        text = ''.join(line for line in old.splitlines(keepends=True) if not re.match(r' MMG_(?:land|army)_', line))
        if text != old:
            path.write_text(text, encoding='utf-8-sig', newline='\n')
    for prefix in ('mmg_land_', 'mmg_army_'):
        for path in (root / 'gfx/event_pictures').glob(prefix + '*.dds'):
            path.unlink()


def menu_card(zh, en, items, fonts):
    image = Image.new('RGBA', (720, 450), '#d7ceb5')
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 711, 441), 12, outline='#665c43', width=2)
    draw.text((26, 20), zh, font=fonts[26], fill='#252b22')
    draw.text((26, 61), en, font=fonts[16], fill='#4b4c3d')
    step = 52 if len(items) > 5 else 64
    for i, (left, right) in enumerate(items):
        y = 104 + i * step
        draw.text((28, y), left, font=fonts[21], fill='#252b22')
        draw.text((28, y + 29), right, font=fonts[15], fill='#4b4c3d')
    return image


def card_wrap(text, font, width):
    """Keep English words intact; Chinese text uses character wrapping."""
    lines = []
    for paragraph in text.split('\n'):
        if re.search(r'[\u3400-\u9fff]', paragraph):
            lines.extend(wrap(paragraph, font, width))
        else:
            line = ''
            for word in paragraph.split():
                candidate = (line + ' ' + word).strip()
                if line and font.getlength(candidate) > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
    return lines


def note_card(zh, en, desc_zh, desc_en, fonts):
    image = menu_card(zh, en, [], fonts)
    draw = ImageDraw.Draw(image)
    y = 106
    for text, size, spacing in ((desc_zh, 20, 24), (desc_en, 14, 18)):
        lines = card_wrap(text, fonts[size], 662)
        if y + len(lines) * spacing > 428:
            raise ValueError(f'Bilingual note artwork overflow: {zh}')
        for line in lines:
            draw.text((28, y), line, font=fonts[size], fill='#252b22')
            y += spacing
        y += 12
    return image


def build(root, docx, pptx, preview_dir=None):
    content = json.loads((root / 'tools/infantry_1194_content.json').read_text(encoding='utf-8'))
    if root.name != content['canonical_target']:
        raise ValueError('This update targets MengXin_Armaments_Guide only.')
    for source, path in (('word', docx), ('ppt', pptx)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != content['sources'][source]['sha256']:
            raise ValueError(f'Review changed {source} source before rebuilding.')
    templates = {item['id']: item for item in content['templates']}
    assert sorted(templates) == list(range(1, 19))
    assert sorted(n for group in content['groups'] for n in group['templates']) == sorted(templates)
    with ZipFile(docx) as archive:
        expected = {item['source_member'] for item in templates.values()} | {content['preset']['source_member']}
        actual = {name for name in archive.namelist() if name.startswith('word/media/') and name.endswith('.png')}
        assert expected == actual and len(actual) == 19
        originals = {}
        for item in [content['preset'], *templates.values()]:
            raw = archive.read(item['source_member'])
            assert hashlib.sha256(raw).hexdigest() == item['source_sha256'], item['source_member']
            originals[item['source_member']] = Image.open(io.BytesIO(raw)).convert('RGBA')
    fonts = {size: ImageFont.truetype(font_path(), size) for size in (14, 15, 16, 20, 21, 26)}
    remove_old_chapters(root)
    texts = {'simp_chinese': {}, 'english': {}}
    events, pictures, records = [], {}, []
    prefix = 'MMG_inf1194_'

    def localize(key, zh, en):
        texts['simp_chinese'][key] = zh
        texts['english'][key] = en

    def add(ident, name, zh, en, dz, de, asset, choices):
        key = prefix + name
        localize(key + '_t', zh, en)
        localize(key + '_d', dz, de)
        events.append(event(ident, key, 'GFX_MMG_infantry1194_' + asset, choices))
        records.append({'event': ident, 'picture': asset, 'key': key})

    common = {
        'close': ('了解了', 'Understood'), 'index': ('返回编制总目录', 'Back to Template Index'),
        'land': ('返回陆军学说', 'Back to Army Doctrine'), 'spirit': ('返回陆军精神', 'Back to Army Spirits'),
        'support': ('返回支援连目录', 'Back to Support Menu'), 'group': ('返回本组目录', 'Back to Group Menu'),
        'prev': ('上一编制', 'Previous Template'), 'next': ('下一编制', 'Next Template'),
        'menu_prev': ('上一页目录', 'Previous Menu Page'), 'menu_next': ('下一页目录', 'Next Menu Page'),
        'full': ('返回完整编制', 'Back to Full Template'), 'layout': ('放大查看编制与支援', 'Enlarge Battalions and Support'),
        'stats': ('放大查看属性与造价', 'Enlarge Stats and Cost'),
        'preset': ('参考条件与默认学说', 'Conditions and Doctrine Preset'),
        'patch': ('1.19.4机制更正', '1.19.4 Rules and Corrections'),
        'support_menu': ('支援连、团支与占领法案', 'Support Companies and Occupation Laws'),
        'spirit_menu': ('陆军精神：20 / 35 / 50 XP', 'Army Spirits: 20 / 35 / 50 XP'),
    }
    for name, value in common.items():
        localize(prefix + name, *value)
    localize('MMG_army_org_decision', '陆军编制 · 1.19.4', 'Division Templates: 1.19.4')
    localize('MMG_army_org_decision_desc', '查看18套更新编制、默认学说、支援连与1.19.4机制说明。', 'Browse eighteen updated division templates, recommended doctrines, support companies and 1.19.4 mechanics.')
    localize('MMG_land_doctrine_decision', '陆军学说 · 1.19.4', 'Army Doctrine: 1.19.4')
    localize('MMG_land_doctrine_decision_desc', '查看按1.19.4核对的陆军学说与精神，结合编制和可用条件选择。', 'Review army doctrines and spirits for 1.19.4. Choose according to your division templates and the options available to your country.')
    opt = lambda name, target=None: option(prefix + name, target)

    pictures['index'] = menu_card('陆军编制 · 1.19.4', '18 division templates / 54 views',
        [(g['zh'] + f' · {len(g["templates"])}套', g['en']) for g in content['groups']], fonts)
    root_options = [opt('preset', 'MMG_infantry.1')]
    for group in content['groups']:
        localize(prefix + f'group_{group["id"]}', group['zh'], group['en'])
        root_options.append(opt(f'group_{group["id"]}', f'MMG_infantry.{group["id"]}'))
    root_options += [opt('support_menu', 'MMG_infantry.50'), opt('patch', 'MMG_infantry.2'), opt('close')]
    assert len(root_options) == 8
    add('MMG_guide.400', 'index', '陆军编制 · 1.19.4', 'Division Templates: 1.19.4',
        '按战场与学说条件选择18套编制。每项有完整图、编制支援放大和属性造价放大；数值依赖图示装备、学说与精通，不能直接套用于未成型部队。',
        'Choose from eighteen division templates by role and doctrine. Each offers a full view, battalions and support, and stats and cost. Values depend on the equipment, doctrines and mastery shown.', 'index', root_options)

    notes = {note['id']: note for note in content['notes']}
    for ident, note in notes.items():
        name = f'note_{ident}'
        if ident == 1:
            asset = 'preset'
            pictures[asset] = fit(originals[content['preset']['source_member']])
        else:
            asset = name
            pictures[asset] = note_card(note['zh'], note['en'], note['desc_zh'], note['desc_en'], fonts)
        choices = []
        if ident in (2, 3, 4):
            for other in (ident-1, ident+1):
                if 2 <= other <= 4:
                    key = f'note_{other}_label'
                    localize(prefix + key, notes[other]['zh'], notes[other]['en'])
                    choices.append(opt(key, f'MMG_infantry.{other}'))
        if 51 <= ident <= 56:
            choices.append(opt('support', 'MMG_infantry.50'))
        elif 61 <= ident <= 64:
            choices.append(opt('spirit', 'MMG_guide.106'))
        choices += [opt('index', 'MMG_guide.400'), opt('close')]
        add(f'MMG_infantry.{ident}', name, note['zh'], note['en'], note['desc_zh'], note['desc_en'], asset, choices)

    for ids, eid, name, title_zh, title_en, back, desc_zh, desc_en in [
        (list(range(51,57)), 'MMG_infantry.50', 'support_menu', '支援连、团支与占领法案', 'Support Companies and Occupation Laws', 'MMG_guide.400',
         '按地形、补给、人员损耗与火力需求配置支援。团支和师级支援不是同一类型；查看当前学说下的效果，不把旧版绝对排名当成通用规则。',
         'Choose support companies for terrain, supply, casualties and firepower. Divisional and regimental support are separate categories; check their effects with your current doctrines.'),
        ([61,62,64,63], 'MMG_guide.106', 'spirit_menu', '陆军精神 · 按条件选择', 'Army Spirits: Choose by Requirements', 'MMG_guide.100',
         '按20、35、50XP分类查看常用精神。政体、主学说、子学说、军官学院和DLC会影响可用项；不能把几个互斥精神的收益同时算入。',
         'Browse common spirits costing 20, 35 or 50 army XP. Ideology, doctrines, academy and DLC affect availability. Mutually exclusive spirits cannot provide their bonuses at the same time.')]:
        choices = []
        for ident in ids:
            localize(prefix + f'note_{ident}_label', notes[ident]['zh'], notes[ident]['en'])
            choices.append(opt(f'note_{ident}_label', f'MMG_infantry.{ident}'))
        choices += [opt('index' if back.endswith('.400') else 'land', back), opt('close')]
        pictures[name] = menu_card(title_zh, title_en, [(notes[i]['zh'], notes[i]['en']) for i in ids], fonts)
        add(eid, name, title_zh, title_en, desc_zh, desc_en, name, choices)

    for item in content['land']:
        ident = item['id']
        asset = f'land_{ident}'
        pictures[asset] = note_card(item['zh'], item['en'], item['desc_zh'], item['desc_en'], fonts)
        if ident == 100:
            choices = []
            for other in content['land'][1:]:
                localize(prefix + f'land_{other["id"]}_label', other['zh'], other['en'])
                choices.append(opt(f'land_{other["id"]}_label', f'MMG_guide.{other["id"]}'))
            choices += [opt('spirit_menu', 'MMG_guide.106'), opt('index', 'MMG_guide.400'), opt('close')]
        else:
            choices = [opt('land', 'MMG_guide.100'), opt('index', 'MMG_guide.400'), opt('close')]
        add(f'MMG_guide.{ident}', asset, item['zh'], item['en'], item['desc_zh'], item['desc_en'], asset, choices)

    for group in content['groups']:
        ids = group['templates']
        pages = [ids[n:n+4] for n in range(0,len(ids),4)]
        for index, page in enumerate(pages):
            ident = group['id'] + index
            name = f'menu_{ident}'
            choices = []
            for n in page:
                localize(prefix + f'template_{n}_label', templates[n]['zh'], templates[n]['en'])
                choices.append(opt(f'template_{n}_label', f'MMG_infantry.{100+n}'))
            if index:
                choices.append(opt('menu_prev', f'MMG_infantry.{ident-1}'))
            if index+1 < len(pages):
                choices.append(opt('menu_next', f'MMG_infantry.{ident+1}'))
            choices += [opt('index', 'MMG_guide.400'), opt('close')]
            assert len(choices) <= 8
            pictures[name] = menu_card(group['zh'], f'{group["en"]} / {index+1} of {len(pages)}',
                [(templates[n]['zh'],templates[n]['en']) for n in page], fonts)
            add(f'MMG_infantry.{ident}', name, f'{group["zh"]}（{index+1}/{len(pages)}）',
                f'{group["en"]} ({index+1}/{len(pages)})',
                '选择编制后可连续翻看本组方案。标注“改学说”的最后三项必须先核对切换条件。',
                'Select a template, then browse the other formations in this group. The final three templates require the specified doctrine changes.', name, choices)
        for index, ident in enumerate(ids):
            item = templates[ident]
            source = originals[item['source_member']]
            pictures[f'template_{ident}_full'] = fit(source)
            pictures[f'template_{ident}_layout'] = fit(source.crop((0,round(source.height*.33),round(source.width*.525),round(source.height*.865))))
            pictures[f'template_{ident}_stats'] = stack_crops(source, [(.525,.065,.998,.51),(.525,.865,.998,.94)])
            menu = group['id'] + index//4
            desc = {code:'\n'.join(item[f'{field}_{code}'] for field in ('config','note','stats')) for code in ('zh','en')}
            for offset, view, suffix_zh, suffix_en in ((100,'full','',''),(200,'layout',' · 编制与支援',' / Battalions and Support'),(300,'stats',' · 属性与造价',' / Stats and Cost')):
                choices = []
                if view == 'full':
                    choices += [opt('layout',f'MMG_infantry.{200+ident}'),opt('stats',f'MMG_infantry.{300+ident}')]
                    if index:
                        choices.append(opt('prev',f'MMG_infantry.{100+ids[index-1]}'))
                    if index+1<len(ids):
                        choices.append(opt('next',f'MMG_infantry.{100+ids[index+1]}'))
                else:
                    choices.append(opt('full',f'MMG_infantry.{100+ident}'))
                    other = 'stats' if view=='layout' else 'layout'
                    choices.append(opt(other,f'MMG_infantry.{(300 if other=="stats" else 200)+ident}'))
                choices += [opt('group',f'MMG_infantry.{menu}'),opt('index','MMG_guide.400'),opt('close')]
                name = f'template_{ident}_{view}'
                add(f'MMG_infantry.{offset+ident}', name, item['zh']+f'（{index+1}/{len(ids)}）'+suffix_zh,
                    item['en']+f' ({index+1}/{len(ids)})'+suffix_en, desc['zh'],desc['en'],name,choices)

    header = '# OFFLINE guide page data; tools/build_viewer.py compiles the player UI.\n# Source chapter IDs: MMG_guide.100 and .400; never installed as events.\nadd_namespace = MMG_guide\nadd_namespace = MMG_infantry\n\n'
    (root/'tools/page_sources/MMG_infantry_1194_pages.mmg').write_text(header+''.join(events),encoding='utf-8',newline='\n')
    gfx = ['# Word formation panels and reviewed army-note cards.\nspriteTypes = {\n']
    for name, picture in pictures.items():
        path = f'gfx/event_pictures/mmg_infantry_1194_{name}.dds'
        picture.save(root/path)
        gfx.append('\tSpriteType = {\n'+f'\t\tname = "GFX_MMG_infantry1194_{name}"\n'+f'\t\ttexturefile = "{path}"\n'+'\t}\n')
        if preview_dir:
            preview_dir.mkdir(parents=True,exist_ok=True)
            picture.save(preview_dir/f'{name}.png')
    (root/'interface/MMG_infantry_1194.gfx').write_text(''.join(gfx)+'}\n',encoding='utf-8',newline='\n')
    for language, entries in texts.items():
        lines = [f'l_{language}:\n']
        for key,value in entries.items():
            value = value.replace('"',"'").replace('\n',r'\n')
            lines.append(f' {key}: "{value}"\n')
        (root/f'localisation/{language}/MMG_infantry_1194_l_{language}.yml').write_text(''.join(lines),encoding='utf-8-sig',newline='\n')
        # The patch corrects the old tank note: +2% is a multiplier, not +2
        # flat attack. Read from the tank generator's owning source of truth.
        path = root/f'localisation/{language}/MMG_tank_1194_l_{language}.yml'
        text = path.read_text(encoding='utf-8-sig')
        value = TANK_TEXT[language]['version_d'].replace('\n',r'\n')
        text,count = re.subn(r'^ MMG_tank1194_version_d: ".*"$',lambda _:f' MMG_tank1194_version_d: "{value}"',text,flags=re.M)
        assert count == 1
        path.write_text(text,encoding='utf-8-sig',newline='\n')
    manifest = {'sources':content['sources'],'templates':18,'word_images':19,'events':len(events),'textures':len(pictures),
        'formation_sources':[{'id':i['id'],'member':i['source_member'],'sha256':i['source_sha256'],'full':f'MMG_infantry.{100+i["id"]}','layout':f'MMG_infantry.{200+i["id"]}','stats':f'MMG_infantry.{300+i["id"]}'} for i in content['templates']],
        'preset':content['preset'],'objects':records}
    (root/'tools/infantry_1194_source_map.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    # Compile page data into player-only UI; never restore runtime events.
    from guide_model import compile_viewer
    compile_viewer(root)
    print(f'{root.name}: 18 Word formations, {len(events)} army source pages, {len(pictures)} textures; Chinese/English.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('docx',type=Path)
    parser.add_argument('pptx',type=Path)
    parser.add_argument('--preview-dir',type=Path)
    args=parser.parse_args()
    build(Path(__file__).resolve().parents[1],args.docx,args.pptx,args.preview_dir)


if __name__=='__main__':
    main()
