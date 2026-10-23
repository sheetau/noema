"""Check local/remote task scopes, adequate rules and the explanatory contrast."""
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
from scripts.compose_clock_definition_scope import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/clock-definition-scope-v1.md';SOURCE='data/einstein-clock-definition-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/clock-definition-scope-reading-v1.json'
PRIOR='data/clock-definition-proposal-reading-v1.json'
DOMAIN=('proposal','author','problem','clock','hand','frame','unit','paper','local','link','remote','req1','req2','event','display','place','node','prior','other')
POINTS=('now','other');TWO=('a','b')
BASE=['author','clock','hand','frame','unit','now']
ADEQUACY=['proposal','local','author','clock','hand','frame','unit','paper','now']

def forbidden(*args):raise ValueError('Unknown clock-definition-scope input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,(set() if mode=='real' else NUM)|({'eijj','eijt','eijv','eijw'} if mode=='claims' else set()))
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jcs'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jcscontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jcscontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m,domain=DOMAIN):
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,args,m,domain=DOMAIN,mode='native'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jcscontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)

def reject_unknown(name,args,m,symbols,domain=DOMAIN,mode='native'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},domain,mode)
        except ValueError as e:assert 'Unknown clock-definition-scope' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))

@lru_cache(None)
def local_rule_checks():
    cuts,m=arithmetic();r=cuts.read;count=0
    rows={'ca':{('clock',)},'ci':{('unit',)},'va':{('frame',)},'eisdf':{('clock','now')},'eise6':{('clock','author','now')},'eise7':{('hand','clock','now')},
        'cb':{(x,'place','frame') for x in ('clock','event','display')},'zbd':{('event',),('display',)},'eisgf':{('clock','place','frame','now')},'eisgm':{('event','display','clock','frame','now')}}
    m|={n:relation(rs) for n,rs in rows.items()}
    m|={'eisfc':lambda d,h,c,x,s:(d,h,c,r(x),s)==('display','hand','clock',Q(5,2),'now'),'ce':lambda c,e,f,u,x:(c,e,f,u,r(x)) in {('clock',e,'frame','unit',Q(5,2)) for e in ('display','event')}}
    args=BASE+['event','display','place',cuts.make(Q(5,2))]
    assert run('eijr',args,m);count+=1
    for i in range(len(args)-1):
        bad=args.copy();bad[i]='other';assert not run('eijr',bad,m);count+=1
    for name in ('cb','zbd','eisgf','eisgm'):
        for row in rows[name]:
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eijr',args,m|{name:relation((rows[name]-{row})|{bad})});count+=1
    for reading,indication,target in product((Q(5,2),Q(8)),repeat=3):
        mm=m|{'eisfc':lambda d,h,c,x,s,mark=indication:(d,h,c,r(x),s)==('display','hand','clock',mark,'now'),'ce':lambda c,e,f,u,x,mark=target:(c,e,f,u,r(x)) in {('clock','display','frame','unit',Q(5,2)),('clock','event','frame','unit',mark)}}
        assert run('eijr',BASE+['event','display','place',cuts.make(reading)],mm)==(reading==indication==target==Q(5,2));count+=1
    assert not run('eijr',args,m|{'eisgm':relation(set())});count+=1
    assert run('eijr',args,m|{'cc':forbidden,'eihm':forbidden,'qo':forbidden});count+=1
    reject_unknown('eijr',args,m,('ce','eisfc','eisgm','eisgf','ba'))
    try:run('eijr',args,m,mode='real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real domain silently sampled')
    return dict(cases=count,same_display_target_reading_and_present_location=True,equal_hand_phase_alone_not_coincidence=True,no_global_synchronization_or_whole_clock_stationarity=True,unknown_and_full_real_inputs_not_silently_sampled=True)

@lru_cache(None)
def scope_checks():
    count=0;args=['a']*5+['now']
    base={'ca':relation({('a',)}),'va':relation({('a',)}),'ci':relation({('a',)}),'eisgg':relation({tuple(args)}),'eisgf':relation({('a','a','a','now')}),'zbd':relation({('a',),('b',)})}
    for distant,near,member,clock_present in product((False,True),repeat=4):
        location='b' if distant else 'a'
        m=base|{'cb':relation({('a','a','a'),('b',location,'a')}),'eisge':relation({('a','b','now')} if member else set()),'eisfp':relation({('b','a','a','now')} if near else set()),'eisgf':relation({('a','a','a','now')} if clock_present else set())}
        assert run('eijt',args,m,TWO)==(not distant and member and clock_present);count+=1
        assert run('eijw',args,m,TWO)==(distant and not near and member and clock_present);count+=1
    m=base|{'cb':relation({('a','a','a'),('b','b','a')}),'eisge':relation({('a','a','now'),('a','b','now')}),'eisfp':relation(set())}
    assert not run('eijt',args,m,TWO) and not run('eijw',args,m,TWO);count+=2
    for name in ('eijs','eiju'):
        membership='eisge' if name=='eijs' else 'eisgi'
        for first,second,left,right in product((False,True),repeat=4):
            mm={'zbd':relation({('a',),('b',)}),membership:relation({('a',e,'now') for e,on in (('a',first),('b',second)) if on}),'cb':relation({(e,'a','a') for e,on in (('a',left),('b',right)) if on})}
            assert run(name,['a','a','a','now'],mm,TWO)==((first or second) and (not first or left) and (not second or right));count+=1
    remote=base|{'cb':relation({('a','a','a'),('b','b','a')}),'eisge':relation({('a','b','now')}),'eisfp':relation(set())}
    for i in range(len(args)):
        bad=args.copy();bad[i]='other' if i==5 else 'b';assert not run('eijw',bad,remote,TWO);count+=1
    reject_unknown('eijw',args,remote,('eisge','eisgf','eisfp','eisgg','cb'),TWO)
    return dict(cases=count,nonempty_all_target_events=True,exclusively_current_clock_place=True,nearby_not_misclassified_as_remote=True,mixed_local_remote_scope_not_pure_local_or_remote=True)

@lru_cache(None)
def series_checks():
    args=['a']*5+['now'];count=0
    base={'ca':relation({('a',)}),'va':relation({('a',)}),'ci':relation({('a',)}),'eisgj':relation({tuple(args)}),'zbd':relation({('a',),('b',)})}
    for distinct_series,distinct_places,first_member,second_member in product((False,True),repeat=4):
        second='b' if distinct_series else 'a';right='b' if distinct_places else 'a'
        rs={('a','a','a','a','now'),('a',second,right,'a','now')}
        members={('a','a','now')} if first_member else set()
        if second_member:members.add((second,'b','now'))
        m=base|{'eisgh':relation(rs),'eisgi':relation(members),'cb':relation({('a','a','a'),('b',right,'a')})}
        assert run('eijv',args,m,TWO)==(distinct_series and distinct_places and first_member and second_member);count+=1
    rows={'eisgh':{('a','a','a','a','now'),('a','b','b','a','now')},'eisgi':{('a','a','now'),('b','b','now')},'cb':{('a','a','a'),('b','b','a')}}
    m=base|{n:relation(r) for n,r in rows.items()}
    for symbol in ('eisgh','eisgi','cb'):
        for row in rows[symbol]:
            assert not run('eijv',args,m|{symbol:relation(rows[symbol]-{row})},TWO);count+=1
    assert not run('eijv',args,m|{'eisgi':relation(rows['eisgi']|{('a','b','now')})},TWO);count+=1
    for i in range(len(args)):
        bad=args.copy();bad[i]='other' if i==5 else 'b';assert not run('eijv',bad,m,TWO);count+=1
    reject_unknown('eijv',args,m,('eisgj','eisgh','eisgi','cb'),TWO)
    return dict(cases=count,two_distinct_series_at_distinct_places=True,all_series_members_at_assigned_places=True,no_interseries_timing_solution_presupposed=True)

@lru_cache(None)
def adequacy_checks():
    count=0
    required={('local',r,'paper','now') for r in ('req1','req2')}
    row=lambda req:tuple(ADEQUACY[:-1]+[req,'eijr','now'])
    for first,second,metfirst,metsecond in product((False,True),repeat=4):
        reqs={('local',r,'paper','now') for r,on in (('req1',first),('req2',second)) if on}
        met={row(r) for r,on in (('req1',metfirst),('req2',metsecond)) if on}
        m={'eisgk':relation(reqs),'eisgl':relation(met)}
        assert run('eijx',ADEQUACY,m)==((first or second) and (not first or metfirst) and (not second or metsecond));count+=1
        assert run('eijy',ADEQUACY,m)==((first and not metfirst) or (second and not metsecond));count+=1
    rows={row('req1'),row('req2')};m={'eisgk':relation(required),'eisgl':relation(rows)}
    for rr in rows:
        for i in range(len(rr)):
            bad=tuple('other' if j==i else x for j,x in enumerate(rr));mm=m|{'eisgl':relation((rows-{rr})|{bad})}
            assert not run('eijx',ADEQUACY,mm) and run('eijy',ADEQUACY,mm);count+=2
    assert run('eijx',ADEQUACY,m|{'eisgm':forbidden,'ce':forbidden,'eisfc':forbidden});count+=1
    reject_unknown('eijx',ADEQUACY,m,('eisgk','eisgl'))
    reject_unknown('eijy',ADEQUACY,m,('eisgk','eisgl'))
    return dict(cases=count,all_nonempty_requirements_for_sufficiency=True,one_known_unmet_requirement_for_insufficiency=True,same_proposal_clock_rule_and_task=True,unknown_not_converted_to_insufficiency=True)

@lru_cache(None)
def equivalence_checks():
    args=['a']*4+['now'];count=0
    for bits in product((False,True),repeat=4):
        rows={(s,kind,*args) for (kind,s),on in zip(product(('eijv','eijw'),TWO),bits) if on}
        assert run('eijz',args,{'eisgn':relation(rows)},TWO)==(bits[:2]==bits[2:]);count+=1
    rows={('a',kind,*args) for kind in ('eijv','eijw')}
    row=('a','eijv',*args)
    for i in range(len(row)):
        bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eijz',args,{'eisgn':relation((rows-{row})|{bad})},TWO);count+=1
    reject_unknown('eijz',args,{'eisgn':relation(rows)},('eisgn',),TWO)
    return dict(cases=count,solution_scopes_equal_in_both_directions=True,shared_clock_frame_units_and_event_interpretation=True,no_solution_existence_added=True)

def references():
    return {n:(lambda x=x:x) for n,x in zip(('eisf5','rd','eisf6','eisf7','eisga','ra','eisgb','eirf','eisgq','eisgc'),('proposal','author','problem','clock','hand','frame','unit','paper','node','prior'))}|{'ri':lambda:'now'}

@lru_cache(None)
def conditional_checks():
    count=0;fixed=['clock','frame','unit','paper','now']
    rows={'eijj':{('proposal','author','problem','clock','hand','frame','unit','paper','now')},'eisgd':{(t,'problem','author','paper','now') for t in ('local','link','remote')},'eijt':{('local',*fixed)},'eijv':{('link',*fixed)},'eijw':{('remote',*fixed)},'eisgk':{(t,'req1','paper','now') for t in ('local','link','remote')}}
    m=references()|{n:relation(r) for n,r in rows.items()}
    row=lambda t:('proposal',t,'author','clock','hand','frame','unit','paper','req1','eijr','now')
    for local,link,remote,equivalent in product((False,True),repeat=4):
        met={row(t) for t,on in (('local',local),('link',link),('remote',remote)) if on}
        solutions={('author',kind,*fixed) for kind in (('eijv','eijw') if equivalent else ('eijv',))}
        mm=m|{'eisgl':relation(met),'eisgn':relation(solutions)}
        assert run('eij5',[],mm,mode='claims')==(local and not link and not remote and equivalent);count+=1
    good=m|{'eisgl':relation({row('local')}),'eisgn':relation({('author',kind,*fixed) for kind in ('eijv','eijw')})}
    # The finite interpreter evaluates both sides of an implication. Supply known
    # truth values to test vacuity; unknown inputs must still be rejected.
    for met in (set(),{row(t) for t in ('local','link','remote')}):
        assert run('eij5',[],good|{'eisgd':relation(set()),'eisgl':relation(met)},mode='claims');count+=1
    for symbol in references():
        if symbol in ('eisgq','eisgc','ri'):continue
        assert not run('eij5',[],good|{symbol:lambda:'other'},mode='claims');count+=1
    reject_unknown('eij5',[],good,('eisgd','eisgk','eisgl','eisgn'),mode='claims')
    return dict(cases=count,local_sufficiency_and_remote_insufficiency_conditional_on_task=True,same_definition_as_previous_sentence=True,equivalence_is_asserted_not_only_mentioned=True,task_class_boundaries_checked_separately=True)

@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('node','author','paper','eij6','now')},'eisgo':{('node','author','eij2','paper','now')},'zbc':{('node','author','eij2','eij3','problem','now')},'eisgp':{('node','author','eij3','eij4','paper','now')},'ue':{('prior','node','now')}};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(r) for n,r in rows.items()}
        for bits in product((False,True),repeat=5):
            assert evaluate(doc,m|{n:relation(r if on else set()) for (n,r),on in zip(rows.items(),bits)})==all(bits);count+=1
        for symbol,rs in rows.items():
            row=next(iter(rs))
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not evaluate(doc,m|{symbol:relation({bad})});count+=1
        assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{'eisgc':lambda:'node'});count+=1
    return dict(cases=count,in_fact_confirmation_local_only=True,contrast_direction_and_parenthetical_task_equivalence=True,attribution_not_physical_execution=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==231
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[229])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256']);u=json.loads(read(INVENTORY))['units'][10];seg=source['segments'][1]
    assert seg['unit']==u['id'] and seg['range']==[201,639] and seg['text']==u['text'][201:639] and seg['unit_sha256']==u['text_sha256'] and seg['nonblank_characters']==373
    reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256']);assert reading['selection']==selection_binding(new,[INDEX]) and reading['source_nonblank_characters']==373
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=230,prior_sentence_binding_preserved=True,whole_paragraph_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_clock_definition_scope import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('local_rule',local_rule_checks),('scope',scope_checks),('series',series_checks),('adequacy',adequacy_checks),('equivalence',equivalence_checks),('conditions',conditional_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][10]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,PRIOR,'scripts/compose_clock_definition_scope.py','scripts/check_clock_definition_scope.py','scripts/review_clock_definition_scope.py','tests/test_clock_definition_scope.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='clock_definition_local_adequacy_and_remote_scope_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[201,639],source=u['text'][201:639],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['全二文545文字の段落全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
