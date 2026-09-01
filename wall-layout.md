# Changing what the room shows

`wall-layout.txt` at the repo root decides which build hangs where, and in what
order. It is the only file to edit for that. This is how to edit it, how to
bake the result, and how to get it onto the site.

Why it is built this way — see `PROJECT.md`.

## The file

A heading, then the builds under it, in reading order — left to right, top to
bottom. Line breaks are cosmetic; the grid decides where a cover lands.

```
zone 1
  netcode-battle | netcode-demo | netcode-shooter2d | kinder-easter
  polygon-battle | polygon-adventure | polygon-turnbase | color-shoot-2d
  joust-them-all | beat-em-up-2 | survivor-io-clone-2d

trash
  archer-2d | jump-2d | math-game-2d

monitor
  auto section=RESKIN
```

| Heading | What it is |
| --- | --- |
| `zone 1` | the back wall behind the desk — a 4x3 grid, the last cell a count plate |
| `zone 8` | the left wall — 1x3 |
| `zone 9` | the right wall — 1x4 |
| `trash` | the bin: the builds with a scrap of paper sticking out |
| `monitor` | the reskin monitor |
| `tablet` | the AR tablet |
| `showreel` | the hologram |

**Use the id, not the title.** The table at the foot of the file lists every
build and its id to copy from, and the tool regenerates it on every bake so it
cannot go stale. A full title works too — it slugs down to the same id — but
copying a title by hand is where an edit goes wrong.

Everything from the `── ALL GAMES ──` marker down belongs to the tool and is
rewritten on every run. Anything you want to keep goes above it.

### Rules, for props only

A prop can take a rule instead of a list:

```
monitor
  auto section=RESKIN     every build in that section
showreel
  auto link=Youtube       every build with a link of that kind
```

The section names are the `section` fields of `CAT` in
`demos/portfolio-shared.js`. That is the only place they are written down —
a project does not carry one — so a name that is not one of them stops the bake
and lists the ones that are.

The room evaluates a rule against live data, so a new reskin reaches the reskin
monitor by *being* a reskin — nobody re-runs anything. A list is taken exactly
as written. Both on one prop is an error: pick one.

Walls cannot take a rule. Their covers are pixels in a baked JPEG, so they have
to be named.

### What is not in this file

A wall's grid, cell size, and whether it ends in a count plate are `ZONES` in
`tools/wallsheet.py`. They are paired with a plane of a matching shape in the
room, so changing one means reshaping the other — not what anyone opens the
layout to do.

The grid belongs to the zone: a build moved from zone 1 to zone 8 renders at
zone 8's cell size. Each zone's list has to fit `cols * rows` cells, less one
where the zone carries a plate — zone 1 holds 11, zone 8 holds 3, zone 9
holds 4.

Changing a grid is a two-file job, and the second file is easy to forget. The
grid lives in `ZONES` in `tools/wallsheet.py`, and it sets the baked sheet's
proportions; the plane that sheet is painted onto lives in the `sideWall(...)`
calls near the end of `demos/room-3d.html`. Change one without the other and
every cell boundary drifts off the tile it brackets, a little more with each
row. Load the room with `#qa=1` after any grid change — the *Wall cover
mapping* row compares the two and says which zone is wrong.

## Editing, day to day

```sh
python3 tools/serve.py        # → http://127.0.0.1:8000/
```

Edit the file, save, and the open page reloads on the new layout. That is the
whole gesture: the server bakes for you and reloads. A layout that does not
parse leaves the last good sheets in place and prints why, so a typo never
drops you into a broken room.

## Baking by hand

The same thing `serve.py` runs on save, for when the server is not up:

```sh
python3 tools/wallsheet.py
```

```
demos/models/wall.jpg        1600x735   4x3  11 tiles + plate   279 kB  aspect 2.177
demos/models/wall-left.jpg    560x1029  1x3   3 tiles           110 kB  aspect 0.544
demos/models/wall-right.jpg   560x1372  1x4   4 tiles           109 kB  aspect 0.408
demos/wall-layout.js         3 zones, 18 covers, 4 props (trash 6, monitor 15, tablet 3, showreel 30), v=1736cdd6
```

Four lines, four files written. Worth a glance:

- **the cover count** — how many ids the zones actually hold. A line deleted by
  accident shows up here and nowhere else.
- **`v=`** — a content hash of the layout, the fields the tiles are drawn from,
  and the thumbnails. It moves when the pixels do, and it is what stops a
  returning visitor being served the old wall out of cache.

**An error stops the run before anything is written** — every zone is checked
before the first sheet is drawn, so a mistake in the last zone cannot leave new
pixels beside an old map. It names the entry and the zone, all of them in one
run, and the room keeps the sheets it had.

```
wall-layout.txt: zone 9 has no game 'nope-not-a-game' — the ids are listed at the foot of that file
```

**A warning means the files were written**, and something claimed elsewhere may
have just become false:

| Warning | What to do |
| --- | --- |
| no clip for *X* | hovering that cover gets a still — `python3 tools/clips.py`. Three builds have no YouTube link at all and so can never have one: Topdown Sword, Game3d Racing, Game2d Black Ops |
| a case file no longer hangs on zone 1 | the wall panel says all six do — fix the layout, or the copy in `room-3d.html` |
| `og.jpg` is a photograph of this wall | the link preview is now stale; re-shoot it and run `tools/ogimage.py` |

`#qa=1` in the room checks the cell-to-game mapping and each sheet's
proportions against the plane it is mapped onto.

## Getting it onto the site

GitHub Pages serves the repo as it stands and runs no Python. `wall-layout.txt`
is inert there — what the room reads is the baked JPEGs and the generated JS —
so the commit has to carry the output, not just the input:

```sh
python3 tools/wallsheet.py
git add wall-layout.txt demos/wall-layout.js demos/models/wall*.jpg
git commit -m "reorder the wall" && git push
```

Committing only the `.txt` fails in the way worth naming: locally it looks
right, because that machine baked, and the deployed room does not move. The
machine that made the change is the one machine that cannot see the change
missing.

## Adding a build

Add it to `demos/portfolio-data.js` first — that is the canonical list, and a
build the layout names but the data does not stops the bake. Then put its id in
`wall-layout.txt` if it belongs on a wall or a prop; a build matched by a
prop's `auto` rule needs nothing.

A cover on a wall wants a preview clip: `python3 tools/clips.py` (it reads the
generated map, so bake the wall first), then bake the wall again to fold the
result in. As of now every build that has a YouTube link already has a clip —
`python3 tools/clips.py --all --skipped` cut the rest ahead of time, so a build
promoted onto a wall arrives with its preview already on disk. Offsets, crops
and the previews that were measured and rejected are `STARTS`, `CROPS` and
`SKIP` in that script; `SKIP` is a record now, not a gate, so a rejected preview
goes live as soon as its build reaches a wall.

## Checking without baking

    python3 tools/wallsheet.py --check

Every validation the bake does, and a comparison of the generated
`demos/wall-layout.js` against the committed one — so "edited the layout and
forgot to re-bake" is a failure with a message rather than a wall that quietly
does not change. It writes nothing and needs no Pillow. CI runs it on every
push.
