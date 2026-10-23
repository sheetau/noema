"""Check exact constitution, inherited native local valuation, and insertion."""
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
from scripts.check_local_clock_valuation import setup as local_setup,DOMAIN as LOCAL_DOMAIN
from scripts.compose_second_local_clock import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_second_local_clock import SOURCE,INVENTORY,DOC,source_record

READING='data/second-local-clock-reading-v1.json';PRIOR='data/local-clock-valuation-reading-v1.json'
DOMAIN=LOCAL_DOMAIN+('clocka','placea','taska','observera','handa')
POINTS=('now','possible','other')

def forbidden(*args):raise ValueError('Unknown second-local-clock input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries={'conditional':{'eiky','eild','eik6'},'native_local':{'eild'},'intention':set()}.get(mode,set())
    abstract(doc,NUM|boundaries)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jsc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jsccontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jsccontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m,domain=DOMAIN):
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(slots)==len(args)
    return evaluate(doc,m|{'jsccontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)

def reject_unknown(name,args,m,symbols,mode='native',domain=DOMAIN):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode,domain)
        except ValueError as e:assert 'Unknown second-local-clock' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))

@lru_cache(None)
def constitution_checks():
    domain=('a','b');slots=list(product(domain,repeat=3));count=0
    base={'ca':relation({('a',),('b',)}),'eisif':relation({('a','b','a','a','now')}),'eisig':relation({('a',f,'a','now') for f in domain})}
    for bits in product((False,True),repeat=8):
        attrib={(clock,feature,'a',val,'a','now') for (clock,feature,val),on in zip(slots,bits) if on}
        expected=all(bool({v for c,f,v in slots if c=='a' and f==feature and (c,f,'a',v,'a','now') in attrib}) and {v for c,f,v in slots if c=='a' and f==feature and (c,f,'a',v,'a','now') in attrib}=={v for c,f,v in slots if c=='b' and f==feature and (c,f,'a',v,'a','now') in attrib} for feature in domain)
        assert run('eild',['a','b','a','now'],base|{'eisih':relation(attrib)},domain=domain)==expected;count+=1
    attrib={(clock,feature,'a','a','a','now') for clock,feature in product(domain,repeat=2)}
    m=base|{'eisih':relation(attrib)}
    assert run('eild',['a','b','a','now'],m,domain=domain);count+=1
    for symbol in ('ca','eisif','eisig'):
        assert not run('eild',['a','b','a','now'],m|{symbol:relation(set())},domain=domain);count+=1
    # Mutate fixed roles independently of the two quantified feature/value domains.
    for i in range(5):
        row=('a','b','a','a','now');bad=tuple(('other' if j==4 else 'b') if i==j else x for j,x in enumerate(row))
        if bad==row:bad=tuple('a' if j==i else x for j,x in enumerate(row))
        assert not run('eild',['a','b','a','now'],m|{'eisif':relation({bad})},domain=domain);count+=1
    for i in (2,4,5):
        changed={tuple(('other' if i==5 else 'b') if j==i else x for j,x in enumerate(row)) for row in attrib}
        assert not run('eild',['a','b','a','now'],m|{'eisih':relation(changed)},domain=domain);count+=1
    reject_unknown('eild',['a','b','a','now'],m,('eisif','eisig','eisih'),domain=domain)
    return dict(cases=count,all_features_nonempty_exact_bidirectional_description_match=True,extra_or_missing_characteristics_rejected=True,comparison_scope_separate_from_agreement=True)

def references():
    names={'eisik':'clock','eisil':'observer','eisim':'hand','eisin':'task','zir':'place','eisib':'clocka','ziq':'placea','ra':'frame','rb':'unit','eirf':'paper','rd':'author','eisio':'node','eish2':'prior','eisie':'taska','eisic':'observera','eisid':'handa'}
    return {n:(lambda x=x:x) for n,x in names.items()}|{'ri':lambda:'now'}

@lru_cache(None)
def conditional_checks():
    rows={'eiky':{('clocka','placea','frame','now'),('clock','place','frame','now')},'eild':{('clock','clocka','paper','now')},'eik6':{('task','observer','clock','hand','place','frame','unit','paper','now')}}
    m=references()|{n:relation(rs) for n,rs in rows.items()};count=0
    for a,b,same,possible in product((False,True),repeat=4):
        locations={row for row in rows['eiky'] if (a if row[0]=='clocka' else b)}
        mm=m|{'eiky':relation(locations),'eild':relation(rows['eild'] if same else set()),'eik6':relation(rows['eik6'] if possible else set())}
        assert run('eilj',[],mm,'conditional')==((not(a and b and same)) or possible);count+=1
    # Evaluate the B possibility directly so a wrong referent cannot hide in a false premise.
    for n,rs in rows.items():
        name={'eiky':'eilf','eild':'eilg','eik6':'eili'}[n]
        row=next(r for r in rs if r[0]!='clocka')
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run(name,[],m|{n:relation({bad})},'conditional');count+=1
    assert run('eilh',[],m|{'eik6':relation({('taska','observera','clocka','handa','placea','frame','unit','paper','now')})},'conditional');count+=1
    reject_unknown('eilj',[],m,('eiky','eild','eik6'),'conditional')
    return dict(cases=count,same_A_clock_and_distinct_B_setting=True,added_constitution_is_antecedent_not_unconditional_fact=True,existing_local_possibility_reused=True)

@lru_cache(None)
def native_local_checks():
    cuts,m,rows,reads,marks,assigns,fields,candidates=local_setup();count=0
    rows['ca'].add(('clocka',));rows['cb'].add(('clocka','placea','frame'));rows['eisgf'].add(('clocka','placea','frame','now'))
    m|={n:relation(rs) for n,rs in rows.items()}
    for event in DOMAIN:
        for context in POINTS:
            fields.setdefault((event,'clock',context),('near','display'))
            candidates.setdefault((event,'clock','unit',context),next(iter(candidates.values())))
    m|=references()|{'eild':relation({('clock','clocka','paper','now')})}
    assert run('eili',[],m,'native_local');count+=1
    assert run('eilj',[],m,'native_local');count+=1
    # Keep both clock settings and construction matching true; break only one B observation.
    bad=m|{'eish3':relation(rows['eish3']-{('observer','event2','display','hand','clock','frame','possible')})}
    assert not run('eilj',[],bad,'native_local');count+=1
    assert run('eilj',[],m|{n:forbidden for n in ('qo','cc','eisg2','eisgu','eisgv')},'native_local');count+=1
    return dict(cases=count,native_B_clock_reading_and_all_event_method_executed=True,no_remote_synchrony_or_equal_initial_readings_added=True)

@lru_cache(None)
def intention_checks():
    m=references()|{'ug':relation({('node','author','eilg','node','now')}),'eiscf':relation({('author','eilk','paper','now')})};count=0
    for name,symbol,row in (('eilk','ug',('node','author','eilg','node','now')),('eill','eiscf',('author','eilk','paper','now'))):
        assert run(name,[],m);count+=1
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run(name,[],m|{symbol:relation({bad})});count+=1
    assert run('eill',[],m|{'ug':forbidden,'eisih':forbidden});count+=1
    for claim,intent in product((False,True),repeat=2):
        # Both parts of eilm execute, with its physical condition handled in the separate checks.
        mm=m|{'eiky':lambda *xs:True,'eild':lambda *xs:True,'eik6':lambda *xs:claim,'eiscf':relation({('author','eilk','paper','now')} if intent else set())}
        assert run('eilm',[],mm,'conditional')==(claim and intent);count+=1
    reject_unknown('eill',[],m,('eiscf',))
    return dict(cases=count,intention_targets_same_added_assumption=True,intention_does_not_execute_adoption_or_constitution=True)

@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('node','author','paper','eiln','now')},'eisij':{('node','author','eile','eilf','paper','now'),('node','author','eilh','eili','paper','now')},'eisii':{('node','author','eilj','eilg','eill','paper','now')},'ue':{('prior','node','now')}};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(rs) for n,rs in rows.items()}
        assert evaluate(doc,m);count+=1
        for name,rs in rows.items():
            for row in rs:
                assert not evaluate(doc,m|{name:relation(rs-{row})});count+=1
                for i in range(len(row)):
                    bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not evaluate(doc,m|{name:relation((rs-{row})|{bad})});count+=1
        assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{'eish2':lambda:'node'});count+=1
        assert evaluate(doc,m|{'ca':forbidden,'eisih':forbidden,'eiscf':forbidden});count+=1
    return dict(cases=count,both_additive_relations_and_parenthetical_intention_preserved=True,attribution_not_actual_constitution_test=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==236
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[234])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert source['segments'][0]['nonblank_characters']==234
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX]) and rec['source_nonblank_characters']==234
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=235,prior_sentence_binding_preserved=True,four_place_symbols_and_page_boundary_checked=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_second_local_clock import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('constitution',constitution_checks),('conditional',conditional_checks),('native_local',native_local_checks),('intention',intention_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][12]
    segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[252,560],source=u['text'][252:560],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]
    segments.extend(dict(unit=u['id'],unit_sha256=u['text_sha256'],math_id=m['id'],math_sha256=m['sha256'],definitions=['eilj'],status='explicit_interpretive_annotation') for m in source_record()['segments'][0]['math'])
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,PRIOR,'scripts/compose_second_local_clock.py','scripts/check_second_local_clock.py','scripts/review_second_local_clock.py','tests/test_second_local_clock.py','scripts/check_local_clock_valuation.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='second_local_clock_exact_constitution_and_parenthetical_qualification_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['第三文以降の共通時間・同期と段落全体の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
