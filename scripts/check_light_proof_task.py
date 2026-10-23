"""Check the proof target, the scoped absence claim and author presentation."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_frame_light_law import model as light_model,CONSTANTS as LIGHT_CONSTANTS,DOMAIN as LIGHT_DOMAIN
from scripts.compose_light_proof_task import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/light-proof-task-v1.md';SOURCE='data/einstein-light-proof-task-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-origin-constants-u0085-review-v1.json'
DEPENDENCIES=('reports/frame-light-law-v1.json','reports/two-postulates-v1.json','reports/second-section-opening-v1.json','reports/origin-constants-claim-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zfz':'task','zfy':'gap','zfq':'previous','zfx':'stage','wu':'adoption','wv':'following','ra':'rest','zbm':'moving'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'proof','otherproof','other')))
POINTS=('context','discourse','stage','other')

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eifj','eify'}
    if name=='ei7v':boundaries|=({'ei43'} if mode=='boundary' else {'eifw','ei42','eiyf'})
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    body=dict(kind='call',symbol=name,arguments=[])
    if next(d['result'] for d in doc['declarations'] if d['name']==name)=='content':
        doc['declarations'].append(dict(kind='primitive',name='jlptpoint',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jlptpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc

def run(name,m,mode='boundary',point='discourse',domain=DOMAIN,points=POINTS):
    doc=fixture(name,mode);mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{'jlptpoint':lambda:point}
    return evaluate_document(doc,individuals=domain,situations=points,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def target_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0
    for before,after in product((False,True),repeat=2):
        seen=[]
        def law(frame,speed,ctx):
            seen.append((frame,r(speed),ctx));assert frame in ('rest','moving')
            assert r(speed)==5 and ctx in POINTS
            return (before if frame=='rest' else after) if ctx=='other' else False
        assert run('ei7v',m|{'tc':lambda:c(Q(5)),'ei43':law},point='other')==((not before) or after);count+=1
        assert set(seen)=={(frame,Q(5),ctx) for frame in ('rest','moving') for ctx in POINTS}
    cuts,m,rows,norm,records,values=light_model();m|={n:lambda x=x:x for n,x in LIGHT_CONSTANTS.items()}
    # This physical fixture explicitly supplies one setting only. Content
    # construction evaluates every declared setting, so do not invent others.
    native=lambda mm:run('ei7v',mm,'native',point='context',domain=LIGHT_DOMAIN,points=('context',))
    assert native(m);count+=1
    for symbol in ('eifw','ei42','eiyf'):
        old=m[symbol]
        mm=m|{symbol:lambda *xs,old=old:False if 'moving' in xs else old(*xs)}
        assert not native(mm);count+=1
        mm=m|{symbol:lambda *xs,old=old:False if 'frame' in xs else old(*xs)}
        assert native(mm);count+=1
    extra=rows['eiscd']|{('u','moving','lengthunit','timeunit','context')}
    assert not native(m|{'eiscd':lambda *xs:xs in extra});count+=1
    unknowns(native,m,('tc','eiscd','eisce','eifw','ei42','eiyf','zbh'))
    return dict(cases=count,conditional_direction_and_same_speed_context=True,native_complete_frame_laws_connected=True,uncovered_moving_segment_rejects_target=True,unknown_inputs_not_false_premises=True)

@lru_cache(None)
def proof_gap_checks():
    count=0;proper=('proof','author','eif5','stage','paper')
    assert run('ei7w',{'zfr':relation(set())});count+=1
    for proof in ('proof','otherproof'):
        row=(proof,*proper[1:]);assert not run('ei7w',{'zfr':relation({row})});count+=1
        for slot in range(1,5):
            bad=tuple('other' if i==slot else x for i,x in enumerate(row))
            assert run('ei7w',{'zfr':relation({bad})});count+=1
    for wrong in (('proof','author','ei7v','stage','paper'),('proof','author','eif5','other','paper'),('proof','author','eif5','stage','section')):
        assert run('ei7w',{'zfr':relation({wrong})});count+=1
    assert not run('ei7w',{'zfr':relation({proper}),'eif5':forbidden,'eifj':forbidden,'eify':forbidden});count+=1
    unknowns(lambda m:run('ei7w',m),{'zfr':relation(set())},('zfr',))
    return dict(cases=count,all_proof_candidates_searched=True,same_target_author_stage_entire_paper_required=True,absence_not_falsity_impossibility_or_future_absence=True,quoted_compatibility_not_executed=True)

@lru_cache(None)
def compatibility_checks():
    count=0
    for label in ('common_other','separate_settings','empty_admissible','wrong_target','wrong_reference'):
        first=(False,False,False,True);second=(True,False,False,False) if label=='separate_settings' else first
        row=('eifj','eify','discourse','other')
        if label=='wrong_target':row=('eifj','ei7v','discourse','other')
        if label=='wrong_reference':row=('eifj','eify','context','other')
        m={'eifj':lambda:Content(POINTS,first),'eify':lambda:Content(POINTS,second),'eiscj':relation(set() if label=='empty_admissible' else {row})}
        assert run('eif5',m)==(label=='common_other');count+=1
    return dict(cases=count,native_shared_admissible_setting=True,same_two_prior_principles=True,current_principle_truth_not_required=True)

@lru_cache(None)
def presentation_checks():
    adoption={'ug':{('adoption','author','eify','following','discourse')},'ue':{('adoption','task','discourse')}}
    combined={'zga':{('task','author','ei7v','stage','section','discourse')},'eisa5':{('task','author','ei7v','ei7x','discourse')},'uh':{('gap','author','ei7w','section','discourse')},'zgb':{('gap','author','ei7w','task','section','discourse')},'ug':adoption['ug'],'ue':adoption['ue']|{('task','gap','discourse')}}
    author={'eir3':{('task','author','paper','ei7z','discourse')},'ue':{('previous','task','discourse')}}
    count=0
    for name,rows in (('ei7x',adoption),('ei7y',combined),('ei72',author)):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,mm),m,rows)
        assert run(name,m|{n:forbidden for n in ('ei7v','ei7w','eif5','eify','ei43','zfr')});count+=1
    return dict(cases=count,prior_adoption_parenthesis_and_reason_connected=True,task_and_gap_have_distinct_quoted_targets=True,same_author_paper_section_and_source_order=True,quoted_physics_and_proof_gap_not_executed_by_attribution=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][85];math=next(m for m in inv['math'] if m['id']=='M0140')
    assert u['id']=='einstein-1905:u0086' and u['text_sha256']=='cf2cc28bf0e10b0ba62d24e8dab3f7a62c723e9577e865a933da9cbb9b07d902'
    assert ''.join(ET.fromstring(math['mathml']).itertext())=='V'
    s=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=math['id'],sha256=math['sha256'],reading='V')])
    paths={INVENTORY,DOC}
    for retrieval in ('artifacts/einstein-longitudinal-elimination-v1/retrieval.json','artifacts/einstein-light-proof-task-v1/retrieval.json'):
        retrieved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']});paths|={retrieval,*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-light-proof-task-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['900','901'],segments=[s],observations=['原刊900頁末尾のWir haben nun zu beweisenから901頁冒頭のvereinbar seiまでを通読した。改頁はim ruhenden Systemの途中であり、一文の条件と理由を分断しない。','jeder Lichtstrahl、im bewegten System gemessen、同じV、fallsの静止系条件を保持する。wie wir angenommen habenは前提採用への振り返りである。','dennの後は、二原理が両立するという内容の証明をまだ提示していないという理由。両立性の否定でも証明不可能性でもない。','次のZur Zeit ... werdeから始まる球面波の仮定は別単位に残す。901頁の後段の両立性が示されたという結論を、この時点の達成として加えない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==305
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[302,303])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document();ds={d['name']:d for d in doc['declarations']};assert ds['ei7z']['body']['force']=='assert'
    assert not set(extract_document(doc,roots=['ei7v'],statement_indices=[]).retained_symbols)&{'sbc','smw','rc','eing','sjh'}
    assert {'eifj','eify','eif5','eiscj','sqi','zfr','ei43'}<=set(ds)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,current_two_principles_and_frame_laws_reused=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('target',target_checks),('proof_gap',proof_gap_checks),('compatibility',compatibility_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_light_proof_task.py','scripts/check_light_proof_task.py','tests/test_light_proof_task.py','scripts/check_frame_light_law.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='current_light_proof_task_and_stated_compatibility_gap_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0086の全文通読判断登録','u0087以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
