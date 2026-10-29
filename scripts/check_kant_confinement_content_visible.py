"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_confinement_visible as check

CONTROLS='data/kant-confinement-visible-diagnostic-controls-v1.json'
GROUPS={'reading': ('scripts.check_guarded_walking_reading',
             'reports/guarded-walking-reading-v1.json',
             [['interface_checks', 'interfaces']]),
 'modal': ('scripts.check_modal_prevention',
           'reports/modal-prevention-v1.json',
           [['scope_checks', 'scope'], ['binding_checks', 'binding'], ['unknown_checks', 'unknowns']]),
 'prior': ('scripts.check_prior_confinement',
           'reports/prior-confinement-v1.json',
           [['generic_checks', 'generic'], ['native_checks', 'native'], ['source_checks', 'source']]),
 'quiet': ('scripts.check_quiet_depiction',
           'reports/quiet-depiction-v1.json',
           [['local_checks', 'local'], ['motor_checks', 'motor'], ['source_checks', 'source']]),
 'insistence': ('scripts.check_insistent_framing',
                'reports/insistent-framing-v1.json',
                [['generic_checks', 'generic'],
                 ['scope_checks', 'scope'],
                 ['source_checks', 'source'],
                 ['norm_checks', 'norms']]),
 'warning': ('scripts.check_walking_warning',
             'reports/walking-warning-v1.json',
             [['generic_checks', 'generic'], ['scope_checks', 'scope'], ['source_checks', 'source']]),
 'quantified': ('scripts.check_quantified_step_goals',
                'reports/quantified-step-goals-v1.json',
                [['generic_checks', 'generic'],
                 ['physical_checks', 'physical'],
                 ['undertaking_checks', 'undertaking'],
                 ['norm_checks', 'norms']]),
 'step': ('scripts.check_grounded_step',
          'reports/grounded-step-v1.json',
          [['generic_checks', 'generic'],
           ['source_checks', 'source'],
           ['binding_checks', 'bindings'],
           ['norm_checks', 'norms']]),
 'depiction': ('scripts.check_step_depiction',
               'reports/step-depiction-v1.json',
               [['embedding_checks', 'embedding'], ['target_checks', 'target'], ['body_checks', 'body']]),
 'attention': ('scripts.check_careful_prevention',
               'reports/careful-prevention-v1.json',
               [['generic_checks', 'generic'], ['goal_checks', 'goal'], ['source_checks', 'source']]),
 'husbandry': ('scripts.check_husbandry_depiction',
               'reports/husbandry-depiction-v1.json',
               [['generic_checks', 'generic'],
                ['binding_checks', 'bindings'],
                ['source_checks', 'source'],
                ['target_checks', 'target_bindings'],
                ['attribution_checks', 'attribution']])}
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
    engine=finite_evaluate if group=='husbandry' else constructed_evaluate
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
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_confinement_content_visible.py',
        'tests/test_kant_confinement_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def current_integration():
    """Execute current husbandry composition after rab was renamed to zza."""
    from noema.constructed_semantics import SequenceValue
    from noema.finite_semantics import SequenceValue as LegacySequence
    original=importlib.import_module('scripts.check_husbandry_depiction')
    current=deepcopy(check.backprojection(check.restored()['document']))
    current['statements']=[]
    current=check.parse(check.format_graph(current,'compact')+
        'r jtestedperson[] a.r jtestedscene[] d.'+
        'q[t[k qj[k jtestedperson[]]][k jtestedscene[]]].'+
        'q[t[k qk[k jtestedperson[]]][k jtestedscene[]]].q[k qq[]].')
    def adapt(fn):
        def call(*args):
            value=fn(*args)
            return SequenceValue(value.items,value.element_type) if isinstance(value,LegacySequence) else value
        return call
    rows={}
    for variant in ('baseline','rotating_keepers','actual_human','not_animal','unowned','foreign_owner',
            'foreign_keeper','nonhuman_keepers','split_roles','wrong_being','missing_middle',
            'missing_maintenance','missing_management','missing_purpose','single_point'):
        values={name:adapt(fn) for name,fn in original.source_model(current,variant).items()}
        values.update(jtestedperson=lambda:'person',jtestedscene=lambda:'actual')
        result=evaluated('current',current,primitives=values,individuals=original.DOMAIN,situations=original.SCENES,
            max_steps=5000000,memoize_definitions=True,memoize_expressions=True)
        actual=[r['value'] for r in result]
        assert actual==[variant=='actual_human',variant in ('baseline','rotating_keepers'),True],(variant,actual)
        rows[variant]=actual
    assert not HISTORICAL_COMPARISONS.get('current')
    assert {'qj','qk','qq','zza'}<=RECOVERED_DEFINITIONS['current']
    RESULTS['current']=dict(contrasts=rows,current_husbandry_composed=True,historical_bodies_used=False,
        scope='Finite contrasts on exact current source; not a proof over all interpretations.')
    return RESULTS['current']


def build_report():
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    if 'current' not in RESULTS:current_integration()
    return dict(schema='noema-kant-confinement-content-visible-check-1',results=RESULTS,
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
