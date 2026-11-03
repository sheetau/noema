"""Read the frozen generator's actual circle/line relations without its AST.

This is the geometric front end, not a claim that the old script is a lossless
language. Silent links are candidates until a public grammar selects them.
Coordinates here use the published 32-unit writing grid.
"""
from collections import defaultdict
import math

from scripts.balanced_circle_script import (
    SMALL,MEDIUM,LARGE,PITCH,EPS,near,line,_on_segment,
)
from scripts.kant_geometry_rules import geometry_check
from scripts.visible_syntax_geometry import clean

VERSION='kant-observable-geometry-2'


def point(x,y):return (round(x,7),round(y,7))


def merged_lines(shapes):
    """Union collinear ink; SVG element breaks carry no information."""
    rows=defaultdict(list)
    for s in shapes:
        if s['kind']!='line':continue
        ax,ay,bx,by=(s[k] for k in ('x1','y1','x2','y2'))
        if near(ay,by):key=('h',round(ay,9));span=(ax,bx)
        elif near(ax,bx):key=('v',round(ax,9));span=(ay,by)
        elif near(abs(bx-ax),abs(by-ay)):
            slope=1 if (bx-ax)*(by-ay)>0 else -1
            key=(str(slope),round(ay-slope*ax,9));span=(ax,bx)
        else:raise ValueError('Line direction')
        rows[key].append(tuple(sorted(span)))
    answer=[]
    for (direction,offset),spans in sorted(rows.items()):
        joined=[]
        for a,b in sorted(spans):
            if joined and a<=joined[-1][1]+EPS:joined[-1]=(joined[-1][0],max(b,joined[-1][1]))
            else:joined.append((a,b))
        for a,b in joined:
            if direction=='h':ends=((a,offset),(b,offset))
            elif direction=='v':ends=((offset,a),(offset,b))
            else:ends=((a,int(direction)*a+offset),(b,int(direction)*b+offset))
            answer.append(line(*ends))
    return answer


def circle_relations(circles):
    result=[]
    for i,a in enumerate(circles):
        for j in range(i):
            b=circles[j];distance=math.dist((a['x'],a['y']),(b['x'],b['y']))
            if distance>a['r']+b['r']+EPS:continue
            owner=None
            if near(distance,0):kind='concentric'
            elif near(distance,a['r']+b['r']):kind='tangent'
            else:
                kind='center_on_rim'
                owner=i if near(distance,a['r']) else j
            result.append(dict(circles=[j,i],kind=kind,rim_owner=owner))
    return result


def stroke_graph(circles,lines):
    cuts=[{point(s['x1'],s['y1']),point(s['x2'],s['y2'])} for s in lines]
    for i,a in enumerate(lines):
        ax,ay=a['x1'],a['y1'];ux,uy=a['x2']-ax,a['y2']-ay
        length=math.hypot(ux,uy)
        for c in circles:
            center=(c['x'],c['y'])
            if _on_segment(center,a):cuts[i].add(point(*center))
            # Only radial intersections are legal; geometry_check ran first.
            for sign in (-1,1):
                p=(c['x']+sign*c['r']*ux/length,c['y']+sign*c['r']*uy/length)
                if _on_segment(p,a):cuts[i].add(point(*p))
        for j,b in enumerate(lines[:i]):
            bx,by=b['x1'],b['y1'];vx,vy=b['x2']-bx,b['y2']-by
            det=ux*vy-uy*vx
            if abs(det)<EPS:continue
            t=((bx-ax)*vy-(by-ay)*vx)/det;u=((bx-ax)*uy-(by-ay)*ux)/det
            if -EPS<=t<=1+EPS and -EPS<=u<=1+EPS:
                p=point(ax+t*ux,ay+t*uy);cuts[i].add(p);cuts[j].add(p)
    points=sorted(set().union(*cuts)) if cuts else []
    indices={p:i for i,p in enumerate(points)};edges=set()
    for s,items in zip(lines,cuts):
        ordered=sorted(items,key=lambda p:math.dist((s['x1'],s['y1']),p))
        edges.update(tuple(sorted((indices[a],indices[b]))) for a,b in zip(ordered,ordered[1:]))
    neighbors={i:set() for i in range(len(points))}
    for a,b in edges:neighbors[a].add(b);neighbors[b].add(a)
    vertices=[]
    for i,p in enumerate(points):
        centers=[j for j,c in enumerate(circles) if math.dist(p,(c['x'],c['y']))<EPS]
        rims=[j for j,c in enumerate(circles) if near(math.dist(p,(c['x'],c['y'])),c['r'])]
        vertices.append(dict(point=list(p),centers=centers,rims=rims,degree=len(neighbors[i])))
    return vertices,[list(e) for e in sorted(edges)]


def ray_features(c,lines):
    center=(c['x'],c['y']);directions=set();external=set();outer=set();reach=0.
    for s in lines:
        a,b=(s['x1'],s['y1']),(s['x2'],s['y2'])
        if _on_segment(center,s):
            for p in (a,b):
                distance=math.dist(center,p)
                if distance>EPS:
                    directions.add(round(math.atan2(p[1]-center[1],p[0]-center[0])/(math.pi/4))%8)
                    reach=max(reach,distance)
        for d in range(8):
            dx,dy=math.cos(d*math.pi/4),math.sin(d*math.pi/4)
            rim=(c['x']+c['r']*dx,c['y']+c['r']*dy)
            # Positive radial ink beyond the rim, not a tangential near miss.
            if _on_segment(rim,s) and any((p[0]-rim[0])*dx+(p[1]-rim[1])*dy>EPS for p in (a,b)):
                external.add(d)
                if near(c['r'],LARGE) and d%2 and not _on_segment(center,s):outer.add(d)
    direction=next(iter(directions)) if directions else None
    if direction is None:kind='center_free'
    elif reach<=c['r']+EPS:kind='radius'
    elif near(c['r'],LARGE) and direction%2:kind='center_diagonal'
    else:kind='center_external'
    return dict(center_kind=kind,center_direction=direction,
                outer_diagonals=sorted(outer),external_ports=sorted(external))


def read_geometry(shapes):
    """No dictionary, occurrence paths, invisible edges or source are accepted."""
    visible=clean(shapes)
    circles=sorted((s for s in visible if s['kind']=='circle'),key=lambda c:(c['x'],c['y'],c['r']))
    if not circles:raise ValueError('Missing circles')
    if len(circles)>256:raise ValueError('Geometric sentence circle budget')
    lines=merged_lines(visible)
    if len(lines)>512:raise ValueError('Geometric sentence line budget')
    geometry_check(circles+lines,[])
    relations=circle_relations(circles)
    vertices,edges=stroke_graph(circles,lines)
    # Contract circle interiors and the admitted two-circle relations.
    parents=list(range(len(circles)+len(vertices)))
    def root(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    def join(a,b):parents[root(a)]=root(b)
    for r in relations:join(*r['circles'])
    for i,v in enumerate(vertices):
        for c in v['centers']+v['rims']:join(c,len(circles)+i)
    for a,b in edges:join(len(circles)+a,len(circles)+b)
    identifiers={r:i for i,r in enumerate(sorted({root(i) for i in range(len(parents))}))}
    components=[identifiers[root(i)] for i in range(len(circles))]
    candidates=[]
    for i,a in enumerate(circles):
        for j in range(i):
            b=circles[j]
            if components[i]==components[j]:continue
            dx,dy=a['x']-b['x'],a['y']-b['y']
            if not (near(dx,0) or near(dy,0) or near(abs(dx),abs(dy))):continue
            segment=line((b['x'],b['y']),(a['x'],a['y']))
            # Only nearest centers on an axis can be consecutive silent ports.
            if any(k not in (i,j) and _on_segment((c['x'],c['y']),segment) for k,c in enumerate(circles)):continue
            candidates.append([j,i])
    records=[]
    for i,c in enumerate(circles):
        size=next(name for name,r in [('small',SMALL),('medium',MEDIUM),('large',LARGE)] if near(c['r'],r))
        records.append(dict(center=[round(c['x'],7),round(c['y'],7)],size=size,component=components[i],
                            **ray_features(c,lines)))
    return dict(version=VERSION,circles=records,relations=relations,vertices=vertices,edges=edges,
                visible_components=len(identifiers),silent_candidates=candidates)


def recover_seams(geometry):
    """A proposed public production: ordered components join at their extremes.

    The endpoint centers must be horizontally, vertically or diagonally aligned.
    Interleaved components and unattached line-only ink are rejected, not guessed.
    This production does not by itself assign quotation semantics to the gap.
    """
    components=defaultdict(set)
    for c in geometry['circles']:components[c['component']].add(tuple(c['center']))
    if len(components)!=geometry['visible_components']:raise ValueError('Unattached line-only component')
    ordered=sorted(components.values(),key=min);result=[]
    for left,right in zip(ordered,ordered[1:]):
        a,b=max(left),min(right)
        if a>=b:raise ValueError('Interleaved silent components')
        dx,dy=b[0]-a[0],b[1]-a[1]
        if not (near(dx,0) or near(dy,0) or near(abs(dx),abs(dy))):
            raise ValueError('Unaligned silent seam')
        result.append([list(a),list(b)])
    return result
