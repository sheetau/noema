"""Check temporal credit, sustained help, date precision and narrative voices."""
from scripts.compose_closing_acknowledgment import *
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction as Q
import json,re
from noema.finite_semantics import evaluate_document,Content,FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_clock_site_time import relation,perturb
from scripts.check_sustained_assistance import model_for as assistance_model
from scripts.check_rod_setup import guarded

DOC='docs/closing-acknowledgment-v1.md';SOURCE='data/einstein-closing-acknowledgment-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf'
DEPENDENCIES=('reports/sustained-assistance-v1.json','reports/intellectual-credit-v1.json','reports/calendar-dateline-v1.json','reports/unreceived-reference-v1.json','reports/dated-reading-v1.json')
SCENES=('early','middle','late','now','future','belief')
CONSTANTS={'rd':'recipient','zrqperson':'helper','zrqwork':'work','ri':'now','eirf':'paper','zrqscope':'ackscope'}|{n:n for n in REFERENCES}
PEOPLE=tuple(dict.fromkeys([*CONSTANTS.values(),'input1','input2','input3','act0','act2','event','measure','j1','j2','j3','other','monthother','dayother']))
BOUNDS={'ett':{'ets'},'etv':{'etu'},'et2':{'etz'},'et4':{'et3'},'et6':{'et5'}}
def forbidden(*xs):raise ValueError('Unknown closing input')
def reject(f):
    try:f()
    except ValueError:return
    raise AssertionError('Unknown input accepted')
def walk(x):
    if isinstance(x,dict):
        yield x
        for y in x.values():yield from walk(y)
    elif isinstance(x,list):
        for y in x:yield from walk(y)
@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def fixture(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jclosingslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jclosingpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jclosingpoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots
def run(root,values,m,people=PEOPLE,scenes=SCENES):
    doc,slots=fixture(root);assert len(values)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jclosingpoint':lambda:'now'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    if root in ('etw','etx','ety','et3'):people=people+tuple('month'+str(i) for i in range(12))+tuple('day'+str(i) for i in range(30))
    return evaluate_document(doc,individuals=people,situations=scenes,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=8000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def function(parameters,result,callback):return FunctionValue(tuple(parameters),result,callback)

def past_model(variant='baseline'):
    times={x:i for i,x in enumerate(SCENES)};now=('now','belief')
    relation_callbacks={
      'history':lambda p:p!='future',
      'scope':lambda p:p in ('early','middle','late') and not(variant=='scope_hole' and p=='middle'),
      'before':lambda a,b:times[a]<times[b],
      'working':lambda person,work,p:(person,work)==('recipient','work') and p in ('early','middle','late') and not(variant=='work_gap' and p=='middle'),
    }
    fields={'history':(['situation'],'truth'),'scope':(['situation'],'truth'),'before':(['situation','situation'],'truth'),'working':(['individual','individual','situation'],'truth')}
    m={}
    for n,f in relation_callbacks.items():
        value=function(*fields[n],f);m['zrr'+n]=lambda value=value:value
    inputs=('input1','input2','input3') if variant=='three' else ('input1','input2')
    def past(p):return p==('future' if variant=='future_only' else 'early')
    rows={
      'occurs':lambda event,p:event=='event' and past(p),
      'performs':lambda person,event,p:(person,event)==('helper','event') and past(p) and variant!='wrong_giver',
      'produces':lambda event,item,p:event=='event' and item in inputs and past(p),
      'uses':lambda person,item,work,p:(person,work)==('recipient','work') and item in inputs and past(p) and variant!='unused',
      'standard':lambda person,work,measure,p:(person,work,measure)==('recipient','work','measure') and p in now and variant!='no_standard',
      'meets':lambda item,measure,p:item in inputs and measure=='measure' and p in now and not(variant=='bad_second' and item=='input2'),
    }
    for n,t in credit.RELATIONS:
        argc={'occurs':2,'performs':3,'produces':3,'uses':4,'standard':4,'meets':3}[n]
        value=function(['individual']*(argc-1)+['situation'],'truth',rows[n]);m['zrq'+n]=lambda value=value:value
    judgments={'j1':'input1','j2':'input1' if variant=='duplicate' else 'input2'}
    if variant=='one':judgments={'j1':'input1'}
    if variant=='three':judgments['j3']='input3'
    def linked(j,description,bindings,p):
        expected=('recipient','helper',judgments.get(j),'work')
        if variant=='swapped':expected=('helper','recipient',judgments.get(j),'work')
        return j in judgments and json.loads(description.syntax)==dict(kind='call',symbol='eto',arguments=[]) and bindings.items==expected and p=='now'
    judging={
      'judgments':lambda person,j,p:person=='recipient' and j in judgments and p=='now',
      'matters':lambda j,person,p:j in judgments and person=='helper' and p=='now',
      'linked':linked,
      'candidates':lambda j,context,p:j in judgments and context=='now' and p=='belief' and variant!='empty_candidates',
    }
    # Derive exact function types from the declarations to preserve description sorts.
    lookup={d['name']:d for d in core()['declarations']}
    for n,f in judging.items():
        typ=lookup['zrq'+n]['result'];value=function(typ['parameters'],typ['result'],f);m['zrq'+n]=lambda value=value:value
    return m

@lru_cache(None)
def credit_checks():
    cases=0;people=('recipient','helper','work','input1','input2','input3','event','measure','j1','j2','j3','other')
    for variant,wanted in [('baseline',True),('three',True),('one',False),('duplicate',False),('bad_second',False),('unused',False),('wrong_giver',False),('swapped',False),('empty_candidates',False),('scope_hole',False),('work_gap',False),('future_only',False),('no_standard',False)]:
        m=past_model(variant);actual=run('etq',[],m,people);assert actual==wanted,(variant,actual);cases+=1
    m=past_model();assert run('etm',['recipient','helper','input1','work','now'],m,people);cases+=1
    assert run('etp',[],m,people)==run('etq',[],m,people);cases+=1
    for name in ('rd','zrqperson','zrqwork'):
        assert not run('etq',[],m|{name:lambda:'other'},people);cases+=1
    for i in range(4):
        xs=['recipient','helper','input1','work','now'];xs[i]='other';assert not run('etm',xs,m,people);cases+=1
    for name in ('zrrscope','zrrbefore','zrqproduces','zrquses','zrqstandard','zrqmeets'):
        reject(lambda:run('etq',[],m|{name:forbidden},people));cases+=1
    # Present recognition is evaluated in a candidate, without asserting current occurrence.
    assert not m['zrqoccurs']()('event','now');cases+=1
    differs=m|{'zrqmeets':lambda:function(['individual','individual','situation'],'truth',lambda item,measure,p:item in ('input1','input2') and measure=='measure' and p=='belief')}
    assert run('etq',[],differs,people) and not run('etm',['recipient','helper','input1','work','now'],differs,people);cases+=1
    return dict(cases=cases,past_contribution_current_value_and_same_work=True,at_least_two_distinct_inputs_without_upper_bound=True,ordered_argument_binding_and_unknown_rejection=True,current_occurrence_not_inferred_from_credit=True)

@lru_cache(None)
def support_checks():
    doc,_=fixture('etr');cases=0
    rows={'eis5t':{('recipient','helper','now')},'eis5u':{('recipient','helper','now')},'eis5v':{('work','eis6k','now')},'eis5w':{('paper','eis6k','now')}}
    def scope_contract(recipient,work,history,scope,occasions,ctx):
        return (recipient,work,ctx)==('recipient','work','now') and all(history(p) for p in ('early','middle','late','now')) and tuple(p for p in SCENES[:-1] if scope(p))==('early','middle','late') and tuple(p for p in SCENES[:-1] if occasions(p))==('early','late')
    def model(variant):return assistance_model(doc,variant)|{n:lambda x=x:x for n,x in CONSTANTS.items()}|{n:relation(rs) for n,rs in rows.items()}|{'eis5y':scope_contract,'jclosingpoint':lambda:'now'}
    evaluate=lambda m:run('etr',[],m,scenes=SCENES[:-1])
    for variant,wanted in [('baseline',True),('missed_second',False),('other_helper',False),('extra_occasion',False),('empty_occasions',False),('scope_hole',False),('reversed_bindings',False),('different_goal',False),('no_intention',False),('no_beneficiary_goal',False)]:
        assert evaluate(model(variant))==wanted,variant;cases+=1
    m=model('baseline');cases+=perturb(evaluate,m,rows)
    assert not evaluate(m|{'eis5y':lambda *xs:False});reject(lambda:evaluate(m|{'eis5y':forbidden}));cases+=2
    # The native purpose remains quoted and need not be achieved.
    assert evaluate(m|{'zrradvances':forbidden});cases+=1
    return dict(cases=cases,complete_support_scope_not_success_selected=True,friend_colleague_problem_and_same_helper_bound=True,actual_help_required_but_goal_success_not_required=True)

def date_model():
    m={'eis5z':lambda cal,year,n,ctx:(cal,year,n,ctx)==('eis6o','eis6p',Q(1905),'now')}
    seq=lambda xs:SequenceValue(tuple(xs),json.dumps('individual'))
    m['eis6a']=lambda cal,year,ctx:seq('eis6q' if i==5 else 'month'+str(i) for i in range(12)) if (cal,year,ctx)==('eis6o','eis6p','now') else seq('month'+str(i) for i in range(12))
    m['eis6b']=lambda cal,month,ctx:seq('eis6r' if i==29 else 'day'+str(i) for i in range(30)) if (cal,month,ctx)==('eis6o','eis6q','now') else seq('day'+str(i) for i in range(30))
    return m

@lru_cache(None)
def date_checks():
    m=date_model();cases=0;vs=['eis6o','eis6p','eis6q',Q(1905),Q(5),'now']
    assert run('etw',vs,m);cases+=1
    for i,badvalue in [(0,'other'),(1,'other'),(2,'monthother'),(3,Q(1906)),(4,Q(6)),(4,Q(-1)),(4,Q(1,2)),(4,Q(12)),(5,'belief')]:
        bad=vs.copy();bad[i]=badvalue;assert not run('etw',bad,m);cases+=1
    rows={'eira':{('eis6m','now')},'eirb':{('eis6m','eis6s','eis6t','now')},'eis6c':{('eis6m','paper','eis6t','now')},'eis6d':{('eis6m','paper','eis6q','now')}}
    mm=m|{n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda model:run('ety',[],model),mm,rows)
    assert run('ety',[],mm|{'eis6b':forbidden,'eis6e':forbidden,'eis6h':forbidden});cases+=1
    assert not run('ety',[],mm|{'eis6s':lambda:'eis6t'});cases+=1
    rows={'eis6e':{('eis6u','paper','early','now')},'eis6h':{('early','eis6r','now')}}
    mm=m|{n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda model:run('et3',[],model),mm,rows)
    # A different instant inside the same day is permitted; it need not be the display context.
    for p in ('middle','late'):
        assert run('et3',[],m|{'eis6e':relation({('eis6u','paper',p,'now')}),'eis6h':relation({(p,'eis6r','now')})});cases+=1
    assert not run('et3',[],mm|{'eis6b':lambda *xs:SequenceValue(tuple('day'+str(i) for i in range(30)),json.dumps('individual'))});cases+=1
    for name in ('eis5z','eis6a','eis6b'):reject(lambda:run('et3',[],mm|{name:forbidden}));cases+=1
    return dict(cases=cases,year_month_day_roles_and_calendar_preserved=True,month_precision_has_no_hidden_day=True,receipt_in_day_without_fixed_time_or_author_voice=True,unknown_calendar_refused=True)

@lru_cache(None)
def presentation_checks():
    rows={'eis5x':{('eis6i','paper','now')},'uh':{('eis6i','recipient','ets','ackscope','now')},'eira':{('eis6i','now')},'eirb':{('eis6i','eis6l','helper','now')}}
    cases=perturb(lambda m:run('ett',[],m),{n:relation(rs) for n,rs in rows.items()}|{'ets':forbidden},rows)
    assert not run('ett',[],{n:relation(rs) for n,rs in rows.items()}|{'eis6l':lambda:'helper','ets':forbidden});cases+=1
    rows={'eis6f':{('eis6n','paper','et3','now')}};cases+=perturb(lambda m:run('et4',[],m),{n:relation(rs) for n,rs in rows.items()}|{'et3':forbidden},rows)
    for root,node,message,previous,author in [('etv','eis6i','etu','eis6j',True),('et2','eis6m','etz','eis6i',False),('et6','eis6n','et5','eis6m',False)]:
        n='eir3' if author else 'eis6g';row=(node,'recipient','paper',message,'now') if author else (node,'paper',message,'now')
        rows={n:{row},'ue':{(previous,node,'now')}};cases+=perturb(lambda m:run(root,[],m),{n:relation(rs) for n,rs in rows.items()}|{message:forbidden},rows)
    return dict(cases=cases,closing_remark_name_application_and_anaphora=True,authorial_credit_distinct_from_publication_notice=True,source_order_and_quoted_content_not_executed=True)

@lru_cache(None)
def source_record():
    d=json.loads(read(INVENTORY));units=d['units'][275:278]
    for u in units:assert digest(u['text'].encode())==u['text_sha256'] and not u['math_ids']
    return dict(version='einstein-closing-acknowledgment-reading-v1',units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[],source_nonblank_characters=len(re.sub(r'\s','',u['text']))) for u in units],facsimile_pages=[921],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==444 and after.document['statements'][:441]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[437,438,439,440])==selection_binding(before,[437,438,439,440]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert next(d for d in core()['declarations'] if d['name']=='etx')==calendar_definition()
    for n,e in copied_entries().items():assert after.entries[n]['meaning_ja']==e['meaning_ja']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),reused_general_relations=len(COPIED),new_reference_constants=len(REFERENCES),new_statements=3,all_441_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('credit',credit_checks),('support',support_checks),('date',date_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,CALENDAR_LIBRARY,CALENDAR_BASIS,RECEIPT_BASIS,PERIOD_BASIS,'scripts/compose_closing_acknowledgment.py','scripts/check_closing_acknowledgment.py','tests/test_closing_acknowledgment.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='closing_acknowledgment_and_distinct_dates_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
