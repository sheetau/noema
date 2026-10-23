"""Check inadequate consideration, current difficulty scope and shared causes."""
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
from scripts.check_coordinate_correspondence import abstract
from scripts.check_kinematic_foundation import model as first_model
from scripts.compose_kinematic_difficulties import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/kinematic-difficulties-v1.md';SOURCE='data/einstein-kinematics-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/kinematic-difficulties-reading-v1.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json','data/einstein-principles-paragraph-review-v1.json','data/kinematic-foundation-reading-v1.json')
DOMAIN=('a','b')

def forbidden(*args):raise ValueError('Unknown kinematic-difficulty input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode=='bound':abstract(doc,{'eihf','eihh'})
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jkd'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jkdpoint',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jkdpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,model,point='a',domain=DOMAIN):
    m=dict(model,jkdpoint=lambda:point)
    return evaluate_document(doc,individuals=domain,situations=DOMAIN,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,values,model,point='a',mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots)
    return evaluate(doc,model|{n:(lambda x=x:x) for n,x in zip(slots,values)},point,domain)

def base():return dict(rd=lambda:'b',eirf=lambda:'a',ri=lambda:'a',eisdl=lambda:'a',eisds=lambda:'b')
def model(practice='a',inquiry='b',point='a'):
    m,_=first_model(point)
    rows={
        'eisa6':{(inquiry,'eibf','eibs','eico',point)},'eisa7':{(inquiry,'eiag',point)},
        'eisdm':{(practice,inquiry,'eiha',point)},'eisdn':set(),
        'eisdo':{(d,inquiry,point) for d in DOMAIN},'eisdp':{(d,inquiry,'a',point) for d in DOMAIN},
        'eisdq':{(practice,d,inquiry,point) for d in DOMAIN},'eisdr':{(d,'a',point) for d in DOMAIN},
    }
    return m|base()|{n:relation(rs) for n,rs in rows.items()},rows

@lru_cache(None)
def consideration_checks():
    count=0
    for treatment,adequate in product((False,True),repeat=2):
        m,rows=model();m.update(eisdm=relation(rows['eisdm'] if treatment else set()),eisdn=relation({('a','eiha','a')} if adequate else set()))
        assert run('eihf',['a','b','a'],m)==(treatment and not adequate);count+=1
    m,rows=model();row=next(iter(rows['eisdm']))
    for slot in range(len(row)):
        bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
        assert not run('eihf',['a','b','a'],m|{'eisdm':relation({bad})});count+=1
    # Adequate handling of a different fact/practice/situation does not cure this omission.
    row=('a','eiha','a')
    for slot in range(len(row)):
        bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
        assert run('eihf',['a','b','a'],m|{'eisdn':relation({bad})});count+=1
    for n in ('eisdm','eisdn'):
        try:run('eihf',['a','b','a'],m|{n:forbidden})
        except ValueError as e:assert 'Unknown kinematic-difficulty' in str(e)
        else:raise AssertionError('Unknown treatment mistaken for inadequate treatment')
    return dict(cases=count,same_fact_and_practice=True,complete_omission_and_partial_consideration_allowed=True,unknown_inputs_rejected=2)

@lru_cache(None)
def difficulty_checks():
    count=0
    for scope,obstacles,current in product(product((False,True),repeat=2),repeat=3):
        selected={x for x,on in zip(DOMAIN,scope) if on};difficult={x for x,on in zip(DOMAIN,obstacles) if on};now={x for x,on in zip(DOMAIN,current) if on}
        m,_=model();m.update(eisdr=relation({(d,'a','a') for d in selected}),eisdo=relation({(d,'b','a') for d in difficult}),eisdp=relation({(d,'b','a','a') for d in now}))
        assert run('eihh',['b','a'],m)==(len(selected)>=2 and selected<=difficult and selected<=now);count+=1
    m,rows=model()
    for name in ('eisa6','eisa7','eisdo','eisdp','eisdr'):
        for row in rows[name]:
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not run('eihh',['b','a'],m|{name:relation((rows[name]-{row})|{bad})});count+=1
    # A third selected difficulty cannot evade the physical-domain and historical-current conditions.
    assert not run('eihh',['b','a'],m|{'eisdr':relation({(d,'a','a') for d in ('a','b','c')})},domain=('a','b','c'));count+=1
    return dict(cases=count,plural_and_complete_contextual_scope=True,same_moving_body_inquiry=True,document_time_not_runtime=True)

@lru_cache(None)
def cause_checks():
    count=0
    for roots in product((False,True),repeat=2):
        m,rows=model();m['eisdq']=relation({('a',d,'b','a') for d,on in zip(DOMAIN,roots) if on})
        assert run('eihi',['a','b','a'],m)==all(roots);count+=1
    m,rows=model()
    assert run('eihi',['a','b','a'],m|{'eisdq':relation(rows['eisdq']|{('b',d,'b','a') for d in DOMAIN})});count+=1
    for row in rows['eisdq']:
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
            assert not run('eihi',['a','b','a'],m|{'eisdq':relation((rows['eisdq']-{row})|{bad})});count+=1
    for n in ('eisdm','eisdn','eisdo','eisdp','eisdq','eisdr','eisa6','eisa7'):
        try:run('eihi',['a','b','a'],m|{n:forbidden})
        except ValueError as e:assert 'Unknown kinematic-difficulty' in str(e)
        else:raise AssertionError('Unknown cause or difficulty scope accepted')
    return dict(cases=count,all_selected_difficulties_have_same_foundational_cause=True,other_causes_allowed=True,unknown_inputs_rejected=8)

@lru_cache(None)
def sentence_checks():
    count=0
    for practice,inquiry,point in product(DOMAIN,repeat=3):
        m,rows=model(practice,inquiry,point)
        assert run('eihj',[],m,point=point);count+=1
        # Distinguish every slot at the whole-sentence boundary without expanding a large witness domain.
        bound={'eihf':{(practice,inquiry,point)},'eihh':{(inquiry,point)},'eisdq':rows['eisdq'],'eisdr':rows['eisdr']}
        m.update({n:relation(rs) for n,rs in bound.items()})
        assert run('eihj',[],m,point=point,mode='bound');count+=1
        for name in ('eihf','eihh','eisdq'):
            for row in bound[name]:
                for slot in range(len(row)):
                    bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                    assert not run('eihj',[],m|{name:relation((bound[name]-{row})|{bad})},point=point,mode='bound');count+=1
    m,rows=model()
    assert not run('eihj',[],m|{'eisdn':relation({('a','eiha','a')})});count+=1
    # The anaphoric circumstance is the same first-sentence content, not merely a named quotation.
    assert not run('eihj',[],m|{'eisdg':relation(set())});count+=1
    return dict(cases=count,native_sentence_composition=True,same_practice_inquiry_and_context=True,same_preceding_circumstance_retained=True,small_distinguishing_domain=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==219
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216],[217])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert ds['eihk']['body']['force']=='assert'
    assert {'eiha','eie6','eigy','eibf','eibs','eico','eiag'}<=set(ds)
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    count=0;expected={'eir3':{('b','b','a','eihk','a')},'ue':{('a','b','a')}}
    for path in (CORE,FULL):
        p=parse(read(path));p['statements']=p['statements'][-1:]
        for first,second in product((False,True),repeat=2):
            m=base()|{n:relation(rs if on else set()) for (n,rs),on in zip(expected.items(),(first,second))}
            assert evaluate(p,m)==(first and second);count+=1
        m=base()|{n:relation(rs) for n,rs in expected.items()}
        for name,rs in expected.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not evaluate(p,m|{name:relation({bad})});count+=1
        assert not evaluate(p,base()|dict(eisds=lambda:'a',eir3=lambda *xs:True,ue=lambda *xs:True));count+=1
    unit=json.loads(read(INVENTORY))['units'][4];reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256']);validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    assert reading['source']==unit['text'][261:423] and reading['source_nonblank_characters']==142 and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=218,presentation_cases=count,prior_reviews_preserved=True,source_range=[261,423])

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_kinematic_difficulties import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(consideration=consideration_checks(),difficulties=difficulty_checks(),causes=cause_checks(),sentence=sentence_checks(),structure=structure_checks())
    unit=json.loads(read(INVENTORY))['units'][4]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,READING,INVENTORY,*PRIORS,
        'reports/kinematic-foundation-v1.json','scripts/compose_kinematic_difficulties.py','scripts/check_kinematic_difficulties.py','scripts/review_kinematic_difficulties.py','tests/test_kinematic_difficulties.py',
        'scripts/check_kinematic_foundation.py','scripts/compose_kinematic_foundation.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/check_coordinate_correspondence.py'}
    return dict(status='kinematic_difficulties_sentence_checked_under_explicit_reading',document=FULL,**results,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[261,423],source=unit['text'][261:423],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
