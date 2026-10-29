"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_public_civic_opinion_visible as check

CONTROLS='data/kant-public-civic-opinion-visible-diagnostic-controls-v1.json'
GROUPS={'opinions': ('scripts.check_levy_opinions',
              'reports/levy-opinions-v1.json',
              [['content_checks', 'content'],
               ['message_checks', 'message'],
               ['expression_checks', 'expression'],
               ['public_checks', 'public'],
               ['unknown_checks', 'unknown']]),
 'noncontravention': ('scripts.check_civic_noncontravention',
                      'reports/civic-noncontravention-v1.json',
                      [['target_checks', 'target'],
                       ['finite_scope_checks', 'finite_scope'],
                       ['domain_checks', 'domain'],
                       ['quotation_checks', 'quotation'],
                       ['unknown_checks', 'unknown']]),
 'integration': ('scripts.check_public_civic_opinion',
                 'reports/public-civic-opinion-v1.json',
                 [['conditional_checks', 'conditional'],
                  ['branch_checks', 'branches'],
                  ['discourse_checks', 'discourse'],
                  ['domain_unknown_checks', 'domains_unknown']]),
 'scope_binding': ('scripts.check_public_civic_opinion', 'reports/public-civic-opinion-v1.json', []),
 'whole': ('scripts.check_public_civic_opinion', 'reports/public-civic-opinion-v1.json', [])}
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
    paths=set(check.source_pins())|{'scripts/check_civic_levy_refusal.py','scripts/compose_civic_example.py',CONTROLS,'scripts/check_kant_public_civic_opinion_content_visible.py',
        'tests/test_kant_public_civic_opinion_content_visible.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



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


def quantified_parts(name,count):
    d=recovered()[name];body=deepcopy(d['body']);assert body['kind']=='content'
    point=body['variable'];body=body['body'];variables=[]
    for _ in range(count):
        assert body['kind']=='forall' and body['sort']=='individual'
        variables.append(body['variable']);body=body['body']
    return d,point,variables,body


@lru_cache(None)
def slotwise_binding_checks():
    from noema.constructed_semantics import Content
    from scripts.shared_modality import call
    scenes=('reference','outcome');rows=[]
    extras=[dict(kind='primitive',name='jfixed'+letter,parameters=[],result='individual') for letter in 'abcdefgh']
    for name,count in (('r35i',8),('r35h',3)):
        d,point,variables,inner=quantified_parts(name,count)
        v=lambda n:dict(kind='variable',name=n)
        if name=='r35i':
            assert inner==dict(kind='implies',arguments=[call('r33w',*(v(n) for n in variables),call('h232v')),
                dict(kind='evaluate',content=call('r35h',*(v(variables[i]) for i in (3,4,1,0)),call('h232v')),situation=v(point))])
        else:
            params=[p['name'] for p in d['parameters']]
            assert [p['sort'] for p in d['parameters']]==['individual']*4+['situation']
            assert inner==dict(kind='evaluate',content=call('r35g',v(params[0]),v(params[1]),v(variables[0]),v(params[2]),v(variables[1]),v(variables[2]),v(params[3]),v(params[4])),situation=v(point))
        for slot in range(count):
            bindings={n:call('jfixed'+'abcdefgh'[i]) for i,n in enumerate(variables) if i!=slot}
            bindings[point]=call('jpoint')
            if name=='r35h':bindings.update({p['name']:call('jfixed'+'abcd'[i]) if i<4 else call('h232v') for i,p in enumerate(d['parameters'])})
            node=dict(kind='forall',variable=variables[slot],sort='individual',body=substituted(inner,bindings))
            ds=extras+[dict(kind='primitive',name='jpoint',parameters=[],result='situation')]
            boundaries=('r33w','r35h') if name=='r35i' else ('r35g',)
            doc=current_fixture([dict(kind='ask',body=node)],ds,boundaries);contrasts={}
            for variant in ('baseline','one_failure','wrong_reference','wrong_point'):
                visits=set();details=set();target=['x']*count;target[slot]='y'
                fixed_ref='other' if variant=='wrong_reference' else 'reference'
                fixed_point='reference' if variant=='wrong_point' else 'outcome'
                if name=='r35i':
                    def case(*args):
                        visits.add(args)
                        return args==(*target,'reference')
                    expected=tuple(target[i] for i in (3,4,1,0))+(fixed_ref,)
                    def conclusion(*args):
                        details.add(args)
                        return Content(scenes,tuple(variant!='one_failure' and args==expected and p==fixed_point for p in scenes))
                    values={'r33w':case,'r35h':conclusion}
                else:
                    failed=('x','x',target[0],'x',target[1],target[2],'x','reference')
                    def conclusion(*args):
                        visits.add(args)
                        return Content(scenes,tuple(args[-1]==fixed_ref and p==fixed_point and not (variant=='one_failure' and args==failed) for p in scenes))
                    values={'r35g':conclusion}
                values.update({'jfixed'+letter:(lambda:'x') for letter in 'abcdefgh'});values.update(h232v=lambda:'reference',jpoint=lambda:'outcome')
                actual=[r['value'] for r in evaluated('scope_binding',doc,primitives=values,individuals=('x','y'),situations=scenes)]
                assert actual==[variant=='baseline'],(name,slot,variant,actual)
                assert visits
                if name=='r35i':
                    assert (*target,'reference') in visits
                    projected={tuple((value if i==slot else 'x') for i in (3,4,1,0))+('reference',) for value in ('x','y')}
                    assert tuple(target[i] for i in (3,4,1,0))+('reference',) in details
                    assert details<=projected
                elif variant=='baseline':assert len(visits)==2
                elif variant=='one_failure':assert failed in visits
                contrasts[variant]=actual[0]
            rows.append(dict(target=name,slot=slot,independent_values=2,contrasts=contrasts))
    result=dict(slots=rows,current_binder_bodies_used=True,other_arguments_instantiated=True,
        typed_component_boundaries=True,full_cartesian_domain_enumerated=False,unbounded_equivalence_proved=False)
    RESULTS['scope_binding']=result
    return result


def inline_definition(name,args):
    d=recovered()[name];assert len(args)==len(d['parameters'])
    return dict(kind='apply',function=dict(kind='lambda',parameters=deepcopy(d['parameters']),body=deepcopy(d['body'])),arguments=deepcopy(args))


def whole_fixture():
    from noema.constructed import parse
    from scripts.shared_modality import call
    from scripts import check_civic_noncontravention as duties
    from scripts import check_public_civic_opinion as integrated
    from scripts.compose_civic_example import NAMES
    def instantiate(name,args,terms):
        d,point,variables,inner=quantified_parts(name,len(terms))
        body=dict(kind='apply',function=dict(kind='lambda',parameters=[dict(name=n,sort='individual') for n in variables],body=inner),arguments=terms)
        content=dict(kind='content',variable=point,body=body)
        return dict(kind='apply',function=dict(kind='lambda',parameters=deepcopy(d['parameters']),body=content),arguments=args)
    selected={'r35g','r35f','r35e','r35c','r35d','rfg','rfe'}
    def expand(node):
        if isinstance(node,list):return [expand(n) for n in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call':
            name=node['symbol'];args=node['arguments']
            if name=='r35i':return expand(instantiate(name,args,[call('z'+n) for n in NAMES]))
            if name=='r35h':return expand(instantiate(name,args,[call('z'+n) for n in ('activity','scholar','audience')]))
            if name in selected:return expand(inline_definition(name,args))
        return {k:expand(v) for k,v in node.items()}
    expr=lambda n,args:dict(kind='evaluate',content=call(n,*args),situation=call('zpoint'))
    ref=call('zref');names=lambda fields:[call('z'+n) for n in fields]
    questions=[call('r33w',*names(NAMES),ref),expr('r347',names(integrated.PUBLIC)+[ref]),
        expr('r35f',names(('person','role','activity','community'))+[ref]),
        expr('r35g',names(integrated.FIELDS)+[ref]),expr('r35i',[])]
    extras={}
    for text in (duties.EXTRA,integrated.EXTRA):
        for d in parse('p:'+text)['declarations']:
            if d['name'] in extras:assert d==extras[d['name']]
            extras[d['name']]=d
    doc=current_fixture([dict(kind='ask',body=expand(q)) for q in questions],list(extras.values()))
    # Domain instantiation introduces these diagnostic descriptions afterwards.
    doc['declarations']=list(extras.values())+[d for d in doc['declarations'] if d['name'] not in extras]
    doc=duties.restrict_domains(doc,True)
    # Only query expressions were instantiated; source definitions remain exact.
    for d in doc['declarations']:
        if d['name'] in recovered():assert d==recovered()[d['name']],d['name']
    return doc


@lru_cache(None)
def whole_content_checks():
    from scripts import check_civic_noncontravention as duties
    from scripts import check_levy_opinions as opinions
    from scripts import check_civic_levy_refusal as levy
    from scripts import check_public_civic_opinion as integrated
    from scripts.check_motive_causes import unknown,symbol
    from scripts.compose_civic_example import NAMES
    doc=whole_fixture();scenes=duties.SCENES
    domain=tuple(dict.fromkeys((*integrated.CONSTANTS,*duties.DOMAIN,'issuer','source')))
    def model(variant='baseline',branches=('unsuitable',)):
        failing=variant if variant in ('bound','ranked','direct') else 'none'
        duty_variant={'foreign_source':'different_norm_source','separate_activity':'separate_payment'}.get(variant,'baseline')
        if variant in ('foreign_source','separate_activity'):failing='direct'
        values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        case=levy.case_model(doc);opinion=opinions.expression_model(doc,'no_own_judgment' if variant=='no_expression' else 'baseline',branches)
        norm=duties.model(doc,duty_variant,failing)
        for source in (case,opinion,norm):values.update({n:f for n,f in source.items() if f is not unknown})
        for n in domain:values['z'+n]=lambda n=n:n
        values.update(zref=lambda:'reference',zpoint=lambda:'outcome',h232v=lambda:'reference',ztargetref=lambda:'other')
        # Shared predicates agree across models; civic and scholarly roles stay separate.
        for n,args in [('aa',('person',)),('h237c',('person','community','reference')),('hzwn',('person','role','reference')),('h244g',('role','community','reference'))]:
            providers=[s[n] for s in (case,opinion,norm) if n in s and s[n] is not unknown]
            assert all(f(*args)==providers[0](*args) for f in providers)
        case_requirement=case['h7k'];duty_requirement=norm['h7k']
        def required(*args):return case_requirement(*args) if symbol(args[3])=='r33u' else duty_requirement(*args)
        values['h7k']=required
        for n in ('ti','tj','h245n','h245o','h245c'):
            if n in values:assert values[n] is unknown,n
        return values
    def run(v):return [r['value'] for r in evaluated('whole',doc,primitives=v,individuals=domain,situations=scenes,max_steps=100000000,memoize_definitions=True,memoize_expressions=True)]
    rows={}
    for variant,branches in [('baseline',('unsuitable',)),('unjust_only',('unjust',)),('both',('unsuitable','unjust')),('neither',()),
        ('no_expression',('unsuitable',)),('bound',('unsuitable',)),('ranked',('unsuitable',)),('direct',('unsuitable',)),
        ('foreign_source',('unsuitable',)),('separate_activity',('unsuitable',))]:
        expressed=bool(branches) and variant!='no_expression';conforms=variant not in ('bound','ranked','direct')
        expected=[True,expressed,conforms,not expressed or conforms,not expressed or conforms]
        actual=run(model(variant,branches));assert actual==expected,(variant,actual,expected);rows[variant]=actual
    unknowns=('h244h','h244i','h245p','h245q','h245r','h245d','h245s','h245t','h7k','h237z','h7a')
    for name in unknowns:
        try:run(model()|{name:unknown})
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    result=dict(contrasts=rows,current_outer_case_and_public_detail_bodies_instantiated=True,
        actual_expression_and_three_duty_forms_connected=True,original_definitions_unmodified=True,
        description_and_sequence_domains_explicitly_instantiated_for_diagnostics=True,
        full_domain_refusal_tested_separately=True,criticism_truth_payment_and_permission_not_executed=True,
        same_actor_activity_and_distinct_civic_scholarly_roles=True,unknown_inputs_refused=list(unknowns),unbounded_equivalence_proved=False)
    RESULTS['whole_native']=result
    return result


def build_report():
    slotwise_binding_checks();whole_content_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-public-civic-opinion-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
