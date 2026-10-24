"""Check part number, hierarchy, physical topic and transition order."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_clock_site_time import relation,perturb,forbidden
from scripts.compose_electrodynamic_part_heading import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build

DOC='docs/electrodynamic-part-heading-v1.md'
SOURCE='data/einstein-electrodynamic-part-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=('artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg')
PRIORS=('data/einstein-kinematics-heading-review-v1.json','data/einstein-kinematic-transition-u0150-review-v1.json')
DEPENDENCIES=('reports/kinematics-headings-v1.json','reports/electrodynamics-title-v1.json','reports/kinematic-transition-claim-v1.json')
CONSTANTS={'eispc':'heading','eispb':'second','eisdx':'first','eirf':'paper','znj':'transition','ri':'now'}
DOMAIN=('heading','second','first','paper','transition','inquiry','other')


@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jedh'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
    return doc,slots


def run(name,args,model):
    doc,slots=fixture(name);assert len(args)==len(slots)
    m={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=('now','other'),primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=100000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def heading_checks():
    rows={'eisdv':{('heading','second','paper','paper',Q(1),Q(2),'now')},'eisdw':{('heading','second','eie5','now')},'ue':{('transition','heading','now')}}
    m={n:relation(rs) for n,rs in rows.items()}
    count=perturb(lambda pp:run('ejsi',[],pp),m,rows)
    for name,value in (('eispc','second'),('eispb','paper'),('eispc','transition'),('eispb','first')):
        assert not run('ejsi',[],{n:lambda *xs:True for n in rows}|{name:lambda value=value:value});count+=1
    # A part number is not the following section number, and hierarchy is not
    # an ordinal. Keep explicit numeric contrasts in addition to slot changes.
    for depth,ordinal in ((2,2),(1,6),(2,6),(1,1)):
        assert not run('ejsi',[],m|{'eisdv':relation({('heading','second','paper','paper',Q(depth),Q(ordinal),'now')})});count+=1
    return dict(cases=count,part_two_at_depth_one=True,same_paper_parent_and_distinct_first_part=True,transition_then_heading=True,physical_topic_quote_not_executed=True)


@lru_cache(None)
def topic_checks():
    rows={'eisa6':{('inquiry','eibf','eibs','eico','now')}}
    m={n:relation(rs) for n,rs in rows.items()}
    count=perturb(lambda pp:run('eie5',['inquiry','now'],pp),m,rows)
    return dict(cases=count,charge_transport_electric_and_magnetic_roles_shared=True,topic_not_a_field_law_assertion=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][150]
    assert u['id']=='einstein-1905:u0151' and u['kind']=='heading' and not u['math_ids']
    assert u['text']=='II. Elektrodynamischer Teil.' and digest(u['text'].encode())==u['text_sha256']
    sections=[x for x in inv['units'][151:] if x['kind']=='heading']
    assert [re.match(r'§ (\d+)\.',x['text'])[1] for x in sections]==['6','7','8','9','10']
    s=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=[],source_nonblank_characters=sum(not c.isspace() for c in u['text']))
    paths={INVENTORY,DOC,*FACSIMILES}
    return dict(version='einstein-electrodynamic-part-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['907'],segments=[s],division=dict(level=1,displayed_number='II',ordinal=2,parent='eirf',first='einstein-1905:u0151',subordinate_headings=[x['id'] for x in sections],footnotes_follow_references_not_inventory_order=True),observations=['原刊907頁で、運動学の総括と移行の後、§6の前にある独立した第二部見出しを照合した。II・句点・Elektrodynamischer Teilを確認した。','固定転記の後続見出しは§6–§10で、第二部の後に同階層以上の見出しはない。末尾に集められた注の配列位置を所属範囲の代用にしない。','見出しの主題案内と本文の主張、課題開始と達成を区別した。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==357 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([219],[150,151])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert {'ejsi','eihq','eisdv','eisdw','eie5','eisa6','eibf','eibs','eico'}<=names
    assert not names&{'eir3','znh','ejr7','ejsb','s5z','s6o'}
    added=new.document['declarations'][len(old.document['declarations']):]
    assert {d['name'] for d in added if d['kind']=='primitive'}==set(PRIMITIVES)
    assert all(not d['parameters'] and d['result']=='individual' for d in added if d['kind']=='primitive')
    core=parse(read(CORE))
    assert core['statements']==[new.document['statements'][INDEX]]
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=1,new_reference_individuals=2,other_statements_preserved=356,prior_judgments_preserved=True,heading_not_an_assertion_of_physics_or_goal_completion=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('heading',heading_checks),('topic',topic_checks),('structure',structure_checks)]}
    helpers=('compose_kinematic_transition_claim','compose_material_relative_frame','compose_limits','check_clock_site_time','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_electrodynamic_part_heading.py','scripts/check_electrodynamic_part_heading.py','tests/test_electrodynamic_part_heading.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record()['segments'][0]
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')])
    return dict(status='second_part_heading_and_electrodynamic_topic_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0151の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
