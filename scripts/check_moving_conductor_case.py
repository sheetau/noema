"""Check motional driving, scoped denials, shared cases and nested discourse."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.extraction import extract_document
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM,RS
from scripts.check_conductor_cases import sentinel,same_value
from scripts.compose_moving_conductor_case import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,BASE,RESULT,FIELDS,FIRST_FIELDS,EXAMPLE,NEIGHBOR,ELIGIBILITY,CALIBRATION,UNIT,DRIVE,DRIVE_POINT,RESPONSE,ENERGY,ENERGY_HISTORY,ZERO_FIELD,ZERO_POINT,VECTOR,COMPARISON,RELATIVE,PAIRED,MEANINGS,PRIMITIVES,motion,history,current_args,build

DOC='docs/moving-conductor-case-v1.md';READING='data/moving-conductor-case-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=['data/einstein-author-credit-review-v1.json','data/interaction-example-reading-v1.json','data/observable-contrast-reading-v1.json','data/moving-magnet-case-reading-v1.json']
DOMAIN=('body','other','x','y','z','t','node','prior','author','paper','view','process')
CONTEXTS=('first','text','other')
def forbidden(*xs):raise ValueError('Unknown moving-conductor input')
def symbol(x):return json.loads(x.syntax)['symbol']
def names(xs):return [x.removeprefix('v ') for x in xs]
def evaluate(doc,model,individuals=DOMAIN):
    ps={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=individuals,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in ps},max_steps=1000000,memoize_definitions=False,memoize_expressions=False)

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=set(NUM)|{'szi'}
    groups={'eiea':{'eic2','eiag','eiah'},'eier':{'eid2','eid3','lg'},'eiet':{'eidr'},'eieb':{'eidn','eieq','eier','eies','eiet'},
        'eiee':{'eida','eidm','eiea','eids','eieb'},'eief':{'eiee','eia2','eibi'},'eiec':{'eiea','eieb'},'eieq':{'eid5'},'eies':{'eid7'}}
    boundaries|=groups.get(name,set());abstract(doc,boundaries)
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='witness':
        tail=d['body']['arguments'][1]
        while tail['kind']=='exists':d['parameters'].append(dict(name=tail['variable'],sort=tail['sort']));tail=tail['body']
        d['body']['arguments'][1]=tail
    slots=[];calls=[]
    for i,p in enumerate(d['parameters']):
        n='jmcc'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        calls.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=calls))]
    return doc,slots

def run(name,values,model,mode='native'):
    doc,slots=fixture(name,mode);assert len(values)==len(slots);model=dict(model)
    for (n,s),value in zip(slots,values):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    return evaluate(doc,model)[0]['value']

def setup(name,fields,mode='native'):
    cuts,base=arithmetic();slots=fixture(name,mode)[1];assert len(fields)==len(slots)
    supplied=[sentinel(s,i+1,cuts) for i,(_,s) in enumerate(slots)];pos={n:i for i,(n,_) in enumerate(fields)}
    def gate(keys,xs,bit=True):return bit and len(xs)==len(keys) and all(same_value(x,supplied[pos[n]],slots[pos[n]][1],cuts) for x,n in zip(xs,keys))
    return cuts,base,slots,supplied,pos,gate

def binding_group(name,fields,calls,special=None):
    cuts,base,slots,supplied,pos,gate=setup(name,fields);used={n for keys in calls.values() for n in keys}
    if special:used|={'lower','upper','point','right','frame','context','lengthunit','timeunit'}
    def local(missing=None):
        m=dict(base,yn=lambda:'x',yo=lambda:'y',yp=lambda:'z',zc7=lambda:'t')
        for callee,keys in calls.items():
            def callback(*xs,callee=callee,keys=keys):
                if callee=='eisas':assert symbol(xs[-1])=='eidz';xs=xs[:-1]
                return gate(keys,xs,callee!=missing)
            m[callee]=callback
        if special:
            m['lg']=lambda lo,hi,t:gate(['lower','upper'],(lo,hi)) and cuts.read(t)==cuts.read(supplied[pos['point']]('t')) and missing!='lg'
            m['eiro']=lambda body,frame,ctx,lu,tu,*xs:gate(['right','frame','context','lengthunit','timeunit'],(body,frame,ctx,lu,tu)) and all(cuts.read(x)==cuts.read(supplied[pos['point']](axis)) for x,axis in zip(xs,('x','y','z','t'))) and missing!='eiro'
        return m
    assert run(name,supplied,local())
    for i,(field,_) in enumerate(fields):
        changed=supplied.copy();changed[i]=sentinel(slots[i][1],100+i,cuts)
        assert run(name,changed,local())==(field not in used),(name,field)
        old=supplied[i];supplied[i]=changed[i];assert run(name,changed,local()),(name,field,'distinguishing');supplied[i]=old
    missing=list(calls)+(['lg','eiro'] if special else [])
    for callee in missing:assert not run(name,supplied,local(callee)),(name,callee)
    return dict(argument_mutations=len(fields),forwarded_arguments=len(used),missing_connections=len(missing))

@lru_cache(None)
def case_checks():
    rows={}
    rows['eiea']=binding_group('eiea',BASE,{'eisap':[n for n,_ in ELIGIBILITY],'eic2':[n for n,_ in EXAMPLE],'eiah':names(motion('left')),'eiag':names(motion('right'))})
    rows['eier']=binding_group('eier',FIELDS,{'eid2':[n for n,_ in CALIBRATION],'eisas':[n for n,_ in DRIVE[:-1]],'eid3':[n for n,_ in DRIVE_POINT]},special=True)
    rows['eiet']=binding_group('eiet',FIELDS,{'eisau':[n for n,_ in RESPONSE],'eidr':names(history())+['section','orientation','time']})
    rows['eieb']=binding_group('eieb',FIELDS,{'eisal':[n for n,_ in NEIGHBOR],'eidn':names(motion('right'))+['region'],**{n:[f for f,_ in FIELDS] for n in ('eieq','eier','eies','eiet')}})
    rows['eieq']=binding_group('eieq',FIELDS,{'eid5':[n for n,_ in ZERO_FIELD]})
    rows['eies']=binding_group('eies',FIELDS,{'eid7':[n for n,_ in ENERGY_HISTORY]})
    cuts,base,slots,values,pos,gate=setup('eiec',FIELDS,'witness')
    for premise,result in product((False,True),repeat=2):assert run('eiec',values,dict(eiea=lambda *xs:premise,eieb=lambda *xs:result),'witness')==((not premise) or result)
    for i,(field,_) in enumerate(FIELDS):
        changed=values.copy();changed[i]=sentinel(slots[i][1],100+i,cuts)
        assert not run('eiec',changed,dict(eiea=lambda *xs:True,eieb=lambda *xs:gate([n for n,_ in FIELDS],xs)),'witness'),field
    return dict(groups=rows,conditional_body_cases=4,existential_body_witness_slots=len(FIELDS),comparison_not_required_for_single_case=True)

def expected_case(case,fields):
    # Independently list shared roles; all physical case records are case-specific.
    common={'left','right','process','reference','lengthunit','timeunit','leftmembers','rightmembers','standard','threshold','minimumspan','sections'}
    return ['quantityunit' if n=='chargeunit' else n if n in common or n.startswith('trial') else case+n for n,_ in fields]

@lru_cache(None)
def comparison_checks():
    row=binding_group('eiee',PAIRED,{'eida':[n for n,_ in COMPARISON],'eidm':expected_case('first',BASE),'eiea':expected_case('second',BASE),
        'eids':expected_case('first',FIRST_FIELDS),'eieb':expected_case('second',FIELDS)})
    cuts,base,slots,values,pos,gate=setup('eief',PAIRED)
    for valid,relative,current in product((False,True),repeat=3):
        assert run('eief',values,dict(eiee=lambda *xs:valid,eia2=lambda *xs:relative,eibi=lambda *xs:current))==((not(valid and relative)) or current)
    keys=[n for n,_ in RELATIVE];curr=names(current_args())
    for target,selected in (('relative',keys),('current',curr)):
        for n in selected:
            i=pos[n];changed=values.copy();changed[i]=sentinel(slots[i][1],100+i,cuts)
            m=dict(eiee=lambda *xs:True,eia2=(lambda *xs:gate(keys,xs)) if target=='relative' else (lambda *xs:True),eibi=(lambda *xs:False) if target=='relative' else (lambda *xs:gate(curr,xs)))
            assert run('eief',changed,m)==(target=='relative'),(target,n)
    assert run('eief',values,dict(eiee=lambda *xs:gate([n for n,_ in PAIRED],xs),eia2=lambda *xs:gate(keys,xs),eibi=lambda *xs:gate(curr,xs)))
    return dict(pair=row,conditional_combinations=8,relative_history_slots=len(keys),current_history_slots=len(curr),same_relative_different_current_rejected=True,different_relative_same_current_allowed=True)

@lru_cache(None)
def numeric_checks():
    cuts,base=arithmetic();c=cuts.make;r=cuts.read;axes=('x','y','z');m=dict(base,yn=lambda:'x',yo=lambda:'y',yp=lambda:'z',zc7=lambda:'t',szi=lambda flag,a,b:a if flag else b)
    def vec(values):return FunctionValue(('individual',),RS,lambda a:c(dict(zip(('x','y','z','t'),values)).get(a,0)))
    vectors=((0,0,0),(1,2,-1),(-2,1,0));count=0
    for velocity,magnetic,conversion in product(vectors,vectors,(1,2)):
        cross=(velocity[1]*magnetic[2]-velocity[2]*magnetic[1],velocity[2]*magnetic[0]-velocity[0]*magnetic[2],velocity[0]*magnetic[1]-velocity[1]*magnetic[0])
        drive=tuple(conversion*x for x in cross)
        assert run('eidz',[vec(velocity),vec(magnetic),c(conversion),vec(drive)],m);count+=1
        for axis in range(3):
            wrong=list(drive);wrong[axis]+=1;assert not run('eidz',[vec(velocity),vec(magnetic),c(conversion),vec(wrong)],m);count+=1
    # Calibration must reject nonpositive conversion despite accepting boundaries.
    ec,eb,es,ev,ep,eg=setup('eid2',CALIBRATION)
    em=dict(eb,eiru=lambda *xs:eg([n for n,_ in CALIBRATION if n!='driveunit'],xs),eisar=lambda *xs:eg([n for n,_ in UNIT],xs))
    assert run('eid2',ev,em)
    for i,(name,_) in enumerate(CALIBRATION):
        changed=ev.copy();changed[i]=sentinel(es[i][1],100+i,ec);assert not run('eid2',changed,em),name
        old=ev[i];ev[i]=changed[i];assert run('eid2',changed,em);ev[i]=old
    for conv in (-1,0):
        changed=ev.copy();changed[ep['conversion']]=ec.make(conv);assert not run('eid2',changed,dict(eb,eiru=lambda *xs:True,eisar=lambda *xs:True))
    # Test every spatial component, with region and interval guards.
    zero_cases=0
    for values,coords in product(((0,0,0),(1,0,0),(0,-2,0),(0,0,3)),((1,2,3,1),(-1,2,3,1),(1,2,3,-1),(1,2,3,3))):
        field=lambda axis:FunctionValue((RS,RS,RS,RS),RS,lambda *xs:c(dict(zip(axes,values)).get(axis,0)))
        f=dict(electricfield=field,region=lambda x,y,z,t:r(x)>=0,lower=c(0),upper=c(2),**dict(zip(('x','y','z','time'),map(c,coords))))
        assert run('eid4',[f[n] for n,_ in ZERO_POINT],m)==(coords[0]<0 or coords[3] not in (0,1,2) or not any(values));zero_cases+=1
    point=vec((1,2,3,1));field=lambda axis:FunctionValue((RS,RS,RS,RS),RS,lambda x,y,z,t:c((r(x)+r(t)) if axis=='y' else 0))
    assert run('eid3',[field,lambda *xs:True,point,vec((0,2,0))],m)
    for region,driving in ((lambda *xs:False,vec((0,2,0))),(lambda *xs:True,vec((0,0,0))),(lambda *xs:True,vec((0,-2,0)))):
        assert not run('eid3',[field,region,point,driving],m)
    # 'No intrinsic energy' is not 'no attribution at all': zero remains allowed.
    ec,eb,es,ev,ep,eg=setup('eid6',ENERGY)
    for attributed,value in product((False,True),(-3,0,3)):
        values=ev.copy();values[ep['value']]=ec.make(value)
        assert run('eid6',values,dict(eb,eisat=lambda *xs:attributed))==((not attributed) or value==0)
    em=dict(eb,eisat=lambda *xs:eg([n for n,_ in ENERGY],xs));assert not run('eid6',ev,em)
    for i,(name,_) in enumerate(ENERGY):
        changed=ev.copy();changed[i]=sentinel(es[i][1],100+i,ec);assert run('eid6',changed,em),name
        old=ev[i];ev[i]=changed[i];assert not run('eid6',changed,em);ev[i]=old
    unknown=ev.copy();unknown[ep['value']]=FunctionValue(('number',),'truth',lambda q:True)
    try:run('eid6',unknown,em)
    except ValueError as e:assert 'not constructed' in str(e)
    else:raise AssertionError('Unknown energy cut accepted')
    return dict(drive_vector_cases=count,calibration_slots=len(CALIBRATION),zero_field_cases=zero_cases,drive_witness_cases=4,intrinsic_energy_cases=6,intrinsic_energy_slots=len(ENERGY),zero_or_absent_energy_allowed=True,unknown_energy_refused=True)

@lru_cache(None)
def quantifier_checks():
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    for name,fields in (('eid5',ZERO_FIELD),('eid7',ENERGY_HISTORY)):
        cuts,base,slots,values,pos,gate=setup(name,fields)
        try:run(name,values,dict(base,eisat=lambda *xs:False))
        except ValueError as e:assert 'rational number domain' in str(e)
        else:raise AssertionError('Real-domain denial was sampled: '+name)
    for name,kind,expected in (('eid5','forall',4),('eid7','forall',3)):
        tail=ds[name]['body'];n=0
        while tail['kind']==kind:n+=1;tail=tail['body']
        assert n==expected,(name,n)
    body=ds['eiec']['body'];assert body['kind']=='implies' and body['arguments'][0]['symbol']=='eiea'
    tail=body['arguments'][1];chosen=[p['name'] for p in ds['eiec']['parameters']];quant=[]
    while tail['kind']=='exists':quant.append(tail['variable']);tail=tail['body']
    assert len(quant)==len(RESULT) and tail['symbol']=='eieb' and [a['name'] for a in tail['arguments']]==chosen+quant
    counts={}
    for name,fields,target in (('eied',BASE,'eiec'),('eieg',PAIRED,'eief')):
        tail=ds[name]['body']['body'];n=0
        while tail['kind']=='forall':n+=1;tail=tail['body']
        assert n==len(fields)-4 and tail['symbol']==target;counts[name]=n
    def deps(name):return {d['name'] for d in extract_document(doc,roots=[name],statement_indices=[]).document['declarations']}
    assert not deps('eiec')&{'eia2','eibi','eicd'}
    assert not deps('eiee')&{'eia2','eibi'}
    assert {'eiee','eia2','eibi'}<=deps('eief')
    assert ds['eiel']['body']['kind']=='message' and ds['eiel']['body']['force']=='assert'
    return dict(zero_field_quantifiers=4,energy_quantifiers=3,existential_result_slots=len(RESULT),universal_case_slots=counts,relative_equality_scoped_only_to_comparison=True,full_real_denials_refused=True)

def discourse_model(bits=(True,)*5,bad=None):
    m=dict(eisav=lambda:'node',eisaq=lambda:'prior',rd=lambda:'author',eirf=lambda:'paper',ri=lambda:'text',eisak=lambda:'view',eisac=lambda:'process')
    rows=[('eir3',('node','author','paper','eiel','text')),('zbc',('node','author','eidv','eieh','process','text')),
        ('eisaw',('node','author','eiej','eieq','eier','process','text')),('eisaw',('node','author','eiej','eies','eiet','process','text')),('ue',('prior','node','text'))]
    grouped={}
    for i,(name,row) in enumerate(rows):
        if bad and bad[0]==i:row=tuple('other' if j==bad[1] else x for j,x in enumerate(row))
        grouped.setdefault(name,[]).append((row,bits[i]))
    for name,items in grouped.items():
        def callback(*xs,items=items):
            actual=tuple(symbol(x) if hasattr(x,'syntax') else x for x in xs)
            return any(bit and actual==row for row,bit in items)
        m[name]=callback
    return m

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==211
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,index in zip(PRIORS,(206,207,208,209)):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[index])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    for name in ('eieq','eier','eies','eiet'):assert ds[name]['parameters']==ds['eieb']['parameters']
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    count=0
    for path in (CORE,FULL):
        p=parse(read(path));p['statements']=p['statements'][-1:]
        for bits in product((False,True),repeat=5):assert evaluate(p,discourse_model(bits))[0]['value']==all(bits);count+=1
        for row,arity in enumerate((5,6,7,7,3)):
            for slot in range(arity):assert not evaluate(p,discourse_model(bad=(row,slot)))[0]['value'];count+=1
    source=deepcopy(doc);source['statements']=[]
    attributed=parse(format_graph(source,'compact')+'q[t[k eiek[]][k ri[]]].')
    for usual,content in product((False,True),repeat=2):
        m=discourse_model();m.update(eisah=lambda v,p,r:usual and (v,p,r)==('view','paper','text'),eisai=lambda v,d,r:content and (v,symbol(d),r)==('view','eiej','text'))
        assert evaluate(attributed,m)[0]['value']==(usual and content)
    closure=parse(format_graph(source,'compact')+'q[t[k eieh[]][k ri[]]].');m=discourse_model();m.update(eisaa=lambda:'body',eisab=lambda:'other',eisac=lambda:'body')
    try:evaluate(closure,m,individuals=('body','other'))
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Full case domain sampled')
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003');reading=json.loads(read(READING))
    validate_hashes(ROOT,reading['source_sha256']);assert unit['text'][771:1203]==reading['source'] and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=210,presentation_cases=count,usual_view_cases=4,shared_clause_binding=True,quoted_physics_not_executed=True,source_range=[771,1203],prior_reviews_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_moving_conductor_case import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

def build_report():
    results=dict(cases=case_checks(),comparison=comparison_checks(),numeric=numeric_checks(),quantifiers=quantifier_checks(),structure=structure_checks())
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,READING,*PRIORS,INVENTORY,'scripts/compose_moving_conductor_case.py','scripts/check_moving_conductor_case.py','scripts/review_moving_conductor_case.py','tests/test_moving_conductor_case.py',
        'scripts/compose_moving_magnet_case.py','scripts/compose_observable_contrast.py','scripts/compose_relative_history_match.py','scripts/compose_magnetic_action.py','scripts/compose_material_relative_frame.py','scripts/compose_field_equations.py','scripts/compose_rest_force.py','scripts/compose_limits.py',
        'scripts/check_conductor_cases.py','scripts/check_material_relative_frame.py','scripts/check_coordinate_correspondence.py','scripts/check_tau_differential.py'}
    return dict(status='moving_conductor_case_and_current_comparison_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[771,1203],source=unit['text'][771:1203],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
