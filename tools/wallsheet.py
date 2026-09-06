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

Which build hangs where, in what order, on which grid, is build_layout.txt.
This script is the only thing that reads it: it bakes the sheets AND generates
demos/wall-layout.js, so the pixels and the cell -> game map the room hovers
against can only ever come out of the same run. That is the whole point of the
arrangement — the failure it removes is a wall that shows one game and opens
another, which nothing can detect from either side alone. Editing the layout
and not re-running this leaves the room consistent but unchanged.

    python3 tools/wallsheet.py            bake the sheets, regenerate the map
    python3 tools/wallsheet.py --check    validate and diff, write nothing

--check is what CI runs. It does every validation the bake does and regenerates
demos/wall-layout.js in memory, then compares it with the file on disk — which
is exactly the "edited the layout and forgot to re-bake" case, previously
detectable only by looking at the wall. It deliberately does NOT compare the
JPEGs: they are drawn with whatever fonts the machine has, so their bytes are
not reproducible across machines and a pixel diff would fail on the runner for
reasons that have nothing to do with the change. It does not need Pillow
either, which is why the import below is allowed to fail.
"""
import hashlib, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portfolio import (ROOT, LAYOUT, GEN, CLIPDIR, SHARED, THUMBDIR, ASSETV,
                       games, categories, featured, slug, thumb_path, rgb,
                       clips_on_disk)

# Only bake() draws, and only bake() needs this. --check runs every validation
# in the file and generates the map without touching a pixel, so it has to work
# on a machine with no Pillow — which is the whole reason CI can be four lines
# and no pip install.
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:                                   # pragma: no cover
    Image = ImageDraw = ImageFont = None

PAD = 5
CELL_AR = 400 / 245                    # one cell's width:height, all three sheets
BAND    = 198 / 245                    # how much of a cell the image band takes

# What each wall IS — its screen id in room-3d.html, the sheet it is baked to,
# its grid, the baked width of one cell, and whether the last cell is the count
# plate. Structural, and paired with a plane of a matching shape in the room, so
# it does not belong in the file that gets edited to move a game around. The
# grid belongs to the zone: a build moved into zone 8 renders at zone 8's cell
# size, and the layout's list for a zone has to fit cols*rows cells, less one
# where there is a plate.
#
# Cell width is resolution, not layout. Under about 90 screen pixels a cover
# stops reading as a screenshot, which is what ruled out the original 8x5.
ZONES = {
    1: dict(screen='wall',  sheet='wall',       cols=4, rows=3, cell=400, plate=True),
    8: dict(screen='wallL', sheet='wall-left',  cols=1, rows=3, cell=560, plate=False),
    9: dict(screen='wallR', sheet='wall-right', cols=1, rows=4, cell=560, plate=False),
}


def aspect(cols, rows):
    """The width:height a sheet on this grid comes out at.

    The plane it is mapped onto in room-3d.html has to be this shape or every
    cell boundary sits off its tile. That used to be a number worked out by
    hand at each of the three planes and checked afterwards by #qa=1 in a
    browser; it is generated into wall-layout.js now, and the room shapes its
    planes from it. A width is a room-layout decision and stays in the room; a
    height is arithmetic and does not."""
    return cols * CELL_AR / rows

# The props that carry a list of builds. A wall takes a grid, so it is ZONES
# above; these take a list in whatever order the file gives, and most of them
# are a rule rather than a list because their content is a category — a new
# reskin should land on the reskin monitor without anyone editing anything.
SURFACES = {
    'trash':    dict(screen='casual', what='the bin'),
    'monitor':  dict(screen='monR',   what='the reskin monitor'),
    'tablet':   dict(screen='ar',     what='the AR tablet'),
    'showreel': dict(screen='holo',   what='the hologram'),
}

HEAD = re.compile(r'^(?:zone\s+(\S+)|(%s))\s*$' % '|'.join(SURFACES))
AUTO = re.compile(r'^auto\s+(section|link)=(.+)$')


def read_layout(path=LAYOUT):
    """build_layout.txt -> a list of zone dicts, in file order.

    The file carries one thing: which titles hang on which wall, in what order.
    Everything else about a wall is ZONES above, because it is the same shape
    as the plane in room-3d.html and changing it is not what anyone opens this
    file to do."""
    if not os.path.exists(path):
        raise SystemExit('%s is missing — it is the only hand-written record of '
                         'what hangs on the walls' % path)
    zones, surfaces, cur = [], [], None
    for n, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.split('#')[0].strip()
        if not line:
            continue
        m = HEAD.match(line)
        if m and m.group(2):
            cur = dict(SURFACES[m.group(2)], name=m.group(2), titles=[], auto=None, line=n)
            surfaces.append(cur)
        elif m:
            key = int(m.group(1)) if m.group(1).isdigit() else None
            if key not in ZONES:
                raise SystemExit('%s:%d: no zone %s — the walls are %s, and the props '
                                 'are %s (both in %s)'
                                 % (path, n, m.group(1),
                                    ', '.join(str(k) for k in sorted(ZONES)),
                                    ', '.join(sorted(SURFACES)),
                                    os.path.basename(__file__)))
            cur = dict(ZONES[key], zone=key, titles=[], line=n)
            zones.append(cur)
        elif cur is None:
            # Nearly always a heading that was mistyped: it did not match, so it
            # fell through to here and looks like a list with nothing above it.
            raise SystemExit('%s:%d: %r is under no heading — the headings are '
                             'zone %s and %s'
                             % (path, n, line,
                                ', zone '.join(str(k) for k in sorted(ZONES)),
                                ', '.join(sorted(SURFACES))))
        elif line.startswith('auto'):
            a = AUTO.match(line)
            if not a:
                raise SystemExit('%s:%d: auto wants section=<name> or link=<kind>'
                                 % (path, n))
            if 'zone' in cur:
                raise SystemExit('%s:%d: zone %s is a baked grid, so its covers have '
                                 'to be named' % (path, n, cur['zone']))
            cur['auto'] = (a.group(1), a.group(2).strip())
        else:
            cur['titles'] += [t.strip() for t in line.split('|') if t.strip()]
    missing = [k for k in ZONES if k not in {z['zone'] for z in zones}]
    if missing:
        print('warn: zone %s %s not in the layout — %s hangs nothing'
              % (', '.join(str(k) for k in missing),
                 'is' if len(missing) == 1 else 'are',
                 'that wall' if len(missing) == 1 else 'those walls'), file=sys.stderr)
    if not zones:
        raise SystemExit('%s: no zones' % path)
    return zones, surfaces


REF_MARK = '# ── ALL GAMES ─────'


def match(rule, all_games, cats):
    """An auto rule against the data: the same two filters the room used to
    hold inline. Kept as a rule rather than baked to a list so that adding a
    reskin puts it on the reskin monitor without anyone editing anything.

    A section name resolves through CAT rather than against a per-project
    field, so a heading that is not a real category stops the bake and names
    the ones that are. It used to match nothing and warn, which reads the same
    as a category that happens to be empty."""
    key, val = rule
    if key == 'section':
        by_section = {v['section']: k for k, v in cats.items()}
        if val not in by_section:
            raise SystemExit('%s: no section %r — the sections are %s (they are the '
                             '`section` fields of CAT in %s)'
                             % (LAYOUT, val, ', '.join(sorted(by_section)),
                                os.path.relpath(SHARED, ROOT)))
        cat = by_section[val]
        return [g for g in all_games if g['cat'] == cat]
    return [g for g in all_games if any(l.get('kind') == val for l in g.get('links', []))]


def resolve(zones, all_games):
    """Layout entries are ids: the title lowercased with every run of anything
    else turned into a dash, which is the same string that names the clip file.
    A full title works too — slugging it lands on the same id — so the file can
    hold either, and an entry that is neither stops the bake."""
    by_id = {slug(g['title']): g['title'] for g in all_games}
    for z in zones:
        out = []
        for entry in z['titles']:
            title = by_id.get(slug(entry))
            if not title:
                raise SystemExit('%s: zone %s has no game %r — the ids are listed at '
                                 'the foot of that file' % (LAYOUT, z['zone'], entry))
            out.append(title)
        z['titles'] = out


def resolve_surfaces(surfaces, all_games, cats):
    """Same as resolve(), plus the rules. A surface with neither a list nor a
    rule is a surface the file mentions and says nothing about, which is worth
    stopping for — silently leaving it on whatever the room had is how a config
    file becomes decoration."""
    by_id = {slug(g['title']): g['title'] for g in all_games}
    for su in surfaces:
        if su['auto'] and su['titles']:
            raise SystemExit('%s:%d: %s has both a rule and a list — pick one'
                             % (LAYOUT, su['line'], su['name']))
        if su['auto']:
            hit = match(su['auto'], all_games, cats)
            if not hit:
                print('warn: %s matches nothing (%s=%s) — %s will be empty'
                      % (su['name'], su['auto'][0], su['auto'][1], su['what']),
                      file=sys.stderr)
            su['resolved'] = [g['title'] for g in hit]
            continue
        if not su['titles']:
            raise SystemExit('%s:%d: %s lists nothing and has no auto rule'
                             % (LAYOUT, su['line'], su['name']))
        out = []
        for entry in su['titles']:
            title = by_id.get(slug(entry))
            if not title:
                raise SystemExit('%s: %s has no game %r — the ids are at the foot of '
                                 'that file' % (LAYOUT, su['name'], entry))
            out.append(title)
        su['titles'] = su['resolved'] = out


def reference_table(all_games, src):
    """The name -> id table at the foot of the layout, as it should read.

    Copying a title by hand is where a layout edit goes wrong, so the file
    carries every build and its id to copy from instead. Regenerating it on
    every bake is what stops that table going stale the first time a project is
    added. Everything from the marker on is ours; anything to keep goes above
    it."""
    w = max(len(g['title']) for g in all_games) + 1
    table = '\n'.join('# %-*s %s' % (w, g['title'] + ':', slug(g['title'])) for g in all_games)
    return ('%s\n\n%s\n# Every build in portfolio-data.js, in archive order. The zone lists\n'
            '# above take the id. Regenerated by tools/wallsheet.py.\n#\n%s\n'
            % (src.split(REF_MARK)[0].rstrip('\n'), REF_MARK, table))


def refresh_reference(all_games):
    src = open(LAYOUT, encoding='utf-8').read()
    new = reference_table(all_games, src)
    if new != src:
        open(LAYOUT, 'w', encoding='utf-8').write(new)
        print('%-28s %d ids refreshed' % ('build_layout.txt', len(all_games)))


def version(zones, all_games, cats):
    """A content hash over everything a sheet is made of, which becomes the
    ?v= the room loads the texture with. Bumping that by hand was the step
    easiest to forget and worst to forget: skip it and your own browser looks
    right, because it just baked the file, while everyone else keeps the old
    one. Narrow on purpose — the fields the bake actually draws, not the whole
    of portfolio-data.js, so editing a description does not invalidate three
    JPEGs that would come out byte-identical, and rewording a comment in the
    layout file does not invalidate anything at all — the parsed zones are
    hashed, not the bytes they were written as.

    The category colour is in here because the section stripe is drawn from it
    and it is no longer written down in this file: recolouring `reskin` in CAT
    changes fifteen covers, and without this the browser would keep the old
    sheet at the old ?v= and nobody would see it."""
    h = hashlib.sha1()
    h.update(json.dumps([[z['zone'], z['sheet'], z['cols'], z['rows'], z['cell'],
                          z['plate'], z['titles']] for z in zones]).encode())
    h.update(json.dumps([[i, g['title'], g['cat'], cats[g['cat']]['c'], g['info']]
                         for i, g in enumerate(all_games)]).encode())
    for t in sorted({t for z in zones for t in z['titles']}):
        g = next((x for x in all_games if x['title'] == t), None)
        try: h.update(open(thumb_path(g['info']), 'rb').read())
        except Exception: h.update(b'-')
    return h.hexdigest()[:8]


# Every file a page fetches at runtime by a path it builds itself. Both
# families are keyed from the site root, which is what the pages' own paths
# reduce to: portfolio-shared.js writes '../images/thumb/x.jpg' because it is
# read from demos/ as well as from the root, and a leading '..' at the root is
# clamped there by the URL parser rather than escaping the site.
ASSET_DIRS = [('images/thumb', '.jpg'), ('demos/clips', '.mp4')]


def asset_versions():
    """path-from-site-root -> content hash, for demos/asset-v.js.

    The sheets carry WALL_SHEET_V and the shared scripts carry a hash each, and
    a comment here used to claim that covered everything the room fetches. It
    did not. The thumbnails and the clips are named by rules in JS -- thumb()
    rewrites an image path, and CLIP_OF hands back a slug -- so nothing about
    those URLs changes when the file behind them is re-cut or re-cropped, and a
    browser holding yesterday's copy has no way to find out. Which is visible
    exactly where it is most confusing: the wall's baked cover updates, because
    that JPEG is versioned, while the readout that opens over it and the panel
    behind that keep playing the old preview and drawing the old still.

    Per file rather than one token over all of them. Both families together are
    about 5 MB, and re-cutting one 60 kB clip should not make ninety-six other
    files unreachable in every cache that already holds them -- which is the
    same reasoning stamps() gives for hashing each shared script on its own."""
    out = {}
    for rel, ext in ASSET_DIRS:
        d = os.path.join(ROOT, rel)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(ext):
                continue
            body = open(os.path.join(d, f), 'rb').read()
            out['%s/%s' % (rel, f)] = hashlib.sha1(body).hexdigest()[:8]
    return out


def generate_assets(av):
    """demos/asset-v.js, as text. Returned rather than written, like generate()."""
    out = ['/* GENERATED by tools/wallsheet.py. Do not edit.',
           '',
           '   Content hash per thumbnail and per clip, for the ?v= that vsrc()',
           '   in portfolio-shared.js appends. These are the files both pages',
           '   name by a rule rather than by a bake, so this is the only thing',
           '   that can tell a browser one of them has been replaced.',
           '',
           '   Loaded by both pages: the room plays the clips and the flat page',
           '   does not, but they render the same thumbnails through the same',
           '   helper, and a version map only one of them has is a stale picture',
           '   on the other. */',
           'const ASSET_V={']
    for k in sorted(av):
        out.append('  %s:%s,' % (json.dumps(k), json.dumps(av[k])))
    out += ['};']
    return '\n'.join(out) + '\n'


def generate(zones, surfaces, ver, all_games):
    """demos/wall-layout.js, as text — read by room-3d.html as a plain script,
    the way portfolio-data.js already is. Not fetched: the room builds its walls
    synchronously in module scope, and an await there would put a round trip
    on the boot path for 400 bytes.

    Returned rather than written so that --check can compare it with what is on
    disk without the check itself being the thing that makes them agree."""
    have = set(clips_on_disk(CLIPDIR))
    out = ['/* GENERATED by tools/wallsheet.py from build_layout.txt.',
           '   Do not edit — edit the .txt and re-run the tool. This file and',
           '   demos/models/*.jpg come out of the same run, which is the only',
           '   thing keeping the baked pixels and this cell -> game map in step.',
           '',
           '   `python3 tools/wallsheet.py --check` fails if this file does not',
           '   match the layout, which is what CI runs. */',
           "const WALL_SHEET_V=%s;" % json.dumps(ver),
           'const WALL_ZONES={']
    for z in zones:
        # `aspect` is width:height for a sheet on this grid. The room shapes the
        # plane it maps onto from it rather than carrying a height worked out by
        # hand, so changing a grid cannot leave the two disagreeing.
        out.append('  %s:{zone:%s,sheet:%s,cols:%d,rows:%d,plate:%s,aspect:%.6f,titles:[%s]},'
                   % (json.dumps(z['screen']), z['zone'], json.dumps(z['sheet']),
                      z['cols'], z['rows'], 'true' if z['plate'] else 'false',
                      aspect(z['cols'], z['rows']),
                      ','.join(json.dumps(t) for t in z['titles'])))
    out += ['};',
            '/* title -> the .mp4 in demos/clips/ that previews it, for every build',
            '   that has one. A map rather than a set of ids because the id is this',
            '   tool\'s business: the room used to carry its own copy of the slug',
            '   rule so it could turn a title into a filename and hope the two',
            '   agreed. Now it looks the answer up. Baked by tools/clips.py,',
            '   enumerated from what is actually on disk so the two cannot',
            '   disagree — a miss would be a 404 on every hover of that cover. */',
            'const CLIP_OF={']
    for g in all_games:
        if slug(g['title']) in have:
            out.append('  %s:%s,' % (json.dumps(g['title']), json.dumps(slug(g['title']))))
    out += ['};',
            '/* The props that carry a list of builds. A rule is evaluated in the',
            '   room against live data; a list is taken as written. */',
            'const ROOM_LISTS={']
    for su in surfaces:
        out.append('  %s:{name:%s,%s},'
                   % (json.dumps(su['screen']), json.dumps(su['name']),
                      ('auto:{%s:%s}' % (su['auto'][0], json.dumps(su['auto'][1])))
                      if su['auto'] else
                      ('titles:[%s]' % ','.join(json.dumps(t) for t in su['titles']))))
    out += ['};']
    return '\n'.join(out) + '\n'


# The plain scripts a page loads with <script src=>, and the pages that load
# them. Two of these are generated, so stamps() takes their text rather than
# reading a file that may not have been written yet.
#
# This list used to carry a note saying everything else the room fetches was
# already versioned -- the wall JPEGs by WALL_SHEET_V, the models by MODEL_V,
# and the modules by the page naming them relative to itself. That was wrong
# about the two biggest families on the site, which is why asset-v.js is here.
STAMPED = ['portfolio-data.js', 'portfolio-shared.js', 'wall-layout.js',
           'asset-v.js']
PAGES = ['room-3d.html', 'demos/portfolio-2d.html']
# The two pages no longer share a directory, so each names these scripts with a
# prefix of its own: 'demos/' from the root, nothing from inside demos/. Group 1
# absorbs that prefix and is written back untouched; group 2 is the bare name,
# which is what the hashes are keyed on. Matching the bare name alone would
# quietly stop matching the page that moved -- and a page nobody stamps is not
# an error here, it is a browser holding a stale script next to a fresh page.
TAG = re.compile(r'<script src="((?:demos/)?)(%s)(?:\?v=[0-9a-f]+)?"'
                 % '|'.join(map(re.escape, STAMPED)))


def stamps(gen):
    """A content hash per shared script, for the ?v= its <script src=> carries.

    `gen` maps the generated ones to the text this run would write; the rest
    are read off disk.

    These files are the site's globals: portfolio-shared.js defines what both
    pages and the room's module read as free variables. A browser holding a
    stale copy of one of them next to a fresh page does not degrade, it throws
    ReferenceError on the first helper the old copy has never heard of, and the
    room boots into its error card. That is not hypothetical — it is what
    happens the first time anyone loads this site after a release that moved a
    helper into the shared file, because nothing in the URL told the browser
    anything had changed.

    It used to be survivable by accident: every helper had a copy inline in the
    page that loaded it, so a page and its helpers could not be from different
    releases. Sharing them is worth doing and this is its cost, paid here.

    Hashed from content, so a rebuild that changes nothing changes no URL and
    the cache still works — the point is to make a stale copy unreachable, not
    to defeat caching."""
    out = {}
    for name in STAMPED:
        body = (gen[name].encode('utf-8') if name in gen
                else open(os.path.join(ROOT, 'demos', name), 'rb').read())
        out[name] = hashlib.sha1(body).hexdigest()[:8]
    return out


def stamp_pages(ver):
    """The two pages with their ?v= rewritten, as text. Returned rather than
    written for the same reason generate() is: --check has to be able to ask
    what a bake would produce without producing it."""
    return {rel: TAG.sub(lambda m: '<script src="%s%s?v=%s"'
                                  % (m.group(1), m.group(2), ver[m.group(2)]),
                         open(os.path.join(ROOT, rel), encoding='utf-8').read())
            for rel in PAGES}


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


def check_data(all_games, cats):
    """The things that are true of the data whatever the layout says.

    Cheap, and none of it needs a browser — which is the point: #qa=1 checks
    far more and checks it against a real render, but it has to be opened by
    hand at a URL, and nothing was checking any of this between one person
    remembering to and the next."""
    ok = True
    unknown = sorted({g['cat'] for g in all_games} - set(cats))
    if unknown:
        print('portfolio-data.js: cat %s is not in CAT (%s) — that build has no '
              'colour, no filter and no section'
              % (', '.join(map(repr, unknown)), os.path.relpath(SHARED, ROOT)),
              file=sys.stderr)
        ok = False
    if any('section' in g for g in all_games):
        print('portfolio-data.js: `section` is CAT\'s field now, not a project\'s — '
              'remove it, the heading comes from the build\'s cat', file=sys.stderr)
        ok = False
    gone = [(g['title'], p) for g in all_games for p in (g['info'], g['intro'])
            if not os.path.exists(thumb_path(p))]
    if gone:
        for title, p in gone:
            print('images/thumb: %r wants %s, which is not there' % (title, p),
                  file=sys.stderr)
        ok = False
    return ok


def check_zone(name, titles, cols, rows, plate, by_title):
    """Can this zone be baked at all — before anything is written.

    Separate from bake() on purpose, and the separation is load-bearing. A
    sheet is saved the moment its zone is drawn, so validating inside the draw
    loop meant zone 1 and zone 8 reaching disk and zone 9 failing, which stops
    the run before demos/wall-layout.js is regenerated: new pixels, old map,
    and a wall that shows one game and opens another. That is precisely the
    failure this tool exists to make impossible, so every zone is cleared here
    first and only then is anything drawn. Every zone is reported, not just the
    first bad one — two mistakes in one edit should cost one run, not two."""
    ok = True
    missing = [t for t in titles if t not in by_title]
    if missing:
        # a hole would shift every later cell against the hover grid, so refuse
        print('%s: not in portfolio-data.js: %s' % (name, missing), file=sys.stderr)
        ok = False
    cap = cols * rows - (1 if plate else 0)
    if len(titles) > cap:
        print('%s: %d titles will not fit %dx%d — that grid holds %d'
              % (name, len(titles), cols, rows, cap), file=sys.stderr)
        ok = False
    elif len(titles) < cap:
        # not fatal: the grid simply ends early, and the room reads titles from
        # the generated map rather than assuming the sheet is full.
        print('note: %s has %d of %d cells filled' % (name, len(titles), cap),
              file=sys.stderr)
    return ok


def bake(name, titles, cols, rows, cw, plate, all_games, by_title, cats):
    """One sheet. The cell aspect is fixed, so the sheet's aspect follows from
    the grid — which is what keeps a baked sheet square with the plane it is
    mapped onto, whatever shape that plane is. Assumes check_zone() has passed."""
    if Image is None:
        raise SystemExit('Pillow is not installed, so nothing can be drawn:\n'
                         '    python3 -m pip install Pillow\n'
                         '(`--check` needs none of it and would have run.)')
    ch = round(cw / CELL_AR)
    tile_h = round(ch * BAND)
    W, H = cols * cw, rows * ch
    picked = [by_title[t] for t in titles]

    sheet = Image.new('RGB', (W, H), (10, 14, 24))
    d = ImageDraw.Draw(sheet)
    # type scales with the cell, so a one-column sheet is not set in 4-column type
    k = cw / 400
    f_title, f_num = font(round(26 * k), True), mono(round(17 * k), True)
    f_big, f_sub, f_tag = font(64, True), mono(19), mono(15)

    for i, g in enumerate(picked):
        cx, cy = (i % cols) * cw, (i // cols) * ch
        # the category's own accent, read out of CAT — the same colour the page
        # gives this build's filter button and the room gives its readout
        col = rgb(cats[g['cat']]['c']) if g['cat'] in cats else (136, 153, 187)
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
        d.text((cx + round(16 * k), ty + round(8 * k)), '%02d' % (all_games.index(g) + 1),
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
        d.text((x0 + 26, y0 + 46), '%d' % len(all_games), font=f_big, fill=(223, 233, 255))
        d.text((x0 + 28, y0 + 124), 'SHIPPED TITLES', font=f_sub, fill=(90, 208, 255))
        d.text((x0 + 28, y0 + 160), 'UNITY · UNREAL', font=f_tag, fill=(120, 140, 170))
        d.text((x0 + 28, y0 + 184), 'C# · C++ · 2019—', font=f_tag, fill=(120, 140, 170))

    out = os.path.join(ROOT, 'demos/models/%s.jpg' % name)
    sheet.save(out, 'JPEG', quality=84, optimize=True)
    print('%-28s %4dx%-4d  %dx%d  %2d tiles%s  %4.0f kB  aspect %.3f'
          % (out.replace(ROOT + '/', ''), W, H, cols, rows, len(picked),
             ' + plate' if plate else '        ', os.path.getsize(out) / 1024, W / H))
    return True


def prepare():
    """Everything both modes do: read, resolve, validate, and work out what
    demos/wall-layout.js should say. Writes nothing.

    Returning the generated text rather than writing it is what makes --check
    possible at all: the check has to be able to ask "what would this run
    produce" without the asking being the thing that makes the answer true."""
    all_games = games()
    cats = categories()
    by_title = {g['title']: g for g in all_games}
    zones, surfaces = read_layout()
    resolve(zones, all_games)
    resolve_surfaces(surfaces, all_games, cats)

    # A build hanging on two walls at once is legal and almost always a slip,
    # so it is said out loud without stopping the bake.
    seen = {}
    for z in zones:
        for t in z['titles']:
            if t in seen:
                print('note: %r hangs on zone %s and zone %s' % (t, seen[t], z['zone']),
                      file=sys.stderr)
            seen[t] = z['zone']

    ok = check_data(all_games, cats)
    # Clear every zone before a single pixel is written — see check_zone().
    ok = all([check_zone(z['sheet'], z['titles'], z['cols'], z['rows'], z['plate'],
                         by_title) for z in zones]) and ok

    ver = version(zones, all_games, cats)
    gen = generate(zones, surfaces, ver, all_games)
    assets = generate_assets(asset_versions())
    return dict(games=all_games, cats=cats, by_title=by_title, zones=zones,
                surfaces=surfaces, seen=seen, ver=ver, ok=ok,
                gen=gen, assets=assets,
                pages=stamp_pages(stamps({'wall-layout.js': gen,
                                          'asset-v.js': assets})))


def claims(st):
    """The claims made elsewhere that a layout change can quietly turn false.

    Warnings in both modes, deliberately. Both describe a room that is a little
    less tidy than its own commentary, not one that renders anything wrong: the
    wall panel leads with the case-file write-ups on the reasoning that every
    one of them is also hanging behind it as cover art, but nothing visible in
    the panel says so, and three builds can never have a preview at all. A
    check that fails CI should mean the site is wrong, not that a design note
    has aged — otherwise the red turns into something people learn to ignore,
    and the stale-map failure next to it is the one that matters."""
    lead = next((z for z in st['zones'] if z['screen'] == 'wall'), st['zones'][0])
    orphan = [t for t in featured() if t not in lead['titles']]
    if orphan:
        # Used to say the wall panel's lead was making a claim that had stopped
        # being true, because the room took FEATURED as written. It intersects
        # it with this zone now, so the claim holds by construction and what is
        # left to report is the other half: a name in FEATURED that no longer
        # does anything, which is worth knowing before you wonder why the
        # write-up you asked for is not at the top of the panel.
        print('warn: %s %s in FEATURED but no longer on zone %s, so %s write-up '
              'no longer leads the wall panel — it keeps a tile in the archive. '
              'Put it back in the layout, or take it out of FEATURED'
              % (', '.join(map(repr, orphan)),
                 'is' if len(orphan) == 1 else 'are', lead['zone'],
                 'its' if len(orphan) == 1 else 'their'), file=sys.stderr)
    have = set(clips_on_disk(CLIPDIR))
    silent = [t for t in st['seen'] if slug(t) not in have]
    if silent:
        print('warn: no clip for %s — hovering these covers gets a still. Run '
              'tools/clips.py, or check SKIP there for why it cannot have one'
              % ', '.join(map(repr, silent)), file=sys.stderr)


def do_check(st):
    """Validate and diff. Writes nothing, needs no Pillow, and is what CI runs."""
    claims(st)
    ok = st['ok']

    on_disk = open(GEN, encoding='utf-8').read() if os.path.exists(GEN) else None
    if on_disk is None:
        print('%s is missing — run python3 tools/wallsheet.py'
              % os.path.relpath(GEN, ROOT), file=sys.stderr)
        ok = False
    elif on_disk != st['gen']:
        # Name what moved rather than printing a diff: the two cases are "a
        # cover changed place" and "only the hash moved", and they need
        # different things doing about them.
        was = re.search(r'const WALL_SHEET_V="(\w+)"', on_disk)
        print('%s is stale — the layout has been edited without re-baking.\n'
              '  on disk: v=%s\n  layout:  v=%s\n'
              '  Run: python3 tools/wallsheet.py   (and commit the JPEGs with it)'
              % (os.path.relpath(GEN, ROOT), was.group(1) if was else '?', st['ver']),
              file=sys.stderr)
        ok = False

    have = open(ASSETV, encoding='utf-8').read() if os.path.exists(ASSETV) else None
    if have != st['assets']:
        # Named the same way the map above is: what is out of step, and what
        # doing about it. A thumbnail or a clip has been re-baked without this
        # file being regenerated, so its URL is unchanged and every browser
        # that has the old bytes will go on using them.
        print('%s is stale — a thumbnail or a clip has been replaced without '
              'its ?v= moving, so caches would keep the old file.\n'
              '  Run: python3 tools/wallsheet.py'
              % os.path.relpath(ASSETV, ROOT), file=sys.stderr)
        ok = False

    for rel, want in st['pages'].items():
        if open(os.path.join(ROOT, rel), encoding='utf-8').read() != want:
            print('%s: a shared script is loaded at the wrong ?v= — the page '
                  'would let a browser keep a stale copy of a file the page '
                  'reads globals from.\n  Run: python3 tools/wallsheet.py'
                  % rel, file=sys.stderr)
            ok = False

    src = open(LAYOUT, encoding='utf-8').read()
    if reference_table(st['games'], src) != src:
        print('%s: the id table at the foot is stale — run python3 '
              'tools/wallsheet.py' % os.path.relpath(LAYOUT, ROOT), file=sys.stderr)
        ok = False

    if ok:
        print('ok  %d zones, %d covers, %d props, %d clips, %d hashed assets, v=%s'
              % (len(st['zones']), len(st['seen']), len(st['surfaces']),
                 len(clips_on_disk(CLIPDIR)), st['assets'].count(':"'), st['ver']))
    return 0 if ok else 1


def do_bake(st):
    if not st['ok']:
        return 1
    if not all(bake(z['sheet'], z['titles'], z['cols'], z['rows'], z['cell'],
                    z['plate'], st['games'], st['by_title'], st['cats'])
               for z in st['zones']):
        return 1

    refresh_reference(st['games'])
    open(GEN, 'w', encoding='utf-8').write(st['gen'])
    open(ASSETV, 'w', encoding='utf-8').write(st['assets'])
    for rel, want in sorted(st['pages'].items()):
        path = os.path.join(ROOT, rel)
        if open(path, encoding='utf-8').read() != want:
            open(path, 'w', encoding='utf-8').write(want)
            print('%-28s ?v= refreshed on %d shared scripts'
                  % (rel, len(STAMPED)))
    print('%-28s %d files hashed'
          % ('demos/asset-v.js', st['assets'].count(':"')))
    print('%-28s %d zones, %d covers, %d props (%s), v=%s'
          % ('demos/wall-layout.js', len(st['zones']), len(st['seen']),
             len(st['surfaces']),
             ', '.join('%s %d' % (su['name'], len(su['resolved'])) for su in st['surfaces']),
             st['ver']))

    claims(st)
    print('note: demos/models/og.jpg is a photograph of this wall. Re-shoot and '
          're-run tools/ogimage.py if the back wall changed.', file=sys.stderr)
    return 0


def main(argv):
    unknown = [a for a in argv[1:] if a not in ('--check',)]
    if unknown:
        raise SystemExit('unknown argument %s — this takes --check or nothing'
                         % unknown[0])
    st = prepare()
    return do_check(st) if '--check' in argv else do_bake(st)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
