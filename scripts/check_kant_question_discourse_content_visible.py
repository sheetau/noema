"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_question_discourse_visible as check

CONTROLS='data/kant-question-discourse-visible-diagnostic-controls-v1.json'
GROUPS={'discourse': ('scripts.check_question_discourse',
               'reports/question-discourse-v1.json',
               [['content_checks', 'contents'],
                ['discourse_checks', 'discourse'],
                ['quotation_checks', 'quotation']]),
 'questions': ('scripts.check_restriction_questions',
               'reports/restriction-questions-v1.json',
               [['row_checks', 'rows'],
                ['binding_checks', 'bindings'],
                ['extra_checks', 'extra'],
                ['question_checks', 'questions'],
                ['quotation_checks', 'quotation']]),
 'demands': ('scripts.check_demand_candidates',
             'reports/demand-candidates-v1.json',
             [['content_checks', 'contents'], ['anchor_checks', 'anchors'], ['scope_checks', 'scope']]),
 'aligned': ('scripts.check_aligned_influence',
             'reports/aligned-restriction-influence-v1.json',
             [['demand_checks', 'demands'], ['alignment_checks', 'alignment']]),
 'paired': ('scripts.check_paired_influence',
            'reports/paired-restriction-influence-v1.json',
            [['neutral_regression', 'neutral_regression'],
             ['matrix_checks', 'matrix'],
             ['guard_checks', 'guards'],
             ['alignment_checks', 'alignment']]),
 'extent': ('scripts.check_enlightenment_extent',
            'reports/enlightenment-extent-v1.json',
            [['extent_checks', 'extent'],
             ['order_checks', 'order'],
             ['guard_checks', 'guards'],
             ['callback_checks', 'callbacks'],
             ['integration_checks', 'integration'],
             ['native_profile_checks', 'native_profile']])}
STRUCTURAL_ROOTS={'discourse': ['r2ya', 'r2yb', 'r2xx', 'r2xy', 'r2xz'], 'questions': ['r2xv', 'r2xw', 'h232o']}
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
    if function=='quotation_checks':
        original_catalog=ns['catalog'];doc=deepcopy(original_catalog().document);doc['statements']=[]
        roots=STRUCTURAL_ROOTS[group];doc=adapted(group,doc,roots)
        declarations={d['name']:d for d in doc['declarations']}
        for name in roots:
            if name in recovered():
                assert declarations[name]==recovered()[name]
                STRUCTURAL_WITNESSES.add(name)
        ns['catalog']=lambda:SimpleNamespace(document=doc)
        try:result=ns[function]()
        finally:ns['catalog']=original_catalog
    else:
        result=ns[function]()
        assert EVALUATION_CALLS.get(group,0)>before,('No recovered-body evaluation',group,function)
    # Reports store tuples as JSON arrays; compare in that persisted format.
    # All finite-model assertions above still execute on their native values.
    result=json.loads(json.dumps(result,ensure_ascii=False))
    assert result==check.read(GROUPS[group][1])[key],('Retained result differs',group,function)
    RESULTS.setdefault(group,{})[key]=result
    return result


def source_pins():
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_question_discourse_content_visible.py',
        'tests/test_kant_question_discourse_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def build_report():
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-question-discourse-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=sorted(STRUCTURAL_WITNESSES),
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
