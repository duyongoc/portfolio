#!/usr/bin/env python3
"""What the bake tools read out of the site's own data files.

Three of the tools here need the same four things — the project list, the
category table, the slug that names a clip, and the generated wall map — and
before this file existed each one carried its own copy. Two of those copies
were `slug`, whose docstring in wallsheet.py said in words what this module
says in code: it has to agree with the other implementations, and nothing
made it.

Deliberately free of Pillow, ffmpeg and yt-dlp. The tools that draw pixels
need those; the tools that only read data should not, and `wallsheet.py
--check` runs in CI on a machine with none of them installed.

Nothing here is imported by the site. It is the build side of the same data
the browser loads as plain scripts.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'demos/portfolio-data.js')
SHARED = os.path.join(ROOT, 'demos/portfolio-shared.js')
LAYOUT = os.path.join(ROOT, 'build_layout.txt')
GEN = os.path.join(ROOT, 'demos/wall-layout.js')
CLIPDIR = os.path.join(ROOT, 'demos/clips')


def slug(title):
    """The id a build is known by outside portfolio-data.js.

    It names its clip file and it is what build_layout.txt is written in. There
    is exactly one implementation on the build side — this one — and the
    browser has none at all: wallsheet.py resolves every title to its clip up
    front and generates the map, so nothing in room-3d.html ever has to slug a
    string and agree with what happened here."""
    return re.sub(r'(^-|-$)', '', re.sub(r'[^a-z0-9]+', '-', title.lower()))


def games(path=DATA):
    """GAMES out of the canonical data file, without standing up a JS engine.

    The file is one `const GAMES = [...]` of plain JSON, which is the reason
    it is written that way rather than as a JS literal with trailing commas
    and unquoted keys."""
    src = open(path, encoding='utf-8').read()
    try:
        return json.loads(src[src.index('['):src.rindex(']') + 1])
    except (ValueError, json.JSONDecodeError) as e:
        raise SystemExit('%s: cannot read GAMES — %s' % (path, e))


def _shared(path=SHARED):
    return open(path, encoding='utf-8').read()


def categories(path=SHARED):
    """CAT out of portfolio-shared.js.

    CAT is the category table the browser already renders every filter, swatch
    and label from, and since it also carries each category's section heading
    and accent colour it is the only place either is written down. The bake
    reads it rather than restating it: the section stripe on a cover used to be
    a second copy of these colours, in RGB tuples, in Python, and changing an
    accent in the stylesheet left the baked sheets on the old one until someone
    noticed by eye.

    Regex rather than a parser because the shape is fixed and checked: a `key:
    {...}` per line, single-quoted values. A malformed table stops the bake
    instead of silently returning fewer categories than there are."""
    m = re.search(r'const\s+CAT\s*=\s*\{(.*?)\n\};', _shared(path), re.S)
    if not m:
        raise SystemExit('%s: no `const CAT={...};` block — the bake reads the '
                         'category table from there' % path)
    out = {}
    for key, body in re.findall(r'(\w+)\s*:\s*\{([^{}]*)\}', m.group(1)):
        out[key] = dict(re.findall(r"(\w+)\s*:\s*'([^']*)'", body))
    if not out:
        raise SystemExit('%s: CAT parsed to nothing' % path)
    missing = sorted(k for k, v in out.items() if not v.get('section') or not v.get('c'))
    if missing:
        raise SystemExit('%s: CAT entries %s need both a section and a colour — '
                         'the bake draws the section stripe from them'
                         % (path, ', '.join(missing)))
    return out


def sections(path=SHARED):
    """section heading -> category key. The inverse of CAT's `section` field,
    which is what an `auto section=` rule in the layout resolves through."""
    return {v['section']: k for k, v in categories(path).items()}


def featured(path=SHARED):
    """FEATURED out of portfolio-shared.js.

    The wall panel leads with these write-ups on the claim that each one is
    also hanging on the wall behind it, so that claim is checkable."""
    m = re.search(r'const\s+FEATURED\s*=\s*\[(.*?)\]', _shared(path), re.S)
    return [a or b for a, b in re.findall(r"'([^']*)'|\"([^\"]*)\"", m.group(1))] if m else []


def thumb_path(p):
    """A portfolio-data.js image path -> the thumbnail actually on disk.

    Must agree with thumb() in portfolio-shared.js: the full-size originals are
    not shipped, and both pages rewrite every path the same way."""
    p = p.replace('../images/', 'images/thumb/')
    return os.path.join(ROOT, re.sub(r'\.(jpe?g|png)$', '.jpg', p, flags=re.I))


def rgb(hexcol):
    """'#df7ff5' -> (223, 127, 245), for Pillow."""
    h = hexcol.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def clips_on_disk(path=CLIPDIR):
    """Every baked preview, by id. Listed rather than probed for at runtime: a
    miss would be a 404 on every hover of a coverless build."""
    if not os.path.isdir(path):
        return []
    return sorted(f[:-4] for f in os.listdir(path) if f.endswith('.mp4'))


def wall_zones(path=GEN):
    """The generated wall map, back out of demos/wall-layout.js.

    clips.py works from this rather than from build_layout.txt on purpose: the
    walls are what hover, and this is the same list the room indexes its covers
    against. One parser for that file is enough, and it lives here rather than
    in the tool that happens to need it second."""
    if not os.path.exists(path):
        raise SystemExit('%s is missing — run python3 tools/wallsheet.py first, it '
                         'generates the wall map this works from' % path)
    src = open(path, encoding='utf-8').read()
    m = re.search(r'const\s+WALL_ZONES\s*=\s*\{(.*?)\n\};', src, re.S)
    if not m:
        raise SystemExit('%s is not the generated wall map — re-run '
                         'tools/wallsheet.py' % path)
    out = []
    for arr in re.findall(r'titles:(\[[^\]]*\])', m.group(1)):
        out += json.loads(arr)
    return out
