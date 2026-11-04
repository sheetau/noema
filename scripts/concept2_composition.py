"""Scope-aware sharing and radius-based ink construction for concept 2 v2.

Native expansion and SVG ink inspection have separate result fields. Public
spelling components are retained; no sentence-number glyphs are generated.
"""
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import json
import math

from scripts import concept2_preview as old

U,S,M,L,F,P,PEN=old.U,old.S,old.M,old.L,old.F,old.P,old.PEN
D=(math.sqrt(2)-1)*U
EPS=1e-5
circle,arc,line,move,point,on_arc=old.circle,old.arc,old.line,old.move,old.point,old.on_arc
ROOT_NAMES=tuple(old.ROOT_FORMS)


def key(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def bounds(shapes):
    return old.bounds([circle(s['r'],s['x'],s['y']) if s['kind']=='dot' else s for s in shapes])


def simple_word(node):
    if node.get('kind')=='call' and not node['arguments']:return node['symbol'],'call',None
    if node.get('kind')=='function_ref':return node['symbol'],'function_ref',None
    if node.get('kind')=='quote' and node['body'].get('kind') in ('call','function_ref'):
        b=node['body']
        if b['kind']=='function_ref' or not b['arguments']:
            return b['symbol'],'quoted_ref' if b['kind']=='function_ref' else 'quoted_value',node.get('rank')
    return None


def contains_variable(value):
    if isinstance(value,dict):return value.get('kind')=='variable' or any(contains_variable(v) for v in value.values())
    return isinstance(value,list) and any(contains_variable(v) for v in value)


def lexical_cost(value,spellings):
    if isinstance(value,dict):return (len(spellings[value['symbol']]) if 'symbol' in value else 0)+sum(lexical_cost(v,spellings) for v in value.values())
    return sum(lexical_cost(v,spellings) for v in value) if isinstance(value,list) else 0


def make_plan(statement,dictionary,*,sharing=True):
    """Conservative local CSE: quotes/binders establish distinct namespaces."""
    spellings=dictionary['selected_spellings'];decl={d['name']:d for d in dictionary['native']['declarations']}
    statistics=Counter()
    def region(root,dot_counter=None):
        if dot_counter is None:dot_counter=[0]
        occurrences=[]
        def scan(v):
            if isinstance(v,dict):
                if 'kind' in v:occurrences.append(v)
                if v.get('kind') in ('quote','lambda','forall','exists','content'):return
                for x in v.values():scan(x)
            elif isinstance(v,list):
                for x in v:scan(x)
        scan(root);freq=Counter(key(v) for v in occurrences)
        unique={key(v):v for v in occurrences};first={}
        for i,v in enumerate(occurrences):first.setdefault(key(v),i)
        slots={};used_lanes=set()
        if sharing:
            candidates=[k for k,v in unique.items() if freq[k]>=3 and simple_word(v) and not contains_variable(v)]
            candidates.sort(key=lambda k:(-((freq[k]-1)*lexical_cost(unique[k],spellings)),first[k]))
            for k in candidates:
                v=unique[k];word=simple_word(v);sort=decl[word[0]]['result'] if word[1]=='call' else 'description'
                preferred=1 if sort=='situation' else -1 if sort=='individual' else 0
                lanes=[preferred]+[x for x in (-1,1,0) if x!=preferred]
                lane=next((x for x in lanes if x not in used_lanes),None)
                if lane is None:break
                slots[k]=lane;used_lanes.add(lane)
        modes=Counter((w[1],w[2]) for v in occurrences if (w:=simple_word(v)) and w[1].startswith('quoted_'))
        templates={}
        if sharing:
            for mode,n in modes.most_common():
                if n<2:continue
                lane=next((x for x in (0,-1,1) if x not in used_lanes),None)
                if lane is None:break
                templates[mode]=lane;used_lanes.add(lane)
        dots={};locals_={}
        if sharing:
            candidates=[k for k,v in unique.items() if k not in slots and freq[k]>=2 and first[k]>0
                        and lexical_cost(v,spellings)>=5 and not contains_variable(v)
                        and v.get('kind') not in ('lambda','forall','exists','content')]
            candidates.sort(key=lambda k:(-lexical_cost(unique[k],spellings),first[k]))
            for k in candidates[:3]:
                positions=[i for i,v in enumerate(occurrences) if key(v)==k]
                if freq[k]==2 and positions[-1]-positions[0]>=6 and len(dots)<2:
                    dots[k]=dot_counter[0];dot_counter[0]+=1
                else:locals_[k]=len(locals_)
        symbol_counts=Counter(v['symbol'] for v in occurrences if v.get('kind') in ('call','function_ref'))
        repeated_words=[s for s,n in symbol_counts.items() if sharing and n>=2 and len(spellings[s])>=3]
        word_names={s:i for i,s in enumerate(repeated_words[:8])}
        # Declared locally, never a global word-number assignment. The visible
        # definition carries the actual spelling, and the name has no meaning
        # outside this region.
        seen_roles=set();seen_templates=set();seen_dots=set();seen_locals=set();seen_words=set()
        def convert(v,*,allow_binding=True):
            if isinstance(v,list):return [convert(x) for x in v]
            if not isinstance(v,dict):return deepcopy(v)
            k=key(v)
            if allow_binding and k in slots:
                lane=slots[k]
                if k in seen_roles:statistics['role-use']+=1;return dict(form='role-use',lane=lane)
                seen_roles.add(k);statistics['role-definition']+=1
                return dict(form='role-definition',lane=lane,value=convert(v,allow_binding=False))
            if allow_binding and k in dots:
                label=dots[k]
                if k in seen_dots:statistics['dot-use']+=1;return dict(form='dot-use',label=label)
                seen_dots.add(k);statistics['dot-definition']+=1
                return dict(form='dot-definition',label=label,value=convert(v,allow_binding=False))
            if allow_binding and k in locals_:
                label=locals_[k]
                if k in seen_locals:statistics['local-use']+=1;return dict(form='local-use',label=label)
                seen_locals.add(k);statistics['local-definition']+=1
                return dict(form='local-definition',label=label,value=convert(v,allow_binding=False))
            word=simple_word(v)
            if word and (word[1],word[2]) in templates:
                mode=(word[1],word[2]);lane=templates[mode]
                payload=dict(kind='function_ref',symbol=word[0]) if word[1]=='quoted_ref' else dict(kind='call',symbol=word[0],arguments=[])
                if mode not in seen_templates:
                    seen_templates.add(mode);statistics['template-definition']+=1
                    return dict(form='template-definition',lane=lane,mode=word[1],rank=word[2],value=convert(payload,allow_binding=False))
                statistics['template-use']+=1
                return dict(form='template-use',lane=lane,value=convert(payload,allow_binding=False))
            if v.get('kind') in ('quote','lambda','forall','exists','content'):
                isolated=v['kind']=='quote'
                result=deepcopy(v);result['body']=dict(form='scope',quotation=isolated,body=region(v['body'],None if isolated else dot_counter))
                statistics['scope']+=1;return result
            result={}
            if v.get('kind') in ('call','function_ref'):
                symbol=v['symbol']
                if symbol in word_names:
                    label=word_names[symbol]
                    if symbol not in seen_words:
                        seen_words.add(symbol);statistics['word-definition']+=1
                        symbol_plan=dict(form='word-definition',label=label,parts=spellings[symbol])
                    else:
                        statistics['word-use']+=1;symbol_plan=dict(form='word-use',label=label)
                else:symbol_plan=dict(form='word',parts=spellings[symbol])
            for a,b in v.items():result[a]=symbol_plan if a=='symbol' else convert(b)
            return result
        result=convert(root)
        definitions={};uses=Counter()
        def inventory(v):
            if isinstance(v,list):
                for x in v:inventory(x)
            elif isinstance(v,dict):
                if v.get('form')=='scope':return
                if v.get('form')=='word-definition':definitions[v['label']]=v['parts']
                if v.get('form')=='word-use':uses[v['label']]+=1
                for x in v.values():inventory(x)
        inventory(result);remove=set()
        for label,parts in definitions.items():
            forms=spelling_units(parts)
            width=sum(bounds(x['shapes'])[2]-bounds(x['shapes'])[0] for x in forms)+M*(len(forms)-1)
            call_width=bounds(alias_shape(label,word=True))[2]-bounds(alias_shape(label,word=True))[0]
            declaration_width=call_width+M
            if uses[label]*(width-call_width)<=declaration_width:remove.add(label)
        def prune(v):
            if isinstance(v,list):return [prune(x) for x in v]
            if not isinstance(v,dict):return v
            if v.get('form')=='scope':return v
            if v.get('form') in ('word-definition','word-use') and v['label'] in remove:
                return dict(form='word',parts=definitions[v['label']])
            return {k:prune(x) for k,x in v.items()}
        return prune(result)
    plan=dict(form='scope',quotation=True,body=region(statement))
    assert expand_plan(plan,dictionary)==statement
    final=Counter()
    def count(v):
        if isinstance(v,list):
            for x in v:count(x)
        elif isinstance(v,dict):
            if v.get('form') not in (None,'word'):final[v['form']]+=1
            for x in v.values():count(x)
    count(plan)
    return dict(plan=plan,features=dict(final))


def expand_plan(plan,dictionary):
    aliases={tuple(r['parts']):r['symbol'] for r in dictionary['aliases']}
    def expand(v,state):
        if isinstance(v,list):return [expand(x,state) for x in v]
        if not isinstance(v,dict):return deepcopy(v)
        f=v.get('form')
        if f=='scope':
            isolated=v.get('quotation',True)
            child=({k:{} for k in ('roles','templates','dots','locals','words')} if isolated else
                   {k:(x if k=='dots' else deepcopy(x)) for k,x in state.items()})
            result=expand(v['body'],child)
            if isolated:assert all(x['used'] for x in child['dots'].values()),'Unpaired dot'
            return result
        if f=='word':return aliases[tuple(v['parts'])]
        if f in ('role-use','dot-use','local-use','word-use'):
            collection={'role-use':'roles','dot-use':'dots','local-use':'locals','word-use':'words'}[f]
            label=v['lane'] if f=='role-use' else v['label']
            value=state[collection][label]
            if f=='dot-use':assert not value['used'];value['used']=True;value=value['value']
            return deepcopy(value)
        if f in ('role-definition','dot-definition','local-definition','word-definition'):
            collection={'role-definition':'roles','dot-definition':'dots','local-definition':'locals','word-definition':'words'}[f]
            label=v['lane'] if f=='role-definition' else v['label']
            value=aliases[tuple(v['parts'])] if f=='word-definition' else expand(v['value'],state)
            if f=='dot-definition' and label in state['dots']:
                assert state['dots'][label]['used'],'Previous dot is still unpaired'
            if f=='role-definition':state['templates'].pop(label,None)
            state[collection][label]=dict(value=value,used=False) if f=='dot-definition' else deepcopy(value)
            return value
        if f in ('template-definition','template-use'):
            lane=v['lane']
            body=expand(v['value'],state)
            if f=='template-definition':
                state['templates'][lane]=(v['mode'],v['rank']);state['roles'].pop(lane,None)
            mode,rank=state['templates'][lane]
            assert body['kind']==('function_ref' if mode=='quoted_ref' else 'call')
            result=dict(kind='quote',body=body)
            if rank is not None:result['rank']=rank
            return result
        if f:raise ValueError('Unknown composition form '+f)
        return {k:expand(x,state) for k,x in v.items()}
    return expand(plan,{})


def eclipse(side=-1,contact=True,sectors=(0,1,6,7)):
    """Contact quadrant is indivisible; at least one other 45° sector stays."""
    phi=4 if side<0 else 0;contact_sectors={(phi-1)%8,phi%8}
    other=set(sectors)-contact_sectors
    if not other:raise ValueError('Eclipse needs an outside arc of at least 45 degrees')
    selected=other | (contact_sectors if contact else set())
    return sector_arcs(L,selected)+[circle(M,side*math.hypot(L,M))]


def sector_arcs(r,sectors,x=0.,y=0.):
    sectors=set(sectors)
    if not sectors:return []
    if sectors==set(range(8)):return [circle(r,x,y)]
    start=next(i for i in range(8) if i in sectors and (i-1)%8 not in sectors)
    result=[];run=None
    for j in range(start,start+9):
        included=j<start+8 and j%8 in sectors
        if included and run is None:run=j
        if not included and run is not None:result.append(arc(r,45*run,45*j,x,y));run=None
    return result


def connected_root(name):
    """Ordinary morphology uses joined arcs; separation is reserved for syntax."""
    shapes=deepcopy(old.ROOT_FORMS[name])
    # Legal small-circle intersections keep their original geometric form.
    if any(s['kind']=='arc' and abs(s['x'])>EPS for s in shapes):return shapes
    rings=[s for s in shapes if s['kind']=='arc']
    has_small=any(abs(s['r']-S)<EPS for s in rings)
    # Connect concentric layers at one radial direction supported by both.
    for inner,outer in zip(sorted({s['r'] for s in rings}),sorted({s['r'] for s in rings})[1:]):
        choices=[a for a in (270,90,0,180,45,315,135,225)
                 if any(abs(s['r']-inner)<EPS and on_arc(s,a) for s in rings)
                 and any(abs(s['r']-outer)<EPS and on_arc(s,a) for s in rings)]
        if choices:
            a=math.radians(choices[0]);shapes.append(line((inner*math.cos(a),inner*math.sin(a)),(outer*math.cos(a),outer*math.sin(a))))
    # Split arcs of a single ring acquire a small central joint when a radial
    # bridge can join them without passing through the small circle's center.
    if len(rings)>1 and len({s['r'] for s in rings})==1 and not has_small:
        shapes.append(circle(S))
        for segment in rings:
            angle=next((a for a in (0,180,270,90) if on_arc(segment,a)),segment['a'])
            t=math.radians(angle);r=segment['r']
            shapes.append(line((S*math.cos(t),S*math.sin(t)),(r*math.cos(t),r*math.sin(t))))
    return shapes


ROOT_FORMS={n:connected_root(n) for n in ROOT_NAMES}
LIGATURES=deepcopy(old.LIGATURES)
LIGATURES[('book','home','round')]=eclipse(-1,True,(5,6,7,0,1))
LIGATURES[('book','home','above')]=eclipse(-1,False,(5,6,7,0,1))
LIGATURES[('book','inside')]=eclipse(1,True,(1,2,3,4,5))
LIGATURES[('book','methodpossible')]=eclipse(1,False,(1,2,3,4,5))
# Connect the ordinary concentric compound instead of another empty C shell.
LIGATURES[('home','book')]=[circle(M),circle(S),arc(L,45,135),line((0,S),(0,L))]


def spelling_units(parts):
    names=tuple(map(old.root_name,parts));result=[];i=0
    while i<len(names):
        matches=[k for k in LIGATURES if names[i:i+len(k)]==k]
        word=max(matches,key=len) if matches else (names[i],)
        shapes=LIGATURES[word] if word in LIGATURES else ROOT_FORMS[word[0]]
        result.append(unit('/'.join(word),shapes,expansion=list(map(old.root_symbol,word))))
        i+=len(word)
    assert [x for u in result for x in u['expansion']]==parts
    return result


def unit(name,shapes,**kw):
    shapes=deepcopy(shapes);points=[]
    for s in shapes:
        if s['kind']=='arc' and min(abs(s['y']-y) for y in (-P,0,P))<EPS:
            for a in (0,180):
                if on_arc(s,a):points.append(point(s,a))
    if len(points)<2:raise ValueError('Unit has no published horizontal ports: '+name)
    return dict(name=name,shapes=shapes,entry=min(points),exit=max(points),**kw)


def role_shape(lane,definition=False,template=False):
    radius=M;shapes=[circle(radius)]
    if lane:
        distance=math.hypot(radius,S);shapes.append(circle(S,0,lane*distance))
        if definition:shapes.append(line((0,0),(0,lane*(distance-S))))
    else:
        shapes.append(circle(S))
        if definition:shapes.append(line((S,0),(M,0)))
    if template:
        direction=-lane if lane else -1
        shapes.append(line((0,direction*M),(0,direction*2*M)))
    return shapes


def alias_shape(label,definition=False,word=False):
    # Public local keys are oriented arc/ray combinations, introduced before use.
    if not 0<=label<8:raise ValueError('Local spelling key needs another scope')
    angle=label*45
    shapes=[arc(M,45+angle,315+angle)]
    if word:shapes.append(arc(L,135+angle,225+angle))
    shapes.append(circle(S))
    # Connected means a definition's payload; the unconnected small ring is a
    # pending call interface whose value comes from the declared local binding.
    if definition:
        theta=math.radians(angle+180)
        shapes.append(line((S*math.cos(theta),S*math.sin(theta)),(M*math.cos(theta),M*math.sin(theta))))
    return shapes


def dot_shape(label,source=True):
    if label==0:
        if source:return [circle(L),dict(kind='dot',x=0.,y=0.,r=D),circle(S,L+M+S),line((L,0),(L+M,0))]
        return [dict(kind='dot',x=-M-S-D,y=0.,r=D),circle(S)]
    if not 0<label<256:raise ValueError('Dot namespace exhausted')
    return [circle(L)]+sector_arcs(M,{i for i in range(8) if label&(1<<i)})+[dict(kind='dot',x=0.,y=0.,r=D),circle(S,L+M+S),line((L,0),(L+M,0))]


def operator(name):
    if name=='apply':
        return unit(name,deepcopy(old.OPERATORS['lambda'])+[line((-M,0),(-S,0))])
    if name=='exists':return unit(name,[arc(M,0,270),circle(S),arc(L,135,225)])
    if name=='argument-group':
        return unit(name,[circle(S,-M-S),circle(S,M+S),line((-M,0),(0,0)),line((0,0),(M,0)),line((0,-F),(0,F))])
    if name=='scope-hop':
        return unit(name,[circle(M),arc(L,135,225),line((-L,0),(-M,0)),line((0,0),(-M,0))])
    shapes=deepcopy(old.OPERATORS[name])
    if name=='not':shapes.append(circle(S))
    if name in ('quoted_ref','quoted_value','function_ref','not','evaluate'):
        # Keep the semantic distinction but join layers wherever a radial path
        # exists. Scope arcs and unfilled-role arcs deliberately stay separate.
        rings=[s for s in shapes if s['kind']=='arc']
        sizes=sorted({s['r'] for s in rings})
        for a,b in zip(sizes,sizes[1:]):
            angles=[t for t in (180,0,90,270) if all(any(abs(s['r']-r)<EPS and on_arc(s,t) for s in rings) for r in (a,b))]
            if angles:
                t=math.radians(angles[0]);shapes.append(line((a*math.cos(t),a*math.sin(t)),(b*math.cos(t),b*math.sin(t))))
    return unit(name,shapes)


def plan_units(plan):
    output=[];features=Counter();binders=[]
    def add(u):output.append(u)
    def scope(v):
        if isinstance(v,dict) and v.get('form')=='scope':return walk(v['body'])
        return walk(v)
    def word(v):
        f=v['form']
        if f=='word-use':add(unit('word-use',alias_shape(v['label'],word=True),binding=v['label']));return
        if f=='word-definition':add(unit('word-definition',alias_shape(v['label'],True,True),binding=v['label']))
        for u in spelling_units(v['parts']):add(u)
    def walk(v,level=0):
        if not isinstance(v,dict):raise ValueError('Expected expression')
        f=v.get('form')
        if f=='scope':return scope(v)
        if f in ('role-use','role-definition','template-use','template-definition'):
            defining=f.endswith('definition');template=f.startswith('template');lane=v['lane']
            if f=='role-use':
                add(unit(f,role_shape(lane),attach_lane=lane));return
            add(unit(f,role_shape(lane,defining,template),lane=lane))
            if template:
                if defining:
                    add(operator(v['mode']))
                    for _ in range(v.get('rank') or 0):add(operator('quotation-rank'))
                # Function-ref mode is already in the role declaration.
                body=v['value']
                if body.get('kind') in ('function_ref','call') and not body.get('arguments'):
                    word(body['symbol']);return
            walk(v['value'],level);return
        if f in ('local-use','local-definition','dot-use','dot-definition'):
            if f.startswith('dot'):
                add(unit(f,dot_shape(v['label'],f=='dot-definition'),silent=f=='dot-use' and v['label']==0,dot_key=v['label']))
            else:add(unit(f,alias_shape(v['label'],f=='local-definition'),binding=v['label']))
            if f.endswith('definition'):walk(v['value'],5)
            return
        k=v['kind']
        if k=='assert':walk(v['body']);return
        if k in old.PRECEDENCE:
            prec=old.PRECEDENCE[k];grouped=prec<level
            if grouped:add(operator('group-open'))
            walk(v['arguments'][0],prec+1);add(operator(k));walk(v['arguments'][1],prec)
            if grouped:add(operator('group-close'))
        elif k in ('call','function_ref'):
            if k=='function_ref':add(operator(k))
            word(v['symbol'])
            for i,a in enumerate(v.get('arguments',[])):
                if i and i%3==0:add(operator('argument-group'))
                walk(a,5)
        elif k=='quote':
            add(operator('quote-open'))
            for _ in range(v.get('rank',0)):add(operator('quotation-rank'))
            saved=binders[:];binders.clear();scope(v['body']);binders[:]=saved;add(operator('quote-close'))
        elif k in ('lambda','forall','exists'):
            parameters=v['parameters'] if k=='lambda' else [dict(name=v['variable'],sort=v['sort'])]
            if len(parameters)!=1 or parameters[0]['sort']!='individual':
                raise ValueError('Visible binder currently requires one individual parameter')
            add(operator(k));add(operator('group-open'))
            names=[p['name'] for p in v['parameters']] if k=='lambda' else [v['variable']]
            binders.extend(names);scope(v['body']);del binders[-len(names):];add(operator('group-close'))
        elif k=='not':add(operator(k));walk(v['arguments'][0],5)
        elif k=='variable':
            if v['name'] not in binders:raise ValueError('Unbound visible variable')
            add(operator(k));depth=binders[::-1].index(v['name'])
            for _ in range(depth):add(operator('scope-hop'))
        elif k=='evaluate':add(operator(k));walk(v['content'],5);walk(v['situation'],5)
        elif k=='apply':
            add(operator(k));add(operator('group-open'));walk(v['function'],5)
            for a in v['arguments']:walk(a,5)
            add(operator('group-close'))
        else:raise ValueError('Unimplemented visible constructor '+k)
    scope(plan)
    return output


def circle_hits(a,b):
    dx,dy=b['x']-a['x'],b['y']-a['y'];d=math.hypot(dx,dy);r,R=a['r'],b['r']
    if d<EPS or d>r+R+EPS or d<abs(r-R)-EPS:return []
    q=(r*r-R*R+d*d)/(2*d);h=math.sqrt(max(0,r*r-q*q))
    base=(a['x']+q*dx/d,a['y']+q*dy/d)
    return [(base[0]+s*h*-dy/d,base[1]+s*h*dx/d) for s in (-1,1)]


def visible_point(c,p):return on_arc(c,math.degrees(math.atan2(p[1]-c['y'],p[0]-c['x'])))


def line_circle_hits(s,c):
    ax,ay=s['x1']-c['x'],s['y1']-c['y'];dx,dy=s['x2']-s['x1'],s['y2']-s['y1']
    den=dx*dx+dy*dy;b=2*(ax*dx+ay*dy);q=ax*ax+ay*ay-c['r']**2;disc=b*b-4*den*q
    if den<EPS or disc < -EPS:return []
    return [(s['x1']+t*dx,s['y1']+t*dy) for t in ((-b-math.sqrt(max(0,disc)))/(2*den),(-b+math.sqrt(max(0,disc)))/(2*den)) if -EPS<=t<=1+EPS]


def ink_check(shapes,*,rail_origin=0.,allow_shift=False):
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
                contact=[any(on_arc(x,phi+t) for x in large) for t in (-44.9,-22.5,0,22.5,44.9)]
                if len(set(contact))!=1:raise ValueError('Contact quadrant was partially cut')
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
    return dict(arcs=len(arcs),lines=len(lines),dots=len(dots))


def attach_role(previous,lane):
    """Fuse a declared value's use port onto a real word, if legal."""
    shapes=deepcopy(previous['shapes'])
    if any(s['kind']=='dot' for s in shapes):return None
    candidates=sorted([s for s in shapes if s['kind']=='arc' and s['r']>=M-EPS],key=lambda s:-s['r'])
    for core in candidates:
        if lane:
            theta=90 if lane>0 else 270
            if not on_arc(core,theta):continue
            x,y=core['x'],core['y']+lane*math.hypot(core['r'],S)
            if any(s['kind']=='arc' and math.hypot(s['x']-x,s['y']-y)<EPS for s in shapes):continue
            extra=[circle(S,x,y)]
        else:
            if any(s['kind']=='arc' and s['r']<core['r'] and math.hypot(s['x']-core['x'],s['y']-core['y'])<EPS for s in shapes):continue
            extra=[circle(S,core['x'],core['y'])]
        try:ink_check(shapes+extra)
        except ValueError:continue
        result=deepcopy(previous);result['shapes']=shapes+extra;result.setdefault('attached_roles',[]).append(lane)
        return result
    return None


def fuse_units(units):
    result=[];fused=0
    for u in units:
        if 'attach_lane' in u and result and result[-1].get('expansion'):
            candidate=attach_role(result[-1],u['attach_lane'])
            if candidate is not None:result[-1]=candidate;fused+=1;continue
        result.append(u)
    return result,fused


def route_candidates(start,end_y):
    x,y=start;delta=end_y-y
    if abs(delta)<EPS:
        yield [(x,y),(x+M,y)],'direct'
        for sign in (-1,1):
            other=y+sign*P
            if -P-EPS<=other<=P+EPS:
                yield [(x,y),(x+M,y),(x+M+P,other),(x+2*M+P,other),(x+2*M+2*P,y),(x+3*M+2*P,y)],'rail-bridge'
    else:
        yield [(x,y),(x+M,y),(x+M+abs(delta),end_y),(x+2*M+abs(delta),end_y)],'rail-change'


def compile_units(raw_units):
    units,fused=fuse_units(raw_units);placed=[];shapes=[];links=[];moment=0.;mass=0.;rejections=Counter()
    for index,u in enumerate(units):
        local=u['shapes'];left,top,right,bottom=bounds(local)
        fixed=(u['name'].startswith(('role-','template-')) or
               any(s['kind']=='arc' and (s['r']>=L-EPS or abs(s['y'])>EPS) for s in local))
        choices=[]
        for rail in ([0.] if fixed else [0.,-P,P]):
            if index==0:
                routes=[([], 'start')];x=-left
            elif u.get('silent'):
                # A bare dot interrupts the ordinary ink flow. Both blank
                # collars are r2; no line ever touches the dot.
                x=placed[-1]['exit'][0]+M-left;routes=[([], 'dot-gap')]
            else:routes=route_candidates(placed[-1]['exit'],rail+u['entry'][1])
            for poly,kind in routes:
                if poly:x=poly[-1][0]-u['entry'][0]
                translated=move(local,x,rail)
                path=[line(a,b) for a,b in zip(poly,poly[1:])]
                recent=shapes[-180:]
                try:ink_check(recent+translated+path)
                except ValueError as e:rejections[str(e)]+=1;continue
                weight=sum(s['r']*(s.get('b',360)-s.get('a',0)) for s in local if s['kind'] in ('arc','dot'))
                delta=sum(s['r']*(s.get('b',360)-s.get('a',0))*(s['y']+rail) for s in local if s['kind'] in ('arc','dot'))
                score=(x+right-(placed[-1]['right'] if placed else 0))*.2+abs(moment+delta)/max(mass+weight,1)*.9
                if len(placed)>1 and abs(rail-placed[-1]['rail'])<EPS and abs(rail-placed[-2]['rail'])<EPS:score+=12
                choices.append((score,x,rail,translated,path,poly,kind,weight,delta))
        if not choices:raise ValueError(f'No radius-based placement at unit {index} {u["name"]}: {dict(rejections)}')
        _,x,rail,translated,path,poly,kind,weight,delta=min(choices,key=lambda z:z[:3])
        shapes.extend(translated+path)
        placed.append(dict(u,x=x,rail=rail,entry=(x+u['entry'][0],rail+u['entry'][1]),exit=(x+u['exit'][0],rail+u['exit'][1]),
                           shapes=translated,left=x+left,right=x+right))
        links.append(dict(points=poly,kind=kind));moment+=delta;mass+=weight
    metrics=ink_check(shapes)
    for link in links:
        p=link['points']
        if p:
            assert abs(math.dist(p[0],p[1])-M)<EPS
            assert abs(math.dist(p[-2],p[-1])-M)<EPS
    return dict(shapes=shapes,placed=placed,links=links,width=bounds(shapes)[2],fused_role_ports=fused,
                metrics=metrics,connection_radii_checked=sum(bool(x['points']) for x in links),balance=moment/max(mass*P,1))


def svg(shapes,*,width=None,height=None,pad=16,pen=PEN):
    import xml.etree.ElementTree as ET
    left,top,right,bottom=bounds(shapes)
    if width is None:width=right-left+2*pad;height=bottom-top+2*pad;shapes=move(shapes,pad-left,pad-top)
    ink=[s for s in shapes if s['kind']!='dot']
    root=ET.fromstring(old.svg(ink,width=width,height=height,pen=pen));group=list(root)[0]
    for s in shapes:
        if s['kind']=='dot':ET.SubElement(group,'{http://www.w3.org/2000/svg}circle',dict(cx=f'{s["x"]:.7f}',cy=f'{s["y"]:.7f}',r=f'{s["r"]:.7f}',fill='#203438',stroke='none'))
    ET.register_namespace('','http://www.w3.org/2000/svg')
    return ET.tostring(root,encoding='unicode')


def from_svg(raw):
    import xml.etree.ElementTree as ET
    root=ET.fromstring(raw);dots=[]
    for group in root.iter():
        for child in list(group):
            if child.tag.split('}')[-1]=='circle' and child.get('fill')=='#203438' and child.get('stroke')=='none':
                dots.append(dict(kind='dot',x=float(child.get('cx')),y=float(child.get('cy')),r=float(child.get('r'))));group.remove(child)
    return old.from_svg(ET.tostring(root,encoding='unicode'))+dots


def png(shapes,path,width,height,*,pen=PEN):
    from PIL import Image,ImageDraw
    ss=4;im=Image.new('RGB',(round(width*ss),round(height*ss)),'#fffffe');draw=ImageDraw.Draw(im)
    for s in shapes:
        if s['kind']=='dot':
            draw.ellipse(tuple(v*ss for v in (s['x']-s['r'],s['y']-s['r'],s['x']+s['r'],s['y']+s['r'])),fill='#203438');continue
        if s['kind']=='line':points=[(s['x1']*ss,s['y1']*ss),(s['x2']*ss,s['y2']*ss)]
        else:
            steps=max(8,int((s['b']-s['a'])*s['r']/60));points=[tuple(v*ss for v in point(s,s['a']+(s['b']-s['a'])*i/steps)) for i in range(steps+1)]
        draw.line(points,fill='#203438',width=max(1,round(pen*ss)),joint='curve')
    im.resize((round(width),round(height)),Image.Resampling.LANCZOS).save(path)


def fold(drawings,max_width):
    """Rebuild both ends of every continuation as complete r2 strokes."""
    rows=[];shapes=[];cursor=0.;last=None;entry_lanes=[];continuations=[]
    def flush(exit_lanes):
        nonlocal shapes,cursor,last,entry_lanes,continuations
        if shapes:
            rows.append(dict(shapes=shapes,width=bounds(shapes)[2],entry_lanes=entry_lanes,exit_lanes=exit_lanes,continuations=continuations))
        shapes=[];cursor=0.;last=None;entry_lanes=[];continuations=[]
    for di,drawing in enumerate(drawings):
        for ui,u in enumerate(drawing['placed']):
            local=move(u['shapes'],-u['x'],-u['rail']);left,top,right,bottom=bounds(local)
            e=(u['entry'][0]-u['x'],u['entry'][1]);out=(u['exit'][0]-u['x'],u['exit'][1]);y=u['rail']
            if not shapes:
                x=-left;path=[]
            elif ui==0:
                x=cursor+2*M-left;path=[]
            elif u.get('silent'):
                x=last['exit'][0]+M-left;path=[]
            else:
                # Use the already checked route family, without adjusting its
                # stubs to fill the page's remaining width.
                original=drawing['links'][ui]
                target=next((p for p,k in route_candidates(last['exit'],e[1]) if k==original['kind']),None)
                if target is None:raise ValueError('Fold lost its route family')
                x=target[-1][0]-e[0];path=[line(a,b) for a,b in zip(target,target[1:])]
            reserve=max(right,out[0]+M)
            look=ui+1
            while look<len(drawing['placed']) and drawing['placed'][look].get('silent'):
                nxt=drawing['placed'][look]
                reserve=max(reserve,nxt['right']-u['x'],nxt['exit'][0]-u['x']+M)
                look+=1
            if shapes and x+reserve>max_width:
                if ui==0:
                    flush([]);x=-left;path=[]
                elif u.get('silent'):
                    raise ValueError('Silent edge must have moved with its preceding unit')
                else:
                    prev_exit=last['exit'];stub=line(prev_exit,(prev_exit[0]+M,prev_exit[1]));shapes.append(stub)
                    continuations.append(dict(side='out',lane=prev_exit[1],length=M))
                    carry=prev_exit[1];flush([carry]);entry_lanes=[carry]
                    target=next(route_candidates((0.,carry),e[1]))[0]
                    x=target[-1][0]-e[0];path=[line(a,b) for a,b in zip(target,target[1:])]
                    continuations.append(dict(side='in',lane=carry,length=math.dist(target[0],target[1])))
            translated=move(local,x,y);shapes.extend(translated+path)
            cursor=max(cursor,x+right);last=dict(exit=(x+out[0],out[1]))
    flush([])
    for a,b in zip(rows,rows[1:]):
        if a['exit_lanes']!=b['entry_lanes']:raise ValueError('Continuation rail mismatch')
    for row in rows:
        ink_check(row['shapes'])
        assert all(abs(c['length']-M)<EPS for c in row['continuations'])
    return rows


def direction_shape(direction,*,large=False,outer=False):
    if not 0<=direction<8:raise ValueError('Eight directions')
    radius=L if large else M;t=direction*math.pi/4
    if large and direction%2:
        distance=F*math.sqrt(2)
    else:distance=radius
    start=radius if outer else 0.
    if outer and not(large and direction%2):distance=radius+M
    return [circle(radius),line((start*math.cos(t),start*math.sin(t)),(distance*math.cos(t),distance*math.sin(t)))]


def large_link_shape(side=1,lane=1,outer=True):
    if side not in (-1,1) or lane not in (-1,1):raise ValueError('Large link direction')
    radius=L/math.sqrt(2) if outer else 0.
    return [circle(L),line((side*radius,lane*radius),(side*F,lane*F)),circle(S,side*(L+M),lane*P)]


def continuation_witness(lanes):
    if not lanes or any(x not in (-1,0,1) for x in lanes):raise ValueError('Continuation lanes')
    left=[];right=[]
    for lane in lanes:
        left.extend([circle(S,0,lane*P),line((S,lane*P),(S+M,lane*P))])
        right.extend([line((0,lane*P),(M,lane*P)),circle(S,M+S,lane*P)])
    ink_check(left);ink_check(right)
    return left,right
