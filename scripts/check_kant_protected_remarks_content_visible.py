"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_protected_remarks_visible as check

CONTROLS='data/kant-protected-remarks-visible-diagnostic-controls-v1.json'
GROUPS={'remarks': ('scripts.check_military_remarks',
             'reports/military-remarks-v1.json',
             [['defect_checks', 'defect'],
              ['notes_checks', 'notes'],
              ['goal_checks', 'goal'],
              ['candidate_checks', 'candidate'],
              ['officer_checks', 'officer'],
              ['execution_checks', 'execution'],
              ['unknown_checks', 'unknown']]),
 'protection': ('scripts.check_protected_remarks',
                'reports/protected-remarks-v1.json',
                [['payload_checks', 'payload'],
                 ['ban_checks', 'bans'],
                 ['protection_checks', 'protection'],
                 ['scope_checks', 'scope'],
                 ['regulator_checks', 'regulators'],
                 ['discourse_checks', 'discourse'],
                 ['unknown_checks', 'unknown']]),
 'prior_binding': ('scripts.check_protected_remarks', 'reports/protected-remarks-v1.json', []),
 'binding': ('scripts.check_protected_remarks', 'reports/protected-remarks-v1.json', [])}
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
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_protected_remarks_content_visible.py',
        'tests/test_kant_protected_remarks_content_visible.py'}
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


def prior_parts():
    from scripts.shared_modality import call
    d=recovered()['r33n'];params=[p['name'] for p in d['parameters']]
    assert [p['sort'] for p in d['parameters']]==['individual']*3+['situation']
    inner=deepcopy(d['body']);witnesses=[]
    for sort in ['individual']*5+['truth']:
        assert inner['kind']=='exists' and inner['sort']==sort
        witnesses.append(inner['variable']);inner=inner['body']
    v=lambda name:dict(kind='variable',name=name)
    assert inner==call('r323',*(v(n) for n in params[:3]+witnesses+[params[3]]))
    assert len(set(params+witnesses))==10
    return params,witnesses,inner


def conditional_parts():
    from scripts.shared_modality import call
    body=deepcopy(recovered()['r33q']['body']);assert body['kind']=='content'
    point=body['variable'];inner=body['body'];variables=[]
    for _ in range(9):
        assert inner['kind']=='forall' and inner['sort']=='individual'
        variables.append(inner['variable']);inner=inner['body']
    v=lambda n:dict(kind='variable',name=n)
    assert len(set([point,*variables]))==10
    assert inner==dict(kind='implies',arguments=[call('r33o',*(v(n) for n in variables),call('h232v')),
        dict(kind='evaluate',content=call('r33p',*(v(n) for n in variables[2:]),call('h232v')),situation=v(point))])
    join=recovered()['r33o'];params=[p['name'] for p in join['parameters']]
    assert [p['sort'] for p in join['parameters']]==['individual']*9+['situation']
    assert join['body']==dict(kind='and',arguments=[call('r33n',*(v(params[i]) for i in (2,0,1,9))),call('r33c',*(v(n) for n in params))])
    return point,variables,inner


def probe_constants():
    return [dict(kind='primitive',name='jfixed'+letter,parameters=[],result='individual') for letter in 'abcdefghi']+[
        dict(kind='primitive',name='jwitness'+letter,parameters=[],result='individual') for letter in 'abcde']+[
        dict(kind='primitive',name='jsign',parameters=[],result='truth'),
        dict(kind='primitive',name='jstart',parameters=[],result='situation')]


@lru_cache(None)
def prior_binding_checks():
    from scripts.shared_modality import call
    params,witnesses,inner=prior_parts();fixed=('x','y','x','y','x');scenes=('reference','other');rows=[]
    for slot in range(6):
        binds={n:call('jfixed'+'abc'[i]) for i,n in enumerate(params[:3])};binds[params[3]]=call('h232v')
        binds.update({n:call('jwitness'+'abcde'[i]) for i,n in enumerate(witnesses[:5]) if i!=slot})
        if slot!=5:binds[witnesses[5]]=call('jsign')
        body=dict(kind='exists',variable=witnesses[slot],sort='truth' if slot==5 else 'individual',body=substituted(inner,binds))
        doc=current_fixture([dict(kind='ask',body=body)],probe_constants(),('r323',));contrasts={}
        for sign in (False,True):
            for variant in ('baseline','no_witness','wrong_person','wrong_office','wrong_institution','wrong_reference'):
                target=('x','y','x',*fixed,sign,'reference');seen=set()
                wrong={'wrong_person':0,'wrong_office':1,'wrong_institution':2,'wrong_reference':9}.get(variant)
                wanted=list(target)
                if slot<5:wanted[slot+3]='y' if fixed[slot]=='x' else 'x'
                if wrong is not None:wanted[wrong]='other'
                wanted=tuple(wanted)
                def boundary(*args):seen.add(args);return variant!='no_witness' and args==wanted
                values={'jfixeda':lambda:'x','jfixedb':lambda:'y','jfixedc':lambda:'x','jsign':lambda:sign,'h232v':lambda:'reference','r323':boundary}
                values.update({'jwitness'+letter:(lambda value=fixed[i]:value) for i,letter in enumerate('abcde')})
                actual=[r['value'] for r in evaluated('prior_binding',doc,primitives=values,individuals=('x','y'),situations=scenes)]
                assert actual==[variant=='baseline'],(slot,sign,variant,actual)
                if variant=='baseline':assert wanted in seen
                else:
                    expected={tuple(value if i==slot+3 else target[i] for i in range(10)) for value in ((False,True) if slot==5 else ('x','y'))}
                    assert seen==expected,(slot,variant,seen,expected)
                contrasts[str((sign,variant))]=actual[0]
            def unknown(*args):raise ValueError('Unknown prior officer witness')
            try:evaluated('prior_binding',doc,primitives=values|{'r323':unknown},individuals=('x','y'),situations=scenes)
            except ValueError as error:assert 'Unknown prior officer witness' in str(error)
            else:raise AssertionError(slot)
        rows.append(dict(slot=slot,independent_values=2,contrasts=contrasts))
    result=dict(slots=rows,current_existential_body_inspected=True,other_witnesses_instantiated=True,
        boundaries=['r323'],native_command_body_evaluated_here=False,full_cartesian_domain_enumerated=False,unbounded_equivalence_proved=False)
    RESULTS['prior_binding']=result
    return result


@lru_cache(None)
def slotwise_binding_checks():
    from noema.constructed_semantics import Content
    from scripts.shared_modality import call
    point,variables,inner=conditional_parts();fixed=('x','y','x','y','x','y','x','y','x');scenes=('reference','other');rows=[]
    for slot in range(9):
        binds={n:call('jfixed'+'abcdefghi'[i]) for i,n in enumerate(variables) if i!=slot};binds[point]=call('jstart')
        body=dict(kind='forall',variable=variables[slot],sort='individual',body=substituted(inner,binds))
        doc=current_fixture([dict(kind='ask',body=body)],probe_constants(),('r33o','r33p'))
        target=list(fixed);target[slot]='y';target=tuple(target);contrasts={}
        for variant in ('baseline','missing_protection','wrong_reference','wrong_evaluation','empty_scope'):
            seen=set()
            def scope(*args):seen.add(args);return variant!='empty_scope' and args==(*target,'reference')
            def protection(*args):
                good=variant!='missing_protection' and args==(*target[2:],'other' if variant=='wrong_reference' else 'reference')
                return Content(scenes,tuple(good and s==('other' if variant=='wrong_evaluation' else 'reference') for s in scenes))
            values={'r33o':scope,'r33p':protection,'jstart':lambda:'reference','h232v':lambda:'reference'}
            values.update({'jfixed'+letter:(lambda value=fixed[i]:value) for i,letter in enumerate('abcdefghi')})
            actual=[r['value'] for r in evaluated('binding',doc,primitives=values,individuals=('x','y'),situations=scenes)]
            assert actual==[variant in ('baseline','empty_scope')],(slot,variant,actual)
            assert seen=={tuple(value if i==slot else fixed[i] for i in range(9))+('reference',) for value in ('x','y')}
            contrasts[variant]=actual[0]
        # Reset a nonempty scope so required unknown consequences are exercised.
        values['r33o']=lambda *args:args==(*target,'reference')
        def unknown(*args):raise ValueError('Unknown protected remarks binding')
        for name in ('r33o','r33p'):
            try:evaluated('binding',doc,primitives=values|{name:unknown},individuals=('x','y'),situations=scenes)
            except ValueError as error:assert 'Unknown protected remarks binding' in str(error)
            else:raise AssertionError((slot,name))
        rows.append(dict(slot=slot,independent_values=2,contrasts=contrasts))
    result=dict(slots=rows,current_conditional_and_scope_join_inspected=True,other_arguments_instantiated=True,
        boundaries=['r33o','r33p'],native_components_evaluated_here=False,full_cartesian_domain_enumerated=False,unbounded_equivalence_proved=False)
    RESULTS['binding']=result
    return result


def whole_fixture():
    from scripts.shared_modality import call
    point,variables,inner=conditional_parts()
    binds={n:call('jfixed'+'abcdefghi'[i]) for i,n in enumerate(variables)};binds[point]=call('jstart')
    conditional=substituted(inner,binds);scope_args=conditional['arguments'][0]['arguments']
    join=recovered()['r33o'];scope=substituted(join['body'],{p['name']:a for p,a in zip(join['parameters'],scope_args,strict=True)})
    params,witnesses,prior_inner=prior_parts();prior_args=scope['arguments'][0]['arguments']
    bindings=dict(zip(params,prior_args,strict=True));bindings.update({n:call('jwitness'+'abcde'[i]) for i,n in enumerate(witnesses[:5])});bindings[witnesses[5]]=call('jsign')
    prior=substituted(prior_inner,bindings);scope['arguments'][0]=prior
    # This is an explicitly witnessed expansion, not a replacement declaration.
    # Original r33n/r33o/r33q remain unchanged and are retained by discourse checks.
    conditional['arguments'][0]=scope
    statements=[dict(kind='ask',body=deepcopy(n)) for n in (prior,scope['arguments'][1],conditional['arguments'][1],conditional)]
    return current_fixture(statements,probe_constants())


@lru_cache(None)
def whole_content_checks():
    from noema.constructed_semantics import FunctionValue
    from scripts import check_military_remarks as remarks
    from scripts import check_officer_command_binding as officer
    from scripts.check_motive_causes import unknown,symbol
    doc=whole_fixture();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[n]==recovered()[n] for n in ('r323','r33c','r33b','r33a','r33p','r33m'))
    fixed=('office','institution','person','making','presenting','scholar','notes','audience','field')
    witnesses=('issuer','higher','notice','action','work')
    domain=tuple(dict.fromkeys((*officer.DOMAIN,*remarks.DOMAIN,'work','mechanism','community','regulator','secondregulator','standard','policy')))
    scenes=('reference','other')
    def model(sign,variant='baseline',mismatch=None):
        values=officer.model(doc,sign=sign)
        candidate=remarks.candidate_model(doc)
        for name in ('ca','cb','cd','cc','ce','h243w','h243x','h243y','h242g','h243z','hztl'):values[name]=candidate[name]
        values.update(h244a=lambda field,institution,ref:(field,institution,ref)==('field','institution','reference'),
            h237y=lambda work,ref:(work,ref)==('work','reference'),h237h=lambda w,r:'mechanism',h237i=lambda w,r:'community',
            h237d=lambda m,w,r:FunctionValue(('individual',),'truth',lambda p:p=='person'),
            h237c=lambda p,c,r:(p,c,r)==('person','community','reference'),h237e=lambda p,m,w,r:'office',
            h237f=lambda *args:args==('person','office','mechanism','work','reference'),
            h237x=lambda *args:variant!='no_prior' and args==('person','office','work','action','reference'),
            h244d=lambda ref:'standard' if ref=='reference' else 'other',
            h235r=lambda regulator,ref:'policy' if regulator in ('regulator','secondregulator') and ref=='reference' else 'other',
            h244e=lambda regulator,ref:variant!='no_regulators' and ref=='reference' and regulator in ('regulator','secondregulator'))
        if variant=='empty_notes':values['h243w']=lambda *args:False
        expected={'r33j':('person','scholar','making','notes'),
            'r33k':('person','scholar','presenting','notes','audience'),
            'r33l':('person','scholar','making','presenting','notes','audience')}
        absent={'allow_making_ban':'r33j','allow_submission_ban':'r33k','allow_joint_ban':'r33l'}.get(variant)
        def requirement(source,regulator,role,code,bindings,ref,sign,point):
            name=symbol(code)
            if name not in expected:raise ValueError('Unknown protected remarks requirement target')
            return name!=absent and not (variant=='second_unprotected' and regulator=='secondregulator') and regulator in ('regulator','secondregulator') and (
                source,role,code.rank,tuple(bindings.items),ref,sign,point)==(
                    'other' if variant=='wrong_standard' else 'standard','policy',1,(regulator,*expected[name]),'reference',variant=='wrong_polarity',
                    'other' if variant=='wrong_evaluation' else 'reference')
        values['h237z']=requirement
        values.update({'jfixed'+letter:(lambda value='other' if mismatch==i else fixed[i]:value) for i,letter in enumerate('abcdefghi')})
        values.update({'jwitness'+letter:(lambda value=witnesses[i]:value) for i,letter in enumerate('abcde')})
        values.update(jsign=lambda:sign,jstart=lambda:'reference',h232v=lambda:'reference')
        for name in ('cg','h7k','h244b','h244c','h243u','h243v','h6t','fa','fb'):
            if name in values:assert values[name] is unknown,name
        return values
    def run(values):
        return [r['value'] for r in evaluated('whole',doc,primitives=values,individuals=domain,situations=scenes,
            max_steps=100000000,memoize_definitions=True,memoize_expressions=True)]
    rows={}
    for sign in (False,True):
        for variant in ('baseline','allow_making_ban','allow_submission_ban','allow_joint_ban','second_unprotected',
                        'wrong_standard','wrong_polarity','wrong_evaluation','no_regulators','no_prior','empty_notes'):
            prior=variant!='no_prior';candidate=variant!='empty_notes'
            protected=variant in ('baseline','no_regulators','no_prior','empty_notes')
            expected=[prior,candidate,protected,not(prior and candidate) or protected]
            actual=run(model(sign,variant));assert actual==expected,(sign,variant,actual,expected)
            rows[str((sign,variant))]=actual
    mismatches={}
    for slot,name in enumerate(fixed):
        expected=[slot not in (0,1,2),False,slot in (0,1,8),True]
        actual=run(model(True,mismatch=slot));assert actual==expected,(slot,name,actual,expected)
        mismatches[name]=actual
    for name in ('h242v','h243x','h244a','h244d','h244e','h237z'):
        try:run(model(True)|{name:unknown})
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    result=dict(contrasts=rows,argument_mismatches=mismatches,current_witnessed_scope_and_protection_connected=True,
        actual_command_candidate_and_regulator_bodies_evaluated=True,two_regulators_and_three_separate_protections=True,
        command_execution_remarks_execution_defect_truth_and_public_judgment_not_evaluated=True,
        false_scope_and_empty_regulator_scope_are_vacuous=True,prior_witnesses_and_outer_arguments_instantiated=True,
        original_source_definitions_unmodified=True,full_existential_and_universal_domains_not_proved=True,unbounded_equivalence_proved=False)
    RESULTS['whole']=result
    return result


def build_report():
    prior_binding_checks();slotwise_binding_checks();whole_content_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-protected-remarks-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
