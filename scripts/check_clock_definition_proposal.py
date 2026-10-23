"""Check shared rule arguments, all difficulties and nested nonfactive scopes."""
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
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM
from scripts.compose_clock_definition_proposal import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/clock-definition-proposal-v1.md';SOURCE='data/einstein-clock-definition-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/clock-definition-proposal-reading-v1.json'
DOMAIN=('proposal','author','task','clock','hand','frame','unit','paper','d1','d2','display','node','prior','other')
POINTS=('now','view','seen','r1','r2','other')
BASE=['author','clock','hand','frame','unit','r1']
PARAMS=['proposal','author','task','clock','hand','frame','unit','paper']

def forbidden(*args):raise ValueError('Unknown clock-definition-proposal input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,native_real=False):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if not native_real:abstract(doc,NUM)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jcd'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jcdcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jcdcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,args,m,context='now',native_real=False):
    doc,slots=fixture(name,native_real);assert len(args)==len(slots)
    return evaluate(doc,m|{'jcdcontext':lambda:context}|{n:(lambda x=x:x) for n,x in zip(slots,args)})

def references():
    return {n:(lambda x=x:x) for n,x in zip(('eisf5','rd','eisf6','eisf7','eisga','ra','eisgb','eirf','eisgc','eisfm'),PARAMS+['node','prior'])}|{'ri':lambda:'now'}

def rows():
    return {'ca':{('clock',)},'ci':{('unit',)},'va':{('frame',)},'eisdf':{('clock','r1')},'eise6':{('clock','author','r1')},'eise7':{('hand','clock','r1')},
        'eisdu':{('task','r1')},'eisfw':{('task','paper','r1')},'eisfx':{tuple(PARAMS+['eiji','r1'])},
        'eisfy':{(d,'task','paper','seen') for d in ('d1','d2')},'eisfz':{('proposal',d,'paper','seen','r1') for d in ('d1','d2')},
        'eisf2':{('proposal','task','paper','seen','r1')},'eisf3':{('eijm','paper','now','view')},'eisf4':{('eijm','paper','view','seen')}}

def setup():
    rs=rows();return references()|{n:relation(r) for n,r in rs.items()},rs

def unknown_rejected(name,args,m,symbols,context='now'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},context)
        except ValueError as e:assert 'Unknown clock-definition-proposal' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))

@lru_cache(None)
def clock_checks():
    count=0;m,rs=setup();cuts,arith=arithmetic();m|=arith;r=cuts.read
    m|={'eisfc':lambda e,h,c,x,s:(e,h,c,r(x),s)==('display','hand','clock',Q(3,2),'r1'),'ce':lambda c,e,f,u,x:(c,e,f,u,r(x))==('clock','display','frame','unit',Q(3,2))}
    assert run('eijh',BASE,m);count+=1
    for i in range(len(BASE)):
        a=BASE.copy();a[i]='other';assert not run('eijh',a,m);count+=1
    for symbol in ('ca','ci','va','eisdf','eise6','eise7'):
        row=next(iter(rs[symbol]))
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eijh',BASE,m|{symbol:relation({bad})});count+=1
    for actual,indicated,clock_reading in product((Q(3,2),Q(8)),repeat=3):
        mm=m|{'eisfc':lambda e,h,c,x,s,mark=indicated:(e,h,c,r(x),s)==('display','hand','clock',mark,'r1'),'ce':lambda c,e,f,u,x,mark=clock_reading:(c,e,f,u,r(x))==('clock','display','frame','unit',mark)}
        assert run('eiji',BASE+['display',cuts.make(actual)],mm)==(actual==indicated==clock_reading);count+=1
    args=BASE+['display',cuts.make(Q(3,2))]
    for i in range(7):
        a=args.copy();a[i]='other';assert not run('eiji',a,m);count+=1
    assert not run('eiji',args,m|{'ba':lambda *xs:False});count+=1
    assert run('eiji',args,m|{n:forbidden for n in ('cc','eisfa','eisfb','eihm')});count+=1
    unknown_rejected('eiji',args,m,('eisdf','eise6','eise7','eisfc','ce','ba'))
    try:run('eiji',args,m,native_real=True)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real validity silently sampled')
    return dict(cases=count,same_clock_hand_display_frame_unit_and_reading=True,no_seven_train_stationarity_or_remote_synchronization_added=True,full_real_validity_not_sampled=True,unknown_inputs_rejected=True)

@lru_cache(None)
def proposal_checks():
    m,rs=setup();count=0;args=PARAMS+['r1']
    assert run('eijj',args,m);count+=1
    for i in range(len(args)):
        a=args.copy();a[i]='other';assert not run('eijj',a,m);count+=1
    for symbol in ('eisdu','eisfw','eisfx'):
        row=next(iter(rs[symbol]))
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eijj',args,m|{symbol:relation({bad})});count+=1
    assert run('eijj',args,m|{'eisfc':forbidden,'ce':forbidden,'ba':forbidden});count+=1
    unknown_rejected('eijj',args,m,('eisdu','eisfw','eisfx'))
    return dict(cases=count,definition_task_and_same_clock_rule_bound=True,rule_is_quoted_without_asserting_universal_applicability=True)

@lru_cache(None)
def difficulty_checks():
    m,rs=setup();count=0;args=['proposal','task','paper','seen','r1']
    for d1,d2,solved1,solved2 in product((False,True),repeat=4):
        scope={(d,'task','paper','seen') for d,on in (('d1',d1),('d2',d2)) if on}
        done={('proposal',d,'paper','seen','r1') for d,on in (('d1',solved1),('d2',solved2)) if on}
        assert run('eijk',args,m|{'eisfy':relation(scope),'eisfz':relation(done)})==((d1 or d2) and (not d1 or solved1) and (not d2 or solved2));count+=1
    for symbol in ('eisfy','eisfz'):
        for row in rs[symbol]:
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                # Altering membership may legitimately remove a difficulty; use a new unresolved member to test that no member is ignored.
                if symbol=='eisfy':continue
                assert not run('eijk',args,m|{symbol:relation((rs[symbol]-{row})|{bad})});count+=1
    assert not run('eijk',args,m|{'eisfy':relation(rs['eisfy']|{('other','task','paper','seen')})});count+=1
    for i in range(len(args)):
        a=args.copy();a[i]='other';assert not run('eijk',a,m);count+=1
    for i in range(1,4):
        bad={tuple('other' if j==i else x for j,x in enumerate(row)) for row in rs['eisfy']}
        assert not run('eijk',args,m|{'eisfy':relation(bad)});count+=1
    unknown_rejected('eijk',args,m,('eisfy','eisfz'))
    return dict(cases=count,all_difficulties_in_fixed_nonempty_scope=True,same_proposal_reference_and_single_result=True,unresolved_extra_difficulty_rejected=True)

@lru_cache(None)
def modality_checks():
    m,rs=setup();count=0
    for name,args,context in (('eijl',PARAMS+['seen'],'now'),('eijm',[],'seen'),('eijn',['paper','view'],'now'),('eijo',[],'now')):
        assert run(name,args,m,context);count+=1
    assert not run('eijm',[],m,'now');count+=1
    # A genuine successful alternative is enough; no certainty or actual adoption is added.
    assert run('eijo',[],m|{'eisf2':relation(rs['eisf2']|{('proposal','task','paper','seen','r2')})});count+=1
    # Separate successes for separate difficulties cannot masquerade as one possible full solution.
    split={('proposal','d1','paper','seen','r1'),('proposal','d2','paper','seen','r2')}
    mm=m|{'eisf2':relation(rs['eisf2']|{('proposal','task','paper','seen','r2')}),'eisfz':relation(split)}
    assert not run('eijo',[],mm);count+=1
    # One successful appearance candidate does not excuse another failing candidate.
    assert not run('eijo',[],m|{'eisf4':relation(rs['eisf4']|{('eijm','paper','view','other')})});count+=1
    for symbol in ('eisf2','eisf3','eisf4'):
        assert not run('eijo',[],m|{symbol:relation(set())});count+=1
        row=next(iter(rs[symbol]))
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row))
            assert not run('eijo',[],m|{symbol:relation({bad})}),(symbol,i);count+=1
    for symbol in ('eisf5','rd','eisf6','eisf7','eisga','ra','eisgb','eirf'):
        assert not run('eijo',[],m|{symbol:lambda:'other'});count+=1
    # Appearance is not necessarily false: make the same success available at the actual reference too.
    extra={'eisf2':rs['eisf2']|{('proposal','task','paper','now','r1')},'eisfy':rs['eisfy']|{(d,'task','paper','now') for d in ('d1','d2')},'eisfz':rs['eisfz']|{('proposal',d,'paper','now','r1') for d in ('d1','d2')}}
    actual=m|{n:relation(r) for n,r in extra.items()};assert run('eijo',[],actual) and run('eijm',[],actual,'now');count+=1
    unknown_rejected('eijo',[],m,('eisf2','eisf3','eisf4','eisfy','eisfz','eisfx'))
    return dict(cases=count,tentative_view_appearance_and_success_possibility_separated=True,actual_solution_not_required_or_denied=True,nonempty_appearance_scope_and_all_candidates=True,single_result_for_all_difficulties=True)

@lru_cache(None)
def presentation_checks():
    count=0;rs={'eir3':{('node','author','paper','eijp','now')},'ue':{('prior','node','now')}}
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(r) for n,r in rs.items()}
        for bits in product((False,True),repeat=2):
            assert evaluate(doc,m|{n:relation(r if on else set()) for (n,r),on in zip(rs.items(),bits)})==all(bits);count+=1
        for symbol,r in rs.items():
            row=next(iter(r))
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not evaluate(doc,m|{symbol:relation({bad})});count+=1
        assert not evaluate(doc,m|{'eisfm':lambda:'node','eir3':lambda *xs:True,'ue':lambda *xs:True});count+=1
        assert evaluate(doc,m|{n:forbidden for n in PRIMITIVES if PRIMITIVES[n][0]});count+=1
    ds={d['name']:d for d in parse(read(CORE))['declarations']};assert ds['eijp']['body']['force']=='assert'
    return dict(cases=count,attributed_tentative_content_not_executed=True,same_author_paper_and_main_text_order=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==230
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in (('data/einstein-time-paragraph-review-v1.json',[224,225,226,227]),('data/einstein-local-simultaneity-note-review-v1.json',[228])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256']);u=json.loads(read(INVENTORY))['units'][10];seg=source['segments'][0]
    assert seg['unit']==u['id'] and seg['range']==[0,200] and seg['text']==u['text'][:200] and seg['unit_sha256']==u['text_sha256'] and seg['nonblank_characters']==172
    reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256']);assert reading['selection']==selection_binding(new,[INDEX]) and reading['source_nonblank_characters']==172
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=229,prior_paragraph_and_note_bindings_preserved=True,whole_paragraph_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_clock_definition_proposal import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('clock',clock_checks),('proposal',proposal_checks),('difficulties',difficulty_checks),('modality',modality_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][10]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,'scripts/compose_clock_definition_proposal.py','scripts/check_clock_definition_proposal.py','scripts/review_clock_definition_proposal.py','tests/test_clock_definition_proposal.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py','data/einstein-time-paragraph-review-v1.json','data/einstein-local-simultaneity-note-review-v1.json'}
    return dict(status='tentative_clock_definition_proposal_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,200],source=u['text'][:200],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['第二文の局所的十分性と遠隔の課題','段落全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
