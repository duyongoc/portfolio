#!/usr/bin/env python3
"""Dense Sketchfab sculpts -> the .glb files the room actually loads.

Two props come from Sketchfab and both arrive far too heavy for a page that
budgets its whole model payload in hundreds of kilobytes:

    python3 tools/sculptglb.py cat   SRC.glb demos/models/sofacat.glb
    python3 tools/sculptglb.py plush SRC.glb demos/models/chairplush.glb

Any profile setting can be overridden from the command line for a sweep, which
is how the gamma and contrast below were chosen:

    python3 tools/sculptglb.py cat SRC.glb out.glb gamma=0.6 contrast=1.5

`cat` is "Sitting cat (British Shorthair Blue Cat)" by 3D Creator, CC-BY-4.0:
6.6 MB, 74,586 triangles, a tangent buffer, four byte-identical UV sets and
three 1024 square maps. Out: 5,566 triangles and one lifted 512 square sheet.

`plush` is "Cute Penguin 9th May 2020" by Felix_Lim, CC-BY-4.0: 3.6 MB,
111,552 triangles across eight ZBrush subtools, no texture at all — every bit
of its colour is in COLOR_0. Out: 1,672 triangles and no image whatsoever.

Both reach meshoptimizer through @gltf-transform/cli, which npx fetches per
run, so there is nothing to install:

    npx --yes @gltf-transform/cli@4 <command>

This is a build-time fetch. Nothing in the room fetches anything from a third
party at runtime.

The order of the steps is not arbitrary.

1. **Strip first, simplify second.** meshoptimizer will not collapse an edge
   across a discontinuity in any attribute it is given, so every attribute
   carried into the simplifier is another constraint on it. Dropping the
   *normals* is the one that matters, because both sculpts are split for hard
   normals almost everywhere. On the cat, with normals in, the simplifier
   bottoms out at 7,050 triangles no matter how far the error bound is opened;
   without them it reaches 5,566. Nothing downstream misses them: the room
   recomputes normals on everything it cuts.

2. **Give the simplifier one primitive to work on.** The penguin ships as
   eight subtools under eight materials that differ only in a glossiness the
   room's `MeshLambertMaterial` cannot read. Forcing them all to one material
   lets `join` merge them into a single primitive; simplified separately, the
   eight would each keep their own boundary and the seams between them would
   be locked.

3. **Know which floor you are hitting.** The penguin has no UVs and goes as
   low as asked. The cat cannot: 62,074 vertices for 37,295 positions, and an
   exact weld merges 22 of them, because its sheet is an auto-packed atlas of
   several hundred small charts and a quarter of its vertices sit on a seam.
   5,566 triangles is where that stops and no tolerance goes below it. Lower
   would mean giving up the texture, and the texture is why that model was
   picked.

4. **Bake the node transform.** Sketchfab wraps its exports in a chain of
   frame-conversion matrices; `flatten` collapses them onto the mesh node but
   does not touch the vertex data. This writes it into the positions, so both
   shipped files are Y-up with an identity node. Neither is re-centred: the
   cat happens to sit with its feet on y=0 and the penguin does not, so the
   room seats both by measuring, never by trusting the origin.

5. **Lift the cat's texture.** That sheet is photogrammetry with the lighting
   baked in — mean luminance 67 of 255, maximum 194. A British Shorthair blue
   is a light silver-grey, and left alone it renders as a black lump on a
   mid-blue sofa. Gamma rather than a linear gain, so the lift lands on the
   midtones and the ear interiors and the pupils stay dark. Gamma alone
   flattens the fur, though — it pulls the darks up faster than the lights —
   so a contrast term about the midpoint puts the markings back. CONTRAST=1.0
   is gamma only.

6. **Quantise the penguin's colours.** They arrive as float32 VEC4, sixteen
   bytes a vertex for values that came off a colour picker. Normalised
   unsigned bytes are four, and glTF and three.js both read them natively.
"""

import io, json, os, struct, subprocess, sys, tempfile
import numpy as np
from PIL import Image

GLTF = ['npx', '--yes', '@gltf-transform/cli@4']

# cat: one lifted base-colour sheet. CONTRAST is applied about the midpoint
# after the gamma, because gamma alone pulls the darks up faster than the
# lights and the fur markings wash out.
CAT = dict(size=512, quality=78, gamma=0.55, contrast=1.30, ratio=0.02, error=0.02)
# plush: no image at all, and low enough that nothing is gained by going lower
PLUSH = dict(ratio=0.015, error=0.02)


def load(path):
    f = open(path, 'rb')
    magic, ver, total = struct.unpack('<III', f.read(12))
    assert magic == 0x46546C67, 'not a .glb'
    js = bin = None
    while f.tell() < total:
        ln, ty = struct.unpack('<II', f.read(8))
        data = f.read(ln)
        if ty == 0x4E4F534A: js = json.loads(data)
        elif ty == 0x004E4942: bin = data
    return js, bin


def accessor(js, bin, i):
    """Read one accessor, interleaved or not.

    The byteStride branch is not optional: every gltf-transform command writes
    `--vertex-layout interleaved` unless told otherwise, so from `flatten`
    onwards POSITION and its companions share one buffer view and a tight read
    returns neither. Ignoring it produced a cat whose bounding box was a
    two-unit cube and whose triangle count was still, reassuringly, correct.
    """
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    ct = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: '<u1'}[a['componentType']]
    nc = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    stride = bv.get('byteStride')
    if not stride:
        return np.frombuffer(bin, dtype=ct, count=a['count'] * nc,
                             offset=off).reshape(a['count'], nc)
    itemsz = np.dtype(ct).itemsize * nc
    # The final element occupies only its own size, not a whole stride, so a
    # buffer can legitimately end (count-1)*stride + itemsz in. Reading
    # count*stride overruns it by exactly the tail padding.
    span = (a['count'] - 1) * stride + itemsz
    raw = np.frombuffer(bin, dtype=np.uint8, count=span, offset=off)
    raw = np.concatenate([raw, np.zeros(stride - itemsz, np.uint8)])
    cols = raw.reshape(a['count'], stride)[:, :itemsz]
    return np.ascontiguousarray(cols).view(ct).reshape(a['count'], nc)


def write(path, js, bin):
    jsb = json.dumps(js, separators=(',', ':')).encode()
    # the JSON chunk pads with SPACES; NUL bytes are a spec violation that
    # JSON.parse rejects, and the whole .glb then fails to load
    while len(jsb) % 4: jsb += b' '
    blob = bin + b'\x00' * ((4 - len(bin) % 4) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(jsb) + 8 + len(blob)))
        f.write(struct.pack('<II', len(jsb), 0x4E4F534A)); f.write(jsb)
        f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)


def node_matrix(nd):
    if 'matrix' in nd:
        return np.array(nd['matrix'], dtype='f8').reshape(4, 4).T
    qx, qy, qz, qw = nd.get('rotation', [0, 0, 0, 1])
    M = np.eye(4)
    M[:3, :3] = [[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
                 [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
                 [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]]
    M[:3, :3] *= np.array(nd.get('scale', [1, 1, 1]))
    M[:3, 3] = nd.get('translation', [0, 0, 0])
    return M


def geometry(js, bin, want):
    """POSITION, one companion attribute, indices — with the node baked in."""
    pr = js['meshes'][0]['primitives'][0]
    P = accessor(js, bin, pr['attributes']['POSITION']).astype('<f4')
    A = accessor(js, bin, pr['attributes'][want])
    I = accessor(js, bin, pr['indices']).ravel().astype(np.uint32)
    M = node_matrix(js['nodes'][0])
    P = (P.astype('f8') @ M[:3, :3].T + M[:3, 3]).astype('<f4')
    return P, A, I


def base(name, blob_parts, accessors, views, extra):
    """The common minimal glTF: one node, one mesh, one primitive."""
    g = {"asset": {"version": "2.0", "generator": "sculptglb.py", "extras": extra},
         "scene": 0, "scenes": [{"nodes": [0]}],
         "nodes": [{"mesh": 0, "name": name}],
         "meshes": [{"name": name, "primitives": [{}]}],
         "accessors": accessors, "bufferViews": views,
         "buffers": [{"byteLength": sum(len(p) + (4 - len(p) % 4) % 4
                                        for p in blob_parts)}]}
    return g


def pack(parts):
    offs, blob = [], b''
    for p in parts:
        offs.append(len(blob))
        blob += p + b'\x00' * ((4 - len(p) % 4) % 4)
    return offs, blob


# ── cat ────────────────────────────────────────────────────────────────────
CAT_EXTRAS = {
    "title": "Sitting cat (British Shorthair Blue Cat)",
    "author": "3D Creator (https://sketchfab.com/3DChuang-Ke-Ji)",
    "license": "CC-BY-4.0",
    "source": "https://sketchfab.com/3d-models/"
              "sitting-catbritish-shorthair-blue-cat-ee5dcbdd0c2b4c33adf83d4c6708e6ae"}


def strip_cat(src, out):
    js, bin = load(src)
    pr = js['meshes'][0]['primitives'][0]
    for k in ('NORMAL', 'TANGENT', 'TEXCOORD_1', 'TEXCOORD_2', 'TEXCOORD_3'):
        pr['attributes'].pop(k, None)
    m = js['materials'][0]
    m.pop('normalTexture', None)
    m.pop('extensions', None)
    js.pop('extensionsUsed', None)
    m['pbrMetallicRoughness'].pop('metallicRoughnessTexture', None)
    write(out, js, bin)
    return sorted(pr['attributes'])


def repack_cat(src, out, cfg):
    js, bin = load(src)
    P, U, I = geometry(js, bin, 'TEXCOORD_0')
    U = U.astype('<f4')

    bv = js['bufferViews'][js['images'][0]['bufferView']]
    o = bv.get('byteOffset', 0)
    im = Image.open(io.BytesIO(bin[o:o + bv['byteLength']])).convert('RGB')
    if im.size[0] != cfg['size']:
        im = im.resize((cfg['size'], cfg['size']), Image.LANCZOS)
    g, k = cfg['gamma'], cfg['contrast']
    lut = []
    for i in range(256):
        v = (i / 255.0) ** g
        v = 0.5 + (v - 0.5) * k
        lut.append(min(255, max(0, int(round(255.0 * v)))))
    im = im.point(lut * 3)
    tb = io.BytesIO()
    im.save(tb, 'JPEG', quality=cfg['quality'], optimize=True, subsampling=0)
    tex = tb.getvalue()

    idt = np.uint16 if len(P) < 65536 else np.uint32
    parts = [P.tobytes(), U.tobytes(), I.astype(idt).tobytes(), tex]
    offs, blob = pack(parts)
    acc = [
      {"bufferView": 0, "componentType": 5126, "count": len(P), "type": "VEC3",
       "min": P.min(0).tolist(), "max": P.max(0).tolist()},
      {"bufferView": 1, "componentType": 5126, "count": len(U), "type": "VEC2"},
      {"bufferView": 2, "componentType": int(5123 if idt == np.uint16 else 5125),
       "count": len(I), "type": "SCALAR"}]
    views = [{"buffer": 0, "byteOffset": offs[0], "byteLength": len(parts[0]), "target": 34962},
             {"buffer": 0, "byteOffset": offs[1], "byteLength": len(parts[1]), "target": 34962},
             {"buffer": 0, "byteOffset": offs[2], "byteLength": len(parts[2]), "target": 34963},
             {"buffer": 0, "byteOffset": offs[3], "byteLength": len(parts[3])}]
    gl = base("cat", parts, acc, views, CAT_EXTRAS)
    gl['meshes'][0]['primitives'][0] = {
        "attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 0}
    gl["materials"] = [{"name": "cat", "pbrMetallicRoughness": {
        "baseColorTexture": {"index": 0},
        "metallicFactor": 0.0, "roughnessFactor": 1.0}}]
    gl["textures"] = [{"sampler": 0, "source": 0}]
    gl["images"] = [{"bufferView": 3, "mimeType": "image/jpeg"}]
    gl["samplers"] = [{"magFilter": 9729, "minFilter": 9987,
                       "wrapS": 33071, "wrapT": 33071}]
    write(out, gl, blob)
    return len(I) // 3, len(P), len(tex), P.min(0), P.max(0)


# ── plush ──────────────────────────────────────────────────────────────────
PLUSH_EXTRAS = {
    "title": "Cute Penguin 9th May 2020",
    "author": "Felix_Lim (https://sketchfab.com/Felix_Lim)",
    "license": "CC-BY-4.0",
    "source": "https://sketchfab.com/3d-models/"
              "cute-penguin-9th-may-2020-d2156bead52541e58a9c8ff3ec59624c"}


def strip_plush(src, out):
    """One material for eight subtools, so `join` can merge them."""
    js, bin = load(src)
    for me in js['meshes']:
        for pr in me['primitives']:
            pr['attributes'].pop('NORMAL', None)
            pr['material'] = 0
    js['materials'] = [{"name": "plush", "pbrMetallicRoughness": {
        "baseColorFactor": [1, 1, 1, 1],
        "metallicFactor": 0.0, "roughnessFactor": 1.0}}]
    js.pop('extensionsUsed', None)
    js.pop('extensionsRequired', None)
    write(out, js, bin)
    return sorted(js['meshes'][0]['primitives'][0]['attributes'])


def repack_plush(src, out, cfg):
    js, bin = load(src)
    P, C, I = geometry(js, bin, 'COLOR_0')
    # float32 VEC4 -> normalised ubyte VEC4: sixteen bytes a vertex down to four
    C = np.clip(C.astype('f8'), 0.0, 1.0)
    if C.shape[1] == 3:
        C = np.concatenate([C, np.ones((len(C), 1))], axis=1)
    C = np.round(C * 255.0).astype(np.uint8)

    idt = np.uint16 if len(P) < 65536 else np.uint32
    parts = [P.tobytes(), C.tobytes(), I.astype(idt).tobytes()]
    offs, blob = pack(parts)
    acc = [
      {"bufferView": 0, "componentType": 5126, "count": len(P), "type": "VEC3",
       "min": P.min(0).tolist(), "max": P.max(0).tolist()},
      {"bufferView": 1, "componentType": 5121, "normalized": True,
       "count": len(C), "type": "VEC4"},
      {"bufferView": 2, "componentType": int(5123 if idt == np.uint16 else 5125),
       "count": len(I), "type": "SCALAR"}]
    views = [{"buffer": 0, "byteOffset": offs[0], "byteLength": len(parts[0]), "target": 34962},
             {"buffer": 0, "byteOffset": offs[1], "byteLength": len(parts[1]), "target": 34962},
             {"buffer": 0, "byteOffset": offs[2], "byteLength": len(parts[2]), "target": 34963}]
    gl = base("plush", parts, acc, views, PLUSH_EXTRAS)
    gl['meshes'][0]['primitives'][0] = {
        "attributes": {"POSITION": 0, "COLOR_0": 1}, "indices": 2, "material": 0}
    gl["materials"] = [{"name": "plush", "pbrMetallicRoughness": {
        "baseColorFactor": [1, 1, 1, 1],
        "metallicFactor": 0.0, "roughnessFactor": 1.0}}]
    write(out, gl, blob)
    return len(I) // 3, len(P), 0, P.min(0), P.max(0)


def run(*args):
    r = subprocess.run(list(args), capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('failed: %s\n%s' % (' '.join(args), r.stderr[-800:]))


PROFILES = {
    'cat':   dict(cfg=CAT,   strip=strip_cat,   repack=repack_cat,   join=False),
    'plush': dict(cfg=PLUSH, strip=strip_plush, repack=repack_plush, join=True),
}

if __name__ == '__main__':
    if len(sys.argv) < 4 or sys.argv[1] not in PROFILES:
        sys.exit(__doc__)
    profile, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
    P = PROFILES[profile]
    cfg = dict(P['cfg'])
    for kv in sys.argv[4:]:
        k, _, v = kv.partition('=')
        if k not in cfg:
            sys.exit('no such setting %r for profile %r (have %s)'
                     % (k, profile, ', '.join(sorted(cfg))))
        cfg[k] = type(cfg[k])(v)
    tmp = tempfile.mkdtemp(prefix='sculptglb-')
    j = lambda n: os.path.join(tmp, n)
    print('%-42s %8d B' % (os.path.basename(src), os.path.getsize(src)))

    print('  kept attributes %s' % P['strip'](src, j('a.glb')))
    run(*GLTF, 'prune', j('a.glb'), j('b.glb'))
    run(*GLTF, 'flatten', j('b.glb'), j('c.glb'))
    if P['join']:
        run(*GLTF, 'join', j('c.glb'), j('c2.glb'))
    else:
        os.rename(j('c.glb'), j('c2.glb'))
    run(*GLTF, 'weld', j('c2.glb'), j('d.glb'))
    run(*GLTF, 'simplify', j('d.glb'), j('e.glb'),
        '--ratio', str(cfg['ratio']), '--error', str(cfg['error']))
    tri, nv, ntex, mn, mx = P['repack'](j('e.glb'), out, cfg)

    print('  %d triangles, %d vertices%s' %
          (tri, nv, ', texture %d B' % ntex if ntex else ', no texture'))
    print('  bbox %s .. %s' % (mn.round(3).tolist(), mx.round(3).tolist()))
    print('%-42s %8d B' % (os.path.basename(out), os.path.getsize(out)))
