"""Draft structural circle notation: disjoint subtrees and explicit ports.

The decoder consumes only visible circles/segments and public vocabulary.
It recovers a geometric tree before parsing tokens, then checks that the tree
is the one prescribed by the grammar. No renderer or source AST is consulted.
Historical renderers, vocabulary, and semantic judgments are untouched.
"""
from collections import defaultdict
from copy import deepcopy
from functools import wraps
import math

from scripts.visible_syntax import Writer, Reader, END_GLYPH
from scripts.visible_public_page import PublicWriter, PublicReader
from scripts.visible_sharing import SharedReader
from scripts.visible_syntax_vocabulary import Vocabulary, FAMILIES, family_glyph, modifier_glyph
from scripts.visible_word_forms import _marker
from scripts.visible_lexical_script import _glyph, _shape_set, _translate, require
from scripts.visible_syntax_geometry import clean, to_svg, from_svg
from scripts.balanced_circle_script import LARGE, PITCH, line

VERSION = 'structural-circle-draft-1'
STEP = 160.
ROW = 96.
BEVEL = 16.
TOL = 0.00003


def close(a, b):
    return abs(a-b) < TOL


def traced(method):
    @wraps(method)
    def invoke(self, *args, **kwargs):
        span = [self.i, None, []]
        if self.stack:
            self.stack[-1][2].append(span)
        else:
            self.span = span
        self.stack.append(span)
        try:
            return method(self, *args, **kwargs)
        finally:
            span[1] = self.i
            self.stack.pop()
    return invoke


class StructuralReader(PublicReader):
    """Trace grammar boundaries; leaves are still the established public glyphs."""
    def __init__(self, tokens, vocabulary):
        super().__init__(tokens, vocabulary)
        self.stack = []
        self.span = None

    expr = traced(SharedReader.expr)
    statement = traced(Reader.statement)
    document = traced(PublicReader.document)
    type = traced(Reader.type)
    natural = traced(Reader.natural)


def grammar_tree(tokens, vocabulary, mode='document'):
    require(mode in ('document', 'statement'), 'Unknown structural entry point')
    reader = StructuralReader(tokens, vocabulary)
    value = getattr(reader, mode)()
    require(reader.i == len(tokens), 'Extra structural tokens')
    children = [[] for _ in tokens]

    def connect(span):
        start, end, nested = span
        require(start < end, 'Empty structural span')
        cursor = start
        anchor = None
        for child in nested:
            for index in range(cursor, child[0]):
                if anchor is not None:
                    children[anchor].append(index)
                anchor = index
            require(anchor is not None, 'Missing visible operation head')
            children[anchor].append(child[0])
            connect(child)
            cursor = child[1]
        for index in range(cursor, end):
            if anchor is not None:
                children[anchor].append(index)
            anchor = index
    connect(reader.span)
    return value, children


def catalogue(vocabulary):
    glyphs = [END_GLYPH, *[family_glyph(f) for f in FAMILIES],
              *[modifier_glyph(d) for d in (None, *range(8))],
              *[_marker(k, 0.) for k in ('compound', 'proper')],
              *[_glyph(e['form']) for e in vocabulary.document()['entries'].values()]]
    return {_shape_set(g['shapes']): g for g in glyphs}


def render_tree(tokens, children, vocabulary, *, corners='bevel'):
    """One pass for extents, one for placement; no collision-search candidates."""
    require(0 < len(tokens) <= 768, 'Structural glyph budget exceeded')
    require(corners in ('square', 'bevel'), 'Unknown branch corner rule')
    table = catalogue(vocabulary)
    positions, depths, order = {}, {}, []
    pending = [(0, 0)]
    while pending:
        index, depth = pending.pop()
        require(index not in depths and 0 <= index < len(tokens), 'Invalid structural plan')
        depths[index] = depth; order.append(index)
        pending.extend((c,depth+1) for c in reversed(children[index]))
    require(len(order) == len(tokens), 'Disconnected structural plan')
    leaves = [i for i in order if not children[i]]
    leaf_y = {i:j*ROW for j,i in enumerate(leaves)}
    leaf = len(leaves)
    for index in reversed(order):
        ys = [positions[c][1] for c in children[index]]
        positions[index] = (depths[index]*STEP, (ys[0]+ys[-1])/2 if ys else leaf_y[index])
    shapes, ports = [], {}
    for i, token in enumerate(tokens):
        g = table[token]
        x, y = positions[i]
        shapes.extend(_translate(g['shapes'], x-g['x'], y-g['y']))
        ports[i] = (x+g['left']-g['x'], x+g['right']-g['x'], y)
    for i, branch in enumerate(children):
        if not branch:
            continue
        _, right, y = ports[i]
        spine = positions[i][0]+STEP/2
        shapes.append(line((right, y), (spine, y)))
        joints = []
        for c in branch:
            left, _, cy = ports[c]
            chamfer = corners=='bevel' and len(branch)>1 and c in (branch[0],branch[-1])
            jy = cy-math.copysign(BEVEL, cy-y) if chamfer else cy
            joints.append(jy)
            if chamfer:
                shapes.append(line((spine, jy), (spine+BEVEL, cy)))
            shapes.append(line((spine+(BEVEL if chamfer else 0), cy), (left, cy)))
        if not close(min(joints), max(joints)):
            shapes.append(line((spine, min(joints)), (spine, max(joints))))
    return dict(shapes=clean(shapes), glyphs=len(tokens), leaves=leaf,
                forks=sum(len(cs)>1 for cs in children), version=VERSION)


def compile_document(document, vocabulary=None, *, sharing=False, **layout):
    v = vocabulary or Vocabulary()
    writer = PublicWriter(v, automatic=sharing)
    canonical = writer.document(document)
    tokens = [_shape_set(g['shapes']) for g in writer.glyphs]
    decoded, children = grammar_tree(tokens, v)
    require(decoded == canonical, 'Existing grammar conversion differs')
    return render_tree(tokens, children, v, **layout)


def compile_statement(statement, vocabulary=None, **layout):
    v = vocabulary or Vocabulary()
    writer = Writer(v)
    writer.statement(statement)
    tokens = [_shape_set(g['shapes']) for g in writer.glyphs]
    _, children = grammar_tree(tokens, v, 'statement')
    return render_tree(tokens, children, v, **layout)


def segment(s):
    x1, y1, x2, y2 = (s[k] for k in ('x1', 'y1', 'x2', 'y2'))
    require(math.hypot(x2-x1, y2-y1) > TOL, 'Zero length ink')
    if close(y1, y2):
        key, ends = ('h', round(y1, 5)), (x1, x2)
    elif close(x1, x2):
        key, ends = ('v', round(x1, 5)), (y1, y2)
    else:
        require(close(abs(x2-x1), abs(y2-y1)), 'Unknown stroke direction')
        slope = 1 if (x2-x1)*(y2-y1)>0 else -1
        key, ends = (slope, round(y1-slope*x1, 5)), (x1, x2)
    return key, tuple(sorted(round(x, 5) for x in ends))


class Ink:
    """Line unions indexed by direction/intercept; segmentation is immaterial."""
    def __init__(self, shapes):
        self.rows = defaultdict(list)
        for s in shapes:
            if s['kind'] == 'line':
                key, extent = segment(s)
                self.rows[key].append(extent)
        for key, intervals in self.rows.items():
            merged = []
            for a, b in sorted(intervals):
                if merged and a <= merged[-1][1]+TOL:
                    merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
                else:
                    merged.append((a, b))
            self.rows[key] = merged

    def contains(self, s):
        key, (a, b) = segment(s)
        return any(lo-TOL <= a and b <= hi+TOL for lo, hi in self.rows.get(key, ()))

    def overlaps(self, s):
        key, (a, b) = segment(s)
        return any(min(hi,b)-max(lo,a)>TOL for lo,hi in self.rows.get(key, ()))

    def remove(self, s):
        key, (a, b) = segment(s)
        intervals = self.rows.get(key, ())
        for j, (lo, hi) in enumerate(intervals):
            if lo-TOL <= a and b <= hi+TOL:
                rest = ([(lo, a)] if a-lo>TOL else []) + ([(b, hi)] if hi-b>TOL else [])
                self.rows[key][j:j+1] = rest
                return
        raise ValueError('Missing glyph stroke')

    def shapes(self):
        for (direction, intercept), intervals in self.rows.items():
            for a, b in intervals:
                if direction=='h': yield line((a,intercept),(b,intercept))
                elif direction=='v': yield line((intercept,a),(intercept,b))
                else: yield line((a,direction*a+intercept),(b,direction*b+intercept))


def circle_key(rings, x, y):
    return tuple(sorted((round(c['x']-x, 5), round(c['y']-y, 5), round(c['r'], 5)) for c in rings))


def read_geometry(shapes, vocabulary):
    visible = clean(shapes)
    rings = [s for s in visible if s['kind']=='circle']
    require(rings, 'Missing circles')
    radius = max(c['r'] for c in rings)
    anchor = min((c for c in rings if close(c['r'], radius)), key=lambda c:c['x'])
    scale = LARGE/radius
    require(math.isfinite(scale) and scale>0, 'Unsupported drawing scale')
    visible = clean(_translate(visible, -anchor['x']*scale, -anchor['y']*scale, scale))
    groups = defaultdict(list)
    for c in visible:
        if c['kind']=='circle':
            depth = round(c['x']/STEP)
            require(depth >= 0, 'Ink before the structural root')
            groups[(depth, round(c['y'], 5))].append(c)
    require(0 < len(groups) <= 768, 'Structural glyph budget exceeded')
    table = defaultdict(list)
    for signature, g in catalogue(vocabulary).items():
        local = _translate(g['shapes'], -g['x'], -g['y'])
        table[circle_key([s for s in local if s['kind']=='circle'], 0, 0)].append((signature, g))
    ink = Ink(visible)
    glyphs = {}
    for (depth, y), circles in sorted(groups.items()):
        x = depth*STEP
        candidates = []
        for signature, g in table.get(circle_key(circles, x, y), ()):
            strokes = [s for s in _translate(g['shapes'], x-g['x'], y-g['y']) if s['kind']=='line']
            if all(ink.contains(s) for s in strokes):
                candidates.append((len(strokes), signature, g, strokes))
        require(candidates, 'Unknown circle glyph')
        maximum = max(c[0] for c in candidates)
        candidates = [c for c in candidates if c[0]==maximum]
        require(len(candidates)==1, 'Ambiguous glyph strokes')
        _, signature, g, strokes = candidates[0]
        for s in strokes:
            ink.remove(s)
        glyphs[(depth, y)] = (signature, x+g['left']-g['x'], x+g['right']-g['x'])

    # A public 45-degree corner rewrite, checked on actual remaining ink.
    # It replaces a bevel with its two legs; the grammar is not yet known.
    corners, corner_sites = [], []
    for (direction, intercept), intervals in list(ink.rows.items()):
        if direction in (-1,1):
            for a,b in list(intervals):
                depth = round((a-STEP/2)/STEP)
                require(depth>=0 and close(a,depth*STEP+STEP/2) and close(b-a,BEVEL),
                        'Diagonal outside a permitted branch corner')
                y1,y2=direction*a+intercept,direction*b+intercept
                horizontal=line((a,y2),(b,y2)); vertical=line((a,y1),(a,y2))
                require(not ink.overlaps(horizontal) and not ink.overlaps(vertical), 'Duplicate corner ink')
                ink.remove(line((a,y1),(b,y2)))
                corners.extend((horizontal,vertical))
                corner_sites.append((depth,y1,y2))
    ink = Ink([*ink.shapes(),*corners])

    # Ports are located from the recognized glyph, never from SVG IDs.
    left_ports = {(round(left, 5), y): key for key, (_, left, _) in glyphs.items() for y in (key[1],)}
    right_ports = {(round(right, 5), y): key for key, (_, _, right) in glyphs.items() for y in (key[1],)}
    verticals = defaultdict(list)
    horizontal = []
    for (direction, intercept), intervals in ink.rows.items():
        for a, b in intervals:
            if direction == 'v':
                depth = round((intercept-STEP/2)/STEP)
                require(depth >= 0 and close(intercept, depth*STEP+STEP/2), 'Vertical ink outside a branch corridor')
                verticals[depth].append((a, b))
            else:
                require(direction=='h', 'Unexpected external diagonal')
                horizontal.append((intercept, a, b))
    components = defaultdict(lambda: dict(parents=[], children=[]))
    used_verticals = set()
    for y, a, b in horizontal:
        # A unary edge can be one uninterrupted horizontal stroke.
        depth = math.floor((a+TOL)/STEP)
        spine = depth*STEP+STEP/2
        require(a < spine+TOL and b > spine-TOL, 'Horizontal ink misses its branch corridor')
        matches = [(lo, hi) for lo, hi in verticals[depth] if lo-TOL <= y <= hi+TOL]
        require(len(matches)<=1, 'Overlapping branch corridors')
        extent = matches[0] if matches else (y, y)
        key = (depth, *extent)
        if matches:
            used_verticals.add(key)
        group = components[key]
        if a < spine-TOL:
            parent = right_ports.get((round(a, 5), y))
            require(parent is not None and parent[0]==depth, 'Disconnected parent port')
            group['parents'].append(parent)
        if b > spine+TOL:
            child = left_ports.get((round(b, 5), y))
            require(child is not None and child[0]==depth+1, 'Disconnected child port')
            group['children'].append(child)
    require(len(used_verticals)==sum(map(len, verticals.values())), 'Unused vertical ink')
    for depth,y1,y2 in corner_sites:
        matches=[(lo,hi) for d,lo,hi in components if d==depth and (close(lo,y2) or close(hi,y2)) and lo-TOL<=y1<=hi+TOL]
        require(len(matches)==1, 'Bevel must terminate an outermost branch')
    children = {key: [] for key in glyphs}
    incoming = set()
    for (depth, lo, hi), component in components.items():
        parents, branch = component['parents'], sorted(component['children'], key=lambda k:k[1])
        require(len(parents)==1 and branch, 'A branch needs exactly one parent and children')
        require(close(lo, branch[0][1]) and close(hi, branch[-1][1]), 'Dangling branch ink')
        parent = parents[0]
        require(not children[parent], 'Repeated parent branch')
        require(all(c not in incoming for c in branch), 'A glyph has multiple parents')
        require(len(set(branch))==len(branch), 'Repeated child')
        incoming.update(branch)
        children[parent] = branch
    roots = set(glyphs)-incoming
    require(len(roots)==1, 'Disconnected or ambiguous structural root')
    root = roots.pop()
    require(root[0]==0, 'Root must be in the first column')
    order, intervals, seen = [], {}, set()
    pending = [root]
    while pending:
        key = pending.pop()
        require(key not in seen, 'Repeated structural glyph')
        seen.add(key); order.append(key)
        pending.extend(reversed(children[key]))
    require(len(order)==len(glyphs), 'Unreachable structural ink')
    for key in reversed(order):
        ranges = [intervals[c] for c in children[key]]
        require(all(b[0]-a[1] >= ROW-TOL for a,b in zip(ranges,ranges[1:])), 'Overlapping sibling regions')
        low, high = (ranges[0][0], ranges[-1][1]) if ranges else (key[1], key[1])
        require(low-TOL <= key[1] <= high+TOL, 'Parent outside its subtree region')
        intervals[key] = (low, high)
    indices = {key:i for i,key in enumerate(order)}
    return [glyphs[key][0] for key in order], [[indices[c] for c in children[key]] for key in order]


def decode(shapes, vocabulary=None, *, mode='document'):
    v = vocabulary or Vocabulary()
    tokens, geometric_tree = read_geometry(shapes, v)
    value, grammatical_tree = grammar_tree(tokens, v, mode)
    require(geometric_tree == grammatical_tree, 'Visible branches disagree with grammatical scopes')
    return value
