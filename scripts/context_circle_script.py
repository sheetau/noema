"""Draft 05: a contextual, continuous circle network, not repeated word tiles.

The syntax traversal is explicit. Geometry uses bounded running area moment,
asymmetric terminal dependencies, and collision-tested radial routes.
"""
from copy import deepcopy
import json
import math

from scripts.branch_circle_script import (
    display_tree, expanded_tree, restore, signature,
    _on_segment, _check_joined_turns,
)
from scripts.circle_contact_script import (
    SMALL, MEDIUM, LARGE, PITCH, EPS, circle, line, near, line_error,
    RADII, RAILS, legal_pair, line_topology,
)

VERSION = 'context-circle-5-draft'
STROKE = 1.9


def geometry_check(shapes, paths, invisible=()):
    circles = [s for s in shapes if s['kind'] == 'circle']
    lines = [s for s in shapes if s['kind'] == 'line']
    if any(s['kind'] not in ('circle', 'line') for s in shapes): raise ValueError('Unknown shape')
    for i, c in enumerate(circles):
        if not any(near(c['r'],r) for r in RADII) or not any(near(c['y'],y) for y in RAILS): raise ValueError('Circle size/rail')
        if near(c['r'],LARGE) and not near(c['y'],PITCH): raise ValueError('Large circle rail')
        if sum(other is not c and math.dist((c['x'],c['y']),(other['x'],other['y'])) <= c['r']+other['r']+EPS for other in circles)>1:
            raise ValueError('Circle has more than one circle partner')
        for other in circles[i+1:]:
            if not legal_pair(c,other): raise ValueError('Forbidden circle arrangement')
    for s in lines:
        error=line_error(s,[])
        if error: raise ValueError(error)
        for c in circles:
            error=line_error(s,[c])
            if error and error!='stroke terminates inside circle away from center': raise ValueError(error)
            if error:
                # An endpoint on an inner ring's rim is a real circle endpoint,
                # even though it is inside the enclosing ring. The outer ring
                # is still met radially; no arbitrary floating endpoint is legal.
                for p in ((s['x1'],s['y1']),(s['x2'],s['y2'])):
                    d=math.dist(p,(c['x'],c['y']))
                    if EPS<d<c['r']-EPS and not any(near(math.dist(p,(o['x'],o['y'])),o['r']) for o in circles):
                        raise ValueError('Stroke ends inside a circle without another rim')
    topology=line_topology(lines)
    if topology['cycles'] or topology['arrows']: raise ValueError('Line-only loop or arrow')
    _check_joined_turns(lines)
    for c in circles:
        directions = set()
        for s in lines:
            if _on_segment((c['x'], c['y']), s):
                if near(c['r'], SMALL):
                    raise ValueError('Small circle has a center stroke')
                angle = math.atan2(s['y2']-s['y1'], s['x2']-s['x1']) % math.pi
                directions.add(round(angle, 5))
        if len(directions) > 1:
            raise ValueError('More than one stroke axis at a circle center')
        if near(c['r'], LARGE):
            if not directions: raise ValueError('Large circle lacks a center stroke')
            for s in lines:
                if not near(s['x1'],s['x2']) and not near(s['y1'],s['y2']) and _segment_touches(s,c):
                    ends=[(s['x1'],s['y1']),(s['x2'],s['y2'])]
                    tips=[p for p in ends if near(abs(p[1]-c['y']),LARGE)]
                    if not tips or any(other is not s and _on_segment(tips[0],other) for other in lines):
                        raise ValueError('Large diagonal must terminate freely at top/bottom height')
    for edge in invisible:
        a, b = edge['centers']
        dx, dy = b[0]-a[0], b[1]-a[1]
        if not (near(dx, 0) or near(dy, 0) or near(abs(dx), abs(dy))):
            raise ValueError('Invisible connection must be a straight allowed direction')
        if not all(any(near(c['x'], p[0]) and near(c['y'], p[1]) for c in circles) for p in (a, b)):
            raise ValueError('Invisible connection must join actual circle centers')
    return True


def registry(ast, reference_order):
    keys, bindings = set(), {}
    def visit(n):
        keys.add(signature(n))
        if n['tag'] in ('forall', 'exists', 'content') and 'variable' in n['payload']:
            bindings.setdefault(n['payload']['variable'], len(bindings))
        if n['tag'] == 'record' and 'name' in n['payload']:
            bindings.setdefault(n['payload']['name'], len(bindings))
        for c in n['children']: visit(c['node'])
    visit(ast)
    def key(k):
        tag, payload = json.loads(k)
        normalized = {}
        for field, item in payload.items():
            if field in ('symbol', 'identity'):
                if item not in reference_order: raise ValueError('Missing reference registry: '+item)
                normalized[field] = reference_order[item]
            elif field in ('name', 'variable') and item in bindings:
                normalized[field] = bindings[item]
            else: normalized[field] = item
        return tag, tuple((f, type(v).__name__, v) for f, v in sorted(normalized.items()))
    return sorted(keys, key=key)


def events(ast):
    """Preorder continuation plus one short, explicitly addressed side dependency.

    A terminal second argument may attach to the side of its actual parent.
    All other arguments remain in field order; their paths retain scope/order.
    There is no copied parent port and no independently spaced word cell.
    """
    answer = []
    def visit(node, path):
        children = node['children']
        candidates = [i for i, c in enumerate(children) if not c['node']['children']]
        side = candidates[len(candidates)//2] if len(children) >= 2 and candidates else None
        item = dict(node=node, path=list(path), side=None)
        if side is not None:
            item['side'] = dict(node=children[side]['node'], path=list(path+(side,)))
        answer.append(item)
        for i, child in enumerate(children):
            if i != side: visit(child['node'], path+(i,))
    if ast['tag'] == 'assert' and len(ast['children']) == 1:
        visit(ast['children'][0]['node'], (0,))
    else: visit(ast, ())
    return answer


def nucleus(x, y, radius, pair, mark=0):
    shapes = [circle(x, y, radius)]
    paths = []
    # One registered compound referent may share a center or circumference.
    # The small inner ring is joined only at its rim; no spoke goes through it.
    if pair == 'nested':
        inner = MEDIUM if near(radius, LARGE) else SMALL
        shapes.append(circle(x, y, inner))
        if not near(radius, LARGE): paths.append([(x-radius, y), (x-inner, y)])
    elif pair == 'offset':
        shapes.append(circle(x+radius, y, SMALL))
    if near(radius, MEDIUM) and pair != 'nested' and mark:
        # Exactly one center incidence. Its orientation is contextual, while
        # small rings (including the concentric inner ring) get no center ink.
        dx,dy = (-1.,0.) if pair=='offset' or mark==1 else (-2**-.5,2**-.5)
        paths.append([(x,y),(x+radius*dx,y+radius*dy)])
    if near(radius, LARGE): paths.append([(x-radius, y), (x+radius, y)])
    shapes.extend(line(a, b) for p in paths for a, b in zip(p, p[1:]))
    exit_x, exit_r = (x+radius, SMALL) if pair == 'offset' else (x, radius)
    return dict(shapes=shapes, paths=paths, x=x, y=y, radius=radius, pair=pair,
                entry=dict(x=x, y=y, radius=radius), exit=dict(x=exit_x, y=y, radius=exit_r),
                left=x-radius, right=exit_x+exit_r)


def route(a, b, circles, preference=0):
    ax, ay, bx, by = a['x'], a['y'], b['x'], b['y']
    dx, dy = bx-ax, by-ay
    candidates = []
    if near(dx, 0) or near(dy, 0) or near(abs(dx), abs(dy)):
        candidates.append([(ax, ay), (bx, by)])
    if dx >= abs(dy):
        # Relation/depth alters where a bend falls; no fixed Y template.
        fractions = (.22, .72, .46) if preference % 2 else (.72, .22, .46)
        for fraction in fractions:
            bend = ax+(dx-abs(dy))*fraction
            candidates.append([(ax, ay), (bend, ay), (bend+abs(dy), by), (bx, by)])
        candidates += [[(ax, ay), (ax+abs(dy), by), (bx, by)],
                       [(ax, ay), (bx-abs(dy), ay), (bx, by)]]
    for points in candidates:
        points = [p for i, p in enumerate(points) if not i or math.dist(p, points[i-1]) > EPS]
        if len(points) < 2: continue
        if math.dist(points[0], points[1]) < a['radius']-EPS or math.dist(points[-1], points[-2]) < b['radius']-EPS: continue
        # Every external connection stops at the rim. Large circles carry one
        # independent axial diameter; routing may join that diameter at the rim.
        points[0] = tuple(points[0][i]+(points[1][i]-points[0][i])*a['radius']/math.dist(points[0], points[1]) for i in (0, 1))
        points[-1] = tuple(points[-1][i]+(points[-2][i]-points[-1][i])*b['radius']/math.dist(points[-1], points[-2]) for i in (0, 1))
        segments = [line(p, q) for p, q in zip(points, points[1:]) if math.dist(p, q) > EPS]
        if not any(line_error(s, circles) for s in segments):
            # Large diagonal links cannot bend or join another ring.
            if any(near(c['r'], LARGE) and any(
                not near(s['x1'], s['x2']) and not near(s['y1'], s['y2'])
                and _segment_touches(s, c) for s in segments) for c in circles): continue
            return points, segments
    return None


def _segment_touches(s, c):
    dx, dy = s['x2']-s['x1'], s['y2']-s['y1']
    t = max(0, min(1, ((c['x']-s['x1'])*dx+(c['y']-s['y1'])*dy)/(dx*dx+dy*dy)))
    return math.hypot(c['x']-s['x1']-t*dx, c['y']-s['y1']-t*dy) <= c['r']+EPS


def profile(event, code):
    n = event['node']; arity = len(n['children'])
    radius = LARGE if arity >= 2 and n['tag'] in ('call', 'equal', 'implies', 'content') else MEDIUM
    if not arity and code % 3 == 0: radius = SMALL
    pair = None
    if not near(radius, SMALL) and code % 4 == 2: pair = 'nested'
    if near(radius, MEDIUM) and code % 4 == 3: pair = 'offset'
    return radius, pair


def compile_expression(value, styles=None, reference_order=None):
    ast = display_tree(value)
    reference_order = reference_order or {}
    keys = registry(ast, reference_order)
    codes = {key: i for i, key in enumerate(keys)}
    stream = events(ast)
    shapes, paths, groups, edges, invisible = [], [], [], [], []
    moment = 0.0; total_area = 0.0; previous = None
    for index, event in enumerate(stream):
        code = codes[signature(event['node'])]
        radius, pair = profile(event, code)
        depth = len(event['path'])
        choices = []; failures = []
        for y in ([PITCH] if near(radius, LARGE) else [0., PITCH, 2*PITCH]):
            for extra in (0., 12., 28., 48., 72.):
                left = groups[-1]['right']+10+4*(code//6)+extra if groups else 12.
                x = left+radius
                main = nucleus(x, y, radius, pair, (depth+code)%3)
                local = deepcopy(main['shapes']); local_paths = deepcopy(main['paths'])
                satellites = []
                if event['side'] is not None:
                    side_code = codes[signature(event['side']['node'])]
                    # A single off-axis dependency; no mirrored pair. Its rail
                    # compensates accumulated ink area, including this parent.
                    side_y = 2*PITCH if y == 0 else 0. if y == 2*PITCH else (0. if moment > 0 else 2*PITCH)
                    side_r = SMALL if side_code % 2 == 0 else MEDIUM
                    side_x = x if y != PITCH else x+radius+side_r+30
                    side = nucleus(side_x, side_y, side_r, None)
                    local += side['shapes']; local_paths += side['paths']
                    origin = main['entry'] if near(side_x, x) else main['exit']
                    link = route(origin, side['entry'], [s for s in local if s['kind']=='circle'], depth)
                    if link is None: continue
                    p, s = link; local += s; local_paths.append(p)
                    satellites.append(dict(path=event['side']['path'], x=side_x, y=side_y, radius=side_r, code=side_code))
                candidate_edge = None
                if previous:
                    rings = [s for s in shapes[-70:]+local if s['kind']=='circle']
                    # Only the entry into an actual quotation gets a silent
                    # horizontal center-to-center edge, never arbitrary spaces.
                    silent = event['node']['tag']=='quote' and near(previous['y'], y)
                    if silent:
                        candidate_edge = dict(kind='invisible', centers=[(previous['x'],previous['y']),(x,y)])
                    else:
                        link = route(previous, main['entry'], rings, depth+code)
                        if link is None: continue
                        p, s = link; local += s; local_paths.append(p)
                        candidate_edge = dict(kind='visible', points=p)
                # Local collision and topology rejection. A final whole sentence
                # check below also catches interactions outside this window.
                recent = shapes[-90:]
                try: geometry_check(recent+local, paths[-40:]+local_paths)
                except ValueError as error:
                    failures.append(str(error)); continue
                circles = [s for s in local if s['kind']=='circle']
                mass = sum(c['r']**2 for c in circles)
                delta = sum(c['r']**2*(c['y']-PITCH)/PITCH for c in circles)
                right = max(c['x']+c['r'] for c in circles)
                preferred = (depth+len(event['node']['children'])+code)%3
                # Running moment is bounded instead of forcing every word to
                # be center-heavy. Local excursions are followed by compensation.
                imbalance = abs(moment+delta)/MEDIUM**2
                score = max(0.,imbalance-2.0)*14 + imbalance*.35 + (right-left)*.11
                score += (0, 3, 5)[abs(int(y/PITCH)-preferred)]
                if previous and near(previous['y'], y): score += 2
                choices.append((score, main, local, local_paths, satellites, candidate_edge, mass, delta, right))
        if not choices: raise ValueError(f'No legal contextual placement at {event["path"]}: {event["node"]["tag"]}; {failures[:3]}')
        _, main, local, local_paths, satellites, edge, mass, delta, right = min(choices, key=lambda c:c[0])
        shapes += local; paths += local_paths
        moment += delta; total_area += mass
        groups.append(dict(path=event['path'], tag=event['node']['tag'], code=code,
                           x=main['x'], y=main['y'], radius=radius, pair=pair,
                           left=main['left'], right=right, satellites=satellites,
                           moment=moment, area=total_area))
        if edge:
            edge.update(source=groups[-2]['path'], target=event['path'])
            edges.append(edge)
            if edge['kind']=='invisible': invisible.append(edge)
        previous = main['exit']
    geometry_check(shapes, paths, invisible)
    assert restore(expanded_tree(ast)) == value
    return dict(version=VERSION, source=deepcopy(value), tree=ast, dictionary=[json.loads(k) for k in keys],
                reference_order=reference_order, groups=groups, edges=edges, invisible=invisible,
                shapes=shapes, paths=paths, width=groups[-1]['right']+12,
                normalized_moment=moment/total_area if total_area else 0)


def pack_lines(compiled, width, scale=.48):
    """Wrap only between full circle groups; split lines, never a circle.

    This is a view of the same connected unrolled sentence. Split pieces retain
    their original stroke, so wrapping creates no new semantic silent edges.
    """
    limit = width/scale
    groups = compiled['groups']; cuts = [0.]
    for i, group in enumerate(groups):
        if group['right']-cuts[-1] > limit:
            if not i: raise ValueError('Display width too small')
            cut = (groups[i-1]['right']+group['left'])/2
            if cut <= cuts[-1] or group['right']-cut > limit: raise ValueError('Group exceeds line width')
            cuts.append(cut)
    cuts.append(compiled['width'])
    rows = []
    for start, end in zip(cuts, cuts[1:]):
        out = []
        for s in compiled['shapes']:
            if s['kind']=='circle':
                if start <= s['x'] < end: out.append(dict(s, x=s['x']-start))
            else:
                a, b = (s['x1'],s['y1']), (s['x2'],s['y2'])
                if a[0] > b[0]: a,b=b,a
                if b[0] < start or a[0] > end: continue
                if near(a[0], b[0]):
                    if not start <= a[0] < end: continue
                    p,q=a,b
                else:
                    lo, hi=max(a[0],start),min(b[0],end)
                    if hi-lo < EPS: continue
                    interp=lambda x:(x,a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]))
                    p,q=interp(lo),interp(hi)
                out.append(line((p[0]-start,p[1]),(q[0]-start,q[1])))
        rows.append(dict(start=start, end=end, shapes=out))
    return rows
