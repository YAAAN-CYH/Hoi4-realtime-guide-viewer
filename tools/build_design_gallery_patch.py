"""Print an apply_patch patch for PPT-verified gallery events, sprites and localisation."""
import difflib
from pathlib import Path
import re
import sys

from design_gallery import GALLERIES, pages

sys.stdout.reconfigure(encoding='utf-8')
root = Path(__file__).resolve().parents[1]
requested_outputs = set(sys.argv[1:])
events_path = root / 'events/MMG_guide_events.txt'
events = events_path.read_text(encoding='utf-8')


def read_loc(path):
    return dict(re.findall(
        r'^\s*(\w+):\s*"(.*)"',
        path.read_text(encoding='utf-8-sig'),
        re.M,
    ))


base_loc = {
    'simp_chinese': read_loc(root / 'localisation/simp_chinese/MMG_guide_l_simp_chinese.yml'),
    'english': read_loc(root / 'localisation/english/MMG_guide_l_english.yml'),
}
extras = [
    '# Additional pages keep base event IDs and chapter navigation stable.\n'
    '# Each event file must register its namespace before using namespaced IDs.\n'
    '# Without this declaration HOI4 1.19 parses these targets as MMG_guide.0000.\n'
    'add_namespace = MMG_guide\n\n'
]
sprites = ['# One complete design or one explicitly labelled reference per page.\nspriteTypes = {\n']
localisations = {
    'simp_chinese': ['\ufeffl_simp_chinese:\n', ' MMG_gallery_next: "下一张图"\n', ' MMG_gallery_prev: "上一张图"\n'],
    'english': ['\ufeffl_english:\n', ' MMG_gallery_next: "Next Image"\n', ' MMG_gallery_prev: "Previous Image"\n'],
}
kind_text = {
    'simp_chinese': {
        'complete': ('完整设计', ''),
        'partial': ('补充示意', '此图只说明界面位置或差异，不代表另一套完整成品设计。'),
        'reference': ('转换参考', '图中显示的是转换前角色，不能直接当作坦歼成品；请按说明切换设计角色。'),
        'context': ('相关方案', ''),
    },
    'english': {
        'complete': ('Full design', ''),
        'partial': ('Supplement', 'This image explains a UI location or comparison; it is not another complete finished design.'),
        'reference': ('Conversion reference', 'The displayed role is the pre-conversion vehicle, not a finished TD; change the design role as described.'),
        'context': ('Related configuration', ''),
    },
}


def option(name, target=None):
    lines = ['\toption = {', f'\t\tname = {name}']
    if target is not None:
        lines.append(f'\t\tcountry_event = {{ id = MMG_guide.{target} }}')
    return '\n'.join(lines + ['\t}'])


for name, base_id, menu_id, sources in GALLERIES:
    gallery = list(pages(name, base_id, menu_id, sources))
    for index, page in enumerate(gallery):
        key = f'MMG_gallery_{page["id"]}'
        for language in ('simp_chinese', 'english'):
            if language == 'simp_chinese':
                suffix = f'（{index + 1}/{len(gallery)}）' if len(gallery) > 1 else ''
                caption = page['caption_zh']
                separator = '：'
            else:
                suffix = f' ({index + 1}/{len(gallery)})' if len(gallery) > 1 else ''
                caption = page['caption_en']
                separator = ': '
            title = base_loc[language][f'MMG_{name}_t'] + suffix
            label, warning = kind_text[language][page['kind']]
            desc = base_loc[language][f'MMG_{name}_d'] + f'\\n{label}{separator}{caption}。'
            if language == 'english':
                desc = desc[:-1] + '.'
            if warning:
                desc += (' ' if language == 'english' else '') + warning
            localisations[language].extend([
                f' {key}_t: "{title}"\n',
                f' {key}_d: "{desc}"\n',
            ])

        block = '\n'.join([
            'country_event = {', f'\tid = MMG_guide.{page["id"]}',
            f'\ttitle = {key}_t', f'\tdesc = {key}_d',
            f'\tpicture = GFX_MMG_{page["name"]}', '\tis_triggered_only = yes', '',
            option('MMG_detail_understood'), option('MMG_detail_back', menu_id),
            # Boundary pages expose only navigation backed by a real source image.
            *([option('MMG_gallery_prev', gallery[index - 1]['id'])] if index > 0 else []),
            *([option('MMG_gallery_next', gallery[index + 1]['id'])] if index + 1 < len(gallery) else []),
            '}',
        ])
        if index == 0:
            matches = list(re.finditer(r'^country_event\s*=\s*\{.*?^\}', events, re.M | re.S))
            original = next(match for match in matches if re.search(
                rf'^\s*id\s*=\s*MMG_guide\.{base_id}\b', match[0], re.M))
            events = events[:original.start()] + block + events[original.end():]
        else:
            extras.append(block + '\n\n')
            sprites.append(
                '\tSpriteType = {\n'
                f'\t\tname = "GFX_MMG_{page["name"]}"\n'
                f'\t\ttexturefile = "gfx/event_pictures/mmg_{page["name"]}.dds"\n'
                '\t}\n'
            )
sprites.append('}\n')


def patch_file(path, content):
    display_path = path.relative_to(root.parent).as_posix()
    if path.exists():
        old = path.read_text(encoding='utf-8')
        if old == content:
            return ''
        diff = list(difflib.unified_diff(
            old.splitlines(keepends=True),
            content.splitlines(keepends=True),
            n=3,
        ))
        hunks = ''.join('@@\n' if line.startswith('@@ ') else line for line in diff[2:])
        return f'*** Update File: {display_path}\n' + hunks.rstrip('\n') + '\n'
    return f'*** Add File: {display_path}\n' + ''.join(
        '+' + line + '\n' for line in content.splitlines()
    )


def patch_changed_line_half(path, content, half):
    """Split large localisation-only replacements below Windows argv limits."""
    display_path = path.relative_to(root.parent).as_posix()
    old_lines = path.read_text(encoding='utf-8').splitlines()
    new_lines = content.splitlines()
    if len(old_lines) != len(new_lines):
        raise ValueError('Line-half patching requires an already generated key set')
    midpoint = (len(old_lines) + 1) // 2
    indexed = [(index, old, new) for index, (old, new) in
               enumerate(zip(old_lines, new_lines)) if old != new]
    selected = [(old, new) for index, old, new in indexed
                if (index < midpoint) == (half == 1)]
    if not selected:
        return ''
    hunks = ''.join(f'@@\n-{old}\n+{new}\n' for old, new in selected)
    return f'*** Update File: {display_path}\n{hunks}'


patch = '*** Begin Patch\n'
outputs = {
    'base-events': (events_path, events),
    'extra-events': (root / 'events/MMG_design_gallery_events.txt', ''.join(extras).rstrip() + '\n'),
    'gfx': (root / 'interface/MMG_design_gallery.gfx', ''.join(sprites)),
    'zh': (root / 'localisation/simp_chinese/MMG_design_gallery_l_simp_chinese.yml', ''.join(localisations['simp_chinese'])),
    'en': (root / 'localisation/english/MMG_design_gallery_l_english.yml', ''.join(localisations['english'])),
}
if requested_outputs == {'en-part1'}:
    patch += patch_changed_line_half(*outputs['en'], half=1)
elif requested_outputs == {'en-part2'}:
    patch += patch_changed_line_half(*outputs['en'], half=2)
else:
    for output_name, (path, content) in outputs.items():
        if not requested_outputs or output_name in requested_outputs:
            patch += patch_file(path, content)
print(patch + '*** End Patch')
