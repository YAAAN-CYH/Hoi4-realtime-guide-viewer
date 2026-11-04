"""Offline integration and bounds checks for the Word infantry/army chapter.

This validates reference-content wiring, not live gameplay or engine input.
Usage: python tools/validate_infantry_1194.py [--report output.json]
"""

import argparse
import json
from pathlib import Path
import re

from PIL import Image, ImageFont

from build_tank_1194 import font_path
from validate_tank_1194 import wrap


def validate(root):
    content = json.loads((root/'tools/infantry_1194_content.json').read_text(encoding='utf-8'))
    manifest = json.loads((root/'tools/infantry_1194_source_map.json').read_text(encoding='utf-8'))
    errors = []
    events = {}
    for path in (root/'tools/page_sources').glob('*.mmg'):
        text = path.read_text(encoding='utf-8')
        namespaces = set(re.findall(r'^add_namespace\s*=\s*(\w+)',text,re.M))
        for block in re.findall(r'^country_event\s*=\s*\{.*?^\}',text,re.M|re.S):
            ident = re.search(r'^\s*id\s*=\s*(\w+\.\d+)',block,re.M)[1]
            if ident in events:
                errors.append('Duplicate event: '+ident)
            if ident.split('.')[0] not in namespaces:
                errors.append('Unregistered namespace: '+ident)
            events[ident] = block
    retained = {f'MMG_guide.{n}' for n in range(100,107)} | {'MMG_guide.400'}
    owned = {k:v for k,v in events.items() if k.startswith('MMG_infantry.') or k in retained}
    if len(owned) != manifest['events'] or len(owned) != 83:
        errors.append(f'Expected 83 army source pages, got {len(owned)}')
    if any(f'MMG_guide.{n}' in events for n in range(401,407)):
        errors.append('Retired old formation events remain')
    links = {k:re.findall(r'country_event\s*=\s*\{\s*id\s*=\s*(\w+\.\d+)',v) for k,v in events.items()}
    for key, targets in links.items():
        for target in targets:
            if target not in events:
                errors.append(f'Missing event target: {key} -> {target}')
    seen = set()
    pending = ['MMG_guide.100','MMG_guide.400']
    while pending:
        key = pending.pop()
        if key in seen:
            continue
        seen.add(key)
        pending.extend(links.get(key,[]))
    if seen != set(owned):
        errors.append('Unreachable/escaping army source pages: '+str(sorted(seen ^ set(owned))))
    for group in content['groups']:
        ids = group['templates']
        for i,n in enumerate(ids):
            full, layout, stats = (f'MMG_infantry.{offset+n}' for offset in (100,200,300))
            menu = f'MMG_infantry.{group["id"]+i//4}'
            if not {layout,stats,menu,'MMG_guide.400'} <= set(links.get(full,[])):
                errors.append('Broken full-view navigation: '+full)
            for detail in (layout,stats):
                if not {full,menu,'MMG_guide.400'} <= set(links.get(detail,[])):
                    errors.append('Broken enlargement return: '+detail)
            for next_index in (i-1,i+1):
                if 0 <= next_index < len(ids) and f'MMG_infantry.{100+ids[next_index]}' not in links.get(full,[]):
                    errors.append('Broken adjacent formation link: '+full)
    if sorted(i['id'] for i in content['templates']) != list(range(1,19)):
        errors.append('The source must contain exactly the eighteen requested formations')
    source_members = [x['source_member'] for x in content['templates']] + [content['preset']['source_member']]
    if len(set(source_members)) != 19:
        errors.append('Duplicated or missing Word images')
    for source,item in zip(manifest['formation_sources'],content['templates']):
        if source['id']!=item['id'] or source['member']!=item['source_member'] or source['sha256']!=item['source_sha256']:
            errors.append('Incorrect formation source mapping: '+str(item['id']))

    gfx=(root/'interface/MMG_infantry_1194.gfx').read_text(encoding='utf-8')
    sprites=dict(re.findall(r'name\s*=\s*"([^"]+)"\s*\n\s*texturefile\s*=\s*"([^"]+)"',gfx))
    used=set()
    for key,block in owned.items():
        sprite=re.search(r'^\s*picture\s*=\s*(\w+)',block,re.M)[1]
        used.add(sprite)
        if sprite not in sprites or not (root/sprites[sprite]).is_file():
            errors.append('Missing sprite/texture: '+key)
    if used != set(sprites):
        errors.append('Unreferenced or absent army sprites')
    textures=list((root/'gfx/event_pictures').glob('mmg_infantry_1194_*.dds'))
    if len(textures)!=manifest['textures']:
        errors.append('Unexpected army texture count')
    for path in textures:
        with Image.open(path) as im:
            if im.size!=(720,450) or im.mode!='RGBA':
                errors.append('Wrong DDS format: '+path.name)
            im.load()
    if list((root/'gfx/event_pictures').glob('mmg_army_*.dds')) or list((root/'gfx/event_pictures').glob('mmg_land_*.dds')):
        errors.append('Old army/doctrine picture assets remain')

    fonts={size:ImageFont.truetype(font_path(),size) for size in (18,22)}
    layouts=[]
    for language in ('simp_chinese','english'):
        loc={}
        for path in (root/'localisation'/language).glob('*.yml'):
            if not path.read_bytes().startswith(b'\xef\xbb\xbf'):
                errors.append('Missing localisation BOM: '+path.name)
            for k,v in re.findall(r'^ (\w+): "(.*)"$',path.read_text(encoding='utf-8-sig'),re.M):
                if k in loc:
                    errors.append(f'Duplicate localisation: {language} {k}')
                loc[k]=v
        required={'MMG_army_org_decision','MMG_army_org_decision_desc','MMG_land_doctrine_decision','MMG_land_doctrine_decision_desc'}
        for key,block in owned.items():
            required.update(re.findall(r'^\s*(?:title|desc|name)\s*=\s*(MMG_\w+)',block,re.M))
            title=re.search(r'^\s*title\s*=\s*(\w+)',block,re.M)[1]
            desc=re.search(r'^\s*desc\s*=\s*(\w+)',block,re.M)[1]
            opts=re.findall(r'^\s*name\s*=\s*(\w+)',block,re.M)
            lines=len(wrap(loc.get(desc,''),fonts[18],1080))
            title_width=fonts[22].getlength(loc.get(title,''))
            opt_lines=max((len(wrap(loc.get(k,''),fonts[18],332)) for k in opts),default=0)
            if lines>5 or title_width>1050 or len(opts)>8 or opt_lines>2:
                errors.append(f'Text/option overflow: {language} {key}: lines={lines}, title={title_width:.0f}, choices={len(opts)}, option_lines={opt_lines}')
            layouts.append({'language':language,'event':key,'description_lines':lines,'title_width':round(title_width,1),'options':len(opts),'max_option_lines':opt_lines})
        if required-set(loc):
            errors.append('Missing '+language+' keys: '+str(sorted(required-set(loc))))
    for error in errors:
        print('ERROR:',error)
    print(f'{root.name}: {len(events)} total source pages, {len(owned)} army source pages, 18 formations, {len(textures)} army textures, {len(layouts)} localized layouts; {len(errors)} errors.')
    return {'total_events':len(events),'army_events':len(owned),'templates':18,'textures':len(textures),'errors':errors,'layouts':layouts}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    result=validate(Path(__file__).resolve().parents[1])
    if args.report:
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(bool(result['errors']))


if __name__=='__main__':
    main()
