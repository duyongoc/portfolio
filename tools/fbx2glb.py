#!/usr/bin/env python3
"""Binary-FBX (7.x) -> .glb converter, geometry only.

Written because this machine has no Blender, no FBX2glTF and no assimp, and the
Synty packs ship .fbx + Unity prefabs with nothing web-loadable in between.
It reads only what a static prop needs: positions, normals, UV0. Skinning,
animation, cameras and lights are ignored on purpose.

The pack shares one texture atlas across every prop, so the atlas is referenced
as an external image URI rather than embedded — one download serves all models.
Everything merges into a single primitive under that one material, so a prop
that mixes the atlas with a second texture has to be cut down to the atlas part
— see the fourth argument.

    python3 tools/fbx2glb.py SRC.fbx OUT.glb atlas.png [geo indices]
"""
import struct, zlib, json, sys, os, math

def read_prop(f):
    t = f.read(1).decode('ascii')
    if t == 'Y': return struct.unpack('<h', f.read(2))[0]
    if t == 'C': return f.read(1)[0] != 0
    if t == 'I': return struct.unpack('<i', f.read(4))[0]
    if t == 'F': return struct.unpack('<f', f.read(4))[0]
    if t == 'D': return struct.unpack('<d', f.read(8))[0]
    if t == 'L': return struct.unpack('<q', f.read(8))[0]
    if t in 'fdlib':
        n, enc, clen = struct.unpack('<III', f.read(12))
        raw = f.read(clen)
        if enc == 1: raw = zlib.decompress(raw)
        code = {'f':'f','d':'d','l':'q','i':'i','b':'b'}[t]
        return list(struct.unpack('<%d%s' % (n, code), raw))
    if t in 'SR':
        n = struct.unpack('<I', f.read(4))[0]
        d = f.read(n)
        return d.decode('utf-8','replace') if t == 'S' else d
    raise ValueError('unknown property type %r' % t)

def read_node(f, ver):
    if ver >= 7500:
        end, nprop, plen = struct.unpack('<QQQ', f.read(24))
    else:
        end, nprop, plen = struct.unpack('<III', f.read(12))
    namelen = f.read(1)[0]
    if end == 0: return None                      # null terminator record
    name = f.read(namelen).decode('utf-8','replace')
    props = [read_prop(f) for _ in range(nprop)]
    kids = []
    while f.tell() < end:
        c = read_node(f, ver)
        if c is None: break
        kids.append(c)
    f.seek(end)
    return {'n': name, 'p': props, 'c': kids}

def parse(path):
    f = open(path, 'rb')
    head = f.read(27)
    assert head[:20] == b'Kaydara FBX Binary  ', 'not a binary FBX'
    ver = struct.unpack('<I', head[23:27])[0]
    root = []
    size = os.path.getsize(path)
    while f.tell() < size - 32:
        nd = read_node(f, ver)
        if nd is None: break
        root.append(nd)
    return root, ver

def kid(node, name):
    for c in node['c']:
        if c['n'] == name: return c
    return None

def first_array(node, name):
    c = kid(node, name)
    return c['p'][0] if c and c['p'] else None

def geometries(root):
    objs = next((n for n in root if n['n'] == 'Objects'), None)
    if not objs: return []
    return [g for g in objs['c'] if g['n'] == 'Geometry' and kid(g, 'Vertices')]

def build(geo):
    verts = first_array(geo, 'Vertices')
    pvi   = first_array(geo, 'PolygonVertexIndex')
    ln = kid(geo, 'LayerElementNormal'); lu = kid(geo, 'LayerElementUV')
    normals = first_array(ln, 'Normals') if ln else None
    nmap = (first_array(ln, 'MappingInformationType') if ln else '') or ''
    nref = (first_array(ln, 'ReferenceInformationType') if ln else '') or ''
    nidx = first_array(ln, 'NormalsIndex') if ln else None
    uvs  = first_array(lu, 'UV') if lu else None
    uidx = first_array(lu, 'UVIndex') if lu else None
    uref = (first_array(lu, 'ReferenceInformationType') if lu else '') or ''

    pos, nor, uv = [], [], []
    poly = []
    for pvI, raw in enumerate(pvi):
        last = raw < 0
        vi = (~raw) if last else raw
        poly.append((vi, pvI))
        if not last: continue
        for k in range(1, len(poly) - 1):           # fan-triangulate
            for (v, p) in (poly[0], poly[k], poly[k+1]):
                pos.append((verts[v*3], verts[v*3+1], verts[v*3+2]))
                if normals:
                    j = p if nmap == 'ByPolygonVertex' else v
                    if nref.startswith('IndexToDirect') and nidx: j = nidx[j]
                    nor.append((normals[j*3], normals[j*3+1], normals[j*3+2]))
                else:
                    nor.append((0.0, 1.0, 0.0))
                if uvs:
                    j = uidx[p] if (uref.startswith('IndexToDirect') and uidx) else p
                    uv.append((uvs[j*2], uvs[j*2+1]))
                else:
                    uv.append((0.0, 0.0))
        poly = []

    # weld: same position+normal+uv is the same vertex
    seen, idx, P, N, U = {}, [], [], [], []
    for i in range(len(pos)):
        key = (tuple(round(c, 5) for c in pos[i]),
               tuple(round(c, 4) for c in nor[i]),
               tuple(round(c, 5) for c in uv[i]))
        j = seen.get(key)
        if j is None:
            j = len(P); seen[key] = j
            P.append(pos[i]); N.append(nor[i]); U.append(uv[i])
        idx.append(j)
    return P, N, U, idx

def pad4(b): return b + b'\x00' * ((4 - len(b) % 4) % 4)

def write_glb(out, P, N, U, idx, image_uri):
    bp = b''.join(struct.pack('<3f', *v) for v in P)
    bn = b''.join(struct.pack('<3f', *v) for v in N)
    # glTF UV origin is top-left, FBX bottom-left
    bu = b''.join(struct.pack('<2f', v[0], 1.0 - v[1]) for v in U)
    bi = b''.join(struct.pack('<I', i) for i in idx)
    blob = pad4(bp) + pad4(bn) + pad4(bu) + pad4(bi)
    o1, o2, o3 = len(pad4(bp)), len(pad4(bp)) + len(pad4(bn)), len(pad4(bp)) + len(pad4(bn)) + len(pad4(bu))
    mn = [min(v[i] for v in P) for i in range(3)]
    mx = [max(v[i] for v in P) for i in range(3)]
    g = {
      "asset": {"version": "2.0", "generator": "fbx2glb.py"},
      "scene": 0, "scenes": [{"nodes": [0]}],
      "nodes": [{"mesh": 0, "name": os.path.basename(out)[:-4]}],
      "meshes": [{"primitives": [{"attributes": {"POSITION":0,"NORMAL":1,"TEXCOORD_0":2},
                                  "indices": 3, "material": 0}]}],
      "materials": [{"pbrMetallicRoughness": {
                        "baseColorTexture": {"index": 0},
                        "metallicFactor": 0.0, "roughnessFactor": 0.85}}],
      "textures": [{"sampler": 0, "source": 0}],
      "images": [{"uri": image_uri}],
      "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071}],
      "accessors": [
        {"bufferView":0,"componentType":5126,"count":len(P),"type":"VEC3","min":mn,"max":mx},
        {"bufferView":1,"componentType":5126,"count":len(N),"type":"VEC3"},
        {"bufferView":2,"componentType":5126,"count":len(U),"type":"VEC2"},
        {"bufferView":3,"componentType":5125,"count":len(idx),"type":"SCALAR"}],
      "bufferViews": [
        {"buffer":0,"byteOffset":0,"byteLength":len(bp),"target":34962},
        {"buffer":0,"byteOffset":o1,"byteLength":len(bn),"target":34962},
        {"buffer":0,"byteOffset":o2,"byteLength":len(bu),"target":34962},
        {"buffer":0,"byteOffset":o3,"byteLength":len(bi),"target":34963}],
      "buffers": [{"byteLength": len(blob)}]
    }
    # the JSON chunk must be padded with SPACES; NUL bytes are a spec violation
    # and JSON.parse rejects them, so the whole .glb fails to load
    js = json.dumps(g, separators=(',',':')).encode('utf-8')
    while len(js) % 4: js += b' '
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(out, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
    return mn, mx, len(P), len(idx)//3

if __name__ == '__main__':
    src, out, img = sys.argv[1], sys.argv[2], sys.argv[3]
    """A fourth argument picks Geometry nodes by index, e.g. "0" or "0,2".

    Everything here lands in one primitive under one material, which is only
    correct while a prop draws from a single atlas. Several Synty props do not:
    SM_Prop_Holo_Planter_01 is a pot on the pack atlas plus a tree on its own
    foliage sheet, and merged, the tree's full 0..1 UVs pull the entire atlas
    across every leaf. Listing the atlas geometry is how such a prop gets used
    at all. Run with no fourth argument first — it prints each node's index,
    vertex count and UV range, and a node reaching 0..1 is one to leave out.
    """
    want = None
    if len(sys.argv) > 4:
        want = {int(k) for k in sys.argv[4].split(',')}
    root, ver = parse(src)
    geos = geometries(root)
    if not geos:
        print('NO GEOMETRY', src); sys.exit(1)
    if want is not None:
        bad = want - set(range(len(geos)))
        if bad:
            print('no such geometry %s (file has %d)' % (sorted(bad), len(geos)),
                  file=sys.stderr)
            sys.exit(1)
        geos = [g for i, g in enumerate(geos) if i in want]
    # a prop may be split across several Geometry nodes; merge them
    P, N, U, I = [], [], [], []
    for g in geos:
        p, n, u, i = build(g)
        off = len(P)
        P += p; N += n; U += u; I += [x + off for x in i]
    mn, mx, nv, nt = write_glb(out, P, N, U, I, img)
    dim = [round(mx[k]-mn[k], 2) for k in range(3)]
    print('%-38s v=%-6d tri=%-6d size=%s  bbox=%s' %
          (os.path.basename(out), nv, nt, dim, [round(v,1) for v in mn]))
    if want is None and len(geos) > 1:
        # per-node UV ranges, so a merge that should not have happened shows up
        for i, g in enumerate(geos):
            p, n, u, ix = build(g)
            us = [c[0] for c in u]; vs = [c[1] for c in u]
            print('   geo %d: v=%-6d u[%.3f,%.3f] v[%.3f,%.3f]%s' %
                  (i, len(p), min(us), max(us), min(vs), max(vs),
                   '   <- spans the whole sheet, probably its own texture'
                   if max(us) > .999 or max(vs) > .999 else ''))
