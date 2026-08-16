/* ───────────────────────────────────────────────────────────
   vshared.js — shared data helpers + common section builders
   for the "Network" variants. Requires data.js.
   ─────────────────────────────────────────────────────────── */
const CAT={
  multiplayer:{n:'Multiplayer',long:'Multiplayer / Netcode',c:'#22e0ff'},
  ar:{n:'AR',long:'Augmented Reality',c:'#ff5c8a'},
  personal:{n:'Personal',long:'Personal game',c:'#b6ff3a'},
  reskin:{n:'Prototype',long:'Prototype / reskin',c:'#8b7bff'}
};
const CAT_KEYS=Object.keys(CAT);
const FEATURED=['Netcode Battle','POLYGON Battle','Kinder Easter','Netcode Shooter2D','Color Shoot 2d','Survivor.io clone 2d'];

const JOBS=[
  {yr:'10/2024 — Present',t:'Unity Game Developer',co:'Optimizer · Team Leader',
   p:'Responsible for project stability, task assignment, team support and reporting.'},
  {yr:'9/2022 — 10/2024',t:'Unity Game Developer',co:'Bacoor · bountykinds.com',
   p:'Built ~70% of the project on the front-end side: main menu UI, map, items, data, gameplay and asset bundles.'},
  {yr:'2/2022 — 8/2022',t:'Unreal Game Developer (C++)',co:'Sipher · playsipher.com',
   p:'Built the enemy core system, movement, weapon modules, animator, data and AI.'},
  {yr:'7/2019 — 2/2022',t:'Unity Game Developer',co:'Gameloft',
   p:'Worked on several projects — these are the publicly available titles:',
   ul:['<b>Applaydu &amp; Friends</b> — 12-player party royale: main menu UI, chat feature, gameplay bug fixing.',
       '<b>Kinder Easter</b> — main menu UI, QR code scanning, AR toys, gameplay bug fixing.',
       '<b>Dragon Mania Legends</b> — DLC updates, Ads integration, gameplay bug fixing.']},
  {yr:'2016 — 2019',t:'Cao Thang Technical College',co:'Education'}
];

const SKILLS=[
  {n:'Gameplay systems',v:95},{n:'Multiplayer / netcode',v:88},
  {n:'C# · Unity',v:95},{n:'C++ · Unreal',v:78},
  {n:'AR (ARFoundation)',v:80},{n:'UI / UX · tools',v:85}
];

const playOf=g=>g.links.find(l=>l.kind==='WebGL')||g.links.find(l=>l.kind==='Android')||g.links[0];
const actionOf=p=>p.kind==='WebGL'?'Play in browser':p.kind==='Android'?'Google Play':'Watch demo';
const shortOf=p=>p.kind==='WebGL'?'Play':p.kind==='Android'?'Store':'Watch';
const feat=()=>FEATURED.map(t=>GAMES.find(g=>g.title===t)).filter(Boolean);
const countOf=k=>k==='all'?GAMES.length:GAMES.filter(g=>g.cat===k).length;
const imgOf=g=>`src="${g.info}" onerror="this.src='${g.intro}'"`;

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
    b.className='fbtn'+(i?'':' on');
    b.textContent=c.n+' ('+countOf(c.k)+')';
    b.onclick=()=>{el.querySelectorAll('.fbtn').forEach(x=>x.classList.remove('on'));b.classList.add('on');onPick(c.k)};
    el.appendChild(b);
  });
}

/* ── index table ── */
function renderTable(el,k){
  el.innerHTML=GAMES.filter(g=>k==='all'||g.cat===k).map((g,i)=>{
    const p=playOf(g),v=CAT[g.cat];
    return `<a class="trow" href="${p.url}" target="_blank">
      <span class="no">${String(i+1).padStart(2,'0')}</span>
      <img class="th" loading="lazy" ${imgOf(g)} alt="">
      <h4>${g.title}${g.wip?'<span class="wip">WIP</span>':''}</h4>
      <span class="cat"><i style="background:${v.c}"></i>${v.n}</span>
      <span class="act">${shortOf(p)} ↗</span></a>`;
  }).join('');
}

/* ── card grid ── */
function renderGrid(el,k){
  el.innerHTML=GAMES.filter(g=>k==='all'||g.cat===k).map((g,i)=>{
    const p=playOf(g);
    return `<a class="gcard reveal" href="${p.url}" target="_blank" style="transition-delay:${Math.min(i*24,280)}ms">
      <div class="th"><img loading="lazy" ${imgOf(g)} alt="${g.title}">
        <div class="ov"><b>${actionOf(p)} ↗</b></div></div>
      <div class="b"><h4>${g.title}${g.wip?' <em style="color:var(--acc-3);border-color:var(--acc-3)">WIP</em>':''}</h4>
        <div class="m">${g.tags.map(t=>`<em>${t}</em>`).join('')}</div></div></a>`;
  }).join('');
  watch(el);
}

/* ── timeline ── */
function renderTimeline(el){
  el.innerHTML=JOBS.map(j=>`<div class="ent reveal">
    <div class="yr">${j.yr.toUpperCase()}</div>
    <h3>${j.t}</h3><div class="co">${j.co}</div>
    ${j.p?`<p>${j.p}</p>`:''}
    ${j.ul?`<ul>${j.ul.map(x=>`<li>${x}</li>`).join('')}</ul>`:''}</div>`).join('');
  watch(el);
}

/* ── node tooltip wiring for a NetField ── */
function tooltip(tipEl,box){
  return {
    show(i,x,y){
      const g=GAMES[i],p=playOf(g);
      tipEl.innerHTML=`<b>${g.title}</b><div class="c">${CAT[g.cat].n} · node ${String(i+1).padStart(2,'0')}</div>
        <div class="t">${g.tags.map(t=>`<em>${t}</em>`).join('')}</div>
        <div class="go">${actionOf(p)} ↗</div>`;
      tipEl.style.left=x+'px';tipEl.style.top=y+'px';
      tipEl.classList.add('on');
    },
    hide(){tipEl.classList.remove('on')}
  };
}

/* ── boilerplate: year + counts ── */
function fillCounts(){
  document.querySelectorAll('[data-n]').forEach(e=>{
    const k=e.dataset.n;
    e.textContent=k==='year'?new Date().getFullYear():countOf(k);
  });
}
