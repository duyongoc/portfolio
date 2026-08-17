# profile

https://duyongoc.github.io/profile/

- Default entry: 3D portfolio (`demos/room-3d.html`) — the root redirects here
- 2D portfolio: `demos/portfolio-2d.html` — same 33 builds, no WebGL

Both pages read `demos/portfolio-data.js` (the 33 projects) and
`demos/portfolio-shared.js` (categories, jobs, link helpers). Nothing is loaded
from a CDN; three.js and its two loaders are vendored in `demos/lib/`.

## Run locally

The pages use ES modules, so they need a server — opening the file directly
will not work.

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/`.

To test on a phone connected to the same trusted Wi-Fi, bind the server to the
LAN and open `http://<PC-LAN-IP>:8000/` on the phone:

```sh
python3 -m http.server 8000 --bind 0.0.0.0
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

Four things under `demos/models/` are generated rather than hand-made. Re-run
the tool when the source it reads has changed; each one is idempotent.

| File | Tool | Rebuild when |
| --- | --- | --- |
| `wall.jpg` | `tools/wallsheet.py` | the hero list or a thumbnail changes |
| `badge.jpg`, `avatar.jpg` | `tools/badge.py` | the photo or the ID details change |
| `og.jpg` | `tools/ogimage.py` | the room's look changes — this is the link preview |
| `cybercity.png`, `scifi.png` | `tools/atlastint.py` | never, unless a new Synty pack is added |

`tools/ogimage.py` composes from `tools/og-source.png`, a headless capture of
the room; its docstring has the command that takes a fresh one.

`tools/fbx2glb.py` converts a Synty `.fbx` into the `.glb` the room loads.
