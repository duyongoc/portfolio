#!/usr/bin/env python3
"""Serve the site locally, and re-bake the wall the moment the layout is saved.

The pages need a server anyway — they are ES modules — so the watching lives
here rather than in a second terminal. Editing wall-layout.txt and saving it is
the whole gesture: this notices, runs wallsheet.py, and reloads the page that
is already open.

It exists because the walls cannot be read from the .txt at runtime. Their
covers are pixels in a baked JPEG, so a reorder is a re-render, and the step
between saving and seeing is exactly the step that gets forgotten. Nothing
here ships: the reload script is injected into the response, never written into
demos/room-3d.html, and the deployed site has no idea this file exists.

    python3 tools/serve.py
"""
import functools, http.server, os, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAKE = [sys.executable, os.path.join(ROOT, 'tools', 'wallsheet.py')]

# What a bake is made of. portfolio-data.js is in here because a new project,
# or a retitled one, changes the sheets as surely as reordering a zone does.
WATCH = ['wall-layout.txt', 'demos/portfolio-data.js', 'demos/portfolio-shared.js']

_lock = threading.Condition()
_gen = 0                                # bumped once per successful bake

# Polled by the injected script. Held open until the generation moves so a save
# reloads the page immediately rather than up to a poll interval later; the
# timeout is what keeps a proxy, or a sleeping laptop, from holding it forever.
HOLD = 25

RELOAD = b'''<script>
/* injected by tools/serve.py - local dev only, not in the repo copy */
(function(){var g=null;(function poll(){
  fetch('/__reload?g='+(g===null?'':g),{cache:'no-store'}).then(function(r){return r.text()})
   .then(function(n){ if(g!==null&&n!==g){location.reload();return;} g=n; poll(); })
   .catch(function(){ setTimeout(poll,1000); });
})();})();
</script>'''


def stamp():
    out = []
    for rel in WATCH:
        p = os.path.join(ROOT, rel)
        out.append(os.path.getmtime(p) if os.path.exists(p) else 0)
    return tuple(out)


def watch():
    """Re-bake on save.

    The stamp is re-taken after the bake, not before: wallsheet.py rewrites the
    id table at the foot of the layout, and that write is a change to a watched
    file, which would otherwise bake a second time for nothing.

    A failed bake does not move the generation. The last good JPEGs and map stay
    on disk and the open page stays on them — an unreadable layout should leave
    you looking at the room you had, with the reason on stdout."""
    global _gen
    last = stamp()
    while True:
        time.sleep(0.4)
        now = stamp()
        if now == last:
            continue
        time.sleep(0.15)                # let an editor finish writing
        print('\n--- wall-layout.txt changed, baking ---', flush=True)
        ok = subprocess.run(BAKE, cwd=ROOT).returncode == 0
        last = stamp()
        if not ok:
            print('--- bake failed, the room keeps the last good sheets ---', flush=True)
            continue
        with _lock:
            _gen += 1
            _lock.notify_all()
        print('--- reloading the page ---', flush=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # No caching at all locally. The room loads its textures with a ?v= that
        # only moves when the pixels do, which is right for the deployed site and
        # exactly wrong here: a re-bake that comes out to the same hash would be
        # served from cache and look like the save did nothing.
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_GET(self):
        if self.path.split('?')[0] == '/__reload':
            return self.reload_poll()
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, 'index.html')
        if not path.endswith('.html') or not os.path.exists(path):
            return super().do_GET()
        body = open(path, 'rb').read()
        cut = body.lower().rfind(b'</body>')
        body = (body[:cut] + RELOAD + body[cut:]) if cut >= 0 else body + RELOAD
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def reload_poll(self):
        was = self.path.partition('g=')[2]
        with _lock:
            if str(_gen) == was:
                _lock.wait(HOLD)
            now = str(_gen).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(now)))
        self.end_headers()
        self.wfile.write(now)

    def log_message(self, fmt, *a):
        if '__reload' not in (a[0] if a else ''):
            super().log_message(fmt, *a)


def main():
    a = sys.argv[1:]
    port = int(next((x for x in a if x.isdigit()), 8000))
    bind = a[a.index('--bind') + 1] if '--bind' in a else '127.0.0.1'
    if subprocess.run(BAKE, cwd=ROOT).returncode != 0:
        return 1                        # start from a room that is actually correct
    threading.Thread(target=watch, daemon=True).start()
    srv = http.server.ThreadingHTTPServer(
        (bind, port), functools.partial(Handler, directory=ROOT))
    print('\nhttp://%s:%d/  — watching %s, saving re-bakes and reloads'
          % ('127.0.0.1' if bind in ('', '0.0.0.0') else bind, port,
             ', '.join(WATCH)))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
