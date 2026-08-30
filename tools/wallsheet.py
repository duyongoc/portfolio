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
PAD = 5
CELL_AR = 400 / 245                    # one cell's width:height, all three sheets
BAND    = 198 / 245                    # how much of a cell the image band takes

# Reading order is the argument. Row 1 is the three netcode builds, so the rarest
# thing here is the first thing seen; row 2 is the POLYGON trio, and POLYGON
# Battle sits directly under Netcode Battle because it IS that game before it
# went online. Row 3 is everything else. Column 4 takes the odd ones out, where
# the section stripe already marks them as not belonging to the row's trio.
HERO = ['Netcode Battle', 'Netcode Demo', 'Netcode Shooter2D', 'Kinder Easter',
        'POLYGON Battle', 'POLYGON Adventure', 'POLYGON Turnbase', 'Color Shoot 2d',
        'Joust them all', "Beat'em up 2", 'Survivor.io clone 2d']

# The two side columns, on the walls the back wall cannot reach. Each is one
# category so the section stripe reads as a single band down the column — a
# column of mixed stripes looks like leftovers, which is exactly what it would
# be. Picked off a contact sheet at the size they actually render: dark frames
# with a cyan or magenta light in them, which is the room's own palette. The
# prettiest two left in the set, Topdown Sword and Game2d Black Ops, are not
# here because neither has a video, and a cover with no clip is a still in a
# room whose whole readout is motion.
#
# Three each, and that is every remaining title that survives being baked into
# a preview and looked at. Eleven were baked and nine rejected; SKIP in
# tools/clips.py records each one and why. Two of the nine were later found to
# be my own mistake rather than the game's — Battle Board 2d and Game 2d5
# Dungeon both open on a menu, so the default offset judged the menu. Sampling
# four points across each found gameplay. The cheap check and the right check
# disagree often enough here that the cheap one is not worth doing.
LEFT  = ["Beat'em up", 'Topdown Shooter', 'Game 2d5 Dungeon']       # zone 8
RIGHT = ['Game Runner 3d', 'Cardgame Battle 2d', 'Battle Board 2d'] # zone 9

SHEETS = [
    # name,          titles, cols, rows, cell width px, count plate
    ('wall',         HERO,   4, 3, 400, True),
    ('wall-left',    LEFT,   1, 3, 560, False),
    ('wall-right',   RIGHT,  1, 3, 560, False),
]

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


def bake(name, titles, cols, rows, cw, plate, games, by_title):
    """One sheet. The cell aspect is fixed, so the sheet's aspect follows from
    the grid — which is what keeps a baked sheet square with the plane it is
    mapped onto, whatever shape that plane is."""
    ch = round(cw / CELL_AR)
    tile_h = round(ch * BAND)
    W, H = cols * cw, rows * ch

    picked, missing = [], []
    for t in titles:
        (picked if t in by_title else missing).append(by_title.get(t, t))
    if missing:
        print('%s: not in portfolio-data.js: %s' % (name, missing), file=sys.stderr)
        # a hole would shift every later cell against the hover grid, so refuse
        return None
    cap = cols * rows - (1 if plate else 0)
    if len(picked) > cap:
        print('%s: %d titles will not fit %dx%d' % (name, len(picked), cols, rows), file=sys.stderr)
        return None

    sheet = Image.new('RGB', (W, H), (10, 14, 24))
    d = ImageDraw.Draw(sheet)
    # type scales with the cell, so a one-column sheet is not set in 4-column type
    k = cw / 400
    f_title, f_num = font(round(26 * k), True), mono(round(17 * k), True)
    f_big, f_sub, f_tag = font(64, True), mono(19), mono(15)

    for i, g in enumerate(picked):
        cx, cy = (i % cols) * cw, (i // cols) * ch
        col = SEC.get(g['section'], (136, 153, 187))
        d.rectangle([cx + PAD, cy + PAD, cx + cw - PAD, cy + ch - PAD], fill=(12, 17, 32))

        # the thumbnail, cropped to the tile band rather than squashed into it
        try:
            im = Image.open(thumb_path(g['info'])).convert('RGB')
        except Exception:
            im = Image.new('RGB', (160, 100), (18, 24, 44))
        tw, th = cw - PAD * 2, tile_h
        sc = max(tw / im.width, th / im.height)
        im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.LANCZOS)
        ox, oy = (im.width - tw) // 2, (im.height - th) // 2
        sheet.paste(im.crop((ox, oy, ox + tw, oy + th)), (cx + PAD, cy + PAD))

        # section stripe along the top edge, index and title under the image
        d.rectangle([cx + PAD, cy + PAD, cx + cw - PAD, cy + PAD + round(5 * k)], fill=col)
        ty = cy + PAD + tile_h
        d.rectangle([cx + PAD, ty, cx + cw - PAD, cy + ch - PAD], fill=(9, 13, 26))
        d.text((cx + round(16 * k), ty + round(8 * k)), '%02d' % (games.index(g) + 1),
               font=f_num, fill=col)
        nm = g['title']
        while d.textlength(nm, font=f_title) > cw - round(80 * k) and len(nm) > 4:
            nm = nm[:-1]
        if nm != g['title']:
            nm += '…'
        d.text((cx + round(52 * k), ty + round(5 * k)), nm, font=f_title, fill=(223, 233, 255))

    if plate:
        # the last cell carries the number the grid stopped showing
        x0, y0 = (len(picked) % cols) * cw, (len(picked) // cols) * ch
        d.rectangle([x0 + PAD, y0 + PAD, W - PAD, H - PAD], fill=(9, 13, 26))
        d.rectangle([x0 + PAD, y0 + PAD, W - PAD, y0 + PAD + 5], fill=(90, 208, 255))
        d.text((x0 + 26, y0 + 46), '%d' % len(games), font=f_big, fill=(223, 233, 255))
        d.text((x0 + 28, y0 + 124), 'SHIPPED TITLES', font=f_sub, fill=(90, 208, 255))
        d.text((x0 + 28, y0 + 160), 'UNITY · UNREAL', font=f_tag, fill=(120, 140, 170))
        d.text((x0 + 28, y0 + 184), 'C# · C++ · 2019—', font=f_tag, fill=(120, 140, 170))

    out = os.path.join(ROOT, 'demos/models/%s.jpg' % name)
    sheet.save(out, 'JPEG', quality=84, optimize=True)
    print('%-28s %4dx%-4d  %dx%d  %2d tiles%s  %4.0f kB  aspect %.3f'
          % (out.replace(ROOT + '/', ''), W, H, cols, rows, len(picked),
             ' + plate' if plate else '        ', os.path.getsize(out) / 1024, W / H))
    return True


def main():
    src = open(os.path.join(ROOT, 'demos/portfolio-data.js')).read()
    games = json.loads(src[src.index('['):src.rindex(']') + 1])
    by_title = {g['title']: g for g in games}
    ok = [bake(n, t, c, r, cw, p, games, by_title) for n, t, c, r, cw, p in SHEETS]
    return 0 if all(ok) else 1


if __name__ == '__main__':
    sys.exit(main())
