from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json
import pytest
from noema.constructed_semantics import FunctionValue,DescriptionValue,Content,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_transformation_heading_visible as check
from scripts import transformation_heading_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
DOMAIN=('event','tuple','frame','moving','lengthunit','timeunit','x','y','z','time','inquiry','node','section','part','paper','previous','other')
POINTS=('context','discourse','other');SMALL=('zero','one')
def forbidden(*args):raise ValueError('Unknown transformation-heading-visible input')
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
def constants():return {n:lambda x=x:x for n,x in {'ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z','zc7':'time','eismt':'node','eisms':'section','eisdx':'part','eirf':'paper','zbk':'previous','ri':'discourse'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    selected=NUM|set(constants())|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    selected.add('eiuk')
    if mode!='native_uniqueness':selected.add('sd')
    if name=='eiu2':selected|={'eiuz','eiuo'}
    selected.discard(name)
    for d in doc['declarations']:
        if d['name'] in {m[n] for n in selected if n in m}:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(m[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    target=ds[m[name]];slots=[]
    for i,p in enumerate(target['parameters']):
        slot='tripslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(m[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='tripcontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('tripcontext'))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,args,model,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    m=constants()|{'tripcontext':lambda:'discourse'}|model|{n:(lambda x=x:x) for n,x in zip(slots,args)}
    h=handlers(doc);h.update({mapping().get(n,n):f for n,f in m.items() if mapping().get(n,n) in h})
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives=h,max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

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

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown transformation-heading-visible' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def norm_factory(cuts,times):
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return cuts.read(x)
            if x.result==RS:return tuple(cuts.read(x(cuts.make(Q(t)))) for t in times)
            forbidden()
        return tuple(one(x) for x in xs)
    return norm

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def assignment_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,())
    components={'x':Q(2),'y':Q(-3),'z':Q(4),'time':Q(7)}
    def component(tup,axis):
        if tup!='tuple' or axis not in components:forbidden()
        return c(components[axis])
    def stamp(e,f,u,ctx):
        if (e,f,u,ctx)!=('event','frame','timeunit','context'):forbidden()
        return c(Q(7))
    rows={'zbd':{('event',)},'va':{('frame',)},'ti':{('lengthunit',)},'ci':{('timeunit',)},'zc5':{('tuple',)},'eisdd':{('frame','lengthunit','timeunit','context')},'sd':{('frame','context','lengthunit','timeunit')},'eiuk':{('event','frame','timeunit','context')},'zzbu':{('event','frame','context','lengthunit','timeunit',Q(7),Q(2),Q(-3),Q(4))}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};m|={'zc6':component,'zbe':stamp}
    check=lambda mm:run('eiuz',['event','tuple','frame','context'],mm)
    count=perturb(check,m,rows,norm)
    for axis in components:
        changed=lambda tup,a,axis=axis:c(components[a]+(1 if a==axis else 0))
        assert not check(m|{'zc6':changed});count+=1
    assert not check(m|{'zbe':lambda *xs:c(Q(8))});count+=1
    for name in ('ba','zzba'):
        assert not check(m|{name:lambda x:False});count+=1
    # If only the local-clock time differs, numeric equality still rejects it.
    assert not check(m|{'sca':lambda a,b:False});count+=1
    for a,b in (('yn','yo'),('yn','yp'),('yn','zc7'),('yo','yp'),('yo','zc7'),('yp','zc7')):
        assert not check(m|{a:constants()[b]});count+=1
    # Distinct length/time units remain a structural requirement even if all
    # boundary relations accept the collision.
    yes={n:lambda *xs:True for n in rows};yes|={'zbe':lambda *xs:c(Q(7))}
    assert not check(m|yes|{'rb':lambda:'lengthunit'});count+=1
    unknowns(check,m,('zc6','zbe','ba','zzba','sca'))
    try:run('eiuz',['event','tuple','frame','context'],m,'native_uniqueness')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Complete coordinate uniqueness silently sampled')
    return dict(cases=count,three_coordinates_and_time_same_event_units_and_frame=True,native_sha_and_sa_with_current_eiuk_boundary=True,all_real_coordinate_uniqueness_preserved_and_refused=True,unknown_components_not_zero=True)

@lru_cache(None)
def correspondence_checks():
    args=['zero','one','zero','one','context'];count=0
    base={'eiuo':relation({('zero','one','context')}),'zbd':lambda e:True}
    # With only two carrier values, distinguish every source/target witness.
    for source,target in product(SMALL,repeat=2):
        rows={(source,'zero','zero','context'),(target,'one','one','context')}
        model=base|{'eiuz':relation(rows)}
        assert run('eiu2',args,model,domain=SMALL)==(source==target);count+=1
    rows={'eiuo':{('zero','one','context')},'zbd':{('zero',)},'eiuz':{('zero','zero','zero','context'),('zero','one','one','context')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiu2',args,mm,domain=SMALL),m,rows)
    for slot in range(5):
        bad=list(args);bad[slot]='other' if slot==4 else ('one' if bad[slot]=='zero' else 'zero')
        assert not run('eiu2',bad,m,domain=SMALL);count+=1
    assert not run('eiu2',args,m|{'eiuz':relation({('zero','zero','one','context'),('zero','one','zero','context')})},domain=SMALL);count+=1
    assert not run('eiu2',args,m|{'eiuz':lambda *xs:False},domain=SMALL);count+=1
    return dict(cases=count,same_event_witness_not_two_different_events=True,source_and_target_direction_and_all_argument_slots=True,current_nonzero_uniform_motion_and_assignments_bound=True)

@lru_cache(None)
def topic_checks():
    rows={'eismr':{('inquiry','eiu2','context')}};m={'eismr':relation(rows['eismr'])}
    count=perturb(lambda mm:run('eiu3',['inquiry','context'],mm),m,rows)
    assert run('eiu3',['inquiry','context'],m|{n:forbidden for n in ('eiuo','eiuz','eiuk','zc6','zzbu','sd')});count+=1
    return dict(cases=count,directed_correspondence_is_theory_subject=True,no_formula_discovery_or_physical_model_execution_implied=True)

@lru_cache(None)
def heading_checks():
    rows={'eisdv':{('node','section','part','paper',Q(2),Q(3),'discourse')},'eisdw':{('node','section','eiu3','discourse')},'ue':{('previous','node','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiu4',[],mm),m,rows)
    for n,x in (('eismt','section'),('eisms','part'),('zbk','node')):
        assert not run('eiu4',[],m|{p:lambda *xs:True for p in rows}|{n:lambda x=x:x});count+=1
    assert run('eiu4',[],m|{n:forbidden for n in ('eismr','eiuo','eiuz','eiuk','zc6','zzbu','sd')});count+=1
    return dict(cases=count,section_three_depth_two_parent_part_one=True,preceding_conclusion_order_and_distinct_nodes=True,heading_not_physical_assertion=True)

def test_profile_and_exact_projection():
    voc=check.vocabulary();parent=check.previous.vocabulary().document();new=voc.document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new[field].get(k)==v for k,v in parent[field].items())
    assert len(voc._words)==705
    doc=check.restored()['document'];ds={d['name']:d for d in doc['declarations']}
    assert doc['statements'][:-1]==check.previous.document()['statements']
    assert all(ds[d['name']]==d for d in check.previous.document()['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(check.source_excerpt()['declarations'])==106
    assert check.bridge()['source_statement_indices']==[102]


def test_physical_four_tuple_assignment():assert assignment_checks()['all_real_coordinate_uniqueness_preserved_and_refused']
def test_same_event_and_directed_correspondence():assert correspondence_checks()['same_event_witness_not_two_different_events']
def test_topic_does_not_execute_physics():assert topic_checks()['no_formula_discovery_or_physical_model_execution_implied']
def test_heading_depth_ordinal_and_preceding_conclusion():assert heading_checks()['preceding_conclusion_order_and_distinct_nodes']


def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]
def context(doc):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}


def test_new_references_are_acyclic_and_do_not_execute_roles():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    for old in ('eismt','eisms','zc7'):
        doc['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        assert native_run(doc,context(doc)|dict(expected=lambda:check.BASE[old]))==[True]
        assert native_run(doc,context(doc)|dict(expected=lambda:'other'))==[False]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())


def test_connected_native_heading():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][62:63]
    rows={'eisdv':{('eismt','eisms','eisdx','doc',Q(2),Q(3),'body')},'eisdw':{('eismt','eisms','eiu3','body')},'ue':{('zbk','eismt','body')}}
    h=context(doc)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]
    for n in rows:assert native_run(doc,h|{mapping()[n]:lambda *xs:False})==[False]


def test_reference_keys_roles_and_heading_position():
    from scripts.temporal_discourse_profile import ROLE
    b=check.BASE;model=check.reference_model(b)
    for old,name in [('eisms','sectionrole'),('zc7','timecomponentrole')]:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.names()[name])),json.dumps(ROLE,sort_keys=True,separators=(',',':')),0)
        key=[b['eirf'],b['eismt'],role,b['ri']]
        assert model.described(*key)==b[old]
        for i in (0,1,3):
            bad=list(key);bad[i]='unknown'
            with pytest.raises(ValueError):model.described(*bad)
        for bad in (True,DescriptionValue(role.syntax,role.result_type,1),DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.names()['eiu3'])),role.result_type,0)):
            with pytest.raises(ValueError):model.described(key[0],key[1],bad,key[3])
    h=check.context_handlers(b)['headingreference']
    assert h(b['ri'],Q(4))==b['eismt']
    assert h(b['ri'],Q(3))!=b['eismt']
    for bad in (0,-1,Q(1,2),True,4.0,'4',99):
        with pytest.raises(ValueError):h(b['ri'],bad)
    with pytest.raises(ValueError):h('unknown',4)


def test_reference_role_conditions_and_time_component_bindings():
    rows={'eisdv':{('node','section','part','paper',Q(2),Q(3),'discourse')}}
    perturb(lambda mm:run('sectionrole',['section','discourse'],mm),{'eisdv':relation(rows['eisdv'])},rows)
    cuts,m=numbers();c=cuts.make
    # Two-value witness binding diagnostics, with local uniqueness at its
    # explicit boundary. The native physical assignment is checked separately.
    for event,tup,frame in product(SMALL,repeat=3):
        model=m|{n:lambda:'one' for n in ('rb','yn','yo','yp')}
        model|={'zbd':lambda x,e=event:x==e,'va':lambda x,f=frame:x==f,'zc5':lambda x,t=tup:x==t,
            'eiuk':relation({(event,frame,'one','context')}),
            'zc6':lambda t,r,tup=tup:c(Q(7 if (t,r)==(tup,'zero') else 8)),
            'zbe':lambda *xs:c(Q(7))}
        args=['zero','context']
        assert run('timecomponentrole',args,model,domain=SMALL)
        for axis in ('yn','yo','yp'):
            assert not run('timecomponentrole',args,model|{axis:lambda:'zero'},domain=SMALL)
        for p in ('zbd','va','zc5','eiuk'):
            assert not run('timecomponentrole',args,model|{p:lambda *xs:False},domain=SMALL)
        assert not run('timecomponentrole',args,model|{'zbe':lambda *xs:c(Q(9))},domain=SMALL)
        assert not run('timecomponentrole',args,model|{'zc6':lambda *xs:c(Q(9))},domain=SMALL)
        assert not run('timecomponentrole',['zero','other'],model,domain=SMALL)
    unknowns(lambda mm:run('timecomponentrole',['zero','context'],mm,domain=SMALL),model,('zbd','va','zc5','eiuk','zc6','zbe','sca'))


def test_source_heading_scope_and_unchanged_evidence():
    b=check.bridge();assert b['heading_ordinal']==4
    assert b['division']==dict(level=2,ordinal=3,parent='einstein-1905:u0006',scope_first='einstein-1905:u0042',scope_last='einstein-1905:u0108',next_boundary='einstein-1905:u0109')
    doc=deepcopy(check.restored()['document']);doc['statements'][62]['body']=dict(kind='truth',value=True)
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
