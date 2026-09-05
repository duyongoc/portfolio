#!/usr/bin/env python3
"""Which links a build carries, out of build_links.txt and into the data file.

The links were the last thing in the data file that anyone edited by hand, and
they are the thing edited most often: a build gets a Play Store page, a WebGL
build moves, a video is re-cut. Doing that in portfolio-data.js meant opening
33 entries of JSON to change one URL, and getting the `tags` array — which is
nothing but the list of kinds, deduplicated — to agree with it afterwards. It
did agree, on all 33, but only because nobody had got it wrong yet.

So build_links.txt is the hand-written record and this generates the two fields
from it. Same arrangement as build_layout.txt -> wallsheet.py, and for the same
reason: Pages runs no Python, so the output is committed, and --check in CI is
what stops "edited the file and forgot to bake" from being a silent no-op.

    python3 tools/links.py            write the links into portfolio-data.js
    python3 tools/links.py --check    validate and diff, write nothing
    python3 tools/links.py --export   rebuild build_links.txt from the data

--export is how build_links.txt was first made, and it is kept because it is the
proof the two directions agree: export, bake, and `git diff` is empty. It
overwrites the file, so it is not part of the day-to-day loop.

Only portfolio-data.js is written. Its ?v= is wallsheet.py's business — that
file hashes it into the <script src> of both pages — so a run that changes the
data says to re-run wallsheet, and `wallsheet.py --check` fails until it has
been.
"""
import difflib, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portfolio import ROOT, DATA, games, slug

LINKS = os.path.join(ROOT, 'build_links.txt')

# The kinds a link can be, in the order the file lists them. Closed on purpose:
# each one is a case in playOf, actionOf, shortOf and availOf in
# portfolio-shared.js, and in gameCard() in room-3d.html — a fifth kind is a
# code change in those five places, not a data change, and a typo that silently
# became a new kind would render a button nobody wrote the label for.
#
# The order is also the file's slot order, which is why it reads
# playable-first: it is the order the covers' own links are worth trying in.
KINDS = ['WebGL', 'Android', 'Youtube', 'Source']

# A slot with nothing in it. Written rather than left blank so that an empty
# slot and a line someone was halfway through typing do not look the same.
EMPTY = '-'

HEADER = '''\
# Which links each build carries. Edit this file, then:
#
#     python3 tools/links.py       (then tools/wallsheet.py, for the ?v=)
#
# One block per build, headed by its id — the same ids build_layout.txt uses.
# Under it, one indented line per slot:
#
#     WebGL    https://...            the link
#     WebGL    -                      no link of that kind
#     Youtube  https://... | Watch 2  an explicit label for the button
#
# Every block carries all four slots, in this order, so a glance down the file
# says which build is still missing a store page. A label defaults to the kind
# and is only worth writing when a build has two links of the same kind — the
# second Youtube on the netcode builds is the whole reason labels exist.
#
# Extra lines of a kind are allowed and are kept in the order written; the four
# slots are the template, not a limit. The kinds themselves are not open: they
# are %s, and each one is a case in the button
# helpers in demos/portfolio-shared.js.
#
# A build with every slot empty is allowed — its card renders with no button
# row. A build with no block at all is a build nobody has got to yet: the tool
# appends an empty one for it rather than guessing.
#
# The order of the links here is the order the buttons appear in. The one that
# gets the primary treatment is not: that is WebGL, else Android, else the
# first link there is (playOf, in demos/portfolio-shared.js).
''' % (', '.join(KINDS[:-1]) + ' and ' + KINDS[-1])


def read(path=LINKS, ids=None):
    """build_links.txt -> {id: [link, ...]}, in file order, links as written.

    Every error in the file is collected and reported together. Finding out
    about the second typo only after fixing the first is the thing that makes
    a hand-edited data file tiring, and it is the whole reason this format is
    parsed rather than hand-maintained as JSON."""
    if not os.path.exists(path):
        raise SystemExit('%s is missing — it is the hand-written record of every '
                         "build's links. `python3 tools/links.py --export` "
                         'rebuilds it from portfolio-data.js' % path)
    out, errs, cur, cur_id = {}, [], None, None
    for n, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.split('#')[0].rstrip()
        if not line.strip():
            continue
        if not line[0].isspace():                       # a heading: a build id
            bid = line.strip()
            if ids is not None and bid not in ids:
                near = difflib.get_close_matches(bid, ids, 1, .6)
                errs.append('%s:%d: no build with id %r%s — the ids are the '
                            'headings in this file, and portfolio-data.js is '
                            'what they come from'
                            % (path, n, bid, ' (did you mean %r?)' % near[0] if near else ''))
                cur, cur_id = [], None                  # keep parsing the block
                continue
            if bid in out:
                errs.append('%s:%d: %r has a second block — one per build, and '
                            'extra links go in the first one' % (path, n, bid))
            cur = out.setdefault(bid, [])
            cur_id = bid
            continue
        if cur is None:
            errs.append('%s:%d: %r is under no build — an indented line is a '
                        'link slot and needs an id above it'
                        % (path, n, line.strip()))
            continue
        kind, _, rest = line.strip().partition(' ')
        if kind not in KINDS:
            errs.append('%s:%d: %r is not a link kind — they are %s'
                        % (path, n, kind, ', '.join(KINDS)))
            continue
        url, _, label = (r.strip() for r in rest.partition('|'))
        if url in ('', EMPTY):                          # an empty slot
            if label:
                errs.append('%s:%d: %s has a label but no url — an empty slot '
                            'carries nothing' % (path, n, kind))
            continue
        if not url.startswith(('http://', 'https://')):
            errs.append('%s:%d: %s url %r is not http(s) — every one of these '
                        'opens in a new tab' % (path, n, kind, url))
            continue
        cur.append({'kind': kind, 'url': url, 'label': label or kind})
    if errs:
        raise SystemExit('\n'.join(errs))
    if cur_id is None and not out:
        raise SystemExit('%s parsed to nothing — it needs a build id at the '
                         'left margin and its slots indented under it' % path)
    return out


def tags(links):
    """The `tags` array: the kinds, deduplicated, in the order they appear.

    Derived rather than written because it always was derived — measured across
    all 33 entries it was exactly this, including the two builds with a second
    Youtube where the duplicate is dropped. A field that can only be one thing
    is not data."""
    seen, out = set(), []
    for l in links:
        if l['kind'] not in seen:
            seen.add(l['kind'])
            out.append(l['kind'])
    return out


def apply(by_id, path=DATA):
    """portfolio-data.js with links and tags replaced, as text.

    Returned rather than written so --check can ask what a run would produce
    without producing it — the same reason wallsheet.py's generate() does.

    The array is re-emitted with json.dumps(indent=1), which reproduces the
    committed file byte for byte: every other field goes back out exactly as it
    came in, and the diff of a run that changes nothing is empty."""
    src = open(path, encoding='utf-8').read()
    i, j = src.index('['), src.rindex(']') + 1
    data = json.loads(src[i:j])
    for g in data:
        links = by_id.get(slug(g['title']), [])
        # A label that is just the kind is what every reader falls back to
        # anyway (l.label||l.kind), so writing it out is 33 lines of noise.
        g['links'] = [{k: v for k, v in l.items() if k != 'label' or v != l['kind']}
                      for l in links]
        g['tags'] = tags(links)
    return src[:i] + json.dumps(data, indent=1, ensure_ascii=False) + src[j:]


def export(path=LINKS):
    """build_links.txt as it would be written from portfolio-data.js right now.

    Not part of the loop — it is how the file was first made, and it is the
    check that the two directions agree."""
    out = [HEADER]
    for g in games():
        out.append('\n%s\n' % slug(g['title']))
        by_kind = {}
        for l in g['links']:
            by_kind.setdefault(l['kind'], []).append(l)
        for kind in KINDS:
            got = by_kind.get(kind) or [None]
            for l in got:
                if l is None:
                    out.append('  %-8s %s\n' % (kind, EMPTY))
                else:
                    label = l.get('label') or kind
                    out.append('  %-8s %s%s\n'
                               % (kind, l['url'], '' if label == kind else ' | ' + label))
    return ''.join(out)


def stub(missing):
    """An empty block per build that has none, to append.

    A build added to portfolio-data.js and not to this file would otherwise
    render with no buttons and no sign of why. Appending is additive — nothing
    written above it moves — and it puts the four slots in front of whoever
    added the build, which is when they know the URLs."""
    return ''.join('\n%s\n' % bid + ''.join('  %-8s %s\n' % (k, EMPTY) for k in KINDS)
                   for bid in missing)


def main(argv):
    check = '--check' in argv
    if '--export' in argv:
        text = export()
        open(LINKS, 'w', encoding='utf-8').write(text)
        print('%-22s %d builds' % ('build_links.txt', text.count('\n\n')))
        return 0

    ids = [slug(g['title']) for g in games()]
    by_id = read(ids=ids)
    missing = [b for b in ids if b not in by_id]
    if missing and not check:
        open(LINKS, 'a', encoding='utf-8').write(stub(missing))
        print('%-22s %d build%s appended with empty slots: %s'
              % ('build_links.txt', len(missing),
                 '' if len(missing) == 1 else 's', ', '.join(missing)))

    text = apply(by_id)
    same = text == open(DATA, encoding='utf-8').read()
    empty = [b for b in ids if not by_id.get(b)]

    if check:
        if missing:
            raise SystemExit('build_links.txt has no block for %s — run '
                             '`python3 tools/links.py`, which appends an empty '
                             'one' % ', '.join(missing))
        if not same:
            raise SystemExit('demos/portfolio-data.js does not match '
                             'build_links.txt — run `python3 tools/links.py`, '
                             'then wallsheet.py, and commit both')
        print('ok  %d builds, %d links%s'
              % (len(ids), sum(len(v) for v in by_id.values()),
                 ', %d with none' % len(empty) if empty else ''))
        return 0

    if same:
        print('%-22s unchanged' % 'demos/portfolio-data.js')
    else:
        open(DATA, 'w', encoding='utf-8').write(text)
        print('%-22s %d builds, %d links — now run tools/wallsheet.py, it '
              'stamps the ?v=' % ('demos/portfolio-data.js', len(ids),
                                  sum(len(v) for v in by_id.values())))
    if empty:
        print('%-22s no links, so no button row: %s'
              % ('warning', ', '.join(empty)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
