/* ───────────────────────────────────────────────────────────
   portfolio-shared.js — shared data helpers + common section builders.
   Requires portfolio-data.js.
   ─────────────────────────────────────────────────────────── */
const CAT={
  multiplayer:{n:'Multiplayer',long:'Multiplayer / Netcode',c:'#5ad0ff'},
  ar:{n:'AR',long:'Augmented Reality',c:'#ff599e'},
  personal:{n:'Personal',long:'Personal game',c:'#7d77f7'},
  reskin:{n:'Prototype',long:'Prototype / reskin',c:'#df7ff5'}
};
const CAT_KEYS=Object.keys(CAT);
const FEATURED=['Netcode Battle','POLYGON Battle','Kinder Easter','Netcode Shooter2D','Color Shoot 2d','Survivor.io clone 2d'];

const JOBS=[
  // every other row reads "company · where", so the role belongs in the title
  {yr:'10/2024 — Present',t:'Unity Game Developer · Team Leader',co:'Optimizer',
   p:'Responsible for project stability, task assignment, team support and reporting.'},
  {yr:'9/2022 — 10/2024',t:'Unity Game Developer',co:'Bacoor · bountykinds.com',
   p:'Built ~70% of the project on the front-end side: main menu UI, map, items, data, gameplay and asset bundles.'},
  {yr:'2/2022 — 8/2022',t:'Unreal Game Developer (C++)',co:'Sipher · playsipher.com',
   p:'Built the enemy core system, movement, weapon modules, animator, data and AI.'},
  {yr:'7/2019 — 2/2022',t:'Unity Game Developer',co:'Gameloft',
   p:'Worked on several projects — these are the publicly available titles:',
   ul:['Applaydu & Friends — 12-player party royale: main menu UI, chat feature, gameplay bug fixing.',
       'Kinder Easter — main menu UI, QR code scanning, AR toys, gameplay bug fixing.',
       'Dragon Mania Legends — DLC updates, Ads integration, gameplay bug fixing.']},
  {yr:'2016 — 2019',t:'Cao Thang Technical College',co:'Education'}
];

const playOf=g=>g.links.find(l=>l.kind==='WebGL')||g.links.find(l=>l.kind==='Android')||g.links[0];
const actionOf=p=>p.kind==='WebGL'?'Play in browser':p.kind==='Android'?'Google Play':'Watch demo';
const shortOf=p=>p.kind==='WebGL'?'Play':p.kind==='Android'?'Store':'Watch';
const feat=()=>FEATURED.map(t=>GAMES.find(g=>g.title===t)).filter(Boolean);
const countOf=k=>k==='all'?GAMES.length:GAMES.filter(g=>g.cat===k).length;

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
    b.textContent=c.n+' ('+countOf(c.k)+')';
    b.setAttribute('aria-pressed',String(i===0));
    b.onclick=()=>{el.querySelectorAll('.fbtn').forEach(x=>{
      x.classList.remove('on');x.setAttribute('aria-pressed','false')
    });b.classList.add('on');b.setAttribute('aria-pressed','true');onPick(c.k)};
    el.appendChild(b);
  });
}
