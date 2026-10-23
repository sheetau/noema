"""Check failed detection, nonfactive conjecture and the limited prior result."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.compose_relativity_conjecture import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build

DOC='docs/relativity-conjecture-v1.md';READING='data/relativity-conjecture-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
SOURCE='data/einstein-principles-source-reading-v1.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json')
DOMAIN=('a','b','c');CONTEXTS=('a','b')
def forbidden(*xs):raise ValueError('Unknown conjecture-sentence input')
def val(x):return json.loads(x.syntax)['symbol'] if hasattr(x,'syntax') else x
def relation(row,bit=True):return lambda *xs:bit and tuple(val(x) for x in xs)==row
def evaluate(doc,model):
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={d['name']:model.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=200000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def fixture(name,native=False):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if name=='eifr' and not native:abstract(doc,{'eifo','eifj'})
    doc['declarations'].append(dict(kind='primitive',name='jaapoint',parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=dict(kind='evaluate',content=dict(kind='call',symbol=name,arguments=[]),situation=dict(kind='call',symbol='jaapoint',arguments=[])))]
    return doc
def run(name,model,point='a',native=False):return evaluate(fixture(name,native),dict(model,jaapoint=lambda:point))

def evidence_model(examples=DOMAIN,similar=DOMAIN,attempts=DOMAIN,trying=DOMAIN,successful=(),point='a'):
    return dict(eirf=lambda:'a',eisac=lambda:'b',eisbt=lambda item,doc,ctx:item in examples and (doc,ctx)==('a',point),
        eisbs=lambda item,anchor,kind,ctx:item in similar and (anchor,val(kind),ctx)==('b','eiew',point),
        eisbu=lambda item,doc,ctx:item in attempts and (doc,ctx)==('a',point),
        eisbv=lambda item,goal,ctx:item in trying and (val(goal),ctx)==('eifl',point),
        eisbw=lambda item,goal,ctx:item in successful and (val(goal),ctx)==('eifl',point))

@lru_cache(None)
def grounds_checks():
    sets=[{x for x,on in zip(DOMAIN,bits) if on} for bits in product((False,True),repeat=3)];count=0
    for selected in sets:
        for similar in sets:
            assert run('eifm',evidence_model(examples=selected,similar=similar))==(len(selected)>=2 and selected<=similar);count+=1
    for selected in (set(),{'a'},{'a','b'},set(DOMAIN)):
        for trying,successful in product(sets,repeat=2):
            expected=len(selected)>=2 and selected<=trying and not selected&successful
            assert run('eifn',evidence_model(attempts=selected,trying=trying,successful=successful))==expected;count+=1
    # Same goal/anchor/schema/document/context, with no physical goal evaluation.
    expected={'eisbs':('a','b','eiew','a'),'eisbv':('a','eifl','a'),'eisbw':('a','eifl','a')}
    for name in ('eisbs','eisbv'):
        for slot in range(1,len(expected[name])):
            m=evidence_model();good=m[name]
            m[name]=lambda *xs,slot=slot,good=good:good(*xs) and val(xs[slot])=='wrong'
            assert not run('eifm' if name=='eisbs' else 'eifn',m);count+=1
    for point in CONTEXTS:
        m=evidence_model(point=point);assert run('eifo',m,point=point);assert not run('eifo',m,point='b' if point=='a' else 'a');count+=2
    for name,root in (('eisbt','eifm'),('eisbs','eifm'),('eisbu','eifn'),('eisbv','eifn'),('eisbw','eifn')):
        m=evidence_model();m[name]=forbidden
        try:run(root,m)
        except ValueError as e:assert 'Unknown conjecture-sentence' in str(e)
        else:raise AssertionError('Unknown evidence accepted')
    return dict(cases=count,unknown_inputs_rejected=5,plural_and_all_selected=True,failed_detection_not_negated_motion=True,quoted_goal_and_similarity_not_executed=True)

def epistemic_model(bits=(True,)*5,target=True):
    grounds,leads,conjecture,restricted,established=bits
    return dict(eirf=lambda:'a',eisbo=lambda:'c',eifo=lambda:Content(CONTEXTS,(grounds,grounds)),
        eifj=lambda:Content(CONTEXTS,(target,target)),eisbq=relation(('a','eifo','eifj','a'),leads),
        eisbr=relation(('a','eifj','a'),conjecture),eisbn=relation(('eifg','c',Fraction(1),'a'),restricted),
        eisbp=relation(('a','eifp','a'),established))

@lru_cache(None)
def epistemic_checks():
    count=0
    for bits in product((False,True),repeat=5):
        for target in (False,True):
            assert run('eifr',epistemic_model(bits,target))==all(bits);count+=1
    for name,row in {'eisbq':('a','eifo','eifj','a'),'eisbr':('a','eifj','a'),'eisbn':('eifg','c',Fraction(1),'a'),'eisbp':('a','eifp','a')}.items():
        for slot in range(len(row)):
            m=epistemic_model();m[name]=relation(tuple('wrong' if i==slot else x for i,x in enumerate(row)))
            assert not run('eifr',m);count+=1
        m=epistemic_model();m[name]=forbidden
        try:run('eifr',m)
        except ValueError as e:assert 'Unknown conjecture-sentence' in str(e)
        else:raise AssertionError('Unknown epistemic input accepted')
    m=epistemic_model();m['eifj']=forbidden;assert run('eifr',m);count+=1
    # All local bodies integrated: no conjecture/goal truth, sampled motion or law oracle.
    m=evidence_model()|epistemic_model();assert run('eifr',m,native=True);count+=1
    for change in (dict(examples=('a',)),dict(similar=('a',)),dict(attempts=('a',)),dict(trying=('a',)),dict(successful=('b',))):
        m=evidence_model(**change)|epistemic_model();assert not run('eifr',m,native=True);count+=1
    return dict(cases=count,unknown_inputs_rejected=4,conjecture_truth_independent=True,restricted_content_and_prior_establishment_both_required=True,native_ground_and_qualification_integration=True)

@lru_cache(None)
def restriction_and_motion_checks():
    count=0
    # Explicit finite interpretation examples, not an implementation of all physical expansions.
    for coeff in product((-1,0,1),repeat=3):
        def restricted(claim,parameter,order,point):
            assert (val(claim),parameter,point)==('eifg','c','a') or point=='b'
            return point=='a' and order.denominator==1 and order>=0 and all(c==0 for degree,c in enumerate(coeff) if degree<=order)
        assert run('eifp',dict(eisbo=lambda:'c',eisbn=restricted))==(coeff[0]==coeff[1]==0);count+=1
    for order,expected in ((0,True),(1,True),(2,False)):
        doc=deepcopy(fixture('eifp'));d=next(d for d in doc['declarations'] if d['name']=='eifp');d['body']['body']['arguments'][2]['numerator']=order
        fn=lambda claim,parameter,n,point:(val(claim),parameter,point)==('eifg','c','a') and n<2
        assert evaluate(doc,dict(jaapoint=lambda:'a',eisbo=lambda:'c',eisbn=fn))==expected;count+=1
    # Goal binding checked structurally across all nine existential parameters.
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};goal=ds['eifl']['body'];point=goal['variable'];body=goal['body'];quantified=[]
    while body['kind']=='exists':quantified.append((body['variable'],body['sort']));body=body['body']
    motion=ds['eiag']['parameters'];assert [t for n,t in quantified]==[p['sort'] for i,p in enumerate(motion) if i not in (0,2)]
    call=lambda n:dict(kind='call',symbol=n,arguments=[])
    variable=lambda n:dict(kind='variable',name=n)
    assert body['arguments'][0]==dict(kind='call',symbol='eisbz',arguments=[variable(quantified[0][0]),call('eisby'),variable(point)])
    expected=[call('eisbx'),variable(quantified[0][0]),variable(point)]+[variable(n) for n,t in quantified[1:]]
    assert body['arguments'][1]==dict(kind='call',symbol='eiag',arguments=expected)
    try:run('eifl',dict(eisbx=lambda:'a',eisby=lambda:'b',eisbz=lambda *xs:True))
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real/function motion goal sampled')
    return dict(coefficient_examples=count,higher_order_difference_allowed=True,coefficient_examples_are_primitive_interpretations=True,motion_existential_slots=len(quantified),same_earth_medium_frame_and_context=True,full_motion_domain_refused=True)

def presentation_model(bits=(True,)*5,bad=None,collision=False):
    node='b' if collision else 'c'
    m=dict(eisb4=lambda:node,rd=lambda:'b',eirf=lambda:'a',ri=lambda:'a',eisav=lambda:'b')
    expected={'eir3':(node,'b','a','eifs','a'),'eisb2':(node,'b','eift','eifu','a','a'),'eisb3':(node,'b','eifi','eifg','a','a'),'eisa5':(node,'b','eifg','eifq','a'),'ue':('b',node,'a')}
    for i,(name,row) in enumerate(expected.items()):
        if bad and bad[0]==name:row=tuple('wrong' if j==bad[1] else x for j,x in enumerate(row))
        m[name]=relation(row,bits[i])
    return m

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==214
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert ds['eifs']['body']['force']=='assert'
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    count=0
    for path in (CORE,FULL):
        p=parse(read(path));p['statements']=p['statements'][-1:]
        for bits in product((False,True),repeat=5):assert evaluate(p,presentation_model(bits))==all(bits);count+=1
        for name,arity in (('eir3',5),('eisb2',6),('eisb3',6),('eisa5',5),('ue',3)):
            for slot in range(arity):assert not evaluate(p,presentation_model(bad=(name,slot)));count+=1
        assert not evaluate(p,presentation_model(collision=True));count+=1
    unit=json.loads(read(INVENTORY))['units'][3];reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256'])
    assert reading['source']==unit['text'][:522] and reading['source_nonblank_characters']==452 and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=213,presentation_cases=count,prior_reviews_preserved=True,quoted_targets_not_executed=True,source_range=[0,522])

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_relativity_conjecture import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(grounds=grounds_checks(),epistemic=epistemic_checks(),restriction_and_motion=restriction_and_motion_checks(),structure=structure_checks())
    unit=json.loads(read(INVENTORY))['units'][3]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,READING,INVENTORY,*PRIORS,'reports/conjecture-laws-v1.json','scripts/compose_relativity_conjecture.py','scripts/check_relativity_conjecture.py','scripts/review_relativity_conjecture.py','tests/test_relativity_conjecture.py','scripts/compose_conjecture_laws.py','scripts/compose_material_body_motion.py','scripts/compose_apparent_asymmetry.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/check_coordinate_correspondence.py'}
    return dict(status='relativity_conjecture_sentence_checked_under_explicit_reading',document=FULL,**results,alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,522],source=unit['text'][:522],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
