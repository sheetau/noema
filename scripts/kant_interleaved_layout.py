"""Schedule the next nucleus of each flow before laying out its entire tail."""
from copy import deepcopy
import math


def compile_stream(stream, *, contacts=True):
    # Import at the entry point: this layout uses the public grammar's forms,
    # but neither it nor its scheduling metadata is used by the reader.
    from scripts import kant_public_fragment as p
    flows=[];placed=[];shapes=[];paths=[];invisible=[];moment=0.;right=0.
    def add_flow(events,parent=None):
        flow=dict(id=len(flows),events=events,index=0,previous=parent,groups=[],
                  middle=p.fixed_middle_events(events),contact=False,waiting=None)
        flows.append(flow)
        return flow
    main_flow=add_flow(stream)
    forced=None
    while any(f['index']<len(f['events']) for f in flows):
        pending=[f for f in flows if f['index']<len(f['events']) and
                 (f['waiting'] is None or f['waiting']['groups'])]
        if forced is not None:
            flow=forced;forced=None
        else:
            flow=min(pending,key=lambda f:((f['previous']['glyph']['x'] if f['previous'] else -1)
                +p.PITCH*(len(f['events'])-f['index']),f['id']))
        index=flow['index'];event=flow['events'][index];token=event['token']
        parent=flow['previous'];previous=parent['glyph']['exit'] if parent else None
        if event.get('word'):flow['contact']=False
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
                            link=p.route(previous,glyph['entry'],
                                [s for s in shapes+local if s['kind']=='circle'],event['depth'],shapes+local,
                                forbidden_start=parent['ports'],detours=True,separate=True)
                            if link is None:continue
                            path,segments=link
                            local+=segments;local_paths.append(path)
                            start_port=path[0];entry_port=p.boundary_port(glyph['entry'],path[-2])
                            edge=dict(kind='visible')
                    try:p.geometry_check(shapes+local,paths+local_paths,
                        invisible+([edge] if edge and edge['kind']=='invisible' else []))
                    except ValueError:continue
                    reserved=[];reserved_paths=[];tail=glyph
                    for following in flow['events'][index+1:]:
                        if not following.get('lexical_seam'):break
                        form=p.forms(following['token'])[0]
                        tail=p.forms(following['token'],tail['right']+p.MIN_GAP-form['left'],y)[0]
                        reserved+=tail['shapes'];reserved_paths+=tail['paths']
                    reachable=True
                    for other in flows:
                        if other is flow or other['previous'] is None or other['index']>=len(other['events']):continue
                        if other['waiting'] is not None and not other['waiting']['groups'] and other['waiting'] is not flow:
                            continue
                        future=other['events'][other['index']]
                        origin=other['previous'];port=origin['glyph']['exit']
                        forbidden=origin['ports']+([start_port] if origin is parent and start_port is not None else [])
                        probe_template=p.forms(future['token'])[0]
                        rails=[p.PITCH] if other['index'] in other['middle'] else [0.,p.PITCH,2*p.PITCH]
                        reachable=False
                        for probe_extra in (0.,160.):
                            probe_x=tail['right']+p.MIN_GAP+probe_extra-probe_template['left']
                            for probe_y in rails:
                                for probe in p.forms(future['token'],probe_x,probe_y):
                                    obstacles=shapes+local+reserved+probe['shapes']
                                    link=p.route(port,probe['entry'],[s for s in obstacles if s['kind']=='circle'],
                                        future['depth'],obstacles,forbidden_start=forbidden,detours=True,separate=True)
                                    if link is None:continue
                                    trial,segments=link
                                    try:p.geometry_check(obstacles+segments,paths+local_paths+reserved_paths+probe['paths']+[trial])
                                    except ValueError:continue
                                    reachable=True;break
                                if reachable:break
                            if reachable:break
                        if not reachable:break
                    if not reachable:continue
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
            raise p.PlacementFailure('No interleaved placement: '+token+' at '+str(event['path']),
                [tuple(e['path']) for e in stream if isinstance(e['side'],list)])
        _,glyph,local,local_paths,edge,start_port,entry_port,delta=min(choices,key=lambda c:c[0])
        group=dict(glyph=glyph,event=event,ports=[] if entry_port is None else [entry_port],
                   shape_start=len(shapes),path_start=len(paths),side_flow=None,
                   lexical_contact=bool(edge and edge['kind']=='tangent'))
        shapes+=local;paths+=local_paths;moment+=delta;right=max(right,glyph['right'])
        placed.append(group);flow['groups'].append(group);flow['previous']=group;flow['index']+=1
        flow['waiting']=None
        if start_port is not None:parent['ports'].append(start_port)
        if edge and edge['kind']=='invisible':invisible.append(edge)
        if edge and edge['kind']=='tangent':flow['contact']=True
        if event.get('side') is not None:
            side=event['side']
            if isinstance(side,str):
                side=[dict(token=part,side=None,depth=event['depth']+1,path=event['path'],
                      **({'word':event['side']} if i==0 else {}))
                      for i,part in enumerate(p.parts_for().get(side,(side,)))]
            branch=add_flow(side,group);group['side_flow']=branch;flow['waiting']=branch
            forced=branch
        elif flow['index']<len(flow['events']) and flow['events'][flow['index']].get('lexical_seam'):
            # A compact silent boundary is an actual measured gap. Keep its
            # two endpoints together; never insert another flow in that gap.
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
        flow_count=len(flows),nested_forks=sum(g['side_flow'] is not None for f in flows[1:] for g in f['groups']))
