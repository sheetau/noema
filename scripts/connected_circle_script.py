"""Experimental semantic contour, independent of the production writing systems.

No alphabet/codepoint glyphs: ordinary definitions expand into semantic relations;
relations sharing ordered participants coalesce before global port routing.
The deliberately small supported fragment fails closed outside its profile.
"""
from copy import deepcopy
from html import escape
import json
import math

from noema.constructed import parse

VERSION = 'connected-circle-2-draft'
RAILS = (0, 40, 80)
RADII = (8, 20, 32)
STROKE = 1.65

# These are semantic operations on a contour, not glyphs for primitive names.
# A feature's rail is reflected by directed roles and embedded clause context.
FEATURES = {
    'prospect': (0, 20),
    'positive': (40, 8),
    'action': (40, 32),
    'dependence': (80, 20),
    'benefit': (0, 32),
}


def circle(x, y, r):
    return dict(kind='circle', x=x, y=y, r=r)


def line(x1, y1, x2, y2):
    return dict(kind='line', x1=x1, y1=y1, x2=x2, y2=y2)


def _key(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def validate_profile(document, profile):
    declarations = {d['name']: d for d in document['declarations']}
    signatures = set()
    identities = set()
    for symbol, spec in profile['references'].items():
        d = declarations.get(symbol)
        if not d or d['kind'] != 'primitive' or d['parameters'] or d['result'] != 'individual':
            raise ValueError('Reference profile must name an individual constant: ' + symbol)
        marks = spec['marks']
        if not marks or any(m not in ('ring', 'dot') for m in marks):
            raise ValueError('Reference marks must be a nonempty ring/dot sequence')
        signature = tuple(marks)
        if signature in signatures:
            raise ValueError('Reference marks must be distinct within the reading')
        signatures.add(signature)
        if not isinstance(spec.get('identity'), str) or not spec['identity'] or spec['identity'] in identities:
            raise ValueError('Reference identities must be nonempty and distinct')
        identities.add(spec['identity'])
    features_seen = set()
    for symbol, spec in profile['relations'].items():
        d = declarations.get(symbol)
        if not d or d['kind'] != 'primitive' or d['parameters'] != ['individual', 'individual'] or d['result'] != 'truth':
            raise ValueError('Relation profile must name a binary truth predicate: ' + symbol)
        if not spec['features'] or any(f not in FEATURES for f in spec['features']):
            raise ValueError('Unknown semantic feature: ' + symbol)
        signature = tuple(spec['features'])
        if signature in features_seen:
            raise ValueError('Different primitives need distinguishable semantic profiles')
        features_seen.add(signature)
        if len(spec['roles']) != 2 or not spec.get('reading'):
            raise ValueError('A relation needs two ordered roles and an explicit reading')


def expand(node, declarations, environment=None, trail=(), cache=None):
    """Expand only ordinary calls; no substitution underneath unsupported binders."""
    environment = environment or {}
    cache = {} if cache is None else cache
    kind = node['kind']
    if kind == 'variable':
        if node['name'] not in environment:
            raise ValueError('Free or unsupported bound variable')
        return deepcopy(environment[node['name']])
    if kind == 'call':
        args = [expand(a, declarations, environment, trail, cache) for a in node['arguments']]
        d = declarations[node['symbol']]
        key = (node['symbol'], _key(args))
        if key in cache:
            return cache[key]
        if d['kind'] == 'definition':
            if d['name'] in trail:
                raise ValueError('Recursive definition')
            bindings = {p['name']: a for p, a in zip(d['parameters'], args)}
            result = expand(d['body'], declarations, bindings, trail + (d['name'],), cache)
        else:
            result = dict(kind='call', symbol=node['symbol'], arguments=args)
        cache[key] = result
        return result
    if kind in ('and', 'or', 'implies', 'not'):
        return dict(kind=kind, arguments=[expand(a, declarations, environment, trail, cache) for a in node['arguments']])
    raise ValueError('Unsupported expression in contour v2: ' + kind)


def semantic_plan(node, profile, memo=None):
    memo = {} if memo is None else memo
    if id(node) not in memo:
        memo[id(node)] = _semantic_plan(node, profile, memo)
    return memo[id(node)]


def _semantic_plan(node, profile, memo):
    kind = node['kind']
    if kind == 'call':
        spec = profile['relations'].get(node['symbol'])
        if spec is None:
            raise ValueError('No explicit semantic profile for relation: ' + node['symbol'])
        participants = []
        for a in node['arguments']:
            if a['kind'] != 'call' or a['arguments'] or a['symbol'] not in profile['references']:
                raise ValueError('Contour v2 requires profiled individual constants')
            participants.append(deepcopy(profile['references'][a['symbol']]))
        return dict(kind='bundle', participants=participants,
                    relations=[dict(features=spec['features'], roles=spec['roles'], reading=spec['reading'])])
    children = [semantic_plan(a, profile, memo) for a in node['arguments']]
    # Conjunction is associative in this truth-valued fragment. Fuse ONLY equal
    # ordered argument tuples, never across a negation/disjunction/implication.
    if kind == 'and':
        flat = []
        for child in children:
            flat.extend(child['children'] if child['kind'] == 'and' else [child])
        fused = []
        for child in flat:
            if (fused and child['kind'] == fused[-1]['kind'] == 'bundle'
                    and child['participants'] == fused[-1]['participants']):
                # Idempotent conjunction in this truth-valued reading: repeated
                # uses of an identical relation share the same stroke graph.
                existing = {_key(r) for r in fused[-1]['relations']}
                fused[-1]['relations'].extend(r for r in child['relations'] if _key(r) not in existing)
            else:
                fused.append(deepcopy(child))
        if len(fused) == 1:
            return fused[0]
        children = fused
    return dict(kind=kind, children=children)


class Contour:
    """A sentence-wide constraint pass; no reusable word-sized glyph function."""
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.scopes = []
        self.bundles = []

    def node(self, y, radii=(), dot=False, **properties):
        result = dict(y=y, radii=sorted(set(radii)), dot=dot, **properties)
        self.nodes.append(result)
        return len(self.nodes) - 1

    def connect(self, left, right, mode='flow'):
        self.edges.append(dict(left=left, right=right, mode=mode))

    def reference(self, spec, y, role):
        ids = []
        for i, mark in enumerate(spec['marks']):
            radii = [20] if i == 0 else []
            if mark == 'ring':
                radii.append(8)
            ids.append(self.node(y, radii, mark == 'dot', type='reference', role=role,
                                 reference=spec['identity'], mark_index=i))
            if len(ids) > 1:
                self.connect(ids[-2], ids[-1], 'identity')
        return ids[0], ids[-1]

    def build(self, plan, depth=0):
        kind = plan['kind']
        if kind == 'bundle':
            # Keep referents in a stable local roster order. Reversing roles
            # reverses the whole relation's rail trajectory and port choice.
            a, b = plan['participants']
            reverse = tuple(a['marks']) > tuple(b['marks'])
            left, right = (b, a) if reverse else (a, b)
            start, tail = self.reference(left, 80 if reverse else 0,
                                         'target' if reverse else 'source')
            feature_nodes = []
            joints = []
            for ri, relation in enumerate(plan['relations']):
                if ri:
                    # Shared nucleus is the exit of one relation and entry of
                    # another. It is part of BOTH, not a third letter between.
                    extra = next(r for r in (8, 20, 32) if r not in self.nodes[tail]['radii'])
                    self.nodes[tail]['radii'] = sorted(set(self.nodes[tail]['radii'] + [extra]))
                    self.nodes[tail]['shared_relations'] = [ri - 1, ri]
                    joints.append(tail)
                for fi, feature in enumerate(relation['features']):
                    y, radius = FEATURES[feature]
                    if reverse ^ bool(depth % 2):
                        y = 80 - y
                    if feature == 'positive' and fi and 8 not in self.nodes[tail]['radii']:
                        # A modifier becomes a concentric part of its head.
                        # There is no separate advance or connector for it.
                        self.nodes[tail]['radii'] = sorted(set(self.nodes[tail]['radii'] + [8]))
                        self.nodes[tail].setdefault('absorbed_features', []).append(feature)
                        continue
                    # Distinct rails of ONE primitive relation share a vertical
                    # nucleus. Overlapping circles form one compound contour.
                    same_column = fi > 0 and self.nodes[tail]['y'] != y
                    if same_column:
                        column_rails = {self.nodes[tail]['y']}
                        j = tail
                        while self.nodes[j].get('same_column'):
                            j -= 1
                            column_rails.add(self.nodes[j]['y'])
                        same_column = y not in column_rails
                    current = self.node(y, [radius], type='feature', feature=feature,
                                        relation=ri, feature_index=fi, same_column=same_column)
                    self.connect(tail, current, 'shared' if ri and fi == 0 else 'flow')
                    tail = current
                    feature_nodes.append(current)
            first, last = self.reference(right, 0 if reverse else 80,
                                        'source' if reverse else 'target')
            self.connect(tail, first)
            self.bundles.append(dict(start=start, end=last, feature_nodes=feature_nodes,
                                     shared_joints=joints, relations=len(plan['relations']),
                                     participant_occurrences=2, reversed_roles=reverse))
            return start, last
        # Logical scopes have two attached small-circle ports, with inward
        # diagonal arms. Recursive scopes remain visible even with just 3 rails.
        start = self.node(40, [8], type='scope', side='open', operator=kind)
        previous = start
        for i, child in enumerate(plan['children']):
            a, b = self.build(child, depth + 1)
            self.connect(previous, a, kind if i else 'scope')
            previous = b
        end = self.node(40, [8], type='scope', side='close', operator=kind)
        self.connect(previous, end, 'scope')
        self.scopes.append(dict(operator=kind, start=start, end=end, depth=depth))
        # Negation grows across the child's existing entry/exit nuclei: no
        # standalone NOT letter. The enclosing ports still delimit its scope.
        if kind == 'not':
            for index in (start + 1, end - 1):
                self.nodes[index]['negated_boundary'] = True
                self.nodes[index]['radii'] = sorted(set(self.nodes[index]['radii'] + [32]))
        return start, end

    def layout(self):
        # All edges follow the reading spine. Scope, repeated argument and
        # lexical grouping are recorded separately; crossings create no binding.
        incoming = {e['right']: e for e in self.edges}
        outgoing = {e['left']: e for e in self.edges}
        columns = []
        for i, node in enumerate(self.nodes):
            node['radius'] = max(node['radii'], default=3)
            if node.get('same_column'):
                columns[-1].append(i)
            else:
                columns.append([i])
        x = 48
        for ci, column in enumerate(columns):
            radius = max(self.nodes[i]['radius'] for i in column)
            if ci:
                previous = self.nodes[columns[ci - 1][-1]]
                node = self.nodes[column[0]]
                mode = incoming[column[0]]['mode']
                dy = abs(node['y'] - previous['y'])
                # Clearance depends on both adjacent shapes and the topology.
                gap = previous['column_radius'] + radius + 30 + dy
                if mode in ('or', 'implies', 'and'):
                    gap = max(gap, 256)
                x += gap
            for i in column:
                self.nodes[i].update(x=x, column_radius=radius, column_size=len(column))
        shapes = []
        for i, node in enumerate(self.nodes):
            x, y = node['x'], node['y']
            for radius in node['radii']:
                shapes.append(circle(x, y, radius))
            if node['dot']:
                shapes.append(dict(kind='dot', x=x, y=y, r=2.8))
            if node.get('negated_boundary'):
                shapes.append(line(x - 27, y - 27, x + 27, y + 27))
            if node['type'] == 'scope':
                sign = 1 if node['side'] == 'open' else -1
                shapes.extend([line(x, y, x + sign * 16, y - 16),
                               line(x, y, x + sign * 16, y + 16)])
        for edge in self.edges:
            a, b = self.nodes[edge['left']], self.nodes[edge['right']]
            mode = edge['mode']
            ax, ay, bx, by = a['x'], a['y'], b['x'], b['y']
            # A neighboring joint changes the outgoing/ingoing port, not just
            # the distance between two independently drawn symbols.
            prefer_departure = (mode == 'shared' or a['radius'] > b['radius']
                                or (outgoing.get(edge['right'], {}).get('mode') == 'shared'))
            if mode in ('or', 'implies', 'and'):
                # Operators are paths between clauses. OR forks/rejoins;
                # implication has one descending gate; AND shares the midline.
                mid = (ax + bx) / 2
                p, q = (mid - 48, 40), (mid + 48, 40)
                left_path = _route(ax, ay, *p, prefer_departure)
                right_path = _route(*q, bx, by, not prefer_departure)
                points = [p, (mid - 8, 0), (mid + 8, 0), q]
                if mode == 'and':
                    points = [p, q]
                    shapes.append(circle(mid, 40, 8))
                elif mode == 'implies':
                    points = [p, (mid - 48, 0), (mid - 8, 0), (mid + 72, 80), (mid + 72, 40), q]
                shapes += _segments(left_path) + _segments(points) + _segments(right_path)
                if mode == 'or':
                    shapes += _segments([p, (mid - 8, 80), (mid + 8, 80), q])
                edge['path'] = left_path + points + right_path
            else:
                if ax == bx:
                    points = [(ax, ay), (bx, by)]
                elif a['column_size'] > 1 or b['column_size'] > 1:
                    # Enter/leave a fused column horizontally so that a diagonal
                    # cannot clip a neighboring ring off its radial axis.
                    dy = abs(by - ay)
                    guard = a['column_radius'] + 15
                    bend = ax + guard if prefer_departure else bx - b['column_radius'] - 15 - dy
                    points = [(ax, ay), (bend, ay), (bend + dy, by), (bx, by)]
                    points = [p for j, p in enumerate(points) if j == 0 or p != points[j-1]]
                else:
                    points = _route(ax, ay, bx, by, prefer_departure)
                shapes += _segments(points)
                edge['path'] = points
            edge['departure_port'] = _direction(edge['path'][0], edge['path'][1])
            edge['arrival_port'] = _direction(edge['path'][-2], edge['path'][-1])
        # Deduplicate actual geometric strokes, allowing shared structure rather
        # than overprinting one glyph on another.
        unique = {_key(s): s for s in shapes}
        return list(unique.values())


def _direction(a, b):
    return [int(math.copysign(1, b[i] - a[i])) if b[i] != a[i] else 0 for i in (0, 1)]


def _route(ax, ay, bx, by, departure):
    if ay == by:
        return [(ax, ay), (bx, by)]
    delta = abs(by - ay)
    middle = (ax + delta, by) if departure else (bx - delta, ay)
    points = [(ax, ay), middle, (bx, by)]
    return [p for i, p in enumerate(points) if i == 0 or p != points[i - 1]]


def _segments(points):
    return [line(*a, *b) for a, b in zip(points, points[1:]) if a != b]


def geometry_check(shapes):
    rings = [s for s in shapes if s['kind'] in ('circle', 'dot')]
    segments = [s for s in shapes if s['kind'] == 'line']
    for c in rings:
        if c['y'] not in RAILS or (c['kind'] == 'circle' and c['r'] not in RADII):
            raise ValueError('Circle outside the three rails/radii')
    for s in segments:
        dx, dy = s['x2'] - s['x1'], s['y2'] - s['y1']
        if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
            raise ValueError('Non-axial/diagonal line')
        if dy == 0 and s['y1'] not in RAILS:
            raise ValueError('Horizontal line outside rails')
        length2 = dx * dx + dy * dy
        for c in rings:
            vx, vy = c['x'] - s['x1'], c['y'] - s['y1']
            t = max(0, min(1, (vx * dx + vy * dy) / length2))
            distance = math.hypot(vx - t * dx, vy - t * dy)
            if distance <= c['r'] + STROKE / 2 and abs(vx * dy - vy * dx) > 1e-6:
                raise ValueError('Non-radial contact: ' + repr((s, c)))
    return True


def packed_expansion(root):
    """Persist a DAG, so reused definitions do not balloon into a JSON tree."""
    indexes, nodes = {}, []

    def visit(node):
        if id(node) in indexes:
            return indexes[id(node)]
        index = len(nodes)
        indexes[id(node)] = index
        nodes.append(None)
        record = {k: v for k, v in node.items() if k != 'arguments'}
        record['arguments'] = [visit(a) for a in node.get('arguments', [])]
        nodes[index] = record
        return index

    return dict(root=visit(root), nodes=nodes)


def compile_document(text, profile):
    document = parse(text)
    validate_profile(document, profile)
    declarations = {d['name']: d for d in document['declarations']}
    results = []
    for statement in document['statements']:
        if statement['kind'] != 'assert':
            raise ValueError('Contour v2 currently supports assertions only')
        expanded = expand(statement['body'], declarations)
        plan = semantic_plan(expanded, profile)
        contour = Contour()
        contour.build(plan)
        shapes = contour.layout()
        geometry_check(shapes)
        results.append(dict(plan=plan, expanded_dag=packed_expansion(expanded), nodes=contour.nodes,
                            edges=contour.edges, scopes=contour.scopes,
                            bundles=contour.bundles, shapes=shapes,
                            width=contour.nodes[-1]['x'] + 48))
    return dict(version=VERSION, source=document, profile=deepcopy(profile), sentences=results)


def svg(result, index):
    sentence = result['sentences'][index]
    body = []
    for s in sentence['shapes']:
        if s['kind'] in ('circle', 'dot'):
            body.append(f'<circle cx="{s["x"]}" cy="{s["y"]}" r="{s["r"]}" fill="{"#182629" if s["kind"] == "dot" else "none"}"/>')
        else:
            body.append(f'<line x1="{s["x1"]}" y1="{s["y1"]}" x2="{s["x2"]}" y2="{s["y2"]}"/>')
    metadata = escape(json.dumps(dict(version=VERSION, source=result['source'], profile=result['profile'], sentence=index), ensure_ascii=False))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -48 {sentence["width"]} 176">'
            f'<metadata>{metadata}</metadata><g stroke="#182629" stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round">'
            + ''.join(body) + '</g></svg>\n')
