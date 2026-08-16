#!/usr/bin/env python3
"""Bake the wall display behind the desk into one image.

The wall panel used to be a canvas of flat coloured rectangles because pulling
33 separate <img> files at runtime costs 33 requests and about a megabyte for
something that is wall decoration. Baking them here gives one JPEG and one
request, and the tiles become the actual game art.

The first version put all 33 on the wall in an 8x5 grid. Measured at the room's
default framing, the panel spans about 370 screen pixels, which made each tile
roughly 44x32 — below the size at which a screenshot is a screenshot. It read
as a mosaic texture. Eleven tiles in a 4x3 grid put each one at about 92 px
instead, which is enough to recognise a game, and the twelfth cell states the
count that the grid no longer shows. The full 33 are one click away in the
panel the wall opens, where they get 300 px each.

    python3 tools/wallsheet.py
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS, ROWS = 4, 3
CW, CH = 400, 245                      # cell size in px
TILE_H = 198                           # image band; the rest is the caption
PAD = 5
W, H = COLS * CW, ROWS * CH            # 1600 x 735  ->  2.177, panel is 2.18

# The eleven that survive being seen small: readable silhouettes, strong colour,
# and between them one of each thing I actually do.
HERO = ['Netcode Battle', 'POLYGON Battle', 'Kinder Easter', 'POLYGON Adventure',
        'Netcode Shooter2D', 'POLYGON Turnbase', 'Joust them all', 'Netcode Demo',
        "Beat'em up 2", 'Color Shoot 2d', 'Survivor.io clone 2d']

# One arc from cyan to magenta, four even stops. The old set had an amber and a
# mint in it, and two hues sitting outside the room's range are what made a
# wall of small tiles read as confetti rather than as a shelf of games.
SEC = {'Multiplayer Games': (90, 208, 255), 'MY GAMES': (125, 119, 247),
       'RESKIN': (223, 127, 245), 'AR Games': (255, 89, 158)}


def font(size, bold=False):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else
              '/System/Library/Fonts/Supplemental/Arial.ttf',
              '/System/Library/Fonts/Helvetica.ttc'):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()


def mono(size, bold=False):
    for p in ('/System/Library/Fonts/Menlo.ttc', '/System/Library/Fonts/Courier.ttc'):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return font(size, bold)


def thumb_path(p):
    p = p.replace('../images/', 'images/thumb/')
    return os.path.join(ROOT, re.sub(r'\.(jpe?g|png)$', '.jpg', p, flags=re.I))


def main():
    src = open(os.path.join(ROOT, 'demos/portfolio-data.js')).read()
    games = json.loads(src[src.index('['):src.rindex(']') + 1])
    by_title = {g['title']: g for g in games}

    picked, missing = [], []
    for t in HERO:
        (picked if t in by_title else missing).append(by_title.get(t, t))
    if missing:
        print('not in portfolio-data.js: %s' % missing, file=sys.stderr)
        # fall back to filling from the front rather than leaving holes
        for g in games:
            if len(picked) >= COLS * ROWS - 1: break
            if g not in picked: picked.append(g)
    picked = picked[:COLS * ROWS - 1]

    sheet = Image.new('RGB', (W, H), (10, 14, 24))
    d = ImageDraw.Draw(sheet)
    f_title, f_num, f_sec = font(26, True), mono(17, True), mono(14)
    f_big, f_sub, f_tag = font(64, True), mono(19), mono(15)

    for i, g in enumerate(picked):
        cx, cy = (i % COLS) * CW, (i // COLS) * CH
        col = SEC.get(g['section'], (136, 153, 187))
        d.rectangle([cx + PAD, cy + PAD, cx + CW - PAD, cy + CH - PAD], fill=(12, 17, 32))

        # the thumbnail, cropped to the tile band rather than squashed into it
        try:
            im = Image.open(thumb_path(g['info'])).convert('RGB')
        except Exception:
            im = Image.new('RGB', (160, 100), (18, 24, 44))
        tw, th = CW - PAD * 2, TILE_H
        sc = max(tw / im.width, th / im.height)
        im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.LANCZOS)
        ox, oy = (im.width - tw) // 2, (im.height - th) // 2
        sheet.paste(im.crop((ox, oy, ox + tw, oy + th)), (cx + PAD, cy + PAD))

        # section stripe along the top edge, index and title under the image
        d.rectangle([cx + PAD, cy + PAD, cx + CW - PAD, cy + PAD + 5], fill=col)
        ty = cy + PAD + TILE_H
        d.rectangle([cx + PAD, ty, cx + CW - PAD, cy + CH - PAD], fill=(9, 13, 26))
        d.text((cx + 16, ty + 8), '%02d' % (games.index(g) + 1), font=f_num, fill=col)
        name = g['title']
        while d.textlength(name, font=f_title) > CW - 80 and len(name) > 4:
            name = name[:-1]
        if name != g['title']:
            name += '…'
        d.text((cx + 52, ty + 5), name, font=f_title, fill=(223, 233, 255))

    # the last cell carries the number the grid stopped showing
    x0, y0 = (len(picked) % COLS) * CW, (len(picked) // COLS) * CH
    d.rectangle([x0 + PAD, y0 + PAD, W - PAD, H - PAD], fill=(9, 13, 26))
    d.rectangle([x0 + PAD, y0 + PAD, W - PAD, y0 + PAD + 5], fill=(90, 208, 255))
    d.text((x0 + 26, y0 + 46), '%d' % len(games), font=f_big, fill=(223, 233, 255))
    d.text((x0 + 28, y0 + 124), 'SHIPPED TITLES', font=f_sub, fill=(90, 208, 255))
    d.text((x0 + 28, y0 + 160), 'UNITY · UNREAL', font=f_tag, fill=(120, 140, 170))
    d.text((x0 + 28, y0 + 184), 'C# · C++ · 2019—', font=f_tag, fill=(120, 140, 170))

    out = os.path.join(ROOT, 'demos/models/wall.jpg')
    sheet.save(out, 'JPEG', quality=84, optimize=True)
    print('%s  %dx%d  %d tiles + count plate  %.0f kB'
          % (out, W, H, len(picked), os.path.getsize(out) / 1024))


if __name__ == '__main__':
    sys.exit(main())
