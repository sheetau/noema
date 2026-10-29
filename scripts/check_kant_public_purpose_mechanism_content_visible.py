"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_public_purpose_mechanism_visible as check

CONTROLS='data/kant-public-purpose-mechanism-visible-diagnostic-controls-v1.json'
GROUPS={'purpose': ('scripts.check_public_purpose_mechanism',
             'reports/public-purpose-mechanism-v1.json',
             [['target_checks', 'target'],
              ['means_checks', 'means'],
              ['purpose_checks', 'purpose'],
              ['discourse_checks', 'discourse']]),
 'requirements': ('scripts.check_mechanism_requirements',
                  'reports/mechanism-requirements-v1.json',
                  [['passive_checks', 'passive'], ['requirements_checks', 'requirements']]),
 'coordination': ('scripts.check_institutional_coordination',
                  'reports/institutional-coordination-v1.json',
                  [['alternatives_checks', 'alternatives'], ['binding_checks', 'bindings']])}
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
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_public_purpose_mechanism_content_visible.py',
        'tests/test_kant_public_purpose_mechanism_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def whole_fixture(kind):
    from noema.constructed import parse
    purpose=namespace('purpose');requirements=namespace('requirements')
    source={d['name']:deepcopy(d) for d in check.source_excerpt()['declarations']}
    # Providers return explicit closed descriptions. All source definitions,
    # especially r2zx, retain their recovered bodies.
    for doc in (requirements['fixture']('requirements'),purpose['fixture']('purpose')):
        for d in doc['declarations']:
            if d['name'] not in source or d['name'] in ('h232f','h237k'):source[d['name']]=deepcopy(d)
    if kind=='whole':statements=deepcopy(purpose['fixture']('purpose')['statements'])
    else:
        statements=[dict(kind='ask',body=dict(kind='evaluate',content=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in ('zwork','zreference')]),situation=dict(kind='call',symbol='zpoint',arguments=[]))) for name in ('r2zt','r2zw')]
    result=[];seen=set();visiting=set()
    def visit(name):
        if name in seen:return
        assert name not in visiting,('Dependency cycle',name)
        visiting.add(name);d=source[name]
        for dependency in sorted(_references(d.get('body'))):visit(dependency)
        visiting.remove(name);seen.add(name);result.append(d)
    for name in sorted(_references(statements)):visit(name)
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=result,statements=statements)


@lru_cache(None)
def whole_content_checks():
    purpose=namespace('purpose');requirements=namespace('requirements')
    domain=tuple(dict.fromkeys((*purpose['DOMAIN'],*requirements['DOMAIN'])))
    scenes=purpose['SCENES'];doc=whole_fixture('whole')
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[n]==recovered()[n] for n in ('r2zx','r3c','r3d'))
    def run(document,values):
        return [r['value'] for r in evaluated('whole',document,primitives=values,individuals=domain,situations=scenes,
            max_steps=10000000,memoize_definitions=True,memoize_expressions=True)]
    def model(requirement='baseline',purpose_variant='baseline'):
        pv=purpose['purpose_model'](purpose_variant);rv=requirements['requirements_model'](requirement)
        values=pv|rv
        for name in ('h237l','h237u','h237m','h237n','h237o','zgoalcode','zgoal','zothergoal','zpoint'):values[name]=pv[name]
        values.pop('r2zx',None)
        return values
    cases={}
    for requirement,purpose_variant in [('baseline','baseline'),('multiple_works','baseline'),
        ('no_necessity','baseline'),('empty_members','baseline'),('no_role_requirement','baseline'),
        ('assignment_other_role','baseline'),('wrong_role_target','baseline'),('norm_source_conflated','baseline'),
        ('wrong_requirement_state','baseline'),('baseline','private_goal_only'),('baseline','missing_purpose'),
        ('baseline','purpose_reversed'),('baseline','purpose_other_work'),('baseline','public_goal_other_community')]:
        actual=run(doc,model(requirement,purpose_variant));expected=requirement in ('baseline','multiple_works') and purpose_variant=='baseline'
        assert actual==[expected,expected],(requirement,purpose_variant,actual)
        cases[requirement+'/'+purpose_variant]=actual
    def unknown(*args):raise ValueError('Unknown whole mechanism input')
    for name in ('h237a','h237b','h237s','h237t','h236x','h236z','zgoal'):
        assert run(doc,model()|{name:unknown})==[True,True]
    for name in ('h232e','h7k','h237l','h237u','zrequiredcode','zgoalcode'):
        try:run(doc,model()|{name:unknown})
        except ValueError as error:assert 'Unknown whole mechanism input' in str(error)
        else:raise AssertionError(name)
    direct=whole_fixture('direct');direct_rows={}
    def direct_model(variant):
        values={d['name']:unknown for d in direct['declarations'] if d['kind']=='primitive'}
        values.update(zwork=lambda:'otherwork' if variant=='other_work' else 'work',
            zreference=lambda:'other' if variant=='other_reference' else 'reference',
            zpoint=lambda:'reference' if variant=='other_point' else 'future',
            h237h=lambda w,r:'mechanism' if (w,r)==('work','reference') and variant!='other_mechanism' else 'other',
            h236x=lambda w,p:variant!='no_performance' and (w,p)==('work','future'),
            h236z=lambda m,w,p:variant!='no_supply' and (m,w,p)==('mechanism','work','future'))
        return values
    expected={'baseline':[True,True],'other_work':[False,False],'other_reference':[True,False],
        'other_point':[False,False],'other_mechanism':[True,False],'no_performance':[False,True],'no_supply':[True,False]}
    for variant,wanted in expected.items():
        actual=run(direct,direct_model(variant));assert actual==wanted,(variant,actual);direct_rows[variant]=actual
    for name in ('h236x','h237h','h236z'):
        try:run(direct,direct_model('baseline')|{name:unknown})
        except ValueError as error:assert 'Unknown whole mechanism input' in str(error)
        else:raise AssertionError(name)
    result=dict(whole_requirements_and_purpose=cases,actual_work_and_supply=direct_rows,
        r2zx_body_retained=True,required_and_purpose_contents_not_executed=True,
        direct_content_binding_diagnostics=True,unbounded_equivalence_proved=False)
    RESULTS['whole']=result
    return result


def build_report():
    whole_content_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-public-purpose-mechanism-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
