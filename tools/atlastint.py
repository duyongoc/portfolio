#!/usr/bin/env python3
"""Pull the yellow out of the Synty atlases, then resize them to 1024px.

The POLYGON packs colour a model by pointing its UVs at flat swatches in a
shared atlas, and the swatch the furniture lands on is a saturated
yellow-orange. In a room lit cyan and magenta that reads as a construction
site, and worse, the loudest thing on screen ends up being a side table nobody
can click.

Rather than tint the whole texture — which would drag the signage and the
screens along with it — this walks the UVs of the models the room actually
places, collects only the texels those models sample, and rotates just the
yellow ones toward steel. Signage the room never shows keeps its colour.

Then both atlases go from their source resolution to exactly 1024. The swatches
are flat, so NEAREST cannot blend across a swatch boundary; 2 MB of texture
becomes about 600 kB. An atlas already at 1024 skips only the resize, not the
tint: adding a prop to USES has to be able to reach the swatches that prop is
the first to sample. Re-running is still safe — restyle() lands on hue
200-222 deg, outside the window is_yellow() tests, so a tinted swatch is never
tinted twice and a run with nothing new to do rewrites nothing.

    python3 tools/atlastint.py
"""
import colorsys, json, os, struct, sys
from collections import Counter
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, 'demos/models')

# which atlas each model draws from, matching the room's prop() calls
USES = {'cybercity': ['desk', 'chair2', 'keyboard', 'mouse', 'mousepad',
                      'planter', 'shelf', 'sidetable', 'console', 'crate',
                      'bin', 'vending'],
        'scifi': ['sofa', 'locker', 'plant', 'plant2', 'bloom']}
TARGET_SIZE = 1024

# hue window counted as "the offending yellow", in degrees
HUE_LO, HUE_HI = 18, 68
SAT_MIN, VAL_MIN = .30, .28

COMP = {'f': 4, 'd': 8, 'b': 1, 'B': 1, 'h': 2, 'H': 2, 'i': 4, 'I': 4}
CTYPE = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read_glb(path):
    """Minimal GLB reader — just enough to get TEXCOORD_0 out."""
    b = open(path, 'rb').read()
    assert b[:4] == b'glTF', path
    off, js, bins = 12, None, b''
    while off < len(b):
        ln, kind = struct.unpack_from('<II', b, off)
        chunk = b[off + 8: off + 8 + ln]
        if kind == 0x4E4F534A:
            js = json.loads(chunk.decode('utf-8').rstrip(' \0'))
        elif kind == 0x004E4942:
            bins = chunk
        off += 8 + ln + ((4 - ln % 4) % 4 if ln % 4 else 0)
    return js, bins


def accessor(g, bins, idx):
    a = g['accessors'][idx]
    bv = g['bufferViews'][a['bufferView']]
    fmt = CTYPE[a['componentType']]
    n = NCOMP[a['type']]
    stride = bv.get('byteStride') or COMP[fmt] * n
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    out = []
    for i in range(a['count']):
        out.append(struct.unpack_from('<' + fmt * n, bins, base + i * stride))
    return out


def sampled_texels(name, size):
    """Every atlas texel touched by this model's UVs, as a Counter."""
    path = os.path.join(MODELS, name + '.glb')
    if not os.path.exists(path):
        return Counter()
    g, bins = read_glb(path)
    hits = Counter()
    for mesh in g.get('meshes', []):
        for prim in mesh['primitives']:
            uv = prim['attributes'].get('TEXCOORD_0')
            if uv is None:
                continue
            for u, v in accessor(g, bins, uv):
                x = min(size - 1, max(0, int(u * size)))
                y = min(size - 1, max(0, int(v * size)))
                hits[(x, y)] += 1
    return hits


def is_yellow(rgb):
    r, g, b = [c / 255 for c in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return HUE_LO <= h * 360 <= HUE_HI and s >= SAT_MIN and v >= VAL_MIN


def restyle(rgb):
    """Yellow -> steel blue, keeping the swatch's own light/dark relationship
    so the model's shading ladder survives the swap."""
    r, g, b = [c / 255 for c in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    t = (h * 360 - HUE_LO) / (HUE_HI - HUE_LO)      # 0 at red-orange, 1 at lime
    nh = (200 + t * 22) / 360                        # 200°..222°, steel -> indigo
    ns = min(.62, s * .78)
    nv = v * .93
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(nh, ns, nv))


def main():
    for atlas, names in USES.items():
        src = os.path.join(MODELS, atlas + '.png')
        if not os.path.exists(src):
            print('skip %s (missing)' % atlas)
            continue
        im = Image.open(src).convert('RGB')
        if im.width != im.height:
            print('%s: expected a square atlas, got %dx%d' %
                  (atlas, im.width, im.height), file=sys.stderr)
            return 1
        size = im.width
        if size < TARGET_SIZE:
            print('%s: refusing to upscale %dx%d atlas' % (atlas, size, size),
                  file=sys.stderr)
            return 1
        px = im.load()

        hits = Counter()
        for n in names:
            hits += sampled_texels(n, size)
        if not hits:
            print('%s: no models sampled, left alone' % atlas)
            continue

        # collect the distinct colours those models actually land on
        colours = Counter()
        for (x, y), c in hits.items():
            colours[px[x, y]] += c
        remap = {c: restyle(c) for c in colours if is_yellow(c)}
        print('%s: %d texels sampled, %d distinct colours, %d yellow -> remapped'
              % (atlas, len(hits), len(colours), len(remap)))
        for c in sorted(remap, key=lambda c: -colours[c])[:6]:
            print('   %-16s -> %-16s (%d refs)' % (c, remap[c], colours[c]))

        # apply the remap across the whole atlas so neighbouring texels inside
        # the same flat swatch move together and no seam appears at the edge
        if remap:
            data = list(im.getdata())
            im.putdata([remap.get(p, p) for p in data])
        elif size == TARGET_SIZE:
            print('   already %d and nothing left to remap, untouched' % size)
            continue

        if size != TARGET_SIZE:
            im = im.resize((TARGET_SIZE, TARGET_SIZE), Image.NEAREST)
        im.save(src, 'PNG', optimize=True)
        print('   %d -> %d, %.0f kB' % (size, TARGET_SIZE, os.path.getsize(src) / 1024))


if __name__ == '__main__':
    sys.exit(main())
