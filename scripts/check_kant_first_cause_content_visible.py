"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType
import importlib
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_first_cause_visible as check

CONTROLS='data/kant-first-cause-visible-diagnostic-controls-v1.json'
GROUPS={
    'cause':('scripts.check_first_cause_reading','reports/first-cause-reading-v1.json',
        [('population_checks','population'),('composition_checks','composition'),('attribution_checks','attribution')]),
    'motives':('scripts.check_evaluated_motives','reports/evaluated-motives-v1.json',[('motive_checks','motives')]),
    'past':('scripts.check_relative_past','reports/relative-past-v1.json',[('generic_checks','generic'),('source_checks','source')]),
    'attitude':('scripts.check_scoped_attitude','reports/scoped-attitude-v1.json',[('scope_checks','scopes')]),
    'concession':('scripts.check_concession','reports/concession-v1.json',[('expectation_checks','expectations')])}
RESULTS={}
RECOVERED_DEFINITIONS={}
ABSTRACTED_DEFINITIONS={}
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
    for index,d in enumerate(actual['declarations']):
        if d['kind']!='definition':continue
        name=d['name']
        if name in recovered():
            if d!=recovered()[name]:
                assert controls.get(name)==d,('Unexpected source-body difference',group,name)
                ABSTRACTED_DEFINITIONS.setdefault(group,set()).add(name)
            else:
                actual['declarations'][index]=deepcopy(recovered()[name])
                RECOVERED_DEFINITIONS.setdefault(group,set()).add(name)
        else:FIXTURE_ONLY_DEFINITIONS.setdefault(group,set()).add(name)
    selected={d['name']:primitives[d['name']] for d in actual['declarations'] if d['kind']=='primitive'}
    engine=finite_evaluate if group=='concession' else constructed_evaluate
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
    assert result==check.read(GROUPS[group][1])[key],('Retained result differs',group,function)
    RESULTS.setdefault(group,{})[key]=result
    return result


def source_pins():
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_first_cause_content_visible.py',
        'tests/test_kant_first_cause_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}


def build_report():
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-first-cause-content-visible-check-1',results=RESULTS,
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        explicit_abstractions={k:sorted(v) for k,v in ABSTRACTED_DEFINITIONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '抽象化した下位条件と過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
