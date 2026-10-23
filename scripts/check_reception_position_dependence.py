"""Check matched placements, native reception cases and empirical attribution."""
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
from scripts.check_material_relative_frame import NUM
from scripts.check_reception_time_alternative import setup as reception_setup,DOMAIN as OLD_DOMAIN
from scripts.compose_reception_position_dependence import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/reception-position-dependence-v1.md';SOURCE='data/einstein-reception-time-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/reception-position-dependence-reading-v1.json';PRIOR='data/reception-time-alternative-reading-v1.json'
DOMAIN=OLD_DOMAIN+('left','right','secondplace','secondframe','signal2','departure2','reception2','display2')
POINTS=('now','possible','other');CASE=['left','scheme','task','event','paper','now'];PAIR=['left','right','scheme','task','event','paper','now']

def forbidden(*args):raise ValueError('Unknown reception-position-dependence input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,(set() if mode=='real' else NUM-{'sca'})|{'pair':{'eikk'},'quantifier':{'eikl'},'claim':{'eikm'}}.get(mode,set()))
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrp'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrpcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jrpcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m,domain=DOMAIN):
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jrpcontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)

def reject_unknown(name,args,m,symbols,mode='native'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode)
        except ValueError as e:assert 'Unknown reception-position-dependence' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))

def setup(left=9,right=12):
    cuts,m,rows,reads,indications,assignments,record_fields,candidates=reception_setup();r=cuts.read
    mapping={'origin':'secondplace','frame':'secondframe','record':'record2','signal':'signal2','departure':'departure2','reception':'reception2','display':'display2','now':'possible'}
    transform=lambda row:tuple(mapping.get(x,x) for x in row)
    for name,rs in rows.items():rows[name]=rs|{transform(row) for row in rs}
    m|={n:relation(rs) for n,rs in rows.items()}
    old_reads=set(reads);reads.clear()
    reads.update(tuple(Q(left) if isinstance(x,Q) and x==9 else x for x in row) for row in old_reads)
    reads.update(transform(tuple(Q(right) if isinstance(x,Q) and x==9 else x for x in row)) for row in old_reads)
    for table in (indications,assignments):
        old=set(table);table.clear()
        table.update(tuple(Q(left) if isinstance(x,Q) else x for x in row) for row in old)
        table.update(transform(tuple(Q(right) if isinstance(x,Q) else x for x in row)) for row in old)
    record_fields['record2','possible']=transform(record_fields['record','now'])
    candidates['record','clock','unit','now']=Q(left);candidates['record2','clock','unit','possible']=Q(right)
    fields={(case,s):('record','observer','clock','hand','origin','frame','unit') for case in DOMAIN for s in POINTS}
    fields['right','now']=('record2','observer','clock','hand','secondplace','secondframe','unit')
    contexts={(case,s):'now' for case in DOMAIN for s in POINTS};contexts['right','now']='possible'
    def project(case,slot,ref):
        if (case,ref) not in fields or slot.denominator!=1 or not 1<=slot<=7:raise ValueError('Unknown reception-position-dependence field')
        return fields[case,ref][int(slot)-1]
    def context(case,ref):
        if (case,ref) not in contexts:raise ValueError('Unknown reception-position-dependence situation')
        return contexts[case,ref]
    extra={'eishh':{tuple(CASE),tuple(['right']+CASE[1:])},'eishk':{tuple(PAIR)}}
    m|={n:relation(rs) for n,rs in extra.items()};m|={'eishi':project,'eishj':context}
    return cuts,m,rows,extra,fields,contexts,candidates

@lru_cache(None)
def native_case_checks():
    _,m,rows,extra,fields,contexts,_=setup();count=0
    for case in ('left','right'):
        assert run('eikk',[case]+CASE[1:],m);count+=1
    for i in range(len(CASE)):
        bad=CASE.copy();bad[i]='other';assert not run('eikk',bad,m);count+=1
    for i in range(7):
        original=fields['left','now'];changed=list(original);changed[i]='other';fields['left','now']=tuple(changed)
        assert not run('eikk',CASE,m);count+=1;fields['left','now']=original
    for a,b in ((0,1),(1,2),(2,3),(4,5),(5,6)):
        original=fields['left','now'];changed=list(original);changed[a],changed[b]=changed[b],changed[a];fields['left','now']=tuple(changed)
        assert not run('eikk',CASE,m);count+=1;fields['left','now']=original
    contexts['left','now']='other';assert not run('eikk',CASE,m);count+=1;contexts['left','now']='now'
    for name in ('eisg3','eisgy','eisgm','eisca'):
        assert not run('eikk',CASE,m|{name:relation(set())});count+=1
    for i in range(len(CASE)):
        bad=tuple('other' if j==i else x for j,x in enumerate(CASE));assert not run('eikk',CASE,m|{'eishh':relation({bad})});count+=1
    reject_unknown('eikk',CASE,m,('eishh','eishi','eishj'))
    return dict(cases=count,original_reception_record_body_executed=True,all_seven_fields_and_case_context_bound=True,same_original_event_required=True,original_rule_and_vacuum_path_preserved=True)

@lru_cache(None)
def pair_checks():
    count=0
    for left,right in product((Q(0),Q(9),Q(12)),repeat=2):
        _,m,*_=setup(left,right)
        assert run('eikl',PAIR,m)==(left!=right);count+=1
    _,m,rows,extra,fields,contexts,_=setup()
    assert run('eikl',PAIR,m);count+=1
    for i in range(len(PAIR)):
        bad=PAIR.copy();bad[i]='other';assert not run('eikl',bad,m);count+=1
    for i in range(len(PAIR)):
        bad=tuple('other' if j==i else x for j,x in enumerate(PAIR));assert not run('eikl',PAIR,m|{'eishk':relation({bad})});count+=1
    # Independently check position and units even when both case bodies are granted.
    granted=m|{'eikk':relation({tuple(CASE),tuple(['right']+CASE[1:])})}
    original=fields['right','now']
    for i,new in ((4,'origin'),(6,'other')):
        changed=list(original);changed[i]=new;fields['right','now']=tuple(changed)
        assert not run('eikl',PAIR,granted,'pair');count+=1;fields['right','now']=original
    reject_unknown('eikl',PAIR,m,('eishk','eishi','eishj','bc'))
    try:run('eikl',PAIR,m,mode='real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real validity silently sampled')
    return dict(cases=count,different_physical_positions_and_same_unit=True,native_real_value_comparison_not_function_identity=True,initial_clock_offset_only_not_admissible=True,full_real_validation_not_sampled=True)

@lru_cache(None)
def witness_checks():
    domain=('a','b');count=0;tuples=list(product(domain,repeat=3))
    for bits in product((False,True),repeat=8):
        rows={(left,right,'a','a',event,'a','now') for (event,left,right),on in zip(tuples,bits) if on}
        assert run('eikm',['a','a','a','now'],{'eikl':relation(rows)},'quantifier',domain)==any(bits);count+=1
    row=('a','b','a','a','a','a','now');m={'eikl':relation({row})}
    for slot in (2,3,5,6):
        bad=tuple(('other' if slot==6 else 'b') if i==slot else x for i,x in enumerate(row))
        assert not run('eikm',['a','a','a','now'],{'eikl':relation({bad})},'quantifier',domain);count+=1
    return dict(cases=count,existence_of_one_matched_counterexample=True,not_every_pair_required_to_differ=True,quantifier_binding_checked_on_two_individuals=True,native_pair_body_checked_separately=True)

def references():
    return {n:(lambda x=x:x) for n,x in zip(('eisg7','eishe','eirf','rd','eishp','eishg'),('scheme','task','paper','author','node','prior'))}|{'ri':lambda:'now'}

@lru_cache(None)
def drawback_and_knowledge_checks():
    rows={'eikm':{('scheme','task','paper','now')},'eishl':{('scheme','eikn','paper','now')},'eishm':{('eikn','task','paper','now')},'eishn':{('author','eikn','paper','now')}}
    m=references()|{n:relation(rs) for n,rs in rows.items()};count=0
    for bits in product((False,True),repeat=4):
        assert run('eikp',[],m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)},'claim')==all(bits);count+=1
    for name,rs in rows.items():
        row=next(iter(rs))
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eikp',[],m|{name:relation({bad})},'claim');count+=1
    # Experience is about the same claim; its attribution alone does not evaluate it.
    assert run('eiko',[],m|{'eikm':forbidden},'claim');count+=1
    reject_unknown('eikp',[],m,tuple(rows),'claim')
    return dict(cases=count,actual_noninvariance_and_inherent_drawback_all_asserted=True,knowledge_from_experience_about_same_content=True,knowledge_attribution_not_an_experiment_by_the_interpreter=True)

@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('node','author','paper','eikq','now')},'zbc':{('node','author','eikh','eikp','task','now')},'eisho':{('node','author','eikn','eiko','paper','now')},'ue':{('prior','node','now')}};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(rs) for n,rs in rows.items()}
        for bits in product((False,True),repeat=4):
            assert evaluate(doc,m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
        for name,rs in rows.items():
            row=next(iter(rs))
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not evaluate(doc,m|{name:relation({bad})});count+=1
        assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{'eishg':lambda:'node'});count+=1
        assert evaluate(doc,m|{'eishk':forbidden,'eishn':forbidden,'ce':forbidden});count+=1
    return dict(cases=count,contrast_with_possible_adoption_not_its_retraction=True,empirical_knowledge_parenthetical_kept=True,attribution_does_not_execute_physical_comparison=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==233
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[231])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256']);u=json.loads(read(INVENTORY))['units'][11];seg=source['segments'][1]
    assert seg['unit']==u['id'] and seg['range']==[310,488] and seg['text']==u['text'][310:488] and seg['unit_sha256']==u['text_sha256'] and seg['nonblank_characters']==151
    reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256']);assert reading['selection']==selection_binding(new,[INDEX]) and reading['source_nonblank_characters']==151
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=232,first_sentence_binding_preserved=True,whole_paragraph_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_reception_position_dependence import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('native_cases',native_case_checks),('pair',pair_checks),('witness',witness_checks),('drawback_and_knowledge',drawback_and_knowledge_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][11]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,PRIOR,'scripts/compose_reception_position_dependence.py','scripts/check_reception_position_dependence.py','scripts/review_reception_position_dependence.py','tests/test_reception_position_dependence.py','scripts/check_reception_time_alternative.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='reception_assignment_position_dependence_and_empirical_knowledge_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[310,488],source=u['text'][310:488],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['第三文71文字のより実用的な取り決めへの導入','三文全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
