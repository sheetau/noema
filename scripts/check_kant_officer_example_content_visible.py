"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_officer_example_visible as check

CONTROLS='data/kant-officer-example-visible-diagnostic-controls-v1.json'
GROUPS={'command': ('scripts.check_officer_command_binding',
             'reports/officer-command-binding-v1.json',
             [['message_checks', 'message'],
              ['officer_checks', 'officer'],
              ['hierarchy_checks', 'hierarchy'],
              ['delivery_checks', 'delivery'],
              ['bound_checks', 'bound']]),
 'deliberation': ('scripts.check_command_deliberation',
                  'reports/command-deliberation-v1.json',
                  [['profile_checks', 'profile'],
                   ['appraisal_checks', 'appraisals'],
                   ['discussion_checks', 'discussion'],
                   ['unknown_checks', 'unknown']]),
 'example': ('scripts.check_officer_example',
             'reports/officer-example-v1.json',
             [['profile_checks', 'profile'],
              ['harm_checks', 'harm'],
              ['obedience_checks', 'obedience'],
              ['norm_checks', 'norm'],
              ['scope_checks', 'scope'],
              ['discourse_checks', 'discourse'],
              ['unknown_checks', 'unknown']]),
 'binding': ('scripts.check_officer_example', 'reports/officer-example-v1.json', [])}
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
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_officer_example_content_visible.py',
        'tests/test_kant_officer_example_content_visible.py'}
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


def current_fixture(statements,extras,boundaries=()):
    from noema.constructed_discourse import normalize_document
    source={d['name']:deepcopy(d) for d in check.source_excerpt()['declarations']}
    for name in boundaries:
        d=source[name];assert d['kind']=='definition'
        source[name]=dict(kind='primitive',name=name,parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    for d in extras:assert d['name'] not in source;source[d['name']]=d
    ds=[];seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name);d=source[name]
        for dependency in sorted(_references(d.get('body'))):visit(dependency)
        ds.append(d)
    for name in sorted(_references(statements)):visit(name)
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=statements))


def conditional_parts():
    from scripts.shared_modality import call
    body=deepcopy(recovered()['r324']['body']);assert body['kind']=='content'
    point=body['variable'];inner=body['body'];variables=[]
    for sort in ['individual']*8+['truth']:
        assert inner['kind']=='forall' and inner['sort']==sort
        variables.append(inner['variable']);inner=inner['body']
    discussion=inner['arguments'][1]['arguments'][1]
    assert discussion['kind']=='forall' and discussion['sort']=='individual'
    variable=discussion['variable'];v=lambda n:dict(kind='variable',name=n)
    args=[v(n) for n in variables];ref=call('h232v')
    scope=call('r323',*args,ref)
    norm=dict(kind='evaluate',content=call('r322',*(args[i] for i in (3,0,1,6,8)),ref),situation=v(point))
    intent=call('r32u',*(args[i] for i in (0,1,2,5,6,8)),v(variable),ref)
    work=call('h237x',args[0],args[1],args[7],v(variable),ref)
    harm=dict(kind='evaluate',content=call('r32x',args[0],v(variable),args[7],ref),situation=v(point))
    assert inner==dict(kind='implies',arguments=[scope,dict(kind='and',arguments=[norm,
        dict(kind='forall',variable=variable,sort='individual',body=dict(kind='implies',arguments=[
            dict(kind='and',arguments=[intent,work]),harm]))])])
    assert len(set([point,*variables,variable]))==11
    return point,variables,variable,inner


def probe_constants():
    return [dict(kind='primitive',name='jfixed'+letter,parameters=[],result='individual') for letter in 'abcdefgh']+[
        dict(kind='primitive',name='jsign',parameters=[],result='truth'),
        dict(kind='primitive',name='jdiscussion',parameters=[],result='individual'),
        dict(kind='primitive',name='jstart',parameters=[],result='situation')]


def instantiated_condition(slot=None):
    from scripts.shared_modality import call
    point,variables,discussion,inner=conditional_parts()
    names=[*variables,discussion]
    bindings={n:call('jfixed'+'abcdefgh'[i]) for i,n in enumerate(variables[:8]) if i!=slot}
    if slot!=8:bindings[variables[8]]=call('jsign')
    bindings[point]=call('jstart')
    if slot!=9:
        # Remove only the discussion binder being instantiated; preserve its body.
        inner['arguments'][1]['arguments'][1]=substituted(inner['arguments'][1]['arguments'][1]['body'],{discussion:call('jdiscussion')})
    inner=substituted(inner,bindings)
    if slot is not None and slot!=9:
        inner=dict(kind='forall',variable=names[slot],sort='truth' if slot==8 else 'individual',body=inner)
    return inner


@lru_cache(None)
def slotwise_binding_checks():
    from noema.constructed_semantics import Content
    fixed=('x','y','y','x','y','x','y','x');scenes=('reference','other');rows=[]
    for slot in range(10):
        doc=current_fixture([dict(kind='ask',body=instantiated_condition(slot))],probe_constants(),('r323','r32u','r322','r32x'))
        target=list(fixed)
        if slot<8:target[slot]='y' if fixed[slot]=='x' else 'x'
        target=tuple(target);sign=False if slot==8 else True;discussion='y'
        rows_for_slot={}
        def model(variant):
            seen=set();intents=set()
            def scope(*args):
                seen.add(args)
                return variant!='empty_scope' and args==(*target,sign,'reference')
            def intent(*args):
                intents.add(args)
                return variant not in ('no_intent_no_harm','no_intent_no_obligation') and args==(
                    *(target[i] for i in (0,1,2,5,6)),sign,discussion,'reference')
            def norm(*args):
                wanted=tuple(target[i] for i in (3,0,1,6))+(sign,'reference')
                good=args==wanted and variant!='no_intent_no_obligation'
                if variant=='wrong_norm_source':good=args==('other',*wanted[1:])
                return Content(scenes,tuple(good and (s=='other' if variant=='wrong_norm_evaluation' else s=='reference') for s in scenes))
            def harm(*args):
                wanted=(target[0],discussion,target[7],'other' if variant=='wrong_harm_reference' else 'reference')
                good=args==wanted and variant not in ('no_intent_no_harm','intent_no_harm')
                return Content(scenes,tuple(good and s==('other' if variant=='wrong_harm_evaluation' else 'reference') for s in scenes))
            values={name:(lambda value=fixed[i]:value) for i,name in enumerate('jfixed'+n for n in 'abcdefgh')}
            values.update(jsign=lambda:True,jdiscussion=lambda:discussion,jstart=lambda:'reference',h232v=lambda:'reference',
                r323=scope,r32u=intent,r322=norm,r32x=harm,
                h237x=lambda *args:variant!='other_discussion_work' and args==(target[0],target[1],target[7],discussion,'reference'))
            return values,seen,intents
        for variant in ('baseline','no_intent_no_harm','no_intent_no_obligation','intent_no_harm',
                        'other_discussion_work','wrong_norm_source','wrong_norm_evaluation','wrong_harm_reference','wrong_harm_evaluation','empty_scope'):
            values,seen,intents=model(variant)
            actual=[r['value'] for r in evaluated('binding',doc,primitives=values,individuals=('x','y'),situations=scenes,
                memoize_definitions=True,memoize_expressions=True)]
            expected=variant in ('baseline','no_intent_no_harm','other_discussion_work','empty_scope')
            assert actual==[expected],(slot,variant,actual)
            if slot<9:
                possible=({tuple(value if i==slot else fixed[i] for i in range(8))+(True,'reference') for value in ('x','y')}
                    if slot<8 else {(*fixed,s,'reference') for s in (False,True)})
                assert seen<=possible,(slot,variant,seen)
                # A false universal can stop at its counterexample. Successful
                # baselines must visit both values; false cases must visit the
                # exact target tuple that refutes the universal.
                if expected:assert seen==possible,(slot,variant,seen)
                else:assert (*target,sign,'reference') in seen,(slot,variant,seen)
            elif variant=='baseline':assert {args[-2] for args in intents}=={'x','y'}
            rows_for_slot[variant]=actual[0]
        def unknown(*args):raise ValueError('Unknown officer binding input')
        for name in ('r323','r32u','r322','r32x','h237x'):
            values,_,_=model('baseline')
            try:evaluated('binding',doc,primitives=values|{name:unknown},individuals=('x','y'),situations=scenes)
            except ValueError as error:assert 'Unknown officer binding input' in str(error)
            else:raise AssertionError((slot,name))
        rows.append(dict(slot=slot,contrasts=rows_for_slot,independent_values=2))
    result=dict(slots=rows,canonical_outer_and_discussion_binders_inspected=True,duty_outside_intention_condition=True,
        other_arguments_instantiated=True,native_components_evaluated_here=False,
        boundaries=['r323','r32u','r322','r32x'],full_cartesian_domain_enumerated=False,unbounded_equivalence_proved=False)
    RESULTS['binding']=result
    return result


def whole_fixture():
    body=instantiated_condition();consequence=body['arguments'][1]
    norm,conditional=consequence['arguments'];intent=conditional['arguments'][0]['arguments'][0];harm=conditional['arguments'][1]
    return current_fixture([dict(kind='ask',body=deepcopy(n)) for n in (body['arguments'][0],intent,norm,harm,body)],probe_constants())


@lru_cache(None)
def whole_content_checks():
    from noema.constructed_semantics import FunctionValue
    from scripts import check_officer_example as original
    from scripts.check_command_deliberation import discussion_model
    from scripts.check_motive_causes import symbol,unknown
    doc=whole_fixture();ds={d['name']:d for d in doc['declarations']}
    for name in ('r323','r32u','r322','r32x','r32w','r32y','r32z'):
        assert ds[name]==recovered()[name],name
    names=('person','office','institution','issuer','higher','notice','action','work')
    def model(sign,variant):
        values=discussion_model(doc,flags=(True,True,variant not in ('no_intent_no_harm','no_intent_no_obligation')),sign=sign)
        harm=original.harm_model(doc,'small_loss' if variant=='small_loss' else 'baseline')
        for name in ('h243l','h243m','h243n','h243o','cg','h242n','h242o','h243p','h243q'):values[name]=harm[name]
        if variant in ('no_intent_no_harm','no_harm'):
            values['h242o']=lambda work,ref,left,right:(work,ref)==('work','reference') and left in original.POINTS and right in original.POINTS
        if variant=='no_hypothetical_execution':values['cg']=lambda *args:False
        execution=values['cg']
        def discussion_execution(person,action,point):
            assert action!='action','Command compliance must remain quoted'
            return execution(person,action,point)
        values['cg']=discussion_execution
        values.update(h237y=lambda work,ref:(work,ref)==('work','reference'),
            h237h=lambda work,ref:'mechanism',h237i=lambda work,ref:'community',
            h237d=lambda mech,work,ref:FunctionValue(('individual',),'truth',lambda person:person=='person'),
            h237c=lambda person,community,ref:(person,community,ref)==('person','community','reference'),
            h237e=lambda person,mech,work,ref:'office',
            h237f=lambda *args:args==('person','office','mechanism','work','reference'),
            h237x=lambda p,role,w,a,r:(p,role,w,r)==('person','office','work','reference') and
                a in (('action',) if variant=='other_discussion_work' else ('discussion',) if variant=='empty_scope' else ('action','discussion')))
        def demand(source,person,role,code,bindings,targetsign,ref,requiredsign,point):
            return variant!='no_intent_no_obligation' and (source,person,role,symbol(code),code.rank,tuple(bindings.items),targetsign,ref,requiredsign,point)==(
                'issuer','person','office','r32z',1,('issuer','person','office','action'),sign,'reference',True,'reference')
        values['h243r']=demand
        values.update({'jfixed'+letter:(lambda value=names[i]:value) for i,letter in enumerate('abcdefgh')})
        values.update(jsign=lambda:sign,jdiscussion=lambda:'discussion',jstart=lambda:'reference',h232v=lambda:'reference')
        assert values['h7a'] is unknown and values['h234b'] is unknown
        return values
    def run(values):
        return [r['value'] for r in evaluated('whole',doc,primitives=values,individuals=original.DOMAIN,situations=original.SCENES,
            max_steps=100000000,memoize_definitions=True,memoize_expressions=True)]
    rows={}
    for sign in (False,True):
        for variant in ('baseline','no_intent_no_harm','no_intent_no_obligation','small_loss','no_harm','no_hypothetical_execution','other_discussion_work','empty_scope'):
            scope=variant!='empty_scope';intent=variant not in ('no_intent_no_harm','no_intent_no_obligation')
            norm=variant!='no_intent_no_obligation';harm=variant not in ('no_intent_no_harm','small_loss','no_harm','no_hypothetical_execution')
            expected=[scope,intent,norm,harm,not scope or (norm and (not intent or variant=='other_discussion_work' or harm))]
            actual=run(model(sign,variant));assert actual==expected,(sign,variant,actual,expected)
            rows[str((sign,variant))]=actual
    for name in ('h243r','h243i','h243q','h242n','h237x'):
        try:run(model(True,'baseline')|{name:unknown})
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    result=dict(contrasts=rows,current_scope_intention_norm_and_harm_connected=True,
        duty_independent_of_intention=True,positive_and_negative_commands=True,command_compliance_not_executed=True,
        hypothetical_discussion_execution_distinct=True,false_scope_conditional_is_vacuous=True,
        outer_arguments_and_discussion_instantiated_for_native_body_diagnostic=True,unbounded_equivalence_proved=False)
    RESULTS['whole']=result
    return result


def build_report():
    slotwise_binding_checks();whole_content_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-officer-example-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
