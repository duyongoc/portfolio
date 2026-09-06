/* ───────────────────────────────────────────────────────────
   portfolio-shared.js — shared data helpers + common section builders.
   Requires portfolio-data.js.

   Both pages load this as a plain script, so everything here is a global.
   Anything defined in BOTH pages belongs in this file rather than in either
   of them: two `const esc=` at the top level of two classic scripts is not
   only a duplicate, it is a redeclaration error waiting for whoever loads
   them together.
   ─────────────────────────────────────────────────────────── */

/* The category table. Every filter, swatch, label and baked section stripe is
   drawn from here, in both pages and in tools/wallsheet.py — which reads this
   block out of this file rather than restating the colours in Python.

   `section` is the heading a category is known by in build_layout.txt (`auto
   section=RESKIN`) and on the baked covers. It used to be a second field on
   every project in portfolio-data.js, kept in step with `cat` by hand across
   all 33 of them — measured, a perfect 1:1 map, so it carried no information
   and could only ever drift. It is a property of the category, and it lives
   with the category. */
const CAT={
  multiplayer:{n:'Multiplayer',long:'Multiplayer / Netcode',section:'Multiplayer Games',c:'#5ad0ff'},
  ar:{n:'AR',long:'Augmented Reality',section:'AR Games',c:'#ff599e'},
  personal:{n:'Personal',long:'Personal game',section:'MY GAMES',c:'#7d77f7'},
  reskin:{n:'Prototype',long:'Prototype / reskin',section:'RESKIN',c:'#df7ff5'}
};
const CAT_KEYS=Object.keys(CAT);
/* What an `auto section=` rule from the layout resolves through, so the
   headings are never written down a second time. The inverse map — heading to
   category key — is the bake's business and lives in tools/portfolio.py; it is
   not built here because nothing on either page has ever needed it. */
const inSection=(g,name)=>CAT[g.cat]&&CAT[g.cat].section===name;

const FEATURED=['Netcode Battle','POLYGON Battle','Kinder Easter','Netcode Shooter2D','Color Shoot 2d','Survivor.io clone 2d'];

const JOBS=[
  // every other row reads "company · where", so the role belongs in the title
  {yr:'10/2024 — Present',t:'Unity Game Developer · Team Leader',co:'Optimizer',
   p:'Responsible for project stability, task assignment, team support and reporting.'},
  // url only where the row already prints a domain: a company name that does
  // not look like a link should not quietly become one, and a printed .com that
  // is not clickable is a control that does nothing.
  {yr:'9/2022 — 10/2024',t:'Unity Game Developer',co:'Bacoor · bountykinds.com',
   url:'https://bountykinds.com',
   p:'Built ~70% of the project on the front-end side: main menu UI, map, items, data, gameplay and asset bundles.'},
  {yr:'2/2022 — 8/2022',t:'Unreal Game Developer (C++)',co:'Sipher · playsipher.com',
   url:'https://playsipher.com',
   p:'Built the enemy core system, movement, weapon modules, animator, data and AI.'},
  {yr:'7/2019 — 2/2022',t:'Unity Game Developer',co:'Gameloft',
   p:'Worked on several projects — these are the publicly available titles:',
   ul:['Applaydu & Friends — 12-player party royale: main menu UI, chat feature, gameplay bug fixing.',
       'Kinder Easter — main menu UI, QR code scanning, AR toys, gameplay bug fixing.',
       'Dragon Mania Legends — DLC updates, Ads integration, gameplay bug fixing.']},
  {yr:'2016 — 2019',t:'Cao Thang Technical College',co:'Education'}
];

/* A build can have no links at all: build_links.txt lets every slot be empty,
   which is what a build under NDA with no video yet looks like. So playOf returns
   undefined there, and everything that takes its result takes undefined —
   rather than each caller testing g.links.length before it dares ask. */
const playOf=g=>g.links.find(l=>l.kind==='WebGL')||g.links.find(l=>l.kind==='Android')||g.links[0];
/* One case per kind, no catch-all. The tail used to be a bare else, so a
   Source link reaching either of these — which it does the moment a build's
   only link is its repository, one edit to build_links.txt away — was labelled
   "Watch demo" on a button that opens GitHub. Nothing pointed at it: playOf
   prefers WebGL then Android, and all three builds with a Source link happen
   to have a WebGL build too, so the branch was unreachable by accident rather
   than by design. */
const actionOf=p=>!p?'No public link yet':p.kind==='WebGL'?'Play in browser'
  :p.kind==='Android'?'Google Play':p.kind==='Source'?'View source':'Watch demo';
const shortOf=p=>!p?'':p.kind==='WebGL'?'Play'
  :p.kind==='Android'?'Store':p.kind==='Source'?'Source':'Watch';
const feat=()=>FEATURED.map(t=>GAMES.find(g=>g.title===t)).filter(Boolean);
const countOf=k=>k==='all'?GAMES.length:GAMES.filter(g=>g.cat===k).length;

/* ── markup helpers, shared by both pages ──
   These were a copy each. Nothing about escaping a title or resolving a
   thumbnail is specific to a room or to a scrolling page, and the two copies
   had already drifted once — the flat page's cards were missing the
   screen-reader note the room's carry on every link that leaves the site. */

/* Every string here comes from portfolio-data.js, which we own — but a title
   with an ampersand in it is one edit away, and finding out by watching a
   panel render blank is a bad way to find out.

   The apostrophe is here for a second reason, not for symmetry. Everywhere
   else this lands in a double-quoted HTML attribute, where `"` is the only
   quote that can end it — but img() below interpolates into a JS string
   literal that is itself single-quoted, inside the attribute. Two titles
   already carry an apostrophe (Beat'em up), and the paths are derived from
   titles, so the distance between "does not happen" and "the onerror handler
   is a syntax error" is one change to how a thumbnail gets named. */
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);

/* A content hash on the end of a picture or a clip, from the map in
   demos/asset-v.js. These are the only files either page names by a rule
   instead of by a bake — thumb() rewrites an image path below, and the room
   builds a clip path out of CLIP_OF — so their URLs do not move when the file
   behind them does, and a browser holding the old bytes never finds out. The
   place that showed is the wall: its cover is baked into a JPEG that carries
   WALL_SHEET_V and updates, while the readout that opens over it and the panel
   behind that go on playing the previous cut and drawing the previous crop.

   Keyed from the site root, which is what these paths reduce to: the '../' is
   here because this file is read from demos/ as well as from the root, and at
   the root the URL parser clamps a leading '..' rather than letting it escape.
   Absent map, absent key, absent path: return what came in. A missing asset-v.js
   is a page with no cache-busting, not a page of broken images. */
const vsrc=p=>{
  if(!p) return p;
  const v=(typeof ASSET_V!=='undefined'?ASSET_V:null);
  if(!v) return p;
  const h=v[p.replace(/^(?:\.\.\/)+/,'')];
  return h?p+'?v='+h:p;
};

/* portfolio-data.js stores the full-size path; only the thumbnails are
   shipped. Must agree with thumb_path() in tools/portfolio.py — which hashes
   the same files vsrc() looks up, so the two cannot be pointed at different
   pictures. */
const thumb=p=>p?vsrc(p.replace('../images/','../images/thumb/')
                       .replace(/\.(jpe?g|png)$/i,'.jpg')):'';

const externalNote='<span class="sr"> (opens externally)</span>';

/* The `info` shot, falling back to `intro` — the other thumbnail, not the
   full-size original: shipping 6 MB of art to insure against a 404 on a file
   sitting in the same commit as its own fallback is the wrong trade. */
const img=g=>`<img loading="lazy" decoding="async" alt="" src="${esc(thumb(g.info))}"
  onerror="this.onerror=null;this.src='${esc(thumb(g.intro))}'">`;

/* The attributes of an element that IS a link, or nothing at all when the
   build has none. Used where a whole card is the anchor: an <a> with no href
   is still an <a>, so the card keeps its styling, but it is not focusable, not
   clickable and announces nothing — which is the truth about a build with no
   link. The alternative was seven ternaries picking between two tag names. */
const hrefAttr=l=>l?` href="${esc(l.url)}" target="_blank" rel="noopener"`:'';

/* The row of links under a card: the one worth pressing, then the rest.
   Both pages render this identically and both derive it the same way, so the
   derivation lives here even though the cards around it do not — their
   wrappers really are different shapes, and folding those together would be
   inventing a template language to save four lines.

   It used to stop after two more, which was a cap from when the links were
   hand-written in portfolio-data.js and nothing was going to add a fourth. It
   did have something to hide: the netcode builds carry a second Youtube, and
   that link had been in the data, unreachable from either page, the whole
   time. build_links.txt is edited to be shown, so everything in it is shown,
   and `.lk` already wraps. */
const linkRow=g=>{
  if(!g.links.length) return '';
  const p=playOf(g), rest=g.links.filter(l=>l!==p);
  return `<div class="lk"><a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(shortOf(p))} ↗${externalNote}</a>`+
    rest.map(l=>`<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label||l.kind)}${externalNote}</a>`).join('')+
    `</div>`;
};

/* ── reveal on scroll ── */
const OBS=new IntersectionObserver(es=>es.forEach(e=>{
  if(e.isIntersecting){e.target.classList.add('in');OBS.unobserve(e.target)}
}),{threshold:.05,rootMargin:'0px 0px -40px'});
const watch=(root=document)=>root.querySelectorAll('.reveal:not(.in)').forEach(e=>OBS.observe(e));

/* ── nav shadow ── */
function navScroll(sel='.nav'){
  const n=document.querySelector(sel);
  if(n)addEventListener('scroll',()=>n.classList.toggle('on',scrollY>30),{passive:true});
}

/* ── filter buttons ── */
function buildFilters(el,onPick,labels){
  const list=[{k:'all',n:(labels&&labels.all)||'All'},...CAT_KEYS.map(k=>({k,n:CAT[k].n}))];
  el.innerHTML='';
  list.forEach((c,i)=>{
    const b=document.createElement('button');
    b.type='button';
    b.className='fbtn'+(i?'':' on');
    /* The key each button stands for, on the button. The flat page needs it to
       drive a filter from its cluster cards, and used to recover it by walking
       el.children in the order this loop happens to append them — a contract
       between two files that nothing could check and a reorder here would have
       broken silently. */
    b.dataset.k=c.k;
    b.textContent=c.n+' ('+countOf(c.k)+')';
    b.setAttribute('aria-pressed',String(i===0));
    b.onclick=()=>{el.querySelectorAll('.fbtn').forEach(x=>{
      x.classList.remove('on');x.setAttribute('aria-pressed','false')
    });b.classList.add('on');b.setAttribute('aria-pressed','true');onPick(c.k)};
    el.appendChild(b);
  });
}
