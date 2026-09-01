/* ═══ sound ═════════════════════════════════════════════════════
   Everything here is synthesised. The room is one HTML file whose textures are
   drawn into canvases at load; the same discipline says the audio is generated
   too, and it turns out rain and thunder are the two easiest things in the
   world to build out of filtered noise. The whole section adds no asset, no
   request and no decode — which matters more than usual on a page a recruiter
   opens once, on someone else's wifi, and closes.

   The bed is not an independent thing that happens to play during rain. Like
   every visual weather term it is a function of `W`, computed from the same
   numbers in the same frame, so the sound cannot disagree with the window
   about how hard it is raining. `windLean` drives the bed's brightness, so the
   gusts you can see are the gusts you can hear.

   Autoplay is a hard constraint and not a preference: no browser will start
   audio before a real gesture, so "on by default" can only ever mean "armed,
   and running from the first interaction". This room needs a drag to look
   around, so that arrives within seconds — but the choice is remembered, so
   anyone who mutes it stays muted on every later visit.

   ── why this is a file ──
   The first thing lifted out of room-3d.html, and it was chosen for being the
   least entangled thing in it: everything below reads exactly two values from
   the rest of the room — the weather object and whether the visit is a cold
   one — and owns its own DOM, its own storage and its own state. `W` is a
   const object mutated in place, so a reference taken once stays live;
   `windLean` is a `let` reassigned every frame, so it is a tick argument
   rather than a binding.

   The room is 7,700 lines in one file and that is defended in PROJECT.md as
   "no bundler". The defence is about bundling, not about files: this page has
   run `<script type="module">` for as long as it has used three.js, and a
   static host serves an import graph without a build step. So the question
   each further split has to answer is not "can we" but "does this piece read
   less from the room than it gives back". This one gives back 275 lines and
   reads two values.
   ═══════════════════════════════════════════════════════════════ */
import {clamp} from './math.js';

/* Returns the three things the room calls into: the per-frame update, the duck
   the readout takes while a clip plays, and a strike. Everything else —
   arming on the first gesture, the mute button, the volume slider, suspending
   on a hidden tab — is wired up in here and never spoken to from outside. */
export function createSound({W, COLD}){

  const SND={on:true, vol:.55, ctx:null, ready:false};
  try{
    SND.on=localStorage.getItem('room-sound')!=='0';
    const v=parseInt(localStorage.getItem('room-volume'),10);
    if(v>=0&&v<=100) SND.vol=v/100;
  }catch(e){}
  /* Two stored values that can contradict each other, so one of them wins here
     rather than at four call sites: a slider left at zero IS muted, whatever the
     mute flag says. */
  if(SND.vol<.005) SND.on=false;
  /* A master trim under the slider, not a new default. The room was mixed loud
     enough that the honest fix is half the bus, and lowering `vol` instead would
     only reach a first-time visitor — anyone who has ever touched the slider
     carries their own number in localStorage and would never see the change.
     The slider stays what it always was: a relative control over what is left. */
  const SND_TRIM=.5;

  let sMaster,sDuck,sBedG,sThun,sNoiseBuf,sBodyG,sHissG,sHissF,sLast=0;

  function sndBuild(){
    const AC=window.AudioContext||window.webkitAudioContext;
    if(!AC) return false;
    let ctx; try{ ctx=new AC() }catch(e){ return false }
    SND.ctx=ctx;

    const N=Math.floor(ctx.sampleRate*4);
    sNoiseBuf=ctx.createBuffer(1,N,ctx.sampleRate);
    const d=sNoiseBuf.getChannelData(0);
    for(let i=0;i<N;i++) d[i]=Math.random()*2-1;

    sMaster=ctx.createGain(); sMaster.gain.value=0; sMaster.connect(ctx.destination);
    sDuck=ctx.createGain();   sDuck.gain.value=1;   sDuck.connect(sMaster);
    sBedG=ctx.createGain();   sBedG.gain.value=1;   sBedG.connect(sDuck);
    sThun=ctx.createGain();   sThun.gain.value=1;   sThun.connect(sMaster);

    /* Two sources at incommensurable playback rates rather than one. A looped
       noise buffer has no click at its seam — one random sample follows another,
       which is what noise is — but it does have a PERIOD, and four seconds is
       short enough to hear the same shower come round again. Two loops beating
       against each other push that period past anyone's patience. */
    const mix=ctx.createGain(); mix.gain.value=.5;
    [1,.79].forEach(rate=>{
      const s=ctx.createBufferSource();
      s.buffer=sNoiseBuf; s.loop=true; s.playbackRate.value=rate;
      s.connect(mix); s.start(0,Math.random()*4);
    });

    /* Two bands, and they arrive at different times. The body is the rain
       itself; the hiss is rain hitting glass, which only really exists once it
       is coming down hard — hence the squared term on its gain. */
    const body=ctx.createBiquadFilter(); body.type='bandpass';
    /* A blizzard is not quiet rain, it is a different sound: no hiss at all, and
       what is left sits an octave and a half lower — wind against glass rather
       than water hitting concrete. Set once at build rather than per frame,
       because COLD cannot change during a visit. */
    body.frequency.value=COLD?190:480; body.Q.value=.45;
    sBodyG=ctx.createGain(); sBodyG.gain.value=0;
    mix.connect(body).connect(sBodyG).connect(sBedG);

    /* The hiss needs a TOP as much as a bottom. A lone highpass passes
       everything up to Nyquist, and measured that way a storm came out with its
       spectral centroid at 9.1kHz — which is not rain, it is static. Rain sits
       around 2-4kHz because a drop hitting glass is a small impact, not a hiss.
       Corner rides the weather and the gust; the ceiling does not move. */
    sHissF=ctx.createBiquadFilter(); sHissF.type='highpass';
    sHissF.frequency.value=1400; sHissF.Q.value=.7;
    /* Two lowpass stages, not one. A single biquad rolls off at 12dB/octave,
       which still left a measured centroid of 6.1kHz two octaves above the
       corner — the ceiling has to be a slope steep enough to actually be a
       ceiling. Raising Q instead would put a resonant peak right where the
       brightness already is. */
    const top1=ctx.createBiquadFilter(), top2=ctx.createBiquadFilter();
    top1.type=top2.type='lowpass';
    top1.frequency.value=top2.frequency.value=5600;
    top1.Q.value=top2.Q.value=.5;
    sHissG=ctx.createGain(); sHissG.gain.value=0;
    mix.connect(sHissF).connect(top1).connect(top2).connect(sHissG).connect(sBedG);

    /* Room tone. Not weather — the room's own air, at a level you notice only
       when it is missing. Without it, clear weather is digital silence, and
       digital silence is what a broken audio system sounds like. */
    const tone=ctx.createBiquadFilter(); tone.type='lowpass';
    tone.frequency.value=320; tone.Q.value=.4;
    const toneG=ctx.createGain(); toneG.gain.value=.038;
    mix.connect(tone).connect(toneG).connect(sDuck);
    return true;
  }

  function sndArm(){
    if(SND.ready||!SND.on) return;
    if(!sndBuild()) return;
    SND.ready=true;
    SND.ctx.resume();
    sndFade(SND.vol,2);          // never a hard start: two seconds up from nothing
  }
  function sndFade(to,secs){
    if(!SND.ready) return;
    const g=sMaster.gain, t=SND.ctx.currentTime;
    g.cancelScheduledValues(t); g.setValueAtTime(g.value,t);
    g.linearRampToValueAtTime(to*SND_TRIM,t+secs);
  }
  ['pointerdown','keydown','touchstart'].forEach(e=>addEventListener(e,sndArm,{passive:true}));

  /* Ducked, not paused. A showreel clip carries its own audio and the bed would
     fight it, but cutting the bed dead and bringing it back is more noticeable
     than leaving it under. */
  function sndDuck(on){
    if(!SND.ready) return;
    sDuck.gain.setTargetAtTime(on?.16:1,SND.ctx.currentTime,.12);
  }

  /* The bed follows the same `W.rain` the sheets do, offset by the clear-sky
     baseline so clear weather is silent rather than quietly raining. Everything
     moves by setTargetAtTime: a weather fade takes 17 seconds and the gain has
     to cross it as smoothly as the opacity does. */
  function sndTick(now,windLean){
    if(!SND.ready||now-sLast<120) return;
    sLast=now;
    const t=SND.ctx.currentTime, r=clamp((W.rain-.62)/2,0,1);
    /* A soft knee rather than a flat trim. Heavy rain was too loud; overcast and
       the room tone were not, and scaling the whole bed would have taken those
       down for a complaint nobody made. This costs the top of the range 40% and
       the bottom almost nothing — storm -40%, rain -19%, overcast -3% — so the
       dynamic range between weathers narrows instead of the whole thing getting
       quieter, which is also what a limiter would have done to it. */
    const knee=1-.40*Math.pow(r,1.2);
    /* Snow's signature is the ABSENCE of the sound rain makes. There is no hiss
       at all — the hiss is water hitting hard surfaces and snow does not hit —
       and the body drops to a sixth, which leaves the room tone alone carrying
       the frame. A room that goes quiet as the weather closes in is the most
       effective thing in this whole feature and it costs two multipliers.

       Not zero: a blizzard has a low roar, and going to silence would also make
       the mute button ambiguous — the one state the visitor must be able to
       tell apart from "off" is "on, and the weather is quiet". */
    const cw=COLD?.42:1;
    sBodyG.gain.setTargetAtTime(r*.21*knee*cw,t,.4);
    /* Superlinear, because hiss is what heavy rain adds and light rain has
       almost none of — but 1.6 rather than the 2 it started at. Squared put a
       5.3x loudness step between rain and storm, and a portfolio should not
       startle anyone; the weather fade is 17 seconds and the ear should have to
       work slightly to notice it has been crossed. */
    sHissG.gain.setTargetAtTime(COLD?0:Math.pow(r,1.6)*.11*knee,t,.4);
    sHissF.frequency.setTargetAtTime(1400+r*1400+Math.abs(windLean)*400,t,.5);
  }

  /* Thunder is the one moment worth the whole section, and it is nearly free:
     `fNear` already exists because the flash needed to know how far away it was.
     Sound covers a kilometre in three seconds, so the delay IS the distance —
     the same number that decides whether the room lights up decides how long you
     wait to hear about it, and near strikes crack while far ones roll.

     The rolls are the point of the envelope. Thunder is not a fade; it is a
     sound that keeps arriving, because it is one discharge heard along a path
     kilometres long with every part of it a different distance away. A smooth
     decay reads as a sound effect. */
  function sndThunder(near,peak){
    if(!SND.ready||!SND.on||document.hidden) return;
    /* Distance is paid for twice, and the second one is easy to miss. The gain
       term takes it once; the lowpass takes it again, because a narrower band
       carries less energy for the same gain. Measured, a far strike came out at
       0.021 against a storm bed sitting at 0.020 — the rumble was quieter than
       the rain that caused it. So the corner is linear rather than squared (a
       far strike keeps a little more of its 300Hz) and the gain term leans back
       toward the far end. Near strikes are unchanged; they were never the ones
       in trouble. */
    const ctx=SND.ctx, t0=ctx.currentTime+.3+(1-near)*8.5,
          dur=1.1+(1-near)*4.8, amp=(.22+peak*.5)*(.62+near*.38);
    const src=ctx.createBufferSource();
    src.buffer=sNoiseBuf; src.loop=true; src.playbackRate.value=.55+Math.random()*.5;
    const lp=ctx.createBiquadFilter(); lp.type='lowpass';
    lp.frequency.value=200+near*1750; lp.Q.value=.6;
    const hp=ctx.createBiquadFilter(); hp.type='highpass'; hp.frequency.value=26;
    const g=ctx.createGain(); g.gain.value=0;
    src.connect(lp).connect(hp).connect(g).connect(sThun);

    const atk=.005+(1-near)*.55, end=t0+dur;
    g.gain.setValueAtTime(0,t0);
    g.gain.linearRampToValueAtTime(amp,t0+atk);
    let t=t0+atk;
    for(let i=0,n=2+(Math.random()*3|0);i<n;i++){
      const nt=t+(dur-atk)/(n+1)*(.55+Math.random()*.9);
      if(nt>=t0+dur*.92) break;
      t=nt;
      g.gain.linearRampToValueAtTime(Math.max(0,amp*(1-(t-t0)/dur)*(.3+Math.random()*.65)),t);
    }
    g.gain.linearRampToValueAtTime(0,end);
    src.start(t0,Math.random()*3); src.stop(end+.05);

    // close strikes get the crack on top of the roll; distance eats it entirely
    const ca=amp*Math.max(0,near-.4)/.6*.9;
    if(ca>1e-4){
      const c=ctx.createBufferSource(); c.buffer=sNoiseBuf;
      const chp=ctx.createBiquadFilter(); chp.type='highpass';
      chp.frequency.value=700+near*1400;
      const cg=ctx.createGain(); cg.gain.value=0;
      c.connect(chp).connect(cg).connect(sThun);
      cg.gain.setValueAtTime(0,t0);
      cg.gain.linearRampToValueAtTime(ca,t0+.004);
      cg.gain.exponentialRampToValueAtTime(1e-4,t0+.30);
      c.start(t0,Math.random()*3); c.stop(t0+.35);
    }
  }

  {
    const btn=document.getElementById('snd'), sl=document.getElementById('volR'),
          num=document.getElementById('volN');
    const paint=()=>{
      btn.textContent=SND.on?'♪ Sound':'♪ Muted';
      btn.classList.toggle('off',!SND.on);
      btn.setAttribute('aria-label',SND.on?'Turn room sound off':'Turn room sound on');
      const pc=Math.round(SND.vol*100);
      if(+sl.value!==pc) sl.value=pc;
      num.textContent=(SND.on?pc:0)+'%';
    };
    const store=()=>{ try{
      localStorage.setItem('room-sound',SND.on?'1':'0');
      localStorage.setItem('room-volume',Math.round(SND.vol*100));
    }catch(e){} };
    /* Suspending is worth doing and worth delaying. A context left running at
       gain zero still holds an audio thread, but a slider dragged through zero on
       its way somewhere else must not tear the graph down and rebuild it, so the
       teardown waits to see whether the silence was meant. */
    let zzz=0;
    const idle=()=>{ clearTimeout(zzz);
      if(SND.ready&&!SND.on) zzz=setTimeout(()=>{ if(!SND.on&&SND.ready)SND.ctx.suspend() },1500) };
    btn.onclick=()=>{
      SND.on=!SND.on;
      // unmuting a slider somebody dragged to zero has to actually do something
      if(SND.on&&SND.vol<.02) SND.vol=.3;
      store(); paint();
      if(!SND.on){ sndFade(0,.35); idle(); return }
      if(!SND.ready){ sndArm(); return }
      SND.ctx.resume(); sndFade(SND.vol,.5);
    };
    sl.oninput=()=>{
      SND.vol=+sl.value/100;
      SND.on=SND.vol>0;
      store(); paint();
      if(SND.on&&!SND.ready){ sndArm(); return }
      /* 50ms, not the 350ms the button uses. The slider IS the ramp; a fade
         chasing the thumb lags it by a visible amount and feels broken. Not zero,
         because a step change on a gain node is a click. */
      if(SND.ready) sMaster.gain.setTargetAtTime(SND.on?SND.vol*SND_TRIM:0,SND.ctx.currentTime,.05);
      idle();
    };
    paint();
    /* A tab nobody is looking at should not be making noise or burning a thread
       on a filter graph. Suspend rather than mute: the context stops advancing,
       so a thunder scheduled eight seconds out survives the round trip. */
    document.addEventListener('visibilitychange',()=>{
      if(!SND.ready) return;
      if(document.hidden) SND.ctx.suspend(); else if(SND.on) SND.ctx.resume();
    });
  }

  return {tick:sndTick, duck:sndDuck, thunder:sndThunder};
}
