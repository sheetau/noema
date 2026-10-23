"""Check sufficient premises, consequence consistency and shared construction witnesses."""
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
from scripts.compose_sufficient_postulates import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/sufficient-postulates-v1.md';SOURCE='data/einstein-principles-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/sufficient-postulates-reading-v1.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json','data/relativity-conjecture-reading-v1.json','data/two-postulates-reading-v1.json')
DOMAIN=('a','b');POINTS=DOMAIN
def forbidden(*args):raise ValueError('Unknown sufficient-postulate input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name]+(['eifj','eify'] if name=='eigh' else []),statement_indices=[]).document
    if mode=='bound':abstract(doc,{'eige','eigf','eigg','eigh'})
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        if isinstance(p['sort'],dict) and p['sort']['kind']=='description':
            args.append(dict(kind='quote',body=dict(kind='call',symbol='eifj' if i==1 else 'eify',arguments=[])));continue
        n='jsp'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jsppoint',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jsppoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,model,point='a',domain=DOMAIN):
    m=dict(model,jsppoint=lambda:point)
    return evaluate_document(doc,individuals=domain,situations=POINTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,values,model,point='a',mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(slots)==len(values)
    m=model|{n:(lambda x=x:x) for n,x in zip(slots,values)};return evaluate(doc,m,point,domain)
def base():return dict(rd=lambda:'b',eirf=lambda:'a',eisax=lambda:'b',eiscl=lambda:'a',eiscu=lambda:'b',ri=lambda:'a')

def model(route='a',basis='b',theory='a',inquiry='b',point='a'):
    rows={
        'eisco':{(route,basis,theory,point)},'eiscn':{(basis,'b','eiah',point)},
        'eiscm':{(theory,inquiry,point)},'eisa6':{(inquiry,'eibf','eibs','eico',point)},'eisa7':{(inquiry,'eiag',point)},
        'eiscr':{(theory,'a',point)},'eiscs':{('a','b',point),('b','a',point)},'eisct':{(theory,'a',point)},
        'eiscp':{(p,route,point) for p in DOMAIN},'eiscq':{('a','eifj',point),('b','eify',point)},
    }
    return base()|{n:relation(rs) for n,rs in rows.items()},rows

@lru_cache(None)
def premise_checks():
    count=0;cells=list(product(DOMAIN,('eifj','eify')))
    for mask,bits in product(product((False,True),repeat=2),product((False,True),repeat=4)):
        selected={p for p,on in zip(DOMAIN,mask) if on};mapping={x for x,on in zip(cells,bits) if on}
        m=base()|dict(eiscp=relation({(p,'a','a') for p in selected}),eiscq=relation({(p,c,'a') for p,c in mapping}))
        expected=any(l!=r and l in selected and r in selected and (l,'eifj') in mapping and (r,'eify') in mapping for l,r in product(DOMAIN,repeat=2)) and all(any((p,c) in mapping for c in ('eifj','eify')) for p in selected)
        assert run('eigh',['a','a'],m)==expected;count+=1
    m,_=model();m['eiscp']=relation({(p,'a','a') for p in ('a','b','c')})
    assert not run('eigh',['a','a'],m,domain=('a','b','c'));count+=1
    m['eiscq']=relation({('a','eifj','a'),('b','eify','a'),('c','eifj','a')})
    assert run('eigh',['a','a'],m,domain=('a','b','c'));count+=1  # Redundant records are allowed, not extra content.
    for name in ('eiscp','eiscq'):
        m,_=model()
        try:run('eigh',['a','a'],m|{name:forbidden})
        except ValueError as e:assert 'Unknown sufficient-postulate' in str(e)
        else:raise AssertionError('Unknown premise set treated as complete')
    return dict(cases=count,both_same_postulates_supplied=True,no_third_independent_physical_premise=True,redundancy_allowed_not_necessity_claim=True,unknown_inputs_rejected=2)

@lru_cache(None)
def consistency_checks():
    count=0
    for mask,opposite in product(product((False,True),repeat=2),(False,True)):
        claims={c for c,on in zip(DOMAIN,mask) if on}
        m=base()|dict(eiscr=relation({('a',c,'a') for c in claims}),eiscs=relation({('a','b','a'),('b','a','a')} if opposite else set()))
        assert run('eigg',['a','a'],m)==not_both(claims,opposite);count+=1
    # A contradiction in a different theory or under different conditions is not transferred.
    for other in (('b','a'),('a','b')):
        theory,point=other
        m=base()|dict(eiscr=relation({(theory,c,point) for c in DOMAIN}),eiscs=relation({('a','b',point),('b','a',point)}))
        assert run('eigg',['a','a'],m);assert not run('eigg',[theory,point],m);count+=2
    m,_=model()
    for name in ('eiscr','eiscs'):
        try:run('eigg',['a','a'],m|{name:forbidden})
        except ValueError as e:assert 'Unknown sufficient-postulate' in str(e)
        else:raise AssertionError('Unknown consequence input treated as no contradiction')
    return dict(cases=count,same_theory_and_conditions=True,all_logical_consequences_are_meaning_input=True,unknown_inputs_rejected=2)
def not_both(claims,opposite):return not (len(claims)==2 and opposite)

@lru_cache(None)
def construction_checks():
    count=0;m,rows=model();values=['a','b','a','a']
    assert run('eigi',values,m);assert run('eigj',[],m);count+=2
    # Native inquiry composition uses the same current, electric, magnetic and body-motion schemas.
    for name in ('eisco','eiscn','eiscm','eisa6','eisa7','eisct','eiscp','eiscq'):
        for row in rows[name]:
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not run('eigi',values,m|{name:relation((rows[name]-{row})|{bad})}),(name,slot);count+=1
        try:run('eigi',values,m|{name:forbidden})
        except ValueError as e:assert 'Unknown sufficient-postulate' in str(e)
        else:raise AssertionError('Unknown construction input accepted')
    for slot in range(len(values)):
        bad=list(values);bad[slot]='b' if values[slot]=='a' else 'a';assert not run('eigi',bad,m);count+=1
    # No compulsory contradiction may be omitted; simplicity cannot substitute for consistency.
    assert not run('eigi',values,m|{'eiscr':relation({('a',p,'a') for p in DOMAIN})});count+=1
    # Mixing individually suitable but different target theories or different inquiry witnesses fails.
    assert not run('eigi',values,m|{'eisct':relation({('b','a','a')})});count+=1
    assert not run('eigi',values,m|{'eisa7':relation({('a','eiag','a')})});count+=1
    return dict(cases=count,native_research_topic_and_premise_composition=True,same_rest_basis_route_and_target=True,rest_not_static_fields=True,quoted_physical_contents_not_executed=True,unknown_inputs_rejected=8)

@lru_cache(None)
def witness_checks():
    count=0
    for route,basis,theory,point in product(DOMAIN,repeat=4):
        rows={'eisco':{(route,basis,theory,point)},'eigf':{(basis,point)},'eige':{(theory,point)},'eigg':{(theory,point)},
            'eisct':{(theory,'a',point)},'eigh':{(route,'eifj','eify',point)}}
        m=base()|{n:relation(r) for n,r in rows.items()}
        assert run('eigj',[],m,point=point,mode='bound');count+=1
        for name,rs in rows.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                changed=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not run('eigj',[],m|{name:relation({changed})},point=point,mode='bound');count+=1
    return dict(cases=count,all_three_existential_slots_bound=True,no_separate_witnesses_for_target_qualities=True,small_distinguishing_domain=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==216
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213],[214])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert ds['eigk']['body']['force']=='assert'
    assert {'eifj','eify','eie6','eiah','eisax'}<=set(ds)
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    count=0;expected={'eir3':{('b','b','a','eigk','a')},'ue':{('a','b','a')}}
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
        # Even externally supplied presentation relations do not erase distinct textual nodes.
        assert not evaluate(p,base()|dict(eiscu=lambda:'a',eir3=lambda *xs:True,ue=lambda *xs:True));count+=1
    unit=json.loads(read(INVENTORY))['units'][3];reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256'])
    assert reading['source']==unit['text'][890:1081] and reading['source_nonblank_characters']==169 and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=215,presentation_cases=count,prior_reviews_preserved=True,source_range=[890,1081])

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_sufficient_postulates import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(premises=premise_checks(),consistency=consistency_checks(),construction=construction_checks(),witnesses=witness_checks(),structure=structure_checks())
    unit=json.loads(read(INVENTORY))['units'][3]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,READING,INVENTORY,*PRIORS,
        'reports/two-postulates-v1.json','scripts/compose_sufficient_postulates.py','scripts/check_sufficient_postulates.py','scripts/review_sufficient_postulates.py','tests/test_sufficient_postulates.py',
        'scripts/compose_two_postulates.py','scripts/compose_material_body_motion.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/check_coordinate_correspondence.py'}
    return dict(status='sufficient_postulates_sentence_checked_under_explicit_reading',document=FULL,**results,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[890,1081],source=unit['text'][890:1081],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
