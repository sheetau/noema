"""Check universal scope, physical schema bindings and the explanatory sentence."""
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
from scripts.compose_material_body_motion import FIELDS
from scripts.compose_kinematic_foundation import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/kinematic-foundation-v1.md';SOURCE='data/einstein-kinematics-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/kinematic-foundation-reading-v1.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json','data/einstein-principles-paragraph-review-v1.json')
DOMAIN=('a','b')

def forbidden(*args):raise ValueError('Unknown kinematic-foundation input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode=='scope':abstract(doc,{'eig4','eig5','eig6','eig7'})
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jkf'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jkfpoint',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jkfpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,model,point='a',domain=DOMAIN):
    m=dict(model,jkfpoint=lambda:point)
    return evaluate_document(doc,individuals=domain,situations=DOMAIN,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,values,model,point='a',mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots)
    return evaluate(doc,model|{n:(lambda x=x:x) for n,x in zip(slots,values)},point,domain)

def base():return dict(rd=lambda:'b',eirf=lambda:'a',ri=lambda:'a',eisdc=lambda:'a',eisdl=lambda:'b')
def model(point='a',upcoming='a'):
    rows={
        'eiscm':{(t,'b',point) for t in DOMAIN},'eisa6':{('b','eibf','eibs','eico',point)},
        'eiscr':{(t,c,point) for t,c in product(DOMAIN,repeat=2)},
        'eisdg':{(c,'eigz','eig2','eig3',point) for c in DOMAIN},
        'eisdh':{('b','eigy',point)},'eisdi':{(t,'b',point) for t in DOMAIN},
        'eisdj':{(upcoming,'a','eigj',point)},'eisdk':{('a','eiha','eihb',point)},
    }
    return base()|{n:relation(rs) for n,rs in rows.items()},rows

@lru_cache(None)
def referent_checks():
    count=0
    for clock,calibrated in product((False,True),repeat=2):
        m={'ca':relation({('a',)} if clock else set()),'eisdf':relation({('a','a')} if calibrated else set())}
        assert run('eig2',['a','a'],m)==(clock and calibrated);count+=1
    for row in (('b','a'),('a','b')):
        assert not run('eig2',['a','a'],{'ca':lambda x:True,'eisdf':relation({row})});count+=1
    row=('a','b','eibf','eibs','eico','a')
    assert run('eig3',['a','a'],{'eisc3':relation({row})});count+=1
    for slot in range(len(row)):
        bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
        assert not run('eig3',['a','a'],{'eisc3':relation({bad})});count+=1
    # Neither synchrony nor a currently evaluated full rigid history is needed to classify a quoted schema.
    for name,values,primitive in (('eig2',['a','a'],'ca'),('eig2',['a','a'],'eisdf'),('eig3',['a','a'],'eisc3')):
        m={'ca':lambda x:True,'eisdf':lambda *x:True,'eisc3':lambda *x:True}
        try:run(name,values,m|{primitive:forbidden})
        except ValueError as e:assert 'Unknown kinematic-foundation' in str(e)
        else:raise AssertionError('Unknown physical referent accepted')
    ds={d['name']:d for d in parse(read(CORE))['declarations']};node=ds['eigz']['body'];bound=[]
    while node['kind']=='exists':bound.append((node['variable'],node['sort']));node=node['body']
    expected=[n for n,_ in FIELDS if n not in ('body','context')]
    assert len(bound)==len(expected)
    # Compact formatting alpha-renames binders; compare their binding positions and sorts.
    names={'body':ds['eigz']['parameters'][0]['name'],'context':ds['eigz']['parameters'][1]['name']}
    names.update({n:b for n,(b,_) in zip(expected,bound)})
    rigid_sorts={n:p['sort'] for (n,_),p in zip(FIELDS,ds['eigy']['parameters'])}
    assert [s for _,s in bound]==[rigid_sorts[n] for n in expected]
    assert node['kind']=='and'
    assert node['arguments'][0]==dict(kind='call',symbol='eigy',arguments=[dict(kind='variable',name=names[n]) for n,_ in FIELDS])
    assert node['arguments'][1]==dict(kind='call',symbol='eisde',arguments=[dict(kind='variable',name=names[n]) for n in ('body','frame','context')])
    try:run('eigz',['a','a'],{})
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full reference-body history finitely enumerated')
    return dict(cases=count,same_rigid_body_frame_and_history=True,clock_does_not_require_remote_synchrony=True,electromagnetic_process_not_only_light=True,full_real_history_domain_refused=True,unknown_inputs_rejected=3)

@lru_cache(None)
def claim_checks():
    count=0
    for members,mapped in product(product((False,True),repeat=2),repeat=2):
        claims={c for c,on in zip(DOMAIN,members) if on};physical={c for c,on in zip(DOMAIN,mapped) if on}
        m={'eiscr':relation({('a',c,'a') for c in claims}),'eisdg':relation({(c,'eigz','eig2','eig3','a') for c in physical})}
        assert run('eig5',['a','a'],m)==(claims<=physical);count+=1
    m,rows=model()
    # Mismatching any of the three types, the claim, or the situation loses one required interpretation.
    for row in rows['eisdg']:
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
            assert not run('eig5',['a','a'],m|{'eisdg':relation((rows['eisdg']-{row})|{bad})});count+=1
    # A newly admitted consequence must also be covered, not silently skipped.
    m['eiscr']=relation({('a',c,'a') for c in ('a','b','c')})
    assert not run('eig5',['a','a'],m,domain=('a','b','c'));count+=1
    for n in ('eiscr','eisdg'):
        try:run('eig5',['a','a'],m|{n:forbidden})
        except ValueError as e:assert 'Unknown kinematic-foundation' in str(e)
        else:raise AssertionError('Unknown complete consequence scope accepted')
    return dict(cases=count,all_claims_and_consequences=True,three_closed_types_and_same_context=True,unknown_inputs_rejected=2)

@lru_cache(None)
def scope_checks():
    count=0
    # Exhaust all two-theory membership, foundation and referent assignments, with either upcoming theory.
    for scope,foundations,referents in product(product((False,True),repeat=2),repeat=3):
        selected={x for x,on in zip(DOMAIN,scope) if on};based={x for x,on in zip(DOMAIN,foundations) if on};stated={x for x,on in zip(DOMAIN,referents) if on}
        for upcoming in DOMAIN:
            m=base()|{'eig4':relation({(x,'a') for x in selected}),'eig5':relation({(x,'a') for x in stated}),
                'eig6':relation({(x,'a') for x in based}),'eig7':relation({(upcoming,'a')} if upcoming in selected else set()),'eisdk':relation({('a','eiha','eihb','a')})}
            assert run('eiha',[],m,mode='scope')==(selected<=stated)
            assert run('eihb',[],m,mode='scope')==(upcoming in selected and selected<=based)
            assert run('eihc',[],m,mode='scope')==(upcoming in selected and selected<=based and selected<=stated);count+=3
    # An additional other electrodynamics cannot escape the universal comparison.
    m=base()|{'eig4':relation({(x,'a') for x in ('a','b','c')}),'eig6':relation({(x,'a') for x in DOMAIN}),'eig7':relation({('a','a')})}
    assert not run('eihb',[],m,mode='scope',domain=('a','b','c'));count+=1
    return dict(cases=count,every_other_electrodynamics=True,same_upcoming_theory_also_requires_foundation=True,full_scope_not_selected_successes=True,finite_cases_not_universal_physical_proof=True)

@lru_cache(None)
def sentence_checks():
    count=0
    for point,upcoming in product(DOMAIN,repeat=2):
        m,rows=model(point,upcoming);assert run('eihc',[],m,point=point);count+=1
        for name in ('eisa6','eisdg','eisdh','eisdi','eisdj','eisdk'):
            for row in rows[name]:
                for slot in range(len(row)):
                    bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                    assert not run('eihc',[],m|{name:relation((rows[name]-{row})|{bad})},point=point),(name,slot);count+=1
        # Reverse the explanatory direction while retaining both true contents.
        assert not run('eihc',[],m|{'eisdk':relation({('a','eihb','eiha',point)})},point=point);count+=1
    m,rows=model()
    assert not run('eig6',['a','a'],m|{'eisdi':relation({('a','a','a')})});count+=1
    # No theory other than the intended one can replace the upcoming project.
    assert not run('eig7',['b','a'],m);count+=1
    # A non-electrodynamic inquiry is outside the comparison, but cannot be the selected upcoming theory.
    assert not run('eihc',[],m|{'eiscm':relation({('b','b','a')})});count+=1
    unknown=0
    for name in ('eiscm','eisa6','eiscr','eisdg','eisdh','eisdi','eisdj','eisdk'):
        try:run('eihc',[],m|{name:forbidden})
        except ValueError as e:assert 'Unknown kinematic-foundation' in str(e)
        else:raise AssertionError('Unknown sentence input accepted')
        unknown+=1
    return dict(cases=count,native_sentence_composition=True,same_inquiry_and_project=True,both_contents_and_explanatory_direction=True,quoted_physical_schemas_not_executed=True,unknown_inputs_rejected=unknown)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==218
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert ds['eihd']['body']['force']=='assert'
    assert {'eigy','eiad','eigj','eie5','eisc3','eibf','eibs','eico','ca'}<=set(ds)
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    count=0;expected={'eir3':{('b','b','a','eihd','a')},'ue':{('a','b','a')}}
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
        assert not evaluate(p,base()|dict(eisdl=lambda:'a',eir3=lambda *xs:True,ue=lambda *xs:True));count+=1
    unit=json.loads(read(INVENTORY))['units'][4];reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256']);validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    assert reading['source']==unit['text'][0:260] and reading['source_nonblank_characters']==227 and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=217,presentation_cases=count,prior_reviews_preserved=True,source_range=[0,260],whole_paragraph_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_kinematic_foundation import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(referents=referent_checks(),claims=claim_checks(),scope=scope_checks(),sentence=sentence_checks(),structure=structure_checks())
    unit=json.loads(read(INVENTORY))['units'][4]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,READING,INVENTORY,*PRIORS,
        'reports/rigid-body-kinematics-v1.json','scripts/compose_kinematic_foundation.py','scripts/check_kinematic_foundation.py','scripts/review_kinematic_foundation.py','tests/test_kinematic_foundation.py',
        'scripts/compose_rigid_body_kinematics.py','scripts/compose_material_body_motion.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/check_coordinate_correspondence.py'}
    return dict(status='kinematic_foundation_sentence_checked_under_explicit_reading',document=FULL,**results,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,260],source=unit['text'][0:260],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
