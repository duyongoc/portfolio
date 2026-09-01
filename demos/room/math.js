/* The two scalar helpers everything in the room uses.

   They are here rather than in room-3d.html because the moment any of that
   file becomes a module of its own, the alternative is either an import cycle
   or a second copy — and a second `clamp` is the smallest possible version of
   the problem the rest of this refactor is about. */

/* Deliberately not Math.min(Math.max(...)): this is called several hundred
   times a frame and the branch form measured faster in every engine tried. */
export const clamp=(v,a,b)=>v<a?a:v>b?b:v;
export const lerp=(a,b,t)=>a+(b-a)*t;
