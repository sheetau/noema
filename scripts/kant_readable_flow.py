"""Experimental port-separated variant of the actual Kant compiler.

The old compiler and geometry checker are unchanged. This copy adds visible
flow constraints; lexical identity and native syntax decoding remain pending.
"""
from copy import deepcopy
from collections import Counter
import json
import math
from scripts.balanced_circle_script import line, line_error, radial_clearance, spacing_check, _segment_touches
from scripts.balanced_circle_script import (
    display_tree, expanded_tree, restore, signature, registry, events, profile,
    ray_order, stroke_mode, near, SMALL, MEDIUM, LARGE, PITCH, EPS, MIN_RUN,
    MIN_GAP, nucleus, geometry_check, pack_lines, STROKE,
)

VERSION = 'kant-port-separated-flow-1'


def boundary_port(circle, toward):
    dx,dy=toward[0]-circle['x'],toward[1]-circle['y']
    length=math.hypot(dx,dy)
    if length<EPS: raise ValueError('Missing direction at boundary')
    return (circle['x']+circle['radius']*dx/length,
            circle['y']+circle['radius']*dy/length)


def route(a, b, circles, preference=0, obstacles=(), diagnostics=None, end_center=False, forbidden_start=(), forbidden_end=()):
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
        terminal = boundary_port(b, points[-2])
        if any(math.dist(points[0],p)<EPS for p in forbidden_start): continue
        if any(math.dist(terminal,p)<EPS for p in forbidden_end): continue
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



def opening_form(event, mode, radius):
    """Classify actual syntax, never spelling, sentence index or random choice.

    Mirrored alternatives stay within the same opening family; they are selected
    only by the unchanged collision checker. This does not infer topic/emotion.
    """
    node = event['node']
    children = [c['node']['tag'] for c in node['children']]
    if node['tag'] == 'and':
        return dict(family='conjunction', mode='radius', directions=[6, 2])
    if node['tag'] == 'call' and 'function_ref' in children:
        return dict(family='function-argument', mode='outer' if near(radius,LARGE) else 'radius', directions=[5, 3])
    if node['tag'] == 'call' and 'quote' in children:
        return dict(family='quoted-argument', mode='radius', directions=[3, 5])
    if node['tag'] == 'evaluate' and not near(radius,LARGE):
        return dict(family='evaluation', mode='none', directions=[None])
    return dict(family='native-'+node['tag'], mode='entry' if mode=='incoming' else mode, directions=None)


def compile_expression(value, styles=None, reference_order=None, compact_columns=True):
    ast = display_tree(value)
    reference_order = reference_order or {}
    keys = registry(ast, reference_order)
    codes = {key: i for i, key in enumerate(keys)}
    stream = events(ast)
    occurrences=Counter(signature(e['node']) for e in stream)
    occurrences.update(signature(e['side']['node']) for e in stream if e['side'])
    shapes, paths, groups, edges, invisible = [], [], [], [], []
    moment = 0.0; total_area = 0.0; previous = None; previous_entry = None
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
        opening = opening_form(event, mode, radius) if index == 0 else None
        if opening: mode = opening['mode']
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
                if opening and opening['directions'] is not None: directions = opening['directions']
                main = nucleus(x, y, radius, pair, directions[0],companion,mode)
                local = deepcopy(main['shapes']); local_paths = deepcopy(main['paths'])
                satellites = []; side_ports = []
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
                    p, s = link; local += s; local_paths.append(p); side_ports.append(p[0])
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
                        link = route(previous, main['entry'], rings, depth+code,recent+local[len(main['shapes']):],
                                     failures,end_center=mode=='incoming',
                                     forbidden_start=() if previous_entry is None else (previous_entry,),
                                     forbidden_end=side_ports)
                        if link is None: continue
                        p, s = link; local += s; local_paths.append(p)
                        candidate_edge = dict(kind='visible', points=p, entry_port=boundary_port(main['entry'],p[-2]))
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
        previous_entry = edge.get('entry_port') if edge else None
    geometry_check(shapes, paths, invisible)
    assert restore(expanded_tree(ast)) == value
    return dict(opening=opening_form(stream[0], stroke_mode(stream[0], groups[0]['radius'], groups[0]['code']), groups[0]['radius']), version=VERSION, source=deepcopy(value), tree=ast, dictionary=[json.loads(k) for k in keys],
                reference_order=reference_order, groups=groups, edges=edges, invisible=invisible,
                shapes=shapes, paths=paths, width=groups[-1]['right']+12,columns=columns_used,
                normalized_moment=moment/total_area if total_area else 0)

