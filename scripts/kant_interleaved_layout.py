"""Schedule the next nucleus of each flow before laying out its entire tail."""
from copy import deepcopy
import math


def compile_stream(stream, *, contacts=True):
    from scripts import kant_public_fragment as p
    def has_multiple(chain):
        return any(e.get('extra_sides') or any(has_multiple(side) for side in p.event_sides(e) if isinstance(side,list)) for e in chain)
    def attempt(lookahead):
        try:original=_compile_stream(stream,contacts=contacts,lookahead=lookahead,frontier_window=False)
        except p.PlacementFailure:
            if not lookahead:raise
            return _compile_stream(stream,contacts=contacts,lookahead=True)
        def excursion(drawing):
            return max((max(0.,-s['y1'],s['y1']-2*p.PITCH,-s['y2'],s['y2']-2*p.PITCH)
                for s in drawing['shapes'] if s['kind']=='line'),default=0.)
        previous=excursion(original)
        if not lookahead or previous<=2*p.PITCH:return original
        # Only investigate a large arch. The alternative must actually lower
        # it; otherwise preserve the original placement and its branch count.
        try:drawing=_compile_stream(stream,contacts=contacts,lookahead=True)
        except p.PlacementFailure:
            original['frontier_window_fallback']=True
            return original
        if excursion(drawing)<previous-p.EPS:return drawing
        original['frontier_window_rejected']=True
        return original
    lookahead=has_multiple(stream)
    try:
        return attempt(lookahead)
    except p.PlacementFailure:
        if lookahead:raise
        # Single branches also compete with their parent's continuation.
        # Try alternate routes before the caller removes a requested branch.
        # Successful old placements need neither a retry nor a new layout.
        drawing=attempt(True)
        drawing['continuation_search_retry']=True
        return drawing


def _compile_stream(stream, *, contacts=True, lookahead=False, frontier_window=True):
    # Import at the entry point: this layout uses the public grammar's forms,
    # but neither it nor its scheduling metadata is used by the reader.
    from scripts import kant_public_fragment as p
    flows=[];placed=[];shapes=[];paths=[];invisible=[];moment=0.;right=0.;frontier_yields=0
    def fork_points(path):
        points=list(path[1:-1])
        for a,b in zip(path,path[1:]):
            if math.dist(a,b)>=2*p.MIN_RUN:
                points.append(((a[0]+b[0])/2,(a[1]+b[1])/2))
        return points
    def connect(origin,target,depth,obstacles,checked_paths,forbidden,extra_forks=(),accept=None):
        root_start=origin['glyph']['exit'];starts=[root_start]
        if origin['fan']:
            starts += [dict(x=x,y=y,radius=0.) for x,y in (*origin['forks'],*extra_forks)]
            starts.sort(key=lambda s:math.dist((s['x'],s['y']),(target['entry']['x'],target['entry']['y'])))
        def allowed(path,segments):
            if origin['fan']:
                try:p.geometry_check(obstacles+segments,checked_paths+[path])
                except ValueError:return False
            return accept is None or accept(path,segments)
        for start in starts:
            link=p.route(start,target['entry'],[s for s in obstacles if s['kind']=='circle'],
                depth,obstacles,forbidden_start=forbidden if start is root_start else (),
                detours=True,separate=True,accept=allowed if lookahead else None,line_detours=lookahead)
            if link is None:continue
            if origin['fan'] and not lookahead:
                try:p.geometry_check(obstacles+link[1],checked_paths+[link[0]])
                except ValueError:continue
            return link
        return None

    def preserves_continuations(flow,index,parent,glyph,y,local,local_paths,edge,start_port):
        try:p.geometry_check(shapes+local,paths+local_paths,
            invisible+([edge] if edge and edge['kind']=='invisible' else []))
        except ValueError:return False
        reserved=[];reserved_paths=[];tail=glyph
        for following in flow['events'][index+1:]:
            if not following.get('lexical_seam'):break
            form=p.forms(following['token'])[0]
            tail=p.forms(following['token'],tail['right']+p.MIN_GAP-form['left'],y)[0]
            reserved+=tail['shapes'];reserved_paths+=tail['paths']
        for other in flows:
            if other is flow or other['previous'] is None or other['index']>=len(other['events']):continue
            if other['entrance_after'] is not None and not other['entrance_after']['groups'] and other['entrance_after'] is not flow:
                continue
            if other['waiting'] is not None and not other['waiting']['groups'] and other['waiting'] is not flow and not other['previous']['fan']:
                continue
            future=other['events'][other['index']]
            origin=other['previous']
            forbidden=origin['ports']+([start_port] if origin is parent and start_port is not None else [])
            probe_template=p.forms(future['token'])[0]
            rails=[p.PITCH] if other['index'] in other['middle'] else [0.,p.PITCH,2*p.PITCH]
            reachable=False
            for probe_extra in (0.,160.):
                probe_x=tail['right']+p.MIN_GAP+probe_extra-probe_template['left']
                for probe_y in rails:
                    for probe in p.forms(future['token'],probe_x,probe_y):
                        obstacles=shapes+local+reserved+probe['shapes']
                        extra_forks=fork_points(edge['path']) if origin is parent and edge and edge['kind']=='visible' else ()
                        link=connect(origin,probe,future['depth'],obstacles,
                            paths+local_paths+reserved_paths+probe['paths'],forbidden,extra_forks)
                        if link is None:continue
                        trial,segments=link
                        if not origin['fan']:
                            try:p.geometry_check(obstacles+segments,paths+local_paths+reserved_paths+probe['paths']+[trial])
                            except ValueError:continue
                        reachable=True;break
                    if reachable:break
                if reachable:break
            if not reachable:return False
        return True
    def add_flow(events,parent=None,entrance_after=None):
        flow=dict(id=len(flows),events=events,index=0,previous=parent,groups=[],
                  middle=p.fixed_middle_events(events),contact=False,waiting=None,entrance_after=entrance_after,
                  word_end=0,level=0 if parent is None else parent['level']+1)
        flows.append(flow)
        return flow
    main_flow=add_flow(stream)
    forced=None
    while any(f['index']<len(f['events']) for f in flows):
        pending=[f for f in flows if f['index']<len(f['events']) and
                 (f['waiting'] is None or f['waiting']['groups']) and
                 (f['entrance_after'] is None or f['entrance_after']['groups'])]
        if forced is not None:
            flow=forced;forced=None
        else:
            flow=min(pending,key=lambda f:(-f['level'],f['id']) if lookahead else
                ((f['previous']['glyph']['x'] if f['previous'] else -1)
                +p.PITCH*(len(f['events'])-f['index']),f['id']))
            if lookahead and frontier_window:
                oldest=min(pending,key=lambda f:(f['previous']['glyph']['right'] if f['previous'] else -1,f['id']))
                # Keep word/entrance obligations above indivisible. Otherwise
                # advance an old connection once two maximum-size nuclei and
                # their gaps fit between its source and the drawing frontier.
                if oldest['previous'] and right-oldest['previous']['glyph']['right']>2*(2*p.LARGE+p.MIN_GAP):
                    frontier_yields+=flow is not oldest
                    flow=oldest
        index=flow['index'];event=flow['events'][index];token=event['token']
        parent=flow['previous'];previous=parent['glyph']['exit'] if parent else None
        if event.get('word'):
            flow['contact']=False
            flow['word_end']=index+event.get('word_length',len(p.parts_for().get(event['word'],(event['word'],))))
        template=p.forms(token)[0];radius=template['radius']
        seam=bool(event.get('lexical_seam'))
        choices=[]
        for y in ([p.PITCH] if index in flow['middle'] or p.near(radius,p.LARGE) else [0.,p.PITCH,2*p.PITCH]):
            if seam and not p.near(y,previous['y']):continue
            touching=(contacts and not flow['contact'] and parent and placed[-1] is parent and
                token in p.root_words() and not event.get('word') and not seam and p.single_medium(parent['glyph']) and
                p.single_medium(template) and p.near(abs(y-previous['y']),p.PITCH))
            for extra in ((None,) if touching else ())+((0.,) if seam else (0.,12.,28.,48.,72.,104.,160.)):
                contact=extra is None
                left=(parent['glyph']['right']+p.MIN_GAP if seam else right+p.MIN_GAP) if placed else 12.
                x=previous['x']+p.PITCH if contact else left+(extra or 0.)-template['left']
                # A main continuation starts to the right of the first side
                # nucleus, regardless of where either flow eventually ends.
                if flow['waiting'] is not None and x<=flow['waiting']['groups'][0]['glyph']['x']+p.EPS:continue
                if not flow['groups'] and flow['entrance_after'] is not None and x<=flow['entrance_after']['groups'][0]['glyph']['x']+p.EPS:continue
                found=False
                for glyph in p.forms(token,x,y):
                    local=deepcopy(glyph['shapes']);local_paths=deepcopy(glyph['paths'])
                    edge=None;start_port=None;entry_port=None
                    if parent:
                        if contact:
                            start_port=p.boundary_port(previous,(x,y))
                            entry_port=p.boundary_port(glyph['entry'],(previous['x'],previous['y']))
                            if any(math.dist(start_port,port)<p.EPS for port in parent['ports']):continue
                            edge=dict(kind='tangent')
                        elif seam:
                            edge=dict(kind='invisible',centers=[(previous['x'],previous['y']),(x,y)])
                        else:
                            def keep_open(path,segments):
                                return preserves_continuations(flow,index,parent,glyph,y,
                                    local+segments,local_paths+[path],dict(kind='visible',path=path),path[0])
                            link=connect(parent,glyph,event['depth'],shapes+local,paths+local_paths,parent['ports'],
                                accept=keep_open if lookahead else None)
                            if link is None:continue
                            path,segments=link
                            local+=segments;local_paths.append(path)
                            start_port=path[0];entry_port=p.boundary_port(glyph['entry'],path[-2])
                            edge=dict(kind='visible',path=path)
                    if not (lookahead and edge and edge['kind']=='visible') and not preserves_continuations(
                        flow,index,parent,glyph,y,local,local_paths,edge,start_port):continue
                    delta=sum(s['r']**2*(s['y']-p.PITCH)/p.PITCH for s in local if s['kind']=='circle')
                    imbalance=abs(moment+delta)/p.MEDIUM**2
                    score=max(0.,imbalance-2.)*14+imbalance*.35+(glyph['right']-left)*.11
                    if previous and p.near(abs(previous['y']-y),2*p.PITCH):score+=22
                    if previous and p.near(previous['y'],y):score+=2
                    if parent and flow is not main_flow and index==0:
                        preferred=2*p.PITCH-previous['y'] if not p.near(previous['y'],p.PITCH) else (0. if moment>0 else 2*p.PITCH)
                        if not p.near(y,preferred):score+=100
                    choices.append((score,glyph,local,local_paths,edge,start_port,entry_port,delta))
                    found=True
                if found and not contact:break
        if not choices:
            raise p.PlacementFailure('No interleaved placement: '+str(token)+' at '+str(event['path']),
                [tuple(e['path']) for e in stream if isinstance(e['side'],list)])
        _,glyph,local,local_paths,edge,start_port,entry_port,delta=min(choices,key=lambda c:c[0])
        group=dict(glyph=glyph,event=event,ports=[] if entry_port is None else [entry_port],
                   shape_start=len(shapes),path_start=len(paths),side_flow=None,side_flows=[],
                   # One side and its continuation may share a stem too.
                   # The reader orders their first nuclei, not their ports.
                   fan=event.get('side') is not None,forks=[],level=flow['level'],
                   lexical_contact=bool(edge and edge['kind']=='tangent'))
        shapes+=local;paths+=local_paths;moment+=delta;right=max(right,glyph['right'])
        placed.append(group);flow['groups'].append(group);flow['previous']=group;flow['index']+=1
        flow['waiting']=None
        if start_port is not None:parent['ports'].append(start_port)
        if parent and parent['fan'] and edge and edge['kind']=='visible':parent['forks']+=fork_points(edge['path'])
        if edge and edge['kind']=='invisible':invisible.append(edge)
        if edge and edge['kind']=='tangent':flow['contact']=True
        if event.get('side') is not None:
            previous_branch=None
            for side in p.event_sides(event):
                if isinstance(side,str):
                    side=[dict(token=part,side=None,depth=event['depth']+1,path=event['path'],
                          **({'word':side} if i==0 else {}))
                          for i,part in enumerate(p.parts_for().get(side,(side,)))]
                branch=add_flow(side,group,previous_branch)
                group['side_flows'].append(branch);previous_branch=branch
            group['side_flow']=group['side_flows'][0];flow['waiting']=group['side_flows'][-1]
            forced=group['side_flows'][0]
        elif flow['index']<len(flow['events']) and (flow['events'][flow['index']].get('lexical_seam') or
                (lookahead and flow['index']<flow['word_end'])):
            # A compact silent boundary is an actual measured gap. Keep its
            # two endpoints together; never insert another flow in that gap.
            # At a fan, finish the current lexical word before placing another
            # entrance. A first nucleus alone does not reserve a route for its
            # remaining parts; competing entrances can trap that continuation.
            forced=flow
    p.geometry_check(shapes,paths,invisible)
    groups=[]
    for group in main_flow['groups']:
        glyph=group['glyph'];branch=group['side_flow'];event=group['event']
        centers=[[g['glyph']['x'],g['glyph']['y']] for g in branch['groups']] if branch else []
        groups.append(dict(token=event['token'],center=[glyph['x'],glyph['y']],
            right=max([glyph['right']]+[g['glyph']['right'] for g in branch['groups']]) if branch else glyph['right'],
            shape_start=group['shape_start'],path_start=group['path_start'],
            expression_branch=isinstance(event.get('side'),list),lexical_contact=group['lexical_contact'],
            side=centers[0] if centers else None,side_centers=centers))
    return dict(version=p.VERSION,shapes=shapes,groups=groups,width=right+12.,layout='interleaved',
        flow_count=len(flows),nested_forks=sum(len(g['side_flows']) for f in flows[1:] for g in f['groups']),
        frontier_yields=frontier_yields)
