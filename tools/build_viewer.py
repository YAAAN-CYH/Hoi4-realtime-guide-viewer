"""Compile the complete guide into an additive player-only scripted GUI.

Usage: python tools/build_viewer.py [--preview-dir DIR]
No events, decisions, on_actions, vanilla windows or gameplay data are emitted.
Only two private country variables hold the current UI page/choice count;
every close path clears both. No effects run from visibility or on a timer.
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from build_tank_1194 import font_path
from guide_model import CHAPTERS, load_pages, page_number, read_localisation


PAGE = 'MMG_UI_page'
CHOICES = 'MMG_UI_choices'
TEXT = {
    'simp_chinese': {
        'home_title': '实时攻略查看器',
        'home_desc': '选择章节查阅学说、编制与装备设计。可在目录中翻页，放大配置与属性，或随时返回总目录。',
        'open': '攻略查看器', 'open_tt': '打开实时攻略查看器',
        'home': '返回总目录', 'close': '关闭攻略', 'blank': '',
    },
    'english': {
        'home_title': 'Realtime Strategy Guide Viewer',
        'home_desc': 'Choose a chapter to browse doctrines, division templates and equipment designs. Browse menus, enlarge modules or stats, and return to the guide index at any time.',
        'open': 'Guide Viewer', 'open_tt': 'Open the Realtime Strategy Guide Viewer',
        'home': 'Guide Index', 'close': 'Close Guide', 'blank': '',
    },
}


def check(value):
    return f'check_variable = {{ var = {PAGE} value = {value} compare = equals }}'


def state(page):
    return (f'set_variable = {{ {PAGE} = {page["number"]} }}\n'
            f'      set_variable = {{ {CHOICES} = {len(page["choices"])} }}')


def clear():
    return f'clear_variable = {PAGE}\n      clear_variable = {CHOICES}'


def selector(name, rows, fallback):
    lines = ['defined_text = {\n', f' name = {name}\n']
    for number, key in rows:
        lines.append(f' text = {{ trigger = {{ {check(number)} }} localization_key = "{key}" }}\n')
    lines.append(f' text = {{ localization_key = "{fallback}" }}\n}}\n\n')
    return ''.join(lines)


def build(root, preview_dir=None):
    if root.name != 'MengXin_Armaments_Guide':
        raise ValueError('Only the canonical mod is maintained by this compiler.')
    pages = load_pages(root)
    by_id = {p['id']: p for p in pages}
    for path in (root / 'events').glob('*.txt'):
        raise ValueError('Guide sources must not remain in engine events/: ' + path.name)
    for path in (root / 'common/decisions').rglob('*.txt'):
        raise ValueError('Decision entry points must be removed: ' + str(path))
    if (root / 'interface/eventwindow.gui').exists():
        raise ValueError('Remove the global EventWindow override before compiling.')

    for language, values in TEXT.items():
        entries = {'MMG_UI_' + key: value for key, value in values.items()}
        entries.update({'MMG_UI_title': '[MMG_UI_GetTitle]', 'MMG_UI_description': '[MMG_UI_GetDescription]'})
        entries.update({f'MMG_UI_option_{i}': f'[MMG_UI_GetOption{i}]' for i in range(1, 9)})
        lines = [f'l_{language}:\n']
        lines += [f' {key}: "{value}"\n' for key, value in entries.items()]
        (root / f'localisation/{language}/MMG_viewer_l_{language}.yml').write_text(''.join(lines), encoding='utf-8-sig', newline='\n')
    for language in TEXT:
        loc = read_localisation(root, language)
        needed = {p[k] for p in pages for k in ('title', 'description')}
        needed.update(c['label'] for p in pages for c in p['choices'])
        if needed - loc.keys():
            raise ValueError('Missing visible text: ' + str(sorted(needed - loc.keys())))

    # Native AST cabinet UI uses image = "[DEFINED_TEXT]" to select a sprite.
    # Text uses localisation wrappers so ordinary textbox/button consumers
    # receive the same country-context defined_text result.
    loc_script = '# Private UI selectors; read-only page checks, no effects.\n\n'
    for name, field, fallback in [('Title', 'title', pages[0]['title']),
                                  ('Description', 'description', pages[0]['description']),
                                  ('Image', 'picture', pages[0]['picture'])]:
        loc_script += selector('MMG_UI_Get' + name, [(p['number'], p[field]) for p in pages], fallback)
    for i in range(1, 9):
        loc_script += selector(f'MMG_UI_GetOption{i}',
            [(p['number'], p['choices'][i-1]['label']) for p in pages if len(p['choices']) >= i], 'MMG_UI_blank')
    path = root / 'common/scripted_localisation/MMG_viewer.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(loc_script, encoding='utf-8', newline='\n')

    sg = [
        '# Player-only guide UI. Only MMG_UI_page/MMG_UI_choices may be written.\n',
        '# No gameplay hooks, decisions, events, random effects or logging.\n',
        'scripted_gui = {\n MMG_UI_launcher = {\n',
        '  context_type = player_context\n  window_name = "MMG_UI_Launcher"\n',
        '  # Mount on the full-screen in-game topbar, not the default main window.\n',
        '  # This is an additive child; interface/topbar.gui is never overridden.\n',
        '  parent_window_token = top_bar\n',
        '  visible = { is_ai = no }\n  ai_enabled = { always = no }\n',
        '  effects = {\n   MMG_UI_Open_click = {\n      ' + state(pages[0]) + '\n   }\n  }\n }\n',
        ' MMG_UI_viewer = {\n  context_type = player_context\n',
        '  # Keep the panel on the same in-game layer as its launcher.\n',
        '  parent_window_token = top_bar\n',
        '  window_name = "MMG_UI_Viewer"\n  dirty = MMG_UI_page\n',
        '  visible = { is_ai = no has_variable = MMG_UI_page }\n',
        '  ai_enabled = { always = no }\n',
        '  properties = { MMG_UI_Picture = { image = "[MMG_UI_GetImage]" } }\n',
        '  triggers = {\n',
    ]
    for i in range(1, 9):
        for name in (f'MMG_UI_Option_{i}', f'MMG_UI_OptionLabel_{i}'):
            sg.append(f'   {name}_visible = {{ check_variable = {{ var = {CHOICES} value = {i} compare = greater_than_or_equals }} }}\n')
    sg += ['  }\n  effects = {\n', '   MMG_UI_Home_click = {\n      ' + state(pages[0]) + '\n   }\n',
           '   MMG_UI_Close_click = {\n      ' + clear() + '\n   }\n']
    for i in range(1, 9):
        sg.append(f'   MMG_UI_Option_{i}_click = {{\n')
        first = True
        for page in pages:
            if len(page['choices']) < i:
                continue
            choice = page['choices'][i-1]
            # The one matching branch changes only the viewer's private state.
            effect = state(by_id[choice['target']]) if choice['target'] else clear()
            sg.append(f'    {"if" if first else "else_if"} = {{\n     limit = {{ {check(page["number"])} }}\n      {effect}\n    }}\n')
            first = False
        sg.append('   }\n')
    sg.append('  }\n }\n}\n')
    path = root / 'common/scripted_guis/MMG_viewer.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(sg), encoding='utf-8', newline='\n')

    gui = '''# Additive containers only: never define EventWindow or replace vanilla GUI.
guiTypes = {
 containerWindowType = {
  name = "MMG_UI_Launcher"
  # Root x=0 plus the button's x=16 preserves the original button position.
  # The uncovered left grip belongs to this moveable parent. A button there
  # would capture the mouse and prevent the native window drag.
  position = { x = 0 y = -100 }
  orientation = lower_left
  size = { width = 164 height = 34 }
  moveable = yes
  background = {
   name = "MMG_UI_Grip"
   quadTextureSprite = "GFX_MMG_UI_launcher_grip"
  }
  buttonType = {
   name = "MMG_UI_Open"
   position = { x = 16 y = 0 }
   quadTextureSprite = "GFX_button_148x34"
   buttonText = "MMG_UI_open"
   buttonFont = "hoi_16mbs"
   pdx_tooltip = "MMG_UI_open_tt"
   clicksound = click_default
  }
 }
 containerWindowType = {
  name = "MMG_UI_Viewer"
  position = { x = -570 y = -340 }
  orientation = center
  size = { width = 1140 height = 680 }
  moveable = yes
  click_to_front = yes
  background = {
   name = "MMG_UI_Paper"
   quadTextureSprite = "GFX_MMG_UI_frame"
  }
  buttonType = {
   name = "MMG_UI_Home"
   position = { x = 918 y = 14 }
   quadTextureSprite = "GFX_button_148x34"
   buttonText = "MMG_UI_home"
   buttonFont = "hoi_16mbs"
   clicksound = click_default
  }
  buttonType = {
   name = "MMG_UI_Close"
   position = { x = 1080 y = 14 }
   quadTextureSprite = "GFX_closebutton"
   pdx_tooltip = "MMG_UI_close"
   clicksound = click_close
  }
  instantTextBoxType = {
   name = "MMG_UI_Title"
   position = { x = 45 y = 54 }
   font = "hoi4_typewriter22"
   text = "MMG_UI_title"
   maxWidth = 1050
   maxHeight = 32
   format = centre
   alwaystransparent = yes
  }
  instantTextBoxType = {
   name = "MMG_UI_Description"
   position = { x = 30 y = 94 }
   font = "hoi4_typewriter16"
   text = "MMG_UI_description"
   maxWidth = 1080
   maxHeight = 100
   format = left
   alwaystransparent = yes
  }
  iconType = {
   name = "MMG_UI_Picture"
   position = { x = 24 y = 206 }
   spriteType = "GFX_MMG_UI_home"
   alwaystransparent = yes
  }
'''
    for i in range(1, 9):
        y = 206 + (i-1)*56
        gui += f'''  buttonType = {{
   name = "MMG_UI_Option_{i}"
   position = {{ x = 764 y = {y} }}
   quadTextureSprite = "GFX_MMG_UI_option"
   clicksound = click_default
  }}
  instantTextBoxType = {{
   name = "MMG_UI_OptionLabel_{i}"
   position = {{ x = 774 y = {y+3} }}
   font = "hoi4_typewriter16"
   text = "MMG_UI_option_{i}"
   maxWidth = 332
   maxHeight = 44
   format = center
   vertical_alignment = center
   alwaystransparent = yes
  }}
'''
    gui += ' }\n}\n'
    (root / 'interface/MMG_viewer.gui').write_text(gui, encoding='utf-8', newline='\n')

    # Preserve the complete fixed paper frame; only its consumer is isolated.
    gfx = '''# Unique viewer sprites only; vanilla sprites and windows are untouched.
spriteTypes = {
 SpriteType = {
  name = "GFX_MMG_UI_frame"
  texturefile = "gfx/interface/mmg_eventwindow_background.dds"
  noOfFrames = 1
 }
 SpriteType = {
  name = "GFX_MMG_UI_launcher_grip"
  texturefile = "gfx/interface/mmg_ui_launcher_grip.dds"
  noOfFrames = 1
 }
 SpriteType = {
  name = "GFX_MMG_UI_option"
  texturefile = "gfx/interface/mmg_ui_option.dds"
  noOfFrames = 3
 }
 SpriteType = {
  name = "GFX_MMG_UI_home"
  texturefile = "gfx/event_pictures/mmg_ui_home.dds"
 }
}
'''
    (root / 'interface/MMG_viewer.gfx').write_text(gfx, encoding='utf-8', newline='\n')
    old = root / 'interface/MMG_eventwindow.gfx'
    if old.exists():
        old.unlink()
    buttons = Image.new('RGBA', (1056, 50), (0, 0, 0, 0))
    draw = ImageDraw.Draw(buttons)
    for i, color in enumerate(('#bdb59d', '#cec3a8', '#a2977d')):
        draw.rounded_rectangle((i*352, 0, (i+1)*352-1, 49), 4, fill=color, outline='#72674f', width=1)
    buttons.save(root / 'gfx/interface/mmg_ui_option.dds')
    # Only the 14px grip is painted. The 2px gap and the original 148x34
    # button area stay transparent, keeping the native button skin intact.
    grip = Image.new('RGBA', (164, 34), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grip)
    draw.rounded_rectangle((0, 0, 13, 33), 2, fill='#464c40', outline='#20271e')
    draw.line((2, 1, 11, 1), fill='#858771')
    draw.line((2, 32, 11, 32), fill='#242b20')
    for x in (4, 9):
        for y in (10, 16, 22):
            draw.rectangle((x, y+1, x+1, y+2), fill='#24291f')
            draw.rectangle((x, y, x+1, y+1), fill='#c8c5af')
    grip.save(root / 'gfx/interface/mmg_ui_launcher_grip.dds')
    home = Image.new('RGBA', (720, 450), '#d7ceb5')
    draw = ImageDraw.Draw(home)
    font = font_path()
    draw.rounded_rectangle((8, 8, 711, 441), 12, outline='#665c43', width=2)
    draw.text((26, 18), TEXT['simp_chinese']['home_title'], font=ImageFont.truetype(font, 26), fill='#252b22')
    draw.text((26, 58), TEXT['english']['home_title'], font=ImageFont.truetype(font, 17), fill='#4b4c3d')
    zh = read_localisation(root, 'simp_chinese')
    en = read_localisation(root, 'english')
    for i, (label, _) in enumerate(CHAPTERS):
        draw.text((28, 99+i*46), zh[label], font=ImageFont.truetype(font, 19), fill='#252b22')
        draw.text((28, 123+i*46), en[label], font=ImageFont.truetype(font, 13), fill='#4b4c3d')
    home.save(root / 'gfx/event_pictures/mmg_ui_home.dds')
    if preview_dir:
        preview_dir.mkdir(parents=True, exist_ok=True)
        home.save(preview_dir / 'home.png')
        grip.save(preview_dir / 'launcher-grip.png')
    manifest = {'format': 'isolated scripted GUI', 'pages': pages, 'source_pages': len(pages)-1,
                'private_variables': [PAGE, CHOICES], 'clear_on_close': True,
                'runtime_events': 0, 'runtime_decisions': 0, 'vanilla_overrides': 0}
    (root / 'tools/viewer_source_map.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(f'{root.name}: {len(pages)} GUI pages, 2 private UI variables, 0 loaded events/decisions; no vanilla GUI override.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    build(Path(__file__).resolve().parents[1], args.preview_dir)


if __name__ == '__main__':
    main()
