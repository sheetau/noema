"""Public lexical shapes and geometry-only decoding of unary assertions.

This deliberately small fragment is not a decoder for the historical page
renderer. All inputs to decode() are visible circles and straight segments.
"""
from copy import deepcopy
from importlib.resources import files
import json
import math
import re
import xml.etree.ElementTree as ET

from scripts.balanced_circle_script import (
    SMALL, MEDIUM, LARGE, PITCH, EPS, MIN_GAP, MIN_RUN, STROKE,
    circle, line, near, nucleus, route, geometry_check, _on_segment,
)

SCHEMA = 'noema-visible-lexicon-1'
DIRECTIONS = ('east', 'southeast', 'south', 'southwest',
              'west', 'northwest', 'north', 'northeast')
SIZES = {'medium': MEDIUM, 'large': LARGE}
COMPANIONS = ('none', 'small-concentric', 'small-east-rim')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _glyph(form, x=0., y=PITCH):
    radius = SIZES[form['size']]
    ray = DIRECTIONS.index(form['ray']) if form['ray'] is not None else None
    glyph = nucleus(x, y, radius, None, ray,
                    mode='radius' if ray is not None else 'none')
    if form['companion'] == 'small-concentric':
        glyph['shapes'].append(circle(x, y, SMALL))
    elif form['companion'] == 'small-east-rim':
        glyph['shapes'].append(circle(x + radius, y, SMALL))
        glyph['exit'] = dict(x=x + radius, y=y, radius=SMALL)
        glyph['right'] += SMALL
    return glyph


def _shape_key(shape):
    if shape['kind'] == 'line':
        shape = line(*sorted(((shape['x1'], shape['y1']), (shape['x2'], shape['y2']))))
    return tuple((key, round(value, 7) if key != 'kind' else value)
                 for key, value in sorted(shape.items()))


def _shape_set(shapes):
    return tuple(sorted(_shape_key(s) for s in shapes))


class Lexicon:
    """A learned public lexicon, independent of a document's declaration order."""

    def __init__(self, document=None):
        if document is None:
            document = json.loads(files('noema').joinpath(
                'resources/visible-lexicon-v1.json').read_text(encoding='utf-8'))
        data = deepcopy(document)
        require(isinstance(data, dict) and set(data) == {'schema', 'edition', 'entries'},
                'Invalid lexical document')
        require(data['schema'] == SCHEMA and isinstance(data['edition'], str)
                and data['edition'].strip(), 'Invalid lexical edition')
        require(isinstance(data['entries'], dict) and data['entries'], 'Empty lexicon')
        names, forms = {}, set()
        for name, entry in data['entries'].items():
            require(isinstance(name, str) and re.fullmatch('[a-z2-7]+', name),
                    'Invalid lexical name')
            require(isinstance(entry, dict) and set(entry) == {
                'parameters', 'result', 'roles', 'meaning', 'context',
                'contrast', 'form', 'aliases'}, 'Invalid lexical entry')
            require(entry['parameters'] in ([], ['individual'])
                    and entry['result'] == ('truth' if entry['parameters'] else 'individual'),
                    'This fragment supports individual constants and unary predicates')
            require(isinstance(entry['meaning'], str) and entry['meaning'].strip(),
                    'A lexical entry needs a meaning convention')
            for key in ('roles', 'context', 'contrast', 'aliases'):
                require(isinstance(entry[key], list) and all(
                    isinstance(v, str) and v.strip() for v in entry[key]),
                    'Invalid lexical ' + key)
            require(len(entry['roles']) == len(entry['parameters']) and entry['contrast'],
                    'Roles and contrasts are required')
            form = entry['form']
            require(isinstance(form, dict) and set(form) == {'size', 'companion', 'ray'},
                    'Invalid form fields')
            require(form['size'] in SIZES and form['companion'] in COMPANIONS
                    and (form['ray'] is None or form['ray'] in DIRECTIONS), 'Unknown form')
            require(form['size'] == ('large' if entry['parameters'] else 'medium'),
                    'Unary predicate/individual form size mismatch')
            glyph = _glyph(form)
            geometry_check(glyph['shapes'], glyph['paths'])
            signature = _shape_set(glyph['shapes'])
            require(signature not in forms, 'Ambiguous public lexical form')
            forms.add(signature)
            for alias in [name, *entry['aliases']]:
                require(re.fullmatch('[a-z2-7]+', alias) and alias not in names,
                        'Duplicate or invalid lexical alias')
                names[alias] = name
        self._document, self._names = data, names

    def document(self):
        return deepcopy(self._document)

    def resolve(self, name):
        require(isinstance(name, str) and name in self._names, 'Unknown lexical name')
        canonical = self._names[name]
        return canonical, deepcopy(self._document['entries'][canonical])

    def match(self, shapes):
        signature = _shape_set(shapes)
        matches = [name for name, entry in self._document['entries'].items()
                   if _shape_set(_glyph(entry['form'])['shapes']) == signature]
        require(len(matches) == 1, 'Unknown or ambiguous visible word')
        return self.resolve(matches[0])


def check_extension(previous, successor):
    """Reject changed meanings/forms, even when the old spelling is retained."""
    old, new = previous.document()['entries'], successor.document()['entries']
    for name, entry in old.items():
        require(name in new, 'Extension removed a lexical entry')
        require({k: v for k, v in entry.items() if k != 'aliases'} ==
                {k: v for k, v in new[name].items() if k != 'aliases'},
                'Extension changed an existing form or meaning')
        require(set(entry['aliases']) <= set(new[name]['aliases']), 'Extension removed an alias')
    return True


def _call(node):
    require(isinstance(node, dict) and set(node) == {'kind', 'symbol', 'arguments'}
            and node['kind'] == 'call' and isinstance(node['arguments'], list),
            'Only explicit function applications are supported')
    return node['symbol'], node['arguments']


def compile_assertion(statement, lexicon=None, *, argument_rail=0, separation=160.):
    """Render two public words with an ordinary frozen-geometry connection."""
    lexicon = lexicon or Lexicon()
    require(isinstance(statement, dict) and set(statement) == {'kind', 'body'}
            and statement['kind'] == 'assert', 'Expected a single assertion')
    head, args = _call(statement['body'])
    require(len(args) == 1, 'Only a unary assertion is supported')
    argument, inner = _call(args[0])
    require(not inner, 'Argument must be an individual constant')
    _, predicate = lexicon.resolve(head)
    _, individual = lexicon.resolve(argument)
    require(predicate['parameters'] == ['individual'] and predicate['result'] == 'truth'
            and individual['parameters'] == [] and individual['result'] == 'individual',
            'Lexical type mismatch')
    require(type(argument_rail) is int and argument_rail in (0, 1, 2), 'Unknown rail')
    require(type(separation) in (int, float) and math.isfinite(separation)
            and separation >= 120, 'Insufficient word separation')
    a = _glyph(predicate['form'], 50., PITCH)
    b = _glyph(individual['form'], 50. + separation, argument_rail * PITCH)
    shapes = a['shapes'] + b['shapes']
    connection = route(a['exit'], b['entry'],
                       [s for s in shapes if s['kind'] == 'circle'])
    require(connection is not None, 'No legal connection for this layout')
    path, segments = connection
    shapes += segments
    geometry_check(shapes, a['paths'] + b['paths'] + [path])
    # No AST, per-document registry or occurrence addresses in the output.
    return dict(shapes=shapes, width=b['right'] + 12.)


def _clean_shapes(shapes):
    require(isinstance(shapes, list) and 0 < len(shapes) <= 256, 'Invalid visible input size')
    result = []
    for shape in shapes:
        require(isinstance(shape, dict), 'Expected visible primitives')
        fields = {'circle': {'kind', 'x', 'y', 'r'},
                  'line': {'kind', 'x1', 'y1', 'x2', 'y2'}}.get(shape.get('kind'))
        require(fields is not None and set(shape) == fields, 'Unknown visible primitive or field')
        require(all(type(v) in (float, int) and math.isfinite(v)
                    for k, v in shape.items() if k != 'kind'), 'Nonfinite visible coordinate')
        require(shape['kind'] != 'circle' or shape['r'] > 0, 'Invalid circle radius')
        result.append(dict(shape))
    return result


def _translate(shapes, dx, dy, scale=1.):
    result = []
    for shape in shapes:
        moved = dict(shape)
        for key in ('x', 'x1', 'x2'):
            if key in moved:
                moved[key] = moved[key] * scale + dx
        for key in ('y', 'y1', 'y2'):
            if key in moved:
                moved[key] = moved[key] * scale + dy
        if 'r' in moved:
            moved['r'] *= scale
        result.append(moved)
    return result


def _merge_segments(lines):
    """Normalize storage direction and subdivisions of the same visible stroke."""
    segments = []
    for s in lines:
        a, b = (s['x1'], s['y1']), (s['x2'], s['y2'])
        require(math.dist(a, b) > EPS, 'Zero-length segment')
        segments.append(line(*sorted((a, b))))
    changed = True
    while changed:
        changed = False
        for i, s in enumerate(segments):
            a, b = (s['x1'], s['y1']), (s['x2'], s['y2'])
            for j in range(i):
                other = segments[j]
                c, d = (other['x1'], other['y1']), (other['x2'], other['y2'])
                cross = lambda p: (p[0]-a[0])*(b[1]-a[1]) - (p[1]-a[1])*(b[0]-a[0])
                if (abs(cross(c)) < EPS and abs(cross(d)) < EPS and
                    (any(_on_segment(p, s) for p in (c, d)) or
                     any(_on_segment(p, other) for p in (a, b)))):
                    points = sorted((a, b, c, d))
                    segments[j] = line(points[0], points[-1])
                    segments.pop(i)
                    changed = True
                    break
            if changed:
                break
    return segments


def _connected_words(circles):
    groups = []
    remaining = set(range(len(circles)))
    while remaining:
        component = {remaining.pop()}
        while True:
            neighbors = {i for i in remaining if any(
                math.dist((circles[i]['x'], circles[i]['y']),
                          (circles[j]['x'], circles[j]['y'])) <=
                circles[i]['r'] + circles[j]['r'] + EPS for j in component)}
            if not neighbors:
                break
            component.update(neighbors)
            remaining.difference_update(neighbors)
        require(len(component) <= 2, 'More than two circles in a lexical group')
        groups.append([circles[i] for i in component])
    return groups


def _connection(lines, groups):
    require(lines, 'Missing application connection')
    points, adjacency = [], {}

    def vertex(p):
        for i, existing in enumerate(points):
            if math.dist(p, existing) < EPS:
                return i
        points.append(p)
        return len(points)-1

    for s in lines:
        ends = [(s['x1'], s['y1']), (s['x2'], s['y2'])]
        # An external line may end on a rim but may not enter any circle.
        for rings in groups:
            for c in rings:
                a, b = ends
                dx, dy = b[0]-a[0], b[1]-a[1]
                t = max(0., min(1., ((c['x']-a[0])*dx+(c['y']-a[1])*dy)/(dx*dx+dy*dy)))
                distance = math.dist((c['x'], c['y']), (a[0]+t*dx, a[1]+t*dy))
                require(distance >= c['r']-EPS, 'External connection enters a lexical circle')
        a, b = map(vertex, ends)
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    terminals = []
    for i, point in enumerate(points):
        ports = [j for j, rings in enumerate(groups) if any(
            near(math.dist(point, (c['x'], c['y'])), c['r']) for c in rings)]
        require(len(ports) <= 1, 'Ambiguous lexical port')
        require(len(adjacency[i]) == (1 if ports else 2), 'Open or branched application path')
        if ports:
            terminals.append((i, ports[0]))
    require(len(terminals) == 2 and {g for _, g in terminals} == {0, 1},
            'Connection must join the two words exactly once')
    seen, pending = set(), [terminals[0][0]]
    while pending:
        node = pending.pop()
        if node not in seen:
            seen.add(node)
            pending.extend(adjacency[node] - seen)
    require(len(seen) == len(points), 'Disconnected ink')


def decode(shapes, lexicon=None):
    """Recover the canonical AST from visible primitives and shared vocabulary."""
    lexicon = lexicon or Lexicon()
    visible = _clean_shapes(shapes)
    circles = [s for s in visible if s['kind'] == 'circle']
    require(circles, 'No circles')
    anchor = max(circles, key=lambda c: c['r'])
    require(sum(near(c['r'], anchor['r']) for c in circles) == 1,
            'This fragment needs one large predicate circle')
    scale = LARGE / anchor['r']
    visible = _translate(visible, 50.-anchor['x']*scale, PITCH-anchor['y']*scale, scale)
    circles = [s for s in visible if s['kind'] == 'circle']
    segments = _merge_segments([s for s in visible if s['kind'] == 'line'])
    geometry_check(circles + segments, [[(s['x1'], s['y1']), (s['x2'], s['y2'])]
                                      for s in segments])
    groups = _connected_words(circles)
    require(len(groups) == 2, 'Expected two visible lexical groups')
    words, remaining = [], list(segments)
    for rings in groups:
        main = max(rings, key=lambda c: c['r'])
        center = (main['x'], main['y'])
        marks = [s for s in remaining if _on_segment(center, s)]
        for mark in marks:
            remaining.remove(mark)
        local = _translate(rings + marks, -main['x'], PITCH-main['y'])
        name, entry = lexicon.match(local)
        words.append((main['x'], name, entry))
    _connection(remaining, groups)
    words.sort(key=lambda row: row[0])
    require(words[0][0] < words[1][0]-EPS, 'Ambiguous left/right order')
    _, head, predicate = words[0]
    _, argument, individual = words[1]
    require(predicate['parameters'] == ['individual'] and individual['parameters'] == [],
            'Visible application has incompatible lexical types/order')
    return {'kind': 'assert', 'body': {'kind': 'call', 'symbol': head, 'arguments': [
        {'kind': 'call', 'symbol': argument, 'arguments': []}]}}


def to_svg(shapes):
    """Plain visible SVG: no source AST, IDs, titles, text or custom attributes."""
    visible = _clean_shapes(shapes)
    xs, ys = [], []
    elements = []
    for s in visible:
        if s['kind'] == 'circle':
            xs.extend((s['x']-s['r'], s['x']+s['r']))
            ys.extend((s['y']-s['r'], s['y']+s['r']))
            elements.append(f'<circle cx="{s["x"]:.9f}" cy="{s["y"]:.9f}" r="{s["r"]:.9f}"/>')
        else:
            xs.extend((s['x1'], s['x2']))
            ys.extend((s['y1'], s['y2']))
            attrs = ' '.join(f'{k}="{s[k]:.9f}"' for k in ('x1', 'y1', 'x2', 'y2'))
            elements.append(f'<line {attrs}/>')
    x, y = min(xs)-12, min(ys)-12
    width, height = max(xs)-x+12, max(ys)-y+12
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.9f} {y:.9f} {width:.9f} {height:.9f}" '
            f'fill="none" stroke="#203438" stroke-width="{STROKE}">\n' +
            '\n'.join(elements) + '\n</svg>\n')


def from_svg(text):
    """Extract the explicitly supported visible SVG subset; reject hidden ink."""
    require(isinstance(text, str) and len(text) <= 200000, 'Invalid SVG input')
    require('<!' not in text and '<?' not in text, 'SVG declarations are unsupported')
    root = ET.fromstring(text)
    ns = '{http://www.w3.org/2000/svg}'
    require(root.tag == ns+'svg' and set(root.attrib) == {
        'viewBox', 'fill', 'stroke', 'stroke-width'}, 'Unsupported SVG root')
    require(root.get('fill') == 'none' and root.get('stroke') == '#203438'
            and root.get('stroke-width') == str(STROKE), 'Unsupported SVG paint')
    require(not (root.text or '').strip(), 'SVG text is not supported')
    box = [float(v) for v in root.get('viewBox').split()]
    require(len(box) == 4 and all(math.isfinite(v) for v in box)
            and box[2] > 0 and box[3] > 0, 'Invalid SVG viewBox')
    shapes = []
    for element in root:
        require(not list(element) and not (element.text or '').strip()
                and not (element.tail or '').strip(), 'Unsupported SVG content')
        if element.tag == ns+'circle':
            require(set(element.attrib) == {'cx', 'cy', 'r'}, 'Unsupported circle attributes')
            shapes.append(circle(float(element.get('cx')), float(element.get('cy')),
                                 float(element.get('r'))))
        else:
            require(element.tag == ns+'line' and set(element.attrib) == {'x1','y1','x2','y2'},
                    'Unsupported SVG shape or attributes')
            shapes.append(dict(kind='line', **{k: float(v) for k, v in element.attrib.items()}))
    visible = _clean_shapes(shapes)
    for s in visible:
        if s['kind'] == 'circle':
            xs, ys = (s['x']-s['r'], s['x']+s['r']), (s['y']-s['r'], s['y']+s['r'])
        else:
            xs, ys = (s['x1'], s['x2']), (s['y1'], s['y2'])
        margin = STROKE/2
        require(min(xs)-margin >= box[0]-EPS and max(xs)+margin <= box[0]+box[2]+EPS
                and min(ys)-margin >= box[1]-EPS and max(ys)+margin <= box[1]+box[3]+EPS,
                'SVG viewport clips visible ink')
    return visible
