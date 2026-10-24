"""Check current inverse-method bindings and the attributed conditional result."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_moving_trip_geometry import NUM
from scripts.check_material_relative_frame import arithmetic,RS
from scripts.check_calculation_discourse import sequence,symbol
from scripts.compose_calculation_discourse import STEPS
from scripts.compose_inverse_field_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDICES,SOURCE_ORDER,MEANINGS,build

DOC='docs/inverse-field-claim-v1.md';SOURCE='data/einstein-inverse-field-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';CORRECTION='data/field-scale-inverse-facsimile-v1.json'
FACSIMILES=('artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg')
PRIORS=tuple(f'data/einstein-field-comparison-claim-u{n:04d}-review-v1.json' for n in (163,164))
DEPENDENCIES=('reports/field-comparison-claim-v1.json','reports/inverse-methods-v1.json','reports/field-scale-inverse-v1.json','reports/field-transform-v1.json')
CONSTANTS={'ri':'context','rd':'author','eirf':'paper','zno':'scope','zoe':'methods','zn3':'result','eisp4':'prior','eisp5':'display'}
DOMAIN=tuple(CONSTANTS.values())+('other',);SITUATIONS=('context','other')

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sjt'}|{'ejur':{'ejub'},'ejus':{'ejur','sbp2'},'ejut':{'ejur','sbq2'},'ejuv':{'ejur','sbr2'},'ejuw':{'ejur','ejuv'},'ejux':{'ejuu','ejuw'},'ejuy':{'ejux','ejuh','ejur'},'ejuz':{'ejur','s45'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    d=next(d for d in doc['declarations'] if d['name']==name);expr=dict(kind='call',symbol=name,arguments=[])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc

def run(name,m,doc=None):
    doc=fixture(name) if doc is None else doc;mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    return evaluate_document(doc,individuals=DOMAIN,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def contents(names,bits):return {n:lambda b=b:Content(SITUATIONS,(b,not b)) for n,b in zip(names,bits)}

@lru_cache(None)
def binding_checks():
    cases=0
    for a,b,expected in ((2,Q(1,2),True),(-2,Q(-1,2),True),(2,3,True),(0,1,False),(2,0,True)):
        cuts,m=arithmetic();c,r=cuts.make,cuts.read;seen=[]
        def factor(x):seen.append(r(x));return c(a if r(x)==3 else b)
        m|={'znz':lambda:FunctionValue((RS,),RS,factor),'zb7':lambda:c(3),'ejub':lambda:Content(SITUATIONS,(True,False))}
        assert run('ejur',m)==expected;assert set(seen)=={Q(3),Q(-3)};cases+=1
        assert not run('ejur',m|{'ejub':lambda:Content(SITUATIONS,(False,True))});cases+=1
    for name,names in [('ejus',('ejur','sbp2')),('ejut',('ejur','sbq2')),('ejuv',('ejur','sbr2')),('ejux',('ejuu','ejuw')),('ejuy',('ejux','ejuh','ejur'))]:
        for bits in product((False,True),repeat=len(names)):
            assert run(name,contents(names,bits))==all(bits);cases+=1
        unknowns(lambda mm:run(name,mm),contents(names,[True]*len(names)),names)
    return dict(cases=cases,first_inverse_nonzero_without_positivity=True,current_physical_setting_and_previous_formula_connected=True,coefficient_evaluated_at_both_opposite_speeds=True)

@lru_cache(None)
def path_checks():
    cases=0
    alternatives={
      'baseline':([('ejuh','ejus')],[('ejuh','ejut')],True),
      'empty_first':([],[('ejuh','ejut')],False),
      'empty_second':([('ejuh','ejus')],[],False),
      'swapped':([('ejuh','ejut')],[('ejuh','ejus')],False),
      'obsolete_source':([('sak2','ejus')],[('ejuh','ejut')],False),
      'broken_first':([('ejuh','ejut'),('ejuh','ejus')],[('ejuh','ejut')],False),
      'wrong_context':([('ejuh','ejus')],[('ejuh','ejut')],False),
      'disallowed_second':([('ejuh','ejus')],[('ejuh','ejut')],False),
    }
    for label,(first,second,want) in alternatives.items():
        doc=deepcopy(fixture('ejuu'))
        for name,pairs in (('zoc',first),('zod',second)):
            definition=parse('n:r ejuh[] e.r ejus[] e.r ejut[] e.r sak2[] e.d '+name+'[] '+STEPS+'['+sequence(pairs)+'].')['declarations'][-1]
            doc['declarations']=[d for d in doc['declarations'] if d['name']!=name]
            index=next(i for i,d in enumerate(doc['declarations']) if d['name']=='ejuu');doc['declarations'].insert(index,definition)
        allowed={('ejuh','ejus'),('ejuh','ejut')}
        if label=='disallowed_second':allowed.remove(('ejuh','ejut'))
        m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zla':lambda a,b,ctx:(symbol(a),symbol(b)) in allowed and ctx==('other' if label=='wrong_context' else 'context')}
        assert run('ejuu',m,doc)==want,label;cases+=1
    return dict(cases=cases,native_nonempty_ordered_paths=True,previous_current_formula_not_obsolete_quote=True,quoted_contents_not_executed=True)

@lru_cache(None)
def necessity_checks():
    cases=0
    for selected,truth in product(product((False,True),repeat=2),repeat=2):
        m={'ejur':lambda:Content(SITUATIONS,selected),'ejuv':lambda:Content(SITUATIONS,truth)}
        assert run('ejuw',m)==(any(selected) and all(not a or b for a,b in zip(selected,truth)));cases+=1
    unknowns(lambda mm:run('ejuw',mm),contents(('ejur','ejuv'),(True,True)),('ejur','ejuv'))
    return dict(cases=cases,nonempty_all_selected_situations=True,necessity_not_current_identity=True)

@lru_cache(None)
def conclusion_checks():
    cases=0
    for a,b,want in ((2,Q(1,2),True),(-2,Q(-1,2),True),(-1,-1,True),(2,3,False),(0,1,False)):
        cuts,m=arithmetic();c,r=cuts.make,cuts.read
        m|={'znz':lambda:FunctionValue((RS,),RS,lambda x:c(a if r(x)==3 else b)),'zb7':lambda:c(3),'tc':lambda:c(5),'s45':lambda light,speed:r(light)==5 and r(speed)==3,'ejur':lambda:Content(SITUATIONS,(True,False))}
        assert run('ejuz',m)==want;cases+=1
        assert not run('ejuz',m|{'ejur':lambda:Content(SITUATIONS,(False,True))});cases+=1
    return dict(cases=cases,native_product_one=True,negative_and_minus_one_allowed=True,no_evenness_or_positive_one_assumed=True)

@lru_cache(None)
def presentation_checks():
    rows={'zc':{('result','author','ejuy','ejuz','scope','context')},'eisox':{('display','ejuz','context')},'uf':{('author','result','display','context')},'ue':{('methods','result','context'),('result','display','context')}}
    m={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mm:run('ejvc',mm),m,rows)
    assert run('ejvc',m|{n:forbidden for n in ('ejuy','ejuz','ejuw','sbo2')});cases+=1
    for symbol,target in [('zn3','methods'),('eisp5','result'),('eisp5','methods')]:
        assert not run('ejvc',{n:lambda *xs:True for n in rows}|{symbol:lambda target=target:target});cases+=1
    for name,rs in [('ejvb',{'eir3':{('methods','author','paper','ejva','context')},'ue':{('prior','methods','context')}}),('ejve',{'eir3':{('result','author','paper','ejvd','context')}})]:
        cases+=perturb(lambda mm:run(name,mm),{n:relation(v) for n,v in rs.items()},rs)
    return dict(cases=cases,conditional_inference_display_order_and_author=True,necessity_and_conclusion_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));table={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][164:166]:
        assert digest(u['text'].encode())==u['text_sha256'];ms=[table[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    flat=lambda mid:''.join(ET.fromstring(table[mid]['mathml']).itertext())
    raw={n:flat(n) for n in ('M0308','M0309','M0310','M0311')}
    assert list(raw.values())==['k','K','−v','φ(v).φ(−v)=1'],raw
    correction=json.loads(read(CORRECTION));assert digest((ROOT/correction['image']).read_bytes())==correction['image_sha256']
    assert digest((ROOT/correction['path']).read_bytes())==correction['sha256']
    return dict(version='einstein-inverse-field-claim-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['909'],segments=segments,raw_math=raw,observations=['原刊909頁のu0165–u0166を一文として通読した。erstens/zweitens、soeben、kからK、-v、identisch sein müssen、indem man berücksichtigt、so folgtを二方法・参照・必要性・理由付き帰結に接続する。','φ(v)φ(-v)=1の両速度・積・値1を照合した。909頁のφは908頁のψと同じ第六節の係数を指すという旧字形照合の読みを維持する。','式の同一性は変換規則として任意入力で成立する必要性と読む。零の場だけの一致を係数の制約へ格上げしない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,CORRECTION,*FACSIMILES)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==INDICES
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p in PRIORS:
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[155])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,INDICES)['dependencies'])
    assert set(MEANINGS)|{'ejub','ejuh','sbi2','sbj2','sbk2','sbl2','sbm2','sbp2','sbq2','sbo2','sbs2','saq2','ejrj','s5k','zc'}<=names
    assert not names&{'sar2','sat2','sap2'}
    prior=json.loads(read('reports/inverse-methods-v1.json'))
    assert prior['finite_refusal']['refused'] and prior['scalars']['nonzero_witness_algebra']['status']=='valid'
    assert prior['fields']['zero_field_agreement_not_general_operator_agreement']
    assert prior['source_binding']['global_field_equality_and_domain_equality_are_explicit_fixture_oracles']
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=1,replaced_statements=INDICES,source_order_statements=SOURCE_ORDER,other_356_statements_and_prior_judgments_preserved=True,prior_native_six_inverse_components_and_zero_counterexample_pinned=True,full_domain_refusal_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('binding',binding_checks),('paths',path_checks),('necessity',necessity_checks),('conclusion',conclusion_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_moving_trip_geometry','check_material_relative_frame','check_calculation_discourse','compose_calculation_discourse','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_inverse_field_claim.py','scripts/check_inverse_field_claim.py','tests/test_inverse_field_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    segments=[]
    for s in source_record()['segments']:
        row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=INDICES,definitions=list(MEANINGS),status='explicit_interpretive_annotation');segments.append(row)
        for m in s['math']:segments.append(dict(row,math_id=m['id'],math_sha256=m['sha256']))
    return dict(status='two_inverse_methods_required_identity_and_product_one_connected',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0165–u0166の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
