"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_scholarly_compatibility_visible as check

CONTROLS='data/kant-scholarly-compatibility-visible-diagnostic-controls-v1.json'
GROUPS={'self': ('scripts.check_scholarly_self_ascription',
          'reports/scholarly-self-ascription-v1.json',
          [['membership_checks', 'membership'], ['self_checks', 'self_ascription']]),
 'causal': ('scripts.check_nonimpairing_reasoning',
            'reports/nonimpairing-reasoning-v1.json',
            [['causal_checks', 'causal'], ['method_checks', 'method'], ['unknown_checks', 'unknown']]),
 'compatibility': ('scripts.check_scholarly_compatibility',
                   'reports/scholarly-compatibility-v1.json',
                   [['premise_checks', 'premise'],
                    ['result_checks', 'result'],
                    ['binding_checks', 'bindings'],
                    ['focus_checks', 'focus'],
                    ['discourse_checks', 'discourse']]),
 'binding': ('scripts.check_scholarly_compatibility', 'reports/scholarly-compatibility-v1.json', [])}
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
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_scholarly_compatibility_content_visible.py',
        'tests/test_kant_scholarly_compatibility_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def conditional_parts():
    from scripts.shared_modality import call
    body=deepcopy(recovered()['r32f']['body']);assert body['kind']=='content'
    point=body['variable'];inner=body['body'];variables=[]
    for _ in range(9):
        assert inner['kind']=='forall' and inner['sort']=='individual'
        variables.append(inner['variable']);inner=inner['body']
    var=lambda n:dict(kind='variable',name=n)
    assert len(set(variables))==9 and point not in variables
    assert inner==dict(kind='implies',arguments=[call('r32b',*(var(n) for n in variables),call('h232v')),
        dict(kind='evaluate',content=call('r32a',*(var(variables[i]) for i in (0,5,2,7)),call('h232v')),situation=var(point))])
    return point,variables,inner


def substituted(node,bindings):
    if isinstance(node,list):return [substituted(n,bindings) for n in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name'] in bindings:return deepcopy(bindings[node['name']])
    assert not ('variable' in node and node['variable'] in bindings),'Do not capture a nested binder'
    return {k:substituted(v,bindings) for k,v in node.items()}


def current_fixture(statements,extras,boundaries=()):
    from noema.constructed_discourse import normalize_document
    source={d['name']:deepcopy(d) for d in check.source_excerpt()['declarations']}
    for name in boundaries:
        d=source[name];assert d['kind']=='definition'
        source[name]=dict(kind='primitive',name=name,parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    for d in extras:assert d['name'] not in source;source[d['name']]=d
    ds=[];seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name);d=source[name]
        for dependency in sorted(_references(d.get('body'))):visit(dependency)
        ds.append(d)
    for name in sorted(_references(statements)):visit(name)
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=statements))


def probe_constants():
    return [dict(kind='primitive',name='jfixed'+letter,parameters=[],result='individual') for letter in 'abcdefghi']+[
        dict(kind='primitive',name='jstart',parameters=[],result='situation')]


@lru_cache(None)
def slotwise_binding_checks():
    from noema.constructed_semantics import Content
    from scripts.shared_modality import call
    point,variables,inner=conditional_parts();scenes=('reference','start','other');rows=[]
    fixed=('x','y','x','y','x','y','x','y','x')
    for slot in range(9):
        bindings={n:call('jfixed'+'abcdefghi'[i]) for i,n in enumerate(variables) if i!=slot}
        bindings[point]=call('jstart')
        body=dict(kind='forall',variable=variables[slot],sort='individual',body=substituted(inner,bindings))
        doc=current_fixture([dict(kind='ask',body=body)],probe_constants(),('r32a','r32b'))
        target=list(fixed);target[slot]='y';target=tuple(target)
        results={}
        for variant in ('baseline','false_consequence','wrong_evaluation','empty_antecedent','wrong_reference'):
            seen=set();consequences=set()
            def premise(*args):
                seen.add(args)
                return variant!='empty_antecedent' and args==(*target,'other' if variant=='wrong_reference' else 'reference')
            def consequence(*args):
                consequences.add(args)
                wanted=tuple(target[i] for i in (0,5,2,7))+('reference',)
                return Content(scenes,tuple(args==wanted and variant!='false_consequence' and s==('other' if variant=='wrong_evaluation' else 'start') for s in scenes))
            values={'r32b':premise,'r32a':consequence,'h232v':lambda:'reference','jstart':lambda:'start'}
            values.update({'jfixed'+letter:(lambda v=fixed[i]:v) for i,letter in enumerate('abcdefghi')})
            actual=[r['value'] for r in evaluated('binding',doc,primitives=values,individuals=('x','y'),situations=scenes,
                memoize_definitions=True,memoize_expressions=True)]
            assert actual==[variant in ('baseline','empty_antecedent','wrong_reference')],(slot,variant,actual)
            wanted_seen={tuple(value if i==slot else fixed[i] for i in range(9))+('reference',) for value in ('x','y')}
            assert seen==wanted_seen,(slot,seen)
            assert all(args[-1]=='reference' for args in consequences)
            results[variant]=actual[0]
        def unknown(*args):raise ValueError('Unknown scholarly binding input')
        for name in ('r32a','r32b'):
            try:evaluated('binding',doc,primitives=values|{name:unknown},individuals=('x','y'),situations=scenes)
            except ValueError as error:assert 'Unknown scholarly binding input' in str(error)
            else:raise AssertionError(name)
        rows.append(dict(slot=slot,contrasts=results,independent_values=2))
    result=dict(slots=rows,canonical_nine_binder_body_inspected=True,eight_other_arguments_instantiated=True,
        native_premise_and_consequence_evaluated_here=False,boundaries=['r32b','r32a'],
        full_cartesian_domain_enumerated=False,unbounded_equivalence_proved=False)
    RESULTS['binding']=result
    return result


def whole_fixture():
    from scripts.shared_modality import call
    point,variables,inner=conditional_parts()
    bindings={n:call('jfixed'+'abcdefghi'[i]) for i,n in enumerate(variables)};bindings[point]=call('jstart')
    conditional=substituted(inner,bindings);args=conditional['arguments'][0]['arguments']
    statements=[dict(kind='ask',body=conditional['arguments'][0]),dict(kind='ask',body=conditional)]
    statements += [dict(kind='ask',body=call(n,*deepcopy(args))) for n in ('r32c','r32d','r32e')]
    return current_fixture(statements,probe_constants())


@lru_cache(None)
def whole_content_checks():
    from scripts import check_scholarly_compatibility as original
    from scripts.check_nonimpairing_reasoning import scholarly_model,key
    from scripts.check_scholarly_self_ascription import DOMAIN as CIVIC_DOMAIN
    doc=whole_fixture();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[n]==recovered()[n] for n in ('r32a','r32b','r32c','r32d','r32e','r3u','r3v','r3y','r3z','r3r','r3m'))
    domain=tuple(dict.fromkeys((*CIVIC_DOMAIN,*original.DOMAIN)));scenes=original.SCENES
    names=tuple(original.NAMES)
    def unknown(*args):raise ValueError('Unknown whole scholarly input')
    def model(variant='baseline',mismatch=None):
        values=original.result_model(doc,variant)
        premise=scholarly_model(doc,'baseline')
        for n in ('aa','ca','cb','cd','cc','ce','h242g','fa','h242h','h242d','h237y','h237h','h237i','h237d','h237c','h237e','h237f','h232p'):
            values[n]=premise[n]
        values.update({'jfixed'+letter:(lambda value='other' if mismatch==i else names[i]:value) for i,letter in enumerate('abcdefghi')})
        values['jstart']=lambda:'start'
        if variant=='missing_record':values['sc']=lambda *args:False
        if variant in ('different_methods','safe_method_available'):
            prefix=lambda args:args[:5]==('person','activity','work','reference','start')
            values['h242k']=lambda *args:args[5]=='othermethod' and bool(args[-1]('factor')) if args[-2]=='result' else False
            values['h242o']=lambda w,ref,left,right:(w,ref)==('work','reference') and left in original.POINTS and right in original.POINTS and (1 if left=='on_a' else 2)>=(1 if right=='on_a' else 2)
            values['h242p']=lambda *args:prefix(args) and args[5] in (('method','othermethod') if variant=='safe_method_available' else ('method',))
            values['h242q']=lambda *args:prefix(args) and args[5] in ('method','othermethod') and args[6]==('on_a' if args[5]=='method' else 'on_b')
            values['h242r']=values['h242q']
            values.update(sc=lambda w,s:w=='writing' and s in ('on_a','on_b'),
                hzwr=lambda record,w,s:(record,w)==('record','writing') and s in ('on_a','on_b'),
                hzws=lambda record,carrier,s:(record,carrier)==('record','carrier') and s in ('on_a','on_b'),
                hzwt=lambda record,s:record=='record' and s in ('on_a','on_b'))
        return values
    def run(values):
        return [r['value'] for r in evaluated('whole',doc,primitives=values,individuals=domain,situations=scenes,
            max_steps=100000000,memoize_definitions=True,memoize_expressions=True)]
    rows={}
    for variant in ('baseline','split_record','unreadable','harmful','unavailable','missing_record','different_methods','safe_method_available'):
        wanted=[True,variant in ('baseline','safe_method_available'),True,True,True]
        actual=run(model(variant));assert actual==wanted,(variant,actual);rows[variant]=actual
    mismatches={}
    for slot,name in enumerate(names):
        wanted=[False,True,slot not in (0,3,4),slot not in (0,5,6,7,8),slot not in (0,1,2,3)]
        actual=run(model(mismatch=slot));assert actual==wanted,(name,actual,wanted);mismatches[name]=actual
    for name in ('h242d','h242n','h242o','h242p','hzwt'):
        try:run(model()|{name:unknown})
        except ValueError as error:assert 'Unknown whole scholarly input' in str(error)
        else:raise AssertionError(name)
    assert run(model()|{'h242e':unknown,'h242f':unknown})==[True]*5
    result=dict(contrasts=rows,argument_mismatches=mismatches,current_premise_and_consequence_connected=True,
        native_focus_bodies_evaluated=['r32c','r32d','r32e'],same_method_for_causality_ability_and_written_record=True,
        ascribed_cosmopolitan_membership_not_executed=True,conditional_with_false_premise_is_vacuous=True,
        nine_arguments_instantiated_for_native_body_diagnostic=True,unbounded_equivalence_proved=False)
    RESULTS['whole']=result
    return result


def build_report():
    slotwise_binding_checks();whole_content_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-scholarly-compatibility-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
