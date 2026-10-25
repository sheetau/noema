"""Draft 09: a contextual, continuous circle network, not repeated word tiles.

The syntax traversal is explicit. Geometry uses bounded running area moment,
asymmetric terminal dependencies, and collision-tested radial routes.
"""
from copy import deepcopy
from collections import Counter
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

VERSION = 'balanced-circle-9-draft'
STROKE = 1.9
MIN_RUN = PITCH / 2  # Circle rim to the first bend/branch, in drawing units.
MIN_GAP = PITCH / 3
RAYS = [(math.cos(i*math.pi/4),math.sin(i*math.pi/4)) for i in range(8)]


def point_segment(p,s):
    a=(s['x1'],s['y1']);b=(s['x2'],s['y2'])
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.dist(p,(a[0]+t*dx,a[1]+t*dy))


def spacing_check(shapes):
    """Separate unrelated ink; trim only the collar of a real line junction."""
    circles=[s for s in shapes if s['kind']=='circle']
    lines=[s for s in shapes if s['kind']=='line']
    for i,c in enumerate(circles):
        for other in circles[:i]:
            gap=math.dist((c['x'],c['y']),(other['x'],other['y']))-c['r']-other['r']
            if EPS<gap<MIN_GAP-EPS: raise ValueError('Unrelated circles are too close')
        for s in lines:
            gap=point_segment((c['x'],c['y']),s)-c['r']
            if EPS<gap<MIN_GAP-EPS:
                # Two deliberately intersecting circles form one compound.
                # An axial outward stem of its companion is not unrelated ink.
                dx,dy=s['x2']-s['x1'],s['y2']-s['y1']
                same_compound=any(o is not c and math.dist((o['x'],o['y']),(c['x'],c['y']))<=o['r']+c['r']+EPS
                                  and _segment_touches(s,o) and abs((c['x']-s['x1'])*dy-(c['y']-s['y1'])*dx)<EPS for o in circles)
                if not same_compound: raise ValueError('Line is too close to another circle')
    for i,s in enumerate(lines):
        a=(s['x1'],s['y1']);b=(s['x2'],s['y2'])
        for other in lines[:i]:
            c=(other['x1'],other['y1']);d=(other['x2'],other['y2'])
            ux,uy=b[0]-a[0],b[1]-a[1];vx,vy=d[0]-c[0],d[1]-c[1]
            determinant=ux*vy-uy*vx
            if abs(determinant)>EPS:
                t=((c[0]-a[0])*vy-(c[1]-a[1])*vx)/determinant
                u=((c[0]-a[0])*uy-(c[1]-a[1])*ux)/determinant
                if EPS<t<1-EPS and EPS<u<1-EPS:
                    raise ValueError('Unintended crossing of line interiors')
                if -EPS<=t<=1+EPS and -EPS<=u<=1+EPS:
                    # At a genuine shared endpoint/fork, 45 degrees is the
                    # smallest allowed opening. Outside its MIN_RUN collar,
                    # such rays are at least MIN_GAP apart.
                    continue
            gap=min(point_segment(a,other),point_segment(b,other),point_segment(c,s),point_segment(d,s))
            if EPS<gap<MIN_GAP-EPS: raise ValueError('Unrelated line segments are too close')
    return True


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
            outer_diagonal=any(not near(s['x1'],s['x2']) and not near(s['y1'],s['y2']) and _segment_touches(s,c) for s in lines)
            if not directions and not outer_diagonal: raise ValueError('Large circle lacks a center stroke or rim diagonal')
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
    spacing_check(shapes)
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


def nucleus(x, y, radius, pair, mark=None, companion=None, mode='radius'):
    shapes = [circle(x, y, radius)]
    paths = []
    # Only large/medium concentric rings admit a shared center-origin ray.
    # A small companion instead sits with its center on the medium rim.
    if pair == 'nested':
        if not near(radius,LARGE): raise ValueError('A small concentric ring cannot have a legal center-origin connection')
        inner = MEDIUM
        shapes.append(circle(x, y, inner))
    elif pair in ('offset','offset-left'):
        if companion is None: companion=MEDIUM if near(radius,LARGE) else SMALL
        sign=-1 if pair=='offset-left' else 1
        shapes.append(circle(x+sign*radius,y,companion))
    if near(radius,LARGE) and mark is None and mode=='radius': mark=0
    if mode=='outer' and (not near(radius,LARGE) or mark not in (1,3,5,7)):
        raise ValueError('Rim-only terminal diagonal requires a large circle and an odd direction')
    if not near(radius,SMALL) and mark is not None and mode in ('radius','outer'):
        dx,dy=RAYS[mark]
        reach=radius*math.sqrt(2) if near(radius,LARGE) and mark%2 else radius
        start=(x+radius*dx,y+radius*dy) if mode=='outer' else (x,y)
        paths.append([start,(x+reach*dx,y+reach*dy)])
    if mode=='entry': paths.append([(x-radius-MIN_RUN,y),(x,y)])
    shapes.extend(line(a, b) for p in paths for a, b in zip(p, p[1:]))
    exit_x, exit_r = (x+radius, companion) if pair == 'offset' else (x, radius)
    entry_x, entry_r = (x-radius, companion) if pair == 'offset-left' else (x,radius)
    return dict(shapes=shapes, paths=paths, x=x, y=y, radius=radius, pair=pair,
                ray=mark if mode in ('radius','outer') else None,companion=companion,stroke_mode=mode,
                entry=dict(x=entry_x, y=y, radius=entry_r), exit=dict(x=exit_x, y=y, radius=exit_r),
                left=min(entry_x-entry_r,x-radius-MIN_RUN) if mode=='entry' else entry_x-entry_r, right=exit_x+exit_r)


def route(a, b, circles, preference=0, obstacles=(), diagnostics=None, end_center=False):
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
    # A single right-angle bend is legal, unlike successive right angles.
    # The radial collar filter decides whether the span is sufficient.
    candidates += [[(ax,ay),(ax,by),(bx,by)],[(ax,ay),(bx,ay),(bx,by)]]
    for points in candidates:
        points = [p for i, p in enumerate(points) if not i or math.dist(p, points[i-1]) > EPS]
        if len(points) < 2: continue
        if math.dist(points[0], points[1]) < a['radius']-EPS or math.dist(points[-1], points[-2]) < b['radius']-EPS: continue
        # Every external connection stops at the rim. Large circles carry one
        # one-sided radius stroke; no line crosses their center to the far side.
        points[0] = tuple(points[0][i]+(points[1][i]-points[0][i])*a['radius']/math.dist(points[0], points[1]) for i in (0, 1))
        if not end_center:
            points[-1] = tuple(points[-1][i]+(points[-2][i]-points[-1][i])*b['radius']/math.dist(points[-1], points[-2]) for i in (0, 1))
        segments = [line(p, q) for p, q in zip(points, points[1:]) if math.dist(p, q) > EPS]
        if not any(line_error(s, circles) for s in segments):
            try: radial_clearance(segments,circles)
            except ValueError as error:
                if diagnostics is not None: diagnostics.append(str(error))
                continue
            # Large diagonal links cannot bend or join another ring.
            if any(near(c['r'], LARGE) and any(
                not near(s['x1'], s['x2']) and not near(s['y1'], s['y2'])
                and _segment_touches(s, c) for s in segments) for c in circles): continue
            try: spacing_check(circles+[s for s in obstacles if s['kind']=='line']+segments)
            except ValueError as error:
                if diagnostics is not None: diagnostics.append(str(error))
                continue
            return points, segments
    return None


def _segment_touches(s, c):
    dx, dy = s['x2']-s['x1'], s['y2']-s['y1']
    t = max(0, min(1, ((c['x']-s['x1'])*dx+(c['y']-s['y1'])*dy)/(dx*dx+dy*dy)))
    return math.hypot(c['x']-s['x1']-t*dx, c['y']-s['y1']-t*dy) <= c['r']+EPS


def profile(event, code, repeats=1):
    n = event['node']; arity = event.get('arity_override',len(n['children']))
    radius = LARGE if arity >= 2 and n['tag'] in ('call', 'equal', 'implies', 'content') else MEDIUM
    if event.get('fused_paths'): radius=LARGE
    if not arity and code % 3 == 0: radius = SMALL
    pair = None
    if event.get('fused_paths'): pair='nested'
    elif repeats>1 and not arity and not near(radius,SMALL): pair='offset'
    return radius, pair


def stroke_mode(event,radius,code):
    if near(radius,SMALL): return 'none'
    tag=event['node']['tag']
    if tag in ('quote','content','exists','forall','not','function_ref','subtract','multiply'):return 'radius'
    if tag=='call' and event.get('arity_override',len(event['node']['children']))==1:return 'radius'
    if not event['node']['children']: return 'incoming' if code%3==2 else 'none'
    if near(radius,LARGE) and event['node']['tag']=='equal': return 'outer'
    if event['node']['tag']=='content': return 'radius'
    if event['node']['tag']=='quote': return 'none'
    return 'incoming'


def ray_order(event,ast):
    """Role selects a preferred direction; neighboring geometry selects allographs.

    Directions are E, SE, S, SW, W, NW, N, NE. No spelling hash or RNG.
    """
    preferred={'and':0,'or':1,'not':4,'implies':7,'equal':0,'forall':6,
               'exists':2,'content':5,'quote':3,'variable':2,'function_ref':6,
               'literal':1,'record':5}.get(event['node']['tag'],0)
    parent=ast; field=None
    for index in event['path']:
        edge=parent['children'][index]; field=edge['field']; parent=edge['node']
    if isinstance(field,list) and field[0]=='arguments':
        preferred=(0,7,1,4,5,3,6,2)[field[1]%8]
    return [(preferred+offset)%8 for offset in (0,1,-1,2,-2,3,-3,4)]


def compile_expression(value, styles=None, reference_order=None, compact_columns=True):
    ast = display_tree(value)
    reference_order = reference_order or {}
    keys = registry(ast, reference_order)
    codes = {key: i for i, key in enumerate(keys)}
    stream = events(ast)
    occurrences=Counter(signature(e['node']) for e in stream)
    occurrences.update(signature(e['side']['node']) for e in stream if e['side'])
    shapes, paths, groups, edges, invisible = [], [], [], [], []
    moment = 0.0; total_area = 0.0; previous = None
    contacts_used=0; offsets_used=0; columns_used=0
    for index, event in enumerate(stream):
        code = codes[signature(event['node'])]
        radius, pair = profile(event, code,occurrences[signature(event['node'])])
        if pair=='offset' and offsets_used>=max(1,len(stream)//5): pair=None
        companion=SMALL if near(radius,LARGE) and code//4%2 else None
        if pair=='offset' and ray_order(event,ast)[0] in (3,4,5): pair='offset-left'
        depth = len(event['path'])
        mode=stroke_mode(event,radius,code)
        if pair=='offset-left' and mode=='incoming':mode='none'
        if mode=='incoming' and not previous: mode='entry'
        choices = []; failures = []
        recent=shapes[groups[-3]['shape_start']:] if len(groups)>=3 else shapes
        recent_paths=paths[groups[-3]['path_start']:] if len(groups)>=3 else paths
        for y in ([PITCH] if near(radius, LARGE) else [0., PITCH, 2*PITCH]):
            can_stack=(compact_columns and len(stream)>=6 and columns_used<max(1,len(stream)//12)
                       and index>0 and not groups[-1].get('stacked')
                       and not event['node']['children'] and not stream[index-1]['node']['children']
                       and not event['side'] and not groups[-1]['satellites'] and pair is None and groups[-1]['pair'] is None
                       and event['path'][:-1]==groups[-1]['path'][:-1]
                       and abs(y-previous['y'])-radius-groups[-1]['radius']>=MIN_GAP-EPS)
            for extra in ((None,) if can_stack else ())+(0., 12., 28., 48., 72., 104.):
                stacked=extra is None
                left = groups[-1]['right']+MIN_GAP+4*(code//3)+(extra or 0) if groups else 12.
                x = previous['x'] if stacked else left+radius
                if mode=='entry': x+=MIN_RUN
                if pair=='offset-left': x+=companion or (MEDIUM if near(radius,LARGE) else SMALL)
                directions=ray_order(event,ast) if mode=='radius' else [d for d in ray_order(event,ast) if d%2] if mode=='outer' else [None]
                main = nucleus(x, y, radius, pair, directions[0],companion,mode)
                local = deepcopy(main['shapes']); local_paths = deepcopy(main['paths'])
                satellites = []
                if event['side'] is not None:
                    side_code = codes[signature(event['side']['node'])]
                    # A single off-axis dependency; no mirrored pair. Its rail
                    # compensates accumulated ink area, including this parent.
                    side_r = SMALL if side_code % 2 == 0 else MEDIUM
                    tangent=(near(y,PITCH) and near(radius,MEDIUM) and pair is None
                             and event['node']['tag'] in ('subtract','multiply') and not contacts_used)
                    if tangent:
                        side_y=PITCH if y!=PITCH else (0. if moment>0 else 2*PITCH)
                        side_x=x if near(side_r,SMALL) else x+PITCH
                    elif y != PITCH and near(side_r,SMALL) and near(radius,MEDIUM):
                        side_y=PITCH; side_x=x+PITCH
                    elif y != PITCH:
                        side_y=2*PITCH-y; side_x=x
                    else:
                        side_y=0. if moment>0 else 2*PITCH
                        side_x=x+radius+side_r+2*MIN_RUN+PITCH
                    side = nucleus(side_x, side_y, side_r, None)
                    local += side['shapes']; local_paths += side['paths']
                    origin = dict(x=x,y=y,radius=radius) if near(side_x,x) or tangent else main['exit']
                    link = route(origin, side['entry'], [s for s in local if s['kind']=='circle'], depth)
                    if link is None: continue
                    p, s = link; local += s; local_paths.append(p)
                    satellites.append(dict(path=event['side']['path'], fused_paths=event['side'].get('fused_paths',[]), x=side_x, y=side_y, radius=side_r, code=side_code,contact=tangent))
                candidate_edge = None
                if previous:
                    rings = [s for s in recent+local if s['kind']=='circle']
                    # Only the entry into an actual quotation gets a silent
                    # horizontal center-to-center edge, never arbitrary spaces.
                    silent = (event['node']['tag']=='quote' and near(previous['y'], y)
                              and len(invisible)<max(1,len(stream)//12))
                    if silent:
                        candidate_edge = dict(kind='invisible', centers=[(previous['x'],previous['y']),(x,y)])
                    else:
                        link = route(previous, main['entry'], rings, depth+code,recent+local[len(main['shapes']):],failures,end_center=mode=='incoming')
                        if link is None: continue
                        p, s = link; local += s; local_paths.append(p)
                        candidate_edge = dict(kind='visible', points=p)
                # Local collision and topology rejection. A final whole sentence
                # check below also catches interactions outside this window.
                tail=local[len(main['shapes']):]; tail_paths=local_paths[len(main['paths']):]
                legal=False
                for direction in directions:
                    candidate=nucleus(x,y,radius,pair,direction,companion,mode)
                    candidate_shapes=candidate['shapes']+tail
                    candidate_paths=candidate['paths']+tail_paths
                    try: geometry_check(recent+candidate_shapes,recent_paths+candidate_paths)
                    except ValueError as error:
                        failures.append(str(error)); continue
                    main=candidate;local=candidate_shapes;local_paths=candidate_paths;legal=True;break
                if not legal: continue
                circles = [s for s in local if s['kind']=='circle']
                mass = sum(c['r']**2 for c in circles)
                delta = sum(c['r']**2*(c['y']-PITCH)/PITCH for c in circles)
                right = max(c['x']+c['r'] for c in circles)
                if stacked:right=max(right,groups[-1]['right'])
                preferred = (depth+len(event['node']['children'])+code)%3
                # Running moment is bounded instead of forcing every word to
                # be center-heavy. Local excursions are followed by compensation.
                imbalance = abs(moment+delta)/MEDIUM**2
                score = max(0.,imbalance-2.0)*14 + imbalance*.35 + (right-left)*.11
                score += (0, 3, 5)[abs(int(y/PITCH)-preferred)]
                if previous and near(previous['y'], y): score += 2
                if groups and near(groups[-1]['radius'],radius) and groups[-1]['pair']==pair and near(groups[-1]['y'],y): score += 5
                if previous and near(abs(previous['y']-y),2*PITCH): score += 22
                if stacked:
                    score+= (left-main['left'])*.11  # Undo the negative local width.
                    score-=min(left+2*radius-right,2*PITCH)*.45
                choices.append((score, main, local, local_paths, satellites, candidate_edge, mass, delta, right,stacked))
                if not stacked:break  # Also compare the ordinary placement to a column.
        if not choices: raise ValueError(f'No legal contextual placement at {event["path"]}: {event["node"]["tag"]}, pair={pair}; {sorted(set(failures))}')
        _, main, local, local_paths, satellites, edge, mass, delta, right,stacked = min(choices, key=lambda c:c[0])
        shapes += local; paths += local_paths
        moment += delta; total_area += mass
        contacts_used+=sum(s['contact'] for s in satellites)
        offsets_used+=pair in ('offset','offset-left')
        columns_used+=stacked
        groups.append(dict(path=event['path'], tag=event['node']['tag'], code=code,
                           ray=main['ray'],stroke_mode=mode,companion=main['companion'],stacked=stacked,shape_start=len(shapes)-len(local),path_start=len(paths)-len(local_paths),
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
                shapes=shapes, paths=paths, width=groups[-1]['right']+12,columns=columns_used,
                normalized_moment=moment/total_area if total_area else 0)


def pack_lines(compiled, width, scale=.48):
    """Wrap only between full circle groups; split lines, never a circle.

    This is a view of the same connected unrolled sentence. Split pieces retain
    their original stroke, so wrapping creates no new semantic silent edges.
    """
    limit = width/scale
    units=[]
    for group in compiled['groups']:
        if group.get('stacked'):
            units[-1]['left']=min(units[-1]['left'],group['left'])
            units[-1]['right']=max(units[-1]['right'],group['right'])
        else: units.append(dict(left=group['left'],right=group['right']))
    groups = units; cuts = [0.]
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
