"""Compositional lexical spellings in the frozen circle geometry.

The decoder reads visible primitives, never a spelling sidecar or a registry
of complete names. Definitions use the existing typed Noema document schema.
"""
from copy import deepcopy
from dataclasses import dataclass
import math

from noema.constructed_discourse import normalize_document
from scripts.visible_lexical_script import (
    Lexicon, require, _glyph, _shape_set, _translate, _clean_shapes,
    _merge_segments, _connected_words, _take_marks, to_svg, from_svg,
)
from scripts.balanced_circle_script import (
    SMALL, MEDIUM, LARGE, PITCH, EPS, MIN_RUN, circle, line, near,
    nucleus, route, geometry_check, _on_segment,
)

MAX_PARTS = 24


@dataclass(frozen=True)
class Word:
    kind: str
    parts: tuple[str, ...]


def canonical(word, lexicon=None):
    lexicon = lexicon or Lexicon()
    require(isinstance(word, Word) and word.kind in ('root', 'compound', 'proper')
            and type(word.parts) is tuple, 'Invalid word form')
    minimum = 2 if word.kind == 'compound' else 1
    require(minimum <= len(word.parts) <= MAX_PARTS, 'Word component count exceeds this fragment')
    require(word.kind != 'root' or len(word.parts) == 1, 'Root words have one component')
    return Word(word.kind, tuple(lexicon.resolve(part)[0] for part in word.parts))


def symbol(word, lexicon=None):
    """Injective textual spelling of the visible name, without numeric IDs."""
    word = canonical(word, lexicon)
    prefix = {'root': 'wr', 'compound': 'wc', 'proper': 'wp'}[word.kind]
    return prefix + ''.join(part.replace('z', 'zz') + 'zq' for part in word.parts)


def read_symbol(value, lexicon=None):
    require(isinstance(value, str) and value[:2] in ('wr', 'wc', 'wp'), 'Unknown word prefix')
    parts, letters, i = [], [], 2
    while i < len(value):
        ch = value[i]
        if ch != 'z':
            letters.append(ch)
            i += 1
        else:
            require(i+1 < len(value) and value[i+1] in ('z', 'q'), 'Invalid word escape')
            if value[i+1] == 'z':
                letters.append('z')
            else:
                require(letters, 'Empty word component')
                parts.append(''.join(letters))
                letters = []
            i += 2
    require(not letters and parts, 'Unterminated word component')
    word = canonical(Word({'wr':'root', 'wc':'compound', 'wp':'proper'}[value[:2]], tuple(parts)), lexicon)
    require(symbol(word, lexicon) == value, 'Noncanonical word symbol')
    return word


def _marker(kind, x=50.):
    require(kind in ('compound', 'proper'), 'A new-name marker is required')
    return nucleus(x, PITCH, LARGE, 'nested', 6 if kind == 'compound' else 4)


def _lines(paths):
    return [line(a, b) for path in paths for a, b in zip(path, path[1:])]


def _add(glyph, previous, shapes, paths):
    joined = route(previous['exit'], glyph['entry'],
                   [s for s in shapes+glyph['shapes'] if s['kind'] == 'circle'],
                   obstacles=shapes+glyph['shapes'])
    require(joined is not None, 'No legal lexical connection')
    path, lines = joined
    candidate = shapes + glyph['shapes'] + lines
    candidate_paths = paths + glyph['paths'] + [path]
    geometry_check(candidate, candidate_paths)
    return candidate, candidate_paths


def compile_word(word, lexicon=None, *, branch=True, first_rail=0, gap=80.):
    lexicon = lexicon or Lexicon()
    word = canonical(word, lexicon)
    require(word.kind != 'root', 'Bare roots use the lexical context, not this name envelope')
    require(type(branch) is bool and type(first_rail) is int and first_rail in (0, 2), 'Invalid layout')
    require(type(gap) in (int, float) and math.isfinite(gap) and gap >= 48., 'Invalid lexical spacing')
    previous = _marker(word.kind)
    shapes, paths = previous['shapes'][:], previous['paths'][:]
    forms = [lexicon.resolve(part)[1]['form'] for part in word.parts]
    i, moment = 0, 0.
    while i < len(forms):
        # Two medium components become an asymmetric branch. Their x order,
        # not their upper/lower rail, preserves spelling order.
        can_branch = (branch and i+1 < len(forms) and near(previous['exit']['y'], PITCH)
                      and all(f['size'] == 'medium' for f in forms[i:i+2]))
        if can_branch:
            fork_x = previous['right'] + MIN_RUN + 24.
            fork = (fork_x, PITCH)
            a = _glyph(forms[i], fork_x+PITCH+MEDIUM+MIN_RUN+gap, first_rail*PITCH)
            b = _glyph(forms[i+1], a['right']+2*gap+MEDIUM, (2-first_rail)*PITCH)
            branches = [[(previous['exit']['x']+previous['exit']['radius'], PITCH), fork],
                        [fork, (fork_x+PITCH, a['y']), (a['entry']['x']-a['entry']['radius'], a['y'])],
                        [fork, (fork_x+PITCH, b['y']), (b['entry']['x']-b['entry']['radius'], b['y'])]]
            trial_shapes = shapes+a['shapes']+b['shapes']+_lines(branches)
            trial_paths = paths+a['paths']+b['paths']+branches
            try:
                geometry_check(trial_shapes, trial_paths)
            except ValueError:
                can_branch = False
            else:
                shapes, paths, previous = trial_shapes, trial_paths, b
                moment += sum(s['r']**2*(s['y']-PITCH) for s in a['shapes']+b['shapes'] if s['kind']=='circle')
                i += 2
                continue
        preferred = (0 if moment > 0 else 2 if moment < 0 else first_rail)
        rails = [1] if forms[i]['size']=='large' else [preferred, 2-preferred, 1]
        found = None
        for extra in (0., 64., 128.):
            for rail in rails:
                glyph = _glyph(forms[i], previous['right']+gap+extra+LARGE, rail*PITCH)
                try:
                    candidate = _add(glyph, previous, shapes, paths)
                except ValueError:
                    continue
                found = glyph, candidate
                break
            if found:
                break
        require(found is not None, 'No legal layout for this lexical component')
        previous, (shapes, paths) = found
        moment += sum(s['r']**2*(s['y']-PITCH) for s in previous['shapes'] if s['kind']=='circle')
        i += 1
    terminal = nucleus(previous['right']+gap+SMALL, previous['y'], SMALL, None, mode='none')
    shapes, paths = _add(terminal, previous, shapes, paths)
    require(len(shapes) <= 256, 'Visible primitive budget exceeded')
    return dict(shapes=shapes, width=terminal['right']+12.)


def _lexical_tree(segments, groups):
    """Contract lexical circles, then require one connected external tree."""
    require(segments, 'Missing lexical connections')
    points = []

    def point_id(p):
        for i, q in enumerate(points):
            if math.dist(p, q) < EPS:
                return i
        points.append(p)
        return len(points)-1

    for s in segments:
        point_id((s['x1'], s['y1']))
        point_id((s['x2'], s['y2']))
    vertices = {}
    for i, p in enumerate(points):
        ports = [j for j, rings in enumerate(groups) if any(
            near(math.dist(p, (c['x'], c['y'])), c['r']) for c in rings)]
        require(len(ports) <= 1, 'Ambiguous lexical connection')
        vertices[i] = ('word', ports[0]) if ports else ('joint', i)
    adjacency = {('word', i):set() for i in range(len(groups))}
    edges = set()
    for s in segments:
        a, b = (s['x1'], s['y1']), (s['x2'], s['y2'])
        for rings in groups:
            for c in rings:
                dx, dy = b[0]-a[0], b[1]-a[1]
                t = max(0., min(1., ((c['x']-a[0])*dx+(c['y']-a[1])*dy)/(dx*dx+dy*dy)))
                require(math.dist((c['x'],c['y']), (a[0]+t*dx,a[1]+t*dy)) >= c['r']-EPS,
                        'External line enters a lexical circle')
        cuts = sorted((i for i,p in enumerate(points) if _on_segment(p, s)),
                      key=lambda i: math.dist(a, points[i]))
        for p, q in zip(cuts, cuts[1:]):
            u, v = vertices[p], vertices[q]
            require(u != v, 'Loop at a lexical word')
            edge = tuple(sorted((u, v)))
            require(edge not in edges, 'Repeated external edge')
            edges.add(edge)
            adjacency.setdefault(u,set()).add(v)
            adjacency.setdefault(v,set()).add(u)
    require(all(len(neighbors) >= (2 if v[0]=='joint' else 1)
                for v,neighbors in adjacency.items()), 'Dangling or disconnected lexical ink')
    seen, pending = set(), [('word',0)]
    while pending:
        vertex = pending.pop()
        if vertex not in seen:
            seen.add(vertex)
            pending.extend(adjacency[vertex]-seen)
    require(len(seen)==len(adjacency) and len(edges)==len(adjacency)-1,
            'Lexical connections must form one tree')


def decode_word(shapes, lexicon=None):
    lexicon = lexicon or Lexicon()
    visible = _clean_shapes(shapes)
    circles = [s for s in visible if s['kind']=='circle']
    require(circles, 'No circles')
    anchor = max(circles, key=lambda c:c['r'])
    scale = LARGE/anchor['r']
    visible = _translate(visible, 50.-anchor['x']*scale, PITCH-anchor['y']*scale, scale)
    circles = [s for s in visible if s['kind']=='circle']
    segments = _merge_segments([s for s in visible if s['kind']=='line'])
    geometry_check(circles+segments, [[(s['x1'],s['y1']),(s['x2'],s['y2'])] for s in segments])
    groups = _connected_words(circles)
    tokens, remaining = [], segments
    markers = {kind:_shape_set(_translate(_marker(kind)['shapes'], -50., 0.))
               for kind in ('compound','proper')}
    for rings in groups:
        main = max(rings, key=lambda c:c['r'])
        marks, remaining = _take_marks(main, remaining)
        local = _translate(rings+marks, -main['x'], PITCH-main['y'])
        signature = _shape_set(local)
        marker = next((k for k,v in markers.items() if v==signature), None)
        if marker:
            token = ('start', marker)
        elif len(rings)==1 and near(main['r'], SMALL) and not marks:
            token = ('end', None)
        else:
            token = ('part', lexicon.match(local)[0])
        tokens.append((main['x'], token))
    _lexical_tree(remaining, groups)
    tokens.sort()
    require(all(b[0]-a[0]>EPS for a,b in zip(tokens,tokens[1:])), 'Ambiguous lexical order')
    ordered = [token for x,token in tokens]
    require(ordered[0][0]=='start' and ordered[-1][0]=='end'
            and all(k=='part' for k,v in ordered[1:-1]), 'Missing or misplaced word boundary')
    return canonical(Word(ordered[0][1], tuple(v for k,v in ordered[1:-1])), lexicon)


class NamingDocument:
    """Typed native declarations keyed by their publicly readable spelling."""

    def __init__(self, lexicon=None):
        self.lexicon = lexicon or Lexicon()
        self._document = dict(schema_version='0.16', lexicon_version='0.16', declarations=[], statements=[])
        for name, entry in sorted(self.lexicon.document()['entries'].items()):
            self._document['declarations'].append(dict(kind='primitive',
                name=symbol(Word('root',(name,)), self.lexicon),
                parameters=entry['parameters'], result=entry['result']))
        self._document = normalize_document(self._document)

    def define(self, word, parameters, result, body):
        word = canonical(word, self.lexicon)
        require(word.kind != 'root', 'A learned root cannot be redefined')
        if word.kind == 'proper':
            require(parameters == [] and result == 'individual', 'Proper names designate individuals')
        candidate = deepcopy(self._document)
        candidate['declarations'].append(dict(kind='definition', name=symbol(word,self.lexicon),
            parameters=deepcopy(parameters), result=result, body=deepcopy(body)))
        self._document = normalize_document(candidate)

    def append(self, statement):
        candidate = deepcopy(self._document)
        candidate['statements'].append(deepcopy(statement))
        self._document = normalize_document(candidate)

    def document(self):
        return deepcopy(self._document)


def call(word, arguments=(), lexicon=None):
    return dict(kind='call', symbol=symbol(word,lexicon), arguments=deepcopy(list(arguments)))
