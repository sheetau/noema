"""Check shared targets, prospective scope and only-apparent incompatibility."""
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import Content,DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.compose_two_postulates import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/two-postulates-v1.md';SOURCE='data/einstein-principles-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/two-postulates-reading-v1.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json','data/relativity-conjecture-reading-v1.json')
DOMAIN=('a','b','c');POINTS=('a','b')
def forbidden(*args):raise ValueError('Unknown two-postulate input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    names={'eifj','eify'}
    if mode=='appearance':names.add('eif5')
    abstract(doc,names)
    d=next(d for d in doc['declarations'] if d['name']==name)
    body=dict(kind='call',symbol=name,arguments=[])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtppoint',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jtppoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc

def evaluate(doc,model,point='a'):
    m=dict(model,jtppoint=lambda:point)
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,model,point='a',mode='native'):return evaluate(fixture(name,mode),model,point)
def base():return dict(rd=lambda:'c',eirf=lambda:'a',eiscl=lambda:'b',eiscg=lambda:'c',eisb4=lambda:'a',ri=lambda:'a')

@lru_cache(None)
def adoption_and_naming_checks():
    count=0
    for first,second in product((False,True),repeat=2):
        rows={('b','c',n,'a','a') for n,on in (('eifj',first),('eify',second)) if on}
        m=base()|{'ug':relation(rows),'eifj':forbidden,'eify':forbidden}
        assert run('eifz',m)==first and run('eif2',m)==second and run('eif3',m)==(first and second);count+=3
    rows={('b','c','eifj','a','a'),('b','c','eify','a','a')}
    for row in rows:
        for slot in range(len(row)):
            changed=tuple('wrong' if i==slot else x for i,x in enumerate(row))
            assert not run('eif3',base()|{'ug':relation((rows-{row})|{changed})});count+=1
    # The same witness must be both the subsequent scope and the name's scope.
    for future_bits,name_bits,point in product(product((False,True),repeat=3),product((False,True),repeat=3),POINTS):
        future={s for s,on in zip(DOMAIN,future_bits) if on};named={s for s,on in zip(DOMAIN,name_bits) if on}
        m=base()|dict(eisci=relation({(s,'a','b',point) for s in future}),eisch=relation({('c','eifj',s,point) for s in named}))
        assert run('eif4',m,point)==bool(future&named);count+=1
    for name,row in (('eisci',('b','a','b','a')),('eisch',('c','eifj','b','a'))):
        m=base()|dict(eisci=relation({('b','a','b','a')}),eisch=relation({('c','eifj','b','a')}))
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not run('eif4',m|{name:relation({bad})});count+=1
        try:run('eif4',m|{name:forbidden})
        except ValueError as e:assert 'Unknown two-postulate' in str(e)
        else:raise AssertionError('Unknown naming input accepted')
    return dict(cases=count,adopted_targets_not_executed=True,prospective_scope_bound_to_same_content=True,empty_or_disjoint_naming_scope_rejected=True,unknown_inputs_rejected=2)

@lru_cache(None)
def compatibility_checks():
    count=0;cells=list(product(POINTS,repeat=2))
    for first,second,mask in product(product((False,True),repeat=2),product((False,True),repeat=2),product((False,True),repeat=4)):
        allowed={x for x,on in zip(cells,mask) if on}
        m=dict(eifj=lambda:Content(POINTS,first),eify=lambda:Content(POINTS,second),eiscj=relation({('eifj','eify',r,s) for r,s in allowed}))
        for point in POINTS:
            expected=any((point,s) in allowed and first[i] and second[i] for i,s in enumerate(POINTS))
            assert run('eif5',m,point)==expected;assert run('eif6',m,point)==(not expected);count+=2
    m=dict(eifj=lambda:Content(POINTS,(False,True)),eify=lambda:Content(POINTS,(False,True)),eiscj=relation({('eifj','eify','a','b')}))
    assert run('eif5',m);count+=1  # No truth of either principle at the current point is required.
    for slot in range(4):
        row=('eifj','eify','a','b');bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
        assert not run('eif5',m|{'eiscj':relation({bad})});count+=1
    try:run('eif5',m|{'eiscj':forbidden})
    except ValueError as e:assert 'Unknown two-postulate' in str(e)
    else:raise AssertionError('Unknown admissibility treated as incompatibility')
    return dict(cases=count,native_sqh_shared_witness=True,same_two_contents_and_reference=True,current_truth_not_required=True,unknown_inputs_rejected=1)

def integrated_model():
    return base()|dict(eifj=lambda:Content(POINTS,(False,True)),eify=lambda:Content(POINTS,(False,True)),
        eisci=relation({('b','a','b','a')}),eisch=relation({('c','eifj','b','a')}),
        eiscf=relation({('c','eif3','a','a')}),eiscj=relation({('eifj','eify','a','b')}),
        eisck=relation({('eif6','a','b')}),ug=forbidden)

@lru_cache(None)
def appearance_and_intent_checks():
    count=0
    for compatibility,mask in product(product((False,True),repeat=2),product((False,True),repeat=2)):
        candidates={p for p,on in zip(POINTS,mask) if on}
        m=dict(eif5=lambda:Content(POINTS,compatibility),eisck=relation({('eif6','a',p) for p in candidates}))
        apparent=bool(candidates) and all(not compatibility[POINTS.index(p)] for p in candidates)
        assert run('eif7',m,mode='appearance')==apparent
        assert run('eigd',m,mode='appearance')==(apparent and compatibility[0]);count+=2
    m=integrated_model();assert run('eiga',m);count+=1
    # Outer intention quotes the joint adoption; neither ug nor current principle truth is demanded.
    for name,row in (('eiscf',('c','eif3','a','a')),('eisck',('eif6','a','b'))):
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not run('eiga',m|{name:relation({bad})});count+=1
    for name in ('eiscf','eisch','eisci','eiscj','eisck'):
        assert not run('eiga',m|{name:lambda *xs:False});count+=1
        try:run('eiga',m|{name:forbidden})
        except ValueError as e:assert 'Unknown two-postulate' in str(e)
        else:raise AssertionError('Unknown second-sentence input accepted')
    return dict(cases=count,nonempty_all_appearance_candidates=True,apparent_incompatibility_and_actual_compatibility=True,intention_not_completed_adoption=True,full_local_composition=True,unknown_inputs_rejected=5)

def presentation(bits=(True,)*5,bad=None,collision=False):
    node='a' if collision else 'b';m=base()|dict(eiscl=lambda:node)
    rows=[('eir3',(node,'c','a','eigb','a')),('eisb2',(node,'c','eifz','eif2','a','a')),
        ('eisa5',(node,'c','eifj','eif4','a')),('eisa5',(node,'c','eify','eigd','a')),('ue',('a',node,'a'))]
    selected={}
    for i,(name,row) in enumerate(rows):
        if bad and bad[0]==i:row=tuple('wrong' if j==bad[1] else x for j,x in enumerate(row))
        if bits[i]:selected.setdefault(name,set()).add(row)
    for name in ('eir3','eisb2','eisa5','ue'):m[name]=relation(selected.get(name,set()))
    return m

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==215
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    ann=load_annotations(ROOT,BASIS,ANNOTATIONS);assert ann.find('Prinzip der Relativität','de')['matches'][0]['symbol']=='eiscg'
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert ds['eigb']['body']['force']=='assert'
    assert {'eifj','eify','sqh','ug'}<=set(ds)
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    count=0
    for path in (CORE,FULL):
        p=parse(read(path));p['statements']=p['statements'][-1:]
        for bits in product((False,True),repeat=5):assert evaluate(p,presentation(bits))==all(bits);count+=1
        for i,arity in enumerate((5,6,5,5,3)):
            for slot in range(arity):assert not evaluate(p,presentation(bad=(i,slot)));count+=1
        assert not evaluate(p,presentation(collision=True));count+=1
    unit=json.loads(read(INVENTORY))['units'][3];reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256'])
    assert reading['source']==unit['text'][523:889] and reading['source_nonblank_characters']==320 and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=214,presentation_cases=count,prior_reviews_preserved=True,quoted_message_not_executed=True,source_range=[523,889])

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_two_postulates import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(adoption_and_naming=adoption_and_naming_checks(),compatibility=compatibility_checks(),appearance_and_intent=appearance_and_intent_checks(),structure=structure_checks())
    unit=json.loads(read(INVENTORY))['units'][3]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,READING,INVENTORY,*PRIORS,
        'reports/vacuum-light-postulate-v1.json','scripts/compose_two_postulates.py','scripts/check_two_postulates.py','scripts/review_two_postulates.py','tests/test_two_postulates.py',
        'scripts/compose_vacuum_light_postulate.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/check_coordinate_correspondence.py'}
    return dict(status='two_postulates_sentence_checked_under_explicit_reading',document=FULL,**results,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[523,889],source=unit['text'][523:889],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
