"""Check stage scope, no further stipulation, and local-rule bindings."""
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
from scripts.compose_local_times_only import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_local_times_only import SOURCE,INVENTORY,DOC,source_record

READING='data/local-times-only-reading-v1.json'
PRIORS={234:'data/local-clock-valuation-reading-v1.json',235:'data/second-local-clock-reading-v1.json'}
POINTS=('now','other')


def forbidden(*args):raise ValueError('Unknown local-times-only input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def changed(row,i):return tuple(('other' if x!='other' else 'now') if j==i else x for j,x in enumerate(row))


@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries={'tasks':{'eilt','eilw'},'content':{'eily','eilz','eil2'}}.get(mode,set())
    abstract(doc,NUM|boundaries)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jlt'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jltcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jltcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m,domain=('a','b')):
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def run(name,args,m,mode='native',domain=('a','b')):
    doc,slots=fixture(name,mode);assert len(slots)==len(args)
    return evaluate(doc,m|{'jltcontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)


def reject_unknown(name,args,m,symbols,mode='native',domain=('a','b')):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode,domain)
        except ValueError as e:assert 'Unknown local-times-only' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))


@lru_cache(None)
def stage_checks():
    domain=('a','b','c');stage=['a','a','a','now'];count=0
    for bits in product((False,True),repeat=3):
        defined={(t,*stage) for t,on in zip(domain,bits) if on}
        m={'eisiq':relation(defined|{('c','a','b','a','now')})}
        assert run('eilq',['a','b']+stage,m,domain=domain)==(bits==(True,True,False));count+=1
    rows={('a',*stage),('b',*stage)};m={'eisiq':relation(rows)}
    assert not run('eilq',['a','a']+stage,m,domain=domain);count+=1
    # Same two conventions at another author/stage/document/context do not count here.
    for i in range(1,5):
        assert not run('eilq',['a','b']+stage,{'eisiq':relation({changed(r,i) for r in rows})},domain=domain);count+=1
    shared={('a','a','a','a','a','now'),('a','b','a','a','a','now')}
    for left,right,defined_now,defined_later in product((False,True),repeat=4):
        definitions=({('a',*stage)} if defined_now else set())|({('a','a','b','a','now')} if defined_later else set())
        places={r for r in shared if (left if r[1]=='a' else right)}
        mm={'eisiq':relation(definitions),'eisir':relation(places)}
        assert run('eils',['a','b','a','a']+stage,mm,domain=domain)==(not(left and right and defined_now));count+=1
    # Separate local tables never supply a single shared convention.
    mm=m|{'eisir':relation({('a','a','a','a','a','now'),('b','b','a','a','a','now')})}
    assert run('eils',['a','b','a','a']+stage,mm,domain=domain);count+=1
    assert not run('eilr',['a','a','a','a','a','a','now'],{'eisir':relation(shared)},domain=domain);count+=1
    for i in (2,3,4,5):
        assert not run('eilr',['a','a','b','a','a','a','now'],{'eisir':relation({changed(r,i) for r in shared})},domain=domain);count+=1
    reject_unknown('eilq',['a','b']+stage,m,('eisiq',),domain=domain)
    reject_unknown('eils',['a','b','a','a']+stage,mm,('eisiq','eisir'),domain=domain)
    return dict(cases=count,only_two_current_definitions_and_future_stage_separate=True,same_shared_convention_required=True,no_current_definition_not_eternal_nonexistence=True)


@lru_cache(None)
def method_checks():
    method=['a','a','a','a','a','now'];count=0
    for needed_bits,defined_bits in product(product((False,True),repeat=2),repeat=2):
        needed={(method[0],method[1],c,'a','a','now') for c,on in zip(('a','b'),needed_bits) if on}
        defined={(c,'a','a','a','now') for c,on in zip(('a','b'),defined_bits) if on}
        mm={'eisiu':relation(needed),'eisiq':relation(defined)}
        assert run('eilu',method,mm)==all(not n or d for n,d in zip(needed_bits,defined_bits));count+=1
    for req_bits,met_bits in product(product((False,True),repeat=2),repeat=2):
        req={('a',r,'a','now') for r,on in zip(('a','b'),req_bits) if on}
        met={('a','a',r,'a','a','now') for r,on in zip(('a','b'),met_bits) if on}
        mm={'eisgk':relation(req),'eisiv':relation(met)}
        assert run('eilv',method,mm)==(any(req_bits) and all(not r or s for r,s in zip(req_bits,met_bits)));count+=1
    # Run native composition: success with new conventions does not refute the restricted inability.
    for available,success,extra_needed,extra_defined,nonempty in product((False,True),repeat=5):
        rows={'eisit':{('a','a','a','a','now')} if available else set(),'eisiu':{('a','a','a','a','a','now')}|({('a','a','b','a','a','now')} if extra_needed else set()),'eisiq':{('a','a','a','a','now')}|({('b','a','a','a','now')} if extra_defined else set()),'eisgk':{('a','a','a','now')} if nonempty else set(),'eisiv':{('a','a','a','a','a','now')} if success else set()}
        mm={n:relation(rs) for n,rs in rows.items()}
        expected=not(available and success and nonempty and (not extra_needed or extra_defined))
        assert run('eilw',['a','a','a','a','now'],mm)==expected;count+=1
    # A second applicable method must also be checked, even if the first fails.
    rows={'eisit':{('b','a','a','a','now')},'eisiu':{('b','a','a','a','a','now')},'eisiq':{('a','a','a','a','now')},'eisgk':{('a','a','a','now')},'eisiv':{('b','a','a','a','a','now')}}
    mm={n:relation(rs) for n,rs in rows.items()}
    assert not run('eilw',['a','a','a','a','now'],mm);count+=1
    # Exact stage, task, author, document and context binding for prerequisites and success.
    for name,symbols in (('eilu',('eisiq',)),('eilv',('eisgk','eisiv'))):
        args=['b','a','a','a','a','now']
        for symbol in symbols:
            row=next(iter(rows[symbol]))
            for i in range(len(row)):
                result=run(name,args,mm|{symbol:relation({changed(row,i)})})
                assert not result, (name,symbol,i,result)
                count+=1
    reject_unknown('eilw',['a','a','a','a','now'],mm,tuple(rows))
    # Distinct fixed roles detect task/author/stage/document swaps in the universal bodies.
    roles=['method','task','author','stage','paper','now'];domain=tuple(roles[:-1])+('convention','requirement')
    calls={n:[] for n in ('eisiu','eisiq','eisgk','eisiv')}
    def capture(n):
        return lambda *xs:calls[n].append(xs) or True
    bound={n:capture(n) for n in calls}
    assert run('eilu',roles,bound,domain=domain);count+=1
    assert run('eilv',roles,bound,domain=domain);count+=1
    assert calls['eisiu'] and all(xs==('method','task',xs[2],'stage','paper','now') for xs in calls['eisiu'])
    assert calls['eisiq'] and all(xs==(xs[0],'author','stage','paper','now') for xs in calls['eisiq'])
    assert calls['eisgk'] and all(xs==('task',xs[1],'paper','now') for xs in calls['eisgk'])
    assert calls['eisiv'] and all(xs==('method','task',xs[2],'stage','paper','now') for xs in calls['eisiv'])
    return dict(cases=count,all_required_conventions_checked=True,nonempty_all_requirements_checked=True,future_stipulation_success_allowed=True,successful_existing_method_refutes_inability=True,unknown_not_false=True)


@lru_cache(None)
def task_checks():
    scope=['a','b','a','b','a','b','a','a','a','a','a','now'];args=['a']+scope
    row=('a','a','b',*scope)
    rows={'eisis':{row},'zbd':{('a',),('b',)},'cb':{('a','a','a'),('b','b','a')}}
    mm={n:relation(rs) for n,rs in rows.items()};count=0
    assert run('eilt',args,mm);count+=1
    for i in range(len(row)):
        # All individual values stay in the two-element quantified domain.
        bad=tuple(('other' if x=='now' else ('b' if x=='a' else 'a')) if j==i else x for j,x in enumerate(row))
        assert not run('eilt',args,mm|{'eisis':relation({bad})});count+=1
    for symbol in ('zbd','cb'):
        for r in rows[symbol]:
            assert not run('eilt',args,mm|{symbol:relation(rows[symbol]-{r})});count+=1
    equalplaces=args.copy();equalplaces[6]='a'
    assert not run('eilt',equalplaces,mm|{'eisis':lambda *xs:True,'cb':lambda *xs:True});count+=1
    # Quantified comparison tasks use the same fixed scope; native task body was checked above.
    for tasks,inabilities in product(product((False,True),repeat=2),repeat=2):
        taskrows={(t,*scope) for t,on in zip(('a','b'),tasks) if on}
        norows={(t,'a','a','a','now') for t,on in zip(('a','b'),inabilities) if on}
        assert run('eilx',scope,{'eilt':relation(taskrows),'eilw':relation(norows)},'tasks')==all(not t or n for t,n in zip(tasks,inabilities));count+=1
    for i in range(len(scope)):
        badscope=changed(tuple(scope),i)
        # Direct calls distinguish every task-scope slot without vacuous implication.
        assert not run('eilt',args,mm|{'eisis':relation({('a','a','b',*badscope)})});count+=1
    # One varying individual role at a time distinguishes coincident roles in the small domain.
    for i in range(len(args)-1):
        if i in (5,6):continue
        bound_args=['a']*(len(args)-1)+['now'];bound_args[6]='b';bound_args[i]='b'
        expected=(bound_args[0],'a','b',*bound_args[1:])
        locations={('a','a',bound_args[7]),('b','b',bound_args[7])}
        assert run('eilt',bound_args,mm|{'eisis':relation({expected}),'cb':relation(locations)});count+=1
    reject_unknown('eilt',args,mm,tuple(rows))
    reject_unknown('eilx',scope,{'eilt':lambda *xs:True,'eilw':lambda *xs:True},('eilt','eilw'),'tasks')
    return dict(cases=count,every_event_and_scope_slot_checked=True,native_event_types_and_locations_checked=True,all_comparison_tasks_in_same_scope=True,no_actual_event_population_added=True)


def references():
    names={'eisiw':'localA','eisix':'localB','eisib':'clockA','eisik':'clockB','ziq':'placeA','zir':'placeB','ra':'frame','rb':'unit','rd':'author','eisiy':'stage','eirf':'paper','eisie':'taskA','eisin':'taskB','eisic':'observerA','eisil':'observerB','eisid':'handA','eisim':'handB','eisiz':'node','eisio':'prior','eisi2':'nameA','eisi3':'nameB'}
    return {n:(lambda x=x:x) for n,x in names.items()}|{'ri':lambda:'now'}


@lru_cache(None)
def binding_checks():
    rows={('localA','taskA','observerA','clockA','handA','placeA','frame','unit','paper','eik4','now'),('localB','taskB','observerB','clockB','handB','placeB','frame','unit','paper','eik4','now')}
    m=references()|{'eisip':relation(rows),'eisiq':relation({(t,'author','stage','paper','now') for t in ('localA','localB')})};count=0
    domain=tuple(fn() for n,fn in references().items() if n!='ri')+('other',)
    assert run('eilz',[],m,domain=domain);count+=1
    for row in rows:
        for i in range(len(row)):
            assert not run('eilz',[],m|{'eisip':relation((rows-{row})|{changed(row,i)})},domain=domain);count+=1
    assert run('eilz',[],m|{n:forbidden for n in ('ca','cb','eish3','eish4')},domain=domain);count+=1
    scope=tuple(references()[n]() for n in ('eisiw','eisix','eisib','eisik','ziq','zir','ra','rb','rd','eisiy','eirf'))+('now',)
    taskrow=('other',*scope);failrow=('other','author','stage','paper','now')
    m2=references()|{'eilt':relation({taskrow}),'eilw':relation({failrow})}
    assert run('eily',[],m2,'tasks',domain);count+=1
    # Inspect the evaluated call, since a swapped scope could make a universal claim vacuous.
    seen=[];methods=[]
    assert run('eily',[],m2|{'eilt':lambda *xs:seen.append(xs) or False,'eilw':lambda *xs:methods.append(xs) or True},'tasks',domain);count+=1
    assert seen and all(xs[1:-1]==scope[:-1] and xs[-1] in POINTS for xs in seen)
    assert methods and all(xs[1:-1]==('author','stage','paper') and xs[-1] in POINTS for xs in methods)
    # Fixed no-common-time must look at the same stage and places.
    common={('localA',p,'frame','unit','paper','now') for p in ('placeA','placeB')}
    assert not run('eil2',[],m|{'eisir':relation(common)},domain=domain);count+=1
    for i in range(1,6):
        assert run('eil2',[],m|{'eisir':relation({changed(r,i) for r in common})},domain=domain);count+=1
    reject_unknown('eilz',[],m,('eisip','eisiq'),domain=domain)
    return dict(cases=count,all_local_rule_roles_bound_to_prior_eik4=True,rule_quote_does_not_execute_physical_readings=True,fixed_current_stage_and_comparison_scope_checked=True)


@lru_cache(None)
def content_checks():
    from noema.finite_semantics import Content
    domain=tuple(fn() for n,fn in references().items() if n!='ri')+('other',)
    count=0
    for impossible,local,no_common in product((False,True),repeat=3):
        m=references()|{n:(lambda b=b:Content(POINTS,(b,b))) for n,b in (('eily',impossible),('eilz',local),('eil2',no_common))}|{'eisdk':relation({('paper','eil3','eily','now')})}
        assert run('eil4',[],m,'content',domain)==(impossible and local and no_common);count+=1
    base=references()|{n:(lambda:Content(POINTS,(True,True))) for n in ('eily','eilz','eil2')}
    reason=('paper','eil3','eily','now')
    for i in range(len(reason)):
        assert not run('eil4',[],base|{'eisdk':relation({changed(reason,i)})},'content',domain);count+=1
    reject_unknown('eil4',[],base|{'eisdk':relation({reason})},('eisdk',),'content',domain)
    return dict(cases=count,both_clauses_asserted=True,semicolon_reason_has_correct_direction=True)


@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('node','author','paper','eil5','now')},'zbc':{('node','author','eilm','eily','paper','now'),('node','author','eilz','eil2','paper','now')},'eisi4':{('nameA','localA','placeA','paper','now'),('nameB','localB','placeB','paper','now')},'ue':{('prior','node','now')}};count=0
    domain=tuple(fn() for n,fn in references().items() if n!='ri')+('other',)
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(rs) for n,rs in rows.items()}
        assert evaluate(doc,m,domain);count+=1
        for name,rs in rows.items():
            for row in rs:
                assert not evaluate(doc,m|{name:relation(rs-{row})},domain);count+=1
                for i in range(len(row)):
                    assert not evaluate(doc,m|{name:relation((rs-{row})|{changed(row,i)})},domain);count+=1
        assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{'eisio':lambda:'node'},domain);count+=1
        assert evaluate(doc,m|{n:forbidden for n in ('eisiq','eisit','eisiu','eisiv','ca')},domain);count+=1
    return dict(cases=count,both_contrasts_designations_author_and_order_preserved=True,attribution_is_nonfactive=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==237
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for index,path in PRIORS.items():
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[index])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert source['segments'][0]['nonblank_characters']==181
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX]) and rec['source_nonblank_characters']==181
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=236,both_prior_sentence_bindings_preserved=True,six_place_symbols_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_local_times_only import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('stage',stage_checks),('method',method_checks),('task',task_checks),('binding',binding_checks),('content',content_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][12]
    segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[561,821],source=u['text'][561:821],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]
    segments.extend(dict(unit=u['id'],unit_sha256=u['text_sha256'],math_id=m['id'],math_sha256=m['sha256'],definitions=['eil4','eil6'],status='explicit_interpretive_annotation') for m in source_record()['segments'][0]['math'])
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*PRIORS.values(),'scripts/compose_local_times_only.py','scripts/check_local_times_only.py','scripts/review_local_times_only.py','tests/test_local_times_only.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='local_times_only_current_stage_and_comparison_without_further_stipulation_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['第四文以降の等片道時間・往復光・同期式と段落全体の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
