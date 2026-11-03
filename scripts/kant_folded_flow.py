"""Fold and reconstruct connected ink using matching visible cut strokes."""
from copy import deepcopy
import math
from scripts.balanced_circle_script import EPS,near,line
from scripts.visible_syntax_geometry import clean
from scripts.kant_geometry_rules import merged_lines
from scripts.kant_item_rows import pack_rows,split_rows
from scripts.kant_item_runs import read_row
from scripts.kant_incremental_dictionary import Reader


def translate(shapes,dx=0.,dy=0.):
    result=deepcopy(shapes)
    for s in result:
        for key in ('x',) if s['kind']=='circle' else ('x1','x2'):s[key]+=dx
        for key in ('y',) if s['kind']=='circle' else ('y1','y2'):s[key]+=dy
    return result


def _bounds(shapes):
    return (min(s['x']-s['r'] if s['kind']=='circle' else min(s['x1'],s['x2']) for s in shapes),
            max(s['x']+s['r'] if s['kind']=='circle' else max(s['x1'],s['x2']) for s in shapes))


def _crossings(lines,x):
    result=[]
    for s in lines:
        a,b=(s['x1'],s['y1']),(s['x2'],s['y2'])
        if near(a[0],x) or near(b[0],x):return []
        if min(a[0],b[0])<x<max(a[0],b[0]):
            slope=(b[1]-a[1])/(b[0]-a[0])
            result.append((a[1]+slope*(x-a[0]),slope))
    result.sort()
    if any(near(a[0],b[0]) for a,b in zip(result,result[1:])):return []
    return result


def _cut_candidates(lines,left,right):
    # Between vertices/intersections, the crossing set and its order are
    # constant. Choose interior points of these intervals, not a fixed grid.
    stops={left,right};active=[]
    for s in lines:
        a,b=(s['x1'],s['y1']),(s['x2'],s['y2'])
        if max(a[0],b[0])<left or min(a[0],b[0])>right:continue
        stops.update(x for x in (a[0],b[0]) if left<x<right)
        if near(a[0],b[0]):continue
        slope=(b[1]-a[1])/(b[0]-a[0])
        active.append((min(a[0],b[0]),max(a[0],b[0]),slope,a[1]-slope*a[0]))
    for i,(lo,hi,m,c) in enumerate(active):
        for low,high,n,d in active[:i]:
            if near(m,n):continue
            x=(d-c)/(m-n)
            if max(left,lo,low)<x<min(right,hi,high):stops.add(x)
    stops=sorted(stops)
    return [(a+b)/2 for a,b in zip(stops,stops[1:]) if b-a>2*EPS and _crossings(lines,(a+b)/2)]


def fold(shapes,max_width):
    if not isinstance(max_width,(int,float)) or not math.isfinite(max_width) or max_width<=0:
        raise ValueError('Expected positive finite row width')
    parts=clean(shapes)
    circles=[s for s in parts if s['kind']=='circle']
    if not circles:raise ValueError('Fold requires circles')
    intervals=[]
    for a,b in sorted((c['x']-c['r'],c['x']+c['r']) for c in circles):
        if intervals and a<=intervals[-1][1]+EPS:intervals[-1]=(intervals[-1][0],max(b,intervals[-1][1]))
        else:intervals.append((a,b))
    lines=[s for s in parts if s['kind']=='line']
    left,right=_bounds(parts);cuts=[left]
    while right-cuts[-1]>max_width+EPS:
        candidates=[];limit=cuts[-1]+max_width
        for (_,a),(b,_) in zip(intervals,intervals[1:]):
            if a<=cuts[-1]+EPS or a>=limit-EPS:continue
            candidates+=_cut_candidates(lines,a,min(b,limit))
        if not candidates:raise ValueError('Row width has no legal circle-free continuation cut')
        cuts.append(max(candidates))
    cuts.append(right)
    rows=[]
    for start,end in zip(cuts,cuts[1:]):
        row=[]
        for s in parts:
            if s['kind']=='circle':
                if start-EPS<=s['x']<end+EPS:row.append(dict(s,x=s['x']-start))
                continue
            a,b=(s['x1'],s['y1']),(s['x2'],s['y2'])
            if a[0]>b[0]:a,b=b,a
            if near(a[0],b[0]):
                if start-EPS<=a[0]<=end+EPS:row.append(line((a[0]-start,a[1]),(b[0]-start,b[1])))
                continue
            lo,hi=max(a[0],start),min(b[0],end)
            if hi-lo<EPS:continue
            at=lambda x:(x-start,a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]))
            row.append(line(at(lo),at(hi)))
        if not any(s['kind']=='circle' for s in row):raise ValueError('Continuation row has no circles')
        rows.append(row)
    return dict(shapes=pack_rows(rows),row_shapes=rows,width=max(end-start for start,end in zip(cuts,cuts[1:])))


def _ports(shapes,side):
    circles=[s for s in shapes if s['kind']=='circle']
    if not circles:raise ValueError('Continuation row has no circles')
    left,right=_bounds(shapes);edge=left if side=='left' else right
    circle_edge=min(c['x']-c['r'] for c in circles) if side=='left' else max(c['x']+c['r'] for c in circles)
    if (edge>=circle_edge-EPS if side=='left' else edge<=circle_edge+EPS):return None
    lines=merged_lines(shapes);ports=[]
    for s in lines:
        a,b=(s['x1'],s['y1']),(s['x2'],s['y2'])
        ends=[v for v in (a,b) if near(v[0],edge)]
        if not ends:continue
        if len(ends)!=1:raise ValueError('Vertical stroke at continuation edge')
        if near(a[0],b[0]):raise ValueError('Invalid continuation stroke')
        slope=(b[1]-a[1])/(b[0]-a[0])
        if not any(near(slope,n) for n in (-1,0,1)):raise ValueError('Invalid continuation slope')
        ports.append((ends[0][1],round(slope)))
    ports.sort()
    if not ports or any(near(a[0],b[0]) for a,b in zip(ports,ports[1:])):
        raise ValueError('Ambiguous continuation edge')
    return edge,ports


def unfold(shapes):
    """Recover complete flows using rows and stroke ports, never source cuts."""
    flows=[];pending=None;exit_=None
    for row in split_rows(shapes):
        entry=_ports(row,'left');out=_ports(row,'right')
        if pending is None:
            if entry:raise ValueError('Continuation entry without a preceding row')
            pending=row
        else:
            if entry is None or exit_ is None:raise ValueError('Missing continuation counterpart')
            x,ports=exit_;next_x,next_ports=entry
            if len(ports)!=len(next_ports):raise ValueError('Continuation stroke count mismatch')
            dy=ports[0][0]-next_ports[0][0]
            if any(a[1]!=b[1] or not near(a[0],b[0]+dy) for a,b in zip(ports,next_ports)):
                raise ValueError('Continuation stroke directions/heights mismatch')
            dx=x-next_x;pending+=translate(row,dx,dy)
            if out:out=(out[0]+dx,[(y+dy,slope) for y,slope in out[1]])
        exit_=out
        if exit_ is None:
            flows.append([s for s in pending if s['kind']=='circle']+merged_lines(pending))
            pending=None
    if pending is not None:raise ValueError('Unfinished visible continuation')
    if not flows:raise ValueError('Empty folded page')
    return flows


def decode_page(shapes,*,seed=None,include_spellings=False,reader=None):
    if reader is not None and seed is not None:raise ValueError('Choose a reader or a seed')
    reader=Reader(seed) if reader is None else reader.fork()
    for flow in unfold(shapes):reader=read_row(flow,reader)
    return reader.result(include_spellings)
