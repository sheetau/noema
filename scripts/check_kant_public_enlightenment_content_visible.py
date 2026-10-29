"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_public_enlightenment_visible as check

CONTROLS='data/kant-public-enlightenment-visible-diagnostic-controls-v1.json'
GROUPS={'core': ('scripts.check_public_comparison_claim',
          'reports/public-comparison-claim-v1.json',
          [['public_checks', 'public'],
           ['extent_checks', 'extent'],
           ['binding_checks', 'binding'],
           ['quantifier_checks', 'quantifiers'],
           ['attribution_checks', 'attribution']]),
 'sentence': ('scripts.check_public_first_sentence',
              'reports/public-first-sentence-v1.json',
              [['factoring_checks', 'factoring'],
               ['family_checks', 'families'],
               ['discourse_checks', 'discourse'],
               ['portability_checks', 'portability']]),
 'comparison': ('scripts.check_prospective_comparison',
                'reports/prospective-comparison-v1.json',
                [['individual_checks', 'individual'],
                 ['modal_checks', 'modal'],
                 ['attribution_checks', 'attribution']]),
 'future': ('scripts.check_prospective_liberty',
            'reports/prospective-liberty-v1.json',
            [['generic_checks', 'generic'],
             ['native_checks', 'native'],
             ['unknown_checks', 'unknowns']]),
 'collective': ('scripts.check_collective_change',
                'reports/collective-change-v1.json',
                [['generic_checks', 'generic'],
                 ['source_checks', 'source_cases']]),
 'permission': ('scripts.check_audience_liberty',
                'reports/audience-liberty-v1.json',
                [['generic_checks', 'generic'],
                 ['permission_checks', 'permission'],
                 ['native_checks', 'native']]),
 'modality': ('scripts.check_graded_modality',
              'reports/graded-modality-v1.json',
              [['checks', 'checks']])}
RESULTS={}
EVALUATION_CALLS={}
RECOVERED_DEFINITIONS={}
HISTORICAL_COMPARISONS={}
FIXTURE_ONLY_DEFINITIONS={}


@lru_cache(None)
def recovered():
    return {d['name']:d for d in check.backprojection(check.restored()['document'])['declarations'] if d['kind']=='definition'}


def evaluated(group,doc,*,primitives,**options):
    EVALUATION_CALLS[group]=EVALUATION_CALLS.get(group,0)+1
    ds={d['name']:d for d in doc['declarations']};needed=set();pending=_references(doc['statements'])
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
    selected={d['name']:primitives[d['name']] for d in actual['declarations'] if d['kind']=='primitive'}
    engine=constructed_evaluate
    return engine(actual,primitives=selected,**options)


@lru_cache(None)
def namespace(group):
    original=importlib.import_module(GROUPS[group][0]);ns=dict(vars(original))
    for name,wrapped in vars(original).items():
        fn=getattr(wrapped,'__wrapped__',wrapped)
        if isinstance(fn,FunctionType) and (fn.__module__==original.__name__ or name in ('evaluate','values')):
            copied=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__);copied.__kwdefaults__=fn.__kwdefaults__
            ns[name]=lru_cache(None)(copied) if hasattr(wrapped,'cache_info') else copied
    ns['evaluate_document']=lambda doc,**kwargs:evaluated(group,doc,**kwargs)
    if group in ('permission','future'):
        # Only these retained helpers call a nested module's evaluator. Copy
        # that module view so no historical evaluator is patched globally.
        prior=original.prior
        ns['prior']=SimpleNamespace(**vars(prior))
        leaf=prior if group=='permission' else prior.prior
        leaf_globals=dict(vars(leaf))
        leaf_globals['evaluate_document']=lambda doc,**kwargs:evaluated(group,doc,**kwargs)
        fn=leaf.evaluate
        wrapped=FunctionType(fn.__code__,leaf_globals,fn.__name__,fn.__defaults__,fn.__closure__)
        wrapped.__kwdefaults__=fn.__kwdefaults__
        if group=='permission':ns['prior'].evaluate=wrapped
        else:
            ns['prior'].prior=SimpleNamespace(**vars(leaf))
            ns['prior'].prior.evaluate=wrapped
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
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_public_enlightenment_content_visible.py',
        'tests/test_kant_public_enlightenment_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def build_report():
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-public-enlightenment-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
