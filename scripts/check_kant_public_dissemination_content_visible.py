"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_public_dissemination_visible as check

CONTROLS='data/kant-public-dissemination-visible-diagnostic-controls-v1.json'
GROUPS={'sentence': ('scripts.check_public_second_sentence',
              'reports/public-second-sentence-v1.json',
              [['achievement_checks', 'achievement'],
               ['attribution_checks', 'attribution'],
               ['portability_checks', 'portability']]),
 'content': ('scripts.check_dissemination_content',
             'reports/dissemination-content-v1.json',
             [['state_checks', 'state'],
              ['binding_checks', 'binding'],
              ['witness_checks', 'witnesses']]),
 'forecast': ('scripts.check_guardian_forecast',
              'reports/guardian-forecast-v1.json',
              [['crowd_checks', 'crowd'],
               ['appointment_checks', 'appointment'],
               ['package_checks', 'package'],
               ['aggregation_checks', 'aggregation'],
               ['attribution_checks', 'attribution']]),
 'opportunities': ('scripts.check_dissemination_opportunities',
                   'reports/dissemination-opportunities-v1.json',
                   [['opportunity_checks', 'opportunities'],
                    ['connection_checks', 'connection']]),
 'yoke': ('scripts.check_yoke_depiction',
          'reports/yoke-depiction-v1.json',
          [['physical_checks', 'physical'],
           ['release_checks', 'release'],
           ['attribution_checks', 'attribution']]),
 'receipt': ('scripts.check_qualitative_receipt',
             'reports/qualitative-receipt-v1.json',
             [['generic_checks', 'generic'],
              ['response_checks', 'responses'],
              ['route_checks', 'routes']]),
 'appraisal': ('scripts.check_reasoned_self_appraisal',
               'reports/reasoned-self-appraisal-v1.json',
               [['generic_checks', 'generic'],
                ['source_checks', 'source'],
                ['goal_checks', 'goal'],
                ['change_checks', 'change'],
                ['unknown_checks', 'unknowns']])}
RESULTS={}
EVALUATION_CALLS={}
WITNESS_CALLS={}
CERTIFICATE=None
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


def witnessed(group,doc,witnesses,**options):
    from noema.existential_witnesses import verify_witnesses
    WITNESS_CALLS[group]=WITNESS_CALLS.get(group,0)+1
    actual=adapted(group,doc,_references(witnesses))
    options=dict(options)
    options['primitives']={d['name']:options['primitives'][d['name']] for d in actual['declarations'] if d['kind']=='primitive'}
    return verify_witnesses(actual,witnesses,**options)


@lru_cache(None)
def namespace(group):
    original=importlib.import_module(GROUPS[group][0]);ns=dict(vars(original))
    for name,wrapped in vars(original).items():
        fn=getattr(wrapped,'__wrapped__',wrapped)
        if isinstance(fn,FunctionType) and (fn.__module__==original.__name__ or name in ('evaluate','values')):
            copied=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__);copied.__kwdefaults__=fn.__kwdefaults__
            ns[name]=lru_cache(None)(copied) if hasattr(wrapped,'cache_info') else copied
    ns['evaluate_document']=lambda doc,**kwargs:evaluated(group,doc,**kwargs)
    if group=='content':ns['verify_witnesses']=lambda doc,witnesses,**kwargs:witnessed(group,doc,witnesses,**kwargs)
    if group=='receipt':
        leaf=original.profiles
        leaf_globals=dict(vars(leaf))
        leaf_globals['evaluate_document']=lambda doc,**kwargs:evaluated(group,doc,**kwargs)
        fn=leaf.evaluate
        wrapped=FunctionType(fn.__code__,leaf_globals,fn.__name__,fn.__defaults__,fn.__closure__)
        wrapped.__kwdefaults__=fn.__kwdefaults__
        ns['profiles']=SimpleNamespace(**vars(leaf))
        ns['profiles'].evaluate=wrapped
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


def binding_certificate():
    global CERTIFICATE
    if CERTIFICATE is not None:return CERTIFICATE
    original=importlib.import_module(GROUPS['sentence'][0])
    entries=deepcopy(original.catalog().entries)
    names=('h4q','hzod','hzoe','hzr3','hzr4','hzr5','r2lu','r2lv','r2m3','hzpp')
    for name in names:
        assert entries[name]['declaration']==recovered()[name],('Certificate source differs',name)
        entries[name]['declaration']=deepcopy(recovered()[name])
    result=original.witness_chain(entries)
    cases=[('hzoe','hzod',0,3),('hzoe','hzod',3,16),('hzod','h4p',0,1),
        ('hzod','h4p',3,2),('hzr3','hzoe',2,1),('hzr4','hzr3',0,2),('r2lu','hzr5',1,3)]
    for owner,name,argument,wrong_parameter in cases:
        changed=deepcopy(entries);d=changed[owner]['declaration']
        original.single(d,name)['arguments'][argument]=original.parameters(d)[wrong_parameter]
        try:original.witness_chain(changed)
        except AssertionError:pass
        else:raise AssertionError(('Undetected role mutation',owner,argument))
    result['wrong_role_mutations_refused']=len(cases)
    assert result==check.read(GROUPS['sentence'][1])['binding']
    CERTIFICATE=dict(result=result,current_declarations=list(names),
        classification='Syntactic local witness binding certificate; not a full-domain semantic proof.')
    return CERTIFICATE


def source_pins():
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_public_dissemination_content_visible.py',
        'tests/test_kant_public_dissemination_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def build_report():
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-public-dissemination-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        recovered_witness_checks=WITNESS_CALLS,binding_certificate=binding_certificate(),
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
