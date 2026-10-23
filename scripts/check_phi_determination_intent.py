"""Check current-stage candidates and the same-function determination intent."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_translated_light_trial import expose
from scripts.check_four_coordinate_claim import model as previous_model,RS
from scripts.compose_phi_determination_intent import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/phi-determination-intent-v1.md';SOURCE='data/einstein-phi-determination-intent-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-wave-compatibility-conclusion-u0091-review-v1.json'
DEPENDENCIES=('reports/origin-constants-claim-v1.json','reports/four-coordinate-claim-v1.json','reports/reverse-transform-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zgt':'unknown','zgn':'intent','zgg':'previous','zee':'agent','zfm':'stage','zgl':'current'}
DOMAIN=tuple(dict.fromkeys((*[x for n,x in CONSTANTS.items() if n not in ('zfm','zgl','ri')],'other')))
POINTS=('stage','current','context','discourse','other')

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky'}
    if name=='srp':bounds|={'smq','smb'}
    if name=='ejaw':bounds|={'ei7c','sqd','srp'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'}))=={'srp':2,'smq':1,'smb':3}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jpdi'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpdipoint',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jpdipoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jpdicapture',parameters=[d['result']],result='truth'));body=dict(kind='call',symbol='jpdicapture',arguments=[body])
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jpdipoint':lambda:'discourse'}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def model():
    cuts,m,*_=previous_model();c=cuts.make;r=cuts.read
    def family(stage):
        if stage not in POINTS:forbidden()
        return FunctionValue((RS,),RS,lambda speed:c(Q(2)+(r(speed)-3)**2 if stage=='other' else Q(2)))
    fam=FunctionValue(('situation',),dict(kind='function',parameters=[RS],result=RS),family)
    m|={'zer':lambda:fam,'zet':lambda agent,stage,alt:agent=='agent' and stage=='current' and alt in ('current','other')}
    return cuts,m


def capture(name,m):
    out=[];assert run(name,[],m|{'jpdicapture':lambda x:out.append(x) is None});assert len(out)==1;return out[0]


@lru_cache(None)
def candidate_checks():
    cuts,m=model();c=cuts.make;r=cuts.read;family=capture('sqc',m);coefficient=capture('spc',m);count=0
    domain=FunctionValue((RS,),'truth',lambda x:0<=r(x)<5);same=FunctionValue((RS,RS),'truth',lambda a,b:r(a)==r(b));alt=FunctionValue(('individual','situation','situation'),'truth',m['zet'])
    for speed,unequal in ((0,True),(3,False),(4,True),(-3,False)):
        value=c(Q(speed));args=['agent','current',domain,alt,family,same,'current','other',value]
        assert run('smb',args,m,'instance')==unequal;count+=1
        for slot,wrong in ((0,'other'),(1,'stage'),(6,'context'),(7,'context')):
            bad=args.copy();bad[slot]=wrong;assert not run('smb',bad,m,'instance');count+=1
        assert run('smq',[coefficient,family,'current',domain,value],m,'instance');count+=1
        assert run('smq',[coefficient,family,'other',domain,value],m,'instance')==(speed in (3,-3));count+=1
    # Fingerprints belong only to this explicit rational test boundary.
    one=lambda f:tuple(r(f(c(Q(v)))) for v in (0,3,4))
    fingerprint=lambda f:tuple(one(f(ctx)) for ctx in POINTS)
    scope=lambda f:tuple(f(c(Q(v))) for v in (-3,0,3,4,5))
    current_expected=one(coefficient);family_expected=fingerprint(family)
    m|={'smq':lambda f,fam,stage,dom:one(f)==current_expected and fingerprint(fam)==family_expected and stage=='current' and scope(dom)==(False,True,True,True,False),
        'smb':lambda agent,stage,dom,alternatives,fam,same:agent=='agent' and stage=='current' and scope(dom)==(False,True,True,True,False) and alternatives(agent,stage,'current') and alternatives(agent,stage,'other') and fingerprint(fam)==family_expected and same(c(Q(2)),c(Q(2))) and not same(c(Q(2)),c(Q(3)))}
    for ctx in POINTS:
        assert run('srp',[ctx,c(Q(3))],m,'instance');count+=1
    for n in ('smq','smb'):
        assert not run('srp',['other',c(Q(3))],m|{n:lambda *xs:False},'instance');count+=1
    for n,bad in (('zgl',lambda:'stage'),('zet',lambda a,s,t:t=='other'),('zeq',lambda:FunctionValue((RS,),RS,lambda v:c(Q(7))))):
        assert not run('srp',['other',c(Q(3))],m|{n:bad},'instance');count+=1
    # Validity of an admitted candidate is separate from witness inequality.
    assert not run('srp',['other',c(Q(4))],m|{'ba':lambda cut:r(cut)!=5},'instance');count+=1
    unknowns(lambda mm:run('srp',['other',c(Q(3))],mm,'instance'),m,('zer','zet','zeq','smq','smb','tc','sky'))
    try:run('srp',[],m)
    except ValueError as error:assert 'Cannot finitely quantify' in str(error)
    else:raise AssertionError('Whole real-function scope sampled')
    return dict(cases=count,native_same_speed_witness_and_current_function_membership=True,current_stage_not_prior_stage=True,one_speed_agreement_not_determined_function=True,current_candidate_and_admitted_valid_family_required=True,real_function_quantification_refused_and_boundaries_explicit=True)


@lru_cache(None)
def continuation_checks():
    count=0;names=('ei7c','sqd','srp')
    for bits in product((False,True),repeat=3):
        m={n:lambda on=on:Content(POINTS,(False,False,False,on,False)) for n,on in zip(names,bits)}
        assert run('ejaw',[],m)==all(bits);count+=1
    m={n:lambda:Content(POINTS,(True,True,True,True,True)) for n in names}
    unknowns(lambda mm:run('ejaw',[],mm),m,names)
    return dict(cases=count,current_four_equations_prior_and_now_unknown_all_required=True)


@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
        ('ejax',{'uh':{('unknown','author','ejaw','section','discourse')},'zgm':{('intent','author','spc','current','section','discourse')},'ue':{('unknown','intent','discourse')}}),
        ('ejaz',{'eir3':{('unknown','author','paper','ejay','discourse')},'ue':{('previous','unknown','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ejaw','ei7c','sqd','srp','spc','zeq')});count+=1
    return dict(cases=count,same_phi_description_current_stage_author_scope_and_order=True,intention_not_completed_determination=True,quoted_function_and_content_not_executed=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][91];math={m['id']:m for m in inv['math']};readings={'M0148':'φ','M0149':'v'}
    assert u['id']=='einstein-1905:u0092' and u['text_sha256']=='32b7574fa03e69d2584b370f552609b4ae086006a86253d0718362ce7a17a6e8'
    for n,t in readings.items():assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==t
    segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']])
    retrieval='artifacts/einstein-light-proof-task-v1/retrieval.json';retrieved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']});paths={INVENTORY,DOC,retrieval,*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-phi-determination-intent-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['901'],segments=[segment],observations=['原刊901頁で両立性の結論に続くIn den entwickelten Transformationsgleichungenからbestimmen wollenまで一文を通読し、次の第三系導入との境界を確認した。','φは既出の四式に現れる同じ正規化後の速度vの関数。nochは先行の未決定性がなお残ることを示す。','welcheは同じ関数φを受け、wir nun bestimmen wollenは今の論述段階からそれを決定する著者の意図を述べる。','φ=1や負速度での値はこの文では示されず、決定の方法は次の第三系導入へ続く。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==310
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[307,308])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document();ds={d['name']:d for d in doc['declarations']};assert ds['ejay']['body']['force']=='assert'
    previous=deepcopy(ds['sqd']);previous['name']='srp'
    def replace_stage(node):
        if isinstance(node,dict):
            if node.get('symbol')=='zfm':node['symbol']='zgl'
            for x in node.values():replace_stage(x)
        elif isinstance(node,list):
            for x in node:replace_stage(x)
    replace_stage(previous);assert previous==ds['srp']
    assert {'ei7c','spc','sqc','sqd','srp','smq','smb','zgm','zgl'}<=set(ds)
    assert not set(ds)&{'spk','shd','sri','srj','srk','sro'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,srp_reuses_same_uncertainty_with_only_stage_changed=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('candidates',candidate_checks),('continuation',continuation_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_phi_determination_intent.py','scripts/check_phi_determination_intent.py','tests/test_phi_determination_intent.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_four_coordinate_claim.py','scripts/check_translated_light_trial.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='still_unknown_phi_and_determination_intent_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0092の全文通読判断登録','u0093以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
