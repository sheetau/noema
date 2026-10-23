"""Check nonfactive relational judgment accounts and universal consideration."""
from copy import deepcopy
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
from scripts.check_motion_time_description import PRIORS
from scripts.compose_temporal_judgments import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/temporal-judgments-v1.md';SOURCE='data/einstein-time-continuation-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/temporal-judgments-reading-v1.json'
EARLIER_READING='data/motion-time-description-reading-v1.json'
DOMAIN=('a','b');POINTS=('now','other')

def forbidden(*args):raise ValueError('Unknown temporal-judgment input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,boundaries=()):
    root='eiiu' if name=='component_body' else name
    doc=extract_document(parse(read(CORE)),roots=[root],statement_indices=[]).document;abstract(doc,set(boundaries))
    if name=='component_body':
        d=deepcopy(next(d for d in doc['declarations'] if d['name']==root));d['name']='jtjbody';bound=[];node=d['body']
        while node['kind']=='exists':bound.append(dict(name=node['variable'],sort=node['sort']));node=node['body']
        assert len(bound)==4 and all(p['sort']=='individual' for p in bound)
        d['parameters']+=bound;d['body']=node;doc['declarations'].append(d);name=d['name']
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtj'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtjcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jtjcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,values,m,boundaries=(),context='now'):
    doc,slots=fixture(name,tuple(boundaries));assert len(values)==len(slots)
    return evaluate(doc,m|{'jtjcontext':lambda:context}|{n:(lambda x=x:x) for n,x in zip(slots,values)})

@lru_cache(None)
def component_checks():
    count=0
    for first,second,frame,unit in product(DOMAIN,repeat=4):
        row=('a',first,second,frame,unit,'eihm','now');model={'eisez':relation({row})}
        assert run('eiiu',['a','now'],model);count+=1
        values=['a','now',first,second,frame,unit]
        assert run('component_body',values,model);count+=1
        for slot in range(6):
            bad=list(values);bad[slot]='other' if slot==1 else 'b' if values[slot]=='a' else 'a'
            assert not run('component_body',bad,model);count+=1
        bad=list(row);bad[5]='sek';assert not run('eiiu',['a','now'],{'eisez':relation({tuple(bad)})});count+=1
    # Quoted relation classification must not evaluate any physical simultaneity predicate.
    row=('a','a','b','a','b','eihm','now')
    for model in ({'eisez':relation({row})},{'eisez':relation({row}),'eihm':forbidden,'zbe':forbidden,'qo':forbidden,'ce':forbidden}):
        assert run('eiiu',['a','now'],model);count+=1
    try:run('eiiu',['a','now'],{'eisez':forbidden})
    except ValueError as e:assert 'Unknown temporal-judgment' in str(e)
    else:raise AssertionError('Unknown component accepted')
    return dict(cases=count,same_relation_and_five_arguments=True,relation_classification_not_physical_truth=True,unknown_mapping_rejected=True)

@lru_cache(None)
def account_checks():
    count=0
    for selected_mask,typed_mask in product(range(4),repeat=2):
        selected={p for i,p in enumerate(DOMAIN) if selected_mask&(1<<i)};typed={p for i,p in enumerate(DOMAIN) if typed_mask&(1<<i)}
        model={'eisey':relation({('a',p,'now') for p in selected}),'eiiu':relation({(p,'now') for p in typed})}
        assert run('eiiv',['a','now'],model,('eiiu',))==bool(selected and selected<=typed);count+=1
    for judgment,account,document,part in product(DOMAIN,repeat=4):
        rows={'eisex':{(judgment,account,document,'now')},'eisey':{(account,part,'now')},'eisez':{(part,'a','b','a','b','eihm','now')}}
        model={n:relation(rs) for n,rs in rows.items()}
        assert run('eiiw',[judgment,document,'now'],model);count+=1
        # Mutate the judgment/account binding and all selection slots; a different account cannot rescue it.
        for n in ('eisex','eisey'):
            row=next(iter(rows[n]))
            for slot in range(len(row)):
                changed=tuple(('other' if x=='now' else 'b' if x=='a' else 'a') if i==slot else x for i,x in enumerate(row))
                assert not run('eiiw',[judgment,document,'now'],model|{n:relation({changed})}),(n,slot);count+=1
    # A second selected but untyped item cannot be omitted from the account.
    rows={'eisex':{('a','a','b','now')},'eisey':{('a','a','now'),('a','b','now')},'eisez':{('a','a','b','a','b','eihm','now')}}
    model={n:relation(rs) for n,rs in rows.items()};assert not run('eiiw',['a','b','now'],model);count+=1
    for n in model:
        try:run('eiiw',['a','b','now'],model|{n:forbidden})
        except ValueError as e:assert 'Unknown temporal-judgment' in str(e)
        else:raise AssertionError('Unknown account accepted')
    return dict(cases=count,nonempty_all_relation_items=True,same_judgment_account_document=True,untyped_second_item_not_dropped=True,unknown_inputs_rejected=True)

@lru_cache(None)
def universal_scope_checks():
    count=0
    for scope_mask,time_mask,account_mask in product(range(4),repeat=3):
        scope={p for i,p in enumerate(DOMAIN) if scope_mask&(1<<i)};temporal={p for i,p in enumerate(DOMAIN) if time_mask&(1<<i)};explained={p for i,p in enumerate(DOMAIN) if account_mask&(1<<i)}
        m={'rd':lambda:'a','eirf':lambda:'b','eisev':relation({(p,'a','b','now') for p in scope}),'eisew':relation({(p,'b','now') for p in temporal}),'eiiw':relation({(p,'b','now') for p in explained})}
        assert run('eiix',[],m,('eiiw',))==((scope&temporal)<=explained);count+=1
    rows={'eisev':{(p,'a','b','now') for p in DOMAIN},'eisew':{(p,'b','now') for p in DOMAIN},'eiiw':{(p,'b','now') for p in DOMAIN}}
    base={'rd':lambda:'a','eirf':lambda:'b'};m=base|{n:relation(rs) for n,rs in rows.items()}
    for row in rows['eiiw']:
        for slot in range(3):
            bad=tuple(('other' if x=='now' else 'b' if x=='a' else 'a') if i==slot else x for i,x in enumerate(row))
            assert not run('eiix',[],m|{'eiiw':relation((rows['eiiw']-{row})|{bad})},('eiiw',));count+=1
    return dict(cases=count,all_temporally_relevant_judgments=True,non_temporal_judgments_not_forced=True,no_actual_judgment_existence_added=True,same_document_and_context=True)

def setup():
    rows={'eisev':{('a','b','a','now')},'eisew':{('a','a','now')},'eisex':{('a','b','a','now')},'eisey':{('b','a','now')},'eisez':{('a','a','b','a','b','eihm','now')},'eise2':{('b','eiix','a','now')}}
    base={'rd':lambda:'b','eirf':lambda:'a'}
    return base|{n:relation(rs) for n,rs in rows.items()},rows

@lru_cache(None)
def consideration_checks():
    m,rows=setup();count=0
    for account,obligation in product((False,True),repeat=2):
        assert run('eiiy',[],m|{'eisex':relation(rows['eisex'] if account else set()),'eise2':relation(rows['eise2'] if obligation else set())})==(account and obligation);count+=1
    for n in ('eisex','eisey','eise2'):
        row=next(iter(rows[n]))
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not run('eiiy',[],m|{n:relation({bad})});count+=1
    # Same-shape relation for a different meaning is not the promised simultaneity account.
    row=next(iter(rows['eisez']));bad=list(row);bad[5]='eiiq';assert not run('eiiy',[],m|{'eisez':relation({tuple(bad)})});count+=1
    for n in rows:
        try:run('eiiy',[],m|{n:forbidden})
        except ValueError as e:assert 'Unknown temporal-judgment' in str(e)
        else:raise AssertionError('Unknown sentence relation accepted')
    # No implementation of actual consideration or the truth of individual judgments is queried.
    assert run('eiiy',[],m|{'eisdn':forbidden,'eihm':forbidden,'ce':forbidden,'zbe':forbidden});count+=1
    return dict(cases=count,native_whole_sentence_composition=True,property_and_consideration_requirement_both_kept=True,same_quoted_property_required=True,actual_consideration_and_physical_truth_not_inferred=True,unknown_inputs_rejected=len(rows))

@lru_cache(None)
def presentation_checks():
    count=0
    rows={'eir3':{('a','b','a','eiiz','now')},'ue':{('b','a','now')}}
    base={'eise3':lambda:'a','eiseu':lambda:'b','rd':lambda:'b','eirf':lambda:'a','ri':lambda:'now'}
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=base|{n:relation(rs) for n,rs in rows.items()}
        for bits in product((False,True),repeat=2):
            assert evaluate(doc,m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
        for n,rs in rows.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not evaluate(doc,m|{n:relation({bad})});count+=1
        assert not evaluate(doc,m|{'eise3':lambda:'b','eir3':lambda *xs:True,'ue':lambda *xs:True});count+=1
    ds={d['name']:d for d in parse(read(CORE))['declarations']};assert ds['eiiz']['body']['force']=='assert'
    return dict(cases=count,same_author_document_and_order=True,quoted_content_not_executed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==227
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216],[217,218],[219],[220],[221,222],[223])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    prior=json.loads(read(EARLIER_READING));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[224,225])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256']);u=json.loads(read(INVENTORY))['units'][9]
    segment=source['segments'][0];assert segment['unit']==u['id'] and segment['range']==[338,481] and segment['text']==u['text'][338:481] and segment['unit_sha256']==u['text_sha256']
    reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256']);assert reading['selection']==selection_binding(new,[INDEX]) and reading['source_nonblank_characters']==123
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=226,prior_reviews_and_two_sentences_preserved=True,whole_paragraph_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_temporal_judgments import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('components',component_checks),('accounts',account_checks),('scope',universal_scope_checks),('consideration',consideration_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][9]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,EARLIER_READING,*PRIORS,'scripts/compose_temporal_judgments.py','scripts/check_temporal_judgments.py','scripts/review_temporal_judgments.py','tests/test_temporal_judgments.py','scripts/check_motion_time_description.py','scripts/compose_motion_time_description.py','scripts/check_coordinate_correspondence.py','scripts/compose_kinematics_headings.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='temporal_judgments_and_required_consideration_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[338,481],source=u['text'][338:481],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['第四文の列車・時計の引用例','脚注u0279と本文の参照','段落全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
