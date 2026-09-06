#!/usr/bin/env python3
"""Bake the desk ID badge — the one place a real photo appears in the room.

Drawn here rather than in a runtime canvas because the photo has to be fetched
either way, and an image that arrives half a second after the texture is built
is the bug that made every Synty prop render black. One JPEG, one request, and
the type is laid out at a fixed size instead of scaling with the card.

The source is a candid at a desk, not a studio headshot. Badge and panel must
use the exact same square portrait crop: rendering two independent crops made
the identity card look like a different photo when it opened.

    python3 tools/badge.py
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# images/user-3.png, not images/user.jpg. Both are 636x553 and the same frame,
# but the PNG is the lossless master the JPEG was encoded from (PSNR 45.6 dB
# between them). Nothing here is served straight to a browser — every output is
# cropped and then upscaled 2-3x — so starting from the master keeps one
# generation of JPEG ringing out of a picture that gets magnified afterwards.
SRC = os.path.join(ROOT, 'images/user-3.png')
OUT = os.path.join(ROOT, 'demos/models/badge.jpg')
PLATE = os.path.join(ROOT, 'demos/models/portrait.jpg')

W, H = 704, 400                     # the card is 4.4 x 2.5 world units
FACE = (272, 74, 468, 322)          # head-and-shoulders box in the source
AVATAR_SIZE = 768                    # large enough for the 1/3-panel portrait
# The contact panel's left third is a full-height plate, not a circle. It is
# baked at 0.719 while the plate displays at ~0.615, on purpose: an image cut to
# exactly the box's aspect gives object-fit:cover nothing to crop, which makes
# object-position inert and the framing unadjustable in CSS. The 14% of extra
# width is the slack that lets the subject be nudged across the plate.
# Vertically it stops at y=430 of 553 — below that is the white tablecloth,
# which is the brightest thing in the source and would own the bottom third of
# the panel.
PLATE_W, PLATE_H = 604, 840
PLATE_TOP, PLATE_BOT = 10, 430
INK, DIM, CY, AC = (233, 243, 251), (142, 164, 184), (90, 208, 255), (255, 90, 160)


def font(size, bold=False):
    for p in (('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf'),
              '/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else
              '/System/Library/Fonts/Supplemental/Arial.ttf',
              '/System/Library/Fonts/Menlo.ttc',
              '/System/Library/Fonts/Helvetica.ttc'):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()


def mono(size):
    for p in ('C:/Windows/Fonts/consola.ttf', 'C:/Windows/Fonts/cour.ttf',
              '/System/Library/Fonts/Menlo.ttc', '/System/Library/Fonts/Courier.ttc'):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return font(size)


def portrait_crop():
    """Return the single square crop used by every profile surface.

    The half-width is a fraction of the face box, and 47% was too tight: at
    that size the head filled the circle edge to edge with the hair clipped at
    the top, which reads as a photo somebody zoomed into rather than a
    portrait. 64% is the widest crop the source still supports — beyond ~70%
    the box runs off the top of images/user.jpg and the subject drifts left of
    centre against empty curtain. It also takes 316 source pixels instead of
    232, so the upscale to AVATAR_SIZE is 2.4x rather than 3.3x."""
    im = Image.open(SRC).convert('RGB')
    cx = (FACE[0] + FACE[2]) // 2
    cy = FACE[1] + (FACE[3] - FACE[1]) * 42 // 100
    half = (FACE[3] - FACE[1]) * 64 // 100
    box = (max(0, cx - half), max(0, cy - half),
           min(im.width, cx + half), min(im.height, cy + half))
    return im.crop(box)


def plate_crop():
    """The tall crop for the contact panel's portrait plate.

    Same horizontal centre as portrait_crop, so the badge on the desk and the
    panel it opens still read as one photograph — only the frame differs.
    """
    im = Image.open(SRC).convert('RGB')
    h = PLATE_BOT - PLATE_TOP
    w = round(h * PLATE_W / PLATE_H)
    cx = (FACE[0] + FACE[2]) // 2
    left = max(0, min(im.width - w, cx - w // 2))
    return im.crop((left, PLATE_TOP, left + w, PLATE_BOT))


def main():
    try:
        portrait = portrait_crop()
        plate = plate_crop()
    except Exception as e:
        print('portrait failed: %s' % e, file=sys.stderr)
        return 1

    # The DOM portrait is intentionally larger than the old 256 px thumbnail:
    # it can occupy roughly one third of a projected panel without upscaling.
    out2 = os.path.join(ROOT, 'demos/models/avatar.jpg')
    portrait.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS).save(
        out2, 'JPEG', quality=90, optimize=True, subsampling=0)

    plate.resize((PLATE_W, PLATE_H), Image.LANCZOS).save(
        PLATE, 'JPEG', quality=90, optimize=True, subsampling=0)

    card = Image.new('RGB', (W, H), (13, 20, 34))
    d = ImageDraw.Draw(card)

    # header band and the cut corner that everything else in the room shares
    d.rectangle([0, 0, W, 46], fill=(9, 14, 26))
    d.rectangle([0, 0, W, 4], fill=AC)
    d.text((22, 15), 'ACCESS CARD', font=mono(17), fill=CY)
    d.text((W - 200, 15), 'CLEARANCE  L3', font=mono(17), fill=DIM)

    # The badge uses the same crop and circular silhouette as the opened panel.
    # Only the rendered size changes; the visible portrait does not.
    pw = ph = 224
    px, py = 18, 82
    badge_portrait = portrait.resize((pw, ph), Image.LANCZOS)
    mask = Image.new('L', (pw, ph), 0)
    ImageDraw.Draw(mask).ellipse((1, 1, pw - 2, ph - 2), fill=255)
    card.paste(badge_portrait, (px, py), mask)
    d.ellipse([px - 2, py - 2, px + pw + 1, py + ph + 1], outline=AC, width=3)

    tx = px + pw + 30
    d.text((tx, 78), 'O NGOC DUY', font=font(42, True), fill=INK)
    d.text((tx + 2, 130), 'UNITY  GAME  DEVELOPER', font=mono(18), fill=CY)

    rows = [('ID', '2019-0714'), ('DEPT', 'GAMEPLAY / NETCODE'),
            ('SINCE', '2019'), ('MAIL', 'ongocduy.dev@gmail.com')]
    y = 176
    for k, v in rows:
        d.text((tx, y), k, font=mono(14), fill=(85, 105, 124))
        d.text((tx + 62, y - 1), v, font=mono(15), fill=DIM)
        y += 27

    # barcode: deterministic widths so re-runs produce an identical card
    bx, by, bh = tx, 300, 34
    seed = 7
    while bx < W - 40:
        seed = (seed * 16807) % 2147483647
        w = 2 + (seed % 4)
        if seed % 3:
            d.rectangle([bx, by, bx + w, by + bh], fill=(190, 214, 236))
        bx += w + 2 + (seed >> 8) % 3
    d.text((tx, by + bh + 8), 'HO CHI MINH CITY', font=mono(13), fill=(85, 105, 124))

    card.save(OUT, 'JPEG', quality=90, optimize=True, subsampling=0)
    print('%s  %dx%d  %.0f kB' % (OUT, W, H, os.path.getsize(OUT) / 1024))
    print('%s  %dx%d  %.0f kB' %
          (out2, AVATAR_SIZE, AVATAR_SIZE, os.path.getsize(out2) / 1024))
    print('%s  %dx%d  %.0f kB  (source crop %dx%d)' %
          (PLATE, PLATE_W, PLATE_H, os.path.getsize(PLATE) / 1024,
           plate.width, plate.height))


if __name__ == '__main__':
    sys.exit(main())
