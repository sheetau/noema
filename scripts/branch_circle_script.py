"""Draft 04: typed syntax becomes branching words, separated at subtree boundaries.

Dictionary entries are whole, scoped Noema references, never character codes.
The complete syntax and dictionary accompany the geometric representation.
"""
from copy import deepcopy
from itertools import combinations
import json
import math

from scripts.circle_contact_script import (
    SMALL, MEDIUM, LARGE, PITCH, EPS, STROKE, circle, line, near,
    geometry_check as prior_geometry_check, line_topology,
)

VERSION='branch-circle-4-draft'
STROKE=1.9


def tree(value):
    """A lossless structural representation, including binding and quoted code."""
    if isinstance(value,dict):
        tag=value.get('kind','record')
        payload={}
        children=[]
        for key,item in value.items():
            if key=='kind':continue
            if isinstance(item,(dict,list)):
                children.append(dict(field=key,node=tree(item)))
            else:payload[key]=item
        return dict(tag=tag,payload=payload,children=children)
    if isinstance(value,list):
        return dict(tag='list',payload={},children=[dict(field=i,node=tree(v)) for i,v in enumerate(value)])
    return dict(tag='literal',payload={'value':value},children=[])


def restore(node):
    if node['tag']=='literal':return node['payload']['value']
    if node['tag']=='list':return [restore(c['node']) for c in node['children']]
    result={} if node['tag']=='record' else {'kind':node['tag']}
    result.update(node['payload'])
    result.update({c['field']:restore(c['node']) for c in node['children']})
    return result


def compact(node):
    """Argument list containers fuse into their application; other fields survive."""
    answer=deepcopy(node)
    children=[]
    for child in answer['children']:
        if child['field'] in ('arguments','items') and child['node']['tag']=='list':
            for item in child['node']['children']:
                children.append(dict(field=[child['field'],item['field']],node=compact(item['node'])))
        else:children.append(dict(field=child['field'],node=compact(child['node'])))
    answer['children']=children
    return answer


def expanded_tree(node):
    """Undo display fusion; this is syntax recovery, not optical recognition."""
    answer=deepcopy(node)
    groups={}
    children=[]
    for child in answer['children']:
        field=child['field']
        value=expanded_tree(child['node'])
        if isinstance(field,list):
            key,index=field
            if key not in groups:
                container=dict(field=key,node=dict(tag='list',payload={},children=[]))
                groups[key]=container;children.append(container)
            groups[key]['node']['children'].append(dict(field=index,node=value))
        else:children.append(dict(field=field,node=value))
    # Empty argument/item lists must not disappear from the raw source.
    for field in node.get('empty_lists',[]):
        children.append(dict(field=field,node=dict(tag='list',payload={},children=[])))
    answer['children']=children
    answer.pop('empty_lists',None)
    return answer


def display_tree(value):
    # compact recurses; record empty lists on every source node first.
    def annotate(node):
        node=deepcopy(node)
        node['empty_lists']=[c['field'] for c in node['children'] if c['field'] in ('arguments','items')
                            and c['node']['tag']=='list' and not c['node']['children']]
        for c in node['children']:c['node']=annotate(c['node'])
        return node
    return compact(annotate(tree(value)))


def signature(node):
    return json.dumps([node['tag'],node['payload']],ensure_ascii=False,sort_keys=True,separators=(',',':'))


def geometry_check(shapes,paths):
    prior_geometry_check(shapes)
    circles=[s for s in shapes if s['kind']=='circle']
    lines=[s for s in shapes if s['kind']=='line']
    # Each circle can interact with at most ONE other circle, including nesting.
    for a in circles:
        overlaps=sum(b is not a and math.hypot(a['x']-b['x'],a['y']-b['y'])<=a['r']+b['r']+EPS for b in circles)
        if overlaps>1:raise ValueError('A circle interacts with more than one circle')
        if near(a['r'],LARGE):
            if not any(_on_segment((a['x'],a['y']),s) for s in lines):
                raise ValueError('Large circle lacks a center stroke')
            for path in paths:
                for p,q in zip(path,path[1:]):
                    if not near(abs(p[0]-q[0]),abs(p[1]-q[1])) or near(p[0],q[0]):continue
                    s=line(p,q)
                    if _touches_circle(s,a):
                        if len(path)!=2 or not any(near(abs(v[1]-a['y']),LARGE) for v in (p,q)):
                            raise ValueError('A large-circle diagonal must terminate freely at its top/bottom height')
                        tip=next(v for v in (p,q) if near(abs(v[1]-a['y']),LARGE))
                        if any(other!=s and _on_segment(tip,other) for other in lines):
                            raise ValueError('Large-circle diagonal endpoint is not free')
    for path in paths:
        turns=[]
        for a,b,c in zip(path,path[1:],path[2:]):
            u=(b[0]-a[0],b[1]-a[1]);v=(c[0]-b[0],c[1]-b[1])
            turns.append(abs(u[0]*v[0]+u[1]*v[1])<EPS)
        if any(a and b for a,b in zip(turns,turns[1:])):
            raise ValueError('Consecutive right-angle turns')
    _check_joined_turns(lines)
    return True


def _check_joined_turns(lines):
    # Detect the same violation even if a caller splits a stroke into paths.
    ends=[((s['x1'],s['y1']),(s['x2'],s['y2'])) for s in lines]
    points={p for pair in ends for p in pair}
    adjacency={}
    for s,(a,b) in zip(lines,ends):
        cuts=sorted((p for p in points if _on_segment(p,s)),key=lambda p:math.dist(a,p))
        for p,q in zip(cuts,cuts[1:]):
            if math.dist(p,q)<EPS:continue
            p=tuple(round(x,6) for x in p);q=tuple(round(x,6) for x in q)
            adjacency.setdefault(p,set()).add(q);adjacency.setdefault(q,set()).add(p)
    elbows=set()
    for p,neighbors in adjacency.items():
        if len(neighbors)!=2:continue
        a,b=neighbors
        if abs((a[0]-p[0])*(b[0]-p[0])+(a[1]-p[1])*(b[1]-p[1]))<1e-4:elbows.add(p)
    if any(q in elbows for p in elbows for q in adjacency[p]):
        raise ValueError('Consecutive right-angle turns across joined paths')


def _on_segment(point,s):
    a=(s['x1'],s['y1']);b=(s['x2'],s['y2'])
    return abs(math.dist(a,point)+math.dist(point,b)-math.dist(a,b))<EPS


def _touches_circle(s,c):
    dx,dy=s['x2']-s['x1'],s['y2']-s['y1']
    length2=dx*dx+dy*dy
    t=max(0,min(1,((c['x']-s['x1'])*dx+(c['y']-s['y1'])*dy)/length2))
    return math.hypot(c['x']-s['x1']-t*dx,c['y']-s['y1']-t*dy)<=c['r']+EPS


class Word:
    def __init__(self):self.shapes=[];self.paths=[];self.nuclei=[]

    def stroke(self,points):
        self.paths.append(points)
        self.shapes.extend(line(a,b) for a,b in zip(points,points[1:]) if math.dist(a,b)>EPS)

    def nucleus(self,x,y,radius,code,context=0,central=False):
        # Four axial incidences are combined, then reflected by argument role.
        # A reference is represented as one composed signature, not its spelling.
        if central:
            # Reserve vertical incidences for the head signature: its required
            # horizontal argument stems must not erase lexical distinctions.
            bits=(2 if code%4&1 else 0)|(8 if code%4&2 else 0)
            nested=bool((code//4)%2)
        else:
            bits=code%15+1
            nested=bool((code//15)%2)
        if nested and near(radius,SMALL):radius=MEDIUM
        self.shapes.append(circle(x,y,radius))
        if nested:self.shapes.append(circle(x,y,SMALL))
        directions=[(1,0),(0,1),(-1,0),(0,-1)]
        for i,(dx,dy) in enumerate(directions):
            if bits&(1<<i):
                if context%2:dy=-dy
                self.stroke([(x,y),(x+dx*radius,y+dy*radius)])
        self.nuclei.append(dict(x=x,y=y,radius=radius,code=code,context=context,central=central))
        return radius

    def build(self,head,children,codes,bank=0,style=None):
        count=len(children)
        address_gap=8*(codes[signature(head)]//8)
        root_radius=LARGE if count>=2 or any(codes[signature(c['node'])]>=15 for c in children) else MEDIUM
        # The head remains on the middle rail. Leaves are short upper/lower
        # branches; third arguments sit opposite the fork on the middle rail.
        style=style or {'equal':'symmetric','or':'opposed','implies':'conditional'}.get(head['tag'],'fork')
        bilateral=count==2 and style in ('symmetric','opposed','vertical','conditional')
        root_x=160.0 if bilateral else 128.0 if count==3 else 48.0
        root=self.nucleus(root_x,32,root_radius,codes[signature(head)],bank,True)
        ordered=list(enumerate(children))
        if bilateral:
            for index,child in ordered:
                side=-1 if index==0 else 1
                vertical=0 if style=='symmetric' or (style=='conditional' and index==0) else (-1 if index==0 else 1)
                if not vertical:
                    x,y=root_x+side*(108+address_gap),32
                    r=self.nucleus(x,y,SMALL,codes[signature(child['node'])],index)
                    self.stroke([(root_x,32),(x-side*r,y)])
                else:
                    fork=root_x+side*(root+18+address_gap)
                    x,y=fork+side*64,32+vertical*32
                    r=self.nucleus(x,y,SMALL,codes[signature(child['node'])],index)
                    self.stroke([(root_x,32),(fork,32),(fork+side*32,y),(x-side*r,y)])
            ordered=[]
        if count==3:
            index,child=ordered.pop(0)
            r=self.nucleus(40,32,SMALL,codes[signature(child['node'])],index)
            self.stroke([(40+r,32),(root_x,32)])
        if (ordered and count==1 and style=='event' and near(root,MEDIUM)
                and codes[signature(head)]<4 and codes[signature(ordered[0][1]['node'])]<15):
            # A unary local process can share a single s/m contact with its
            # place. This narrowly scoped rule keeps tangency uncommon.
            index,child=ordered[0]
            self.nucleus(root_x,0,SMALL,codes[signature(child['node'])],index)
            self.stroke([(root_x,32),(root_x,0)])
            ordered=[]
        elif ordered and count==1 and style in ('event','containment'):
            index,child=ordered[0]
            x=root_x+root+62+address_gap
            r=self.nucleus(x,32,SMALL,codes[signature(child['node'])],index)
            self.stroke([(root_x,32),(x-r,32)])
            ordered=[]
        elif ordered:
            fork=root_x+root+18+address_gap
            # Every branch begins axially from a large circle. The diagonal is
            # outside it, and the Y fork has no continuing forward shaft.
            self.stroke([(root_x,32),(fork,32)])
            for j,(index,child) in enumerate(ordered):
                side=-1 if j==0 else 1
                if count==1 and (codes[signature(head)]+bank)%2:side=1
                x,y=fork+64,32+side*32
                r=self.nucleus(x,y,SMALL,codes[signature(child['node'])],index)
                # Diagonal leaves the fork, then horizontal enters the circle.
                # Only one 45-degree bend; no repeated right angles.
                self.stroke([(fork,32),(fork+32,y),(x-r,y)])
        if not ordered:
            self.stroke([(root_x-root-address_gap,32),(root_x,32)])
        self.width=max(s['x']+s['r'] for s in self.shapes if s['kind']=='circle')+20
        # Remove coincident strokes before topology analysis.
        unique={json.dumps(s,sort_keys=True):s for s in self.shapes}
        self.shapes=list(unique.values())
        geometry_check(self.shapes,self.paths)
        return self


def compile_expression(value,styles=None,reference_order=None):
    ast=display_tree(value)
    keys=[]
    bindings={}
    def collect(node):
        key=signature(node)
        if key not in keys:keys.append(key)
        if node['tag'] in ('forall','exists','content') and 'variable' in node['payload']:
            bindings.setdefault(node['payload']['variable'],len(bindings))
        if node['tag']=='record' and 'name' in node['payload']:
            bindings.setdefault(node['payload']['name'],len(bindings))
        for child in node['children']:collect(child['node'])
    collect(ast)
    reference_order=reference_order or {}
    def stable_key(key):
        tag,payload=json.loads(key)
        stable={}
        for field,item in payload.items():
            if field in ('symbol','identity'):
                if item not in reference_order:raise ValueError('Missing reference registry: '+item)
                stable[field]=reference_order[item]
            elif field in ('name','variable') and item in bindings:stable[field]=bindings[item]
            else:stable[field]=item
        return tag,tuple((field,type(item).__name__,item) for field,item in sorted(stable.items()))
    # Declaration/quantity identity survives argument reordering. First-use
    # assignment would make give(A,book,B) indistinguishable from give(B,book,A).
    keys.sort(key=stable_key)
    if len(keys)>30:
        raise ValueError('This display dictionary exceeds 30 distinct references; split at an explicit assertion boundary')
    codes={key:i for i,key in enumerate(keys)}
    words=[]
    def emit(node,path=()):
        children=node['children']
        banks=[children[i:i+3] for i in range(0,len(children),3)] or [[]]
        for bank,items in enumerate(banks):
            style=(styles or {}).get(node['payload'].get('symbol'))
            word=Word().build(node,items,codes,bank,style)
            words.append(dict(path=list(path),bank=bank,tag=node['tag'],payload=node['payload'],
                              fields=[c['field'] for c in items],shapes=word.shapes,paths=word.paths,
                              nuclei=word.nuclei,width=word.width))
        # Atomic arguments are fused into the parent's branches. Structured
        # arguments continue as separate words, in exact field/argument order.
        for i,child in enumerate(children):
            if child['node']['children']:emit(child['node'],path+(i,))
    # On this specimen sheet the enclosing section explicitly declares normal
    # and Kant statements as assertions. Fuse that redundant outer wrapper.
    if ast['tag']=='assert' and len(ast['children'])==1 and ast['children'][0]['field']=='body':
        emit(ast['children'][0]['node'],(0,))
        assertion_wrapper=True
    else:
        emit(ast);assertion_wrapper=False
    assert restore(expanded_tree(ast))==value
    return dict(version=VERSION,source=deepcopy(value),tree=ast,assertion_wrapper=assertion_wrapper,
                dictionary=[json.loads(key) for key in keys],words=words,
                reference_order={payload[field]:reference_order[payload[field]]
                                 for _,payload in (json.loads(key) for key in keys)
                                 for field in ('symbol','identity') if field in payload})


def pack_lines(compiled,width,scale=.52):
    rows=[];row=[];x=0
    for i,word in enumerate(compiled['words']):
        w=word['width']*scale
        if w>width:raise ValueError('Word exceeds the requested line width')
        if row and x+w>width:rows.append(row);row=[];x=0
        row.append(dict(word=i,x=x));x+=w+16*scale
    if row:rows.append(row)
    return rows
