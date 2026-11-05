"""Concept2 v5 geometry; earlier validators remain available unchanged."""
from copy import deepcopy
from collections import Counter
import math
from scripts import concept2_composition as v2
from scripts.concept2_composition import (S,M,L,F,P,D,PEN,EPS,circle,arc,line,move,point,on_arc,bounds,circle_hits,visible_point,line_circle_hits)


def eclipse(side=-1,contact=True,sectors=(0,1,6,7)):
    phi=180 if side<0 else 0
    excluded={(int(phi/45)-1)%8,int(phi/45)%8}
    outside=set(sectors)-excluded
    if not outside:raise ValueError('At least 45 degrees outside the medium circle')
    pieces=v2.sector_arcs(L,outside)
    beta=45 if contact else math.degrees(math.atan2(M,L))
    pieces.append(arc(L,phi-beta,phi+beta))
    return pieces+[circle(M,side*math.hypot(M,L))]


def merge_arcs(shapes):
    groups={};other=[]
    for s in shapes:
        if s['kind']!='arc':other.append(s);continue
        groups.setdefault((s['x'],s['y'],s['r']),[]).append(s)
    for (x,y,r),segments in groups.items():
        cuts=sorted({0.,360.,*(a%360 for s in segments for a in (s['a'],s['b']))})
        intervals=[]
        for a,b in zip(cuts,cuts[1:]):
            if any(on_arc(s,(a+b)/2) for s in segments):
                if intervals and abs(intervals[-1][1]-a)<EPS:intervals[-1]=(intervals[-1][0],b)
                else:intervals.append((a,b))
        if len(intervals)>1 and intervals[0][0]==0 and intervals[-1][1]==360:
            intervals=[(intervals[-1][0],intervals[0][1]+360)]+intervals[1:-1]
        other.extend(arc(r,a,b,x,y) for a,b in intervals)
    return other


def trim_small_interiors(shapes):
    """Clip internal construction strokes; never silently clip external routes."""
    small=[s for s in shapes if s['kind']=='arc' and abs(s['r']-S)<EPS]
    out=[]
    for s in shapes:
        if s['kind']!='line':out.append(s);continue
        ax,ay=s['x1'],s['y1'];dx,dy=s['x2']-ax,s['y2']-ay;den=dx*dx+dy*dy
        cuts={0.,1.}
        for ring in small:
            for x,y in line_circle_hits(s,ring):cuts.add(max(0.,min(1.,((x-ax)*dx+(y-ay)*dy)/den)))
        cuts=sorted(cuts)
        for a,b in zip(cuts,cuts[1:]):
            t=(a+b)/2
            if b-a>EPS and not any(math.hypot(ax+t*dx-r['x'],ay+t*dy-r['y'])<S-EPS for r in small):
                out.append(line((ax+a*dx,ay+a*dy),(ax+b*dx,ay+b*dy)))
    return merge_arcs(out)


def from_svg(raw):
    import xml.etree.ElementTree as ET
    result=[]
    for e in ET.fromstring(raw).iter():
        tag=e.tag.split('}')[-1]
        if 'transform' in e.attrib:raise ValueError('SVG transforms must be flattened')
        if 'style' in e.attrib or any(e.get(k) not in (None,'1') for k in ('opacity','stroke-opacity','fill-opacity')):
            raise ValueError('Styled or hidden ink is outside the flat SVG grammar')
        if e.get('display') or e.get('visibility') or e.get('stroke-width')=='0':raise ValueError('Hidden ink')
        if tag in ('g','line','path') and e.get('stroke')=='none':raise ValueError('Invisible stroke')
        if tag=='circle':
            x,y,r=(float(e.attrib[k]) for k in ('cx','cy','r'))
            if e.get('fill')=='#203438' and e.get('stroke')=='none':result.append(dict(kind='dot',x=x,y=y,r=r))
            else:result.append(circle(r,x,y))
        elif tag=='line':result.append(dict(kind='line',**{k:float(e.attrib[k]) for k in ('x1','y1','x2','y2')}))
        elif tag=='path':
            t=e.attrib['d'].split()
            if not(len(t)==11 and t[0]=='M' and t[3]=='A'):raise ValueError('Expected a circular SVG arc')
            ax,ay,r,ry,rotation,large,sweep,bx,by=map(float,[*t[1:3],*t[4:]])
            if abs(r-ry)>EPS or rotation or sweep!=1:raise ValueError('Unsupported SVG arc')
            dx,dy=bx-ax,by-ay;length=math.hypot(dx,dy)
            if not length or length>2*r+1e-5:raise ValueError('Invalid arc chord')
            h=0. if abs(length-2*r)<1e-5 else math.sqrt(max(0,r*r-length*length/4))
            for sign in (1,-1):
                x=(ax+bx)/2-sign*dy*h/length;y=(ay+by)/2+sign*dx*h/length
                a=math.degrees(math.atan2(ay-y,ax-x));b=math.degrees(math.atan2(by-y,bx-x));span=(b-a)%360
                if h==0 or (span>180)==bool(large):result.append(arc(r,a,a+span,x,y));break
            else:raise ValueError('Invalid SVG arc sweep')
        elif tag not in ('svg','g'):raise ValueError('Unexpected SVG element '+tag)
    supports=[]
    for s in result:
        if s['kind']!='arc':continue
        same=next((q for q in supports if abs(q['r']-s['r'])<1e-4 and math.hypot(q['x']-s['x'],q['y']-s['y'])<1e-4),None)
        if same:s['x'],s['y'],s['r']=same['x'],same['y'],same['r']
        else:supports.append(s)
    return merge_arcs(result)


def side_gap(segments,angle):
    if any(on_arc(s,angle) for s in segments):return 0.
    before=min((angle-s['b'])%360 for s in segments)
    after=min((s['a']-angle)%360 for s in segments)
    return before+after


def has_side_arc(segments,side):
    lo,hi=(-90,90) if side==1 else (90,270)
    return any(min(s['b'],hi+360*k)-max(s['a'],lo+360*k)>EPS
               for s in segments for k in range(-3,4))


def port(shapes,side):
    arcs=[s for s in shapes if s['kind']=='arc'];angle=0 if side==1 else 180
    groups={}
    for s in arcs:groups.setdefault((s['x'],s['y'],s['r']),[]).append(s)
    choices=[]
    rails=sorted({round(s['y'],8) for s in arcs if min(abs(s['y']-y) for y in (-P,0,P))<EPS})
    for rail in rails:
        points=[];guards=[]
        for (x,y,r),pieces in groups.items():
            if abs(y-rail)>EPS:continue
            gap=side_gap(pieces,angle)
            if gap==0:points.append(x+side*r)
            elif r>S+EPS and not any(q['r']==S and math.hypot(q['x']-x,q['y']-y)<S-EPS for q in arcs) and not any(q['kind']=='dot' and math.hypot(q['x']-x,q['y']-y)<EPS for q in shapes):points.append(x)
            if r in (M,L) and has_side_arc(pieces,side):guards.append(x+side*r)
        if not points:continue
        actual=max(points,key=lambda x:side*x)
        anchor=max([actual,*guards],key=lambda x:side*x)
        choices.append((side*anchor,side*actual,-abs(rail),actual,anchor,rail))
    if not choices:raise ValueError('No horizontal port')
    _,_,_,actual,anchor,y=max(choices)
    return (actual,y),(anchor,y)


def unit(token,shapes,*,fixed=False,silent=False):
    shapes=trim_small_interiors(shapes)
    left,top,right,bottom=bounds(shapes)
    entry,entry_anchor=port(shapes,-1);exit,exit_anchor=port(shapes,1)
    return dict(token=token,shapes=shapes,entry=entry,exit=exit,entry_anchor=entry_anchor,exit_anchor=exit_anchor,
                fixed=fixed or any(s['kind']=='arc' and (s['r']>=L-EPS or abs(s['y'])>EPS) for s in shapes),silent=silent)


ROOT_FORMS={k:trim_small_interiors(s) for k,s in v2.ROOT_FORMS.items()}
LIGATURES=deepcopy(v2.LIGATURES)
for key,side,contact,sectors in [
    (('book','home','round'),-1,True,(5,6,7,0,1)),
    (('book','home','above'),-1,False,(5,6,7,0,1)),
    (('book','inside'),1,True,(1,2,3,4,5)),
    (('book','methodpossible'),1,False,(1,2,3,4,5))]:
    LIGATURES[key]=eclipse(side,contact,sectors)
LIGATURES={k:trim_small_interiors(s) for k,s in LIGATURES.items()}
def large_link_shape(side=1,lane=1):
    if side not in (-1,1) or lane not in (-1,1):raise ValueError('Large link direction')
    start=L/math.sqrt(2);end=F/math.sqrt(2)
    return [circle(L),line((side*start,lane*start),(side*end,lane*end)),circle(S,side*(L+M),lane*P)]


LIGATURES[('aki','round')]=large_link_shape(-1,-1)
LIGATURES[('round','aki')]=large_link_shape(1,1)


def separator(last=False,family='values'):
    # The small circle connects the two stems through its circumference.
    shapes=[circle(S),circle(M) if last else arc(M,90,270),
            line((0,-F),(0,-S)),line((0,S),(0,F))]
    if family=='quoted':shapes.append(arc(F,135,225))
    elif family=='references':shapes.append(arc(L,315,405))
    elif family!='values':raise ValueError('Unknown argument-group family')
    return shapes


def branch_shape(lanes):
    shapes=[];spacing=2*S+M
    for i,lane in enumerate(lanes):
        x=i*spacing;y=(-1 if i%2==0 else 1)*P;sign=-1 if y<0 else 1
        shapes.append(circle(S,x))
        shapes.extend([line((x,sign*S),(x,y)),line((x,y),(x+spacing-S,y)),circle(S,x+spacing,y)])
        a={-1:180,0:135,1:90}[lane]
        shapes.append(arc(M,a,a+90,x+spacing,y))
        shapes.append(line((x+S,0),(x+spacing-S,0)))
    shapes.append(circle(S,len(lanes)*spacing))
    return shapes


def selection_shape(lanes):
    """An ordered upper/middle/lower selection, not a freely ordered tuple."""
    if tuple(lanes)!=tuple(sorted(set(lanes))) or any(x not in (-1,0,1) for x in lanes):
        raise ValueError('Selection requires distinct lanes in ascending order')
    distance=math.hypot(L,S);beta=math.degrees(math.atan2(S,L));intervals=[(0.,360.)];small=[]
    for lane in lanes:
        theta=45*lane;rad=math.radians(theta);small.append(circle(S,distance*math.cos(rad),distance*math.sin(rad)))
        for k in (-1,0,1):
            cut=(theta-beta+360*k,theta+beta+360*k);next_intervals=[]
            for a,b in intervals:
                if cut[1]<=a or cut[0]>=b:next_intervals.append((a,b));continue
                if a<cut[0]:next_intervals.append((a,cut[0]))
                if cut[1]<b:next_intervals.append((cut[1],b))
            intervals=next_intervals
    return merge_arcs([arc(L,a,b) for a,b in intervals]+small)


def dot_mask(label):
    if not 0<=label<256:raise ValueError('Dot key')
    return 153 if label==0 else 0 if label==153 else label


def dot_shape(label,source=True):
    mask=dot_mask(label)
    if mask==0 and not source:return v2.dot_shape(0,False)
    medium=v2.sector_arcs(M,{i for i in range(8) if mask&(1<<i)})
    # A missing port does not force a larger enclosure. Disconnected small
    # terminals belong to the glyph and never carry a line through the dot.
    radius=M if mask else L
    enclosure=medium if mask else [circle(L)]
    shapes=enclosure+[dict(kind='dot',x=0.,y=0.,r=D),circle(S,radius+M+S)]
    if any(on_arc(s,0) for s in enclosure):shapes.append(line((radius,0),(radius+M,0)))
    if not any(on_arc(s,180) for s in enclosure):shapes.append(circle(S,-radius-M-S))
    return shapes


def directed_selection_shape(lanes):
    """The center ray selects the first port; continue clockwise, wrapping once."""
    ordered=sorted(set(lanes))
    start=ordered.index(lanes[0])
    if list(lanes)!=ordered[start:]+ordered[:start]:raise ValueError('Selection must follow clockwise order')
    shapes=selection_shape(ordered)
    theta=math.radians(45*lanes[0]);end=math.hypot(L,S)-S
    return shapes+[line((0,0),(end*math.cos(theta),end*math.sin(theta)))]


def merge_shape(lanes):
    """Two or three scoped references converge on a small-circle circumference.

    Physical top-to-bottom order is argument order. Each leaf's outward arc
    identifies the referenced lane; repeated references remain distinct leaves.
    """
    if len(lanes) not in (2,3) or any(v not in (-1,0,1) for v in lanes):raise ValueError('Merge arity/lanes')
    rails=(-1,1) if len(lanes)==2 else (-1,0,1)
    shapes=[circle(S)]
    for rail,lane in zip(rails,lanes):
        # Only outward arcs: no incidental crossing of neighbouring leaves.
        base={-1:225,0:135,1:45}[rail]
        a,b={-1:(base,base+45),0:(base,base+90),1:(base+45,base+90)}[lane]
        leaf=[circle(S),arc(M,a,b)];actual,anchor=port(leaf,1)
        if rail:
            x=-P-M-anchor[0];y=rail*P
            shapes.extend(move(leaf,x,y))
            shapes.extend([line((x+actual[0],y),(-P,y)),line((-P,y),(-S/math.sqrt(2),rail*S/math.sqrt(2)))])
        else:
            x=-S-M-anchor[0]
            shapes.extend(move(leaf,x))
            shapes.append(line((x+actual[0],0),(-S,0)))
    return merge_arcs(shapes)


def routes(previous,u,rail):
    actual,anchor=previous['exit'],previous['exit_anchor']
    for poly,kind in v2.route_candidates(anchor,u['entry_anchor'][1]+rail):
        x=poly[-1][0]-u['entry_anchor'][0]
        target=(x+u['entry'][0],rail+u['entry'][1])
        points=[actual,*poly[1:-1],target]
        yield x,[line(a,b) for a,b in zip(points,points[1:])],kind


def layout(units,*,max_width=None):
    rows=[];shapes=[];placed=[];carry=None;moment=mass=0.;rejected=Counter();continuations=[]
    def finish(outgoing):
        nonlocal shapes,placed,continuations
        if outgoing:
            last=placed[-1];end=(last['exit_anchor'][0]+M,last['exit_anchor'][1])
            shapes.append(line(last['exit'],end))
            continuations.append(end)
        ink_check(shapes,continuations=continuations)
        rows.append(dict(shapes=shapes,placed=placed,width=bounds(shapes)[2],outgoing=outgoing))
        shapes=[];placed=[];continuations=[]
    for index,u in enumerate(units):
        local=u['shapes'];left,top,right,bottom=bounds(local)
        def candidates():
            for rail in ([0.] if u['fixed'] else [0.,-P,P]):
                if not placed:
                    if carry is None:variants=[(-left,[],'start')]
                    else:
                        dummy=dict(exit=(0.,carry),exit_anchor=(0.,carry))
                        variants=routes(dummy,u,rail)
                elif u.get('silent'):
                    variants=[(placed[-1]['exit_anchor'][0]+M-left,[],'silent')]
                else:variants=routes(placed[-1],u,rail)
                for x,path,kind in variants:
                    translated=move(local,x,rail)
                    # Keep complete circle supports; slicing by primitive count
                    # can drop the mandatory interior arc of an older eclipse.
                    threshold=x+left-2*F
                    recent=[s for s in shapes if (s['x']+s['r'] if s['kind']!='line' else max(s['x1'],s['x2']))>=threshold]
                    try:ink_check(recent+translated+path,free_ends=False)
                    except ValueError as e:rejected[str(e)]+=1;continue
                    weight=sum(s['r'] for s in local if s['kind']=='arc')
                    delta=sum(s['r']*(s['y']+rail) for s in local if s['kind']=='arc')
                    score=(x+right)*.2+abs(moment+delta)/max(mass+weight,1)*.7
                    if len(placed)>1 and rail==placed[-1]['rail']==placed[-2]['rail']:score+=8
                    yield score,x,rail,path,translated,weight,delta,kind
        choices=list(candidates())
        if not choices:raise ValueError(f'No legal placement at {index}: {u["token"]}; {dict(rejected)}')
        result=min(choices,key=lambda x:x[:3])
        # A bare dot and its preceding unit are kept together at row boundaries.
        reserve=right
        if index+1<len(units) and units[index+1].get('silent'):
            nxt=units[index+1];reserve=max(reserve,u['exit_anchor'][0]+M+bounds(nxt['shapes'])[2]-bounds(nxt['shapes'])[0]+M)
        if max_width and placed and result[1]+max(reserve,u['exit_anchor'][0]+M)>max_width:
            if u.get('silent'):raise ValueError('Silent edge cannot begin a new row')
            carry=placed[-1]['exit_anchor'][1];finish(True)
            result=min(candidates(),key=lambda x:x[:3])
        _,x,rail,path,translated,weight,delta,kind=result
        if not placed and carry is not None:continuations.append((0.,carry))
        shapes.extend(path+translated);mass+=weight;moment+=delta
        positioned=dict(u,x=x,rail=rail,shapes=translated,route=kind)
        for field in ('entry','exit','entry_anchor','exit_anchor'):
            positioned[field]=(u[field][0]+x,u[field][1]+rail)
        placed.append(positioned)
    if placed:finish(False)
    return rows


def fold(drawings,width):
    """Retain checked glyph rails/routes; rebuild only the radius-based collars."""
    rows=[];shapes=[];last=None;cursor=0.;carry=None;starts=[];continuations=[]
    def finish(outgoing):
        nonlocal shapes,last,cursor,starts,continuations
        if outgoing:
            end=(last['exit_anchor'][0]+M,last['exit_anchor'][1])
            shapes.append(line(last['exit'],end));continuations.append(end)
        if shapes:
            ink_check(shapes,continuations=continuations)
            rows.append(dict(shapes=shapes,width=bounds(shapes)[2],outgoing=outgoing,starts=starts))
        shapes=[];last=None;cursor=0.;starts=[];continuations=[]
    for drawing in drawings:
        for i,p in enumerate(drawing['placed']):
            u=deepcopy(p);u['shapes']=move(p['shapes'],-p['x'],-p['rail'])
            for field in ('entry','exit','entry_anchor','exit_anchor'):
                u[field]=(p[field][0]-p['x'],p[field][1]-p['rail'])
            left,top,right,bottom=bounds(u['shapes']);rail=p['rail']
            if not shapes:x=-left;path=[]
            elif i==0:x=cursor+2*M-left;path=[]
            elif u.get('silent'):x=last['exit_anchor'][0]+M-left;path=[]
            else:x,path,_=next((r for r in routes(last,u,rail) if r[2]==p['route']))
            reserve=max(right,u['exit_anchor'][0]+M)
            if i+1<len(drawing['placed']) and drawing['placed'][i+1].get('silent'):
                nxt=drawing['placed'][i+1]
                reserve=max(reserve,nxt['exit_anchor'][0]-p['x']+M)
            if shapes and x+reserve>width:
                if i==0:finish(False);x=-left;path=[]
                elif u.get('silent'):raise ValueError('Silent-dot fold split')
                else:
                    carry=last['exit_anchor'][1];finish(True)
                    dummy=dict(exit=(0.,carry),exit_anchor=(0.,carry))
                    x,path,_=next(routes(dummy,u,rail))
                    continuations.append((0.,carry))
            if i==0:starts.append(x)
            shapes.extend(move(u['shapes'],x,rail)+path);cursor=max(cursor,x+right)
            last={field:(u[field][0]+x,u[field][1]+rail) for field in ('entry','exit','entry_anchor','exit_anchor')}
    finish(False)
    return rows

def check_free_ends(arcs,lines,continuations):
    """Bound radial free ink, including a ray split into several SVG lines."""
    tolerance=2e-4
    def on_segment(p,s):
        dx,dy=s['x2']-s['x1'],s['y2']-s['y1'];length=math.hypot(dx,dy)
        t=((p[0]-s['x1'])*dx+(p[1]-s['y1'])*dy)/length**2
        return -tolerance/length<=t<=1+tolerance/length and abs((p[0]-s['x1'])*dy-(p[1]-s['y1'])*dx)<tolerance*length
    for s in lines:
        for p,q in (((s['x1'],s['y1']),(s['x2'],s['y2'])),((s['x2'],s['y2']),(s['x1'],s['y1']))):
            if any(math.dist(p,c)<tolerance for c in continuations):continue
            if any(math.dist(p,(c['x'],c['y']))<tolerance for c in arcs):continue
            if any(abs(math.dist(p,(c['x'],c['y']))-c['r'])<tolerance and visible_point(c,p) for c in arcs):continue
            directions=set()
            for t in lines:
                if on_segment(p,t):
                    for v in ((t['x1'],t['y1']),(t['x2'],t['y2'])):
                        if math.dist(p,v)>tolerance:directions.add(round(math.atan2(v[1]-p[1],v[0]-p[0]),4))
            if len(directions)!=1:continue
            # Grow the collinear connected support; segmentation cannot hide its owner.
            dx,dy=q[0]-p[0],q[1]-p[1];length=math.hypot(dx,dy);dx/=length;dy/=length
            intervals=[]
            for t in lines:
                ends=((t['x1'],t['y1']),(t['x2'],t['y2']))
                if all(abs((v[0]-p[0])*dy-(v[1]-p[1])*dx)<tolerance for v in ends):
                    intervals.append(sorted((v[0]-p[0])*dx+(v[1]-p[1])*dy for v in ends))
            reach=0.
            for a,b in sorted(intervals):
                if a<=reach+tolerance and b>=-tolerance:reach=max(reach,b)
            support=line(p,(p[0]+reach*dx,p[1]+reach*dy))
            for c in arcs:
                center=(c['x'],c['y'])
                if abs((center[0]-p[0])*dy-(center[1]-p[1])*dx)>tolerance:continue
                owns=on_segment(center,support) or any(visible_point(c,h) for h in line_circle_hits(support,c))
                if owns and math.dist(p,center)>F+tolerance:raise ValueError(f'Radial free end exceeds fourth circle: {p}, owner {center}')


def ink_check(shapes,*,rail_origin=0.,allow_shift=False,continuations=(),free_ends=True):
    """Check actual arcs, rather than mistaking missing quadrants for ink."""
    arcs=[s for s in shapes if s['kind']=='arc'];lines=[s for s in shapes if s['kind']=='line'];dots=[s for s in shapes if s['kind']=='dot']
    for c in arcs:
        if min(abs(c['r']-r) for r in (S,M,L,F))>2e-4:raise ValueError('Unknown circle radius')
        if c['r']>=L-EPS and abs(c['y']-rail_origin)>2e-4:raise ValueError('Large circle off middle rail')
        if abs(c['r']-S)<EPS and abs(c['b']-c['a']-360)>2e-3:raise ValueError('Small partial circle')
        if abs(c['r']-F)<EPS:
            if any(on_arc(c,a) for a in (90,270)):raise ValueError('Forbidden fourth-circle top/bottom arc')
    supports={}
    for c in arcs:supports.setdefault(tuple(round(c[k],4) for k in ('x','y','r')),[]).append(c)
    groups=list(supports.values())
    for i,aa in enumerate(groups):
        a=aa[0]
        for bb in groups[:i]:
            b=bb[0];distance=math.hypot(a['x']-b['x'],a['y']-b['y']);r,R=sorted((a['r'],b['r']))
            if distance<2e-4:continue
            if distance<abs(R-r)-2e-4:raise ValueError('Eccentric containment')
            hits=circle_hits(a,b)
            visible=[p for p in hits if any(visible_point(x,p) for x in aa) and any(visible_point(x,p) for x in bb)]
            orthogonal=abs(distance*distance-r*r-R*R)<2e-3*max(distance,1)
            if visible:
                tangent=abs(distance-r-R)<2e-4
                dx,dy=abs(a['x']-b['x']),abs(a['y']-b['y'])
                permitted=(abs(r-S)<EPS and abs(R-M)<EPS and dx<2e-4 and abs(dy-P)<2e-4 or
                           abs(r-M)<EPS and abs(R-M)<EPS and abs(dx-P)<2e-4 and abs(dy-P)<2e-4)
                if not (orthogonal or tangent and permitted):raise ValueError('Nonorthogonal visible circles')
            if orthogonal and abs(r-M)<EPS and abs(R-L)<EPS:
                large=aa if a['r']>b['r'] else bb;small=bb[0] if a['r']>b['r'] else aa[0];base=large[0]
                phi=math.degrees(math.atan2(small['y']-base['y'],small['x']-base['x']))
                if abs(phi/90-round(phi/90))>1e-3:raise ValueError('Medium/large orientation')
                beta=math.degrees(math.atan2(M,L))
                inside=[any(on_arc(x,phi+t) for x in large) for t in (-beta+.01,0,beta-.01)]
                if not all(inside):raise ValueError('Missing large arc inside medium circle')
                wings=[any(on_arc(x,phi+t) for x in large) for t in (-(45+beta)/2,(45+beta)/2)]
                if len(set(wings))!=1:raise ValueError('Unequal outside wings in contact quadrant')
                outside=[any(on_arc(x,phi+t) for x in large) for t in (67.5,112.5,157.5,202.5,247.5,292.5)]
                if not any(outside):raise ValueError('Eclipse has no outside arc')
    center_rays={}
    for s in lines:
        dx,dy=s['x2']-s['x1'],s['y2']-s['y1'];length=math.hypot(dx,dy)
        if length<EPS:raise ValueError('Zero line')
        if not(abs(dx)<2e-4 or abs(dy)<2e-4 or abs(abs(dx)-abs(dy))<2e-4):raise ValueError('Non-45-degree line')
        if abs(dy)<2e-4 and min(abs(s['y1']-rail_origin-y) for y in (-P,0,P))>2e-4:raise ValueError('Horizontal stroke off rail')
        for c in arcs:
            for p in line_circle_hits(s,c):
                if visible_point(c,p) and abs((p[0]-c['x'])*dy-(p[1]-c['y'])*dx)>1e-3*max(1,length):
                    raise ValueError('Nonradial line/arc incidence')
            t=((c['x']-s['x1'])*dx+(c['y']-s['y1'])*dy)/(length*length)
            if abs(c['r']-S)<EPS:
                near=max(0,min(1,t))
                if math.hypot(s['x1']+near*dx-c['x'],s['y1']+near*dy-c['y'])<S-2e-4:
                    raise ValueError('Line enters small circle')
            if -EPS<t<1+EPS and math.hypot(s['x1']+t*dx-c['x'],s['y1']+t*dy-c['y'])<2e-4:
                if abs(c['r']-S)<EPS:
                    raise ValueError('Line through small-circle center')
                if min(abs(t),abs(1-t))*length>2e-4:raise ValueError('Line through circle center (diameter)')
                sign=1 if t<.5 else -1
                center=(round(c['x'],4),round(c['y'],4))
                center_rays.setdefault(center,set()).add(round(math.degrees(math.atan2(sign*dy,sign*dx)),3))
        for d in dots:
            t=max(0,min(1,((d['x']-s['x1'])*dx+(d['y']-s['y1'])*dy)/(length*length)))
            if math.hypot(s['x1']+t*dx-d['x'],s['y1']+t*dy-d['y'])<=d['r']+EPS:raise ValueError('Line touches dot')
    for d in dots:
        if abs(d['r']-D)>2e-4:raise ValueError('Dot radius')
        if any(abs(c['r']-S)<EPS and math.hypot(c['x']-d['x'],c['y']-d['y'])+d['r']<S+EPS for c in arcs):raise ValueError('Dot inside small circle')
    if any(len(angles)>1 for angles in center_rays.values()):raise ValueError('Multiple directions from circle center')
    # Reject crossings without a declared endpoint junction.
    for i,s in enumerate(lines):
        ax,ay=s['x1'],s['y1'];dx,dy=s['x2']-ax,s['y2']-ay
        for t in lines[:i]:
            bx,by=t['x1'],t['y1'];ux,uy=t['x2']-bx,t['y2']-by;den=dx*uy-dy*ux
            if abs(den)<EPS:continue
            a=((bx-ax)*uy-(by-ay)*ux)/den;b=((bx-ax)*dy-(by-ay)*dx)/den
            if EPS<a<1-EPS and EPS<b<1-EPS:raise ValueError('Crossing line interiors')
    if free_ends:check_free_ends(arcs,lines,continuations)
    return dict(arcs=len(arcs),lines=len(lines),dots=len(dots))
