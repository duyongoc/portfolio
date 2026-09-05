# duyongoc.github.io

https://duyongoc.github.io/

A portfolio for a Unity/Unreal game developer, built as a room you look around
rather than a page you scroll.

- Default entry: 3D portfolio (`room-3d.html`) — the root redirects here
- 2D portfolio: `demos/portfolio-2d.html` — same 33 builds, no WebGL

Both pages read `demos/portfolio-data.js` (the 33 projects) and
`demos/portfolio-shared.js` (categories, jobs, and the link and markup helpers
they share). Nothing is loaded from a CDN; three.js and its two loaders are
vendored in `demos/lib/`.

A project is classified by its `cat` and nothing else — the section heading,
the labels and the accent colour all belong to the category and live in `CAT`
in `portfolio-shared.js`, which is also where `tools/wallsheet.py` reads them
from when it bakes the covers.

## Running it

The pages are ES modules, so they need a server:

```sh
python3 tools/serve.py      # → http://127.0.0.1:8000/
```

Everything else operational — the three checks, the bake steps, the local
server's watch-and-rebake, headless capture — is **§ 7 of
[docs/PROJECT.md](docs/PROJECT.md)**.

## Documentation

| | |
| --- | --- |
| [docs/PROJECT.md](docs/PROJECT.md) | how the repository is put together, why the load-bearing decisions were made that way, and how to run it |
| [docs/decisions.md](docs/decisions.md) | the working out — prop tunings and the change logs |
| [doc_build_layout.md](doc_build_layout.md) | editing `build_layout.txt` — what hangs on which wall, and baking it |
| [doc_build_links.md](doc_build_links.md) | editing `build_links.txt` — the links each build carries |

## Licence

All rights reserved — see [`LICENSE`](LICENSE). The source is published to be
read, not reused; ask first for anything beyond that.

three.js, the two Sketchfab models (`sofacat.glb`, `chairplush.glb`, both
CC BY 4.0) and the Synty POLYGON props keep their own licences and are listed
individually in `LICENSE`.
