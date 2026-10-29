"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_public_reversal_visible as check

CONTROLS='data/kant-public-reversal-visible-diagnostic-controls-v1.json'
GROUPS={'sentence': ('scripts.check_public_third_sentence',
              'reports/public-third-sentence-v1.json',
              [['attribution_checks', 'attribution']]),
 'retention': ('scripts.check_collective_retention',
               'reports/collective-retention-v1.json',
               [['causal_checks', 'causal'],
                ['source_checks', 'source'],
                ['quote_checks', 'quotation']]),
 'reversal': ('scripts.check_public_reversal',
              'reports/public-reversal-v1.json',
              [['prior_checks', 'prior_action'],
               ['incitation_checks', 'incitation'],
               ['reversal_checks', 'reversal']]),
 'capacity': ('scripts.check_enlightenment_incapacity',
              'reports/enlightenment-incapacity-v1.json',
              [['capacity_checks', 'capacity'],
               ['source_checks', 'source'],
               ['role_checks', 'roles'],
               ['integration_checks', 'integration']]),
 'incitation': ('scripts.check_public_incitation',
                'reports/public-incitation-v1.json',
                [['component_checks', 'components'],
                 ['group_checks', 'group'],
                 ['quotation_checks', 'quotation'],
                 ['integration_checks', 'integration']]),
 'attribution': ('scripts.check_reversal_attribution',
                 'reports/reversal-attribution-v1.json',
                 [['scope_checks', 'scope'],
                  ['supply_checks', 'supply'],
                  ['quantified_checks', 'quantification'],
                  ['attribution_checks', 'attribution']]),
 'yoke': ('scripts.check_reversal_yoke',
          'reports/reversal-yoke-v1.json',
          [['depiction_checks', 'depiction'],
           ['generalized_checks', 'generalization'],
           ['family_checks', 'families'],
           ['attribution_checks', 'attribution']]),
 'focus': ('scripts.check_reversal_focus',
           'reports/reversal-focus-v1.json',
           [['conditional_checks', 'conditional'],
            ['family_checks', 'families'],
            ['attribution_checks', 'attribution']]),
 'effects': ('scripts.check_prejudice_effects',
             'reports/prejudice-effects-v1.json',
             [['judgment_checks', 'judgment'],
              ['instilling_checks', 'instilling'],
              ['adverse_checks', 'adverse_effect'],
              ['return_checks', 'return']]),
 'claim': ('scripts.check_prejudice_claim',
           'reports/prejudice-claim-v1.json',
           [['terminal_checks', 'terminal'],
            ['case_checks', 'cases'],
            ['scope_checks', 'scope'],
            ['focus_checks', 'focus'],
            ['attribution_checks', 'attribution']]),
 'reason': ('scripts.check_prejudice_reason',
            'reports/prejudice-reason-v1.json',
            [['harm_checks', 'harm'],
             ['degree_checks', 'degree'],
             ['family_checks', 'family'],
             ['discourse_checks', 'discourse']]),
 'depictions': ('scripts.check_prejudice_depictions',
                'reports/prejudice-depictions-v1.json',
                [['planting_checks', 'planting'],
                 ['retaliation_checks', 'retaliation'],
                 ['binding_checks', 'binding'],
                 ['attribution_checks', 'attribution']])}
RESULTS={}
EVALUATION_CALLS={}
CERTIFICATE=None
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


def attachment_certificate():
    global CERTIFICATE
    if CERTIFICATE is not None:return CERTIFICATE
    original=importlib.import_module(GROUPS['focus'][0])
    ns=dict(namespace('focus'))
    selections={'parent':('r2nb','r2mv','r2mr','r2ne','r2mq'),'catalog':('r2nr','r2nv')}
    verified={}
    for provider,names in selections.items():
        source=getattr(original,provider)();entries=deepcopy(source.entries)
        for name in names:
            assert entries[name]['declaration']==recovered()[name],('Attachment source differs',name)
            entries[name]['declaration']=deepcopy(recovered()[name])
        view=SimpleNamespace(**(vars(source)|{'entries':entries}))
        ns[provider]=lambda view=view:view
        verified[provider]=list(names)
    fn=original.attachment_checks.__wrapped__
    result=FunctionType(fn.__code__,ns,fn.__name__,fn.__defaults__,fn.__closure__)()
    result=json.loads(json.dumps(result))
    assert result==check.read(GROUPS['focus'][1])['attachment']
    CERTIFICATE=dict(result=result,current_declarations=verified,
        classification='Exact recovered syntactic extraction and conditional binder attachment; not a full-domain semantic proof.')
    return CERTIFICATE


def source_pins():
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_public_reversal_content_visible.py',
        'tests/test_kant_public_reversal_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def build_report():
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-public-reversal-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        attachment_certificate=attachment_certificate(),
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
