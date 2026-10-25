"""Circle-led contextual writing, with the revised concept's contact geometry.

The semantic compiler of draft 02 is reused unchanged. This module replaces
its geometry, line spine, logical symbols and arbitrary circle overlaps.
"""
from copy import deepcopy
import json
import math
from html import escape

from noema.constructed import parse
from scripts.connected_circle_script import expand, semantic_plan, validate_profile, packed_expansion

VERSION = 'circle-contact-3-draft'
PITCH = 32.0
MEDIUM = PITCH / math.sqrt(2)
SMALL = PITCH - MEDIUM
LARGE = 2 * MEDIUM - SMALL
RADII = (SMALL, MEDIUM, LARGE)
RAILS = (0.0, PITCH, 2 * PITCH)
EPS = 1e-6
STROKE = 1.45


def near(a, b):
    return abs(a-b) < EPS


def circle(x, y, r):
    return dict(kind='circle', x=x, y=y, r=r)


def line(a, b):
    return dict(kind='line', x1=a[0], y1=a[1], x2=b[0], y2=b[1])


def legal_pair(a, b):
    dx, dy = abs(a['x']-b['x']), abs(a['y']-b['y'])
    distance = math.hypot(dx, dy)
    r, s = a['r'], b['r']
    if distance > r+s+EPS:
        return True
    if near(distance, 0):
        return not near(r, s)
    if not near(r, s) and (near(distance, r) or near(distance, s)):
        return True  # One circumference passes through the other's center.
    if near(distance, r+s) and near(dy, PITCH):
        return ((near(min(r,s), SMALL) and near(max(r,s), MEDIUM) and near(dx, 0))
                or (near(r, MEDIUM) and near(s, MEDIUM) and near(dx, PITCH)))
    return False


def line_error(s, circles):
    ax, ay, bx, by = (s[k] for k in ('x1','y1','x2','y2'))
    dx, dy = bx-ax, by-ay
    length = math.hypot(dx, dy)
    if length < EPS:
        return 'zero length'
    if not (near(dx, 0) or near(dy, 0) or near(abs(dx), abs(dy))):
        return 'line direction'
    if near(dy, 0) and not any(near(ay, y) for y in RAILS):
        return 'horizontal outside rails'
    for c in circles:
        vx, vy = c['x']-ax, c['y']-ay
        projection = (vx*dx+vy*dy)/length
        perpendicular = abs(vx*dy-vy*dx)/length
        closest = math.hypot(perpendicular, max(0, -projection, projection-length))
        if closest > c['r']+EPS:
            continue
        if perpendicular > EPS:
            return 'nonradial circle contact'
        # A stroke can stop only at a center or circumference, never midway.
        for endpoint in (projection, projection-length):
            if EPS < abs(endpoint) < c['r']-EPS:
                return 'stroke terminates inside circle away from center'
    return None


def geometry_check(shapes):
    circles = [s for s in shapes if s['kind']=='circle']
    if any(s['kind'] not in ('circle','line') for s in shapes):
        raise ValueError('This draft deliberately uses no dots')
    for c in circles:
        if not any(near(c['r'],r) for r in RADII) or not any(near(c['y'],y) for y in RAILS):
            raise ValueError('Circle size/rail')
        if near(c['r'], LARGE) and not near(c['y'], PITCH):
            raise ValueError('Large circle must be on middle rail')
    for i, a in enumerate(circles):
        for b in circles[i+1:]:
            if not legal_pair(a,b):
                raise ValueError('Forbidden circle arrangement: '+repr((a,b)))
    for s in shapes:
        if s['kind']=='line':
            error=line_error(s,circles)
            if error:
                raise ValueError(error+': '+repr(s))
    topology=line_topology([s for s in shapes if s['kind']=='line'])
    if topology['cycles'] or topology['arrows']:
        raise ValueError('Line-only loop or arrow')
    return True


def line_topology(segments):
    """Split intersections/overlaps before testing the actual line-only graph."""
    ends=[[(s['x1'],s['y1']),(s['x2'],s['y2'])] for s in segments]
    cuts=[list(pair) for pair in ends]
    cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
    sub=lambda a,b:(a[0]-b[0],a[1]-b[1])
    for i,(a,b) in enumerate(ends):
        d=sub(b,a)
        for j in range(i):
            c,e=ends[j]
            v=sub(e,c)
            denominator=cross(d,v)
            if abs(denominator)>EPS:
                t=cross(sub(c,a),v)/denominator
                u=cross(sub(c,a),d)/denominator
                if -EPS<=t<=1+EPS and -EPS<=u<=1+EPS:
                    point=(a[0]+t*d[0],a[1]+t*d[1])
                    cuts[i].append(point);cuts[j].append(point)
            elif abs(cross(sub(c,a),d))<EPS:
                for point in (a,b,c,e):
                    if (min(a[0],b[0])-EPS<=point[0]<=max(a[0],b[0])+EPS
                            and min(a[1],b[1])-EPS<=point[1]<=max(a[1],b[1])+EPS
                            and min(c[0],e[0])-EPS<=point[0]<=max(c[0],e[0])+EPS
                            and min(c[1],e[1])-EPS<=point[1]<=max(c[1],e[1])+EPS):
                        cuts[i].append(point);cuts[j].append(point)
    edges=set()
    for points,(a,b) in zip(cuts,ends):
        points=sorted({(round(x,6),round(y,6)) for x,y in points},key=lambda p:math.dist(a,p))
        edges.update(tuple(sorted((p,q))) for p,q in zip(points,points[1:]) if math.dist(p,q)>EPS)
    parents={p:p for pair in edges for p in pair}
    adjacency={p:set() for p in parents}
    def root(p):
        while parents[p]!=p:
            parents[p]=parents[parents[p]];p=parents[p]
        return p
    cycles=0
    for p,q in edges:
        adjacency[p].add(q);adjacency[q].add(p)
        a,b=root(p),root(q)
        if a==b:cycles+=1
        else:parents[a]=b
    arrows=0
    for p,neighbors in adjacency.items():
        angles={round(math.atan2(q[1]-p[1],q[0]-p[0])/(math.pi/4))%8 for q in neighbors}
        arrows+=any({k,(k+1)%8,(k-1)%8}<=angles for k in angles)
    return dict(components=len({root(p) for p in parents}),cycles=cycles,arrows=arrows)


class Composer:
    def __init__(self):
        self.nodes=[]
        self.links=[]
        self.scopes=[]

    def add(self, radii, y, kind, link='ordinary', start='rim', end='rim', **properties):
        index=len(self.nodes)
        self.nodes.append(dict(radii=sorted(set(radii)), y=y, kind=kind, **properties))
        if index:
            self.links.append(dict(a=index-1,b=index,relation=link,start=start,end=end))
        return index

    def reference(self, reference, y, role, link='argument'):
        first=len(self.nodes)
        for mark in reference['marks']:
            # Local referent signatures, not spelling or alphabet codepoints.
            # A ring mark can be absorbed into the same nucleus as a modifier.
            radii=[SMALL] if mark=='dot' else [SMALL,MEDIUM]
            self.add(radii,y,'reference',link=link,identity=reference['identity'],role=role)
            link='identity'
        return first,len(self.nodes)-1

    def build(self, plan, depth=0):
        if plan['kind']=='bundle':
            a,b=plan['participants']
            reverse=tuple(a['marks'])>tuple(b['marks'])
            left,right=(b,a) if reverse else (a,b)
            flip=reverse ^ bool(depth%2)
            source_y=64.0 if flip else 0.0
            target_y=64.0-source_y
            first,_=self.reference(left,source_y,'target' if reverse else 'source')
            last_feature=None
            for ri,relation in enumerate(plan['relations']):
                for fi,feature in enumerate(relation['features']):
                    if feature=='positive' and fi and last_feature is not None:
                        # Positivity changes the existing entry stroke. No extra
                        # ring, fixed modifier glyph, or advance is inserted.
                        if 'positive' in self.nodes[last_feature].get('absorbed',[]):
                            raise ValueError('Repeated positive modifier has no distinct geometric reading yet')
                        self.links[last_feature-1]['end']='center'
                        self.nodes[last_feature].setdefault('absorbed',[]).append(feature)
                        continue
                    if feature=='action':
                        # A terminal dependence closes a two-role relation. An
                        # action that also carries an outcome/next relation is
                        # a shared nucleus and occupies the larger middle ring.
                        shared=('benefit' in relation['features'] or ri<len(plan['relations'])-1)
                        radius,y=(LARGE if shared else MEDIUM),PITCH
                    elif feature=='prospect':
                        radius,y=MEDIUM,PITCH if ri==0 else source_y
                    elif feature=='dependence':
                        radius,y=MEDIUM,target_y
                    elif feature=='benefit':
                        radius,y=SMALL,PITCH
                    else:
                        raise ValueError('Unsupported feature operation: '+feature)
                    relation_kind=('fusion' if ri and fi==0 else
                                   'dependence' if feature=='dependence' else
                                   'benefit' if feature=='benefit' else 'argument')
                    last_feature=self.add([radius],y,'semantic',link=relation_kind,
                                          start='center' if feature=='dependence' else 'rim',
                                          feature=feature,relation_index=ri)
            if self.nodes[-1].get('feature')=='benefit' and len(right['marks'])==1:
                # Predicate feature + participant share ONE circle center.
                self.nodes[-1].update(identity=right['identity'],role='source' if reverse else 'target')
                if right['marks'][0]=='ring':
                    self.nodes[-1]['radii'].append(MEDIUM)
                self.nodes[-1]['absorbed']=['participant']
            else:
                self.reference(right,target_y,'source' if reverse else 'target')
            return first,len(self.nodes)-1
        kind=plan['kind']
        # Logical force lives in paired attachment choices, never in an arrow,
        # diamond, slash or closed line-only path. Matching ports delimit scope.
        entry,exit_mode={'and':('rim','rim'),'or':('center','rim'),
                         'implies':('rim','center'),'not':('center','center')}[kind]
        y=0.0 if depth%2 else 64.0
        first=self.add([SMALL],y,'scope',link='scope',side='entry',operator=kind,depth=depth)
        for child in plan['children']:
            a,b=self.build(child,depth+1)
            self.links[a-1]['relation']='scope'
        last=self.add([SMALL],64.0-y,'scope',link='scope',end=exit_mode,side='exit',operator=kind,depth=depth)
        self.links[first]['start']=entry
        self.scopes.append(dict(kind=kind,entry=first,exit=last,entry_port=entry,exit_port=exit_mode))
        return first,last

    def layout(self):
        circles=[]
        strokes=[]
        for i,node in enumerate(self.nodes):
            node['radius']=max(node['radii'])
            if not i:
                candidates=[48.0]
            else:
                p=self.nodes[i-1]
                edge=self.links[i-1]
                dy=abs(node['y']-p['y'])
                candidates=[]
                r,s=p['radius'],node['radius']
                if edge['relation'] not in ('scope','identity'):
                    # Contact choices express binding/composition. The actual
                    # allograph is selected against ALL neighboring circles.
                    if near(dy,PITCH):
                        if near(min(r,s),SMALL) and near(max(r,s),MEDIUM):
                            candidates.append(p['x'])
                        if near(r,MEDIUM) and near(s,MEDIUM):
                            candidates.append(p['x']+PITCH)
                    if edge['relation'] in ('fusion','benefit','dependence') and not near(r,s):
                        for distance in (max(r,s),min(r,s)):
                            if distance>=dy:
                                candidates.append(p['x']+math.sqrt(max(0,distance*distance-dy*dy)))
                # Compact separated alternatives. Expansion is a routing
                # fallback, not random decorative variation.
                gap=r+s+12+dy*.35
                candidates.extend(p['x']+gap+12*k for k in range(25))
            placed=False
            for x in candidates:
                trial=[circle(x,node['y'],r) for r in node['radii']]
                if any(not legal_pair(a,b) for a in trial for b in circles):
                    continue
                combined=circles+trial
                if any(line_error(s,combined) for s in strokes):
                    continue
                route=[]
                if i:
                    route=self.route(self.nodes[i-1],dict(node,x=x),self.links[i-1],combined)
                    if route is None:
                        continue
                if len(node['radii'])>1:
                    # Concentric identity parts remain connected by a radial
                    # arm. Its orientation is solved against neighboring rings.
                    bridge=None
                    for vx,vy in ((1,0),(-1,0),(0,1),(0,-1),(.5**.5,.5**.5),(-.5**.5,.5**.5)):
                        candidate=line((x,node['y']),(x+vx*node['radius'],node['y']+vy*node['radius']))
                        if not line_error(candidate,combined):
                            bridge=candidate;break
                    if bridge is None:
                        continue
                    route=route+[bridge]
                node['x']=x
                if i:
                    self.links[i-1]['strokes']=route
                    self.links[i-1]['placement']='contact' if not route else 'routed'
                circles=combined
                strokes.extend(route)
                placed=True
                break
            if not placed:
                raise ValueError('Cannot place semantic nucleus without breaking geometry')
        shapes=circles+strokes
        geometry_check(shapes)
        return dict(nodes=self.nodes,links=self.links,scopes=self.scopes,shapes=shapes,
                    width=max(c['x']+c['r'] for c in circles)+40)

    @staticmethod
    def route(a,b,edge,circles):
        ax,ay,bx,by=a['x'],a['y'],b['x'],b['y']
        dx,dy=bx-ax,by-ay
        distance=math.hypot(dx,dy)
        touching=distance<=a['radius']+b['radius']+EPS
        if touching and edge['start']==edge['end']=='rim':
            return []  # The actual circle contact carries this incidence.
        paths=[]
        if near(dx,0) or near(dy,0) or near(abs(dx),abs(dy)):
            paths.append([(ax,ay),(bx,by)])
        if dx>=abs(dy):
            paths.extend([[(ax,ay),(bx-abs(dy),ay),(bx,by)],
                          [(ax,ay),(ax+abs(dy),by),(bx,by)]])
            for fraction in (.5,.3,.7):
                bend=ax+(dx-abs(dy))*fraction
                paths.append([(ax,ay),(bend,ay),(bend+abs(dy),by),(bx,by)])
        for fraction in (.5,.35,.65):
            middle=ax+dx*fraction
            paths.append([(ax,ay),(middle,ay),(middle,by),(bx,by)])
        for path in paths:
            path=[p for j,p in enumerate(path) if not j or math.dist(p,path[j-1])>EPS]
            if len(path)<2:
                continue
            # Clip to each circumference; never send a shared baseline through
            # every circle. Center modes are explicit grammatical incidences.
            if edge['start']=='rim':
                length=math.dist(path[0],path[1])
                if length<a['radius']-EPS:
                    continue
                path[0]=tuple(path[0][k]+(path[1][k]-path[0][k])*a['radius']/length for k in (0,1))
            if edge['end']=='rim':
                length=math.dist(path[-1],path[-2])
                if length<b['radius']-EPS:
                    continue
                path[-1]=tuple(path[-1][k]+(path[-2][k]-path[-1][k])*b['radius']/length for k in (0,1))
            segments=[line(u,v) for u,v in zip(path,path[1:]) if math.dist(u,v)>EPS]
            if not any(line_error(s,circles) for s in segments):
                return segments
        return None


def compile_document(text,profile):
    document=parse(text)
    validate_profile(document,profile)
    declarations={d['name']:d for d in document['declarations']}
    sentences=[]
    for statement in document['statements']:
        if statement['kind']!='assert':
            raise ValueError('Only assertions are supported by this design trial')
        expanded=expand(statement['body'],declarations)
        plan=semantic_plan(expanded,profile)
        composer=Composer()
        composer.build(plan)
        sentence=composer.layout()
        sentence.update(plan=plan,expanded_dag=packed_expansion(expanded))
        sentences.append(sentence)
    return dict(version=VERSION,source=document,profile=deepcopy(profile),sentences=sentences)


def svg(result,index):
    s=result['sentences'][index]
    body=[]
    for shape in s['shapes']:
        if shape['kind']=='circle':
            body.append(f'<circle cx="{shape["x"]}" cy="{shape["y"]}" r="{shape["r"]}"/>')
        else:
            body.append('<line '+ ' '.join(f'{k}="{shape[k]}"' for k in ('x1','y1','x2','y2'))+'/>')
    metadata=escape(json.dumps(dict(version=VERSION,source=result['source'],profile=result['profile'],sentence=index),ensure_ascii=False))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -24 {s["width"]} 112">'
            f'<metadata>{metadata}</metadata><g stroke="#172a2b" stroke-width="{STROKE}" stroke-linecap="round" fill="none">'
            +''.join(body)+'</g></svg>\n')
