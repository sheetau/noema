"""Check all material-event links, actual flow arguments and the K specialization."""
from copy import deepcopy
from functools import lru_cache
import json
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_convective_transformed_quantities as prior
from scripts.check_ninth_section_opening import lifted
from scripts.check_convective_foundation_reading import walk
from scripts.check_problem_series_reduction import collapse
from scripts.compose_convective_velocity_interpretation import *

DOC='docs/convective-velocity-interpretation-v1.md';SOURCE='data/einstein-convective-velocity-obligations-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p917-0.jpg'
DEPENDENCIES=('reports/convective-transformation-claim-v1.json','reports/convective-transformed-quantities-v1.json','reports/convective-foundation-reading-v1.json','reports/convective-charge-setting-v1.json')
BOUNDS={'ek2f':{'s46','s6m','ejsj'},'ek2g':{'s46','ejsj'},'ek2h':{'s6m','ejsj','ek2f','ek2g'},'ek2i':{'ek2h','ekxl','ekzu','s6m'},'ek2j':{'ekzx','ek2i'},'ek2k':{'ejsn'},'ekym':{'ejsn'},'ek2m':{'ek2l','ekyq'}}
CONSTANTS=prior.CONSTANTS;PEOPLE=prior.PEOPLE;forbidden=prior.forbidden;old=prior.old

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.NUM|{'bg','be','bj','sjd','szi'}|BOUNDS[root]:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=deepcopy(boundary(root));doc=collapse(doc) if mode=='flat' else doc;d=next(d for d in doc['declarations'] if d['name']==root);extras={}
    if mode=='sample' and root=='ek2h':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='forall':
                names=('jcviia','jcviib') if node['sort']=='individual' else ('jcvipa','jcvipb') if node['sort']==old.sort(POINT) else None
                if names:
                    extras.update({n:node['sort'] for n in names})
                    return dict(kind='and',arguments=[sample(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in names])
            return {k:sample(x) for k,x in node.items()}
        d['body']=sample(d['body'])
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=t) for n,t in extras.items()]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jcviarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jcvicontext',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jcvicontext',arguments=[]))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots

def run(root,vs,m,mode='sample'):
    doc,slots=fixture(root,mode);assert len(vs)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jcvicontext':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=60000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def contrasts(root,vs,m,rows,key):
    rel=lambda rs:lambda *xs:key(xs) in rs
    good=m|{n:rel(rs) for n,rs in rows.items()};assert run(root,vs,good),root;cases=1
    for n,rs in rows.items():
        for row in rs:
            assert not run(root,vs,good|{n:rel(rs-{row})}),(root,n,'missing');cases+=1
            for i in range(len(row)):
                wrong=list(row);wrong[i]='wrong';assert not run(root,vs,good|{n:rel((rs-{row})|{tuple(wrong)})}),(root,n,i);cases+=1
        try:run(root,vs,good|{n:forbidden})
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError('Unknown input accepted')
        cases+=1
    return cases

@lru_cache(None)
def event_checks():
    by,m,c,r,points,jets,key,derived,U=prior.setup();E,H,region,vel,rho=derived;vs=[by[n] for n,t in SETTING];cases=0
    matter,event='a','b';p=points[0]
    position=lambda who,frame,ev,place:key([who,frame,ev,by['lengthunit'],by['timeunit'],place,'case'])
    record=lambda who,frame,ev,place:key([who,frame,ev,place,'case'])
    for root,first,second,speed,targetregion in [('ek2f','frame','moving',3,region),('ek2g','moving','frame',-3,by['region'])]:
        mapped=m['s46'](by['light'],c(speed),p)
        rows={'eisqd':{position(matter,first,event,p),position(matter,second,event,mapped)},'zpb':{record(matter,second,event,mapped)},'ejsj':{key([mapped,targetregion])}}
        cases+=contrasts(root,vs+[matter,event,p],m,rows,key)
    # Distinct members, events and positions in each frame: no same-number shortcut.
    members={('a',by['distribution'],'case'),('b',by['distribution'],'case')}
    records={record(who,frame,ev,point) for who,ev,point in [('a','a',points[0]),('b','b',points[1])] for frame in ('frame','moving')}
    relation=lambda rs:lambda *xs:key(xs) in rs
    worlds=m|{'jcviia':lambda:'a','jcviib':lambda:'b','jcvipa':lambda:points[0],'jcvipb':lambda:points[1],
        'zqn':lambda:old.fn(old.sort('h[a a d] c'),lambda *xs:xs in members),'zpb':relation(records),'ejsj':lambda *xs:True}
    obligations={n:{key(vs+[who,ev,point]) for who,ev,point in [('a','a',points[0]),('b','b',points[1])]} for n in ('ek2f','ek2g')}
    cases+=contrasts('ek2h',vs,worlds,obligations,key)
    # A record on only one side still requires its opposite-side counterpart.
    for frame,required,other in [('frame','ek2f','ek2g'),('moving','ek2g','ek2f')]:
        one={record('a',frame,'b',points[0])};row=key(vs+['a','b',points[0]])
        base=worlds|{'zpb':relation(one),required:relation({row}),other:lambda *xs:False}
        assert run('ek2h',vs,base);assert not run('ek2h',vs,base|{required:lambda *xs:False});cases+=2
    for n in ('zpb','ejsj','zqn'):
        try:run('ek2h',vs,worlds|{x:lambda *xs:True for x in obligations}|{n:forbidden})
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError('Unknown selection accepted')
        cases+=1
    try:run('ek2h',vs,worlds,'native')
    except ValueError as e:assert any(x in str(e) for x in ('Finite function domain','rational number domain'))
    else:raise AssertionError('Unbounded positions enumerated')
    cases+=1
    newflow=by|dict(frame='moving',region=region,velocityfield=vel)
    rows={'ek2h':{key(vs)},'eiscc':{('moving',by['lengthunit'],by['timeunit'],'speedunit','case')},'ekxl':{key([newflow[n] for n,t in FLOW])}}
    cases+=contrasts('ek2i',vs,m,rows,key)
    return dict(cases=cases,same_member_event_units_and_forward_inverse_points=True,both_record_directions_required=True,missing_new_records_not_hidden_by_vacuity=True,new_flow_uses_same_distribution_units_region_and_constructed_field=True)

@lru_cache(None)
def calibration_checks():
    by,m,c,r,points,jets,key,derived,U=prior.setup();cases=0
    for frame in ('frame','moving','other'):
        b=by|dict(frame=frame);vs=[b[n] for n,t in GLOBAL];rows={'ejsn':{key([b[n] for n,t in FIELD_SETTING])}}
        cases+=contrasts('ek2k',vs,m,rows,key)
        good=m|{'ejsn':lambda *xs:True}
        assert run('ekym',vs,good)==(frame=='frame');cases+=1
        for name,bad in [('lengthunit','other'),('timeunit','other'),('light',c(7)),('electricconversion',c(2)),('magneticconversion',c(1))]:
            changed=b|{name:bad};assert not run('ek2k',[changed[n] for n,t in GLOBAL],good);cases+=1
    return dict(cases=cases,only_fixed_K_reference_removed=True,units_light_and_both_conversions_preserved=True)

@lru_cache(None)
def binder_checks():
    cases=0
    for pivot in range(len(CASES)):
        doc,d,slots,var,body=lifted(boundary('ek2j'),'ek2j',pivot,len(CASES),'forall')
        calls={x['symbol']:x for x in walk(body) if x.get('kind')=='call'};assert calls['ekzx']['arguments']==calls['ek2i']['arguments']
        env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
        rows=lambda picks:{tuple((env|{var:pick})[x['name']] for x in calls['ek2i']['arguments']) for pick in picks}
        for selected,allowed,want in [(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]:
            hs,ls=rows(selected),rows(allowed);m={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'ekzx':lambda *xs:xs in hs,'ek2i':lambda *xs:xs in ls}
            assert evaluate_document(doc,individuals=('a','b'),situations=('case','other'),primitives=m,max_steps=20000)[0]['value']==want;cases+=1
    vs=['case' if t=='d' else 'a' for n,t in GLOBAL]
    for a,b,want in [(True,True,True),(True,False,False),(False,True,True),(False,False,True)]:
        assert run('ek2m',vs,{'ek2l':lambda *xs:a,'ekyq':lambda *xs:b},'flat')==want;cases+=1
    for i in range(len(vs)):
        changed=vs.copy();changed[i]='other' if GLOBAL[i][1]=='d' else 'b'
        assert not run('ek2m',changed,{'ek2l':lambda *xs:True,'ekyq':lambda *xs:xs==tuple(vs)},'flat')
        assert run('ek2m',changed,{'ek2l':lambda *xs:xs==tuple(changed),'ekyq':lambda *xs:xs==tuple(changed)},'flat');cases+=2
    return dict(cases=cases,all_32_velocity_content_binders_shared=True,same_32_foundation_arguments_in_condition_and_law=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][236];math={m['id']:m for m in inv['math']};ms=[math[n] for n in u['math_ids']]
    assert u['id']=='einstein-1905:u0237' and digest(u['text'].encode())==u['text_sha256']
    for m in ms:assert digest(m['mathml'].encode())==m['sha256']
    assert [''.join(ET.fromstring(m['mathml']).itertext()) for m in ms]==['uξ,uη,uζ','k']
    return dict(version='einstein-convective-velocity-obligations-v1',unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=ms,semantic_completion=False,connected=['全物質成員・同じ出来事・両系の正逆位置対応','新系の単位付き履歴と座標時刻微分への構成流速の接続','同じ条件付き基礎法則の表示系の引数化とKへの制限'],unresolved=['§5の速度合成則から同定が従うという著者の参照・推論提示','採用する運動学的原理と同じLorentz理論の基礎の接続','相対性原理の全内容を保った具体的な基礎法則の適合','Da ... so ... damit gezeigtの一文全体の帰結提示と通読判断'],observations=['原刊917頁の先頭一段落を視認し、§5の挿入、三成分、kで測った速度との同定、運動学的原理を基礎とする限定、同じLorentz理論の基礎と相対性原理への結論を確認した。','今回の接続だけで原文単位を意味確認済みとはしない。後続u0238の任意運動での電荷不変をこの同定の前提にしない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

def rename(node,before,after):
    if isinstance(node,list):return [rename(x,before,after) for x in node]
    if not isinstance(node,dict):return node
    return {k:(after if k=='symbol' and x==before else rename(x,before,after)) for k,x in node.items()}

def terms(node):return sum((terms(x) for x in node['arguments']),[]) if node.get('kind')=='and' else [node]

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements']==before.document['statements'] and len(after.document['statements'])==411
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[410])==selection_binding(before,[410]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/convective-transformation-claim-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    ds={d['name']:d for d in core()['declarations']}
    oldterms=terms(ds['ekym']['body']);fixed=[t for t in oldterms if any(x.get('symbol')=='ra' for x in walk(t))]
    assert len(fixed)==1 and [t for t in oldterms if t not in fixed]==terms(ds['ek2k']['body'])
    assert ds['ekyo']['parameters']==ds['ek2l']['parameters']
    assert rename(ds['ek2l']['body'],'ek2k','ekym')==ds['ekyo']['body']
    hypothesis={d['name'] for d in extract_document(core(),roots=['ek2l'],statement_indices=[]).document['declarations']}
    assert not hypothesis&{'semf','semh','seme','semd','ekyq','ekym','ek2i','ek2j'}
    sourcehyp={d['name'] for d in extract_document(core(),roots=['ekzx'],statement_indices=[]).document['declarations']}
    assert not sourcehyp&{'ek2h','ek2i','ek2j','ekxlnew'}
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,all_411_prior_statements_and_meanings_preserved=True,K_specialization_preserves_original_model_exactly=True,no_equations_in_generalized_model_condition=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('events',event_checks),('calibration',calibration_checks),('binder',binder_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_convective_velocity_interpretation.py','scripts/check_convective_velocity_interpretation.py','tests/test_convective_velocity_interpretation.py','scripts/check_convective_transformed_quantities.py','scripts/check_ninth_section_opening.py','scripts/check_convective_foundation_reading.py','scripts/check_problem_series_reduction.py'}
    return dict(status='new_frame_velocity_and_frame_neutral_foundation_pending_claim',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
