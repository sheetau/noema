"""Check frame-specific unit-charge records and quoted inference attribution."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import NUM
from scripts.check_point_charge_calibration import setup as calibration_setup,CONSTANTS as CALIBRATION_CONSTANTS
from scripts.compose_moving_unit_charge import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,build

DOC='docs/moving-unit-charge-v1.md';SOURCE='data/einstein-moving-unit-charge-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg'
DEPENDENCIES=('reports/point-charge-calibration-v1.json','reports/first-principle-v1.json','reports/rest-force-v1.json')
CONSTANTS=CALIBRATION_CONSTANTS|{'zbm':'moving','zpd':'movingrecord','zpg':'inference','eisk3':'principlename'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'other')));SITUATIONS=('context','other')

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    # eion contains full real/function quantification; its binding, not a new
    # finite proof of the principle, is under test here. Its prior checks are pinned.
    abstract(doc,NUM|{'eion'});doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    d=next(d for d in doc['declarations'] if d['name']==name);expr=dict(kind='call',symbol=name,arguments=[])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc

def run(name,m):
    doc=fixture(name);mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    return evaluate_document(doc,individuals=DOMAIN,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=200000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup():
    s=calibration_setup();c=s['c'];norm=s['norm'];rows={
        'eisqc':{('first','context')},'va':{('moving',)},
        'zof':{('chargeunit','chargekind',Q(1),'context')},
        'zog':{norm(('movingrecord','first','chargekind','moving','event','chargeunit',c(1),'context'))}}
    return s,rows,s['m']|{n:s['rel'](rs) for n,rs in rows.items()}

@lru_cache(None)
def amount_checks():
    s,rows,m=setup();cases=perturb(lambda mm:run('ejwm',mm),m,rows,s['norm'])
    for symbol,wrong in [('zol','second'),('zbm','frame'),('zoo','other'),('zou','dyn'),('zor','forcekind'),('zpd','chargerecord')]:
        assert not run('ejwm',m|{symbol:lambda wrong=wrong:wrong});cases+=1
    for amount in (Q(-1),Q(0),Q(2)):
        wrong={s['norm'](('movingrecord','first','chargekind','moving','event','chargeunit',s['c'](amount),'context'))}
        assert not run('ejwm',m|{'zog':s['rel'](wrong)});cases+=1
    for scale in (Q(-1),Q(0),Q(2)):
        assert not run('ejwm',m|{'zof':s['rel']({('chargeunit','chargekind',scale,'context')})});cases+=1
    assert run('ejwm',m|{'x4':forbidden,'xm':forbidden,'zpa':forbidden,'eion':forbidden});cases+=1
    assert not run('ejwm',m|{'ba':lambda x:False});cases+=1
    return dict(cases=cases,same_target_event_unit_scale_and_kind=True,separate_moving_record_required=True,no_rest_or_motion_added_to_conclusion=True)

@lru_cache(None)
def premise_checks():
    s=calibration_setup();yes=lambda:Content(SITUATIONS,(True,False));m=s['m']|{'eion':yes}
    rows={n:rs for n,rs in s['rows'].items() if n in ('eisqc','zof','zog')}
    rows['zof']={row for row in rows['zof'] if row[1]=='chargekind'}
    rows['zog']={row for row in rows['zog'] if row[0]=='chargerecord'}
    cases=perturb(lambda mm:run('ejwl',mm),m,rows,s['norm'])
    assert not run('ejwl',m|{'eion':lambda:Content(SITUATIONS,(False,True))});cases+=1
    unknowns(lambda mm:run('ejwl',mm),m,('eion',))
    assert run('ejwl',m|{n:forbidden for n in ('saw','sca2','x4','zpa','xm')});cases+=1
    # True quoted premises do not install a new physical result record.
    assert run('ejwl',m)
    assert not run('ejwm',m|{'va':lambda f:f in ('frame','moving')});cases+=2
    _,postrows,post=setup()
    assert run('ejwm',post|{'eion':lambda:Content(SITUATIONS,(False,True))});cases+=1
    return dict(cases=cases,current_principle_and_native_old_frame_unit_assumption=True,calibration_rest_not_extended=True,premise_and_conclusion_not_conflated=True,principle_is_explicit_fixture_boundary=True)

@lru_cache(None)
def presentation_checks():
    rows={'zc':{('inference','author','ejwl','ejwm','scope','context')},'eisch':{('principlename','eion','scope','context')}}
    m={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mm:run('ejwn',mm),m,rows)
    assert run('ejwn',m|{n:forbidden for n in ('ejwl','ejwm','eion','zog','eisqc')});cases+=1
    outer={'eir3':{('inference','author','paper','ejwo','context')},'ue':{('explanation','inference','context')}}
    cases+=perturb(lambda mm:run('ejwp',mm),{n:relation(rs) for n,rs in outer.items()},outer)
    assert not run('ejwp',{n:lambda *xs:True for n in outer}|{'zpg':lambda:'explanation'});cases+=1
    return dict(cases=cases,quoted_inference_not_evaluated_as_proof=True,named_current_principle_and_author_bound=True,following_calibration_order=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][172]
    assert u['id']=='einstein-1905:u0173' and digest(u['text'].encode())==u['text_sha256']
    start=u['text'].index('Nach dem');end=u['text'].index(' Ruht diese');text=u['text'][start:end]
    assert text=='Nach dem Relativitätsprinzip ist diese elektrische Masse auch im bewegten System gemessen von der Größe „eins“.'
    return dict(status='partial_current_principle_unit_charge_inference',unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=text,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text)),observations=['原刊909頁の第三文を再読した。dieseは直前の点状電気量zol、auchはKに加えてkでも値1、elektrische Masseは電気量を指す。','同じ出来事・電気量単位・尺度での二系の記録と読む。力を評価する後続の出来事への時間的保持は別に接続する。','相対性原理によるという著者の推論を引用された前提と結論で保持する。推論の提示を電荷不変性の自動証明へ替えない。'],remaining=['第一文の六式の解釈導入','第四・第五文の現在の物理的な場と静止・瞬間静止への接続','第六文の二つの言い表しへの導入','u0173全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,FACSIMILE)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[157,158,159,160,161,162,163])==selection_binding(old,[157,158,159,160,161,162,163])
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'ejwf','eion','sbw2','scc2','eisqc','eisch','zc'}<=names
    assert not names&{'saw','sca2','sby2','zoi','zok','xm','zpa'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,replaced_statement=INDEX,other_357_statements_and_prior_judgments_preserved=True,whole_unit_review_not_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('amount',amount_checks),('premise',premise_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','check_point_charge_calibration','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_moving_unit_charge.py','scripts/check_moving_unit_charge.py','tests/test_moving_unit_charge.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='current_principle_moving_unit_charge_inference_connected',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=s['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
