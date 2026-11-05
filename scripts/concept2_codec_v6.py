"""A public glyph grammar, syntax writer, and ink-only SVG reader.

The reader accepts only SVG ink and the shared dictionary. No source statement,
expected token tape, placement records, or statement-specific glyph table enters
the decoding API.
"""
from collections import Counter,defaultdict
from copy import deepcopy
from itertools import product,combinations
import math
from fractions import Fraction
from scripts import concept2_composition as v2
from scripts import concept2_geometry_v5 as g
from scripts.kant_type_grammar import BASE_TYPES,type_tokens,type_list_tokens,read_type,read_type_list


TYPE_NAMES=tuple('type_'+n for n in (*BASE_TYPES,'sequence','description','question','function'))+('types_end',)
EXTRA_OPERATORS=('content','number','number-negative','bit-zero','bit-one','sequence','length','position',
                 'concat','fold','disquote','quoted_lift','quoted_application','question','answer_matches',
                 'message','message_content','force-assert','force-ask','force-direct','ask','perform','iff')
PRECEDENCE={**v2.old.PRECEDENCE,'iff':0}
FIELDS={'length':('sequence',),'position':('sequence','index','value'),'concat':('left','right'),
        'fold':('sequence','initial','step'),'quoted_lift':('description',),'question':('function',),
        'message_content':('message',)}


def grammar_shape(family,slot):
    """Grammar families use rim-to-rim strokes, never a center reference ray."""
    sectors=((-135,0),(0,135),(45,180),(180,315),(-45,90),(90,225))[family]
    shapes=[g.circle(g.M)]
    shapes.extend(g.arc(g.L,a,b) for a,b in zip(sectors[::2],sectors[1::2]))
    angle=math.radians((-135,-90,-45,45,90,135)[slot])
    return shapes+[g.line((g.M*math.cos(angle),g.M*math.sin(angle)),(g.L*math.cos(angle),g.L*math.sin(angle)))]


def token(*values):return tuple(values)


class Codec:
    def __init__(self,dictionary):
        self.dictionary=dictionary
        self.declarations={d['name']:d for d in dictionary['native']['declarations']}
        self.evaluation_requirements={}
        def requirement(v,active=()):
            if isinstance(v,list):return max((requirement(x,active) for x in v),default=0)
            if not isinstance(v,dict):return 0
            own=v.get('rank',0)+1 if v.get('kind')=='disquote' else 0
            if v.get('kind') in ('call','function_ref'):
                name=v['symbol']
                if name not in self.evaluation_requirements:
                    if name in active:raise ValueError('Recursive declaration')
                    self.evaluation_requirements[name]=requirement(self.declarations[name].get('body'),(*active,name))
                own=max(own,self.evaluation_requirements[name])
            return max(own,max((requirement(x,active) for x in v.values()),default=0))
        self.evaluation_requirement=requirement
        self.aliases={tuple(x['parts']):x['symbol'] for x in dictionary['aliases']}
        self.prefixes={w[:i] for w in self.aliases for i in range(1,len(w))}
        self.forms={};self.expansions={}
        def add(t,shapes,**kw):self.forms[t]=g.unit(t,shapes,**kw)
        for name,shapes in g.ROOT_FORMS.items():
            t=token('root',name);add(t,shapes);self.expansions[t]=[v2.old.root_symbol(name)]
        for names,shapes in g.LIGATURES.items():
            t=token('lig',*names);add(t,shapes);self.expansions[t]=list(map(v2.old.root_symbol,names))
        for names,side,lane in ((('aki','round'),-1,1),(('round','aki'),1,-1)):
            t=token('lig-alt',*names);add(t,g.large_link_shape(side,lane));self.expansions[t]=list(map(v2.old.root_symbol,names))
        for name in [*v2.old.OPERATORS,'exists','apply','scope-hop']:
            add(token('op',name),v2.operator(name)['shapes'])
        for last in (False,True):
            for family in ('values','quoted','references'):add(token('separator',family,last),g.separator(last,family),fixed=True)
        add(token('word-end'),[g.circle(g.S),g.line((0,-g.S),(0,-g.P))])
        add(token('rank-zero'),[g.circle(g.S),g.arc(g.M,45,135),g.arc(g.L,225,315)])
        for lane in (-1,0,1):
            for defining in (False,True):
                for template in (False,True):
                    name=('template' if template else 'role')+('-definition' if defining else '-use')
                    add(token(name,lane),v2.role_shape(lane,defining,template),fixed=True)
        for label in range(8):
            for defining in (False,True):
                for word in (False,True):
                    name=('word' if word else 'local')+('-definition' if defining else '-use')
                    add(token(name,label),v2.alias_shape(label,defining,word))
        for label in range(256):
            add(token('dot',label),g.dot_shape(label,True),fixed=True)
        add(token('dot-bare',153),g.dot_shape(153,False),silent=True)
        for count,radius in zip(range(2,6),(g.S,g.M,g.L,g.F)):
            t=token('repeat',count)
            self.forms[t]=dict(token=t,shapes=[g.line((0,-radius),(0,radius))],entry=(0.,0.),exit=(0.,0.),
                               entry_anchor=(0.,0.),exit_anchor=(0.,0.),fixed=True,silent=False)
        for n in (2,3):
            for lanes in product((-1,0,1),repeat=n):
                t=token('branch',*lanes);add(t,g.branch_shape(lanes),fixed=True)
                # Continuation follows the small-circle trunk, not a branch tip.
                end=n*(2*g.S+g.M)+g.S
                self.forms[t]['exit']=self.forms[t]['exit_anchor']=(end,0.)
            for lanes in combinations((-1,0,1),n):
                add(token('select',*lanes),g.selection_shape(lanes),fixed=True)
                for i in range(n):
                    rotated=lanes[i:]+lanes[:i]
                    add(token('select-directed',*rotated),g.directed_selection_shape(rotated),fixed=True)
            for lanes in product((-1,0,1),repeat=n):add(token('merge',*lanes),g.merge_shape(lanes),fixed=True)
        for i,name in enumerate(TYPE_NAMES):add(token('type',name),grammar_shape(i//6,i%6),fixed=True)
        for i,name in enumerate(EXTRA_OPERATORS):add(token('op',name),grammar_shape(2+i//6,i%6),fixed=True)
        self._prepare_recognition()

    def spelling(self,parts,plane=0):
        names=tuple(map(v2.old.root_name,parts));out=[];i=0
        while i<len(names):
            matches=[n for n in g.LIGATURES if names[i:i+len(n)]==n]
            if matches:
                chosen=max(matches,key=len)
                kind='lig-alt' if plane>0 and token('lig-alt',*chosen) in self.forms else 'lig'
                out.append(token(kind,*chosen));i+=len(chosen)
            else:out.append(token('root',names[i]));i+=1
        if tuple(parts) in self.prefixes:out.append(token('word-end'))
        return out

    def validate_native(self,statement):
        """Use existing native typing; declarations are shared signatures, not glyph IDs."""
        from noema.constructed_discourse import normalize_document
        used=set()
        def visit(v):
            if isinstance(v,dict):
                if v.get('kind') in ('call','function_ref'):used.add(v['symbol'])
                if v.get('kind')=='quote' and self.evaluation_requirement(v['body'])>v.get('rank',0):
                    raise ValueError('Quoted evaluation must target lower ranks, including referenced definitions')
                for x in v.values():visit(x)
            elif isinstance(v,list):
                for x in v:visit(x)
        visit(statement);declarations=[]
        for name in sorted(used):
            d=self.declarations[name]
            parameters=[p['sort'] if isinstance(p,dict) and 'sort' in p else p for p in d['parameters']]
            declarations.append(dict(kind='primitive',name=name,parameters=parameters,result=d['result']))
        return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[statement]))['statements'][0]

    def encode(self,plan,*,compress=True,branch=True):
        self.validate_native(v2.expand_plan(plan,self.dictionary))
        out=[];binders=[];word_stops={}
        def emit(*t):out.append(token(*t))
        def word(w,plane=0):
            if w['form']=='word-use':emit('word-use',w['label']);return
            if w['form']=='word-definition':emit('word-definition',w['label'])
            out.extend(self.spelling(w['parts'],plane))
            if out[-1]==('word-end',):word_stops[len(out)-1]=tuple(w['parts'])
        def rank(v):
            if v.get('rank')==0:emit('rank-zero')
            for _ in range(v.get('rank') or 0):emit('op','quotation-rank')
        def typ(value):
            for item in type_tokens(value):emit('op','quotation-rank') if item=='quote_raise' else emit('type',item)
        def integer(value):
            emit('op','group-open')
            for bit in bin(value)[2:]:emit('op','bit-one' if bit=='1' else 'bit-zero')
            emit('op','group-close')
        def walk(v,level=0,plane=0):
            f=v.get('form');k=v.get('kind')
            if f=='scope':return walk(v['body'],level)
            if f in ('role-use','role-definition','local-use','local-definition'):
                emit(f,v.get('lane',v.get('label')))
                if f.endswith('definition'):walk(v['value'],5)
                return
            if f in ('template-use','template-definition'):
                emit(f,v['lane'])
                if f=='template-definition':emit('op',v['mode']);rank(v)
                body=v['value'];assert body['kind'] in ('call','function_ref') and not body.get('arguments')
                word(body['symbol']);return
            if f in ('dot-use','dot-definition'):
                emit('dot-bare' if f=='dot-use' and v['label']==153 else 'dot',v['label'])
                if f=='dot-definition':walk(v['value'],5)
                return
            if k in ('assert','ask','perform'):
                if k!='assert':emit('op',k)
                walk(v['body']);return
            if k in PRECEDENCE:
                p=PRECEDENCE[k];group=p<level
                if group:emit('op','group-open')
                walk(v['arguments'][0],p+1);emit('op',k);walk(v['arguments'][1],p)
                if group:emit('op','group-close')
            elif k in ('call','function_ref'):
                if k=='function_ref':emit('op',k)
                word(v['symbol'],plane);args=v.get('arguments',[]);i=0
                while i<len(args):
                    if i and i%3==0:
                        group=args[i:i+3]
                        family=('references' if all(a.get('form') in ('role-use','local-use','dot-use') for a in group) else
                                'quoted' if any(a.get('kind')=='quote' or a.get('form','').startswith('template-') for a in group) else 'values')
                        emit('separator',family,i+3>=len(args))
                    run=[]
                    while i+len(run)<len(args) and len(run)<min(3,3-i%3) and args[i+len(run)].get('form')=='role-use':
                        run.append(args[i+len(run)]['lane'])
                    if branch and len(run)>=2:
                        emit('select-directed' if len(run)==2 and run==sorted(set(run)) else 'merge',*run);i+=len(run)
                    else:walk(args[i],5,1 if i%2 else -1);i+=1
            elif k=='quote':
                emit('op','quote-open');rank(v);saved=binders[:];binders.clear();walk(v['body']);binders[:]=saved;emit('op','quote-close')
            elif k in ('lambda','forall','exists','content'):
                params=v['parameters'] if k=='lambda' else [dict(name=v['variable'],sort='situation' if k=='content' else v['sort'])]
                if len({p['name'] for p in params})!=len(params):raise ValueError('Duplicate parameter')
                emit('op',k)
                if k!='content' and not(len(params)==1 and params[0]['sort']=='individual'):
                    for p in params:typ(p['sort'])
                    if k=='lambda':emit('type','types_end')
                emit('op','group-open');before=len(binders);binders.extend(p['name'] for p in params)
                walk(v['body']);del binders[before:];emit('op','group-close')
            elif k=='variable':
                emit('op',k)
                for _ in range(binders[::-1].index(v['name'])):emit('op','scope-hop')
            elif k=='not':emit('op',k);walk(v['arguments'][0],5)
            elif k=='evaluate':emit('op',k);walk(v['content'],5);walk(v['situation'],5)
            elif k in ('apply','quoted_application','answer_matches'):
                emit('op',k);emit('op','group-open');walk(v['question' if k=='answer_matches' else 'function'],5)
                for a in v['arguments']:walk(a,5)
                emit('op','group-close')
            elif k in FIELDS:
                emit('op',k)
                for field in FIELDS[k]:walk(v[field],5)
            elif k=='disquote':emit('op',k);rank(v);walk(v['description'],5)
            elif k=='sequence':
                emit('op',k);typ(v['element']);emit('op','group-open')
                for item in v['items']:walk(item,5)
                emit('op','group-close')
            elif k=='message':emit('op',k);emit('op','force-'+v['force']);walk(v['content'],5)
            elif k=='number':
                number=Fraction(v['numerator'],v['denominator']);emit('op',k)
                if number<0:emit('op','number-negative')
                integer(abs(number.numerator));integer(number.denominator)
            else:raise ValueError('Unsupported constructor '+str(k))
        walk(plan)
        # A stop is needed only where the next visible root could extend the
        # current dictionary word. Arity and source-specific hints are not used.
        remove=set()
        for i,parts in word_stops.items():
            following=out[i+1] if i+1<len(out) else None
            extended=parts+tuple(self.expansions.get(following,[]))
            if following not in self.expansions or extended not in self.aliases and extended not in self.prefixes:remove.add(i)
        out=[t for i,t in enumerate(out) if i not in remove]
        if not compress:return out
        result=[];i=0
        while i<len(out):
            t=out[i];j=i+1
            eligible=t[0] in ('root','lig','lig-alt','role-use','word-use') or t==('op','quotation-rank')
            eligible &= t!=('root','aki')
            while eligible and j<len(out) and out[j]==t and j-i<5:j+=1
            result.append(t)
            if j-i>1:result.append(token('repeat',j-i))
            i=j
        if result and result[-1][0]=='repeat':result.append(token('word-end'))
        return result

    def units(self,tokens):return [deepcopy(self.forms[t]) for t in tokens]

    def parse(self,tokens):
        expanded=[];previous_token=None
        for t in tokens:
            if t[0]=='repeat':
                allowed=previous_token and (previous_token[0] in ('root','lig','lig-alt','role-use','word-use') or previous_token==('op','quotation-rank'))
                if not allowed or previous_token==('root','aki'):raise ValueError('Invalid repeat target')
                expanded.extend([expanded[-1]]*(t[1]-1))
            elif t[0] in ('branch','select','select-directed','merge'):expanded.extend(token('role-use',lane) for lane in t[1:])
            elif t[0]!='separator':expanded.append(t)
            previous_token=t
        tokens=expanded;pos=0;serial=0
        def fresh():return {k:{} for k in ('roles','templates','locals','words','dots')}
        state=fresh();binders=[]
        def peek():return tokens[pos] if pos<len(tokens) else None
        def take(expected=None):
            nonlocal pos
            t=peek()
            if t is None or expected is not None and t!=expected:raise ValueError(f'Expected {expected}, got {t} at {pos}')
            pos+=1;return t
        def word():
            defining=None
            if peek() and peek()[0]=='word-use':return state['words'][take()[1]]
            if peek() and peek()[0]=='word-definition':defining=take()[1]
            parts=[]
            while peek() in self.expansions:
                proposed=tuple(parts+self.expansions[peek()])
                if proposed not in self.aliases and proposed not in self.prefixes:
                    if tuple(parts) in self.aliases:break
                    raise ValueError('Unknown public spelling')
                parts.extend(self.expansions[take()]);key=tuple(parts)
                if key in self.aliases and key not in self.prefixes:break
                if key not in self.aliases and key not in self.prefixes:raise ValueError('Unknown public spelling')
            key=tuple(parts)
            if peek()==('word-end',):take()
            symbol=self.aliases[key]
            if defining is not None:state['words'][defining]=symbol
            return symbol
        def rank():
            if peek()==('rank-zero',):take();return 0
            n=0
            while peek()==('op','quotation-rank'):take();n+=1
            return n or None
        def finish_dots():
            if any(not x['used'] for x in state['dots'].values()):raise ValueError('Unpaired dot at scope boundary')
        def type_take():
            t=take()
            if t==('op','quotation-rank'):return 'quote_raise'
            if t[0]!='type':raise ValueError('Expected a type header')
            return t[1]
        def integer():
            take(('op','group-open'));bits=[]
            while peek() in (('op','bit-zero'),('op','bit-one')):bits.append(int(take()[1]=='bit-one'))
            take(('op','group-close'))
            if not bits or len(bits)>1 and not bits[0]:raise ValueError('Noncanonical integer')
            return int(''.join(map(str,bits)),2)
        def primary():
            nonlocal state,binders,serial
            t=peek()
            if not t:raise ValueError('Missing expression')
            f=t[0]
            if f in ('role-use','local-use'):
                take();return deepcopy(state['roles' if f=='role-use' else 'locals'][t[1]])
            if f in ('role-definition','local-definition'):
                take();value=expression(5);state['roles' if f=='role-definition' else 'locals'][t[1]]=deepcopy(value)
                if f=='role-definition':state['templates'].pop(t[1],None)
                return value
            if f in ('dot','dot-bare'):
                take();label=t[1];previous=state['dots'].get(label)
                if previous is not None and not previous['used']:
                    previous['used']=True;return deepcopy(previous['value'])
                if f=='dot-bare':raise ValueError('Bare dot cannot define a value')
                value=expression(5);state['dots'][label]=dict(value=deepcopy(value),used=False);return value
            if f in ('template-definition','template-use'):
                take();lane=t[1]
                if f=='template-definition':
                    mode=take()[1]
                    if mode not in ('quoted_ref','quoted_value'):raise ValueError('Invalid quotation template')
                    n=rank();symbol=word();state['templates'][lane]=(mode,n);state['roles'].pop(lane,None)
                else:mode,n=state['templates'][lane];symbol=word()
                body=dict(kind='function_ref',symbol=symbol) if mode=='quoted_ref' else dict(kind='call',symbol=symbol,arguments=[])
                value=dict(kind='quote',body=body)
                if n is not None:value['rank']=n
                return value
            if f in ('root','lig','lig-alt','word-definition','word-use'):
                symbol=word();args=[expression(5) for _ in self.declarations[symbol]['parameters']]
                return dict(kind='call',symbol=symbol,arguments=args)
            take();k=t[1] if f=='op' else None
            if k=='group-open':value=expression();take(('op','group-close'));return value
            if k=='function_ref':return dict(kind=k,symbol=word())
            if k=='quote-open':
                n=rank();saved=state,binders,serial;state=fresh();binders=[];serial=0
                body=expression();take(('op','quote-close'));finish_dots();state,binders,serial=saved
                value=dict(kind='quote',body=body)
                if n is not None:value['rank']=n
                return value
            if k in ('lambda','forall','exists','content'):
                from noema.grammar import number_word
                if k=='content':sorts=['situation']
                elif peek()==('op','group-open'):sorts=['individual']
                else:sorts=read_type_list(type_take) if k=='lambda' else [read_type(type_take)]
                params=[]
                for sort in sorts:params.append(dict(name='v'+number_word(serial),sort=sort));serial+=1
                saved=state;state={a:(b if a=='dots' else deepcopy(b)) for a,b in state.items()}
                take(('op','group-open'));before=len(binders);binders.extend(p['name'] for p in params)
                body=expression();del binders[before:];take(('op','group-close'));state=saved
                if k=='lambda':return dict(kind=k,body=body,parameters=params)
                return dict(kind=k,body=body,variable=params[0]['name'],**({} if k=='content' else dict(sort=sorts[0])))
            if k=='variable':
                depth=0
                while peek()==('op','scope-hop'):take();depth+=1
                if depth>=len(binders):raise ValueError('Unbound variable')
                return dict(kind=k,name=binders[-1-depth])
            if k=='not':return dict(kind=k,arguments=[expression(5)])
            if k=='evaluate':return dict(kind=k,content=expression(5),situation=expression(5))
            if k in ('apply','quoted_application','answer_matches'):
                take(('op','group-open'));function=expression(5);args=[]
                while peek()!=('op','group-close'):args.append(expression(5))
                take();return dict(kind=k,arguments=args,**{'question' if k=='answer_matches' else 'function':function})
            if k in FIELDS:return dict(kind=k,**{field:expression(5) for field in FIELDS[k]})
            if k=='disquote':
                n=rank();description=expression(5)
                return dict(kind=k,description=description,**({'rank':n} if n is not None else {}))
            if k=='sequence':
                element=read_type(type_take);take(('op','group-open'));items=[]
                while peek()!=('op','group-close'):items.append(expression(5))
                take();return dict(kind=k,element=element,items=items)
            if k=='message':
                force=take()
                if force not in [('op','force-'+x) for x in ('assert','ask','direct')]:raise ValueError('Message force')
                return dict(kind=k,force=force[1][6:],content=expression(5))
            if k=='number':
                negative=peek()==('op','number-negative')
                if negative:take()
                numerator=integer();denominator=integer()
                if not denominator or negative and not numerator or math.gcd(numerator,denominator)!=1:raise ValueError('Noncanonical rational')
                return dict(kind=k,numerator=-numerator if negative else numerator,denominator=denominator)
            raise ValueError(f'Unexpected {t} at {pos-1}')
        def expression(level=0):
            left=primary()
            while peek() and peek()[0]=='op' and peek()[1] in PRECEDENCE:
                name=peek()[1];p=PRECEDENCE[name]
                if p<level:break
                take();left=dict(kind=name,arguments=[left,expression(p)])
            return left
        statement='assert'
        if peek() in (('op','ask'),('op','perform')):statement=take()[1]
        result=dict(kind=statement,body=expression());finish_dots()
        if peek()==('word-end',):take()
        if pos!=len(tokens):raise ValueError(f'Unconsumed tokens at {pos}: {tokens[pos:pos+5]}')
        self.validate_native(result)
        return result

    def _prepare_recognition(self):
        self.recognition=defaultdict(list)
        signatures={}
        for t,u in self.forms.items():
            rings=[s for s in u['shapes'] if s['kind']!='line']
            if not rings:continue
            anchor=min(rings,key=lambda s:(s['x'],s['y'],shape_class(s)))
            u['recognition_anchor']=anchor
            sig=tuple(sorted(shape_key(s,-anchor['x'],-anchor['y']) for s in u['shapes']))
            if sig in signatures:raise ValueError(f'Identical visible forms: {signatures[sig]} / {t}')
            signatures[sig]=t
            self.recognition[shape_class(anchor)].append(u)

    def read_svg(self,raw,*,fragment=False):
        ink=normalize_scale(g.from_svg(raw))
        rings=[s for s in ink if s['kind']!='line'];lines=merge_lines([s for s in ink if s['kind']=='line'])
        remaining=set(range(len(rings)));lookup=defaultdict(list)
        for i,s in enumerate(rings):lookup[shape_class(s)].append(i)
        matches=[]
        while remaining:
            xmin=min(rings[i]['x'] for i in remaining)
            front=[i for i in remaining if rings[i]['x']<xmin+1e-3]
            ymin=min(rings[i]['y'] for i in front)
            first=min((i for i in front if rings[i]['y']<ymin+1e-3),key=lambda i:shape_class(rings[i]))
            anchor=rings[first];candidates=[]
            for u in self.recognition[shape_class(anchor)]:
                base=u['recognition_anchor'];dx=anchor['x']-base['x'];dy=anchor['y']-base['y'];covered=set();valid=True
                translated=g.move(u['shapes'],dx,dy)
                for s in translated:
                    if s['kind']=='line':
                        if not covered_line(s,lines):valid=False;break
                    else:
                        found=[i for i in lookup[shape_class(s)] if i in remaining and math.hypot(rings[i]['x']-s['x'],rings[i]['y']-s['y'])<1e-3]
                        if len(found)!=1:valid=False;break
                        covered.add(found[0])
                if not valid:continue
                # A maximal glyph cannot skip an intervening circle center.
                xmax=max(s['x'] for s in translated if s['kind']!='line')
                if any(rings[i]['x']<=xmax+1e-3 and i not in covered for i in remaining):continue
                candidates.append((len(covered),sum(s['kind']=='line' for s in translated),u,dx,dy,covered))
            if not candidates:raise ValueError(f'Unrecognized ink at {anchor}; after {[m["unit"]["token"] for m in matches[-4:]]}')
            best=max((x[0],x[1]) for x in candidates);chosen=[x for x in candidates if x[:2]==best]
            if len(chosen)!=1:raise ValueError('Ambiguous maximal glyph: '+str([x[2]['token'] for x in chosen]))
            _,_,u,dx,dy,covered=chosen[0];remaining-=covered
            matches.append(dict(unit=u,x=dx,y=dy))
        # Four lengths are a syntactic repeat operator, never word identities.
        internal=[s for m in matches for s in g.move(m['unit']['shapes'],m['x'],m['y']) if s['kind']=='line']
        for s in lines:
            if abs(s['x2']-s['x1'])>1e-3:continue
            if covered_line(s,internal):continue
            radius=abs(s['y2']-s['y1'])/2
            n=next((n for n,r in zip(range(2,6),(g.S,g.M,g.L,g.F)) if abs(r-radius)<1e-3),None)
            if n is not None:
                matches.append(dict(unit=self.forms[('repeat',n)],x=s['x1'],y=(s['y1']+s['y2'])/2))
        matches.sort(key=lambda m:m['x']+min(s.get('x',min(s.get('x1',0),s.get('x2',0))) for s in m['unit']['shapes']))
        expected=[];previous=None;previous_right=None;breaks=[]
        for mi,m in enumerate(matches):
            u=m['unit'];x,y=m['x'],m['y'];expected.extend(g.move(u['shapes'],x,y))
            placed={k:(u[k][0]+x,u[k][1]+y) for k in ('entry','exit','entry_anchor','exit_anchor')}
            if previous and not u.get('silent'):
                options=[]
                for candidate_x,path,_ in g.routes(previous,u,y):
                    if abs(candidate_x-x)<1e-3 and all(covered_line(s,lines) for s in path):options.append(path)
                if len(options)==1:expected.extend(options[0])
                elif not options and fragment and abs(x+g.bounds(u['shapes'])[0]-previous_right-2*g.M)<1e-3:
                    breaks.append(mi)
                else:raise ValueError(f'Invalid or ambiguous radius connection to {u["token"]}')
            elif previous:
                left=g.bounds(u['shapes'])[0]
                if abs(x+left-previous['exit_anchor'][0]-g.M)>1e-3:raise ValueError('Invalid silent-dot gap')
            previous=placed
            previous_right=max(previous_right or -math.inf,x+g.bounds(u['shapes'])[2])
        expected_lines=[s for s in expected if s['kind']=='line']
        leading=trailing=False;entry_rail=exit_rail=None;continuations=[]
        if fragment:
            last=matches[-1];u=last['unit'];x,y=last['x'],last['y']
            end=(u['exit_anchor'][0]+x+g.M,u['exit_anchor'][1]+y)
            stub=g.line((u['exit'][0]+x,u['exit'][1]+y),end)
            if covered_line(stub,lines) and not covered_line(stub,expected_lines):
                expected_lines.append(stub);trailing=True;exit_rail=end[1]
                continuations.append(end)
            first=matches[0];u=first['unit'];x,y=first['x'],first['y'];left=x+g.bounds(u['shapes'])[0]
            candidates=[]
            endpoints={(s[a],s[b]) for s in lines for a,b in (('x1','y1'),('x2','y2')) if s[a]<left-1e-3}
            for start in endpoints:
                dummy=dict(exit=start,exit_anchor=start)
                for px,path,_ in g.routes(dummy,u,y):
                    if abs(px-x)<1e-3 and all(covered_line(s,lines) for s in path):candidates.append((start,path))
            if candidates:
                # Intermediate bends cannot replace the incoming free end.
                xmin=min(start[0] for start,_ in candidates)
                candidates=[item for item in candidates if item[0][0]<xmin+1e-3]
            if len(candidates)>1:raise ValueError('Ambiguous incoming continuation')
            if candidates:
                start,path=candidates[0];expected_lines.extend(path);leading=True;entry_rail=start[1]
                continuations.append(start)
        if any(not covered_line(s,expected_lines) for s in lines):raise ValueError('Unexplained line ink')
        # Validate in the recovered page coordinate system.
        origin=next((m['y'] for m in matches if m['unit']['fixed']),matches[0]['y'])
        g.ink_check(g.move(ink,dy=-origin),continuations=[(x,y-origin) for x,y in continuations])
        tokens=[m['unit']['token'] for m in matches]
        return dict(native=None if fragment else self.parse(tokens),tokens=tokens,glyphs=len(matches),unique=True,
                    breaks=breaks,leading=leading,trailing=trailing,
                    entry_rail=None if entry_rail is None else round(entry_rail-origin,3),
                    exit_rail=None if exit_rail is None else round(exit_rail-origin,3))

    def read_page(self,raw):
        ink=normalize_scale(g.from_svg(raw));bands=[]
        for s in sorted(ink,key=lambda s:g.bounds([s])[1]):
            top,bottom=g.bounds([s])[1::2]
            if not bands or top>bands[-1]['bottom']+1e-3:bands.append(dict(bottom=bottom,shapes=[s]))
            else:bands[-1]['bottom']=max(bands[-1]['bottom'],bottom);bands[-1]['shapes'].append(s)
        statements=[];current=[];previous=None
        for band in bands:
            shapes=band['shapes'];right=g.bounds(shapes)[2];bottom=g.bounds(shapes)[3]
            row=self.read_svg(v2.svg(shapes,width=right+10,height=bottom+10),fragment=True)
            if previous:
                if previous['trailing']!=row['leading']:raise ValueError('Mismatched line continuation')
                if row['leading'] and row['entry_rail']!=previous['exit_rail']:raise ValueError('Continuation changed rail')
                if not row['leading']:
                    statements.append(self.parse(current));current=[]
            elif row['leading']:raise ValueError('Page begins with an unfinished statement')
            for i,t in enumerate(row['tokens']):
                if i in row['breaks']:
                    statements.append(self.parse(current));current=[]
                current.append(t)
            previous=row
        if previous and previous['trailing']:raise ValueError('Page ends inside a statement')
        if current:statements.append(self.parse(current))
        return dict(statements=statements,rows=len(bands),unique=True)


def shape_class(s):
    if s['kind']=='dot':return ('dot',round(s['r'],3))
    if s['kind']=='arc':
        length=s['b']-s['a'];start=0 if abs(length-360)<1e-3 else s['a']%360
        return ('arc',round(s['r'],3),round(start,3)%360,round(length,3))
    return ('line',)


def shape_key(s,dx=0.,dy=0.):
    if s['kind']=='line':
        a,b=sorted(((round(s['x1']+dx,3),round(s['y1']+dy,3)),(round(s['x2']+dx,3),round(s['y2']+dy,3))))
        return ('line',*a,*b)
    return (*shape_class(s),round(s['x']+dx,3),round(s['y']+dy,3))


def covered_line(target,lines):
    ax,ay=target['x1'],target['y1'];dx,dy=target['x2']-ax,target['y2']-ay;den=dx*dx+dy*dy
    intervals=[]
    for s in lines:
        if any(abs((x-ax)*dy-(y-ay)*dx)>1e-3*math.sqrt(den) for x,y in ((s['x1'],s['y1']),(s['x2'],s['y2']))):continue
        a=((s['x1']-ax)*dx+(s['y1']-ay)*dy)/den;b=((s['x2']-ax)*dx+(s['y2']-ay)*dy)/den
        intervals.append(sorted((a,b)))
    end=0.
    for a,b in sorted(intervals):
        if a>end+1e-4:break
        end=max(end,b)
        if end>=1-1e-4:return True
    return False


def merge_lines(lines):
    groups=defaultdict(list)
    for s in lines:
        dx=s['x2']-s['x1'];dy=s['y2']-s['y1']
        if abs(dx)<1e-4:direction='v';offset=s['x1'];a,b=sorted((s['y1'],s['y2']))
        else:
            slope=dy/dx
            if min(abs(slope-x) for x in (-1,0,1))>1e-4:raise ValueError('Unknown line direction')
            direction=round(slope);offset=s['y1']-direction*s['x1'];a,b=sorted((s['x1'],s['x2']))
        groups[(direction,round(offset,3))].append((a,b,offset))
    result=[]
    for (direction,_),segments in groups.items():
        intervals=[];offset=segments[0][2]
        for a,b,_ in sorted(segments):
            if intervals and a<=intervals[-1][1]+1e-4:intervals[-1]=(intervals[-1][0],max(b,intervals[-1][1]))
            else:intervals.append((a,b))
        for a,b in intervals:
            result.append(g.line((offset,a),(offset,b)) if direction=='v' else g.line((a,direction*a+offset),(b,direction*b+offset)))
    return result


def normalize_scale(ink):
    rings=[s for s in ink if s['kind']=='arc'];dots=[s for s in ink if s['kind']=='dot']
    if not rings:raise ValueError('No circle element')
    options=[dots[0]['r']/g.D] if dots else [rings[0]['r']/r for r in (g.S,g.M,g.L,g.F)]
    valid=[s for s in options if all(min(abs(r['r']/s-k) for k in (g.S,g.M,g.L,g.F))<1e-4 for r in rings)
           and all(abs(d['r']/s-g.D)<1e-4 for d in dots)]
    scale=next((s for s in valid if abs(s-1)<1e-5),None)
    if scale is None:
        if len(valid)!=1:raise ValueError('Unknown or ambiguous circle scale')
        scale=valid[0]
    return [{k:(v/scale if k in ('x','y','x1','x2','y1','y2','r') else v) for k,v in s.items()} for s in ink]
