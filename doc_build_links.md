# Changing a build's links

`build_links.txt` at the repo root decides which links each build carries —
the WebGL build, the Play Store page, the video, the source — and therefore
which buttons its cards and its readout show. It is the only file to edit for
that.

Why it is built this way — see `docs/PROJECT.md`.

## The file

One block per build, headed by its id, with the four slots indented under it:

```
netcode-battle
  WebGL    https://webunity.github.io/webgl_netcode_battle/
  Android  https://play.google.com/store/apps/details?id=com.duyongoc.netcode.battle
  Youtube  https://www.youtube.com/watch?v=yqIDxTWt-Lk
  Youtube  https://www.youtube.com/watch?v=60D5mnJLUG8 | Youtube 2
  Source   -

kinder-easter
  WebGL    -
  Android  -
  Youtube  https://www.youtube.com/watch?v=D22sO9HlWPY
  Source   -
```

| Slot | What it is |
| --- | --- |
| `WebGL` | the browser build — the primary button wherever there is one |
| `Android` | the Play Store page — primary when there is no WebGL build |
| `Youtube` | the video |
| `Source` | the repository |

`-` is an empty slot. Every block carries all four so that reading down the
file says which build is still missing a store page, rather than leaving you to
notice an absence.

**The kinds are closed.** Those four, and nothing else. Each has its own case
in `actionOf` and `shortOf` in `demos/portfolio-shared.js`, and in `availOf`
and `ACT_OF` in `room-3d.html` — none of those four has a catch-all
branch, so a kind with no label is a missing label rather than a wrong one.
`playOf` names only WebGL and Android because it picks a priority, not a
label. A fifth kind is a code change in those four places, which is why the
tool stops on one rather than rendering a button nobody wrote the words for.

**Ids, not titles** — the same ids `build_layout.txt` uses. A typo is caught
with the nearest match named.

### A second link of the same kind

Add a line. The four slots are the template, not a limit, and a repeated kind
needs a label so its button says something other than what the first one says:

```
  Youtube  https://www.youtube.com/watch?v=60D5mnJLUG8 | Youtube 2
```

The order of the lines is the order the buttons appear in. Which one gets the
primary treatment is not up to the order: it is the WebGL link, else the
Android one, else whatever is first.

### A build with no links

Allowed. Every slot can be `-`, and the tool says so on every run:

```
warning                no links, so no button row: demo-dental-3d
```

Its cards still render — art, category, description — with no button row, and
where the whole card is normally a link it becomes an ordinary card that does
not pretend to open anything.

## Baking

```sh
python3 tools/links.py        # build_links.txt  -> demos/portfolio-data.js
python3 tools/wallsheet.py    # then this, for the ?v=
```

Both, in that order, and the tool says so. `links.py` writes
`portfolio-data.js`; `wallsheet.py` hashes that file into the `<script src=>`
of both pages, so baking the wall first stamps the version of the data that is
about to be replaced and the browser is told nothing changed.

`python3 tools/serve.py` runs both on save and reloads the page, which is the
whole gesture day to day.

**An error stops the run before anything is written**, and every error in the
file is reported in one go:

```
build_links.txt:12: no build with id 'netcode-batle' (did you mean 'netcode-battle'?) — …
build_links.txt:14: 'Webgl' is not a link kind — they are WebGL, Android, Youtube, Source
build_links.txt:15: Youtube url 'ftp://nope/' is not http(s) — every one of these opens in a new tab
```

## Adding a build

Add it to `demos/portfolio-data.js` first, then run `python3 tools/links.py`:
it appends an empty block for any build that has none, so the four slots are
waiting in the file rather than the build silently rendering with no buttons.
Fill them in and run it again.

## Checking without baking

    python3 tools/links.py --check

Every validation the bake does, plus a comparison of the `links` and `tags` it
would write against what is committed in `portfolio-data.js` — so "edited
build_links.txt and forgot to bake" is a failure with a message rather than a
button that quietly does not appear. It writes nothing. CI runs it on every
push, before the wallsheet check: a stale `build_links.txt` would otherwise
surface as a wrong `?v=`, which is the wrong place to go looking.

## Getting it onto the site

GitHub Pages runs no Python, so `build_links.txt` is inert there — what the
pages read is `portfolio-data.js`. The commit has to carry the output:

```sh
python3 tools/links.py && python3 tools/wallsheet.py
git add build_links.txt demos/portfolio-data.js
git add room-3d.html demos/portfolio-2d.html      # the ?v= moved
```

## What is not in this file

`tags` — it is the list of kinds with duplicates dropped, and `links.py`
derives it. It was a hand-kept field in `portfolio-data.js` that was, measured
across all 33 builds, exactly that and never anything else.
