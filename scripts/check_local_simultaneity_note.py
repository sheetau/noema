"""Check near-local scope, the same conceptual issue and a non-executed remedy."""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_motion_time_description import PRIORS
from scripts.compose_local_simultaneity_note import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/local-simultaneity-note-v1.md';SOURCE='data/einstein-time-continuation-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
READINGS=('data/motion-time-description-reading-v1.json','data/temporal-judgments-reading-v1.json','data/train-clock-example-reading-v1.json')
DOMAIN=('a','b','frame','p','q','issue','note','node','author','paper','other');POINTS=('now','other')

def forbidden(*args):raise ValueError('Unknown local-simultaneity-note input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jln'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jlncontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jlncontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,values,m,context='now'):
    doc,slots=fixture(name);assert len(values)==len(slots)
    return evaluate(doc,m|{'jlncontext':lambda:context}|{n:(lambda x=x:x) for n,x in zip(slots,values)})

@lru_cache(None)
def locality_checks():
    count=0
    for same,near,firstevent,secondevent,frame in product((False,True),repeat=5):
        right='p' if same else 'q'
        m={'cb':relation({('a','p','frame'),('b',right,'frame')}),'zbd':relation({(x,) for x,on in (('a',firstevent),('b',secondevent)) if on}),'va':relation({('frame',)} if frame else set()),'eisfp':relation({('p',right,'frame','now')} if near else set())}
        assert run('eijd',['a','b','frame','now'],m)==((same or near) and firstevent and secondevent and frame);count+=1
    rows={'cb':{('a','p','frame'),('b','q','frame')},'zbd':{('a',),('b',)},'va':{('frame',)},'eisfp':{('p','q','frame','now')}}
    m={n:relation(rs) for n,rs in rows.items()}
    for name in ('cb','eisfp'):
        for row in rows[name]:
            for slot in range(len(row)):
                bad=tuple('other' if i==slot else x for i,x in enumerate(row))
                # Place names are existential. Change both bindings only through the explicitly defined near relation.
                assert not run('eijd',['a','b','frame','now'],m|{name:relation((rows[name]-{row})|{bad})}),(name,slot);count+=1
    assert not run('eijd',['a','a','frame','now'],m);count+=1
    # Locality alone neither queries nor establishes simultaneous occurrence.
    assert run('eijd',['a','b','frame','now'],m|{'eihm':forbidden,'zbe':forbidden});count+=1
    for name in rows:
        try:run('eijd',['a','b','frame','now'],m|{name:forbidden})
        except ValueError as e:assert 'Unknown local-simultaneity-note' in str(e)
        else:raise AssertionError('Unknown local scope accepted')
    return dict(cases=count,exact_and_approximately_same_place=True,remote_or_other_frame_not_silently_local=True,distinct_events_without_asserting_simultaneity=True,unknown_inputs_rejected=True)

def references():return dict(eisfv=lambda:'issue',eisfn=lambda:'note',eisfm=lambda:'node',rd=lambda:'author',eirf=lambda:'paper',ri=lambda:'now')

@lru_cache(None)
def caveat_checks():
    count=0
    rows={'eisfq':{('issue','eihm','eijd','paper','now')},'eisfs':{('issue','eisfr','paper','now')},'eisfu':{('note','issue','eisfr','paper','now')},'eisft':{('author','issue','note','paper','now')}}
    m=references()|{n:relation(rs) for n,rs in rows.items()}
    for bits in product((False,True),repeat=4):
        assert run('eije',[],m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
    for name,rs in rows.items():
        row=next(iter(rs))
        for slot in range(len(row)):
            bad=tuple('other' if i==slot else x for i,x in enumerate(row));assert not run('eije',[],m|{name:relation({bad})});count+=1
        try:run('eije',[],m|{name:forbidden})
        except ValueError as e:assert 'Unknown local-simultaneity-note' in str(e)
        else:raise AssertionError('Unknown caveat accepted')
    # A required abstraction remains unexecuted; the problem is asserted through its own relation.
    assert run('eije',[],m|{n:forbidden for n in ('eisfr','eihm','eijd','cb','eisfp','zbe')});count+=1
    for symbol in ('eisfv','eisfn','rd','eirf'):
        assert not run('eije',[],m|{symbol:lambda:'other'});count+=1
    return dict(cases=count,same_issue_concept_scope_and_remedy=True,imprecision_necessity_addition_and_nondiscussion_all_kept=True,abstraction_required_not_already_performed=True,discussion_policy_not_problem_denial=True)

@lru_cache(None)
def presentation_checks():
    count=0;rows={'eir3':{('note','author','paper','eijf','now')},'eisfo':{('node','note','paper',Q(1),'now')}}
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(rs) for n,rs in rows.items()}
        for bits in product((False,True),repeat=2):
            assert evaluate(doc,m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
        for name,rs in rows.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                bad=tuple((Q(2) if isinstance(x,Q) else 'other') if i==slot else x for i,x in enumerate(row));assert not evaluate(doc,m|{name:relation({bad})});count+=1
        assert not evaluate(doc,m|{'eisfn':lambda:'node','eir3':lambda *xs:True,'eisfo':lambda *xs:True});count+=1
    ds={d['name']:d for d in parse(read(CORE))['declarations']};assert ds['eijf']['body']['force']=='assert'
    return dict(cases=count,same_author_document_and_note_one=True,no_main_text_order_inferred_from_inventory_position=True,quoted_note_not_executed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==229
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216],[217,218],[219],[220],[221,222],[223])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    for path,indices in zip(READINGS,([224,225],[226],[227])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256']);inv=json.loads(read(INVENTORY));note=next(u for u in inv['units'] if u['id']=='einstein-1905:u0279');segment=source['segments'][2]
    assert len(note['text'])==212 and sum(not c.isspace() for c in note['text'])==185 and not note['math_ids']
    assert segment['unit']==note['id'] and segment['range']==[0,212] and segment['text']==note['text'] and segment['unit_sha256']==note['text_sha256']
    assert source['pages']==['893'] and source['note_anchor']['target']==note['id']
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=228,prior_reviews_and_four_sentences_preserved=True,original_page_and_note_identity_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results=dict(locality=locality_checks(),caveat=caveat_checks(),presentation=presentation_checks(),structure=structure_checks())
    note=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0279')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,*READINGS,*PRIORS,'scripts/compose_local_simultaneity_note.py','scripts/check_local_simultaneity_note.py','tests/test_local_simultaneity_note.py','scripts/check_motion_time_description.py','scripts/compose_train_clock_example.py','scripts/compose_kinematics_headings.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='local_simultaneity_note_content_and_anchor_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=note['id'],unit_sha256=note['text_sha256'],range=[0,212],source=note['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
