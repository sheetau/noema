from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json
import pytest
from noema.constructed_semantics import FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_homogeneity_visible as check
from scripts import homogeneity_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
VS=dict(kind='function',parameters=['individual'],result=RS)
MS=dict(kind='function',parameters=['individual','individual'],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
ROLES=('x','y','z','time')
POINTS=('context','discourse','other')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'time','ra':'frame','zbm':'moving','ta':'lengthunit','rb':'unit','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zde':'premise','zdf':'inference','zdb':'task'}
DOMAIN=(*ROLES,'frame','moving','lengthunit','unit','author','paper','section','premise','inference','task','later','another','other')

def forbidden(*args):raise ValueError('Unknown homogeneity-visible input')
def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    return x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def abstract(d):
    if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
    d['kind']='primitive';d.pop('body',None)
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
@lru_cache(None)
def mapping():return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

class ConstructedCuts:
    """Only registered exact rational cuts are read; no probing unknown functions."""
    def __init__(self):self.table={}
    def make(self,value):
        value=Q(value);result=cut(value);self.table[result.implementation]=value;return result
    def read(self,value):
        while isinstance(value,FunctionValue):
            impl=value.implementation
            if impl in self.table:return self.table[impl]
            if isinstance(impl,FunctionValue):
                value=impl
                continue
            code=getattr(impl,'__code__',None)
            if code is None:break
            free=dict(zip(code.co_freevars,(c.cell_contents for c in (getattr(impl,'__closure__',None) or ()))))
            value=free.get('raw')
        raise ValueError('Cut was not constructed by this finite fixture')
def arithmetic():
    cuts=ConstructedCuts();r=cuts.read;c=cuts.make
    return cuts,dict(ba=lambda x:isinstance(r(x),Q),bb=c,bc=lambda a,b:r(a)<=r(b),bd=lambda a,b:c(r(a)+r(b)),bf=lambda a,b:c(r(a)-r(b)),shv=lambda a,b:c(r(a)*r(b)),sca=lambda a,b:r(a)==r(b),zzba=lambda x:isinstance(r(x),Q),zzbc=lambda a,b:r(a)<=r(b))

def numbers():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read
    m|={'bg':lambda a,b:r(a)<r(b),'sah':lambda a,b:c(r(a)*r(b))}
    return cuts,m

def project(node,sorts):
    if any(node==s for s in sorts):return 'individual'
    if isinstance(node,dict):return {k:project(v,sorts) for k,v in node.items()}
    if isinstance(node,list):return [project(v,sorts) for v in node]
    return node

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    boundaries=NUM|set(CONSTANTS)|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}|{'eiyz','eiy2','eiyy','shh'}
    if name in ('eize','eizf'):boundaries|={'sia','eizd','eizc','shs','sht'}
    if name=='eizg':boundaries.add('eizf')
    if name=='shs':boundaries|={'shn','shp','shr'}
    if name=='sht':boundaries|={'shn','shq','sho'}
    boundaries.discard(name)
    for d in doc['declarations']:
        if d['name'] in {m[n] for n in boundaries if n in m}:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(m[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    if mode=='projection':doc=project(doc,[VS,MS] if name=='eizg' else [VS])
    target=next(d for d in doc['declarations'] if d['name']==m[name]);slots=[]
    for i,p in enumerate(target['parameters']):
        slot='homogeneityslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(m[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='homogeneitycontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('homogeneitycontext'))
    elif target['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jhccapture',parameters=[target['result']],result='truth'))
        body=call('jhccapture',body)
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,args,model,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    m={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'homogeneitycontext':lambda:'discourse'}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    h=handlers(doc);h.update({mapping().get(n,n):f for n,f in m.items() if mapping().get(n,n) in h})
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives=h,max_steps=1500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown homogeneity-visible' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('wrong' if i==j else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

def wrap(sort,fn):return FunctionValue(tuple(sort['parameters']),sort['result'],fn)
def vector(c,values):return FunctionValue(('individual',),RS,lambda a:c(Q(values[ROLES.index(a)])))
def typed_arguments(name,implementations,mode='boundary'):
    doc,slots=fixture(name,mode);decls={d['name']:d for d in doc['declarations']}
    return [wrap(decls[n]['result'],fn) if callable(fn) else fn for n,fn in zip(slots,implementations,strict=True)]
def reject_full(check):
    try:check()
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full function quantification silently sampled')

@lru_cache(None)
def domain_graph_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    vectors={'x':(0,0,0,0),'y':(1,0,0,0),'z':(2,0,0,0),'time':(3,0,0,0)}
    pairs={('x','z'),('y','time')}
    m|={'eiyz':lambda t:t in ('x','y'),'eiy2':lambda t:t in ('z','time'),'eiyy':lambda a,b:(a,b) in pairs,'shh':lambda a,b:vectors[a]==vectors[b],'zc6':lambda t,a:c(Q(vectors[t][ROLES.index(a)]))}
    count=0
    for val,want in ((vectors['x'],True),(vectors['y'],True),(vectors['z'],False),((0,0,0,1),False)):
        assert run('eizc',[vector(c,val)],m,domain=ROLES)==want;count+=1
    assert not run('eizc',[vector(c,vectors['x'])],m|{'eiyz':lambda t:False},domain=ROLES);count+=1
    for role in ROLES:
        assert not run('eizc',[vector(c,vectors['x'])],m|{'zc6':lambda t,a,role=role:c(Q(vectors[t][ROLES.index(a)]+(1 if a==role else 0)))},domain=ROLES);count+=1
    transform=lambda vec:vector(c,[r(vec(a))+(2 if a=='x' else 0) for a in ROLES])
    transform_sort=dict(kind='function',parameters=[VS],result=VS);tr=wrap(transform_sort,transform)
    check=lambda mm:run('eizd',[tr],mm,domain=ROLES)
    assert check(m);count+=1
    for patch in ({'eiyz':lambda t:False},{'eiyy':lambda a,b:(a,b)==('x','z')},{'eiyy':lambda a,b:(a,b) in pairs|{('x','time')}},{'eiy2':lambda t:t=='z'},{'ba':lambda x:r(x)!=3}):assert not check(m|patch);count+=1
    for i in range(4):
        wrong=wrap(transform_sort,lambda vec,i=i:vector(c,[r(vec(a))+(2 if a=='x' else 0)+(1 if j==i else 0) for j,a in enumerate(ROLES)]))
        assert not run('eizd',[wrong],m,domain=ROLES);count+=1
    unknowns(check,m,('eiyz','eiy2','eiyy','shh','zc6','ba','sca'))
    return dict(cases=count,current_measurement_domain_and_same_event_graph_required=True,all_four_output_components_and_missing_extra_pairs_checked=True)

@lru_cache(None)
def numeric_kernel_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;axes=SequenceValue(ROLES,'"individual"');count=0
    matrix=((2,1,0,-1),(0,1,0,0),(0,0,-2,0),(1,0,0,1));offset=(3,-1,2,5);inputs=(1,2,-1,3)
    mat=lambda a,b:c(Q(matrix[ROLES.index(a)][ROLES.index(b)]))
    expected=[offset[i]+sum(matrix[i][j]*inputs[j] for j in range(4)) for i in range(4)]
    args=typed_arguments('shq',[axes,mat,lambda a:c(Q(offset[ROLES.index(a)])),lambda a:c(Q(inputs[ROLES.index(a)])),m['bd'],m['shv']])
    assert run('shq',args,m|{'jhccapture':lambda out:all(r(out(a))==expected[i] for i,a in enumerate(ROLES))},domain=ROLES);count+=1
    for i in range(4):
        bad=list(expected);bad[i]+=1
        assert not run('shq',args,m|{'jhccapture':lambda out,bad=bad:all(r(out(a))==bad[i] for i,a in enumerate(ROLES))},domain=ROLES);count+=1
    # Test every displacement direction; the zero shift alone cannot distinguish
    # a quadratic from an affine map.
    for axis in range(4):
        first=(0,0,0,0);second=(1,1,1,1);shift=tuple(1 if j==axis else 0 for j in range(4))
        for nonlinear in (False,True):
            def transform(vec):
                vals=[r(vec(a)) for a in ROLES]
                return vector(c,[vals[i]*vals[i] if nonlinear and i==axis else offset[i]+sum(matrix[i][j]*vals[j] for j in range(4)) for i in range(4)])
            args=typed_arguments('shr',[axes,vector(c,first),vector(c,second),vector(c,shift),transform,m['ba'],m['sca'],m['bd'],m['bf']])
            assert run('shr',args,m,domain=ROLES)==(not nonlinear);count+=1
    for shift in ((0,0,0,0),(1,-2,3,1)):
        def affine(vec):
            vals=[r(vec(a)) for a in ROLES];return vector(c,[offset[i]+sum(matrix[i][j]*vals[j] for j in range(4)) for i in range(4)])
        args=typed_arguments('shr',[axes,vector(c,(0,1,-1,2)),vector(c,(1,-1,2,0)),vector(c,shift),affine,m['ba'],m['sca'],m['bd'],m['bf']])
        assert run('shr',args,m,domain=ROLES);count+=1
    zeroargs=typed_arguments('shq',[axes,mat,lambda a:c(Q(offset[ROLES.index(a)])),lambda a:c(Q(0)),m['bd'],m['shv']])
    assert run('shq',zeroargs,m|{'jhccapture':lambda out:all(r(out(a))==offset[i] for i,a in enumerate(ROLES))},domain=ROLES);count+=1
    return dict(cases=count,native_matrix_rows_and_increments_use_exact_constructed_cuts=True,all_spatial_temporal_and_mixed_shifts_checked=True,nonzero_origin_offsets_preserved=True,affine_implies_homogeneity_reverse_not_proved=True)

@lru_cache(None)
def quantifier_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;small=('a','b');axes=SequenceValue(small,'"individual"');count=0
    args=typed_arguments('shs',[axes,lambda x:x in small,lambda x:x,m['ba'],m['sca'],m['bd'],m['bf']],'projection')
    triples=set(product(small,repeat=3))
    base=m|{'shn':lambda ax,x,valid:ax.items==small and x in small,'shp':lambda a,b,add:'a' if a==b else 'b','shr':lambda ax,a,b,s,*fs:(a,b,s) in triples}
    check=lambda mm:run('shs',args,mm,'projection',small)
    assert check(base);count+=1
    for row in triples:assert not check(base|{'shr':lambda ax,a,b,s,*fs,row=row:(a,b,s)!=row});count+=1
    empty=typed_arguments('shs',[axes,lambda x:False,lambda x:x,m['ba'],m['sca'],m['bd'],m['bf']],'projection')
    assert not run('shs',empty,base,'projection',small);count+=1
    # Keep only one base point: out-of-domain shifts do not become requirements.
    one=typed_arguments('shs',[axes,lambda x:x=='a',lambda x:x,m['ba'],m['sca'],m['bd'],m['bf']],'projection')
    assert run('shs',one,base|{'shr':lambda ax,a,b,s,*fs:(a,b,s)==('a','a','a')},'projection',small);count+=1
    native=typed_arguments('shs',[axes,lambda x:True,lambda x:x,m['ba'],m['sca'],m['bd'],m['bf']])
    reject_full(lambda:run('shs',native,base,domain=small));count+=1
    # The matrix is still a native two-argument numeric function in this
    # projection; only the infinite vector domain becomes two individuals.
    matrix=lambda a,b:c(Q(1 if a==b else 0))
    args=typed_arguments('sht',[axes,lambda x:x in small,lambda x:x,matrix,'a',m['ba'],m['sca'],m['bd'],m['shv']],'projection')
    base=m|{'shn':lambda ax,x,valid:ax.items==small and x in small,'sho':lambda ax,a,b,same:a==b,'shq':lambda ax,mat,off,vec,add,mul:vec}
    check=lambda mm:run('sht',args,mm,'projection',small)
    assert check(base);count+=1
    for target in small:
        assert not check(base|{'shq':lambda ax,mat,off,vec,add,mul,target=target:('b' if vec=='a' else 'a') if vec==target else vec});count+=1
    for row,col in product(small,repeat=2):
        bad=typed_arguments('sht',[axes,lambda x:x in small,lambda x:x,lambda a,b,row=row,col=col:c(Q(999 if (a,b)==(row,col) else 1)),'a',lambda x:r(x)!=999,m['sca'],m['bd'],m['shv']],'projection')
        assert not run('sht',bad,base,'projection',small);count+=1
    for mask in range(16):
        pairs={p for i,p in enumerate(product(small,repeat=2)) if mask&(1<<i)}
        assert run('eizg',[],{'eizf':relation(pairs)},'projection',small)==bool(pairs);count+=1
    reject_full(lambda:run('eizg',[],{'eizf':lambda *xs:True},domain=small));count+=1
    return dict(cases=count,nonempty_all_base_pairs_and_all_admissible_shifts_preserved=True,same_matrix_and_offset_witness_for_entire_domain=True,projections_are_explicit_and_native_infinite_domains_refused=True)

@lru_cache(None)
def connection_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;values=(0,1,2,3);axes=ROLES
    vec=vector(c,values);transform=wrap(dict(kind='function',parameters=[VS],result=VS),lambda x:x)
    matrix=wrap(MS,lambda a,b:c(Q(ROLES.index(a)*4+ROLES.index(b)+1)))
    def domain(v):return tuple(r(v(a)) for a in axes)==values
    def functions(valid,same,add,operation,multiply=False):
        return valid(c(Q(2))) and same(c(Q(2)),c(Q(2))) and not same(c(Q(2)),c(Q(3))) and r(add(c(Q(2)),c(Q(3))))==5 and r(operation(c(Q(2)),c(Q(3))))==(6 if multiply else -1)
    def common(ax,dom,tr):return ax.items==axes and dom(vec) and tuple(r(tr(vec)(a)) for a in axes)==values
    shs=lambda ax,dom,tr,valid,same,add,sub:common(ax,dom,tr) and functions(valid,same,add,sub)
    sht=lambda ax,dom,tr,mat,off,valid,same,add,mul:common(ax,dom,tr) and tuple(r(mat(a,b)) for a,b in product(axes,repeat=2))==tuple(range(1,17)) and tuple(r(off(a)) for a in axes)==values and functions(valid,same,add,mul,True)
    base=m|{'sia':lambda:transform,'eizc':domain,'eizd':lambda tr:tuple(r(tr(vec)(a)) for a in axes)==values,'shs':shs,'sht':sht}
    assert run('eize',[],base);assert run('eizf',[matrix,vec],base);count=2
    for name in ('eize','eizf'):
        args=[] if name=='eize' else [matrix,vec]
        for boundary in ('eizd','shs' if name=='eize' else 'sht'):
            assert not run(name,args,base|{boundary:lambda *xs:False});count+=1
        unknowns(lambda mm:run(name,args,mm),base,('sia','eizc','eizd','shs' if name=='eize' else 'sht'))
    return dict(cases=count,same_four_roles_domain_transform_and_numeric_operations_bound=True,homogeneity_and_affinity_each_require_current_graph=True)

@lru_cache(None)
def presentation_checks():
    members={('inference','task','paper','discourse'),('later','task','paper','discourse'),('another','task','paper','discourse')}
    rows={'ue':{('inference',n,'discourse') for n in ('later','another')}};m={'eisnm':relation(members),'ue':relation(rows['ue'])}
    count=perturb(lambda mm:run('eizi',[],mm),m,rows)
    assert not run('eizi',[],m|{'eisnm':relation(members-{('inference','task','paper','discourse')})});count+=1
    assert not run('eizi',[],m|{'eisnm':relation(members|{('other','task','paper','discourse')})});count+=1
    assert run('eizi',[],m|{'eisnm':relation({('inference','task','paper','discourse')})});count+=1
    unknowns(lambda mm:run('eizi',[],mm),m,('eisnm',))
    rows|={'ug':{('premise','author','eize','section','discourse')},'zc':{('inference','author','eize','eizg','section','discourse')},'zdg':{('inference','author','eizg','section','discourse')},'zdh':{('inference','task','eizg','section','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()}|{'eisnm':relation(members)}
    count+=perturb(lambda mm:run('eizj',[],mm),m,rows)
    assert run('eizj',[],m|{n:forbidden for n in ('eize','eizg','eizd','shs','sht','sia')});count+=1
    rows={'eir3':{('inference','author','paper','eizk','discourse')},'ue':{('task','inference','discourse')}};m={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('eizl',[],mm),m,rows)
    assert run('eizl',[],m|{n:forbidden for n in ('ug','zc','zdg','zdh','eizj')});count+=1
    return dict(cases=count,first_main_step_not_merely_later_than_task=True,premise_conclusion_obviousness_and_required_task_bound=True,attribution_does_not_prove_homogeneity_implies_affinity=True)


def test_domain_graph_checks():assert domain_graph_checks()

def test_numeric_kernel_checks():assert numeric_kernel_checks()

def test_quantifier_checks():assert quantifier_checks()

def test_connection_checks():assert connection_checks()

def test_presentation_checks():assert presentation_checks()

def test_candidate_binding_and_four_role_normalization():
    # Observe the actual composed predicates at distinguishing rational points.
    # This checks binding/normalization, not equality over every real number.
    map_sort=dict(kind='function',parameters=[VS],result=VS)
    expected_context=('frame','moving','lengthunit','unit','context')
    probes=tuple(Q(q) for q in (-1,0,1,2,3,4,5,6,7,8,9,10,11,20,99))
    domain=(*DOMAIN,'hidden')
    for hidden in (9,17):
        incoming=FunctionValue(('individual',),RS,lambda role:cut(Q(ROLES.index(role)+1 if role in ROLES else hidden)))
        def candidate(*context):
            def transform(vec):
                normalized=all(vec(role)(q)==(q<(ROLES.index(role)+1 if role in ROLES else 0))
                    for role in (*ROLES,'hidden') for q in probes)
                good=context==expected_context and normalized
                return FunctionValue(('individual',),RS,
                    lambda role:cut(Q(7+ROLES.index(role) if role in ROLES and good else 20 if role in ROLES else 99)))
            return wrap(map_sort,transform)
        def captured(transform):
            out=transform(incoming)
            return all(out(role)(q)==(q<(7+ROLES.index(role) if role in ROLES else 0))
                for role in (*ROLES,'hidden') for q in probes)
        model={'zdd':candidate,'jhccapture':captured,'aa':lambda a,b:a<b}
        assert run('sia',[],model,domain=domain)
        for name in ('ra','zbm','ta','rb','zb6'):
            assert not run('sia',[],model|{name:lambda:'other'},domain=domain)
        unknowns(lambda m:run('sia',[],m,domain=domain),model,('zdd',))


def test_source_profile_and_saved_bridge():
    doc=check.restored()['document'];old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert doc['statements'][:79]==old['statements']
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert len(doc['declarations'])==1348 and len(doc['statements'])==80 and len(check.vocabulary()._words)==749
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['source_statement_indices']==[109] and len(b['source_declarations'])==215
    unit=b['source_units']['einstein-1905:u0047'];assert unit['range']==[0,129]
    assert len(''.join(unit['text'].split()))==112
    assert b['math']==[] and b['text_boundaries']['spans']=={'zde':['zdf',12,18]}
    assert ds[mapping()['eizk']]['body']['force']=='assert'
    assert set(profile.SOURCE_RELATIONS)=={'eisnm','zdd','zdh'}
    changed=deepcopy(doc);changed['statements'][79]['body']=dict(kind='truth',value=True)
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(changed)

def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]
def context(doc,b):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()}

def test_reference_scopes_and_inherited_names():
    doc=deepcopy(check.restored()['document']);n=check.names();b=check.BASE|{'zb7':cut(Q(3))}
    for old in (*check.SENTENCES,*check.SPANS):
        trial=deepcopy(doc);trial['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
        trial['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        assert native_run(trial,context(trial,b)|dict(expected=lambda:b[old]))==[True]
        assert native_run(trial,context(trial,b)|dict(expected=lambda:'other'))==[False]
    h=check.context_handlers(b)
    assert h['sentencetokenspanreference'](b['eirf'],b['zda'],28,b['zda'],42,b['ri'])==b['zdb']
    assert h['designationreference'](b['eirf'],b['zc3'],1,b['ri'])==b['eisnl']
    assert h['sentencetokenspanreference'](b['eirf'],b['zco'],24,b['zco'],60,b['ri'])==b['zcp']
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())

def test_property_span_rejects_changed_endpoints_and_unknown_inputs():
    b=check.BASE|{'zb7':cut(Q(3))};h=check.context_handlers(b)
    key=[b['eirf'],b['zdf'],12,b['zdf'],18,b['ri']]
    assert h['sentencetokenspanreference'](*key)==b['zde']
    for slot in range(6):
        bad=key.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    for bad in (0,-1,1,11,13,19,Q(1,2),True,12.0,'12'):
        with pytest.raises(ValueError):h['sentencetokenspanreference'](b['eirf'],b['zdf'],bad,b['zdf'],18,b['ri'])
    for end in (11,17,19):
        with pytest.raises(ValueError):h['sentencetokenspanreference'](b['eirf'],b['zdf'],12,b['zdf'],end,b['ri'])

def test_whole_attribution_preserves_order_without_proving_the_content():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][79:80];b=check.BASE|{'zb7':cut(Q(3))}
    rows={'eir3':{(b['zdf'],b['rd'],b['eirf'],'eizk',b['ri'])},'ue':{(b['zdb'],b['zdf'],b['ri'])}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]
    for n in rows:assert native_run(doc,h|{mapping()[n]:lambda *xs:False})==[False]
