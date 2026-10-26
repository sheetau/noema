from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json
import pytest
from noema.constructed_semantics import FunctionValue,DescriptionValue,Content,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_simultaneity_conclusion_visible as check
from scripts import simultaneity_conclusion_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
DOMAIN=('event','display','clock','reference','place','frame','otherframe','unit','lengthunit','x','y','z','author','paper','previous','conclusion','other')
POINTS=('comparison','discourse','other')
SMALL=('zero','one')

def forbidden(*args):raise ValueError('Unknown simultaneity-conclusion-visible input')
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
def constants():return {n:lambda x=x:x for n,x in {'rb':'unit','rd':'author','eirf':'paper','ri':'discourse','zbj':'comparison','zbb':'previous','zbk':'conclusion','yn':'x','yo':'y','yp':'z'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    selected=NUM|set(constants())|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    selected|={'qo','eiok'}
    if mode in ('projection','native_uniqueness'):selected|={'seg','eiuj'}
    elif name in ('eium','eiun'):selected|={'eiuk','eiul'}
    elif name=='eiuj':selected.add('eiui')
    elif name=='eiul':selected|={'seh','eiuj'}
    elif name in ('eiuq','eiur','eiut'):selected|={'eium','eiun','eiuo'}
    elif name=='eiuw':selected|={'eiur','eiut'}
    elif name=='comparisonrole':selected.add('sdx')
    selected.discard(name)
    for d in doc['declarations']:
        if d['name'] in {m[n] for n in selected if n in m}:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(m[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    if mode=='projection':
        doc=replace_real_sort(doc);ds={d['name']:d for d in doc['declarations']}
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
        except ValueError as e:assert 'Unknown simultaneity-conclusion-visible' in str(e),str(e)
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

def replace_real_sort(node):
    if node==RS:return 'individual'
    if isinstance(node,dict):return {k:replace_real_sort(v) for k,v in node.items()}
    if isinstance(node,list):return [replace_real_sort(v) for v in node]
    return node


@lru_cache(None)
def local_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,());count=0
    rows={'zbd':{('event',),('display',)},'va':{('frame',)},'eisb7':{('frame','reference','unit','comparison')},'ca':{('clock',),('reference',)},'cc':{('clock','frame'),('reference','frame')},'ci':{('unit',)},'cb':{('clock','place','frame'),('event','place','frame'),('display','place','frame')},'ce':{('clock',e,'frame','unit',Q(7)) for e in ('event','display')},'qo':{('clock','reference','frame','unit','comparison')},'eisgm':{('event','display','clock','frame','comparison')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m['zbh']=lambda f,ctx:'reference' if (f,ctx)==('frame','comparison') else 'other'
    args=['event','clock','place','frame','unit',c(Q(7)),'comparison']
    count+=perturb(lambda mm:run('eiui',args,mm),m,rows,norm)
    for i in range(len(args)):
        bad=list(args);bad[i]=c(Q(9)) if i==5 else 'other'
        assert not run('eiui',bad,m),(i,bad);count+=1
    assert not run('eiui',args,m|{'ba':lambda x:False});count+=1
    unknowns(lambda mm:run('eiui',args,mm),m,('zbh','ba'))
    # Test existential bindings on two values; native local-body evidence is above.
    for clock,place in product(SALL:=SMALL,repeat=2):
        args=['zero','one','zero',c(Q(7)),'comparison'];row=('zero',clock,place,'one','zero',Q(7),'comparison')
        mm={'eiui':lambda *xs,row=row:norm(xs)==row}
        assert run('eiuj',args,mm,domain=SMALL);count+=1
        assert not run('eiuj',args,{'eiui':lambda *xs:False},domain=SMALL);count+=1
        for i in (0,3,4,5,6):
            bad=list(row);bad[i]=Q(9) if i==5 else 'other' if i==6 else ('one' if row[i]=='zero' else 'zero')
            assert not run('eiuj',args,{'eiui':lambda *xs,bad=tuple(bad):norm(xs)==bad},domain=SMALL);count+=1
    unknowns(lambda mm:run('eiuj',['zero','one','zero',c(Q(7)),'comparison'],mm,domain=SMALL),{'eiui':lambda *xs:True},('eiui',))
    return dict(cases=count,native_saf_common_reference_and_same_local_display=True,two_value_existential_binding_all_slots=True,unknown_values_rejected=True)

@lru_cache(None)
def time_checks():
    count=0
    # Keep seh's quantification; project only the real carrier to two values.
    for available,candidate,display,equal in product((False,True),repeat=4):
        rows={'zero'} if available else set()
        if equal:rows.add('one')
        stamp='zero' if candidate else 'one'
        model={'zbe':lambda *xs,s=stamp:s,'seg':lambda e,f,u,t,c,sync,valid,rows=rows:t in rows and (e,f,u,c)==('zero','one','zero','comparison'),'eiuj':lambda e,f,u,t,c:display and (e,f,u,t,c)==('zero','one','zero',stamp,'comparison'),'sca':lambda a,b:a==b}
        expected=stamp in rows and len(rows)==1 and display
        assert run('eiuk',['zero','one','zero','comparison'],model,'projection',SMALL)==expected;count+=1
    # Distinct representations may denote the same time; numeric equality is used.
    model={'zbe':lambda *xs:'zero','seg':lambda *xs:True,'eiuj':lambda *xs:True,'sca':lambda a,b:True}
    assert run('eiuk',['zero','one','zero','comparison'],model,'projection',SMALL);count+=1
    unknowns(lambda mm:run('eiuk',['zero','one','zero','comparison'],mm,'projection',SMALL),model,('zbe','seg','eiuj','sca'))
    cuts,m=numbers();c=cuts.make
    try:run('eiuk',['event','frame','unit','comparison'],m|{'zbe':lambda *xs:c(Q(7)),'seg':lambda *xs:True,'eiuj':lambda *xs:True},'native_uniqueness')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Real uniqueness silently sampled')
    norm=norm_factory(cuts,());rows={'va':{('frame',)},'zbd':{('event',),('display',)},'eisb7':{('frame','reference','unit','comparison')},'seh':{(e,'frame','unit','comparison') for e in ('event','display')},'eiuj':{(e,'frame','unit',Q(7),'comparison') for e in ('event','display')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items() if n!='seh'}
    # seh's three passed functions are preserved in production; its full-real
    # body was checked with explicit projection above, not enumerated here.
    m['seh']=lambda e,f,u,ctx,*fs:(e,f,u,ctx) in rows['seh']
    m|={'zbh':lambda *xs:'reference','zbe':lambda *xs:c(Q(7))}
    count+=perturb(lambda mm:run('eiul',['event','display','frame','unit','comparison'],mm),m,{n:rs for n,rs in rows.items() if n!='seh'},norm)
    for e in ('event','display'):
        assert not run('eiul',['event','display','frame','unit','comparison'],m|{'seh':lambda event,*xs,e=e:event!=e});count+=1
        assert not run('eiul',['event','display','frame','unit','comparison'],m|{'zbe':lambda event,*xs,e=e:c(Q(9 if event==e else 7))});count+=1
    unknowns(lambda mm:run('eiul',['event','display','frame','unit','comparison'],mm),m,('seh','zbe','zbh','sca'))
    for root,target,args,row in [('eium','eiuk',['event','frame','comparison'],('event','frame','unit','comparison')),('eiun','eiul',['event','display','frame','comparison'],('event','display','frame','unit','comparison'))]:
        count+=perturb(lambda mm:run(root,args,mm),{target:relation({row})},{target:{row}})
    return dict(cases=count,all_real_uniqueness_preserved_and_native_domain_refused=True,candidate_existence_display_uniqueness_and_numeric_equality_separated=True,same_event_frame_unit_context_connected=True)

@lru_cache(None)
def motion_checks():
    cuts,m=numbers();c=cuts.make;count=0
    def speed(xs,components):
        f,g,lu,tu,axis,ctx=xs
        if (f,g,lu,tu,ctx)!=('frame','otherframe','lengthunit','unit','comparison') or axis not in ('x','y','z'):forbidden()
        return c(Q(components[('x','y','z').index(axis)]))
    model=m|{'eiok':relation({('frame','otherframe','comparison')}),'eisli':lambda *xs:'lengthunit','eislj':lambda *xs:'unit'}
    for components in ((0,0,0),(1,0,0),(0,-2,0),(0,0,3),(-3,4,5)):
        mm=model|{'eislc':lambda *xs,cs=components:speed(xs,cs)}
        assert run('eiuo',['frame','otherframe','comparison'],mm)==any(components);count+=1
    model|={'eislc':lambda *xs:speed(xs,(0,-2,0))}
    count+=perturb(lambda mm:run('eiuo',['frame','otherframe','comparison'],mm),model,{'eiok':{('frame','otherframe','comparison')}})
    assert not run('eiuo',['frame','otherframe','comparison'],model|{'ba':lambda x:False});count+=1
    unknowns(lambda mm:run('eiuo',['frame','otherframe','comparison'],mm),model,('eislc','eisli','eislj','ba','sca','bb'))
    return dict(cases=count,current_complete_uniform_translation_bound=True,nonzero_vector_any_axis_and_sign=True,no_position_gap_or_speed_limit_added=True)

@lru_cache(None)
def logic_checks():
    # The carrier can overlap object roles; no huge event/frame product is needed.
    count=0
    for bits in product((False,True),repeat=7):
        available={pair for pair,yes in zip(product(SMALL,SMALL),bits[:4]) if yes}
        first,second,comparable=bits[4:]
        model={'zbd':lambda e:True,'va':lambda f:True,'eiuo':lambda f,g,c:comparable and (f,g,c)==('zero','one','comparison'),'eium':lambda e,f,c:(e,f) in available and c=='comparison','eiun':lambda a,b,f,c:(first if f=='zero' else second) if a!=b else True}
        valid=all(bits[:4]) and comparable
        assert run('eiuq',[],model,domain=SMALL)==(not valid or first==second)
        assert run('eiur',[],model,domain=SMALL)==(not valid or not first or not second);count+=2
    domain=('zero','one','two')
    model={'zbd':lambda e:True,'va':lambda f:True,'eiuo':lambda f,g,c:(f,g,c)==('zero','one','comparison'),'eium':lambda *xs:True,'eiun':lambda a,b,f,c:f=='zero' or 'two' in (a,b)}
    assert not run('eiuq',[],model,domain=domain)
    assert not run('eiur',[],model,domain=domain);count+=2
    assert model['eiun']('zero','one','zero','comparison') and not model['eiun']('zero','one','one','comparison')
    assert model['eiun']('zero','two','zero','comparison') and model['eiun']('zero','two','one','comparison')
    unknowns(lambda mm:run('eiur',[],mm,domain=domain),model,('zbd','va','eiuo','eium','eiun'))
    return dict(cases=count,all_four_availability_bits_checked=True,changed_and_preserved_pairs_do_not_satisfy_universal=True,empty_comparison_truth_not_nonabsoluteness_evidence=True,actual_current_adapters_and_native_sdx_sea_sed=True)

@lru_cache(None)
def norm_checks():
    rows={'eismo':{('author','eiul','eiuq',False,'paper','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eius',[],mm),m,rows)
    assert run('eius',[],m|{n:forbidden for n in ('eiuq','eiul','eiun','eiok')});count+=1
    # Norms quantify the very same four time-availability slots as the claim.
    base={'rd':lambda:'zero','rb':lambda:'zero','eirf':lambda:'one','zbd':lambda e:True,'va':lambda f:True,'eiuo':lambda f,g,c:(f,g,c)==('zero','one','comparison'),'eiun':lambda a,b,f,c:a!=b and f=='zero'}
    normrows={('zero',a,b,'one','zero','eiul',False,'one','comparison') for a,b in (('zero','one'),('one','zero'))}
    for bits in product((False,True),repeat=4):
        available={p for p,yes in zip(product(SMALL,SMALL),bits) if yes}
        m=base|{'eium':lambda e,f,c:(e,f) in available,'eismp':relation(normrows)}
        assert run('eiut',[],m,domain=SMALL);count+=1
        assert run('eiut',[],m|{'eismp':lambda *xs:False},domain=SMALL)==(not all(bits));count+=1
    m=base|{'eium':lambda *xs:True,'eismp':relation(normrows)}
    count+=perturb(lambda mm:run('eiut',[],mm,domain=SMALL),m,{'eismp':normrows})
    unknowns(lambda mm:run('eiut',[],mm,domain=SMALL),m,('eium','eiuo','eiun'))
    return dict(cases=count,prohibition_not_missing_permission_or_physical_truth=True,negative_epistemic_requirement_same_events_target_frame_unit_and_rule=True,norm_requires_all_four_times_and_universal_scope=True)

@lru_cache(None)
def presentation_checks():
    rows={'eismo':{('author','eiul','eiuq',False,'paper','discourse')},'eismq':{('conclusion','author','eius','eiuu','paper','discourse')},'eisdk':{('paper','eiue','eiuv','discourse')}}
    truth=lambda:Content(POINTS,(True,)*len(POINTS));false=lambda:Content(POINTS,(False,)*len(POINTS))
    m={n:relation(rs) for n,rs in rows.items()}|{'eiur':truth,'eiut':truth}
    count=perturb(lambda mm:run('eiuw',[],mm),m,rows)
    for n in ('eiur','eiut'):
        assert not run('eiuw',[],m|{n:false});count+=1
    assert run('eiuw',[],m|{n:forbidden for n in ('eiue','eiuq','eiul')});count+=1
    rows={'eir3':{('conclusion','author','paper','eiux','discourse')},'ue':{('previous','conclusion','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiuy',[],mm),m,rows)
    assert run('eiuy',[],m|{n:forbidden for n in ('eiur','eiut','eismo','eismq','eisdk','eiun','eiok')});count+=1
    assert run('eiuy',[],m|{'eiun':lambda *xs:True,'eiur':false});count+=1
    return dict(cases=count,corrective_contrast_and_previous_reason_preserved=True,assertion_content_contains_claim_and_norm=True,author_attribution_does_not_require_claim_truth=True)

def test_profile_and_exact_projection():
    voc=check.vocabulary();parent=check.previous.vocabulary().document();new=voc.document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new[field].get(k)==v for k,v in parent[field].items())
    assert len(voc._words)==702
    doc=check.restored()['document'];ds={d['name']:d for d in doc['declarations']}
    assert doc['statements'][:-1]==check.previous.document()['statements']
    assert all(ds[d['name']]==d for d in check.previous.document()['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(check.source_excerpt()['declarations'])==189
    assert check.bridge()['source_statement_indices']==[101]


def test_local_display_and_every_existential_binding():assert local_checks()['two_value_existential_binding_all_slots']
def test_time_uniqueness_and_same_reference():assert time_checks()['all_real_uniqueness_preserved_and_native_domain_refused']
def test_motion_all_axes_and_signs():assert motion_checks()['no_position_gap_or_speed_limit_added']
def test_universal_comparison_and_all_four_times():assert logic_checks()['changed_and_preserved_pairs_do_not_satisfy_universal']
def test_interpretive_and_epistemic_requirements():assert norm_checks()['norm_requires_all_four_times_and_universal_scope']
def test_corrective_contrast_and_nonexecuting_attribution():assert presentation_checks()['author_attribution_does_not_require_claim_truth']


def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]
def context(doc):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}


def test_new_references_are_acyclic_and_do_not_execute_comparison():
    doc=deepcopy(check.restored()['document']);n=check.names()
    for old,sort in [('zbk','individual'),('zbj','situation')]:
        d=deepcopy(doc);d['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result=sort))
        d['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        # All physics and comparison primitives remain forbidden, including for
        # empty or unmeasured comparison settings. Obtaining a reference is not
        # a witness to the quoted role or to any simultaneity claim.
        assert native_run(d,context(d)|dict(expected=lambda:check.BASE[old]))==[True]
        alternative='other' if sort=='individual' else check.BASE['ri']
        assert native_run(d,context(d)|dict(expected=lambda:alternative))==[False]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())
    dependencies=set()
    def collect(name):
        if name in dependencies:return
        dependencies.add(name)
        for ref in _references(ds[name].get('body')):collect(ref)
    collect(n['comparisonrole'])
    assert not {n[x] for x in ('zbj','yd','sea','sed','eiuq','eiur')}&dependencies


def test_connected_native_attribution():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][61:62]
    rows={'eir3':{('zbk','author','doc','eiux','body')},'ue':{('zbb','zbk','body')}}
    h=context(doc)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]
    for n in rows:assert native_run(doc,h|{mapping()[n]:lambda *xs:False})==[False]


def test_comparison_reference_rejects_unknown_or_changed_keys():
    from scripts.rod_experiment_profile import SETTING_ROLE
    role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.names()['comparisonrole'])),json.dumps(SETTING_ROLE,sort_keys=True,separators=(',',':')),0)
    b=check.BASE;model=check.setting_model(b);key=[b['eirf'],b['zbk'],role,b['ri']]
    assert model.described(*key)==b['zbj']
    for i in (0,1,3):
        bad=list(key);bad[i]='unknown'
        with pytest.raises(ValueError):model.described(*bad)
    for bad in (True,dict(kind='function_ref',symbol='unregistered'),DescriptionValue(role.syntax,role.result_type,1),DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.names()['eiup'])),role.result_type,0)):
        with pytest.raises(ValueError):model.described(key[0],key[1],bad,key[3])


def test_changed_document_cannot_reuse_evidence():
    doc=deepcopy(check.restored()['document']);doc['statements'][61]['body']=dict(kind='truth',value=True)
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)


def test_comparison_role_binding_without_assuming_nonempty_scope():
    # Two-value binding diagnostics for each witness slot, not a proof of
    # the full physical domain. Native sdx is covered by logic_checks.
    for witness in product(SMALL,repeat=4):
        model={'sdx':lambda *xs,w=witness:xs[:5]==(*w,'comparison')}
        assert run('comparisonrole',['comparison','discourse'],model,domain=SMALL)
        assert not run('comparisonrole',['other','discourse'],model,domain=SMALL)
        for slot in range(4):
            outside=list(witness);outside[slot]='outside'
            assert not run('comparisonrole',['comparison','discourse'],{'sdx':lambda *xs,w=tuple(outside):xs[:5]==(*w,'comparison')},domain=SMALL)
    assert not run('comparisonrole',['comparison','discourse'],{'sdx':lambda *xs:False},domain=SMALL)
    with pytest.raises(ValueError,match='Unknown simultaneity-conclusion-visible'):
        run('comparisonrole',['comparison','discourse'],{'sdx':forbidden},domain=SMALL)
