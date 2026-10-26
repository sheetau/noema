from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
import json
import pytest
from noema.constructed_semantics import FunctionValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_observer_contrast_visible as check
from scripts import observer_contrast_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
DOMAIN=('observera','observerb','observerc','other','firstend','lastend','carrieda','carriedb','rod','frame','lengthunit','timeunit','x','y','z','author','paper','scope','resultnode','contrastnode','lengthname')
DOMAIN+=('recorda','recordb','recordc')
POINTS=('context','measurement','discourse','other')
def forbidden(*args):raise ValueError('Unknown observer-contrast-visible input')
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
def constants():return {n:lambda x=x:x for n,x in {'yd':'context','xi':'rod','xn':'firstend','xo':'lastend','zaj':'carrieda','zak':'carriedb','zay':'observera','zaz':'observerb','ra':'frame','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z','rd':'author','eirf':'paper','ri':'discourse','xy':'scope','za3':'resultnode','zbb':'contrastnode','eismn':'lengthname'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    selected=NUM|set(constants())|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    selected|={'eiq4','eitm','eip6','eiqg'}
    if mode!='native_history':selected.add('se')
    if name!='eit2':selected.add('eit2')
    if name!='eit3':selected.add('eit3')
    if name=='sdo' and mode!='native_midpoint':selected.add('bi')
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
        except ValueError as e:assert 'Unknown observer-contrast-visible' in str(e),str(e)
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
def rest_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(0,1,2));count=0
    m['zzbg']=lambda a,b:r(a)<r(b)
    def traces(profile):
        return [FunctionValue((RS,),RS,lambda t,a=a:c(Q(4+a)+(r(t) if profile=='drift' and a==1 else r(t)*(2-r(t)) if profile=='return' and a==2 else 0))) for a in range(3)]
    shared=['observera','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2))]
    for profile in ('rest','drift','return'):
        args=shared+traces(profile);row=norm(args)
        model=m|{'se':lambda *xs,row=row:norm(xs)==row,'eisdd':lambda *xs:xs==('frame','lengthunit','timeunit','context')}
        assert run('eit2',args,model)==(profile=='rest');count+=1
    args=shared+traces('rest');rows={'se':{norm(args)},'eisdd':{('frame','lengthunit','timeunit','context')}}
    model=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda mm:run('eit2',args,mm),model,rows,norm)
    for slot in range(len(args)):
        bad=list(args)
        if slot in (5,6):bad[slot]=c(Q(9))
        elif slot>=7:bad[slot]=FunctionValue((RS,),RS,lambda t:c(Q(9)))
        else:bad[slot]='other'
        assert not run('eit2',bad,model);count+=1
    for lower,upper in ((0,0),(2,0)):
        bad=list(args);bad[5:7]=[c(Q(lower)),c(Q(upper))]
        assert not run('eit2',bad,model|{'se':lambda *xs:True});count+=1
    unknowns(lambda mm:run('eit2',args,mm),model,('ba','bf','bd','shv','bg'))
    try:run('eit2',args,model,'native_history')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Complete real history replaced with finite samples')
    rows={'eit2':{norm(args)},'xb':{('observera',)},'x4':{('observera','frame','context')}}
    fs=traces('rest')
    def selector(who,frame,lu,tu,axis,ctx):
        if (who,frame,lu,tu,ctx)!=('observera','frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return fs[('x','y','z').index(axis)]
    mm=m|{'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'eismh':selector}|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda model:run('eit3',['observera','context'],model),mm,rows,norm)
    unknowns(lambda model:run('eit3',['observera','context'],model),mm,('eisls','eislt','eismh'))
    return dict(cases=count,stationary_representative_uses_two_complete_histories=True,interior_return_motion_not_stationary=True,same_frame_units_interval_and_position_functions=True,full_real_history_refused=True,finite_boundary_samples_not_proof_of_all_times=True)

@lru_cache(None)
def quantity_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,(0,1));rows={'yx':{('context','measurement')},'eiqg':{(Q(6),'measurement')},'eip6':{(Q(6),'measurement')}}
    m|={'zav':lambda:c(Q(6))}|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count=perturb(lambda mm:run('eit4',['rod',c(Q(6)),'measurement'],mm),m,rows,norm)
    for rod,val,ctx in (('other',6,'measurement'),('rod',7,'measurement'),('rod',6,'other')):
        assert not run('eit4',[rod,c(Q(val)),ctx],m);count+=1
    assert not run('eit4',['rod',c(Q(6)),'measurement'],m|{'zav':lambda:c(Q(7))});count+=1
    unknowns(lambda mm:run('eit4',['rod',c(Q(6)),'measurement'],mm),m,('zav','sca'))
    return dict(cases=count,same_rod_current_rest_frame_measurement_and_zav=True)

@lru_cache(None)
def judgment_checks():
    rows={'eitm':{('context',)},'zba':{(o,'sdo',False,'context') for o in ('observera','observerb')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiub',['context'],mm),m,rows)
    assert run('eiub',['context'],m|{n:forbidden for n in ('bi','zag','sdo','eiq4')});count+=1
    rows={'eit3':{('observera','context'),('observerb','context')},'zba':{(o,'eit6',True,'context') for o in ('observera','observerb')},'eisfd':{(o,'eit6','paper','context') for o in ('observera','observerb')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiua',['context'],mm),m,{n:rows[n] for n in ('zba','eisfd')})
    assert not run('eiua',['context'],m|{'eit3':lambda *xs:False});count+=1
    assert not run('eiua',['context'],m|{'eit3':relation(rows['eit3']|{('observerc','context')})});count+=1
    assert run('eiua',['context'],m|{'eit3':relation({('observera','context')})});count+=1
    assert run('eiua',['context'],m|{n:forbidden for n in ('eiq4','bi','ce','se')});count+=1
    unknowns(lambda mm:run('eiua',['context'],mm),m,('eit3','zba','eisfd'))
    # The two clock qualifications are native calls inside the positive content;
    # judging that content does not evaluate them.
    rows={'eiq4':{('carrieda','firstend','context'),('carriedb','lastend','context')}}
    m={'tripcontext':lambda:'context',**{n:relation(rs) for n,rs in rows.items()}}
    count+=perturb(lambda mm:run('eit6',[],mm),m,rows)
    return dict(cases=count,explicit_negative_judgment_not_absence_of_positive=True,same_two_comoving_observers_and_midpoint_content=True,nonempty_stationary_scope_and_all_selected_observers=True,positive_declaration_distinct_from_private_judgment=True,judgment_contents_not_executed_or_assumed_true=True,current_complete_clock_qualification_bound=True)

@lru_cache(None)
def presentation_checks():
    rows={'eislo':{('lengthname','eit4','paper','discourse')},'eisa5':{('contrastnode','author','eitp','eit5','discourse')},'uh':{('contrastnode','author','eiue','scope','discourse')},'eisdk':{('paper','eitp','eiue','discourse')},'zbc':{('contrastnode','author','eiuc','eiud','scope','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiuf',[],mm),m,rows)
    assert run('eiuf',[],m|{n:forbidden for n in ('eitp','eit4','eiua','eiub','zba','eisfd','se')});count+=1
    rows={'eir3':{('contrastnode','author','paper','eiug','discourse')},'ue':{('resultnode','contrastnode','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiuh',[],mm),m,rows)
    assert run('eiuh',[],m|{n:forbidden for n in ('uh','zbc','eisdk','eislo')});count+=1
    return dict(cases=count,hypothetical_scope_reason_and_ordered_contrast=True,length_gloss_supplements_same_previous_result=True,author_attribution_does_not_execute_judgments=True)



def test_profile_backprojection_and_inherited_document():
    voc=check.vocabulary();old=check.previous.vocabulary()
    assert len(voc._words)==699 and len(old._words)==696
    for field in ('entries','compounds','definitions','primitives'):
        assert all(voc.document()[field][n]==d for n,d in old.document()[field].items())
    doc=check.restored()['document'];assert len(doc['statements'])==61
    assert doc['statements'][:59]==check.previous.document()['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in check.previous.document()['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(check.source_excerpt()['declarations'])==219
    assert check.bridge()['source_statement_indices']==[100]

def test_stationary_representative_requires_complete_history():assert rest_checks()['full_real_history_refused']
def test_same_moving_rod_rest_frame_length():assert quantity_checks()['same_rod_current_rest_frame_measurement_and_zav']
def test_opposite_criteria_and_judgment_declaration_distinction():assert judgment_checks()['judgment_contents_not_executed_or_assumed_true']
def test_hypothetical_consequence_gloss_reason_and_contrast():assert presentation_checks()['hypothetical_scope_reason_and_ordered_contrast']


def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]

def context(doc):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}


def test_new_references_are_acyclic_and_do_not_execute_judgments():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    for old in ('contrastsecond','zbb','eismn'):
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


def test_connected_native_attribution_and_length_designation():
    from scripts.name_presentation_profile import scalar_text
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][59:60]
    rows={'eir3':{('zbb','author','doc','eiug','body')},'ue':{('za3','zbb','body')}}
    h=context(doc)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]
    for n in rows:assert native_run(doc,h|{mapping()[n]:lambda *xs:False})==[False]
    doc['statements']=check.restored()['document']['statements'][60:61]
    printed=lambda node,lang,text,ctx:(node,scalar_text(lang),scalar_text(text),ctx)==('eismn','und','r_AB','body')
    assert native_run(doc,context(doc)|{check.vocabulary()._symbols['printedform']:printed})==[True]


def test_token_span_is_a_partial_sentence_then_a_complete_sentence():
    b=check.text_boundaries();first=b['sentences']['za3']['tokens'];last=b['sentences']['contrastsecond']['tokens']
    assert first[:3]==['Unter','Berücksichtigung','des']
    assert first[11:16]==['[M0060]','und','[M0061]','wobei','[M0062]']
    assert first[-1]=='bedeutet.' and last[0]=='Mit' and last[-1]=='würden.'
    original=check.author.read(check.READINGS[0])['segments'][0]['text']
    assert ' '.join(first[14:]+last)==original
    assert b['sentences']['contrastsecond']['position']==[26,4]
    assert b['span']==dict(first_sentence='za3',first_token=15,last_sentence='contrastsecond',last_token=28)
    assert b['includes_whole_first_sentence'] is False


@pytest.mark.parametrize('slot',range(6))
def test_span_requires_every_reference_key(slot):
    refs=check.token_model(check.BASE)
    key=(check.BASE['eirf'],check.BASE['za3'],15,check.BASE['contrastsecond'],28,check.BASE['ri'])
    assert refs.span(*key)==check.BASE['zbb']
    bad=list(key);bad[slot]=14 if slot in (2,4) else 'unknown'
    with pytest.raises(ValueError):refs.span(*bad)


def test_token_span_order_bounds_and_exact_numbers():
    layouts={('doc','body'):[('first',6),('second',4)]}
    spans={('doc','first',3,'second',4,'body'):'a',('doc','first',3,'first',5,'body'):'b',('doc','second',1,'second',4,'body'):'c'}
    refs=profile.TokenSpanReferences(layouts,spans)
    assert refs.span('doc','first',Q(3),'second',4,'body')=='a'
    assert refs.span('doc','first',3,'first',5,'body')=='b'
    assert refs.span('doc','second',1,'second',4,'body')=='c'
    invalid=[('doc','first',7,'second',4,'body'),('doc','first',3,'second',5,'body'),('doc','second',1,'first',5,'body'),('doc','first',5,'first',3,'body')]
    for key in invalid:
        with pytest.raises(ValueError):refs.span(*key)
        with pytest.raises(ValueError):profile.TokenSpanReferences(layouts,{key:'bad'})
    for bad in (0,-1,Q(1,2),True,3.0,'3'):
        for slot in (2,4):
            key=list(next(iter(spans)));key[slot]=bad
            with pytest.raises(ValueError):refs.span(*key)
    with pytest.raises(ValueError):profile.TokenSpanReferences({('doc','body'):[('first',3),('first',4)]},{})


def test_changed_source_cannot_reuse_old_projection():
    doc=deepcopy(check.restored()['document']);doc['statements'][59]['body']=dict(kind='truth',value=True)
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)


def test_midpoint_content_uses_same_three_record_readings_in_order():
    cuts,m=numbers();c=cuts.make
    readings={'recorda':Q(1),'recordb':Q(3),'recordc':Q(5)}
    def reading(record):
        if record not in readings:forbidden()
        return c(readings[record])
    # Distinguishing arguments at the midpoint predicate boundary, not a proof
    # of its equality of arbitrary real cuts over the full rational domain.
    m|={'zas':lambda:'recorda','zat':lambda:'recordb','zau':lambda:'recordc','zag':reading,
        'bi':lambda a,b,d:tuple(map(cuts.read,(a,b,d)))==(Q(1),Q(3),Q(5))}
    assert run('sdo',[],m)
    for record in readings:
        changed=readings|{record:readings[record]+Q(1,4)}
        assert not run('sdo',[],m|{'zag':lambda rec:c(changed[rec])})
    for key in ('zas','zat','zau'):
        with pytest.raises(ValueError):run('sdo',[],m|{key:lambda:'other'})
    assert not run('sdo',[],m|{'zas':lambda:'recordc','zau':lambda:'recorda'})
    unknowns(lambda mm:run('sdo',[],mm),m,('zag','bi'))
    with pytest.raises(ValueError,match='rational number domain'):
        run('sdo',[],m,mode='native_midpoint')


def test_result_connects_both_observer_groups_under_same_setting():
    rows={'eitm':{('context',)},'eit3':{('observerc','context')},
        'zba':{('observera','sdo',False,'context'),('observerb','sdo',False,'context'),('observerc','eit6',True,'context')},
        'eisfd':{('observerc','eit6','paper','context')}}
    model={n:relation(rs) for n,rs in rows.items()}
    assert run('eiue',[],model)
    for key in rows:assert not run('eiue',[],model|{key:lambda *xs:False})
    assert not run('eiue',[],model|{'yd':lambda:'other'})
    assert run('eiue',[],model|{'sdo':forbidden,'bi':forbidden,'eiq4':forbidden})
