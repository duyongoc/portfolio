#!/usr/bin/env python3
"""Bake demos/models/og.jpg — the picture that appears when the link is shared.

Every scraper wants 1200x630, and it wants an absolute URL, and it will not run
JavaScript to find out what the page looks like. So the preview for a portfolio
whose entire point is a rendered room has to be a rendered frame, baked ahead
of time.

The source is a real capture of the room with the interface hidden, taken at
20:36 — late enough that the city outside has its lights on, early enough that
the sky is still readable as sky. Re-shoot it with:

    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \\
      --headless=new --disable-gpu-sandbox --enable-unsafe-swiftshader \\
      --use-gl=angle --use-angle=swiftshader --window-size=1600,900 \\
      --virtual-time-budget=26000 --screenshot=tools/og-source.png \\
      "http://127.0.0.1:8000/room-3d.html#t=20.6"

(with #ui hidden, or simply accept the chrome — it is the same room either
way), then:

    python3 tools/ogimage.py [source.png]
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools/og-source.png')
OUT = os.path.join(ROOT, 'demos/models/og.jpg')
W, H = 1200, 630
CY, ACC, INK = (90, 208, 255), (255, 90, 160), (233, 243, 251)


def font(size, bold=False):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else
              '/System/Library/Fonts/Supplemental/Arial.ttf',
              '/System/Library/Fonts/Helvetica.ttc'):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()


def mono(size):
    for p in ('/System/Library/Fonts/Menlo.ttc', '/System/Library/Fonts/Courier.ttc'):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return font(size)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    if not os.path.exists(src):
        print('no source frame at %s — see the docstring' % src, file=sys.stderr)
        return 1
    im = Image.open(src).convert('RGB')

    # cover-crop to 1200x630 rather than squash. Biased above centre: the wall
    # of games and the skyline are the top two thirds, the floor is the bottom.
    sc = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    ox = (im.width - W) // 2
    oy = min(im.height - H, max(0, int((im.height - H) * .38)))
    card = im.crop((ox, oy, ox + W, oy + H))

    # a soft floor for the type to sit on, so the caption survives whatever the
    # frame happens to be doing down there
    d = ImageDraw.Draw(card, 'RGBA')
    band = Image.new('L', (1, H), 0)
    for y in range(H):
        t = max(0.0, (y - H * .52) / (H * .48))
        band.putpixel((0, y), int(232 * t * t))
    shade = Image.new('RGB', (W, H), (3, 6, 13))
    card.paste(shade, (0, 0), band.resize((W, H)).filter(ImageFilter.GaussianBlur(1)))

    d.rectangle([0, 0, W, 5], fill=CY)
    d.rectangle([0, H - 5, W, H], fill=ACC)

    x, y = 62, H - 214
    d.ellipse([x, y + 5, x + 11, y + 16], fill=CY)
    d.text((x + 24, y + 2), 'PORTFOLIO // THE ROOM', font=mono(17), fill=CY)
    d.text((x, y + 36), 'O Ngoc Duy', font=font(76, True), fill=INK)
    d.text((x + 3, y + 126), 'Unity Game Developer', font=font(30), fill=(196, 214, 236))

    facts = [('33', 'SHIPPED'), ('6+', 'YEARS'), ('4', 'STUDIOS')]
    fx = W - 62
    for big, small in reversed(facts):
        wb = d.textlength(big, font=font(44, True))
        ws = d.textlength(small, font=mono(14))
        col = max(wb, ws)
        d.text((fx - col, H - 128), big, font=font(44, True), fill=INK)
        d.text((fx - col, H - 74), small, font=mono(14), fill=CY)
        fx -= col + 46

    card.save(OUT, 'JPEG', quality=88, optimize=True)
    print('%s  %dx%d  %.0f kB' % (OUT, W, H, os.path.getsize(OUT) / 1024))


if __name__ == '__main__':
    sys.exit(main())
