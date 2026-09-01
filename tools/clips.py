#!/usr/bin/env python3
"""Bake the hover-preview clips the room's wall readout plays.

Hovering a cover on the wall opens a readout (#hud in room-3d.html) that wants
to show the game moving, not a still. The obvious way to get that is a YouTube
iframe, and it is the wrong way twice over: it fetches from a third-party origin
on hover, which the room does nowhere else, and a sweep across eleven covers
would build and tear down eleven whole documents.

So the motion is baked here instead. Measured, for one 4-second preview:

    GIF 15fps, 640x360      1.5 - 3 MB      256 colours, no interframe coding
    MP4 H.264 CRF 31        100 - 150 KB    better picture, seekable, cheap

Fifteen to twenty-five times smaller for a better image, which is the whole
argument. Nothing here is fetched until a pointer actually rests on a tile, so
none of it lands in the room's ~2 MB boot payload.

640x360 is sized from the readout: the preview box is ~340 CSS px wide, so 680
device pixels at DPR 2. Anything above 720p is bytes the box cannot show.

Sources are the project's own YouTube links in demos/portfolio-data.js, and
which builds get a clip comes from wall-layout.txt. Where to cut each one, what
to crop out of it and which sources cannot make a preview at all are STARTS,
CROPS and SKIP below. Needs yt-dlp and ffmpeg on PATH:

    brew install yt-dlp ffmpeg
    python3 tools/clips.py              # bake every wall cover that has a video
    python3 tools/clips.py --all        # every build in the dataset, wall or not
    python3 tools/clips.py --skipped    # with --all, include the SKIP list too
    python3 tools/clips.py --list       # the ids on disk, one per line
    python3 tools/clips.py --force      # re-bake clips that already exist
    python3 tools/clips.py --cache DIR  # keep the downloads, for picking offsets

Idempotent: a clip that already exists is left alone unless --force is given.
Which titles it works on comes from wall-layout.txt, or from the whole dataset
under --all. Nothing here has to be pasted anywhere: run
`python3 tools/wallsheet.py` afterwards and the room's CLIP_OF map is
regenerated from whatever ended up in demos/clips/.

--all exists because a clip outlives the wall it was cut for: the layout moves,
and a build promoted onto a wall next month should not have to wait on a
download. Only the wall hovers, so a clip for a build that is not on a wall
costs nothing at runtime — it is not in the boot payload and nothing fetches it
— but it IS committed bytes, and once it is on disk wallsheet.py will put it in
CLIPS, so a build that later reaches a wall gets it live with no further
decision. That is the trap --skipped opens: SKIP is a quality verdict, and
baking past it means the room will happily play a preview that was looked at
and rejected.

The slug that names each file, the project list and the wall map are all read
through tools/portfolio.py — this file used to carry its own copy of the first
two, and the docstring on the other copy said they had to agree.
"""
import os, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portfolio import ROOT, CLIPDIR, games, slug, wall_zones, clips_on_disk

OUT = CLIPDIR

DUR = 4             # long enough to read as gameplay, short enough to loop
START = 12          # default: past the title card most of these open on

# Per-title offsets, picked by sampling each source at six points and looking
# at the result. The default lands on a pair of editor windows in the netcode
# captures and on the parental disclaimer in the Kinder recording, and a
# preview showing neither the game nor anything else legible at 340 px is worse
# than the still it replaced. Every one of these avoids a menu, a modal and a
# title card. Re-pick with --cache and a contact sheet if a source is replaced.
STARTS = {
    'Netcode Battle': 113,        # 0-40s is the two-client lobby, not the game
    'POLYGON Battle': 176,        # first two minutes are skill and inventory UI
    'Kinder Easter': 99,          # opens on the parental disclaimer, twice
    'POLYGON Adventure': 105,     # 85s and 125s are both the character select
    'Netcode Shooter2D': 79,      # lobby windows until ~45s
    'POLYGON Turnbase': 181,      # chapter select sits in the middle
    'Joust them all': 49,         # 68s is the POWER CLASH overlay
    'Netcode Demo': 82,
    "Beat'em up 2": 90,           # opens on black
    'Color Shoot 2d': 20,         # 32s is an update prompt over the game
    # the side columns. The card game's source is a 42-minute compilation, so
    # the default 12s is its character-select screen; 180s and 480s are a turn
    # banner and a recruit modal. 950s is a card resolving against a full board.
    'Cardgame Battle 2d': 950,
    # Both of these were rejected on a first pass and both rejections were
    # wrong, for the same reason: the default 12s is a menu. Sampling four
    # points across each found gameplay with the contrast of the ones that
    # work — worth keeping, because the cheap check (look at the thumbnail)
    # and the right check (sample the video) disagree here.
    'Battle Board 2d': 220,       # 12s is the team builder, 60s the first turn
    'Game 2d5 Dungeon': 120,      # opens on a loading bar and a menu
    # The AR pair. AAF's default lands on the avatar dressing room, and the
    # racing that follows it is fenced by name banners — 64s, 72s and 100s each
    # carry one across the middle of the frame, which is exactly where a
    # portrait source gets centre-cropped to. 88s is a kart, a coin and a boost
    # trail with nothing written over them.
    'AAF': 88,
    # 12s to 30s is the phone panning across a blank grey wall, and 24s is a
    # black frame with a red bar. 36s is the rooftop skyline with three of the
    # creatures in it, which is the only thing in the video that reads as AR.
    'AR demo': 36,
    # Cropped to its canvas this one is legible, but 12s is the equipment
    # screen and 30s is an empty street. 88s is the wave closing in, which is
    # the only four seconds that say what the game is.
    'Survivor.io clone 2d': 88,
}

# The three netcode captures are recordings of the Unity editor running two
# clients side by side, so most of each frame is title bars and a Console. Two
# illegible game views plus log spam is a worse preview at 340 px than one
# legible view, and the readout header already says Multiplayer / Netcode. Each
# rect is the left Game view, measured off a full-resolution frame.
# These rects are pixels on a 1280x720 source, which is what the format
# selector in source() still lands on for a 16:9 video. Re-measure them if that
# ever changes.
#
# The second group is a different capture entirely and the same problem: five
# of these videos are a screen recording of Edge with the Unity WebGL build
# running in a tab, so the frame is browser chrome, a URL bar and a field of
# page white with a 400x600 canvas somewhere in the middle. Uncropped they are
# a screenshot of a browser, which is what SKIP measured them as; cropped to
# the canvas they are the game, and the portrait canvas then gets the same
# centre band that any phone capture gets. Located by taking the standard
# deviation of six frames and finding the region that actually moves — page
# white does not, and neither does chrome.
CROPS = {
    'POLYGON Battle': (1066, 600, 108, 78),   # windowed editor capture too
    'Netcode Battle': (630, 354, 8, 110),
    'Netcode Demo': (630, 354, 6, 124),
    'Netcode Shooter2D': (626, 352, 12, 122),
    'Subway Clone 3d': (400, 600, 426, 46),   # the WebGL canvas in the tab
    'Survivor.io clone 2d': (400, 600, 426, 46),
    'Demo Dental 3d': (525, 528, 342, 41),
    'Archer 2d': (540, 720, 370, 0),          # fullscreen portrait, blue surround
    'Shoot ball 3d': (408, 692, 478, 28),     # fullscreen portrait, olive surround
}

# Per-title quality override. The cropped netcode-demo is four seconds of
# full-screen particle effects, which is the worst case for a fixed CRF: at 31
# it came out at 289 KB, well past the 200 KB that keeps a hover feeling
# instant. The extra compression is invisible in a 340 px box.
# AAF is the same case: four seconds of karts, boost trails and coin sparkle,
# all of it moving, which at 31 came out at 216 KB.
# Subway Clone 3d joins them once cropped: the canvas is a scrolling track at
# full frame rate, and at 31 it came out at 206 KB.
CRFS = {'Netcode Demo': 35, 'AAF': 35, 'Subway Clone 3d': 35}

# Sources that cannot make a good 16:9 preview. The readout falls back to the
# cover art, which is what it shows before a clip loads anyway.
# Baked, looked at, and rejected. Kept here with the reason so the next pass
# does not spend another download finding the same thing out. Two failure modes
# recur: a portrait capture pillarboxed into 16:9, which is mostly surround at
# 340 px, and a scene so dark that the preview reads as a black rectangle —
# measured as the greyscale standard deviation of the first frame, where the
# ones that work land near 30-40 and the ones that do not sit under 20.
SKIP = {
    'Survivor.io clone 2d': 'portrait capture pillarboxed into 16:9 — at 340 px '
                            'the preview is mostly white surround',
    'Subway Clone 3d':      'portrait capture pillarboxed into 16:9, white surround',
    'Archer 2d':            'portrait capture pillarboxed into 16:9, blue surround',
    'Shoot ball 3d':        'portrait capture pillarboxed into 16:9, olive surround',
    'Game Nightmares':      'too dark to read at 340 px (stddev 17 against ~35 for '
                            'the ones that work)',
    'Game Shooter 2d':      'almost no contrast — a grey field with a few dots '
                            '(stddev 12-15 across four offsets)',
    'Math Game 2d':         'a narrow portrait board on a flat pale field, stddev 7-14',
    'Find Monkey 2d':       'same shape as Math Game 2d, stddev 13-18',
    'Demo Dental 3d':       'legible but white-on-white clinical UI — it reads as a '
                            'web tool, and nothing in this room is that colour',
    'City zombie':          'mean luminance 215 — a near-white plane with small figures',
    'Endless car 3d':       'stddev 13-14, flat grey road',
    'Jump 2d':              'stddev 22 but mean 190 — small blocks on a wide beige band',
}
W, H = 640, 360
CRF = 31


def youtube_of(g):
    for l in g.get('links', []):
        if l.get('kind') == 'Youtube':
            return l['url']
    return None


def need(binary):
    if shutil.which(binary):
        return True
    print(f'  ! {binary} not on PATH — brew install {binary}', file=sys.stderr)
    return False


def source(name, url, cache):
    """Fetch the source video, keeping it if a cache directory was given.

    Choosing an offset means looking at several points in a video, so the
    download is worth keeping between runs while the offsets are being picked.
    The cache lives outside the repo and nothing published depends on it."""
    raw = os.path.join(cache, name + '.src.mp4')
    if os.path.exists(raw):
        return raw, None
    # Selected on width, not height, and the difference is the whole picture
    # quality of a portrait source. The output is a 640x360 landscape crop, so
    # width is the axis that survives; capping height at 720 caps a 1080x2400
    # phone capture at its 288x640 rendition, which is then upscaled 2.2x to
    # fill the frame. Measured on AAF: 288 wide reads as a smear, 1080 wide
    # downscales clean. -S +width takes the SMALLEST rendition clearing the
    # bar rather than the biggest, so a 16:9 source still comes down as the
    # 1280x720 it always did — which is what keeps the CROPS rects valid.
    dl = subprocess.run(
        ['yt-dlp',
         '-f', 'bv*[width>=1280][ext=mp4]+ba[ext=m4a]/bv*[width>=1280]+ba/'
               'bv*[width>=640][ext=mp4]+ba[ext=m4a]/bv*[width>=640]+ba/bv*+ba/b',
         '-S', '+width',
         '--merge-output-format', 'mp4', '-o', raw, '--no-playlist',
         '--no-warnings', '-q', url],
        capture_output=True, text=True)
    if dl.returncode != 0 or not os.path.exists(raw):
        tail = (dl.stderr.strip().splitlines() or ['?'])[-1]
        return None, tail
    return raw, None


def bake(title, url, force, cache):
    name = slug(title)
    dest = os.path.join(OUT, name + '.mp4')
    if os.path.exists(dest) and not force:
        print(f'  = {name}.mp4 ({os.path.getsize(dest)//1024} KB, kept)')
        return True
    keep = cache is not None
    tmp = cache if keep else tempfile.mkdtemp()
    try:
        raw, err = source(name, url, tmp)
        if not raw:
            print(f'  ! {name}: download failed — {err}')
            return False
        start = STARTS.get(title, START)
        pre = ''
        if title in CROPS:
            cw, ch, cx, cy = CROPS[title]
            pre = f'crop={cw}:{ch}:{cx}:{cy},'
        # -an, not a muted track: an audio stream nothing can ever play is
        # pure payload. yuv420p is what Safari will decode; +faststart lets
        # playback begin before the file has finished arriving.
        enc = subprocess.run(
            ['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(start), '-t', str(DUR),
             '-i', raw, '-vf', f'{pre}scale={W}:{H}:force_original_aspect_ratio=increase,'
                               f'crop={W}:{H},fps=24',
             '-an', '-c:v', 'libx264', '-profile:v', 'main', '-pix_fmt', 'yuv420p',
             '-crf', str(CRFS.get(title, CRF)), '-movflags', '+faststart', dest],
            capture_output=True, text=True)
        if enc.returncode != 0:
            print(f'  ! {name}: encode failed — {enc.stderr.strip()[:160]}')
            return False
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)
    kb = os.path.getsize(dest) // 1024
    flag = '  (over 200 KB — consider a higher CRF)' if kb > 200 else ''
    print(f'  + {name}.mp4 ({kb} KB){flag}')
    return True


def main():
    force = '--force' in sys.argv
    every = '--all' in sys.argv
    past_skip = '--skipped' in sys.argv
    cache = None
    if '--cache' in sys.argv:
        cache = sys.argv[sys.argv.index('--cache') + 1]
        os.makedirs(cache, exist_ok=True)
    all_games = games()
    by_title = {g['title']: g for g in all_games}

    if '--list' in sys.argv:
        have = clips_on_disk(OUT)
        for h in have:
            print(h)
        print(f'\n{len(have)} clip(s) on disk. tools/wallsheet.py turns these into '
              f'CLIP_OF in demos/wall-layout.js.')
        return 0

    if not (need('yt-dlp') and need('ffmpeg')):
        return 1
    os.makedirs(OUT, exist_ok=True)

    # The wall by default, the whole archive under --all. Every cover that can
    # be hovered, taken out of the generated wall map rather than out of the
    # layout text: the walls are what hover, this is the same list the room
    # indexes its covers against, and one parser for that file is enough — it
    # lives in tools/portfolio.py. The props in the layout carry thirty builds
    # between them and none of them hovers, so none of them wants a clip.
    #
    # wall_zones() is only called in the second case: --all is exactly the mode
    # that should still work when the wall map is stale or was never generated.
    targets = [g['title'] for g in all_games] if every else wall_zones()

    ok = skipped = 0
    for title in targets:
        g = by_title.get(title)
        if not g:
            print(f'  ! {title}: not in portfolio-data.js')
            continue
        if title in SKIP and not past_skip:
            print(f'  - {slug(title)}: skipped — {SKIP[title]}')
            skipped += 1
            continue
        if title in SKIP:
            print(f'  ~ {slug(title)}: baking past SKIP — {SKIP[title]}')
        url = youtube_of(g)
        if not url:
            print(f'  - {slug(title)}: no YouTube link, readout keeps the poster')
            skipped += 1
            continue
        ok += bake(title, url, force, cache)

    total = sum(os.path.getsize(os.path.join(OUT, f))
                for f in os.listdir(OUT) if f.endswith('.mp4'))
    print(f'\n{ok} clip(s) ready, {skipped} without a source, {total//1024} KB on disk.')
    print('Now run  python3 tools/wallsheet.py  to fold this into '
          'demos/wall-layout.js.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
