"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType
import importlib
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_guardians_visible as check

CONTROLS='data/kant-guardians-visible-diagnostic-controls-v1.json'
GROUPS={'reading': ('scripts.check_guardian_reading',
             'reports/guardian-reading-v1.json',
             [('generic_checks', 'generic'),
              ('scope_checks', 'scope'),
              ('source_checks', 'source'),
              ('fact_checks', 'facts')]),
 'benevolent': ('scripts.check_benevolent_framing',
                'reports/benevolent-framing-v1.json',
                [('action_checks', 'action'), ('frame_checks', 'frame'), ('source_checks', 'source')]),
 'rank': ('scripts.check_supervisory_rank',
          'reports/supervisory-rank-v1.json',
          [('order_checks', 'order'), ('source_checks', 'source')]),
 'purpose': ('scripts.check_guardian_purpose',
             'reports/guardian-purpose-v1.json',
             [('purpose_checks', 'purpose'), ('source_checks', 'source')]),
 'causation': ('scripts.check_guardian_causation',
               'reports/guardian-causation-v1.json',
               [('causal_checks', 'causal'), ('majority_checks', 'majority')]),
 'appraisal': ('scripts.check_described_appraisals',
               'reports/described-appraisals-v1.json',
               [('generic_checks', 'judgment_candidates'), ('prospect_checks', 'prospects')])}
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
        if name in fixture_controls:
            assert d==fixture_controls[name],('Unexpected fixture body',group,name)
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
    engine=finite_evaluate if group=='appraisal' else constructed_evaluate
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
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_guardians_content_visible.py',
        'tests/test_kant_guardians_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def current_integration():
    """Execute the current full supervision composition, including refactored di."""
    rank=importlib.import_module('scripts.check_supervisory_rank')
    benevolent=importlib.import_module('scripts.check_benevolent_framing')
    current=deepcopy(check.backprojection(check.restored()['document']))
    current['statements']=[]
    current=check.parse(check.format_graph(current,'compact')+'r zc[] d.q[t[k do[k db[]]][k zc[]]].')
    rows={}
    for variant in ('baseline','lower_in_all_assignments','different_position'):
        values=benevolent.source_values(variant)
        result=evaluated('current',current,primitives=values,individuals=rank.PEOPLE,situations=rank.SCENES,
            # Match the retained rank/purpose evaluator's existing budget.
            max_steps=100000000,memoize_definitions=True,memoize_expressions=True)
        actual=[r['value'] for r in result]
        assert actual==[variant=='baseline'],(variant,actual)
        rows[variant]=actual
    assert not HISTORICAL_COMPARISONS.get('current')
    assert {'di','do','rqyl','rqyg','rqyd','rqyj'}<=RECOVERED_DEFINITIONS['current']
    RESULTS['current']=dict(contrasts=rows,current_di_and_purpose_causation_composed=True,
        historical_bodies_used=False,scope='Finite contrasts on exact current source; not a proof over all interpretations.')
    return RESULTS['current']


def build_report():
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    if 'current' not in RESULTS:current_integration()
    return dict(schema='noema-kant-guardians-content-visible-check-1',results=RESULTS,
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
