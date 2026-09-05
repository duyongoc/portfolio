# Decisions — the long version

`PROJECT.md` is the contract: how this repository is put together, and what a
change to any part of it has to keep true. This file is the archaeology behind
it — how four separate props were got wrong before they were got right, and the
change log of two UI passes.

It is split out because the two are read at different times and by different
people. Somebody about to move a game onto a wall needs the contract, and needs
it short enough that they read it. Somebody about to re-tune the vent, replace
the cat, or wonder why the panel is not simply a fixed width needs this — and
needs it to still exist, because every section below is a mistake that was
expensive to find and is cheap to make again.

Nothing here is a rule. The rules were lifted into
[PROJECT.md § 8](PROJECT.md#8-if-you-change-one-thing-know-this) as they were
found; what is left below is the working out.

---

## Props that took several passes

### Steam and air are different shapes, not different densities

The draught spent four tunings looking like the steam off a bowl of pho, and the
first three of those adjusted the wrong variable. Dimming it, respacing it,
reversing it from sinking to rising, halving and doubling the gain — none of it
moved the read at all, because **what says "cooking" is the silhouette, and the
silhouette was never what was being changed.**

Steam is a *point source that rises*: it leaves a small opening, gathers into a
column, and billows upward. Everything about the first version was that. Air
from a grille is the opposite on every axis, and it takes all four to work:

- **A face, not a point.** The grille is 3.3 tall and 3.5 deep and air leaves all
  of it at once, so a puff is born anywhere across that face rather than in a
  cluster at its middle.
- **Sideways, not up.** 5.6 out against a per-puff vertical of -0.4 to +1.1 —
  and about a fifth of them are negative. A column needs every particle to agree
  on up; disagreeing is what makes a body of air disperse instead of tower.
- **Diverging, not parallel.** A puff born off the centre of the grille keeps
  moving away from it, so the sheet widens as it travels. Without that term
  twelve puffs run in parallel and the thing stays grille-shaped all the way
  across the room, which reads as a slab.
- **Streaks, not discs.** The one that finally did it. Air in motion reads as
  marks drawn along the direction it is moving, so the sprites are stretched
  2:0.8 rather than square. This works only because sprites billboard and yaw is
  clamped to -.5..0.45, so world +x never swings far off screen-right on this
  wall; it would be the wrong trick on a prop that can be walked around.

**Every puff passes through the same small volume at the mouth**, so whatever
alpha they carry at u=0 gets stacked twelve deep there and the vent grows a
bright ball on it. That, not the overall gain, is why two separate envelopes read
as a glow. The fix is to enter faint rather than to dim everything: `u^1.2` is
only at .26 a tenth of the way through a life, and twelve of those overlapping is
the density the mouth should have. Full in the middle of the run, where the puffs
have diverged and each is on its own.

**A prop's constraints can point the opposite way from how they read.** The
draught fell for one draft, on the grounds that cool vapour sinks and that the
ceiling ribs, 4.9 above the top of the housing, would swallow anything rising.
The ribs are never reached — a puff has faded out well below them, which rendered
frames confirm — and one that did reach a rib would be depth-clipped by it, which
looks like air passing behind a rib rather than like an error. Meanwhile the
constraint nobody had written down was underneath: the game grid tops out at
y=32 and the vent's mouth is at 30, so **falling was the one direction that put
the effect over the work.**

Under `prefers-reduced-motion` the puffs are simply not there. A draught is
nothing but motion, and a frozen cloud on a wall is a smudge rather than a
reduced form.

**Eyeballing a translucent effect does not work; diff two frames.** Every pass
looked like "a faint blur near the grille" in a screenshot and it was impossible
to tell whether the far puffs were being drawn at all. Rendering the same frame
with the puffs hidden behind a query parameter and differencing the two answers
it in numbers: the bounding box gives the reach, the peak delta gives the
strength, and the mean delta per column across the drift gives the shape of the
falloff — which is how the bright ball at the mouth was found, as a first column
running hotter than the rest. Peak delta ran 75/255 at the first tuning, 142 when
that was asked to double, 87 as a streak fan, and 25 once it was asked to go 70%
fainter.

It is also the only way to answer "make it 70% fainter" correctly, because
**opacity does not compose linearly and a percentage asked of a translucent
effect is a percentage of what is seen, not of the constant.** Twelve billboards
overlap, and n layers of alpha a composite as `1-(1-a)^n`; scaling the gain to
.30 measured 32/255 against 87, which is .37 of what it was, not .3. The gain was
set from the render instead — .236 lands on 25. Halve the measurement, never the
constant.

A blank result is a bug, not a reading. One A/B pass came back with a peak delta
of exactly 0 and byte-identical PNGs, which no animated scene can produce: the
local server had been started from `demos/` rather than the repo root, so both
frames were the same 404 page. A metric that can only be produced by working
renders is worth more than one that degrades quietly.

**Reading order is the argument.** Row 1 is the three netcode builds, so the
rarest thing in the set is the first thing seen. Row 2 is the POLYGON trio, and
POLYGON Battle sits directly under Netcode Battle because it *is* that game
before it went online — the data says so in its own description, and until the
rows were paired the two hung in unrelated cells and nobody could read it. Row 3
is everything else, and column 4 takes the odd ones out, where the section
stripe already marks them as not belonging to the row's trio.

**Five lists used to have to stay in lockstep, and nothing enforced it.**
`HERO`/`LEFT`/`RIGHT` in `tools/wallsheet.py` decided what got baked into which
cell; `WALL_HERO_TITLES`/`WALL_LEFT_TITLES`/`WALL_RIGHT_TITLES` in
`room-3d.html` were what `wallCellAt()` indexed into; `HERO` in `tools/clips.py`
decided which previews existed; the `CLIPS` set in `room-3d.html` was a
hand-pasted copy of what came out of that; and `FEATURED` in
`portfolio-shared.js` carried an unstated requirement to be a subset of the back
wall. The hover maps a cell index straight back into an array, so a list that
had drifted pointed every cover at the wrong game and rendered perfectly while
doing it.

**They are now one file and a generator.** `build_layout.txt` is the only
hand-edited copy, and it carries one thing — a heading and the builds under it,
in reading order, left to right and top to bottom, by id rather than by title.
`zone 1`, `zone 8` and `zone 9` are the three walls; `trash`, `monitor`,
`tablet` and `showreel` are the props that carry a list. A prop can take a rule
instead — `auto section=RESKIN`, `auto link=Youtube` — which the room evaluates
against live data, so a new reskin reaches the reskin monitor by being a reskin
rather than by anyone re-running a tool. A wall cannot: its covers are pixels in
a baked sheet, so they have to be named. The
ids are the same slugs that name the clip files, and the tool keeps a
`name: id` table for all 33 at the foot of the file so none of them has to be
typed from memory. What each wall *is* — screen id,
sheet, grid, cell width, whether it ends in a count plate — is `ZONES` in
`tools/wallsheet.py`, because it is paired with a plane of a matching shape in
the room and changing it is not what anyone opens the layout to do. A zone
number with no wall behind it stops the bake and names the ones that exist. `tools/wallsheet.py` reads it, bakes the sheets, and
writes `demos/wall-layout.js` — `WALL_ZONES`, `WALL_SHEET_V` and `CLIPS`, the
last enumerated from what is actually in `demos/clips/`. `room-3d.html` loads
that as a plain script beside `portfolio-data.js` and has no title list of its
own; `tools/clips.py` reads the *generated* map rather than the `.txt`, so it
sees the 18 covers on the walls and not the 30 builds a prop's rule sweeps in
(unless it is given `--all`, which takes the whole archive on purpose).

The point is not that one file is tidier than five. It is that the pixels and
the cell-to-game map now come out of a single run, so they cannot disagree —
and the remaining mistake, editing the layout and forgetting to re-bake, leaves
both on the old order. That reads as "my change did nothing", which is a
question somebody asks. The old failure read as nothing at all.

That question is worth not having to ask, so `tools/serve.py` serves the site
and watches the layout: saving the file re-bakes and reloads the page that is
open. It is a development convenience and nothing more — the reload script is
injected into the response, never written into `room-3d.html`, and the deployed
site is still the generated files as committed. The manual run stays the
contract, because that is what a checkout on someone else's machine has.

What is still enforced by hand, and what took its place:

- A title not in `portfolio-data.js` **stops the bake** rather than closing the
  gap. Every zone is checked before the first sheet is drawn, so a mistake in
  the last zone cannot leave new pixels on disk beside the previous map. If a
  bad title reaches `zoneOf()` in the room anyway, that zone hangs no covers at
  all rather than a column of wrong ones, and says so on the console.
- The `?v=` on each sheet is a content hash of the layout, the fields the tiles
  are drawn from and the thumbnails themselves. Bumping it by hand was the step
  easiest to forget and worst to forget: skip it and your own browser looks
  right, because it just wrote the file, while nobody else's does.
- `#qa=1` grew a **Wall cover mapping** row. It walks every cell centre back
  through `wallCellAt()` and checks the title, checks each zone against its
  grid's capacity, and — the one genuinely independent comparison available in
  a browser — checks each baked sheet's own proportions against the plane it is
  mapped onto. Change a zone's grid without reshaping its plane here and every
  cell boundary drifts off its tile; that now fails, naming the zone and the
  ratio. It cannot read the JPEG, so it cannot prove the picture matches the
  list. Only the single run does that.
- The bake warns about the two claims elsewhere that a layout change can
  quietly falsify: a cover with no clip in `demos/clips/`, and a `FEATURED`
  case file that no longer hangs on the back wall the panel says it hangs on.
- It also prints a reminder that `og.jpg` is a photograph of that wall. Nothing
  can check that one — see the assets section.

Four decisions carry it.

**The preview is a local file, not an embed.** The obvious way to show a game
moving is a YouTube iframe, and it is wrong twice over: it fetches from a
third-party origin on hover, which the room does nowhere else, and sweeping
across eleven covers would build and tear down eleven whole documents.
`tools/clips.py` bakes 4-second muted H.264 clips instead. Measured for one
preview: **GIF 15fps ≈ 1.5–3 MB, the same clip as H.264 ≈ 100–190 KB** — fifteen
to twenty-five times smaller for a better picture. All ten together are 1.2 MB
and **none of it is in the boot payload**; nothing is fetched until a pointer
has actually rested on a tile.

**The scan is a moment, not a state.** The reveal is a lit bar travelling down
the frame with the picture arriving behind it, blown out and desaturated at
first and settling into colour (`hud-wipe`, `hud-bar`). Two things about it are
easy to get wrong, and both were wrong here at one point:

- The scanline comb over the preview (`#hud .shot::after`) used to be
  permanent. It is a 26% black rule over every third row, held forever across
  the one thing the readout exists to show. It now sits at `opacity:0` at rest
  and is animated up only for the duration of a reveal — `hud-lines` holds it
  through 55% of `.95s`, which is exactly the `.52s` the bar takes to reach the
  bottom edge, and then clears it. The picture finishes arriving and goes clean.
- The bar itself needs `animation-fill-mode: forwards`. Without it the element
  reverts to its base style when the animation ends, and its base style is a
  lit 2px rule with an 18px glow at `top:0` — measured at `opacity:1, top:0px`
  two and a half seconds after the reveal, parked across the top of the picture
  for as long as the readout stayed open.

Under `prefers-reduced-motion` neither runs and the scanlines never appear,
which falls out of the `opacity:0` base rather than needing its own rule.

**And the scan runs backwards on the way out.** Opening was a scan; closing was
a `.16s` opacity-and-transform fade, which is the one place the readout stopped
being a screen and went back to being a div. `#hud.off` is the close: the
stutter the boot arrives with played in reverse, a lift in brightness, then the
panel powering down — a shallow vertical squash and a drift back toward the
target with the colour draining out of it (`hud-shut`, `.52s`). Under it the
picture rewinds — `hud-unwipe` is `hud-wipe` reversed, so it shrinks back up
off the bottom edge losing its colour, `hud-bar-out` picks the bar up where
`hud-bar` parked it at the bottom and runs it back up the frame, and
`hud-lines-out` brings the comb back as the signal degrades.

**It is deliberately quieter than the boot, and twice as long.** The first cut
of this was a full CRT power-down over `.26s`: a blow-out to white and a
collapse to a 2px line that contracted sideways and snapped off. It is a good
effect exactly once. The close fires on every pointer-leave, which is far more
often than any one boot fires, and at that rate it was the readout shouting on
its way out of every room. So the beats are unchanged and the amplitude is not
— the flicker dips to `.62` instead of blinking to `.4`, brightness lifts to
`1.26` instead of flashing to `2.6`, and the squash stops at `scaleY(.74)`
instead of `.03`. The doubled duration is the other half of it: the same
distance travelled slowly reads as a settle, travelled fast it reads as a snap.
`HUD_SHUT` is `545` — `.52s` of animation plus a frame's slack, so the teardown
never lands on a collapse that is still running.

The reason it is two functions rather than one is that the shutdown has to play
on a panel that is still placed and still holding its picture: `--hud-x` /
`--hud-y`, `.lf` / `.dn` / `.up` and `.rv` all have to outlive the close by the
length of the animation. So `hudDrop` starts it and gives up only the state the
rest of the app reads — `hudCard` above all, which is what says "a readout is
open" and has to go immediately or a re-hover during the shutdown would be
swallowed by the "already showing this" exit in `hudSet` — and `hudReset` does
the teardown `HUD_SHUT` (545ms) later, or straight away when nothing was lit.
Three details fall out of that split:

- **`hudShow` cancels a running shutdown.** It clears the pending `hudReset`
  and takes `.off` off before it writes anything, so a cover hovered on the way
  out gets a boot from rest rather than one playing over a half-collapsed box.
- **The clip keeps running under the rewind**, and `hudReset` is what pauses it.
  Freezing the frame first is the one thing that would read as "this stopped"
  rather than "this is being taken away".
- **`hudhero` is released at the end, not the start.** That class exists so the
  headline is not underneath the readout; letting the hero come back while the
  panel is still collapsing over it is exactly the overlap it was added to
  prevent.

`#idx.on ~ #hud.off` sets `animation:none`. The index does not close the
readout, it hides it with a rule — and a shutdown playing under an open index
would be a panel nobody asked about flashing behind the menu. Under
`prefers-reduced-motion` `hudDrop` skips the animation entirely and calls
`hudReset` directly, which is the old one-step close.

**On touch it is a sheet, not a card beside the thing.** A phone has no hover
to preview with and no right gutter to sit in, so the same readout anchors
across the bottom instead, opened by a tap. Four things had to change with it:

- **A tap on a wall cover now opens the readout, not the archive.** This is a
  swap, not an extra step: `gameCard.acts` already carries `▶ Play` /
  `Watch ↗`, so the build is still exactly one more tap away — and this route
  arrives with the clip already running. A tap on the bare wall between covers
  still opens the archive, and every prop without a card is untouched.
- **The readout never follows the pointer on touch.** `HUD_HOVER` (was
  `HUD_OK`) gates the hover path out of the frame loop entirely. Left in, the
  "pointer" after a tap is wherever the finger last was, and a settling camera
  slides a different tile — or nothing — under that point, closing a sheet the
  visitor opened deliberately. For the same reason orbiting does not close it:
  a tap-opened sheet lives until ✕, a tap on empty room, or a panel.
- **The time bar yields while the sheet is up** (`#hud.on~#clock`). Sitting
  above it cost 104px of a phone's height and bought nothing — the day cycle
  is not what is being read during a preview. It is the same gesture the
  desktop already makes on `#hint`.
- **`aspect-ratio` plus `max-height` shrinks the width, not just the height.**
  A capped square card became a small box against the left edge rather than a
  letterboxed full-width one, so the shot is centred with `margin-inline:auto`.
  The cap is `min(44dvh,380px)`: 44dvh is where a square card reaches full
  width on an 844px phone and stops needing side margins at all.

The bracket and leader line are not drawn on touch. The sheet spans the whole
bottom edge, so a leader has nothing to point at, and four projections plus
three attribute writes per frame is a poor trade on the hardware least able to
afford them. Measured with no overlap against `#brand`, `#idxBtn`, `#gridBtn`
and `#clock`, and fully inside the viewport, at 390x844, 360x640, 414x896 and
768x1024, for both the 16:9 covers and the square Athena card.

**Known, not fixed:** a wall cover is about **40x26 CSS px** on a 390px phone —
the wall is 4x3 cells inside a surface that projects to roughly 160x78 there.
That is well under the 44px touch floor the rest of the UI holds to. Hitting
the neighbouring cover is recoverable (the sheet names what you got, and the
wall stays visible above it, so the next tap corrects it) but it is a real
cost. Fixing it properly means changing the mobile composition so the wall is
larger, which is a bigger decision than this feature.

**It has three positions, and the side columns ask for the middle one.**
Right gutter by default; the opposite gutter when the target is past the middle
of the frame; centre when the surface asks for it, which the two side columns
do. Those hang at the very edges, so for them "the other gutter" is the far
corner of the screen and the leader became a rule drawn across the whole room —
423 px at 1600 wide. Centre is nearer to both edges than either gutter is to
the other, and it happens to be the one position that clears the hero copy on
the left and the control hint on the right at once. Measured after the change:
every side-column leader is 20–24% of the frame at 1280, 1440 and 1920.

**The leader gives up past a third of the frame.** Beyond that it stops being a
pointer and turns into a rule crossing the desk, the monitors and the window,
by which point it is the loudest thing on screen. Sweeping every hoverable
target at four camera positions, the ones that trip it are back-wall covers at
the left end of the yaw clamp, at 34–45%; the bracket still sits on the tile
and the header still counts it, so nothing is lost. The side it attaches to is
measured from the projected quad against the readout's own box rather than read
off the position class — with two rotated surfaces, "the +u edge" is screen-left
on one wall and screen-right on the other.

**It is placed against its target, not pinned to a gutter.** The gutter was the
far side of the frame from most of what the readout describes: measured over
every hoverable target at 1440x900, the median gap from the pointer to the
nearest edge of the panel was **360px** and the worst was 462px. `hudPlace()`
tries four slots — right, left, below and above — and takes the best one that
can still hold the panel.

**Best is a standoff, not the minimum.** Taking the nearest slot every time got
the median down to 67px and that is too near: at 67px the panel crowds its
target, covers whatever surrounds it, and puts the headline under itself for
most of the wall. Slots are scored on `|distance - HUD_REACH|` with
`HUD_REACH = 150`, and the winning slot is then pushed out along its own axis
until it reaches the standoff or runs out of room. Measured over every hoverable
target: **median 150px** (range 67–170) at 1440x900, **median 149px** (range
31–150) at 1280x720 — before the headline was added to the scoring, below.

Widening `HUD_GAP` was the wrong lever and is worth remembering as a trap. At
100px of clearance the left slot fell under `HUD_MINW` for the whole back wall,
three columns dropped back to the gutter at 390px, and the median went *up* to
188. Clearance and standoff are different jobs: `HUD_GAP` stays at 20 so that
widening it never costs a slot, and the distance is bought by the push instead,
which cannot.

**The headline outranks the standoff.** The panel is free to land anywhere now,
and against a target on the left of the frame it landed on "My room, right now."
— the line that says whose room this is — on 3 of 13 targets at 1440x900, where
all `#ui.hudhero` could do was fade the headline out. `hudPlace` is given the
headline's rectangle (padded by `HUD_HPAD`, so clearing it is not clearing it by
a hair), slides a slot off it before scoring, and charges `HUD_HERO` — larger
than any distance the frame can produce — to any slot still sitting on it. Both
axes are tried, not just the slot's free one: a 480px panel in the left of the
frame has no room above the headline and none below it, and the only way off is
sideways, past its right edge. That is the one move allowed to spend distance.
**0 of 13 at 1440x900 and 0 of 19 at 1280x720 now touch the headline**, and the
median moved 150 → 170px at 1440x900 (range 120–284; the three that had to slide
past the headline are the 282–284s) and stayed at 150px at 1280x720 (range
88–284). The `.hudhero` fade stays as the fallback for the case the placement
cannot solve — every slot on the headline, or no slot at all — and is measured
against the real rectangle, not the padded one, so merely being close to the
headline does not put it out.

Outside the *surface*, not outside the hovered cover. That distinction is the
whole design: a 516px panel beside one cover of the wall lands on the other 32
and there is no way left to reach them, so every slot is measured against the
whole quad. The wall is 460x170 on screen and the band under it is 470 tall,
which makes "under the wall" a real position — the one that cuts the distance
without hiding a single cover. Verified over 19 targets at 1440x900 and 1280x720:
**no placement overlaps the target it describes, and none leaves the frame.**

Sizes are measured, not modelled: `hudMeasure()` sets a width and reads the
height back. A square card is a far taller panel than a 16:9 one of the same
width, and the slot changes with every target. If a slot is too short, the width
that would fit is arithmetic — `(slotH - chrome) * ar` — for any card whose
height is a multiple of its width, and that is now both kinds: a still card is
chrome plus its picture, and the bin's card is chrome plus rows that are each
16:9 of the card. `.listing` decides which element to measure. For the list `ar`
is read off the box rather than declared, because how many rows sit under the
cap and how big the gaps between them are belong to the stylesheet, not to this
function.

The list used to arrive here with `ar` 0 on the reasoning that a list does not
scale with width. That was true of a list of 66x42 stills and is false of one
whose rows are clips at the card's own width: no slot ever fitted, and the
placement fell through to the gutter at full width every time.

One arithmetic pass is not enough for the list. It is exact for a picture, whose
height really is a clean multiple of the width, and a few pixels short for the
clip rows, whose gaps and borders are fixed while the rows are not — so
`hudSizeFor` corrects off the measurement rather than modelling the difference.
Two rounds close it; the third is slack. `HUD_MINW` is 330: narrower and the two
action buttons start wrapping.

Decided at open, never in the frame loop — a readout that slid to a new side
mid-hover as the camera drifted would be worse than one that sits a little off.
Held still through six seconds of idle drift the overlap stays zero, and a drag
closes the readout rather than leaving it stranded on its own target.

**The leader runs on whichever axis the panel actually took.** With four slots
the panel is as often above or below its target as beside it, so the attach edge
and the elbow are both chosen from the measured offset rather than from a
position class. `#hud.lf`, `.dn` and `.up` survive only as boot-animation
directions.

**One size knob.** Everything is derived from `--hud-w`
(`clamp(360px, 36vw, 516px)`), so the readout scales as a unit, and `hudPlace`
narrows it from there to fit the slot it chose — 339–410px at 1280x720. Two
`max-height` breakpoints keep the natural width down on a laptop. `#hint` is
dimmed while the readout is open, the way `#idx` already dims it; `#hero` is
dimmed on measured overlap rather than on which side the panel took, because
with four slots "left" no longer implies it.

**The bracket follows the projected quad, not its bounding box.** At the ends of
the yaw range the wall is a long way from frontal, and an axis-aligned box there
sits visibly off the tile.

**A close is deferred while the pointer approaches.** Reaching Play means
crossing the room between the tile and the panel, and the raycast underneath
does not stop while that happens — so the readout used to close before the
pointer arrived and the buttons were unreachable by the only input that can open
them. There is a 700 ms grace, pushed back further for as long as the pointer
keeps getting nearer the panel, and cancelled outright once it is over it.
Hover is frozen while the pointer is on the readout, so the room behind cannot
steal the hover from the panel covering it.

Leaving the readout has to restart that clock itself, and for a while nothing
did. The room's hover cannot do it: reaching the panel means crossing the empty
room around the target, so `hot` is already `null` by the time the pointer
arrives, and `setHot`'s "same hit as last time" exit then swallows every `null`
that follows — including the ones that should have closed the panel. Pointer
from a cover into the readout and back out to bare room left the readout up
indefinitely, and it took a traversal harness reporting a stale card on the
*next* case to notice. `pointerleave` calls `hudHide()` now. Hover only: on
touch the same pair fires around a tap, and the sheet is dismissed by its close
button, not by letting go of it.

**The card lands where the pointer stops, not on what it passes over.** Keeping
the readout open was only half of it: the card it was showing used to swap the
instant a new target came under the pointer, and the crossing runs straight
across four or five other covers. Measured on a 1440x900 frame, a move from
Netcode Battle to the panel changed the card 27 times and arrived showing Color
Shoot 2d — every cover except the column nearest the gutter was unreachable, and
the 700 ms grace was faithfully keeping the wrong card alive. `HUD_SWAP` (190 ms)
now guards a swap the way `HUD_DWELL` (340 ms) guards the first open, and it
counts stillness rather than time on target: any pointermove of more than 4px
pushes the pending swap back, so a hand still travelling never triggers one. The
4px floor is there because a resting mouse is never quite still. Entering the
readout cancels a pending swap outright — freezing the hover does not unschedule
work already queued, and without that line a flick from the left column landed
on the panel and turned into a different build 190 ms later. Verified across
thirteen crossings at every speed from 260 ms to 2.4 s, all arriving on the card
they started from, while resting on a neighbouring cover still swaps at 200 ms
and a fast sweep with nothing open still opens nothing.

Touch never sees any of this. `HUD_OK` is `!MOBILE_GPU`, so on a phone the
readout never opens and not one clip byte is requested; tap-to-panel is
unchanged. It is `aria-hidden` with its controls out of the tab order, and every
fact on it is also in the archive panel — a mouse shortcut, never the only copy,
so the ☰ Contents keyboard route is exactly what it was.

### The bin: the 2D casual pile

The waste bin used to sit at `x=-7.5, z=-13.5` — dead centre of the floor, the
one object in the room on its axis of symmetry, and scenery. It is now at
`x=8.2, z=-15.2, ry=-.55`, just off the desk's right-front corner (`DX1=6`,
`DZ1=-16`) and turned to face it. Nothing else in this room is axis-aligned.

It carries six builds, and **which six is the whole design of it.** Eighteen
of the 33 have a cover on one of the three walls; fifteen have no cover
anywhere and exist only as a tile inside a panel. The bin takes six that are 2D
and one-thumb — Archer 2d, Jump 2d, Math Game 2d, Find Monkey 2d, Game Shooter
2d, Color Shoot 2d. Anything already hanging on
a wall would have been a third copy of the same cover.

**There is actual rubbish in it.** Six quads carrying the six thumbnails,
stuffed in and spilling out — the bin is the one prop whose contents are the
point, and an empty bin labelled "2D casual" would be a caption without a
picture. Quads rather than anything cleverer: what reads at this size is colour
and angle, not geometry.

They are `SCRAP_W` x `SCRAP_H` = 3.0 x 1.9, which is **wider than the bin**,
and that is what fixes the arrangement rather than breaking it. At half this
size two of them sat down inside showing only a corner; doubled, those two came
out through the bin's own walls. Every sheet now meets the rim at y=3.6 and
leans out of it, which is the shape a bin crammed past its capacity actually
has.

**`SCRAPS` is keyed by title, not by position**, because five of the six
builds have a sheet and which one does not is a decision. Indexing into
`CASUAL_TITLES` would state that only by accident: reorder the list and a
different game silently loses its quad. Game2d Black Ops is the absent one —
it is in the readout's list and in the panel, just not in the pile.

Two things about them are load-bearing:

- **`castShadow:false`.** `occCand` is built from every shadow-casting mesh
  that is not itself a pick target, and `pickAt` rejects a hit that has a
  clearly nearer blocker. Left on, the scraps would sit in front of the bin's
  own hit proxy and eat the hover they exist to advertise.
- **The sixth one lay flat on the floor first, and was invisible.** A flat card
  under this camera is edge-on; a .9-unit quad at a grazing angle covers about
  two pixels. Leaning it against the bin is what made it read.

**It is a `SCREENS` entry, not a bespoke widget.** An invisible 6.6x4.8 quad
stands in the bin's place; `addScreen` hangs the hover halo and the raycast
proxy off it and `focusOn` frames it. That buys the Contents row, the
`#panel=casual` deep link, the prev/next ring, Escape, the focus trap and a
scrollable panel for nothing.

**The readout carries a list rather than a still.** This card is six builds,
not one, so the picture slot holds all six and scrolls instead of picking one
of them to stand for the rest. A `hud` payload with a `list` array puts `#hud`
into `.listing`, which swaps `.shot` out for `.hlist`.

**Each row is that build's clip, at the card's own width.** The rows used to be
a 66x42 still, a title, and the words PLAY IN BROWSER. All six of these builds
are WebGL, so that subtitle was the same three words six times over, under a
card whose own subtitle already reads "6 playable in browser" — and a `▶` said
it a third time, six more times, down the right edge. The repetition was not
the expensive part: it is what made the row 58px, and a 58px row is why three
and a half of six builds were ever on screen at once.

A still could not have carried these anyway. The card says they were made "to
try a mechanic rather than to ship a game", and a mechanic is motion — one
frame of Jump 2d is a beige rectangle with a shape on it. All six are already
in `CLIP_OF`, and the six clips together are **125 KB against 135 KB for the
six stills they replace**: 640x360, 24fps, four seconds, looping. The card is
`hudHoverOnly`, so a tap on a phone opens the panel and this list never runs
six decoders on the hardware least able to spare them.

What six decoders cost the room's own frame rate is **not measured and cannot
be, here**: headless Edge rasterises in software, and the sampler returned
10.8 fps for the room alone against 11.7 with all six clips playing — the clips
apparently making it faster, which is only noise on a renderer that has no GPU
to load in the first place. The transfer size and the resolution are facts; the
frame cost is an inference until somebody opens it on a real machine.

- **The cap is written off `--hud-w`, not in pixels.** A clip is 16:9 of the
  card, so three of them are 1.7 cards tall, and expressing the cap as
  `calc(var(--vrow) * var(--vrows) + (var(--vrows) - 1) * 8px)` is the only
  thing that lets `hudSizeFor` trade width for height here. At the full 516px
  three clips are 1013px of card and no slot on a laptop is that tall; at
  1440x900 the placement narrows the card to **330px and the card comes to
  696px against a 700px band** — three clips of 298px and the top sliver of a
  fourth. That sliver is free: the scrollbar takes 4px off each row's width and
  therefore a few off its height, which is the same "there is more" the old
  3.55-row cap had to be hand-picked for.
- **Below 896px of window the row count gives way, not the band.** Chrome is
  158, the placement will not go under `HUD_MINW`, and the band is the viewport
  less 200 — so three rows need 896px of window and two need 719. Two media
  queries step `--vrows` down at each, beside the two that already shrink
  `--hud-w` on a short window. Without them `hudPlace`'s last resort is
  `HUD_MINW` at whatever height that comes to, and the card keeps its three
  rows by running off the bottom of the frame. Measured at five window sizes,
  every one of them inside its band:

  | window | card | rows | clip |
  |---|---|---|---|
  | 1920x1200 | 509 x 998 | 3 | 477px |
  | 1440x900 | 330 x 696 | 3 | 298px |
  | 1440x880 | 411 x 610 | 2 | 379px |
  | 1366x768 | 368 x 562 | 2 | 336px |
  | 1280x700 | 387 x 373 | 1 | 355px |

  The trade reads backwards until you see what it is buying: 1440x900 gets the
  *narrowest* card of the five because it is the only size where three clips
  are nearly too tall to fit, and 1440x880 gets a wider one by giving up a row.
  A tall window pays nothing — at 1200 the card is 509 of its natural 516.
- **Six decoders do not stop themselves.** `hudListStop()` pauses every clip
  and drops its `src` on each exit from the list — in `hudReset`, and again in
  `hudShow` before the next card is written, because the next card may be a
  still. Clearing `innerHTML` detaches the elements but a detached `<video>`
  keeps its stream alive long enough to matter, over a room that is still
  rendering. Measured: six playing while the card is up, **zero the moment the
  pointer leaves**.
- **One `▶ Play`, on the row under the pointer.** Taking `PLAY IN BROWSER` and
  the six glyphs off the rows was right about the words and wrong about the
  affordance: they were the only thing saying a row was a link, and this card
  carries `acts:[]` so there are no action buttons under it to say so instead.
  It comes back as one, in the corner of the gradient the title already sits
  on, so no row is taller for it — and the space is reserved whether or not it
  is showing, so a long title ellipsises in the same place both ways rather
  than reflowing under the pointer. Measured: opacity `[0,1,0,0,0,0]` with the
  pointer on the second row.
- **Reduced motion keeps the posters and drops the movement**, which is the
  whole of what the preference asks for here — the layout, the sizing and the
  narrowing are unchanged, so the card is still 330x696 inside its band with
  six rows and none of them playing. Verified under emulated `reduce`.
- **The window `wheel` handler had to learn about `#hud`.** It
  `preventDefault()`s everything outside `#glass` and `#clock` to drive the
  camera zoom, so without the exception the list is a scroll container that
  never scrolls.
- **The list scrolls itself**, the same manual wheel handler `#gb` uses, for
  the same two reasons: `stopPropagation` keeps a wheel past the end of the
  list off the camera, and a synthetic `WheelEvent` scrolls nothing in
  Chromium — a list relying on native scrolling could only ever be checked by
  hand. Measured on the clip rows: `scrollTop` 0 → 400 of a 513 range, and the
  card stays open throughout, because `hudOver` freezes the hover while the
  pointer is on it.

The quad is deliberately larger than the bin. The halo is 1.5x it and the hit
proxy 1.12x (1.28x on touch), and the bin model is 3.6 units — about 40x38 CSS
px on a 390px phone. Sizing the proxy rather than the model is the cheap half
of the small-target problem the wall covers also have.

Three things the bin exposed, all of them pre-existing:

- **`hudHoverOnly`.** On touch, a surface with a `hud` payload makes
  `activateHit` open the readout sheet *instead of* the panel. That is right
  for a wall cover — the sheet carries that build's own Play button, so the
  build is still one tap away — and a dead end here, where the card describes a
  pile whose contents are in the panel. The flag opts the bin out; the card
  stays a mouse affordance and a tap opens the panel.
- **The readout lands on the hero.** The bin was the first target right of
  centre, which sent the panel left onto the headline and the CTAs; putting the
  panel against its target made it happen for most of the wall too. `#hero`
  precedes `#hud` in the DOM so no sibling selector reaches it; `hudPlace` sets
  `.hudhero` on `#ui` instead, and asks the question as measured overlap rather
  than as which side was taken. The placement now avoids the headline outright
  (above), so the fade is the fallback rather than the answer — 0 targets reach
  it at either size.
- **The leader was measured across, not along.** The rule is "past about a
  third of the frame it stops being a pointer", but the test read
  `Math.abs(hx-ax)` — horizontal span only. Every target it was written against
  sits roughly level with the readout's band, so the two agreed. A prop on the
  floor does not: the bin's leader runs 320px sideways and 425 down, which the
  old test scored at 22% of a 1440 frame while drawing a 532px diagonal across
  the desk. It measures `Math.hypot` now, and the dot — which is only where the
  leader starts — hides with it. Re-measured after: back wall 17–28%, both side
  columns 27–29%, the Athena monitor 20%, all still drawn; only the bin trips
  it.

`.pg3` was also folded into the `@container panel (max-width:560px)` rule
alongside `.pg4`. Three columns in a 390px sheet is a 110px tile with the title
wrapping under it, which is the shape that rule exists to prevent;
`layoutOkFor` now expects `s.cols>=3` to collapse to two, so the harness and
the stylesheet still agree.

### The cat on the sofa

A British Shorthair sits dozing on the sofa. Put the pointer on it and it
flinches awake, sits up, looks about, washes a shoulder, and settles again once
left alone. It opens no panel and is not in `PANELS`.

**The model is downloaded and the animation is not.** `models/sofacat.glb` is
[Sitting cat (British Shorthair Blue Cat)](https://sketchfab.com/3d-models/sitting-catbritish-shorthair-blue-cat-ee5dcbdd0c2b4c33adf83d4c6708e6ae)
by 3D Creator, CC BY 4.0. It ships no rig and no clips; everything it does here
was written in `updateSofaCat`.

#### 6.6 MB down to 188 K

As downloaded it is 74,586 triangles, a tangent buffer, four byte-identical UV
sets and three 1024² maps — **ten times this room's entire model payload, for
one prop.** `tools/sculptglb.py` is the pipeline. Two things in it are not
obvious:

- **Strip the normals before simplifying.** meshoptimizer will not collapse an
  edge across a discontinuity in any attribute it is given, and this mesh is
  split for hard normals nearly everywhere. With normals in, the simplifier
  bottoms out at **7,050 triangles** however far the error bound is opened;
  without them it reaches **5,566**. Nothing downstream misses them — the room
  partitions this mesh at load and recomputes normals on both halves anyway.
- **The UV seams are the real floor.** 62,074 vertices for 37,295 positions,
  and an exact weld merges 22 of them: the sheet is an auto-packed atlas of
  several hundred small charts, so a quarter of the vertices sit on a seam the
  simplifier may not cross. 5,566 is where that stops and no tolerance goes
  below it. Lower means giving up the texture, and the texture is why this
  model was picked.

The sheet is photogrammetry with the lighting baked in — **mean luminance 67 of
255, maximum 194.** A British Shorthair blue is a light silver-grey, and
unlifted this one rendered as a black lump on a mid-blue sofa. A gamma of 0.55
takes the mean to 119 and leaves the ear interiors and pupils dark, which a
linear gain would not.

**Gamma alone flattened it, though**, and that was the first thing anyone
noticed about the shipped cat: it pulls the darks up faster than the lights, so
the fur went uniform grey and the markings disappeared. A contrast term of 1.30
about the midpoint puts them back — the ruff separates from the chest, the back
reads darker than the flank, and the face has a face again. It costs 7 K.
Rendered against a 1024² variant at higher contrast still: the extra resolution
was invisible at the size the room draws the cat, and the extra contrast only
took it back towards being dark.

512² at q78 is 46 K, and the cat draws about 160 px, so the sheet is still
oversampled threefold. That was rendered rather than assumed: downscaling an
atlas of small charts bleeds neighbours across chart borders, so 1024, 768 and
512 were compared side by side first.

It is the one prop in the room read with **trilinear filtering, mipmaps and
anisotropy**. Every Synty prop uses `NearestFilter` and no mipmaps, which is
right for hard-edged palette squares and wrong for photographic fur drawn at a
fraction of its own resolution — sampled nearest it turns into crawling speckle.

#### Four models were tried and three thrown away

All for the same reason, and it is worth keeping because it was got wrong twice:

- **Quaternius' CC0 cat** has a real skeleton and eight clips, which is what put
  it on the shortlist off a thumbnail grid. Sampled and measured they are not
  what they look like: its `Death` clip ends at y=1.31, exactly the height of
  `Idle`, because the cat never lies down in it. **There is no sleeping pose
  anywhere in that file.**
- **`Tubbs`** is a lovely curled loaf and shipped here for one pass. It has **no
  tail and almost no ears**, so at the size the room draws it, it read as a
  bread roll. Creased normals and a fur-coloured vertex ramp were both spent
  trying to fix that before the diagnosis landed: **the problem was the
  silhouette, and shading does not change a silhouette.**
- **`cat loaf`** is a sitting cat, not a sleeping one, and untextured white.
- **`dingus`** is genuinely a cat lying curled and it is textured, but it is a
  black photoreal cat, which is two kinds of wrong in a flat-shaded room.

**This cat sits, and that is the trade** — the same one the last model made. The
brief asked for a cat asleep; every candidate actually lying down was black,
photoreal, or unreadable as a cat. So the resting pose is a doze rather than a
curl.

#### One hinge, and why there is only one

**The neck is a tilted plane.** On a sitting cat the skull is up and forward and
so are the forelegs, so a flat cut takes the paws with the head. The plane is
tilted **72° up from +z, crossed at 66% along its own axis**, found by rendering
the sweep and reading it off: at 45° it takes the whole chest, at 84° it bites
into the shoulders, and at 72° it separates **2,491 triangles that are the head
and the neck ruff and nothing else.** The plane lives in (z, y), not (x, y) —
this model faces +z where the last one faced +x, and reusing that cut wholesale
is exactly the mistake the heading note below is a monument to.

**The plane is a weight, not a cut.** The build that shipped first split the
geometry in two there and plugged the seam; it tore, and the note under *Bugs*
below has the measurements. What is there now is one mesh, two bones and a
per-vertex weight that smoothsteps from body to head across a band **34% of the
axis wide** — wider than the longest triangle edge in the region (0.31 on an
axis 1.02 long), so no single triangle spans the whole blend, and narrow enough
that the shoulders stay put when the head turns. The neck stretches instead of
hinging, which is what a neck does.

Three things follow from there being no cut. The animal is creased **once, over
the whole of itself**, rather than per half — creasing a cut edge is part of
what used to shade it as a collar. The normals have to be **computed here**: the
`.glb` ships positions and one UV set and nothing else, and the split that this
replaced was computing them by accident on its way to building two geometries;
without that the cat renders black. And the two bones are **siblings, not
nested** — the body bone carries the breathing, and a neck parented to it would
breathe with it, which is the pulsing whole-animal scale the reaction rules out.

Picking reads the **bind pose**: `SkinnedMesh` otherwise walks every vertex
through its bones on the CPU for each raycast, and `pickAt` raycasts this on
every `pointermove`, for an occlusion test on an animal that never moves a tenth
of its own width.

**There is no tail hinge, and that is a real loss.** On the last model the tail
was the cheapest cat signal in the file. This cat's tail is wrapped flat around
its own feet and fused into the base ring with both front paws — measured, a cut
low enough to catch it takes **2,482 triangles of paw and haunch** with it — and
a tucked tail has nowhere to swing that is not through the floor or the body.
The ears are no better: this is a breed with small low-set ears, and every
height that catches them catches the whole skull cap between them. So the second
channel is the body itself, turning on the spot towards whoever moved. A cat
that turns to look at you is a weaker signal than a flicking tail, but an honest
one.

The body is **smooth-shaded** (creased at 78°). Every Synty prop in the room is
flat-shaded because every Synty prop is a machine or a box; this is the one
thing in here meant to be soft.

#### Five keys, each five numbers

`[headPitch, headYaw, bodyTurn, squash, lift]` is the whole vocabulary one
hinge, one turntable and a scale have. Pitch is positive nose-down: the model
faces +z, so the head nods about x.

| key | what it is |
| --- | --- |
| `doze` | head down over the chest, body square |
| `flinch` | head up hard, body dropped into the seat and turned away |
| `alert` | head high, turned towards whoever did that, body following |
| `watch` | head level, a slow look the other way |
| `wash` | head dipped to the shoulder |

The script is `flinch 130ms → alert 330ms`, then `watch · watch · wash · wash ·
alert · alert` on a loop while the pointer stays, then `doze 1250ms` once it has
been gone for `SC_LINGER` (1.4 s). **Only the flinch eases out**; everything
else eases in and out, and every beat is slower than the one before, which is
what settling down looks like. A startle that eases in is not a startle.

**Leaving only starts a clock.** A cat that snapped back to dozing the instant
the pointer left would be a button, not an animal.

Breathing runs on the **body bone only** — scaling the whole rig takes the head
with it and the animal pulses — and fades out as the cat wakes. A slow drift
keeps a held pose from being quite still; with no tail to carry it, it sits
almost entirely on the head, and the body turn gets a fraction of what the tail
used to do. A whole animal swinging on a sine reads as a wobble where a tail
doing the same reads as a tail. Under `prefers-reduced-motion` the whole script
collapses to one blend between `doze` and `alert`.

#### Bugs worth keeping written down

*The plug was very nearly the size of the cat.* The seam plug is sized from the
ring the cut passes through. The first version collected every vertex within a
band of the cut **plane**, and because the plane is tilted 72° that band reached
across the chest and round the back: it reported a radius of **0.38 on a cat
0.64 wide**, and the icosahedron built from it sat exactly where the head goes.
The first render of this model was a cat with a boulder for a head. `scSeam`
now takes the positions that appear in **both** a head triangle and a body
triangle — that set is the cut, not a neighbourhood of it — and takes a low
quantile of the radii rather than the maximum, because the cut runs out along
two spikes of chest ruff and a plug reaching those would bulge through the
throat. Ring: 25 vertices, r = 0.152.

*The seam tore, and no plug was ever going to close it.* Reported as the cat
breaking up during the idle and hover animations, and it was. The ring the cut
passes through is **25 vertices whose distance from their own centre runs 0.134
to 0.315** — a 2.4× spread, because a model simplified from 74,586 triangles to
5,566 carries the chest ruff as a few long spikes rather than as a rim. A sphere
at the median leaves **72% of the ring outside it**; rendered with the head
hidden, the body's cut is a crown of spikes with open valleys between them, and
the head's own cut edge no longer registers with them once it turns. The idle
drift alone — 0.045 rad of yaw on a pose that is otherwise held — showed
daylight through the chest at rest, and `wash` at 0.24 opened it. Sizing the
plug to reach the spikes needs **2.2×**, which was rendered too: a boulder wider
than the animal, which is the bug above in a second costume. The fix is not a
bigger plug. It is not having a seam — see the hinge note above.

*Nineteen degrees of pitch flanged the neck open.* A British Shorthair has
essentially no neck — the cut ring is 0.15 across on a cat 0.64 wide, and there
is no narrow place to put it. A rigid cap swung 19° off a ring that size lifts
its own cut edge clear of the body and stands it out as a **collar**. The pitch
keys are half what the first pass used: about eight degrees each way, which
keeps the edge inside the ruff. The skin retired the flange — a weighted cap
cannot lift its own edge out of the body, because there is no edge — but the
numbers were kept, because they were chosen on how a British Shorthair holds
itself and not only on what the seam would take.

*The heading was computed and wrong, again.* Facing the camera works out at
`SC_RY = 0.3` on paper — at the inspection angle the camera sits at
(-19.8, 20.5, 31.2) and the cat at (15, 0, 2), and the heading pointing one at
the other is -0.87 rad against this cat's -0.99. Rendered, 0.3 shows the animal
turned well off to its left and **0.7 is the frontal one**: the mesh's own
muzzle is about **23° off its +z axis**, which no amount of arithmetic about
node transforms was ever going to reveal. `SC_RY` is 1.00, a fraction past
frontal on purpose. **Sweep the heading; do not compute it.**

*The fit was measured in the wrong space.* `Box3.setFromObject` reports world
space, and those numbers were written straight back as the group's own local
position. Taken with the group already parented under the sofa they carried the
sofa's translation with them and **threw the cat 87 units out of the room.** It
is measured detached now, then parented. The fit is by **height**, not
footprint: this animal sits up, so height is what a reader judges it against the
sofa by.

*A prop was vetoing its own hover.* `pickAt` drops a hit when anything in
`occCand` is more than 1.1 nearer than the proxy, so a prop behind a wall cannot
be selected through it. Screens are flat and their models thin, so nothing had
ever been deep enough for it to matter. A cat on a sofa is: measured, its proxy
raycast at 47.4 and its own flank at 45.9, and **every hover was thrown away by
the animal it belonged to.** Meshes carry `userData.own` now, and a surface's
own body cannot veto selecting it.

*A scale multiplied a position.* An earlier model's shut eyes were dark slits
opened by scaling. Their geometry was baked into the body's space with the mesh
origin at the neck offset, so `scale.y` multiplied the vertices' own coordinates
and **the eyes left the head on the first flinch.** Geometry that is going to be
scaled has to be centred on itself first.

#### Measured

**The hover quads are aimed by measurement, not by hand.** `SCREENS` is read
into `picks` at module level, so the entry must exist before the `.glb` lands —
but where the animal ends up is not known until it has been fitted to the
cushion. `scFitProxy` re-centres and re-scales all three quads on the fitted box
in the load callback. The box is **raised 24% before fitting**, because awake
the cat throws its head up by that much, and without it, moving the pointer onto
the head the cat had just raised put the cat back to sleep.

At 1440×900 with the camera at `yaw -0.30`:

| state | cat rect | probes over its own rectangle |
| --- | --- | --- |
| dozing | 174×151 px | 24 / 25 |
| awake | 153×142 px | 23 / 25 |

No runtime errors, `noPanel` true, not in `PANELS`. The probes that miss are
corners where the sofa really is nearer, which is the veto doing its job. The
room's own `#qa` harness does not cover the cat at all — it iterates `PANELS`,
and the cat is not in it.

It glows like every other prop but at `haloGain` .16 rather than .40, and it
withholds the pointer cursor the way the centre monitor does — what the pointer
is promised is an animal waking up, not a document.

**It is desktop-only in practice**, and it is not well framed at rest. There is
no hover on touch; at 390×844 the sofa is off the bottom of the frame entirely;
and at the resting camera (`yaw +0.32`) the cat's box projects to y 780–1014 in
a 900-px viewport, so **only its head clears the bottom edge** until the visitor
drags the camera round. That is the room's framing rather than the cat's, and it
was true of the previous model too, but it means the prop is found by looking
around rather than on arrival.

### The penguin on the chair

A plush penguin sits on the desk chair. It does not move, and that is the
point.

**It replaced a cat that was modelled here in code** — boxes for the body, an
FK tail chain, blinking eyes, an ear twitch, all of it hand-authored in
`relaxedCat`. The reason for removing it is not that it was bad. It is that the
sofa now has an animal on it that wakes up when you point at it, and **two
animated animals asleep in one room read as a theme rather than as a detail.**
A stuffed toy on the chair says somebody works here without competing with the
thing that is worth finding.

`models/chairplush.glb` is
[Cute Penguin 9th May 2020](https://sketchfab.com/3d-models/cute-penguin-9th-may-2020-d2156bead52541e58a9c8ff3ec59624c)
by Felix_Lim, CC BY 4.0.

**25 KB, from 3.6 MB, and no image at all.** It arrives as 111,552 triangles
across eight ZBrush subtools with **no texture whatsoever** — every bit of its
colour is in `COLOR_0`. `tools/sculptglb.py plush` does three things to it:

- **Forces the eight subtools onto one material** so `join` can merge them into
  a single primitive. They differ only in a glossiness `MeshLambertMaterial`
  cannot read. Simplified separately the eight would each keep their own
  boundary, and the seams between them would be locked against collapse.
- **Takes it to 1,672 triangles.** With no UVs there are no chart seams to stop
  the simplifier, so unlike the cat this one goes as low as it is asked.
  1,672 and 3,346 were rendered side by side; at the size the room draws it the
  only visible difference is a slightly blockier beak.
- **Quantises the colours to bytes.** They arrive as float32 `VEC4` — sixteen
  bytes a vertex for values that came off a colour picker. Normalised unsigned
  bytes are four, and glTF and three.js both read them natively.

It is drawn smooth-shaded with `vertexColors`, creased at 69°, which keeps the
beak and the head tuft while rounding the body.

**It rides the chair.** The cat that was here counter-rotated against the
chair's slow swivel to hold a fixed world heading, which is what a live animal
on a turning seat does; a toy turns with the seat, so `CAT_WORLD_RY` went with
the cat. `PLUSH_RY` is chair-local and swept in the room like every other
heading in this file — the chair's forward already points into the room, so 0
is dead frontal and -2.1 shows the back of its head. -0.35 is a fraction off
frontal: both eyes, the beak and both feet, without a toy staring down the lens.

**`PLUSH_H` is 2.8 room units, crest to feet.** The first fit was 4.2, which
filled the seat and reached the backrest and read as a cat-sized animal rather
than as a toy. 1.4 was rendered as well and is a keyring — the eyes and the
beak stop reading at that size.

**It is seated by measurement, not by the file's origin.** The penguin's feet
are at y=-0.908 in its own space where the cat's happen to be at y=0, and
trusting either would have been luck. The load callback measures the fitted box
detached — `Box3.setFromObject` reports world space, for the reason written out
at the sofa cat — then seats it on the cushion at y=3.49, z=0.65.

It opens no panel, has no hover target and is not a `SCREENS` entry at all. It
is enrolled in `occCand` like every other prop so the camera-occlusion fade
still applies to it.

---

## The UI/UX passes

Findings from a review pass, and what was done about each. Verified with
headless Chromium captures at 1440×900 and 390×844 (DPR 3, touch emulated) plus
the in-page QA harness before and after.

### Fixed

**Mobile panel occupied ~20% of the screen.** Panel was anchored to the
monitor's projected rectangle in all cases; on a 390×844 phone the bottom half
of the viewport showed a keyboard while the case study was read through a
letterbox. Added `SHEET` / `sheetRect()`, and a short-circuit in `placePanel()`
and `focusOn()`. The panel is now a full-width bottom sheet at 82% viewport
height on touch devices; desktop projected placement is unchanged.

**Panel header truncated the title and the counter.** At 360px logical width
the header had to fit a title, a `4/11 · …` counter and three 44px controls,
and ellipsised down to `SELECTED…` / `6 cas…`. Added an
`@container panel (max-width: 480px)` rule that wraps the counter onto its own
row. Also removed `@media (max-width:620px){#gh i{display:none}}`, which used
to drop the counter outright on phones — that existed because the old panel had
nowhere to put it, and the sheet does. Widened `#gh i` from 42% to 56% so the
wide-panel case ellipsises less.

**The hero sold the toy, not the developer.** It read *"My room, right now"*
plus an explanation of the day cycle, and on mobile `#hero p` was hidden so only
the headline survived. Added a credential line (name, role, years, 33 titles,
Gameloft / Sipher / Bacoor) and a CTA row: **View CV ↗** as primary, **All 33
builds** opening the wall panel directly. The day-cycle blurb moved to
`p.room` and is the only part a phone drops.

**A mis-tap on the wall navigated away from the portfolio.** `activateHit()`
opened the build's WebGL link in a new tab on the first tap of a 33-tile grid.
It now opens the archive panel scrolled to that build and marks it (`.spot`),
where Play is a labelled control. Tiles carry `data-g` for the lookup;
`spotlightBuild()` divides the rect delta by the panel's `zoom` so the scroll
lands correctly in both placement modes.

**The open index collided with the control hint.** At 1440×900 the last index
row landed on top of the bottom-right hint text and both became unreadable.
`#idx.on ~ #hint` now dims alongside `#gridBtn`.

**The onboarding card outlived its welcome.** It dismissed on canvas drag but
not on opening a panel, so it sat over the content it was describing.
`focusOn()` now dismisses it.

**Jargon navigation.** `Nav matrix` → `Contents`; on the 2D page
`Build archive` → `Projects`, `Service log` → `Experience`, `Comms` →
`Contact`. Styling untouched. This is the most taste-dependent change here and
the easiest to revert if the voice matters more than the scan speed.

### Investigated and deliberately not changed

**Portrait camera framing.** The review flagged too much ceiling and floor on a
phone. `fit()` already opens the vertical FOV below 16:10 to hold the
horizontal field constant, capped at 86° with a comment explaining the cap.
The framing is the documented consequence of that cap, not an oversight.

**`Showreel · Controls` QA failure.** Did not reproduce when re-measured; see
the QA section above.

### Added since

**The wall readout.** Hovering a cover used to get `#tip`: a name and a verb.
That is the right weight for "this prop is a career timeline" and the wrong one
for a game, which has art, a category, a pitch and somewhere to go. `#hud` and
`tools/clips.py` are the answer; the section above covers the four decisions
that hold it up, and the one that took the most work — deferring the close while
the pointer crosses the room — is the one a reader is most likely to undo by
accident.

**The employer screen.** The centre monitor's face is a `brandTex()` canvas
carrying the real `images/athena.webp` lockup rather than a drawn approximation.
The logo is a wide transparent PNG whose mark occupies a band in the middle, so
pasting it whole would have rendered it tiny; `alphaBounds()` finds the opaque
bounding box by scanning a 256px copy (36k pixels rather than 8.7M) and the
paint crops to it. The load is async with the hand-drawn mark as the synchronous
fallback, so a missing or broken file degrades instead of leaving a blank
screen. Hovering the monitor opens the same readout the wall covers use — the
card abstraction was generalised for it, so any surface can now carry a `hud`
payload and the wall tiles are no longer a special case.

**A scroll-safe panel frame.** See the QA section: `#glass` is `overflow:clip`.

**Case files are spotlight targets.** `data-g` lived only on `.tile` and
`.lrow`, so `spotlightBuild` — the thing that scrolls the archive to the build
whose cover you just clicked — could never land on a write-up. It always fell
through to the plain grid tile repeating the same game further down. `.cf`
carries `data-g` now, and because the case files render above the grid, the
first-match lookup lands on the write-up without any change to the lookup
itself. The scroll maths also had to be clamped: centring an element taller
than the panel scrolls its own heading off the top, which is true of every
case-file card, so an element that cannot fit is aligned to the top instead.

**A debug readout behind five taps.** See its section above. It exists because
every conversation about rearranging this room ran aground on the same
question — *which wall, and where on it* — and the honest answer was always
"let me render a screenshot and measure it".

**A click is not a drag.** `pointerdown` set `drag = true`, and the frame loop
closed the readout on any drag, so the readout vanished under the cursor on
every click — and because `setHot` short-circuits while the target is unchanged,
nothing brought it back until the pointer left and returned. The loop now waits
for `moved` before treating a press as orbiting. This was invisible while every
prop opened a panel over the top of it; the `noPanel` monitor is what exposed
it.

### Second UI/UX pass

Measured over CDP at 1280x720, 1440x900, 1920x1080, iPad 1024x1366 with touch
emulated, and 390x844 / 360x640 / 414x896. `#qa=1` was 12/12 before and after.

**Every panel was a magnifying glass, and the container query was reading a
width the panel never had.** See §2 — this is the largest of these changes and
the only one that alters a documented decision.

**Two pieces of copy said something untrue.** `#hint` read `Time bar · 5 min =
1 day` while `CYCLE` is 600000 ms and the hero, three inches to the left, read
"a whole day passes every ten minutes". And all 33 entries in
`portfolio-data.js` carried the identical `"sub": "Make with Unity"` — an
ungrammatical string, repeated 33 times, in the line directly under the title
in the readout, and wrong for the Unreal work besides. The stored field is
corrected to "Made with Unity", but the readout no longer uses it: `availOf(g)`
derives the line from the links, which is the thing a visitor actually wants at
that moment. 30 of the 33 come out "Playable in browser", AR demo is an
"Android build", and the two Gameloft titles read "Video only · build under
NDA", which their own descriptions already said.

**Two of the room's main controls were under the touch floor on a tablet.**
`#idxBtn`, `#gridBtn`, `#real`, the hero CTAs and `#scrub` took their 44px from
`@media (max-width:820px)`, which a tablet is wider than: measured on a
1024x1366 iPad, Contents and View 2D were **124x27** and Resume **76x25**. The
rules moved into `@media (pointer:coarse)`, where they belong — the constraint
is the input, not the width. `#scrub` keeps its 3px rail (it is a hairline on
purpose) and grows a transparent 44px band around it via padding plus
`background-clip:content-box`. That made the time bar 12px taller, which put it
under the hero CTA row, so `#hero`'s bottom offset went 116 → 132; re-checked
for overlap at all three phone sizes.

**The 2D page asked for nothing above the fold.** At 1440x900 — the most common
way it is opened — `.cta` sat at y=908 against a 900px viewport, so "Open build
archive" and "Hire me" were both below the fold along with the stat row. A
`(min-width:961px) and (max-height:940px)` block tightens the hero's vertical
rhythm (avatar 234→168, headline cap 76→58, and the paddings around them);
`.cta` now ends at 729 and the stats at 816.

**Anchor jumps landed under the fixed nav.** `#nav` is `position:fixed` and
66px tall; `#index`, `#exp` and `#contact` had `scroll-margin-top: 0`, so every
route into a section — the three nav links, the hero CTA, every cluster card —
clipped the heading in half. `section[id]{scroll-margin-top:86px}`.

**The 2D page had no navigation at all on a phone.** `nav .links{display:none}`
below 960px with nothing in its place, on a page that measures **16,383px** at
390 wide. Added `.secbar`, a fixed bottom bar with the same three links, 50px
tall and thumb-reachable. It is a `<nav>`, so it also matches
`nav{position:fixed;inset:0 0 auto}` — `top:auto` in its own rule is
load-bearing, and without it the bar stretched into an opaque sheet over the
whole viewport.

### The desk pass: cutting what the walls already say

Three walls carry cover art now — the back grid (zone 1, eleven covers) and the
two side columns (zone 8 with three, zone 9 with four), eighteen of the 33
builds. The
desk was still enumerating the same games on its own screens, and the overlap
was measured rather than argued about:

| Surface | Builds | Already on a wall | In the bin | Only here |
| --- | --- | --- | --- | --- |
| `monL` MY GAMES | 12 | 8 | 3 | **1** |
| `net` NETCODE | 3 | **3** | 0 | **0** |
| `monR` RESKIN | 15 | 5 | 3 | 7 |
| `ar` AR | 3 | 1 | 0 | 2 |
| `phone` Google Play | 10 | 7 | 2 | **1** |
| `holo` Showreel | 30 | 17 | 5 | 8 |

Two of those are duplicates and the rest are not. `phone` and `holo` repeat
titles but not the *claim* — "shipped to a store", "there is video of it" are
different axes from "this is one of my own". `monL` and `net` had no axis of
their own left: the netcode trio **is** row 1 of the back wall, chosen to lead
it because networked work is the rarest thing in the set, and MY GAMES was
eleven-twelfths a second printing of covers hanging three metres away.

**The career timeline took the left monitor and the laptop went.** It was the
opposite case — the one panel nothing else in the room repeats — and it was
sitting on a MacBook at x −24.3…−16.7, which is the left monitor's own x range
(−24.2…−16.9) one step lower. The two screens overlapped in silhouette, which
is what made the left of the desk read as clutter while the right read as a
row. `#panel=job` still resolves; only the object carrying it changed.

**The three monitors are on one eye line.** Screen centres were 14.14 / 15.01 /
16.34 — the right panel was raised 2.2 on a `headX:.7` offset arm, which put
its bottom edge (13.84) above the centre monitor's centre. Both flanks are at
14.14 now with the centre at 15.01, taller because it is a bigger panel rather
than because it was lifted.

**Two props changed sides, and one of the moves was wrong first.** The right
wing carried four objects against the left wing's two, so the badge crossed to
the left, where the laptop had been. The phone was moved with it — out to
x=1.2, off the right monitor's axis — and that put it squarely in front of the
AR tablet at 4.3 and hid the tablet's label. Rendered and looked at, which is
the only way that was ever going to be caught. It sits at −2.2 now, forward
rather than sideways: sharing the monitor's x range is a depth relation the eye
reads correctly, standing in front of another screen is not.

**The corner kept its lit mass and lost its panel.** A server rack stood where
the netcode screen was, and the corner does need something vertical and lit —
the back-left of the frame is otherwise flat. It is a vending machine from the
same PolygonCyberCity pack now: 770 triangles and 46 kB against the rack's 2510
and 167 kB.

An arcade claw machine was the first choice, and it was converted, placed and
rendered before being rejected — which is the only way this could have been
decided. `prop()` gives every mesh an opaque atlas material, so the cabinet's
glass is not glass: the one feature that says "claw machine" renders as a flat
green panel, the 368 kB plushie insert behind it would never have been seen,
and what is left is a wide green crate two-thirds hidden behind the desk. The
shapes are the argument — 271 x 171 cm of claw machine against 260 x 71 of
vending machine — and in this corner, hemmed in by the left wall at x=−34 and
the locker at z=−19, only the second one can stand tall enough to clear the
desk. Both its light strips are placed off measurements taken from the mesh,
banded by height: the front face stops at y=16 and the two fins above it are
set back to z=0.4, so the marquee sits at 15.6 rather than crossing them in
mid-air.

**Four things a second pair of eyes caught, all of them framing rather than
content.** They are worth listing because each one is invisible in the source
and obvious in a render:

- **The AR tablet was inside the right monitor's silhouette.** Its top edge
  (11.9) rose past the monitor's bottom (11.64) and their x ranges overlapped
  by 1.9 units, so from the resting camera the two screens read as one shape
  with a label across the seam. The right wing is 9.3 units wide and the two
  want 11.8 of it, so nothing arranged across the back of that wing can work.
  The tablet took the badge's vacated place at the front of the desk instead,
  five units nearer the camera and clearly below the monitor.
- **The corner cabinet was too big twice.** At h=18 it crowded the career
  panel and reached the wall grid; the fix was not only height but position —
  h=14.5 at x=-30.1, z=-26.9, which is as far into the corner as the left wall
  at x=-34 allows for a 6.94-wide footprint. It now tops out below the
  monitors, which is the job: vertical mass in the back-left, not a second
  subject.
- **The chair sat 10.6 units in front of the desk** — further out than the
  desk is deep — which made the nearest, largest object in the lower frame a
  chair. At z=-8.6 it still clears the desk lip by 3.4.
- **The mug was a bare cylinder.** `CylinderGeometry(1.15,1,2.6,14)` in flat
  magenta: no handle, no rim, the one piece of placeholder geometry left on
  the desk. It is a Synty boba cup now, 444 triangles and 33 kB.

**A second round, driven by a screen-space overlap audit.** Looking at a
render and saying "those two are on top of each other" is where this started;
the way to settle it is to project every `SCREENS` quad's four corners through
the live camera, take the 2D AABBs, and intersect every pair. Run against the
resting camera at 1440x900, that turned four separate arguments into four
numbers — and it also proved which overlaps were harmless. Temporary
`window.__m = {T, scene, SCREENS, camera, chairG, ...}` at the end of the
module is enough to drive it from CDP; it is not committed, but re-add it for
five minutes the next time anything on the desk moves. Candidate positions can
be tried the same way, by moving the object at runtime and re-measuring, which
is how the badge's new place was chosen out of eight.

- **The phone prop is gone.** It listed the 10 Android builds, of which 7 hang
  on zone 1 or zone 9 and 2 are in the bin — one build in it was reachable
  nowhere else. It was also what made the front of the desk unworkable: its
  base stood on the mousepad, and the two places it did not were in front of
  the AR tablet or inside the right monitor's silhouette. The claim survives
  where a visitor can act on it — the contact card's Google Play row links the
  store, and each build keeps its own Android link in the archive. The QA
  harness's narrow anchor moved to `ar` with it.
- **The PC tower is gone.** A 6 x 15 x 9 `box()` in flat dark material with a
  violet panel and three fan quads, at x=-30, z=-13: the only untextured slab
  among fifteen Synty props, 15 units tall in the part of the left wall the
  camera passes closest to, and the third of five objects strung down that
  wall. `rgbFans` went with it.
- **The chair is tucked in and sits left.** z=-11.8, which is as far in as it
  goes: its footprint is 5.42 x 6.22 and at ry=.42 that projects to 7.88 of
  depth, so the seat back reaches z=-15.74 and another .3 would push the
  backrest up through the desk top. x=-19.6 parks it under the career panel
  instead of under the centre monitor, which is where a chair belongs at an L
  of desk this shape.
- **The cup crossed to the left of the keyboard.** Everything small had
  drifted to one side — badge and tablet both sit right of centre — so with
  the cup there too the left half of the desk surface was bare board. It is
  .5 clear of the mousepad's left edge and 20 px clear of the chair in
  projection, which is the pair of numbers that fixes it: the chair moving
  left and the cup moving left are the same trade, and the front-left of the
  desk is exactly what the chair covers.
- **The badge had to leave both wings.** Moving the chair in put it 100%
  inside the chair's projected silhouette — the measurement above, and the
  reason this round exists. The right wing was already spoken for by the AR
  tablet, and the left wing is 5 units wide against the badge's 5-unit
  footprint. It sits on the desk top between the centre and right monitors
  now, which the audit says is clear of the chair, the mousepad, both wings
  and every other screen. The boba cup slid 1.4 left to make room for it.

**A third round: the desk laid out left to right.** Small props had been
placed one at a time, each avoiding the last; this pass placed them as a row.
The keyboard block and the cup moved 1.5 left (`PAD_X` -7.75 → -9.25, keyboard
-10 → -11.5, mouse -2.1 → -3.6, cup -16.4 → -18.2), the AR tablet took the
left wing at half size, and the contact card took the right wing at 1.3x. Left
to right the desk now reads tablet · cup · keyboard · mouse · card, under
career · Athena · reskin.

- **The card is 4.94 x 2.81**, which is `badge.jpg`'s own 704 x 400 to three
  decimals — the photo is neither stretched nor cropped — inside a 5.6 x 3.5
  backing, so the card sits in its holder rather than overhanging it. Centred
  at x=2.5 and turned -.45 its world AABB reaches x=5.96, .04 inside the desk's
  own edge; at 2.7 it measured 6.16 and hung over. Measure the group's AABB,
  not the plane's: the stand is wider than the screen.
- **The tablet is at x=-22, z=-20.2, turned .55**, and every one of those is a
  measurement. The chair covers most of the left wing, so the spot was found by
  scanning a grid and scoring each one; .55 is the angle that puts the screen
  square to the resting camera at (12.6, 20.5, 31), which matters more at half
  size than anywhere else; and the wing's flat top ends at x=-21 — found by
  raycasting straight down onto the desk at half-unit steps — so the stand's
  right edge lands .5 inside it rather than on the bevel.
- **Halving a screen halves its label twice over**, once for the quad and once
  for the proportion, so `uiTex` gained a type-scale argument and the tablet
  asks for 1.8. Without it the tablet is a dark slab at 48 x 32 CSS px. That
  size is also below the 44 px touch floor; the hit proxy's 1.28x on touch is
  what stands between it and being unhittable, and if it ever needs to be
  bigger the scale is the thing to change, not the position.
- **The corner run has one standoff and even gaps.** The left wall's inner face
  is at x=-33.3 and the props were each a different distance off it; locker and
  crate moved to -31.2 and -30, which puts every cabinet's near edge about .2
  from the wall. Gaps along z were 3.31 and 2.39 between the three; the locker
  moved to z=-19.46, which makes both 2.85.

**A fourth round: everything inside the desk it stands on.** The card and the
tablet both passed a "is it on the desk" check and both visibly hung in the
air, because the check was measuring two wrong things at once.

- **A desk's top is not its bounding box.** `desk.glb` occupies x -26..6 and
  z -29..-16, but raycasting straight down onto it at .1 steps finds three
  separate flat tops: the main surface at y=7.38, chamfered in at the front so
  it ends at z=-16.1; the left wing at y=7.74 running x -25.9..-20.5; and the
  right wing, also 7.74, running x .5..5.9 and z -27.3..-17.4. The right wing
  is 5.4 wide where the desk's AABB is 32. A stand can clear x=6 by .04 and
  still be a unit and a half out over the step down to the main desk.
- **A screen group's AABB is not the screen either.** `addScreen` hangs a halo
  1.5x the quad and a hit proxy 1.12x on the same parent, so `setFromObject`
  on the group reports the glow. The card measured 7.29 across that way and is
  5.7 in fact — the difference is the whole of this round's problem. Build the
  box from `g.traverse` with every `s.halo` and `s.hit` skipped.
- **The card fits by straightening, not by shrinking.** A 5.7 x 3.1 base turned
  -.45 sweeps 5.7·cos.45 + 3.1·sin.45 = 6.48 across; at ry=0 it sweeps 5.7.
  Rotation is the expensive variable on this wing, which is short in x and long
  in z, so every degree of turn spends the axis that is scarce. Squaring it up
  paid for all but .3 of the excess; .93 of scale paid the rest, which leaves
  the card at 1.21x its original size instead of 1.3x. ry=0 is also the better
  angle — the resting camera is 51 units back and about 10 degrees off the
  wing's axis, where -.45 pointed the photo 26 degrees away from the room.
  Solid footprint now x .55..5.85 inside a wing that runs .5..5.9, front edge
  at z=-17.76 against the wing's -17.4.
- **The keyboard row went back .75, then .375, then back to 0** — `PAD_Z` is
  -18.5 again, where it started. The measurement that prompted the move is
  real: the mousepad's front edge at z=-16 hangs .1 over the desk's chamfered
  front at -16.1. It is also invisible from any camera the room allows, and
  every retreat that fixed it read as the keyboard sitting too far from the
  edge, so the overhang stays. Kept here because the next person to measure
  this will find the same .1 and be tempted by the same fix.
- **The tablet had the same fault at a twenty-fifth the size** — its base
  reached x=-20.27 against the left wing's inner edge at -20.5. x=-22 → -22.3.
- **The chair went to x=-21.2** (from -19.6) and then turned 30 degrees
  further left, `CHAIR_RY` .42 → .9436 — on this chair a rising ry turns the
  seat toward -x, because the model faces its own -z. The cat rides the chair,
  so the turn would have taken its face with it; the local angle it needs is
  now derived from a new `CAT_WORLD_RY` instead of being a literal that has to
  be hand-corrected every time the chair moves, which had already happened once
  (.45 → -.82). *(Since superseded: the chair cat was replaced by a penguin
  plush, which rides the chair rather than holding a world heading, and
  `CAT_WORLD_RY` is gone.)* The corner run closed up too:
  locker z -19.46 → -21.2, crate -11.5 → -15, which takes the gaps between
  vending machine, locker and crate from 2.85 to 1.1 each and pulls all three
  toward the zone-1 corner. The vending machine still stands .2 off the back
  wall and all three still stand .2 off the left wall. Re-running the 5x5
  raycast after the chair moved: nothing lost, `ar` and `card` still 100%.

**Bounding boxes over-report occlusion, and it cost half an hour.** The AABB
intersection above said the chair covered the AR tablet 100%; the render showed
it plainly visible. A chair's projected box is mostly empty — headrest, gap,
seat — so a box test answers a different question from "can I see it". The
honest test samples the quad on a 5x5 grid and raycasts each point back to the
camera against every solid mesh, counting the fraction that arrives: 96% for
the tablet where the box test said 0. Use the box test to find candidates and
the raycast to decide between them. Current numbers at the resting camera:
every desk screen 100%, `job` 80% (the centre monitor's bezel), `casual` 44%
(the bin stands behind the desk's front rail on purpose).

**The only overlap left in the room is 12 px** of the centre monitor's bezel
across the career panel's right edge — 9% of that panel, with the centre
monitor in front. That is what a three-monitor rig looks like from any angle,
and squaring it up would cost the arc.

**Weather in the city has to be measured after dark, and both mechanisms are
one-sided.** Aerial perspective — lerping a silhouette toward `SKY_BOT` — only
does work while the sky is brighter than the tower, so it is a daylight
mechanism and it is silently inert at night. The night mechanism is the
opposite lerp, toward the light a low deck traps under itself, and it is
silently inert at noon. Both have to be present, each gated on `daylight` or
`night`, or half the day has no weather in the window. Anyone tuning either
should check the other hour before believing the number.

**Any weather term applied flat across the four city layers is wrong.** `L.haze`
is the layer's distance, and distance is what weather attenuates by. A flat term
reads as a dimmer no matter how large it is; the same total, graded by `L.haze`,
reads as depth. This was the bug in `W.dark*.30` and it would be the bug in
anything added next to it.

**The city layers own renderOrder -30..-23** in silhouette/lit pairs, farthest
first. Anything meant to sit *inside* the skyline rather than in front of it
needs a fractional order between two pairs — the rain curtain is -26.5, which
fogs layers 0 and 1 and leaves 2 and 3 sharp. This is also the only handle
available, because every one of those materials is transparent and writes no
depth.

**`COLD` is decided at load, before anything is built, so it reads the hash
directly rather than `HP`.** `HP` is constructed a long way below the glass
section and the sheets are built up there. A cold visit constructs the snow
sheets and no rain or bead sheets, and a warm one the reverse — building both
and hiding one would cost four materials and two canvases for a state that
cannot occur, because `COLD` does not change during a visit. Every array
downstream (`rains`, `snows`, `beadSheets`, `snowSheets`) is therefore empty on
one path and iterated on the other, which is why every consumer is a `forEach`
and never an index.

**Anything that measures a value decided at load must force a real document
load.** `Page.navigate` to a URL differing only in its `#hash` is a
same-document navigation; the script does not re-run. This has now produced two
wrong conclusions — a stale rain probe and an audio measurement that said snow
was as loud as rain. `Page.reload(ignoreCache=True)` after setting the hash.

**Nothing at the window may be made to emit.** Three separate mechanisms have
now been caught doing it and the reports all came back in the same words — *the
glass is glowing and it looks wrong*. The curtain's colour held at its daytime
value after dark; then the curtain going paler and denser in a blizzard; then a
fill light standing 2.6 units from a window mullion and rendering that post at
158/255 against an unlit floor of 33. All three looked physically defensible on
paper.

The distinction that survives all three: **a surface that has snow on it, or sky
behind it, may legitimately be bright — a surface that has been made to emit may
not.** Before shipping anything that touches the aperture, freeze every moving
source in the frame and A/B it on the *same loaded page*; falling precipitation
puts a 2.6–5.1 noise floor on that crop, wide enough to hide the whole effect
you are measuring. And when something in the window looks lit, **raycast it**
before theorising: two of the three were found in one call by picking the pixel
and reading back what was actually under it.

`#qa=1` is **11/11** at 1440x900 and 390x844, on both the warm and the cold
build.

### Not attempted

**Texture payload.** See the payload table — needs measurement against the
`NearestFilter` sampling before it is worth doing.

**The 2D hero node sphere.** 33 unlabelled dots occupying half the hero, with
no affordance beyond "hover or tap a node". Low information density for the
area it takes, but changing it is a design decision, not a defect fix.

---
