"""Rebuild guide textures from the original PPT screenshots, never old DDS files."""

import argparse
import io
import json
import math
from pathlib import Path
import zipfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from design_gallery import DESIGN_PICTURES


# IDs refer to ppt/media/imageN.png in the source guide, not slide numbers.
PICTURES = {
    'land_menu': [6, 7, 8, 9],
    'land_main': [6, 7, 8],
    'land_infantry': [12, 13],
    'land_artillery': [15, 16],
    'land_armored': [19, 21],
    'land_operational': [23, 24],
    'land_spirits': [27, 29, 31, 33, 35, 37, 39, 41, 43, 45],
    'naval_menu': [46],
    'naval_main': [46],
    'naval_spirits': [47, 50, 54, 56, 58],
    'air_menu': [59, 60],
    'air_core': [59, 70],
    'air_fighter_cas': [62, 64, 66, 68],
    'air_bombers': [62, 64],
    'army_menu': [71],
    'army_main': [74],
    'army_filler': [77],
    'army_defense': [78],
    'army_support': [85, 93, 95],
    'army_occupation': [110, 115],
    'plane_menu': [148],
    'ship_menu': [133],
}

# Design pages override old collages; each screenshot gets the entire viewport.
PICTURES.update(DESIGN_PICTURES)

SIZE = (720, 450)
GAP = 12


def trim_black(image):
    """Remove only continuous near-black outside margins, not dark UI panels."""
    rgb = image.convert('RGB')
    mask = ImageChops.difference(rgb, Image.new('RGB', rgb.size))
    channels = mask.split()
    mask = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    bounds = mask.point(lambda value: 255 if value > 3 else 0).getbbox()
    if bounds is None:
        raise ValueError('Blank source screenshot')
    return image.convert('RGBA').crop(bounds), bounds


def pack(images):
    # Exhaustive ordered row partitions preserve screenshot reading order.
    best = None
    for breaks in range(1 << (len(images) - 1)):
        rows = [[]]
        for index, im in enumerate(images):
            rows[-1].append(im)
            if index < len(images) - 1 and breaks & (1 << index):
                rows.append([])
        heights = [max(im.height for im in row) for row in rows]
        widths = [sum(im.width for im in row) for row in rows]
        scale = min(
            (SIZE[1] - GAP * (len(rows) - 1)) / sum(heights),
            *( (SIZE[0] - GAP * (len(row) - 1)) / width
               for row, width in zip(rows, widths) ),
        )
        if best is None or scale > best[0]:
            best = scale, rows
    scale, rows = best
    canvas = Image.new('RGBA', SIZE, (0, 0, 0, 0))
    row_heights = [max(max(1, math.floor(im.height * scale)) for im in row) for row in rows]
    y = (SIZE[1] - sum(row_heights) - GAP * (len(rows) - 1)) // 2
    for row, height in zip(rows, row_heights):
        widths = [max(1, math.floor(im.width * scale)) for im in row]
        x = (SIZE[0] - sum(widths) - GAP * (len(row) - 1)) // 2
        for im, width in zip(row, widths):
            resized = im.resize((width, max(1, math.floor(im.height * scale))), Image.Resampling.LANCZOS)
            resized = resized.filter(ImageFilter.UnsharpMask(radius=0.6, percent=70, threshold=3))
            canvas.alpha_composite(resized, (x, y + (height - resized.height) // 2))
            x += width + GAP
        y += height + GAP
    return canvas, scale


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx', type=Path)
    parser.add_argument('--preview-dir', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.preview_dir.mkdir(parents=True, exist_ok=True)
    records = {}
    with zipfile.ZipFile(args.pptx) as archive:
        for name, ids in PICTURES.items():
            images = []
            sources = []
            for media_id in ids:
                member = f'ppt/media/image{media_id}.png'
                override = root / 'tools' / 'sources' / 'tank_medium.png'
                source = override if media_id == 122 and override.exists() else io.BytesIO(archive.read(member))
                with Image.open(source) as original:
                    image, bounds = trim_black(original)
                    images.append(image)
                    sources.append({'media': 'tools/sources/tank_medium.png' if source == override else member,
                                    'source_size': original.size, 'crop': bounds})
            canvas, scale = pack(images)
            canvas.save(root / 'gfx' / 'event_pictures' / f'mmg_{name}.dds')
            canvas.save(args.preview_dir / f'mmg_{name}.png')
            records[name] = {'sources': sources, 'scale': round(scale, 4), 'canvas': SIZE}
    (args.preview_dir / 'source-map.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    names = list(PICTURES)
    for start in range(0, len(names), 10):
        sheet = Image.new('RGB', (720, 5 * 249), '#d7ceb5')
        draw = ImageDraw.Draw(sheet)
        for index, name in enumerate(names[start:start + 10]):
            x, y = index % 2 * 360, index // 2 * 249
            image = Image.open(args.preview_dir / f'mmg_{name}.png')
            image.thumbnail((360, 225), Image.Resampling.LANCZOS)
            sheet.paste(image, (x, y + 24), image)
            draw.text((x + 8, y + 5), name, fill='black')
        sheet.save(args.preview_dir / f'contact-{start // 10 + 1}.jpg', quality=75)
    print(f'Rebuilt {len(records)} RGBA DDS textures at {SIZE[0]}x{SIZE[1]} from PPT originals.')


if __name__ == '__main__':
    main()
