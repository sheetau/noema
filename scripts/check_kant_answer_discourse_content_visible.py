"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_answer_discourse_visible as check

CONTROLS='data/kant-answer-discourse-visible-diagnostic-controls-v1.json'
GROUPS={'answer': ('scripts.check_answer_discourse',
            'reports/answer-discourse-v1.json',
            [['split_checks', 'split'], ['content_checks', 'contents'], ['discourse_checks', 'discourse']]),
 'duty': ('scripts.check_public_freedom_duty',
          'reports/public-freedom-duty-v1.json',
          [['period_checks', 'period'],
           ['adapter_checks', 'adapter'],
           ['norm_checks', 'norm'],
           ['attribution_checks', 'attribution']]),
 'route': ('scripts.check_public_enlightenment_route',
           'reports/public-enlightenment-route-v1.json',
           [['episode_checks', 'episode'],
            ['part_checks', 'part'],
            ['quantifier_checks', 'quantifiers'],
            ['combined_checks', 'combined'],
            ['claim_checks', 'claim']]),
 'choices': ('scripts.check_private_choice_frequency',
             'reports/private-choice-frequency-v1.json',
             [['degree_checks', 'degree'],
              ['frequency_checks', 'frequency'],
              ['quotation_checks', 'quotation']]),
 'qualified': ('scripts.check_qualified_private_influence',
               'reports/qualified-private-influence-v1.json',
               [['extent_checks', 'extent'],
                ['matched_checks', 'matched'],
                ['native_checks', 'native'],
                ['policy_checks', 'policy']]),
 'permission': ('scripts.check_private_policy_permission',
                'reports/private-policy-permission-v1.json',
                [['binding_checks', 'bindings'],
                 ['scope_checks', 'scope'],
                 ['norm_checks', 'norm'],
                 ['attribution_checks', 'attribution']])}
STRUCTURAL_WITNESSES=set()
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
    ns=namespace(group)
    original_fixture=ns['fixture'];original_catalog=ns['catalog']
    def bound_fixture(kind,*args,**kwargs):
        doc=original_fixture(kind,*args,**kwargs)
        if kind=='quote':
            doc=adapted(group,doc,['zquote'])
            STRUCTURAL_WITNESSES.update(d['name'] for d in doc['declarations']
                if d['kind']=='definition' and d['name'] in recovered() and d==recovered()[d['name']])
        return doc
    if group in ('choices','qualified'):ns['fixture']=bound_fixture
    if group=='answer' and function=='split_checks':
        original=original_catalog();entries=deepcopy(original.entries)
        for name in ('r2yz','r2zb','r2zc'):
            assert entries[name]['declaration']==recovered()[name]
            entries[name]['declaration']=deepcopy(recovered()[name])
            STRUCTURAL_WITNESSES.add(name)
        ns['catalog']=lambda:SimpleNamespace(document=original.document,entries=entries)
    try:result=ns[function]()
    finally:ns['fixture']=original_fixture;ns['catalog']=original_catalog
    if function!='quotation_checks':
        assert EVALUATION_CALLS.get(group,0)>before,('No recovered-body evaluation',group,function)
    # Reports store tuples as JSON arrays; compare in that persisted format.
    # All finite-model assertions above still execute on their native values.
    result=json.loads(json.dumps(result,ensure_ascii=False))
    assert result==check.read(GROUPS[group][1])[key],('Retained result differs',group,function)
    RESULTS.setdefault(group,{})[key]=result
    return result


def source_pins():
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_answer_discourse_content_visible.py',
        'tests/test_kant_answer_discourse_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def build_report():
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-answer-discourse-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=sorted(STRUCTURAL_WITNESSES),
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
