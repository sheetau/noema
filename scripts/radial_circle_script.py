"""Draft 06: a contextual, continuous circle network, not repeated word tiles.

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

VERSION = 'radial-circle-6-draft'
STROKE = 1.9
MIN_RUN = PITCH / 2  # Circle rim to the first bend/branch, in drawing units.


def radial_clearance(lines, circles):
    """Validate actual joined ink, including bends split across path records."""
    ends=[(s['x1'],s['y1']) for s in lines]+[(s['x2'],s['y2']) for s in lines]
    vertices=set(ends)
    for i,s in enumerate(lines):
        ax,ay=s['x1'],s['y1']; ux,uy=s['x2']-ax,s['y2']-ay
        for other in lines[:i]:
            bx,by=other['x1'],other['y1']; vx,vy=other['x2']-bx,other['y2']-by
            determinant=ux*vy-uy*vx
            if abs(determinant)<EPS: continue
            t=((bx-ax)*vy-(by-ay)*vx)/determinant
            u=((bx-ax)*uy-(by-ay)*ux)/determinant
            if -EPS<=t<=1+EPS and -EPS<=u<=1+EPS: vertices.add((ax+t*ux,ay+t*uy))
    for p in vertices:
        axes=set()
        incident=[]
        for s in lines:
            if _on_segment(p,s):
                axes.add(round(math.atan2(s['y2']-s['y1'],s['x2']-s['x1'])/(math.pi/4))%4)
                incident.append(s)
        if len(axes)<2: continue
        for c in circles:
            distance=math.dist(p,(c['x'],c['y']))
            if distance<c['r']-EPS: continue
            if distance-c['r']<MIN_RUN-EPS and _radial_chain(p,c,lines):
                raise ValueError('Bend/branch is too close to a circle rim')


def _radial_chain(p,c,lines):
    distance=math.dist(p,(c['x'],c['y']))
    if distance<EPS: return False
    dx,dy=(p[0]-c['x'])/distance,(p[1]-c['y'])/distance
    intervals=[]
    for s in lines:
        points=[(s['x1']-c['x'],s['y1']-c['y']),(s['x2']-c['x'],s['y2']-c['y'])]
        if any(abs(x*dy-y*dx)>EPS for x,y in points): continue
        intervals.append(sorted(x*dx+y*dy for x,y in points))
    end=c['r']
    for a,b in sorted(intervals):
        if a<=end+EPS and b>=end-EPS: end=max(end,b)
    return end>=distance-EPS


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
            if error: raise ValueError(error)
    topology=line_topology(lines)
    if topology['cycles'] or topology['arrows']: raise ValueError('Line-only loop or arrow')
    _check_joined_turns(lines)
    radial_clearance(lines,circles)
    for c in circles:
        directions = set()
        for s in lines:
            if _on_segment((c['x'], c['y']), s):
                if near(c['r'], SMALL):
                    raise ValueError('Small circle has a center stroke')
                center=(c['x'],c['y'])
                for p in ((s['x1'],s['y1']),(s['x2'],s['y2'])):
                    if math.dist(p,center)>EPS:
                        directions.add(round(math.atan2(p[1]-center[1],p[0]-center[0])/(math.pi/4))%8)
        if len(directions) > 1:
            raise ValueError('Diameter or multiple stroke directions at a circle center')
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
    """Compose conjunctions and shared unary subjects outside quoted syntax.

    Every original occurrence has an address. Fused conjunction addresses and
    repeated subject addresses are attached to the one combined realization.
    Quoted syntax is never flattened or equated by this display rule.
    """
    answer = []
    def visit(node, path, quoted=False):
        if node['tag']=='and' and not quoted:
            conjunctions=[]; leaves=[]
            def gather(n,p):
                if n['tag']=='and':
                    conjunctions.append(list(p))
                    for i,c in enumerate(n['children']): gather(c['node'],p+(i,))
                else: leaves.append((n,p))
            gather(node,path)
            combined=deepcopy(node)
            combined['children']=[dict(field=i,node=n) for i,(n,p) in enumerate(leaves)]
            item=dict(node=combined,path=list(path),side=None,fused_paths=conjunctions[1:],fusion='conjunction')
            unary=all(n['tag']=='call' and len(n['children'])==1 and not n['children'][0]['node']['children'] for n,p in leaves)
            shared=unary and all(n['children'][0]['node']==leaves[0][0]['children'][0]['node'] for n,p in leaves)
            if shared:
                addresses=[list(p+(0,)) for n,p in leaves]
                item['side']=dict(node=leaves[0][0]['children'][0]['node'],path=addresses[0],fused_paths=addresses[1:])
                item['fusion']='conjunction-with-shared-argument'
                answer.append(item)
                for n,p in leaves:
                    reduced=deepcopy(n); reduced['children']=[]
                    answer.append(dict(node=reduced,path=list(p),side=None,arity_override=1,shared_argument=addresses[0]))
            else:
                answer.append(item)
                for n,p in leaves: visit(n,p,quoted)
            return
        children = node['children']
        candidates = [i for i, c in enumerate(children) if not c['node']['children']]
        side = candidates[len(candidates)//2] if len(children) >= 2 and candidates else None
        item = dict(node=node, path=list(path), side=None)
        if side is not None:
            item['side'] = dict(node=children[side]['node'], path=list(path+(side,)))
        answer.append(item)
        for i, child in enumerate(children):
            if i != side: visit(child['node'], path+(i,),quoted or node['tag']=='quote')
    if ast['tag'] == 'assert' and len(ast['children']) == 1:
        visit(ast['children'][0]['node'], (0,))
    else: visit(ast, ())
    return answer


def nucleus(x, y, radius, pair, mark=0):
    shapes = [circle(x, y, radius)]
    paths = []
    # Only large/medium concentric rings admit a shared center-origin ray.
    # A small companion instead sits with its center on the medium rim.
    if pair == 'nested':
        if not near(radius,LARGE): raise ValueError('A small concentric ring cannot have a legal center-origin connection')
        inner = MEDIUM
        shapes.append(circle(x, y, inner))
    elif pair == 'offset':
        shapes.append(circle(x+radius, y, SMALL))
    if near(radius, MEDIUM) and pair != 'nested' and mark:
        # Exactly one center incidence. Its orientation is contextual, while
        # small rings (including the concentric inner ring) get no center ink.
        dx,dy = (-1.,0.) if pair=='offset' or mark==1 else (-2**-.5,2**-.5)
        paths.append([(x,y),(x+radius*dx,y+radius*dy)])
    if near(radius, LARGE): paths.append([(x, y), (x+radius, y)])
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
        # Explicit radial collars, independent of the available span. A route
        # with an insufficient span is rejected rather than bending on the rim.
        for bend in (ax+a['radius']+MIN_RUN, bx-abs(dy)-b['radius']-MIN_RUN):
            if ax<=bend<=bx-abs(dy):
                candidates.append([(ax,ay),(bend,ay),(bend+abs(dy),by),(bx,by)])
        candidates += [[(ax, ay), (ax+abs(dy), by), (bx, by)],
                       [(ax, ay), (bx-abs(dy), ay), (bx, by)]]
    for points in candidates:
        points = [p for i, p in enumerate(points) if not i or math.dist(p, points[i-1]) > EPS]
        if len(points) < 2: continue
        if math.dist(points[0], points[1]) < a['radius']-EPS or math.dist(points[-1], points[-2]) < b['radius']-EPS: continue
        # Every external connection stops at the rim. Large circles carry one
        # one-sided radius stroke; no line crosses their center to the far side.
        points[0] = tuple(points[0][i]+(points[1][i]-points[0][i])*a['radius']/math.dist(points[0], points[1]) for i in (0, 1))
        points[-1] = tuple(points[-1][i]+(points[-2][i]-points[-1][i])*b['radius']/math.dist(points[-1], points[-2]) for i in (0, 1))
        segments = [line(p, q) for p, q in zip(points, points[1:]) if math.dist(p, q) > EPS]
        if not any(line_error(s, circles) for s in segments):
            try: radial_clearance(segments,circles)
            except ValueError: continue
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
    n = event['node']; arity = event.get('arity_override',len(n['children']))
    radius = LARGE if arity >= 2 and n['tag'] in ('call', 'equal', 'implies', 'content') else MEDIUM
    if event.get('fused_paths'): radius=LARGE
    if not arity and code % 3 == 0: radius = SMALL
    pair = None
    if not near(radius, SMALL) and code % 4 == 2: pair = 'nested'
    if near(radius, MEDIUM) and code % 4 == 3: pair = 'offset'
    if near(radius, MEDIUM) and pair=='nested': pair='offset'
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
                    side_r = SMALL if side_code % 2 == 0 else MEDIUM
                    if y != PITCH and near(side_r,SMALL) and near(radius,MEDIUM):
                        side_y=PITCH; side_x=x+PITCH
                    elif y != PITCH:
                        side_y=2*PITCH-y; side_x=x
                    else:
                        side_y=0. if moment>0 else 2*PITCH
                        side_x=x+radius+side_r+2*MIN_RUN+PITCH
                    side = nucleus(side_x, side_y, side_r, None)
                    local += side['shapes']; local_paths += side['paths']
                    origin = main['entry'] if near(side_x, x) else main['exit']
                    link = route(origin, side['entry'], [s for s in local if s['kind']=='circle'], depth)
                    if link is None: continue
                    p, s = link; local += s; local_paths.append(p)
                    satellites.append(dict(path=event['side']['path'], fused_paths=event['side'].get('fused_paths',[]), x=side_x, y=side_y, radius=side_r, code=side_code))
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
                if groups and near(groups[-1]['radius'],radius) and groups[-1]['pair']==pair and near(groups[-1]['y'],y): score += 5
                if previous and near(abs(previous['y']-y),2*PITCH): score += 22
                choices.append((score, main, local, local_paths, satellites, candidate_edge, mass, delta, right))
        if not choices: raise ValueError(f'No legal contextual placement at {event["path"]}: {event["node"]["tag"]}; {failures[:3]}')
        _, main, local, local_paths, satellites, edge, mass, delta, right = min(choices, key=lambda c:c[0])
        shapes += local; paths += local_paths
        moment += delta; total_area += mass
        groups.append(dict(path=event['path'], tag=event['node']['tag'], code=code,
                           fused_paths=event.get('fused_paths',[]),fusion=event.get('fusion'),shared_argument=event.get('shared_argument'),
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
