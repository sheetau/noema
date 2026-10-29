"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_civic_example_visible as check

CONTROLS='data/kant-civic-example-visible-diagnostic-controls-v1.json'
GROUPS={'levy': ('scripts.check_civic_levy_refusal',
          'reports/civic-levy-refusal-v1.json',
          [('payment_checks', 'payment'),
           ('civic_checks', 'civic'),
           ('case_checks', 'case'),
           ('refusal_checks', 'refusal'),
           ('binding_checks', 'bindings'),
           ('unknown_checks', 'unknown')]),
 'reproof': ('scripts.check_levy_reproof',
             'reports/levy-reproof-v1.json',
             [('message_checks', 'message'),
              ('reproof_checks', 'reproof'),
              ('standing_checks', 'standing'),
              ('case_checks', 'case'),
              ('unknown_checks', 'unknown')]),
 'resistance': ('scripts.check_general_resistance',
                'reports/general-resistance-v1.json',
                [('response_checks', 'response'),
                 ('breadth_checks', 'breadth'),
                 ('potential_checks', 'potential'),
                 ('domain_checks', 'domains'),
                 ('unknown_checks', 'unknown')]),
 'sanction': ('scripts.check_scandal_sanction',
              'reports/scandal-sanction-v1.json',
              [('assessment_checks', 'assessment'),
               ('sanction_checks', 'sanction'),
               ('binding_checks', 'bindings'),
               ('permission_checks', 'permission'),
               ('eligibility_checks', 'eligibility')]),
 'civic': ('scripts.check_civic_example',
           'reports/civic-example-v1.json',
           [('refusal_checks', 'refusal'),
            ('conditional_checks', 'conditional'),
            ('detail_checks', 'detail'),
            ('quantifier_checks', 'quantifiers'),
            ('whole_checks', 'whole'),
            ('focus_checks', 'focus'),
            ('discourse_checks', 'discourse'),
            ('unknown_checks', 'unknown')]),
 'scope_binding': ('scripts.check_civic_example', 'reports/civic-example-v1.json', []),
 'witness_binding': ('scripts.check_scandal_sanction', 'reports/scandal-sanction-v1.json', []),
 'whole': ('scripts.check_civic_example', 'reports/civic-example-v1.json', [])}
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
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_civic_example_content_visible.py',
        'tests/test_kant_civic_example_content_visible.py'}
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


def peel(body,kind,count):
    names=[];inner=deepcopy(body)
    for _ in range(count):
        assert inner['kind']==kind and inner['sort']=='individual'
        names.append(inner['variable']);inner=inner['body']
    assert len(set(names))==count
    return names,inner


def constants(count=12):
    return [dict(kind='primitive',name='jfixed'+c,parameters=[],result='individual') for c in 'abcdefghijkl'[:count]]+[
        dict(kind='primitive',name='jpoint',parameters=[],result='situation'),
        dict(kind='primitive',name='jreference',parameters=[],result='situation')]


@lru_cache(None)
def selected_sanction_unknown_checks():
    ns=namespace('sanction');rows=[]
    for kind,model,names in [('assessment','assessment_model',('h244u','h244v','h244w')),
                           ('sanction','sanction_model',('cg','h244x','h244y','h244z')),
                           ('permission','permission_model',('h245c','h237z')),
                           ('eligible','permission_model',('h245a',))]:
        doc=ns['fixture'](kind)
        for name in names:
            values=ns[model](doc);values[name]=ns['unknown']
            try:ns['evaluate'](doc,values,ns['DOMAIN'],ns['SCENES'],True)
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError((kind,name))
            rows.append([kind,name])
    result=dict(unknown_inputs_refused=rows,physical_possibility_outside_selected_source_not_imported=True)
    RESULTS['sanction_unknown']=result
    return result


@lru_cache(None)
def slotwise_scope_checks():
    from noema.constructed_semantics import Content
    from scripts.shared_modality import call
    scenes=('reference','other');rows=[]
    for target,count,boundaries in [('r34u',8,('r33w','r34p')),('r34v',8,('r33w','r34s')),('r34w',8,('r33w','r34t')),
                                    ('r34s',4,('r34q',)),('r34t',4,('r34r',))]:
        d=recovered()[target];content=d['body'];assert content['kind']=='content'
        names,inner=peel(content['body'],'forall',count)
        fixed=tuple('x' if i%2==0 else 'y' for i in range(count))
        for slot in range(count):
            binds={n:call('jfixed'+'abcdefghijkl'[i]) for i,n in enumerate(names) if i!=slot}
            binds[content['variable']]=call('jpoint')
            # Detail families additionally receive the same fixed eight case arguments.
            if d['parameters']:
                assert [p['sort'] for p in d['parameters']]==['individual']*8+['situation']
                binds.update({p['name']:call('jfixed'+'abcdefghijkl'[i]) for i,p in enumerate(d['parameters'][:8])})
                binds[d['parameters'][8]['name']]=call('jreference')
            body=dict(kind='forall',variable=names[slot],sort='individual',body=substituted(inner,binds))
            doc=current_fixture([dict(kind='ask',body=body)],constants(),boundaries)
            target_values=list(fixed);target_values[slot]='y' if fixed[slot]=='x' else 'x';target_values=tuple(target_values)
            cases={}
            for variant in ('baseline','one_failure','wrong_reference','wrong_point'):
                visits=set();values={'jpoint':lambda:'reference','jreference':lambda:'reference','h232v':lambda:'reference'}
                values.update({'jfixed'+c:(lambda value='x' if i%2==0 else 'y':value) for i,c in enumerate('abcdefghijkl')})
                def consequence(*args):
                    visits.add(args)
                    current=args[:8] if count==8 else args[8:12]
                    if target=='r34u':current=(args[1],args[0],*args[2:7])  # No levy in refusal consequence.
                    # All slots including levy are inspected by the scope below.
                    matched=(current==target_values if target!='r34u' else args==(*target_values[1:],'reference'))
                    good=not (variant=='one_failure' and matched) and args[-1]==('other' if variant=='wrong_reference' else 'reference')
                    return Content(scenes,tuple(good and p==('other' if variant=='wrong_point' else 'reference') for p in scenes))
                if count==8:
                    scope_visits=set()
                    def scope(*args):scope_visits.add(args);return args==(*target_values,'reference')
                    values['r33w']=scope
                values[boundaries[-1]]=consequence
                actual=[r['value'] for r in evaluated('scope_binding',doc,primitives=values,individuals=('x','y'),situations=scenes)]
                assert actual==[variant=='baseline'],(target,slot,variant,actual)
                if count==8:
                    expected={tuple(value if i==slot else fixed[i] for i in range(count))+('reference',) for value in ('x','y')}
                    assert scope_visits<=expected and (*target_values,'reference') in scope_visits
                    if variant=='baseline':assert scope_visits==expected
                else:
                    prefix=tuple('x' if i%2==0 else 'y' for i in range(8))
                    expected={prefix+tuple(value if i==slot else fixed[i] for i in range(count))+('reference',) for value in ('x','y')}
                    assert visits and visits<=expected
                    if variant=='baseline':assert visits==expected
                    elif variant=='one_failure':assert prefix+target_values+('reference',) in visits
                    # Wrong reference/point falsifies every assignment, so a
                    # universal may stop at its first counterexample.
                cases[variant]=actual[0]
            rows.append(dict(target=target,slot=slot,independent_values=2,contrasts=cases))
    result=dict(slots=rows,other_arguments_instantiated=True,current_binder_bodies_used=True,
        typed_component_boundaries=True,full_cartesian_domain_enumerated=False,unbounded_equivalence_proved=False)
    RESULTS['scope_binding']=result
    return result


@lru_cache(None)
def sanction_witness_binding_checks():
    from noema.constructed_semantics import Content
    from scripts.shared_modality import call
    d=recovered()['r34o'];content=d['body'];assert content['kind']=='content'
    names,inner=peel(content['body'],'exists',3)
    params=[p['name'] for p in d['parameters']];assert len(params)==6
    scenes=('reference','other');rows=[];fixed=('x','y','x')
    for slot in range(3):
        binds={p:call('jfixed'+'abcde'[i]) for i,p in enumerate(params[:5])};binds[params[5]]=call('jreference')
        binds[content['variable']]=call('jpoint')
        binds.update({n:call('jfixed'+'fgh'[i]) for i,n in enumerate(names) if i!=slot})
        body=dict(kind='exists',variable=names[slot],sort='individual',body=substituted(inner,binds))
        doc=current_fixture([dict(kind='ask',body=body)],constants(),('r34n',));cases={}
        wanted=list(fixed);wanted[slot]='y' if fixed[slot]=='x' else 'x';wanted=tuple(wanted)
        for variant in ('baseline','no_authority','no_permission','wrong_reference','wrong_point'):
            visits=set()
            def authority(a,role,community,ref):
                return variant!='no_authority' and (a,role,community,ref)==(wanted[0],wanted[1],'y','reference')
            def permit(*args):
                visits.add(args)
                good=variant!='no_permission' and args==('x',wanted[1],wanted[0],wanted[2],'y','x','y','x','other' if variant=='wrong_reference' else 'reference')
                return Content(scenes,tuple(good and p==('other' if variant=='wrong_point' else 'reference') for p in scenes))
            values={'h245a':authority,'r34n':permit,'jpoint':lambda:'reference','jreference':lambda:'reference'}
            values.update({'jfixed'+c:(lambda value=('x','y','x','y','x',*fixed)[i]:value) for i,c in enumerate('abcdefgh')})
            actual=[r['value'] for r in evaluated('witness_binding',doc,primitives=values,individuals=('x','y'),situations=scenes)]
            assert actual==[variant=='baseline'],(slot,variant,actual)
            cases[variant]=actual[0]
        rows.append(dict(slot=slot,independent_values=2,contrasts=cases))
    result=dict(slots=rows,other_witnesses_instantiated=True,current_existential_body_used=True,
        boundary=['r34n'],native_permission_tested_separately=True,full_cartesian_domain_enumerated=False,unbounded_equivalence_proved=False)
    RESULTS['witness_binding']=result
    return result


def whole_fixture():
    from scripts.shared_modality import call
    from scripts.compose_civic_example import NAMES,DETAILS
    selected=set(('r34x','r34u','r34v','r34w','r34s','r34t','r34q','r34r','r34o'))
    def expand(node):
        if isinstance(node,list):return [expand(v) for v in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol') in selected:
            n=node['symbol'];d=recovered()[n]
            body=substituted(d['body'],{p['name']:a for p,a in zip(d['parameters'],node['arguments'],strict=True)})
            if n in ('r34u','r34v','r34w','r34s','r34t','r34o'):
                assert body['kind']=='content'
                count=8 if n in ('r34u','r34v','r34w') else 3 if n=='r34o' else 4
                binders,inner=peel(body['body'],'exists' if n=='r34o' else 'forall',count)
                args=[call('jwitness'+c) for c in 'abc'] if n=='r34o' else [call('jfixed'+c) for c in ('abcdefgh' if count==8 else 'ijkl')]
                body['body']=substituted(inner,dict(zip(binders,args,strict=True)))
            return expand(body)
        return {k:expand(v) for k,v in node.items()}
    fields=[call('jfixed'+c) for c in 'abcdefghijkl']
    case=call('r33w',*fields[:8],call('jreference'))
    criticism=dict(kind='evaluate',content=call('r34d',*fields,call('jreference')),situation=call('jpoint'))
    def evaluated_content(n,args=()):return dict(kind='evaluate',content=expand(call(n,*args)),situation=call('jpoint'))
    permission=evaluated_content('r34o',(call('h245d',fields[1],call('jreference')),fields[3],fields[8],fields[1],call('h245e',*fields[:8],call('jreference')),call('jreference')))
    potential=evaluated_content('r34i',(fields[8],fields[1],call('jreference')))
    refusal=evaluated_content('r34p',(*fields[1:8],call('jreference')))
    main=evaluated_content('r34q',(*fields,call('jreference')))
    aside=evaluated_content('r34r',(*fields,call('jreference')))
    whole=evaluated_content('r34x')
    extras=constants()+[dict(kind='primitive',name='jwitness'+c,parameters=[],result='individual') for c in 'abc']
    return current_fixture([dict(kind='ask',body=n) for n in (case,criticism,refusal,permission,potential,main,aside,whole)],extras,('r34f',))


@lru_cache(None)
def whole_content_checks():
    from fractions import Fraction
    from noema.constructed_semantics import Content,SequenceValue
    from scripts import check_levy_reproof as reproof
    from scripts.compose_civic_example import NAMES,DETAILS
    from scripts.check_motive_causes import unknown,symbol
    doc=whole_fixture();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[n]==recovered()[n] for n in ('r33w','r34d','r34n','r34i','r34h','r34g','r34p'))
    scenes=reproof.SCENES;fields=(*NAMES,*DETAILS)
    domain=tuple(dict.fromkeys((*reproof.DOMAIN,'third','response','responseother','authority','sanctionrole','measure','norm','standard')))
    def model(variant='baseline',mismatch=None):
        values=reproof.case_model(doc,'no_disapproval' if variant=='no_criticism' else 'baseline')
        values.update({'jfixed'+c:(lambda value='other' if mismatch==i else fields[i]:value) for i,c in enumerate('abcdefghijkl')})
        values.update(jreference=lambda:'reference',jpoint=lambda:'outcome',h232v=lambda:'reference',
            jwitnessa=lambda:'authority',jwitnessb=lambda:'sanctionrole',jwitnessc=lambda:'measure')
        values['aa']=lambda p:p in ('person','second','third')
        values['h237c']=lambda p,community,ref:p in ('person','second','third') and (community,ref)==('community','reference')
        values['h245d']=lambda community,ref:'norm' if (community,ref)==('community','reference') else 'other'
        values['h245e']=lambda *args:'standard' if args==(*NAMES,'reference') and variant!='wrong_standard' else 'other'
        values['h244k']=lambda response,issuer,person,role,code,bindings,sign,ref:response in ('response','responseother') and (
            issuer,person,role,symbol(code),code.rank,tuple(bindings.items),sign,ref)==('issuer','person','role','r33u',0,('person','transfer','receiver','medium'),True,'reference')
        sanction=('authority','measure','person','criticism','community','standard')
        def requirement(source,person,role,code,bindings,ref,sign,point):
            target=symbol(code)
            if target=='r33y':
                return variant!='no_refusal_ban' and not (variant=='second_response_unprotected' and bindings.items[-1]=='responseother') and (
                    source,person,role,code.rank,tuple(bindings.items[:-1]),ref,sign,point)==('norm','person','role',1,NAMES[2:],'reference',False,'outcome')
            if target=='r34l':return variant=='opposed_requirement' and (source,person,role,code.rank,tuple(bindings.items),ref,sign,point)==('norm','authority','sanctionrole',1,sanction,'reference',False,'outcome')
            raise ValueError('Unknown civic requirement target')
        values['h237z']=requirement
        values['h245a']=lambda authority,role,community,ref:variant!='no_authority' and (authority,role,community,ref)==('authority','sanctionrole','community','reference')
        values['h245c']=lambda source,authority,role,code,bindings,ref,sign,point:variant!='no_permission' and (
            source,authority,role,symbol(code),code.rank,tuple(bindings.items),ref,sign,point)==(
                'norm','authority','sanctionrole','r34l',1,sanction,'reference',variant!='negative_permission','outcome')
        values['h244q']=lambda community,ref:SequenceValue(('person','second','third') if (community,ref)==('community','reference') else (), '"individual"')
        values['r34f']=lambda person,community,ref:Content(scenes,tuple(variant!='no_resistance' and person in ('person','second') and (community,ref)==('community','reference') and p=='other' for p in scenes))
        values.update(ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b,hd=lambda t:Fraction(int(t)),pa=lambda a,b:a/b if b else Fraction(0))
        values['h244r']=lambda community,ref,ratio:(community,ref)==('community','reference') and ratio>=Fraction(2,3)
        values['h244t']=lambda activity,community,evaluation,outcome:variant!='no_candidate' and (activity,community,evaluation)==('criticism','community','outcome') and outcome in (('outcome','other') if variant=='split_cause' else ('other',))
        values['dg']=lambda act,point:(act,point) in (('criticism','outcome'),('criticism','other'))
        values['h244s']=lambda act,community,code,ref,outcome:variant!='no_cause' and (act,community,symbol(code),code.rank,ref,outcome)==('criticism','community','r34h',1,'reference','outcome' if variant=='split_cause' else 'other')
        for n in ('cg','ti','tj','h244j','h244u','h244v','h244w','h244x','h244y','h244z','h243u','h243v'):
            if n in values:assert values[n] is unknown,n
        return values
    def run(values):return [r['value'] for r in evaluated('whole',doc,primitives=values,individuals=domain,situations=scenes,max_steps=100000000,memoize_definitions=True,memoize_expressions=True)]
    rows={}
    variants=('baseline','no_criticism','no_refusal_ban','second_response_unprotected','no_permission','no_authority','wrong_standard','negative_permission','opposed_requirement','no_candidate','no_cause','split_cause','no_resistance')
    for variant in variants:
        criticism=variant!='no_criticism';ban=variant not in ('no_refusal_ban','second_response_unprotected')
        permission=variant not in ('no_permission','no_authority','wrong_standard','negative_permission','opposed_requirement')
        potential=variant not in ('no_candidate','no_cause','split_cause','no_resistance')
        main=not criticism or permission;aside=not criticism or potential
        expected=[True,criticism,ban,permission,potential,main,aside,ban and main and aside]
        actual=run(model(variant));assert actual==expected,(variant,actual,expected);rows[variant]=actual
    for name in ('h244n','h244m','h245a','h245c','h237z','h245d','h245e','h244q','h244r','h244s','h244t','r34f'):
        try:run(model()|{name:unknown})
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    result=dict(contrasts=rows,current_outer_cases_and_criticism_details_instantiated=True,
        current_sanction_witnesses_instantiated=True,original_definitions_unmodified=True,
        actual_levy_criticism_permission_and_possible_induction_bodies_connected=True,
        individual_resistance_boundary='r34f; unrestricted description/sequence quantification separately rejects finite enumeration',
        actual_payment_refusal_sanction_and_assessment_truth_not_executed=True,
        actual_resistance_not_required=True,shared_candidate_required=True,unbounded_equivalence_proved=False)
    RESULTS['whole_native']=result
    return result


def build_report():
    selected_sanction_unknown_checks();slotwise_scope_checks();sanction_witness_binding_checks();whole_content_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-civic-example-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
