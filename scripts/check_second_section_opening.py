"""Check both topics, both premises, and exact prospective definition references."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_second_section_opening import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDICES,build
from scripts.review_second_section_opening import SOURCE,INVENTORY,DOC,PRIORS,source_record

POINTS=('now','other');DOMAIN=('inquiry','paper','part','section','heading','preceding','intro','author','scope','relativity','light','first','second','other')

def forbidden(*args):raise ValueError('Unknown second-section-opening input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def changed(row,i):return tuple('other' if j==i else x for j,x in enumerate(row))


@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jsso'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jssocontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jssocontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=100000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def run(name,args,m):
    doc,slots=fixture(name);assert len(args)==len(slots)
    return evaluate(doc,m|{'jssocontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})


def perturbations(check,m,rows):
    count=0
    assert check(m);count+=1
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:relation(rs-{row})});count+=1
            for i in range(len(row)):
                assert not check(m|{n:relation((rs-{row})|{changed(row,i)})});count+=1
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown second-section-opening' in str(e)
        else:raise AssertionError(('Unknown input accepted',n))
    return count


@lru_cache(None)
def topic_checks():
    rows={'eiskw':{('inquiry','th','now')},'eiskx':{('inquiry','zbe','eihm','now')},'eisky':{('inquiry','now')}}
    m={n:relation(rs) for n,rs in rows.items()}
    count=perturbations(lambda x:run('eiob',['inquiry','now'],x),m,rows)
    for bits in product((False,True),repeat=3):
        assert run('eiob',['inquiry','now'],m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
    assert run('ein7',['inquiry','now'],m|{'eiskx':forbidden});count+=1
    assert run('eioa',['inquiry','now'],m|{'eiskw':forbidden});count+=1
    assert run('eiob',['inquiry','now'],m|{n:forbidden for n in ('th','zbe','va','zbd','eisb7','ce')});count+=1
    return dict(cases=count,both_quantity_topics_and_frame_dependence_required=True,physical_quantity_and_simultaneity_not_executed=True,unknown_inputs_rejected=3)


def base_model():
    values={'eirf':'paper','rd':'author','eisdx':'part','eiskz':'section','eisk2':'heading','eiskt':'preceding','wu':'intro','wv':'scope','eisk3':'relativity','eisk4':'light','vk':'first','wt':'second','ri':'now'}
    return {n:(lambda x=x:x) for n,x in values.items()}


def premise_rows():
    return {'eisch':{('relativity','eifj','scope','now'),('light','eify','scope','now')},'ug':{('intro','author','eifj','scope','now'),('intro','author','eify','scope','now')}}


@lru_cache(None)
def premise_checks():
    rows=premise_rows();m=base_model()|{n:relation(rs) for n,rs in rows.items()}
    count=perturbations(lambda x:run('eiod',['scope','now'],x),m,rows)
    flat=[(n,row) for n,rs in rows.items() for row in sorted(rs)]
    for bits in product((False,True),repeat=4):
        chosen={n:{row for (key,row),on in zip(flat,bits) if key==n and on} for n in rows}
        assert run('eiod',['scope','now'],m|{n:relation(rs) for n,rs in chosen.items()})==all(bits);count+=1
    assert run('eiod',['scope','now'],m|{n:forbidden for n in ('eisb7','va','tc','vj','ws')});count+=1
    return dict(cases=count,both_named_contents_adopted_in_same_scope=True,adoption_does_not_require_physical_truth_or_sufficiency=True,unknown_inputs_rejected=2)


def introduction_model():
    rows=premise_rows()|{'eisci':{('scope','paper','intro','now')},'eisk5':{('intro','author','eifj','first','paper','now'),('intro','author','eify','second','paper','now')},'ue':{('intro','first','now'),('first','second','now')}}
    return base_model()|{n:relation(rs) for n,rs in rows.items()},rows


@lru_cache(None)
def introduction_checks():
    m,rows=introduction_model();count=perturbations(lambda x:run('eioe',[],x),m,rows)
    swapped={('intro','author','eifj','second','paper','now'),('intro','author','eify','first','paper','now')}
    assert not run('eioe',[],m|{'eisk5':relation(swapped)});count+=1
    reversed_order={(b,a,c) for a,b,c in rows['ue']}
    assert not run('eioe',[],m|{'ue':relation(reversed_order)});count+=1
    # External relations all true cannot erase the specified separation of locations.
    yes={n:lambda *xs:True for n in rows}
    for symbol,target in (('vk','intro'),('wt','first')):
        assert not run('eioe',[],m|yes|{symbol:lambda x=target:x});count+=1
    assert run('eioe',[],m|{n:forbidden for n in ('vl','th','zbe','va','eisb7','tc','vj','ws')});count+=1
    return dict(cases=count,same_pair_in_future_definitions=True,following_scope_and_definition_order_preserved=True,definition_and_physics_not_executed=True,unknown_inputs_rejected=5)


@lru_cache(None)
def presentation_checks():
    count=0
    for path in (CORE,FULL):
        original=parse(read(path))
        rows={'eisdv':{('heading','section','part','paper',Q(2),Q(2),'now')},'eisdw':{('heading','section','eiob','now')},'ue':{('preceding','heading','now')}}
        doc=dict(original,statements=original['statements'][-2:-1]);m=base_model()|{n:relation(rs) for n,rs in rows.items()}
        count+=perturbations(lambda x:evaluate(doc,x),m,rows)
        for symbol,target in (('eisk2','section'),('eiskz','part'),('eiskt','heading')):
            assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{symbol:lambda x=target:x});count+=1
        assert evaluate(doc,m|{n:forbidden for n in ('eir3','eiskw','eiskx','eisky','th','zbe')});count+=1
        rows={'eir3':{('intro','author','paper','eiof','now')},'ue':{('heading','intro','now')}}
        doc=dict(original,statements=original['statements'][-1:]);m=base_model()|{n:relation(rs) for n,rs in rows.items()}
        count+=perturbations(lambda x:evaluate(doc,x),m,rows)
        assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{'eisk2':lambda:'intro'});count+=1
        assert evaluate(doc,m|{n:forbidden for n in ('ug','eisch','eisci','eisk5','vl')});count+=1
    return dict(cases=count,section_two_of_part_one=True,heading_not_assertion_of_physics=True,introduction_attributed_to_same_author=True,quoted_topics_and_contents_not_executed=True,unknown_inputs_rejected=10)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==249
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,indices in zip(PRIORS,([220],[213,214,215,216],[246])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert prior['selection']==selection_binding(new,indices)
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    entries=json.loads(read(ANNOTATIONS))['entries'];prior=json.loads(read('data/rest-system-time-identifiers-v1.json'))['entries']
    assert entries[:-2]==prior
    assert [(e['symbol'],e['forms'][0]['text']) for e in entries[-2:]]==[('eisk3','Relativitätsprinzip'),('eisk4','Prinzip der Konstanz der Lichtgeschwindigkeit')]
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert {'th','zbe','eihm','seh','qo','saf','sca','eifj','eify'}<=set(ds)
    assert not {'saw','sbd'}&set(ds)
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert sum(s['nonblank_characters'] for s in source['segments'])==201
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=247,prior_heading_principles_and_time_reviews_preserved=True,source_and_section_boundary_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('topics',topic_checks),('premises',premise_checks),('introduction',introduction_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record()
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,'scripts/compose_second_section_opening.py','scripts/check_second_section_opening.py','scripts/review_second_section_opening.py','tests/test_second_section_opening.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='second_section_topic_and_two_principle_introduction_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['全単位判断の登録、u0025以降の定式化との比較と記述'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
