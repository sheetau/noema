from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
import json
import pytest
from noema.constructed_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_kinematic_replacement as check
from scripts import kinematic_replacement_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
POINTS=('p','q','r')
DOMAIN=POINTS+('body','otherbody','frame','lengthunit','timeunit','xaxis','yaxis','zaxis','author','paper','scope','kinematics','assumptionnode','rewording','forecast','other')
SITUATIONS=('moving','resting','alternative','context')
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
HISTORY={'eiag','eiah','eigy'}
def forbidden(*args):raise ValueError('Unknown kinematic-replacement input')
def value(x):return x
def ask(body):return dict(kind='ask',body=body)
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def abstract(d):
    if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
    d['kind']='primitive';d.pop('body',None)
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
def context(doc,**kwargs):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE,**kwargs).items()}
def native_run(doc,h):return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]

def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','ta':'lengthunit','rb':'timeunit','yn':'xaxis','yo':'yaxis','yp':'zaxis','rd':'author','eirf':'paper','xy':'scope','ri':'context','yd':'moving','zr':'kinematics','zv':'assumptionnode','zw':'rewording','zh':'forecast','ye':'moving','yf':'resting'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);mapping=check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()
    selected=NUM|HISTORY|set(constants())|{'zp'}
    # Physical fixture inputs use the original contract boundary, including
    # fields now projected from typed records. Reference implementations are
    # exercised separately on the full decoded document below.
    selected|={d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    if name=='eiqv':selected|={'eip2','eip6','sbg'}
    if mode=='scope':selected|={'eiqs'}
    if mode=='binding':selected|={'eiqr'}
    if mode=='motion':selected|={'eiad'}
    if mode=='motionbinding':selected|={'eiad','eiaf'}
    selected.discard(name)
    symbols={mapping[n] for n in selected if n in mapping}
    for d in doc['declarations']:
        if d['name'] in symbols:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(mapping[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    target=ds[mapping[name]];slots=[]
    for i,p in enumerate(target['parameters']):
        slot='candidateslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(mapping[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='testcontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('testcontext'))
    doc['statements']=[ask(body)];return doc,slots

def evaluate(doc,m,domain=DOMAIN):
    mapping=check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()
    h=handlers(doc)
    h.update({mapping.get(old,old):f for old,f in m.items() if mapping.get(old,old) in h})
    return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives=h,max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'testcontext':lambda:'context'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)
def unknowns(checker,m,names):
    for n in names:
        with pytest.raises(ValueError,match='Unknown kinematic-replacement'):checker(m|{n:forbidden})

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

def replace_real_sort(node):
    if node==RS:return 'individual'
    if isinstance(node,dict):return {k:replace_real_sort(v) for k,v in node.items()}
    if isinstance(node,list):return [replace_real_sort(v) for v in node]
    return node

def families(cuts,positions,velocity=0):
    def at(axis,p,t):
        if p not in positions:forbidden()
        return cuts.make(Q(positions[p][axis])+(cuts.read(t)-7)*velocity*(axis==0))
    return [FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t:at(i,p,t))) for i in range(3)]


def member(selected):return FunctionValue(('individual',),'truth',lambda p:p in selected)


def snapshot_checks():
    cuts,m=arithmetic();c=cuts.make;count=0
    first={'p':(0,0,0),'q':(2,0,0),'r':(1,1,0)}
    scenarios={
      'identical':(first,True),
      'same_endpoints_hidden_deformation':(first|{'r':(1,0,0)},False),
      'same_xy_different_depth':(first|{'r':(1,1,1)},False),
      'swapped_material_labels':({'p':first['q'],'q':first['p'],'r':first['r']},True),
      'translated_congruent_shape':({p:(x+3,y,z) for p,(x,y,z) in first.items()},False),
      'rotated_congruent_shape':({p:(-y,x,z) for p,(x,y,z) in first.items()},False),
    }
    for label,(second,expected) in scenarios.items():
        args=[member(POINTS),member(POINTS),c(Q(7)),*families(cuts,first),*families(cuts,second)]
        assert run('eiqr',args,m,domain=POINTS)==expected,label;count+=1
    # Exhaustive subset pairs check both inclusions, extra points and nonemptiness.
    for a,b in product(product((False,True),repeat=3),repeat=2):
        left={p for p,yes in zip(POINTS,a) if yes};right={p for p,yes in zip(POINTS,b) if yes}
        args=[member(left),member(right),c(Q(7)),*families(cuts,first),*families(cuts,first)]
        assert run('eiqr',args,m,domain=POINTS)==(bool(left) and left==right);count+=1
    duplicate_first={'p':(0,0,0),'q':(2,0,0),'r':(0,0,0)};duplicate_second=duplicate_first|{'r':(2,0,0)}
    assert run('eiqr',[member(POINTS),member(POINTS),c(Q(7)),*families(cuts,duplicate_first),*families(cuts,duplicate_second)],m,domain=POINTS);count+=1
    for time,expected in ((7,True),(8,False)):
        assert run('eiqr',[member(POINTS),member(POINTS),c(Q(time)),*families(cuts,first,velocity=1),*families(cuts,first)],m,domain=POINTS)==expected;count+=1
    unknown=FunctionValue(('number',),'truth',lambda x:x<7)
    try:run('eiqr',[member(POINTS),member(POINTS),unknown,*families(cuts,first),*families(cuts,first)],m,domain=POINTS)
    except ValueError:pass
    else:raise AssertionError('Unknown time decoded by probing')
    return dict(cases=count,complete_coordinate_images_compared_both_directions=True,interior_and_transverse_shape_changes_detected=True,material_labels_and_multiplicity_not_geometry=True,same_shape_at_other_place_or_time_not_accepted=True)


def setup():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read;m|=constants();m|={'bg':lambda a,b:r(a)<r(b),'va':lambda f:f=='frame','ti':lambda u:u=='lengthunit','ci':lambda u:u=='timeunit'}
    positions={p:(Q(20+i),Q(3),Q(1)) for i,p in enumerate(DOMAIN)}|{'p':(Q(0),Q(0),Q(0)),'q':(Q(2),Q(0),Q(0)),'r':(Q(1),Q(1),Q(0))}
    fs={ctx:families(cuts,positions,velocity=1 if ctx=='moving' else 0) for ctx in SITUATIONS}
    bounds={'moving':(6,8),'resting':(5,9),'alternative':(6,8),'context':(6,8)}
    def family(body,frame,lu,tu,axis,ctx):
        if body not in ('body','otherbody') or (frame,lu,tu)!=('frame','lengthunit','timeunit') or axis not in ('xaxis','yaxis','zaxis') or ctx not in fs:forbidden()
        return fs[ctx][('xaxis','yaxis','zaxis').index(axis)]
    def bound(frame,tu,ctx,i):
        if (frame,tu)!=('frame','timeunit') or ctx not in bounds:forbidden()
        return c(Q(bounds[ctx][i]))
    m|={'eirh':lambda b,p,ctx:b=='body' and p in POINTS and ctx in SITUATIONS,'eislu':family,'eisls':lambda f,u,ctx:bound(f,u,ctx,0),'eislt':lambda f,u,ctx:bound(f,u,ctx,1),'zl':lambda b,mov,rest:(b,mov,rest)==('body','moving','resting')}
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.result=='truth':return tuple(p for p in DOMAIN if x(p))
            if x.result==FS:return tuple(r(x(p)(c(Q(t)))) for p in DOMAIN for t in (7,8))
            forbidden()
        return tuple(one(x) for x in xs)
    def history(ctx):return ('body','frame',ctx,'lengthunit','timeunit',*map(Q,bounds[ctx]),POINTS,*(tuple(r(f(p)(c(Q(t)))) for p in DOMAIN for t in (7,8)) for f in fs[ctx]))
    expected={'eiag':{history('moving')},'eiah':{history('resting')},'eigy':{history('moving'),history('resting')}}
    expected['eiqr']={norm([member(POINTS),member(POINTS),c(Q(7)),*fs['moving'],*fs['resting']])}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in expected.items()}
    return cuts,m,expected,norm


def configuration_checks():
    cuts,m,expected,norm=setup();c=cuts.make;count=0
    args=['body','moving','resting',c(Q(7))];check=lambda mm:run('eiqs',args,mm)
    assert check(m);count+=1
    # The native image comparison is checked above and once with these histories.
    # Binding mutations use an explicit boundary for it to avoid repeating its
    # quadratic point search while changing unrelated history fields.
    binding=lambda mm:run('eiqs',args,mm,mode='binding')
    for n,rs in expected.items():
        for row in rs:
            assert not binding(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs});count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not binding(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs});count+=1
    for n in ('zl','va','ti','ci'):
        assert not binding(m|{n:lambda *xs:False});count+=1
    # Keep image boundary fixed for the guards, with all physical history inputs known.
    for time in (4,9):assert not run('eiqs',['body','moving','resting',c(Q(time))],m|{'eiqr':lambda *xs:True},mode='binding');count+=1
    for lower,upper in ((7,7),(8,6)):
        mm=m|{'eisls':lambda *xs:c(Q(lower)),'eislt':lambda *xs:c(Q(upper)),**{n:lambda *xs:True for n in HISTORY},'eiqr':lambda *xs:True}
        assert not run('eiqs',args,mm,mode='binding');count+=1
    mm=m|{n:lambda *xs:True for n in HISTORY|{'zl','eiqr'}}
    assert not run('eiqs',['body','moving','moving',c(Q(7))],mm,mode='binding');count+=1
    mm|={'eirh':lambda b,p,ctx:b=='body' and p in (('p','q') if ctx=='resting' else POINTS)}
    assert not run('eiqs',args,mm,mode='binding');count+=1
    unknowns(binding,m,('eiag','eiah','eigy','zl','eirh','eislu','eisls','eislt'))
    assert check(m|{'xv':forbidden,'ya':forbidden,'zk':forbidden,'zo':forbidden,'zq':forbidden});count+=1
    # At native boundary an unknown physical input never becomes a false default.
    unknowns(check,m,('zl','eislu'))
    return dict(cases=count,complete_moving_and_resting_rigid_histories_bound=True,same_material_members_and_admissible_configuration_required=True,epoch_inside_both_positive_intervals=True,old_unexpanded_occupancy_and_rigidity_not_used=True)


def scope_checks():
    cuts,m=arithmetic();c=cuts.make;m|=constants();m['zp']=lambda:c(Q(7));count=0
    chosen=('body','otherbody')
    for mask in product((False,True),repeat=2):
        targets={b for b,yes in zip(chosen,mask) if yes}
        for supported in (set(),{'body'},{'otherbody'},set(chosen)):
            model=m|{'zn':lambda b,ctx:ctx=='moving' and b in targets,'eiqs':lambda b,mov,rest,t:b in supported and mov=='moving' and rest=='resting' and cuts.read(t)==7}
            assert run('eiqu',[],model,mode='scope')==(bool(targets) and targets<=supported);count+=1
    for resting in ('resting','alternative'):
        model=m|{'eiqs':lambda b,mov,rest,t:(b,mov,rest,cuts.read(t))==('body','moving',resting,Q(7))}
        assert run('eiqt',['body','moving',c(Q(7))],model,mode='scope');count+=1
    unknowns(lambda mm:run('eiqu',[],mm,mode='scope'),m|{'zn':lambda b,ctx:b=='body','eiqs':lambda *xs:True},('zn','eiqs','zp'))
    return dict(cases=count,nonempty_full_selected_body_range_and_every_body_checked=True,at_least_one_rest_configuration_not_unique=True,epoch_not_identified_with_prior_measurement_time=True)


def length_checks():
    domain=('base','alias','different');numbers={'base':5,'alias':5,'different':4};doc=replace_real_sort(deepcopy(fixture('eiqv')[0]));count=0
    for first_bits,second_bits in product(product((False,True),repeat=3),repeat=2):
        first={p for p,b in zip(domain,first_bits) if b};second={p for p,b in zip(domain,second_bits) if b}
        a={numbers[x] for x in first};b={numbers[x] for x in second}
        m=constants()|{'testcontext':lambda:'context','eip2':lambda v,ctx:ctx=='moving' and v in first,'eip6':lambda v,ctx:ctx=='resting' and v in second,'sbg':lambda v:True,'sca':lambda a,b:numbers[a]==numbers[b]}
        assert evaluate(doc,m,domain)==(len(a)==len(b)==1 and a==b);count+=1
    cuts,m=arithmetic();m|=constants()
    try:run('eiqv',[],m)
    except ValueError as e:assert 'Cannot finitely quantify the rational number domain' in str(e)
    else:raise AssertionError('Real-cut domain silently sampled')
    return dict(cases=count,two_method_values_not_initial_length_compared=True,nonempty_and_value_unique_results_required=True,same_value_aliases_allowed=True,projection_only_and_full_real_domain_refused=True)


def test_existing_public_words_preserved_and_six_old_contracts_exposed():
    old=check.previous.vocabulary();new=check.vocabulary()
    assert len(old._words)==668 and len(new._words)==674
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert set(profile.SOURCE_RELATIONS)=={'zl','zn','zs','zt','zu','zx'}

def test_visible_document_preserves_parent_and_complete_source():
    doc=check.restored()['document'];assert doc==check.document()
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations']) and doc['statements'][:50]==old['statements']
    assert (len(doc['declarations']),len(doc['statements']),len(check.source_excerpt()['declarations']))==(942,51,192)
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['source_statement_indices']==[95] and b['sentence_positions']==dict(zv=[24,1])
    assert b['sentence_ranges']=={'einstein-1905:u0034':[[0,348]]}
    assert b['math'][0]['id']=='M0051' and 'not identified with xv' in b['math'][0]['binding']

def test_tacit_assumptions_rewording_and_author_attribution_keep_quotes():
    for rows,size in ((check.diagnostics(),8),(check.presentation_diagnostics(),11)):
        assert len(rows)==size and rows[0]['values']==[True]
        assert all(r['values']==[False] for r in rows[1:])
    # Missing explicitness must raise; negation cannot turn missing input into truth.
    doc=deepcopy(check.restored()['document']);n=check.names();m=check.mapping()
    doc['statements']=[ask(dict(kind='evaluate',content=call(n['eiqw']),situation=call(n['ri'])))]
    h=context(doc)|{m[k]:lambda *xs:True for k in ('zs','zt')}
    with pytest.raises(ValueError,match='Unknown kinematic-replacement'):native_run(doc,h)

def test_native_references_are_acyclic_and_do_not_execute_roles():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    for old in (*check.SENTENCES,*check.ROLE_ASSIGNMENTS):
        doc['statements']=[ask(op('equal',call(n[old]),call('expected')))]
        assert native_run(doc,context(doc)|dict(expected=lambda:check.BASE[old]))==[True]
        assert native_run(doc,context(doc)|dict(expected=lambda:'other'))==[False]
    doc['declarations'].append(dict(kind='primitive',name='epochcapture',parameters=[RS],result='truth'))
    doc['statements']=[ask(call('epochcapture',call(n['zp'])))]
    # The separate comparison epoch is 7 here; the parent's length reference is 1.
    assert native_run(doc,context(doc)|dict(epochcapture=lambda t:t(Q(6)) and not t(Q(7))))==[True]
    doc['statements']=[ask(call('epochcapture',call(n['ya'])))]
    assert native_run(doc,context(doc)|dict(epochcapture=lambda t:t(Q(0)) and not t(Q(1))))==[True]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in (*check.ROLE_ASSIGNMENTS,*check.CUT_ASSIGNMENTS):visit(n[old],set())

@pytest.mark.parametrize('field',range(4))
def test_all_reference_keys_are_required(field):
    n=check.names();doc=deepcopy(check.document())
    for old,role in check.reference_roles().items():
        roles=check.role_model(check.BASE);key=(check.BASE['eirf'],check.BASE['zv'],check.canonical(dict(kind='function_ref',symbol=role)),check.BASE['ri'])
        found=roles.pop(key);bad=list(key);bad[field]='unknown';roles[tuple(bad)]=found
        doc['statements']=[ask(op('equal',call(n[old]),call(n[old])))]
        with pytest.raises(ValueError,match='Unknown temporal reference'):native_run(doc,context(doc,roles=roles))
    cuts=check.cut_model(check.BASE);key=next(iter(cuts));found=cuts.pop(key);bad=list(key);bad[field]='unknown';cuts[tuple(bad)]=found
    doc['declarations'].append(dict(kind='primitive',name='capture',parameters=[RS],result='truth'))
    doc['statements']=[ask(call('capture',call(n['zp'])))]
    with pytest.raises(ValueError,match='Unknown cut reference'):native_run(doc,context(doc,cuts=cuts)|dict(capture=lambda t:True))

def test_native_epoch_role_uses_candidate_and_all_targets():
    # Abstract only the physical replacement predicate and its context: inspect
    # the role's own nonempty/all-target binding with a two-body domain.
    doc,slots=fixture('kinematicroleepoch','scope');cuts,m=arithmetic();c=cuts.make
    for targets in (set(),{'body'},{'otherbody'},{'body','otherbody'}):
        for supported in (set(),{'body'},{'otherbody'},{'body','otherbody'}):
            for epoch in (7,8):
                h=m|constants()|{'zn':lambda b,s:s=='moving' and b in targets,'eiqs':lambda b,mov,rest,t:b in supported and mov=='moving' and rest=='resting' and cuts.read(t)==7}
                assert run('kinematicroleepoch',[c(epoch),'context'],h,mode='scope',domain=('body','otherbody'))==(bool(targets) and targets<=supported and epoch==7)

def test_native_system_and_rewording_roles_preserve_all_relation_arguments():
    doc=deepcopy(check.restored()['document']);n=check.names();m=check.mapping();inverse={v:k for k,v in m.items()}
    doc['declarations'].append(dict(kind='primitive',name='candidate',parameters=[],result='individual'))
    facts=check.presentation_facts();slots=dict(zt=(1,),zu=(1,),zx=(3,4))
    def relation(name,rows):
        def accept(*args):
            args=list(args)
            for i in slots.get(name,()):
                expr=renamed(json.loads(args[i].syntax),inverse);args[i]=(expr['kind'],expr['symbol'])
            return tuple(args) in rows
        return accept
    for old,role in check.reference_roles().items():
        doc['statements']=[ask(call(role,call('candidate'),call(n['ri'])))]
        h=context(doc)|dict(candidate=lambda:check.BASE[old])|{m[k]:relation(k,rows) for k,rows in facts.items()}
        assert native_run(doc,h)==[True]
        assert native_run(doc,h|dict(candidate=lambda:'other'))==[False]
        used=('zs','zt') if old=='zr' else ('zx',)
        for name in used:
            # The system reference specifies the first assumption only.
            relevant=facts[name][:1] if name=='zt' else facts[name]
            for row in relevant:
                for slot in range(len(row)):
                    changed=list(row);changed[slot]='other'
                    altered=[r for r in facts[name] if r!=row]+[tuple(changed)]
                    assert native_run(doc,h|{m[name]:relation(name,altered)})==[False]
        if old=='zr':
            assert native_run(doc,h|{m['zu']:relation('zu',[facts['zt'][0]])})==[False]

def test_native_geometry_compares_complete_coordinate_images():
    assert snapshot_checks()['cases']==73

def test_native_physical_configuration_binds_every_history_slot():
    r=configuration_checks();assert r['cases']>50 and r['epoch_inside_both_positive_intervals']

def test_native_scope_requires_each_target_but_not_unique_rest_configuration():
    assert scope_checks()['cases']==18

def test_native_length_equality_requires_values_not_unique_representations():
    assert length_checks()['cases']==64

def test_native_motion_witness_requires_member_ordered_times_and_position_change():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read
    m|={'eiad':lambda *args:True,'zzbg':lambda a,b:r(a)<r(b)}
    # Give the nonmember a known moving position too: membership must exclude
    # it even when its coordinate functions and ordered times are valid.
    points={'p':(0,0,0),'q':(2,0,0),'r':(1,1,0),'other':(3,2,1)}
    for velocity in (0,1):
        history=['body','frame','moving','lengthunit','timeunit',c(6),c(8),member(POINTS),*families(cuts,points,velocity)]
        for point,t,u in (('p',6,7),('p',7,6),('p',7,7),('p',5,7),('p',7,9),('other',6,7)):
            expected=velocity==1 and point in POINTS and 6<=t<u<=8
            assert run('eiaf',history+[point,c(t),c(u)],m,mode='motion')==expected
        assert not run('eiaf',history+['p',c(6),c(7)],m|{'eiad':lambda *args:False},mode='motion')

def test_motion_existentials_bind_each_witness_slot_on_two_values():
    doc,slots=fixture('eiag','motionbinding');projected=replace_real_sort(doc)
    domain=('early','late');memberfn=FunctionValue(('individual',),'truth',lambda x:True)
    family=FunctionValue(('individual',),dict(kind='function',parameters=['individual'],result='individual'),lambda p:FunctionValue(('individual',),'individual',lambda t:t))
    args=['early','late','moving','early','late','early','late',memberfn,family,family,family]
    base={n:(lambda x=x:x) for n,x in zip(slots,args)}|{'eiad':lambda *xs:True}
    # Keep the other two witnesses fixed and vary one binder at a time.
    for slot in range(3):
        for chosen in domain:
            witness=['early']*3;witness[slot]=chosen;seen=[]
            def predicate(*xs):
                seen.append(tuple(xs[-3:]));return tuple(xs[-3:])==tuple(witness)
            assert evaluate(projected,base|{'eiaf':predicate},domain)
            assert tuple(witness) in seen
    assert not evaluate(projected,base|{'eiaf':lambda *xs:False},domain)
    assert not evaluate(projected,base|{'eiad':lambda *xs:False,'eiaf':lambda *xs:True},domain)
    with pytest.raises(ValueError,match='Cannot finitely quantify the rational number domain'):
        nativeargs=args[:5]+[cut(0),cut(1),memberfn,*[FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,lambda t:t)) for _ in range(3)]]
        evaluate(doc,{n:(lambda x=x:x) for n,x in zip(slots,nativeargs)}|{'eiad':lambda *xs:True,'eiaf':lambda *xs:True},domain)

def test_changed_composition_or_reference_cannot_reuse_evidence():
    for old in (*check.NEW_DEFINITIONS,*check.ROLE_HELPERS,*check.ROLE_ASSIGNMENTS,*check.CUT_ASSIGNMENTS):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
