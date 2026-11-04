"""Bake the isolated viewer's fixed paper frame from installed vanilla artwork.

Usage: python tools/build_event_window_background.py GAME_ROOT [--preview-dir DIR]
The 1140x680 frame belongs only to MMG_UI_Viewer. This helper emits an owned
texture, never an EventWindow definition. Slicing is done before generation.
"""

import argparse
from pathlib import Path

from PIL import Image


SIZE = (1140, 680)


def nine_slice(image, size, border):
    """Preserve source edges while stretching the paper center offline."""
    width, height = size
    bx, by = border
    xs = (0, bx, image.width - bx, image.width)
    ys = (0, by, image.height - by, image.height)
    dx = (0, bx, width - bx, width)
    dy = (0, by, height - by, height)
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    for row in range(3):
        for col in range(3):
            part = image.crop((xs[col], ys[row], xs[col + 1], ys[row + 1]))
            part = part.resize((dx[col + 1] - dx[col], dy[row + 1] - dy[row]), Image.Resampling.LANCZOS)
            canvas.paste(part, (dx[col], dy[row]))
    return canvas


def header(image, width, height):
    # Preserve the center clip and side edges. Stretch only the two plain
    # shoulder regions; stretching the whole header would widen the clip.
    anchors = (0, 40, 225, 356, image.width - 40, image.width)
    center = anchors[3] - anchors[2]
    left = (width - 80 - center) // 2
    widths = (40, left, center, width - 80 - center - left, 40)
    result = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    x = 0
    for index, target_width in enumerate(widths):
        part = image.crop((anchors[index], 0, anchors[index + 1], image.height))
        part = part.resize((target_width, height), Image.Resampling.LANCZOS)
        result.paste(part, (x, 0))
        x += target_width
    return result


def body(image, width, height):
    # The vanilla body is only 66px tall. Mirror-repeat it vertically instead
    # of stretching its grain over 531px, which produces visible streaks.
    strip = nine_slice(image, (width, image.height), (20, 16))
    canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    for row, y in enumerate(range(0, height, strip.height)):
        tile = strip if row % 2 == 0 else strip.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        canvas.paste(tile.crop((0, 0, width, min(strip.height, height - y))), (0, y))
    return canvas


def build(game_root, root, preview_dir=None):
    source = game_root / 'gfx/interface'
    inputs = {
        'header': ('event_report_top_win.dds', (581, 121)),
        'body': ('event_report_tileable_midsection.dds', (580, 66)),
        'footer': ('event_report_bottom_win_2.dds', (581, 59)),
    }
    images = {}
    for key, (name, expected_size) in inputs.items():
        with Image.open(source / name) as original:
            if original.size != expected_size:
                raise ValueError(f'Review updated vanilla artwork: {name}: {original.size} != {expected_size}')
            images[key] = original.convert('RGBA')
    canvas = Image.new('RGBA', SIZE, (0, 0, 0, 0))
    canvas.paste(header(images['header'], 1140, 90), (0, 0))
    canvas.paste(body(images['body'], 1140, 531), (0, 90))
    canvas.paste(nine_slice(images['footer'], (1140, 59), (20, 16)), (0, 621))
    output = root / 'gfx/interface/mmg_eventwindow_background.dds'
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    if preview_dir:
        preview_dir.mkdir(parents=True, exist_ok=True)
        canvas.save(preview_dir / 'unified-background.png')
    print(f'{root.name}: one {SIZE[0]}x{SIZE[1]} private viewer frame; footer baked at y=621..679.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_root', type=Path)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    build(args.game_root.resolve(), args.root.resolve(), args.preview_dir)


if __name__ == '__main__':
    main()
