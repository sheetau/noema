"""Check topic conjunction, quotation boundaries and title discourse bindings."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_electrodynamics_title import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build

DOC='docs/electrodynamics-title-v1.md';SOURCE='data/einstein-opening-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';REPORT='reports/electrodynamics-title-v1.json'
PRIORS=('data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json')
def forbidden(*xs):raise ValueError('Unknown title input')
def value(x):return json.loads(x.syntax)['symbol'] if hasattr(x,'syntax') else x
def evaluate(doc,model):
    ps={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=('inquiry','node','paper','authorcredit','opening','other'),situations=('front','other'),primitives={n:model.get(n,forbidden) for n in ps},max_steps=10000,memoize_definitions=False,memoize_expressions=False)[0]['value']
def relation(row,bit=True):return lambda *xs:bit and tuple(value(x) for x in xs)==row

@lru_cache(None)
def topic_fixture():
    doc=extract_document(parse(read(CORE)),roots=['eie6'],statement_indices=[]).document
    doc['declarations'] += [dict(kind='primitive',name='jaainquiry',parameters=[],result='individual'),dict(kind='primitive',name='jaacontext',parameters=[],result='situation')]
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol='eie6',arguments=[dict(kind='call',symbol=n,arguments=[]) for n in ('jaainquiry','jaacontext')]))]
    return doc

@lru_cache(None)
def topic_checks():
    count=0
    for inquiry,context in (('inquiry','front'),('other','other')):
        expected={'eisa6':(inquiry,'eibf','eibs','eico',context),'eisa7':(inquiry,'eiag',context)}
        def model(bits=(True,True),bad=None):
            m=dict(jaainquiry=lambda:inquiry,jaacontext=lambda:context)
            for i,(name,row) in enumerate(expected.items()):
                if bad and bad[0]==name:row=tuple('wrong' if j==bad[1] else x for j,x in enumerate(row))
                m[name]=relation(row,bits[i])
            return m
        for bits in product((False,True),repeat=2):assert evaluate(topic_fixture(),model(bits))==all(bits);count+=1
        for name,row in expected.items():
            for slot in range(len(row)):assert not evaluate(topic_fixture(),model(bad=(name,slot)));count+=1
            m=model();m[name]=forbidden
            try:evaluate(topic_fixture(),m)
            except ValueError as e:assert 'Unknown title' in str(e)
            else:raise AssertionError('Unknown topic input accepted')
    return dict(cases=count,unknown_inputs_rejected=4,shared_inquiry_and_context=True,four_quoted_physical_schemas_preserved=True,physical_schemas_not_executed=True)

def presentation_model(bits=(True,)*4,bad=None,collision=None):
    node=collision or 'node'
    m=dict(eisbc=lambda:node,eirf=lambda:'paper',eire=lambda:'authorcredit',eir7=lambda:'opening',eirg=lambda:'front')
    rows={'eisba':(node,'paper','front'),'eisbb':(node,'paper','eie6','front')}
    for i,(name,row) in enumerate(rows.items()):
        if bad and bad[0]==name:row=tuple('wrong' if j==bad[1] else x for j,x in enumerate(row))
        m[name]=relation(row,bits[i])
    orders=[(node,'authorcredit','front'),(node,'opening','front')]
    if bad and bad[0]=='ue':
        which,slot=divmod(bad[1],3);orders[which]=tuple('wrong' if j==slot else x for j,x in enumerate(orders[which]))
    m['ue']=lambda *xs:any(bit and tuple(xs)==row for row,bit in zip(orders,bits[2:]))
    return m

@lru_cache(None)
def presentation_checks():
    count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        for bits in product((False,True),repeat=4):assert evaluate(doc,presentation_model(bits))==all(bits);count+=1
        for name,arity in (('eisba',3),('eisbb',4),('ue',6)):
            for slot in range(arity):assert not evaluate(doc,presentation_model(bad=(name,slot)));count+=1
        for collision in ('authorcredit','opening'):assert not evaluate(doc,presentation_model(collision=collision));count+=1
        for name in ('eisba','eisbb','ue'):
            m=presentation_model();m[name]=forbidden
            try:evaluate(doc,m)
            except ValueError as e:assert 'Unknown title' in str(e)
            else:raise AssertionError('Unknown title role accepted')
    return dict(cases=count,unknown_inputs_rejected=6,title_contribution_and_both_orders_required=True,distinct_nodes=True,topic_not_executed=True,full_and_core=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==213
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([206],[207,208,209,210,211])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert not names&{'eisax','eisak','eisaa','eisab','eisac'}
    assert {'eiag','eibf','eibs','eico','eirf','eire','eir7','eirg'}<=names
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    reading=json.loads(read(SOURCE));validate_hashes(ROOT,reading['source_sha256'])
    unit=json.loads(read(INVENTORY))['units'][0]
    assert unit['id']=='einstein-1905:u0001' and unit['text']=='Zur Elektrodynamik bewegter Körper;' and not unit.get('math_ids',[])
    assert reading['source_units'][0]['text']==unit['text'] and reading['source_units'][0]['unit_sha256']==unit['text_sha256']
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=INDEX,prior_reviews_preserved=True,no_specific_theory_or_example_required=True,core_roundtrips=['compact','full','v2'],source_range=[0,len(unit['text'])])

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    result=dict(topic=topic_checks(),presentation=presentation_checks(),structure=structure_checks())
    unit=json.loads(read(INVENTORY))['units'][0]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{DOC,SOURCE,INVENTORY,*PRIORS,'scripts/compose_electrodynamics_title.py','scripts/check_electrodynamics_title.py','tests/test_electrodynamics_title.py','scripts/compose_apparent_asymmetry.py','scripts/compose_material_body_motion.py','scripts/compose_electric_action.py','scripts/compose_magnetic_action.py','scripts/compose_current_distribution.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='electrodynamics_title_topic_and_presentation_checked',document=FULL,**result,alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],source=unit['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
