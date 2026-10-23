"""Check shared degrees, comparison strength, reasoning and nonfactive reference."""
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
from scripts.compose_practical_time_convention import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/practical-time-convention-v1.md';SOURCE='data/einstein-reception-time-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/practical-time-convention-reading-v1.json'
PRIORS=('data/reception-time-alternative-reading-v1.json','data/reception-position-dependence-reading-v1.json')
DOMAIN=('new','old','task','criterion','high','low','paper','author','argument','node','prior','begin','end','other')
PAIR=['new','old','task','criterion','high','low','paper','now']
COMMON=['new','old','task','criterion','paper','now']

def forbidden(*args):raise ValueError('Unknown practical-time-convention input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,{'quantifier':{'eiks'},'claim':{'eikt'}}.get(mode,set()))
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jpt'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jptcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jptcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m,domain=DOMAIN):
    return evaluate_document(doc,individuals=domain,situations=('now','other'),primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=100000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(slots)==len(args)
    return evaluate(doc,m|{'jptcontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)

def reject_unknown(name,args,m,symbols,mode='native'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode)
        except ValueError as e:assert 'Unknown practical-time-convention' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))

def comparisons():
    return {'eishu':{('new','task','criterion','high','paper','now'),('old','task','criterion','low','paper','now')},'eishv':{('high','low','criterion','now')},'eishw':{('high','low','criterion','now')}}

@lru_cache(None)
def comparison_checks():
    rows=comparisons();m={n:relation(rs) for n,rs in rows.items()};count=0
    for bits in product((False,True),repeat=4):
        a,b,c,d=bits
        vals={r for r in rows['eishu'] if (a if r[0]=='new' else b)}
        mm={'eishu':relation(vals),'eishv':relation(rows['eishv'] if c else set()),'eishw':relation(rows['eishw'] if d else set())}
        assert run('eiks',PAIR,mm)==all(bits);count+=1
    for i in range(len(PAIR)):
        bad=PAIR.copy();bad[i]='other';assert not run('eiks',bad,m);count+=1
    for n,rs in rows.items():
        for row in rs:
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not run('eiks',PAIR,m|{n:relation((rs-{row})|{bad})});count+=1
    equal=PAIR.copy();equal[4]=equal[5]
    assert not run('eiks',equal,{n:lambda *xs:True for n in rows});count+=1
    reverse=PAIR.copy();reverse[4],reverse[5]=reverse[5],reverse[4]
    assert not run('eiks',reverse,m);count+=1
    reject_unknown('eiks',PAIR,m,rows)
    # Native quantification executes both valuations and the strict/large comparison.
    assert run('eikt',COMMON,m);count+=1
    assert not run('eikt',COMMON,m|{'eishw':relation(set())});count+=1
    return dict(cases=count,same_task_criterion_document_and_context=True,strict_direction_and_large_gap_separate=True,native_existential_comparison_executed=True)

@lru_cache(None)
def quantifier_checks():
    domain=('a','b');count=0;pairs=list(product(domain,repeat=2))
    for bits in product((False,True),repeat=4):
        rows={('a','a','a','a',hi,lo,'a','now') for (hi,lo),on in zip(pairs,bits) if on}
        assert run('eikt',['a','a','a','a','a','now'],{'eiks':relation(rows)},'quantifier',domain)==any(bits);count+=1
    for slot in (0,1,2,3,6,7):
        row=['a','a','a','a','a','b','a','now'];row[slot]='other' if slot==7 else 'b'
        assert not run('eikt',['a','a','a','a','a','now'],{'eiks':relation({tuple(row)})},'quantifier',domain);count+=1
    return dict(cases=count,two_degree_witnesses_share_one_pair=True,small_domain_binding_check=True)

def references():
    return {n:(lambda x=x:x) for n,x in zip(('eishq','eisg7','eishe','eisht','eirf','rd','eishr','eishs','eishp','eish2','rj'),('new','old','task','criterion','paper','author','argument','node','prior','begin','end'))}|{'ri':lambda:'now'}

@lru_cache(None)
def content_checks():
    rows={'eishx':{('new','task','qu','end','paper','now')},'eikt':{tuple(COMMON)},'eishy':{('author','argument','new','task','paper','now')}}
    m=references()|{n:relation(rs) for n,rs in rows.items()};count=0
    for bits in product((False,True),repeat=3):
        assert run('eikv',[],m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)},'claim')==all(bits);count+=1
    for n,rs in rows.items():
        row=next(iter(rs))
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eikv',[],m|{n:relation({bad})},'claim');count+=1
    reject_unknown('eikv',[],m,rows,'claim')
    # Evaluation of the content retains the native two-degree comparison.
    native=m|{n:relation(rs) for n,rs in comparisons().items()}
    assert run('eikv',[],native);count+=1
    assert not run('eikv',[],native|{'eishv':relation(set())});count+=1
    assert run('eiku',[],m|{'ce':forbidden,'qo':forbidden,'ba':forbidden});count+=1
    return dict(cases=count,same_convention_task_and_reasoning=True,quoted_existing_assignment_rule_not_executed=True,native_comparison_inside_content=True)

@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('node','author','paper','eikw','now')},'eishz':{('node','author','argument','begin','end','paper','now')},'ue':{('prior','node','now'),('node','begin','now'),('begin','end','now')}};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(rs) for n,rs in rows.items()}
        assert evaluate(doc,m);count+=1
        for n,rs in rows.items():
            for row in rs:
                assert not evaluate(doc,m|{n:relation(rs-{row})});count+=1
                for i in range(len(row)):
                    bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not evaluate(doc,m|{n:relation((rs-{row})|{bad})});count+=1
        for name,replacement in (('eishp','node'),('eishs','begin'),('eish2','end')):
            assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{name:lambda r=replacement:r});count+=1
        assert evaluate(doc,m|{'eishy':forbidden,'eishx':forbidden,'eishu':forbidden,'ce':forbidden});count+=1
        for n in rows:
            try:evaluate(doc,m|{n:forbidden})
            except ValueError as e:assert 'Unknown practical-time-convention' in str(e)
            else:raise AssertionError(n)
    return dict(cases=count,forward_reference_and_order_bound=True,attribution_does_not_execute_following_argument=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==234
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,index in zip(PRIORS,(231,232)):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);assert selection_binding(new,[index])==rec['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256']);u=json.loads(read(INVENTORY))['units'][11];seg=source['segments'][2]
    assert seg['range']==[489,569] and seg['text']==u['text'][489:569] and seg['unit_sha256']==u['text_sha256'] and seg['nonblank_characters']==71
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX]) and rec['source_nonblank_characters']==71
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=233,prior_sentence_bindings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_practical_time_convention import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('comparison',comparison_checks),('quantifier',quantifier_checks),('content',content_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][11]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*PRIORS,'scripts/compose_practical_time_convention.py','scripts/check_practical_time_convention.py','scripts/review_practical_time_convention.py','tests/test_practical_time_convention.py','scripts/check_coordinate_correspondence.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='practical_comparison_and_forward_reasoning_reference_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[489,569],source=u['text'][489:569],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['三文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
