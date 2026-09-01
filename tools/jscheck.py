#!/usr/bin/env python3
"""Parse every script this site ships, and check the two pages agree on what
is global.

Both HTML pages are single files with their JS inline, which is the right shape
for a static host with no bundler and the wrong shape for finding out you have
a syntax error — the only reader is a browser, and a browser reports it into a
console nobody has open. This parses each block on its own and says where.

It also checks the thing that made a duplicate helper dangerous rather than
merely untidy: portfolio-shared.js and the flat page's script are both CLASSIC
scripts, so they share one top-level lexical scope, and a `const esc=` in each
is a redeclaration error that takes the whole page down. Nothing about reading
either file on its own shows that.

Wants node on PATH, purely as a parser — nothing is executed.

    python3 tools/jscheck.py
"""
import os, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portfolio import ROOT

PAGES = ['demos/room-3d.html', 'demos/portfolio-2d.html']
# loaded with <script src=>, so they share one top-level scope with the pages
PLAIN = ['demos/portfolio-data.js', 'demos/portfolio-shared.js', 'demos/wall-layout.js']
# imported, so each has a scope of its own and can declare whatever it likes
MODULES = sorted(
    os.path.join('demos/room', f) for f in os.listdir(os.path.join(ROOT, 'demos/room'))
    if f.endswith('.js')) if os.path.isdir(os.path.join(ROOT, 'demos/room')) else []

# <script> with no src. type="module" is parsed as a module, everything else as
# a classic script — the distinction matters: `import` is only legal in one and
# a top-level redeclaration is only shared in the other.
BLOCK = re.compile(r'<script([^>]*)>(.*?)</script>', re.S | re.I)
SRC = re.compile(r'\bsrc\s*=', re.I)
MODULE = re.compile(r'type\s*=\s*["\']module["\']', re.I)
# A top-level `const x=` / `let x=` / `function x(`, at column 0 only: anything
# indented is inside a block and cannot collide across files.
TOP = re.compile(r'^(?:const|let|var)\s+([A-Za-z_$][\w$]*)|^function\s+([A-Za-z_$][\w$]*)',
                 re.M)


def parse(label, code, module):
    """node --check, with the line numbers mapped back onto the real file."""
    suffix = '.mjs' if module else '.js'
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, code.encode())
        os.close(fd)
        r = subprocess.run(['node', '--check', path], capture_output=True, text=True)
        if r.returncode == 0:
            return True
        print('%s:\n%s' % (label, r.stderr.strip()), file=sys.stderr)
        return False
    finally:
        os.unlink(path)


def globals_of(code):
    return {a or b for a, b in TOP.findall(code)}


def main():
    if not subprocess.run(['which', 'node'], capture_output=True).returncode == 0:
        raise SystemExit('node is not on PATH — this uses it as a JS parser only')
    ok = True
    classic = {}                       # name -> the files that declare it globally

    for rel in PLAIN:
        code = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        ok = parse(rel, code, module=False) and ok
        for n in globals_of(code):
            classic.setdefault(n, []).append(rel)

    for rel in MODULES:
        ok = parse(rel, open(os.path.join(ROOT, rel), encoding='utf-8').read(),
                   module=True) and ok

    for rel in PAGES:
        src = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        # line number of each block, so a failure names somewhere real
        for m in BLOCK.finditer(src):
            attrs, code = m.group(1), m.group(2)
            if SRC.search(attrs) or not code.strip():
                continue
            line = src.count('\n', 0, m.start(2)) + 1
            module = bool(MODULE.search(attrs))
            label = '%s:%d (%s)' % (rel, line, 'module' if module else 'classic')
            ok = parse(label, code, module) and ok
            if module:
                # a module has its own scope: it may shadow a global freely
                continue
            for n in globals_of(code):
                classic.setdefault(n, []).append('%s:%d' % (rel, line))

    for name, where in sorted(classic.items()):
        # Two classic scripts on one page share a top-level scope. The plain
        # .js files are loaded by both pages, so a collision with either is
        # real; two different PAGES colliding with each other is not.
        files = {w.split(':')[0] for w in where}
        if len(where) > 1 and len(files) == len(where) and not (files <= set(PAGES)):
            print('`%s` is declared at top level in %s — both load into the same '
                  'scope, which is a redeclaration error, not a duplicate'
                  % (name, ' and '.join(where)), file=sys.stderr)
            ok = False

    if ok:
        print('ok  %d scripts parse, no top-level collisions'
              % (len(PLAIN) + len(MODULES) + 2))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
