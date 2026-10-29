"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_conditional_visible as check

CONTROLS='data/kant-conditional-visible-diagnostic-controls-v1.json'
GROUPS={'reading': ('scripts.check_fourth_sentence',
             'reports/fourth-sentence-v1.json',
             [['reference_checks', 'reference'],
              ['bodily_checks', 'bodily'],
              ['mapping_checks', 'mapping']]),
 'limited': ('scripts.check_limited_consequence',
             'reports/limited-consequence-v1.json',
             [['exclusion_checks', 'exclusion'],
              ['profile_checks', 'profile'],
              ['concession_checks', 'concession'],
              ['package_checks', 'package'],
              ['attribution_checks', 'attribution'],
              ['quotation_checks', 'quotation'],
              ['native_checks', 'native']]),
 'minimum': ('scripts.check_minimum_challenge',
             'reports/minimum-challenge-v1.json',
             [['minimum_checks', 'minimum'],
              ['expectation_checks', 'expectation']]),
 'unfamiliar': ('scripts.check_unfamiliar_judgment',
                'reports/unfamiliar-judgment-v1.json',
                [['kind_checks', 'kind'],
                 ['familiarity_checks', 'familiarity'],
                 ['cause_checks', 'cause'],
                 ['native_checks', 'native']]),
 'reference': ('scripts.check_depicted_referents',
               'reports/depicted-referents-v1.json',
               [['range_checks', 'ranges'], ['person_checks', 'people']]),
 'departure': ('scripts.check_abandoned_reliance',
               'reports/abandoned-reliance-v1.json',
               [['profile_checks', 'profile'],
                ['transition_checks', 'transition'],
                ['source_checks', 'source'],
                ['capacity_checks', 'capacity']]),
 'uncertain': ('scripts.check_uncertain_judgment',
               'reports/uncertain-judgment-v1.json',
               [['profile_checks', 'profile'],
                ['judgment_checks', 'judgment']]),
 'release': ('scripts.check_conditional_release',
             'reports/conditional-release-v1.json',
             [['minimum_checks', 'minima'], ['release_checks', 'release']]),
 'familiarity': ('scripts.check_learned_familiarity',
                 'reports/learned-familiarity-v1.json',
                 [['generic_checks', 'generic'],
                  ['movement_checks', 'movement']])}
RESULTS={}
RECOVERED_DEFINITIONS={}
HISTORICAL_COMPARISONS={}
FIXTURE_ONLY_DEFINITIONS={}


@lru_cache(None)
def recovered():
    return {d['name']:d for d in check.backprojection(check.restored()['document'])['declarations'] if d['kind']=='definition'}


def evaluated(group,doc,*,primitives,**options):
    ds={d['name']:d for d in doc['declarations']};needed=set();pending=_references(doc['statements'])
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.update(_references(ds[name].get('body')))
    actual=deepcopy(doc);actual['declarations']=[d for d in actual['declarations'] if d['name'] in needed]
    controls=check.read(CONTROLS)['groups'].get(group,{})
    fixture_controls=check.read(CONTROLS).get('fixture_only_controls',{}).get(group,{})
    for index,d in enumerate(actual['declarations']):
        if d['kind']!='definition':continue
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
    engine=finite_evaluate if group in ('release','familiarity') else constructed_evaluate
    return engine(actual,primitives=selected,**options)


@lru_cache(None)
def namespace(group):
    original=importlib.import_module(GROUPS[group][0]);ns=dict(vars(original))
    for name,wrapped in vars(original).items():
        fn=getattr(wrapped,'__wrapped__',wrapped)
        if isinstance(fn,FunctionType) and (fn.__module__==original.__name__ or name=='evaluate'):
            copied=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__);copied.__kwdefaults__=fn.__kwdefaults__
            ns[name]=lru_cache(None)(copied) if hasattr(wrapped,'cache_info') else copied
    ns['evaluate_document']=lambda doc,**kwargs:evaluated(group,doc,**kwargs)
    return ns


def replay(group,function,key):
    result=namespace(group)[function]()
    # Reports store tuples as JSON arrays; compare in that persisted format.
    # All finite-model assertions above still execute on their native values.
    result=json.loads(json.dumps(result,ensure_ascii=False))
    assert result==check.read(GROUPS[group][1])[key],('Retained result differs',group,function)
    RESULTS.setdefault(group,{})[key]=result
    return result


def source_pins():
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_conditional_content_visible.py',
        'tests/test_kant_conditional_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def build_report():
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-conditional-content-visible-check-1',results=RESULTS,
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
