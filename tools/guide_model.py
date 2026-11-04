"""Read the offline guide graph; these files are never installed as events.

The small parser rejects anything beyond inert titles, pictures and page
links. This keeps future content updates from adding gameplay effects to the
viewer compiler. Ordered pairs preserve repeated option blocks.
"""

import json
from pathlib import Path
import re


OFFSETS = {'MMG_guide': 10000, 'MMG_tank': 20000,
           'MMG_infantry': 30000, 'MMG_aircraft': 40000}
CHAPTERS = [
    ('MMG_land_doctrine_decision', 'MMG_guide.100'),
    ('MMG_naval_doctrine_decision', 'MMG_guide.200'),
    ('MMG_air_doctrine_decision', 'MMG_guide.300'),
    ('MMG_army_org_decision', 'MMG_guide.400'),
    ('MMG_tank_design_decision', 'MMG_guide.500'),
    ('MMG_plane_design_decision', 'MMG_guide.600'),
    ('MMG_ship_design_decision', 'MMG_guide.700'),
]


def parse(text):
    tokens = re.findall(r'#[^\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=#]+', text)
    tokens = [t for t in tokens if not t.startswith('#')]
    pos = 0

    def pairs(nested=False):
        nonlocal pos
        result = []
        while pos < len(tokens):
            if tokens[pos] == '}':
                if not nested:
                    raise ValueError('Unexpected closing brace')
                pos += 1
                return result
            key = tokens[pos]
            pos += 1
            if pos >= len(tokens) or tokens[pos] != '=':
                raise ValueError('Expected assignment after ' + key)
            pos += 1
            if pos >= len(tokens):
                raise ValueError('Missing value: ' + key)
            if tokens[pos] == '{':
                pos += 1
                value = pairs(True)
            else:
                value = tokens[pos]
                pos += 1
                if value.startswith('"'):
                    value = json.loads(value)
            result.append((key, value))
        if nested:
            raise ValueError('Unclosed source block')
        return result

    return pairs()


def page_number(ident):
    if ident == 'MMG_UI_HOME':
        return 1
    namespace, number = ident.split('.')
    value = int(number)
    if namespace not in OFFSETS or not 0 <= value < 10000:
        raise ValueError('Invalid guide page ID: ' + ident)
    return OFFSETS[namespace] + value


def load_pages(root):
    pages = []
    for path in sorted((root / 'tools/page_sources').glob('*.mmg')):
        for kind, block in parse(path.read_text(encoding='utf-8')):
            if kind == 'add_namespace':
                if block not in OFFSETS:
                    raise ValueError('Unknown source namespace: ' + block)
                continue
            if kind != 'country_event' or not isinstance(block, list):
                raise ValueError('Unexpected source object: ' + kind)
            fields = {}
            choices = []
            for key, value in block:
                if key == 'option':
                    option = dict(value)
                    if len(option) != len(value) or set(option) - {'name', 'country_event'}:
                        raise ValueError('Unexpected option effects: ' + str(value))
                    target = None
                    if 'country_event' in option:
                        if len(option['country_event']) != 1 or option['country_event'][0][0] != 'id':
                            raise ValueError('Unexpected page link payload')
                        target = option['country_event'][0][1]
                    choices.append({'label': option['name'], 'target': target})
                elif key in {'id', 'title', 'desc', 'picture', 'is_triggered_only'} and key not in fields:
                    if not isinstance(value, str):
                        raise ValueError('Non-scalar page metadata: ' + key)
                    fields[key] = value
                else:
                    raise ValueError('Source contains an unsupported effect or duplicate: ' + key)
            if set(fields) != {'id', 'title', 'desc', 'picture', 'is_triggered_only'} or fields['is_triggered_only'] != 'yes':
                raise ValueError('Incomplete source metadata: ' + str(fields))
            for key in ('title', 'desc'):
                if not re.fullmatch(r'MMG_\w+', fields[key]):
                    raise ValueError('Expected an owned localisation identifier: ' + key)
            if not re.fullmatch(r'GFX_MMG_\w+', fields['picture']):
                raise ValueError('Expected an owned picture identifier')
            for choice in choices:
                if not isinstance(choice['label'], str) or not re.fullmatch(r'MMG_\w+', choice['label']):
                    raise ValueError('Expected an owned option-label identifier')
            if not 1 <= len(choices) <= 8:
                raise ValueError('Invalid choice count: ' + fields['id'])
            pages.append({'id': fields['id'], 'number': page_number(fields['id']),
                          'title': fields['title'], 'description': fields['desc'],
                          'picture': fields['picture'], 'choices': choices,
                          'source': path.relative_to(root).as_posix()})
    ids = {p['id'] for p in pages}
    if len(ids) != len(pages) or len({p['number'] for p in pages}) != len(pages):
        raise ValueError('Duplicate guide source ID')
    for page in pages:
        for choice in page['choices']:
            if choice['target'] and choice['target'] not in ids:
                raise ValueError('Missing page target: ' + choice['target'])
    if any(target not in ids for _, target in CHAPTERS):
        raise ValueError('Missing chapter root')
    home = {'id': 'MMG_UI_HOME', 'number': 1, 'title': 'MMG_UI_home_title',
            'description': 'MMG_UI_home_desc', 'picture': 'GFX_MMG_UI_home',
            'choices': [{'label': label, 'target': target} for label, target in CHAPTERS]
                       + [{'label': 'MMG_UI_close', 'target': None}], 'source': 'generated home'}
    return [home, *sorted(pages, key=lambda p: p['number'])]


def read_localisation(root, language):
    result = {}
    for path in (root / 'localisation' / language).glob('*.yml'):
        for key, value in re.findall(r'^ (\w+): "(.*)"$', path.read_text(encoding='utf-8-sig'), re.M):
            if key in result:
                raise ValueError('Duplicate localisation: ' + language + ' ' + key)
            result[key] = value
    return result


def compile_viewer(root):
    """Finish a source update with its isolated runtime UI, never engine events."""
    # Import at call time: source builders also provide image helpers to the
    # compiler, so eager imports would create a module-import cycle.
    from build_viewer import build
    build(root)
