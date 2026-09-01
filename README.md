# profile

https://duyongoc.github.io/profile/

- Default entry: 3D portfolio (`demos/room-3d.html`) — the root redirects here
- 2D portfolio: `demos/portfolio-2d.html` — same 33 builds, no WebGL

Both pages read `demos/portfolio-data.js` (the 33 projects) and
`demos/portfolio-shared.js` (categories, jobs, and the link and markup helpers
they share). Nothing is loaded from a CDN; three.js and its two loaders are
vendored in `demos/lib/`.

A project is classified by its `cat` and nothing else — the section heading,
the labels and the accent colour all belong to the category and live in `CAT`
in `portfolio-shared.js`, which is also where `tools/wallsheet.py` reads them
from when it bakes the covers.

## Checks

Two, both fast, both needing nothing installed, both run in CI on every push:

```sh
python3 tools/wallsheet.py --check   # the wall map matches wall-layout.txt
python3 tools/jscheck.py             # every shipped script parses (wants node)
```

The first is the one that matters: it catches a layout edited without
re-baking, which otherwise shows up as the wall simply not changing.
The room's own in-browser harness is still `#qa=1` — see `PROJECT.md`.

## Changing what hangs on the walls

What the room shows, and in what order, is `wall-layout.txt` at the repo root —
a heading per wall or prop, then the builds under it by id. Edit it, then
`python3 tools/wallsheet.py` to bake the sheets and regenerate the map the room
reads. Both come out of that one run, and both have to be committed: the site
is static and Pages runs no Python.

**[wall-layout.md](wall-layout.md)** is the guide — the format, the `auto`
rules the props can take, how to read the bake output, and how to publish a
change.

## Run locally

The pages use ES modules, so they need a server — opening the file directly
will not work.

```sh
python3 tools/serve.py
```

Open `http://127.0.0.1:8000/`. It also watches `wall-layout.txt` and the data
files and re-bakes the walls when one is saved — see
[wall-layout.md](wall-layout.md). Nothing it does ships.
`python3 -m http.server 8000 --bind 127.0.0.1` works too, without the watching.

To test on a phone connected to the same trusted Wi-Fi, bind the server to the
LAN and open `http://<PC-LAN-IP>:8000/` on the phone:

```sh
python3 tools/serve.py --bind 0.0.0.0
```

Stop the server with `Ctrl+C` when testing is finished.

## Mobile display

The 3D room requests browser fullscreen on the first canvas gesture where the
Fullscreen API is available. On iPhone, use **Share → Add to Home Screen**;
launching that icon uses the manifest's fullscreen display mode and safe-area
layout. A normal Safari tab keeps Safari's own browser chrome by design.

WebGL renders at up to 2 device pixels per CSS pixel with antialiasing and
anisotropic filtering for screen/image textures. The tightly packed low-poly
palette atlases use nearest sampling to prevent colour bleeding between UV
islands. This keeps Retina phones sharp without paying the full fill-rate cost
of a 3x panel.

## Baked assets

Everything under `demos/models/`, plus `demos/wall-layout.js`, is generated
rather than hand-made. All of it is committed — the site is static, with no
build step — so re-run the tool when the source it reads has changed and commit
the result. Each one is idempotent.

| File | Tool | Rebuild when |
| --- | --- | --- |
| `wall.jpg`, `wall-left.jpg`, `wall-right.jpg`, `wall-layout.js` | `tools/wallsheet.py` | `wall-layout.txt`, a title, a thumbnail, or a category colour changes |
| `badge.jpg`, `avatar.jpg` | `tools/badge.py` | the photo or the ID details change |
| `og.jpg` | `tools/ogimage.py` | the room's look changes — this is the link preview |
| `cybercity.png`, `scifi.png` | `tools/atlastint.py` | never, unless a new Synty pack is added |
| `clips/*.mp4` | `tools/clips.py` | a wall cover changes, or its video is re-cut |
| `sofacat.glb`, `chairplush.glb` | `tools/sculptglb.py` | never, unless the model is replaced |

`tools/ogimage.py` composes from `tools/og-source.png`, a headless capture of
the room; its docstring has the command that takes a fresh one.

`tools/fbx2glb.py` converts a Synty `.fbx` into the `.glb` the room loads.
`tools/portfolio.py` is not a bake step — it is what every other tool reads the
project data, the category table and the slug rule through, so there is one
implementation of each rather than one per tool.
