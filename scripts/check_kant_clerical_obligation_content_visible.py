"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_clerical_obligation_visible as check

CONTROLS='data/kant-clerical-obligation-visible-diagnostic-controls-v1.json'
GROUPS={'audiences': ('scripts.check_clerical_audiences',
               'reports/clerical-audiences-v1.json',
               [['role_checks', 'role'],
                ['pupil_checks', 'pupils'],
                ['audience_checks', 'audiences'],
                ['unknown_checks', 'unknown']]),
 'confession': ('scripts.check_confessional_teaching',
                'reports/confessional-teaching-v1.json',
                [['profession_checks', 'profession'], ['standard_checks', 'standard']]),
 'policy': ('scripts.check_teaching_policy',
            'reports/teaching-policy-v1.json',
            [['local_checks', 'local'],
             ['period_checks', 'period'],
             ['coverage_checks', 'coverage'],
             ['unknown_quote_checks', 'unknown_quote']]),
 'integration': ('scripts.check_clerical_obligation',
                 'reports/clerical-obligation-v1.json',
                 [['discourse_checks', 'discourse']]),
 'scope_binding': ('scripts.check_clerical_obligation', 'reports/clerical-obligation-v1.json', []),
 'policy_binding': ('scripts.check_clerical_obligation', 'reports/clerical-obligation-v1.json', []),
 'appointment': ('scripts.check_clerical_obligation', 'reports/clerical-obligation-v1.json', []),
 'whole': ('scripts.check_clerical_obligation', 'reports/clerical-obligation-v1.json', []),
 'selected_unknown': ('scripts.check_clerical_obligation', 'reports/clerical-obligation-v1.json', [])}
RESULTS={}
EVALUATION_CALLS={}
RECOVERED_DEFINITIONS={}
HISTORICAL_COMPARISONS={}
FIXTURE_ONLY_DEFINITIONS={}


@lru_cache(None)
def recovered():
    return {d['name']:d for d in check.backprojection(check.restored()['document'])['declarations'] if d['kind']=='definition'}


def adapted(group,doc,additional_roots=()):
    ds={d['name']:d for d in doc['declarations']};needed=set();pending=_references(doc['statements'])|set(additional_roots)
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.update(_references(ds[name].get('body')))
    actual=deepcopy(doc);actual['declarations']=[d for d in actual['declarations'] if d['name'] in needed]
    controls=check.read(CONTROLS)['groups'].get(group,{})
    fixture_controls=check.read(CONTROLS).get('fixture_only_controls',{}).get(group,{})
    for index,d in enumerate(actual['declarations']):
        if d['kind']!='definition':
            boundaries=check.read(CONTROLS).get('primitive_boundary_controls',{}).get(group,{})
            if d['name'] in boundaries:
                assert d==boundaries[d['name']],('Unexpected boundary',group,d['name'])
                FIXTURE_ONLY_DEFINITIONS.setdefault(group,set()).add(d['name'])
            elif d['name'] in recovered():
                raise AssertionError(('Unregistered definition-to-primitive boundary',group,d['name']))
            continue
        name=d['name']
        if name in fixture_controls and d in fixture_controls[name]:
            # Scope/focus fixtures use probes, while discourse fixtures retain
            # the current definitions under quotation in this same group.
            FIXTURE_ONLY_DEFINITIONS.setdefault(group,set()).add(name)
            continue
        if name in recovered():
            if d!=recovered()[name]:
                assert d in controls.get(name,[]),('Unexpected source-body difference',group,name)
                HISTORICAL_COMPARISONS.setdefault(group,set()).add(name)
            else:
                actual['declarations'][index]=deepcopy(recovered()[name])
                RECOVERED_DEFINITIONS.setdefault(group,set()).add(name)
        else:FIXTURE_ONLY_DEFINITIONS.setdefault(group,set()).add(name)
    return actual


def evaluated(group,doc,*,primitives,**options):
    EVALUATION_CALLS[group]=EVALUATION_CALLS.get(group,0)+1
    actual=adapted(group,doc)
    selected={d['name']:primitives[d['name']] for d in actual['declarations'] if d['kind']=='primitive'}
    return constructed_evaluate(actual,primitives=selected,**options)


@lru_cache(None)
def namespace(group):
    original=importlib.import_module(GROUPS[group][0]);ns=dict(vars(original))
    for name,wrapped in vars(original).items():
        fn=getattr(wrapped,'__wrapped__',wrapped)
        if isinstance(fn,FunctionType) and (fn.__module__==original.__name__ or name in ('evaluate','values')):
            copied=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__);copied.__kwdefaults__=fn.__kwdefaults__
            ns[name]=lru_cache(None)(copied) if hasattr(wrapped,'cache_info') else copied
    ns['evaluate_document']=lambda doc,**kwargs:evaluated(group,doc,**kwargs)
    return ns


def replay(group,function,key):
    before=EVALUATION_CALLS.get(group,0)
    result=namespace(group)[function]()
    assert EVALUATION_CALLS.get(group,0)>before,('No recovered-body evaluation',group,function)
    # Reports store tuples as JSON arrays; compare in that persisted format.
    # All finite-model assertions above still execute on their native values.
    result=json.loads(json.dumps(result,ensure_ascii=False))
    assert result==check.read(GROUPS[group][1])[key],('Retained result differs',group,function)
    RESULTS.setdefault(group,{})[key]=result
    return result


def source_pins():
    paths=set(check.source_pins())|{'scripts/check_ranked_appointment.py','scripts/compose_clerical_obligation.py',CONTROLS,'scripts/check_kant_clerical_obligation_content_visible.py',
        'tests/test_kant_clerical_obligation_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def substituted(node,bindings):
    if isinstance(node,list):return [substituted(n,bindings) for n in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name'] in bindings:return deepcopy(bindings[node['name']])
    assert not ('variable' in node and node['variable'] in bindings),'Do not capture a nested binder'
    return {k:substituted(v,bindings) for k,v in node.items()}


def current_fixture(statements,extras,boundaries=(),providers=()):
    from noema.constructed_discourse import normalize_document
    source={d['name']:deepcopy(d) for d in check.source_excerpt()['declarations']}
    for name in boundaries:
        d=source[name];assert d['kind']=='definition'
        source[name]=dict(kind='primitive',name=name,parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    for d in providers:
        original=source[d['name']]
        assert original['kind']=='primitive' and d['kind']=='definition'
        assert original['result']==d['result'] and original['parameters']==[p['sort'] for p in d['parameters']]
        source[d['name']]=deepcopy(d)
    for d in extras:assert d['name'] not in source;source[d['name']]=d
    ds=[];seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name);d=source[name]
        for dependency in sorted(_references(d.get('body'))):visit(dependency)
        ds.append(d)
    for name in sorted(_references(statements)):visit(name)
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=statements))


def quantified_parts(name,count):
    d=recovered()[name];body=deepcopy(d['body']);assert body['kind']=='content'
    point=body['variable'];body=body['body'];variables=[]
    for _ in range(count):
        assert body['kind']=='forall' and body['sort']=='individual'
        variables.append(body['variable']);body=body['body']
    return d,point,variables,body


def run_current(group,doc,values,people,scenes):
    return [r['value'] for r in evaluated(group,doc,primitives=values,individuals=people,
        situations=scenes,max_steps=100000000,memoize_definitions=True,memoize_expressions=True)]


@lru_cache(None)
def slotwise_binding_checks():
    from noema.constructed_semantics import Content
    from scripts.shared_modality import call
    scenes=('reference','outcome');rows=[]
    extras=[dict(kind='primitive',name='jfixed'+letter,parameters=[],result='individual') for letter in 'abcdefghi']
    extras+=[dict(kind='primitive',name='jpoint',parameters=[],result='situation')]
    for name,target in (('r36i','r36f'),('r36j','r36g')):
        d,point,variables,inner=quantified_parts(name,9)
        v=lambda n:dict(kind='variable',name=n)
        args=[v(n) for n in variables]+[call('h232v')]
        assert inner==dict(kind='implies',arguments=[call('r35t',*args),
            dict(kind='evaluate',content=call(target,*args),situation=v(point))])
        for slot in range(9):
            bindings={n:call('jfixed'+'abcdefghi'[i]) for i,n in enumerate(variables) if i!=slot}
            bindings[point]=call('jpoint')
            node=dict(kind='forall',variable=variables[slot],sort='individual',body=substituted(inner,bindings))
            doc=current_fixture([dict(kind='ask',body=node)],extras,('r35t',target));contrasts={}
            candidates={tuple(value if i==slot else 'x' for i in range(9))+('reference',) for value in ('x','y')}
            failing=tuple('y' if i==slot else 'x' for i in range(9))+('reference',)
            for variant in ('baseline','one_failure','wrong_reference','wrong_point','no_case'):
                visits=set();conclusions=set()
                def case(*args):
                    visits.add(args);return variant!='no_case' and args in candidates
                def conclusion(*args):
                    conclusions.add(args)
                    return Content(scenes,tuple(args[-1]==('other' if variant=='wrong_reference' else 'reference')
                        and at==('reference' if variant=='wrong_point' else 'outcome')
                        and not (variant=='one_failure' and args==failing) for at in scenes))
                values={'jfixed'+letter:(lambda:'x') for letter in 'abcdefghi'}
                values.update(h232v=lambda:'reference',jpoint=lambda:'outcome',r35t=case)
                values[target]=conclusion
                actual=run_current('scope_binding',doc,values,('x','y'),scenes)
                assert actual==[variant in ('baseline','no_case')],(name,slot,variant,actual)
                assert visits<=candidates and conclusions<=candidates
                if variant in ('baseline','no_case'):assert visits==candidates
                if variant=='one_failure':assert failing in conclusions
                contrasts[variant]=actual[0]
            rows.append(dict(target=name,slot=slot,contrasts=contrasts))
    result=dict(slots=rows,current_binder_bodies_used=True,other_binders_instantiated=True,
        two_distinguishing_values=True,full_cartesian_domain_enumerated=False,unbounded_equivalence_proved=False)
    RESULTS['scope_binding']=result
    return result


@lru_cache(None)
def policy_binding_checks():
    from noema.constructed_semantics import Content
    from scripts import check_teaching_policy as policy
    rows=[]
    for position in range(len(policy.NAMES)):
        names=tuple('person' if i==position else 'other' for i in range(len(policy.NAMES)))
        expected=tuple('x' if i==position else 'y' for i in range(len(policy.NAMES)))+('reference',)
        doc=policy.fixture('r36e',('r36d',),bindings=names);v=policy.base(doc);calls=[]
        def target(*args):
            calls.append(args);return Content(policy.SCENES,tuple(args==expected for _ in policy.SCENES))
        v.update(zperson=lambda:'x',zother=lambda:'y',r36d=target)
        assert run_current('policy_binding',doc,v,('x','y'),policy.SCENES)==[True]
        assert expected in calls
        assert all(len(args)==10 and args[-1]=='reference' and set(args[:-1])<= {'x','y'} for args in calls)
        wrong=list(expected);wrong[position]='y'
        v['r36d']=lambda *args:Content(policy.SCENES,tuple(args==tuple(wrong) for _ in policy.SCENES))
        assert run_current('policy_binding',doc,v,('x','y'),policy.SCENES)==[False]
        rows.append(position)
    for length in (0,8,10):
        doc=policy.fixture('r36e',('r36d',),bindings=('person',)*length);v=policy.base(doc)
        v.update(zperson=lambda:'x',r36d=lambda *args:Content(policy.SCENES,(True,)*len(policy.SCENES)))
        assert run_current('policy_binding',doc,v,('x','y'),policy.SCENES)==[False]
    result=dict(independently_checked_positions=rows,invalid_lengths_refused=[0,8,10],
        native_policy_adapter=True,typed_boundary='r36d',full_domain_proof=False)
    RESULTS['policy_binding']=result
    return result


def appointment_model(doc,variant='baseline',bits=(True,True,True,True,True)):
    from scripts import check_ranked_appointment as past
    from scripts import check_teaching_policy as policy
    from scripts.check_motive_causes import symbol,unknown
    v=past.model(doc,variant,bits)
    v.update({n:f for n,f in policy.base(doc,'now').items() if f is not unknown})
    when='now' if variant=='present_only' else 'future' if variant=='future_only' else 'past'
    def target(code,bindings,ref,sign,prefix):
        wanted=tuple('other' if variant==prefix+'_binding_'+n else n for n in policy.NAMES)
        if variant==prefix+'_short':wanted=wanted[:-1]
        if variant==prefix+'_long':wanted+=('other',)
        if variant==prefix+'_reordered':wanted=wanted[1:]+wanted[:1]
        return (symbol(code),code.rank,tuple(bindings.items),ref,sign)==(
            'r35w' if variant==prefix+'_description' else 'r36e',1,wanted,
            'past' if variant==prefix+'_reference' else 'reference',variant!=prefix+'_sign')
    def condition(event,code,bindings,ref,sign,at):
        events=('event','other') if variant=='two_appointments' else ('other',) if variant=='split_event' else ('event',)
        time='middle' if variant=='split_time' else when
        return bits[3] and event in events and at==time and target(code,bindings,ref,sign,'terms')
    def norm(issuer,person,role,code,bindings,ref,sign,at):
        wanted=tuple('other' if variant=='norm_'+n else value for n,value in
            zip(('issuer','person','role','point'),('church','person','role','now')))
        return bits[4] and (issuer,person,role,at)==wanted and target(code,bindings,ref,sign,'norm')
    v.update(h246m=condition,h237z=norm)
    return v


@lru_cache(None)
def appointment_document():
    from scripts import check_teaching_policy as policy
    from noema.constructed import parse
    from scripts.shared_modality import call
    extras=parse('p:'+policy.EXTRA_LOCAL)['declarations']
    args=[call('z'+n) for n in policy.NAMES]+[call('zref')]
    statements=[dict(kind='ask',body=dict(kind='evaluate',content=call(n,*args),situation=call('zpoint')))
                for n in ('r36f','r36g')]
    return current_fixture(statements,extras)


@lru_cache(None)
def appointment_checks():
    from scripts import check_ranked_appointment as past
    from scripts import check_teaching_policy as policy
    from scripts.check_motive_causes import unknown
    doc=appointment_document();rows={};independent=[]
    for required in (False,True):
        for appointed in (False,True):
            v=appointment_model(doc,bits=(True,True,appointed,True,required))
            assert all(v[n] is unknown for n in ('h246n','h246o','h246p','h246j','h246l'))
            actual=run_current('appointment',doc,v,policy.SMALL,past.SCENES)
            assert actual==[required,appointed],actual
            independent.append(dict(required=required,appointed=appointed,values=actual))
    for prefix in ('terms','norm'):
        fields=('description','reference','sign','short','long','reordered',*('binding_'+n for n in policy.NAMES))
        if prefix=='norm':fields+=('issuer','person','role','point')
        for field in fields:
            variant=prefix+'_'+field
            actual=run_current('appointment',doc,appointment_model(doc,variant),policy.SMALL,past.SCENES)
            assert actual==([True,False] if prefix=='terms' else [False,True]),(variant,actual)
            rows[variant]=actual
    witnesses={}
    for variant in ('baseline','appointment_event','appointment_issuer','appointment_person','appointment_role',
        'appointment_point','history_person','history_anchor','foreign_history','split_event','split_time',
        'present_only','future_only','cyclic','reflexive','incomparable','nontransitive','two_appointments'):
        actual=run_current('appointment',doc,appointment_model(doc,variant),policy.SMALL,past.SCENES)
        assert actual==[True,variant in ('baseline','two_appointments')],(variant,actual)
        witnesses[variant]=actual
    for index,name in enumerate(('occurrence','entrustment','appointment','terms')):
        bits=[True]*5;bits[index]=False
        actual=run_current('appointment',doc,appointment_model(doc,bits=bits),policy.SMALL,past.SCENES)
        assert actual==[True,False],(name,actual);witnesses['absent_'+name]=actual
    result=dict(independent_truth_combinations=independent,identity_contrasts=rows,witness_contrasts=witnesses,
        actual_r36f_r36g_r35x_r35y_used=True,same_rank_one_policy_and_nine_distinct_bindings=True,
        past_appointment_and_current_duty_do_not_entail_one_another=True,quoted_policy_not_executed=True)
    RESULTS['appointment']=result
    return result


@lru_cache(None)
def whole_document():
    from scripts import check_teaching_policy as policy
    from noema.constructed import parse,format_graph
    from scripts.shared_modality import call
    extras=parse('p:'+policy.EXTRA_LOCAL+policy.PROVIDERS)['declarations']
    providers={d['name']:d for d in extras if d['name'] in ('h246e','h246j')}
    extras=[d for d in extras if d['name'] not in providers]
    args=[call('z'+n) for n in policy.NAMES]+[call('zref')]
    query=lambda node:dict(kind='ask',body=node)
    ev=lambda node:dict(kind='evaluate',content=node,situation=call('zpoint'))
    statements=[query(call('r35t',*args)),query(ev(call('r36f',*args))),query(ev(call('r36g',*args)))]
    contents={}
    for name in ('r36i','r36j'):
        d,point,variables,inner=quantified_parts(name,9)
        contents[name]=dict(kind='content',variable=point,body=substituted(inner,
            {v:call('z'+n) for v,n in zip(variables,policy.NAMES)}))
        statements.append(query(ev(contents[name])))
    whole=deepcopy(recovered()['r36k']['body'])
    assert whole['body']['kind']=='and'
    assert [arg['content'] for arg in whole['body']['arguments']]==[call('r36i'),call('r36j')]
    for arg,name in zip(whole['body']['arguments'],('r36i','r36j')):arg['content']=deepcopy(contents[name])
    statements.append(query(ev(whole)))
    doc=current_fixture(statements,extras,providers=providers.values())
    for d in doc['declarations']:
        if d['name'] in recovered():assert d==recovered()[d['name']],d['name']
    return doc


def whole_model(doc,variant='baseline',bits=(True,True,True,True,True)):
    from scripts import check_confessional_teaching as confession
    from scripts.check_motive_causes import unknown
    teaching=confession.model(doc,variant);appointment=appointment_model(doc,variant,bits)
    shared={n for n in teaching if teaching[n] is not unknown and appointment.get(n,unknown) is not unknown}
    # These time-sensitive callbacks belong to actual past appointment here.
    # The teaching policy is quoted, so its concrete execution is not queried.
    assert {n for n in shared if not n.startswith('z')}<= {'dg','cf'},shared
    for n in shared-{'dg','cf','zpoint'}:assert teaching[n]()==appointment[n](),n
    values=teaching|{n:f for n,f in appointment.items() if f is not unknown}
    values['h232v']=lambda:'reference'
    return values


@lru_cache(None)
def whole_content_checks():
    from scripts import check_teaching_policy as policy
    from scripts import check_ranked_appointment as past
    from scripts.check_motive_causes import unknown
    doc=whole_document();rows={}
    cases=[('baseline',(True,)*5),('no_duty',(True,True,True,True,False)),
           ('no_appointment',(True,True,False,True,True)),('neither',(True,True,False,True,False))]
    cases += [(name,(True,)*5) for name in ('terms_binding_church','norm_binding_standard','terms_reference',
        'norm_sign','split_event','split_time','missing_pupil','extra_member','not_profession',
        'provider_standard','equivalent_alias','care_church')]
    no_case={'missing_pupil','extra_member','not_profession','provider_standard','equivalent_alias','care_church'}
    bad_terms={'terms_binding_church','terms_reference','split_event','split_time'}
    bad_norm={'norm_binding_standard','norm_sign'}
    for variant,bits in cases:
        v=whole_model(doc,variant,bits)
        for name in ('h246n','h246o','h246p','h246l','zbelief','zjudge','zconditions'):
            v[name]=unknown
        case=variant not in no_case;duty=bits[4] and variant not in bad_norm;appointed=bits[2] and variant not in bad_terms
        expected=[case,duty,appointed,not case or duty,not case or appointed,not case or (duty and appointed)]
        actual=run_current('whole',doc,v,policy.SMALL,past.SCENES)
        assert actual==expected,(variant,actual,expected);rows[variant]=actual
    result=dict(contrasts=rows,actual_case_and_norm_and_appointment_connected=True,
        current_outer_bodies_explicitly_instantiated=True,source_definitions_unmodified=True,
        quoted_policy_and_creed_truth_not_executed=True,conditional_vacuity_distinguished=True,
        policy_execution_checked_separately=True,unbounded_equivalence_proved=False)
    RESULTS['whole_native']=result
    return result


@lru_cache(None)
def selected_unknown_checks():
    from scripts import check_teaching_policy as policy
    from scripts import check_confessional_teaching as confession
    from scripts import check_ranked_appointment as past
    from scripts import check_clerical_obligation as integration
    from scripts.check_motive_causes import unknown
    rows=[]
    cases=[]
    for target,names in (('r35r',('zchoosebelief','h246g')),('r35s',('zchoosestandard','h246i'))):
        doc=confession.fixture(target)
        cases.append((doc,confession.model(doc),confession.DOMAIN,confession.SCENES,names))
    doc=policy.fixture('r356')
    cases.append((doc,policy.local_model(doc),policy.SMALL,policy.SCENES,('h246k','h246l','zjudge','zconditions')))
    doc=appointment_document()
    cases.append((doc,appointment_model(doc),policy.SMALL,past.SCENES,('ia','ic','dg','cf','h223k','h246m','h237z')))
    doc=integration.fixture('r36l',())
    cases.append((doc,integration.discourse_model(doc),integration.DISCOURSE_DOMAIN,integration.SCENES,('h236i','ud','h245m')))
    for doc,values,people,scenes,names in cases:
        for name in names:
            try:run_current('selected_unknown',doc,values|{name:unknown},people,scenes)
            except ValueError as error:assert 'Unknown' in str(error),str(error)
            else:raise AssertionError(name)
            rows.append(name)
    result=dict(unknown_required_inputs_refused=rows,excluded_old_roots_not_executed=True)
    RESULTS['selected_unknown']=result
    return result


def build_report():
    slotwise_binding_checks();policy_binding_checks();appointment_checks();whole_content_checks();selected_unknown_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-clerical-obligation-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
