/* ─────────────────────────────────────────────────────────────
   netfield.js — 3D node field renderer (canvas 2D, no libs)
   Used by the "Network" family of portfolio variants.

   NetField(canvas, {
     count, shape, groups, colorOf, linkDist, spin, tilt, fill,
     linkRGB, hoverRGB, glow, nodeScale, pulse, drag,
     onHover(i,x,y), onLeave(), onClick(i)
   })
   shapes: sphere | torus | clusters | helix | ring | shell
   ───────────────────────────────────────────────────────────── */
function NetField(cv,opt){
  opt=Object.assign({
    count:33,shape:'sphere',groups:null,colorOf:()=>'#22e0ff',
    linkDist:.78,spin:.0022,tilt:-.32,fill:.38,
    linkRGB:'120,210,255',hoverRGB:'182,255,58',
    glow:true,nodeScale:1,pulse:true,drag:true,linkWidth:1,yScale:1,
    onHover:null,onLeave:null,onClick:null
  },opt||{});

  const ctx=cv.getContext('2d');
  const N=opt.count, GA=Math.PI*(3-Math.sqrt(5));
  let W=0,H=0,R=0,dpr=Math.min(devicePixelRatio||1,2);

  /* ── point layouts ───────────────────────────────────────── */
  function layout(){
    const p=[];
    if(opt.shape==='sphere'||opt.shape==='shell'){
      for(let i=0;i<N;i++){
        const y=1-(i/(N-1))*2, r=Math.sqrt(Math.max(0,1-y*y)), th=i*GA;
        const k=opt.shape==='shell'?(.72+.28*((i*7)%5)/4):1;
        p.push({x:Math.cos(th)*r*k,y:y*k,z:Math.sin(th)*r*k});
      }
    } else if(opt.shape==='torus'){
      const Rr=.72,rr=.30;
      for(let i=0;i<N;i++){
        const u=i*GA*2.1, v=i*GA*3.7;
        p.push({x:(Rr+rr*Math.cos(v))*Math.cos(u),y:rr*Math.sin(v),z:(Rr+rr*Math.cos(v))*Math.sin(u)});
      }
    } else if(opt.shape==='helix'){
      for(let i=0;i<N;i++){
        const t=i/(N-1), a=t*Math.PI*4.6+(i%2?Math.PI:0), rr=.52;
        p.push({x:Math.cos(a)*rr,y:(t*2-1)*.94,z:Math.sin(a)*rr});
      }
    } else if(opt.shape==='ring'){
      for(let i=0;i<N;i++){
        const a=i/N*Math.PI*2, band=(i%3-1)*.10;
        p.push({x:Math.cos(a)*(.88+band),y:band*.7,z:Math.sin(a)*(.88+band)});
      }
    } else if(opt.shape==='clusters'){
      const gs=[...new Set(opt.groups)];
      const cen=gs.map((g,i)=>{
        const y=1-(i/(Math.max(gs.length-1,1)))*2*.72-.14, r=Math.sqrt(Math.max(0,1-y*y));
        const th=i*2.399;
        return {x:Math.cos(th)*r*.72,y:y*.72,z:Math.sin(th)*r*.72};
      });
      let seed=1;
      const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647-.5};
      for(let i=0;i<N;i++){
        const c=cen[gs.indexOf(opt.groups[i])]||{x:0,y:0,z:0};
        p.push({x:c.x+rnd()*.52,y:c.y+rnd()*.52,z:c.z+rnd()*.52});
      }
    }
    return p;
  }

  const pts=layout().map((v,i)=>({...v,i,c:opt.colorOf(i),ph:(i*2.399)%6.283}));

  /* ── neighbour links ─────────────────────────────────────── */
  const pairs=[];
  const LD=opt.linkDist;
  for(let i=0;i<N;i++)for(let j=i+1;j<N;j++){
    const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y,dz=pts[i].z-pts[j].z;
    const d=Math.sqrt(dx*dx+dy*dy+dz*dz);
    if(d<LD)pairs.push([i,j,1-d/LD]);
  }

  /* ── state ───────────────────────────────────────────────── */
  let ry=0,rx=opt.tilt,vy=opt.spin,vx=0,dragging=false,lx=0,ly=0,hover=-1,t=0,run=true;
  const F=2.9;

  function size(){
    const r=cv.getBoundingClientRect();
    W=r.width;H=r.height;R=Math.min(W,H)*opt.fill;
    cv.width=Math.max(1,W*dpr);cv.height=Math.max(1,H*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  function rot(p){
    const cy=Math.cos(ry),sy=Math.sin(ry);
    const x=p.x*cy-p.z*sy, z0=p.x*sy+p.z*cy;
    const cx=Math.cos(rx),sx=Math.sin(rx);
    return {x,y:p.y*cx-z0*sx,z:p.y*sx+z0*cx};
  }
  const proj=v=>{const s=R*(F/(F-v.z));return {x:W/2+v.x*s,y:H/2+v.y*s*opt.yScale,d:(v.z+1)/2}};

  /* ── interaction ─────────────────────────────────────────── */
  if(opt.drag){
    cv.addEventListener('pointerdown',e=>{dragging=true;lx=e.clientX;ly=e.clientY;cv.classList.add('drag');
      try{cv.setPointerCapture(e.pointerId)}catch(_){}});
    addEventListener('pointerup',()=>{dragging=false;cv.classList.remove('drag')});
  }
  cv.addEventListener('pointermove',e=>{
    const r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
    if(dragging){
      vy=(e.clientX-lx)*.00042;vx=(e.clientY-ly)*.00034;
      ry+=(e.clientX-lx)*.006;rx+=(e.clientY-ly)*.005;
      rx=Math.max(-1.2,Math.min(1.2,rx));lx=e.clientX;ly=e.clientY;
    }
    let best=-1,bd=1e9;
    for(const p of pts){
      const v=rot(p);if(v.z<-.35)continue;
      const s=proj(v),dx=s.x-mx,dy=s.y-my,d=dx*dx+dy*dy;
      if(d<361&&d<bd){bd=d;best=p.i}
    }
    if(best!==hover){
      hover=best;
      if(hover<0&&opt.onLeave)opt.onLeave();
    }
    if(hover>=0&&opt.onHover){const s=proj(rot(pts[hover]));opt.onHover(hover,s.x,s.y)}
  });
  cv.addEventListener('pointerleave',()=>{hover=-1;opt.onLeave&&opt.onLeave()});
  cv.addEventListener('click',()=>{if(hover>=0&&opt.onClick)opt.onClick(hover)});

  addEventListener('resize',size);
  document.addEventListener('visibilitychange',()=>run=!document.hidden);
  if(window.IntersectionObserver)
    new IntersectionObserver(es=>run=es[0].isIntersecting&&!document.hidden,{threshold:.02}).observe(cv);

  /* ── draw loop ───────────────────────────────────────────── */
  function frame(){
    requestAnimationFrame(frame);
    if(!run||!W)return;
    t+=.016;
    if(!dragging){ry+=vy;rx+=vx;vy+=(opt.spin-vy)*.02;vx*=.94;rx+=(opt.tilt-rx)*.004}
    ctx.clearRect(0,0,W,H);
    const P=pts.map(p=>proj(rot(p)));

    ctx.lineWidth=opt.linkWidth;
    for(const [i,j,w] of pairs){
      const a=P[i],b=P[j],depth=(a.d+b.d)/2;
      let al=Math.pow(depth,2.1)*w*.85;
      if(al<.015)continue;
      const on=(hover===i||hover===j);
      ctx.strokeStyle='rgba('+(on?opt.hoverRGB:opt.linkRGB)+','+(on?Math.min(al*3+.28,.9):al).toFixed(3)+')';
      ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();
    }

    const order=P.map((p,i)=>i).sort((a,b)=>P[a].d-P[b].d);
    for(const i of order){
      const s=P[i],p=pts[i];
      const r=(1.5+s.d*3.5)*opt.nodeScale*(hover===i?1.9:1);
      const al=.25+s.d*.75;
      ctx.globalAlpha=al;ctx.fillStyle=p.c;
      if(opt.glow){ctx.shadowBlur=hover===i?22:10*s.d;ctx.shadowColor=p.c}
      ctx.beginPath();ctx.arc(s.x,s.y,r,0,6.283);ctx.fill();
      ctx.shadowBlur=0;
      if(opt.pulse&&s.d>.55){
        const ph=(t*.6+p.ph)%6.283;
        ctx.globalAlpha=al*.22*(1-ph/6.283);
        ctx.beginPath();ctx.arc(s.x,s.y,r+ph*2.6,0,6.283);
        ctx.strokeStyle=p.c;ctx.lineWidth=1;ctx.stroke();
        ctx.lineWidth=opt.linkWidth;
      }
      ctx.globalAlpha=1;
    }
  }
  size();frame();

  return {
    resize:size,
    get hover(){return hover},
    spinTo(v){opt.spin=v},
    focus(i){const p=pts[i];if(!p)return;ry=-Math.atan2(p.z,p.x)+Math.PI/2}
  };
}
