"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_clerical_conscience_visible as check

CONTROLS='data/kant-clerical-conscience-visible-diagnostic-controls-v1.json'
GROUPS={'imputation': ('scripts.check_conscientious_imputation',
                'reports/conscientious-imputation-v1.json',
                [['component_checks', 'components'],
                 ['identity_checks', 'identity'],
                 ['scope_checks', 'scope']]),
 'integration': ('scripts.check_clerical_conscience',
                 'reports/clerical-conscience-v1.json',
                 [['native_checks', 'native'], ['discourse_checks', 'discourse']]),
 'mission': ('scripts.check_scholarly_mission',
             'reports/scholarly-mission-v1.json',
             [['scope_checks', 'scope'], ['independence_checks', 'independence']]),
 'arrangement_binding': ('scripts.check_clerical_conscience', 'reports/clerical-conscience-v1.json', []),
 'outer_binding': ('scripts.check_clerical_conscience', 'reports/clerical-conscience-v1.json', []),
 'appointment': ('scripts.check_teaching_policy', 'reports/teaching-policy-v1.json', []),
 'whole_claim': ('scripts.check_clerical_conscience', 'reports/clerical-conscience-v1.json', []),
 'whole_arrangement': ('scripts.check_clerical_conscience', 'reports/clerical-conscience-v1.json', [])}
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
    assert not needed & {'r36t'},('Outside current closure',group,needed & {'r36t'})
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
    paths=set(check.source_pins())|set(check.read('reports/kant-clerical-public-freedom-content-native-v4.json')['source_sha256'])|set(check.read('reports/kant-clerical-obligation-content-native-v1.json')['source_sha256'])|{'scripts/check_kant_clerical_public_freedom_content_visible.py','scripts/check_kant_clerical_obligation_content_visible.py','reports/kant-clerical-public-freedom-content-native-v4.json','reports/kant-clerical-obligation-content-native-v1.json','scripts/compose_scholarly_mission.py','scripts/compose_clerical_conscience.py',CONTROLS,'scripts/check_kant_clerical_conscience_content_visible.py',
        'tests/test_kant_clerical_conscience_content_visible.py'}
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


def current_fixture(statements,extras,boundaries=(),providers=()):
    from noema.constructed_discourse import normalize_document
    source={d['name']:deepcopy(d) for d in check.source_excerpt()['declarations']}
    for name in boundaries:
        d=source[name];assert d['kind']=='definition'
        source[name]=dict(kind='primitive',name=name,parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    for d in providers:
        original=source[d['name']]
        assert original['kind']=='primitive' and d['kind']=='definition'
        assert original['result']==d['result'] and original['parameters']==[p['sort'] for p in d['parameters']]
        source[d['name']]=deepcopy(d)
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


def run_current(group,doc,values,people,scenes):
    return [r['value'] for r in evaluated(group,doc,primitives=values,individuals=people,
        situations=scenes,max_steps=100000000,memoize_definitions=True,memoize_expressions=True)]




def constants(names):
    return [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in names]


def arrangement_parts():
    d=recovered()['r37v'];body=deepcopy(d['body']);assert body['kind']=='content';point=body['variable'];body=body['body'];names=[]
    for _ in range(10):
        assert body['kind']=='exists' and body['sort']=='individual'
        names.append(body['variable']);body=body['body']
    assert body['kind']=='and' and body['arguments'][0]['kind']=='equal'
    return d,point,names,body


def binding_model(selected,bits=(True,)*4):
    from noema.constructed_semantics import Content
    people=('x','y');scenes=('reference','evaluation');nine=selected[:9]
    public=(selected[0],selected[9],selected[2],selected[6],selected[7],'reference')
    values=dict(zx=lambda:'x',zy=lambda:'y',zref=lambda:'reference',zpoint=lambda:'evaluation',
        r35t=lambda *args:bits[0] and args==(*nine,'reference'),
        cd=lambda *args:bits[1] and args==(selected[9],'reference'),
        r36h=lambda *args:Content(scenes,(False,bits[2] and args==(*nine,'reference'))),
        r37l=lambda *args:Content(scenes,(False,bits[3] and args==public)))
    return values


@lru_cache(None)
def arrangement_binding_checks():
    from itertools import product
    from scripts.shared_modality import call
    d,point,variables,body=arrangement_parts();rows=[];table=[]
    extras=constants([('zx','individual'),('zy','individual'),('zref','situation'),('zpoint','situation')])
    boundaries=('r35t','r36h','r37l')
    for slot in range(10):
        selected=tuple('y' if i==slot else 'x' for i in range(10))
        sequence=dict(kind='sequence',element='individual',items=[call('z'+n) for n in selected])
        mapping={d['parameters'][0]['name']:sequence,d['parameters'][1]['name']:call('zref'),point:call('zpoint')}
        mapping.update({n:call('zx') for i,n in enumerate(variables) if i!=slot})
        query=dict(kind='exists',variable=variables[slot],sort='individual',body=substituted(body,mapping))
        doc=current_fixture([dict(kind='ask',body=query)],extras,boundaries)
        assert run_current('arrangement_binding',doc,binding_model(selected),('x','y'),('reference','evaluation'))==[True],slot
        wrong=tuple('x' for _ in selected)
        assert run_current('arrangement_binding',doc,binding_model(wrong),('x','y'),('reference','evaluation'))==[False],slot
        rows.append(slot)
    for bits in product((False,True),repeat=4):
        sequence=dict(kind='sequence',element='individual',items=[call('zx')]*10)
        statement=dict(kind='ask',body=dict(kind='evaluate',content=call('r37v',sequence,call('zref')),situation=call('zpoint')))
        doc=current_fixture([statement],extras,boundaries)
        actual=run_current('arrangement_binding',doc,binding_model(('x',)*10,bits),('x',),('reference','evaluation'))
        assert actual==[all(bits)],(bits,actual);table.append(dict(inputs=list(bits),result=actual[0]))
    for length in (0,9,11):
        sequence=dict(kind='sequence',element='individual',items=[call('zx')]*length)
        node=dict(kind='evaluate',content=call('r37v',sequence,call('zref')),situation=call('zpoint'))
        doc=current_fixture([dict(kind='ask',body=node)],extras,boundaries)
        assert run_current('arrangement_binding',doc,binding_model(('x',)*10),('x',),('reference','evaluation'))==[False],length
    result=dict(independently_checked_positions=rows,original_body_truth_table=table,wrong_lengths=[0,9,11],
        other_existential_binders_instantiated=True,two_distinguishing_values=True,full_cartesian_domain_enumerated=False)
    RESULTS['arrangement_binding']=result;return result


@lru_cache(None)
def outer_binding_checks():
    from noema.constructed_semantics import Content
    from scripts.shared_modality import call
    d,point,variables,inner=quantified_parts('r37x',9);rows=[]
    extras=constants([('jfixed'+c,'individual') for c in 'abcdefghi']+[('jpoint','situation')])
    for slot in range(9):
        mapping={n:call('jfixed'+'abcdefghi'[i]) for i,n in enumerate(variables) if i!=slot};mapping[point]=call('jpoint')
        node=dict(kind='forall',variable=variables[slot],sort='individual',body=substituted(inner,mapping))
        doc=current_fixture([dict(kind='ask',body=node)],extras,('r35t','r37w'))
        selected=tuple('y' if i==slot else 'x' for i in range(9));expected=(*selected,selected[0],'reference')
        candidates={tuple(v if i==slot else 'x' for i in range(9))+('reference',) for v in ('x','y')};contrasts={}
        for variant in ('baseline','failed_claim','wrong_reference','wrong_point','wrong_scholar','not_scholarly','no_case'):
            seen=set();forwarded=set()
            def case(*args):seen.add(args);return variant!='no_case' and args==(*selected,'reference')
            def claim(*args):
                forwarded.add(args);wanted=expected[:-1]+('other' if variant=='wrong_reference' else 'reference',)
                return Content(('reference','evaluation'),tuple(args==wanted and variant!='failed_claim' and
                    at==('reference' if variant=='wrong_point' else 'evaluation') for at in ('reference','evaluation')))
            values={'jfixed'+c:(lambda:'x') for c in 'abcdefghi'}
            values.update(jpoint=lambda:'evaluation',h232v=lambda:'reference',r35t=case,r37w=claim,
                h247d=lambda person,ref:('x' if person=='y' else 'y') if variant=='wrong_scholar' else person,
                cd=lambda role,ref:variant!='not_scholarly' and (role,ref)==(selected[0],'reference'))
            actual=run_current('outer_binding',doc,values,('x','y'),('reference','evaluation'))
            assert actual==[variant in ('baseline','no_case')],(slot,variant,actual)
            assert seen<=candidates
            if variant in ('baseline','no_case'):assert seen==candidates
            if variant=='baseline':assert expected in forwarded
            contrasts[variant]=actual[0]
        rows.append(dict(slot=slot,contrasts=contrasts))
    result=dict(slots=rows,current_binder_body_used=True,other_binders_instantiated=True,
        two_distinguishing_values=True,full_cartesian_domain_enumerated=False)
    RESULTS['outer_binding']=result;return result


@lru_cache(None)
def appointment_checks():
    from noema.constructed import parse
    from scripts import check_kant_clerical_obligation_content_visible as old
    from scripts import check_teaching_policy as policy,check_ranked_appointment as past
    from scripts.shared_modality import call
    extras=parse('p:'+policy.EXTRA_LOCAL)['declarations'];args=[call('z'+n) for n in policy.NAMES]+[call('zref')]
    nodes=[dict(kind='ask',body=dict(kind='evaluate',content=call(n,*args),situation=call('zpoint'))) for n in ('r36f','r36g','r36h')]
    doc=current_fixture(nodes,extras);saved=check.read('reports/kant-clerical-obligation-content-native-v1.json')['results']['appointment']
    independent=[];identities={};witnesses={}
    for row in saved['independent_truth_combinations']:
        bits=(True,True,row['appointed'],True,row['required'])
        actual=run_current('appointment',doc,old.appointment_model(doc,bits=bits),policy.SMALL,past.SCENES)
        assert actual==row['values']+[all(row['values'])],actual;independent.append(actual)
    for key,out in [('identity_contrasts',identities),('witness_contrasts',witnesses)]:
        for variant,expected in saved[key].items():
            bits=[True]*5
            if variant.startswith('absent_'):
                bits[('occurrence','entrustment','appointment','terms').index(variant[7:])]=False
            actual=run_current('appointment',doc,old.appointment_model(doc,variant,bits),policy.SMALL,past.SCENES)
            assert actual==expected+[all(expected)],(variant,actual,expected);out[variant]=actual
    result=dict(independent_truth_combinations=independent,identity_contrasts=identities,witness_contrasts=witnesses,
        actual_r35z_r36h_and_past_appointment_evaluated=True,same_policy_and_distinct_duty_appointment=True)
    RESULTS['appointment']=result;return result


def shared_extras():
    from noema.constructed import parse
    from scripts import check_confessional_teaching as confession,check_reviewed_thoughts as review,check_reform_proposals as proposal
    extras={};providers={}
    declarations=parse('p:'+confession.EXTRA+confession.PROVIDERS)['declarations']+parse('p:'+review.EXTRA+review.PROVIDER)['declarations']
    declarations+=constants([('z'+n,'individual') for n in proposal.DOMAIN]+[('zref','situation'),('zpoint','situation')])
    for d in declarations:
        if d['name'] in ('h246e','h246j','h224y'):providers[d['name']]=d;continue
        if d['name'] in extras:assert extras[d['name']]==d,d['name']
        extras[d['name']]=d
    return list(extras.values()),list(providers.values())


@lru_cache(None)
def whole_claim_document():
    from scripts import check_confessional_teaching as case
    from scripts.shared_modality import call
    extras,providers=shared_extras();args=[call('z'+n) for n in case.NAMES]+[call('zscholar'),call('zref')]
    d,point,variables,inner=quantified_parts('r37x',9)
    content=dict(kind='content',variable=point,body=substituted(inner,{n:call('z'+p) for n,p in zip(variables,case.NAMES)}))
    nodes=[call('r35t',*(args[:9]+[call('zref')])),dict(kind='evaluate',content=call('r37w',*args),situation=call('zpoint')),
        dict(kind='evaluate',content=content,situation=call('zpoint'))]
    return current_fixture([dict(kind='ask',body=n) for n in nodes],extras,providers=providers)


def whole_claim_model(doc,variant='baseline'):
    from scripts import check_confessional_teaching as case
    from scripts.check_motive_causes import unknown,symbol
    values=case.model(doc,variant);values.update(zscholar=lambda:'scholar',h232v=lambda:'reference',
        h247d=lambda person,ref:'role' if variant=='wrong_scholar' else 'scholar',cd=lambda role,ref:(role,ref)==('scholar','reference'))
    scope=() if variant=='empty_scope' else ('matter',) if variant=='outside_scope' else ('matter','matterb')
    matter='matterb' if variant in ('second_matter','outside_scope') else 'matter'
    def pertinent(person,item,code,bindings,ref):
        assert (person,symbol(code),code.rank,ref)==('person','r37v',2,'reference')
        allowed={(*case.NAMES,'scholar')}
        if variant=='wrong_scholar':allowed.add((*case.NAMES,'role'))
        assert tuple(bindings.items) in allowed
        return item in scope
    values.update(h247k=pertinent,fa=lambda p,j,at:(p,j,at)==('person','judgment','candidate'),
        se=lambda j,p,at:variant!='not_moral' and (j,p,at)==('judgment','person','candidate'),
        fb=lambda j,m,at:(j,m,at)==('judgment',matter,'candidate'),
        h247h=lambda j,p,m,ref,at:(j,p,m,ref,at)==('judgment','person',matter,'reference','candidate'),
        h247i=lambda j,ref,at:variant not in ('baseline','unwarranted') and (j,ref,at)==('judgment','reference','candidate'),
        h247j=lambda p,m,ref,ev,candidate:variant!='no_candidate' and
            (p,m,ref,ev,candidate)==('person',matter,'reference','outcome','candidate'))
    for name in ('h237z','h245c','h246m','zbelief','zcontent'):values[name]=unknown
    return values


@lru_cache(None)
def whole_claim_checks():
    from scripts import check_confessional_teaching as case
    from scripts.check_motive_causes import unknown
    doc=whole_claim_document();people=tuple(dict.fromkeys((*case.DOMAIN,'scholar','judgment','matter','matterb')))
    scenes=('reference','outcome','candidate','other');rows={}
    for variant in ('baseline','warranted','unwarranted','not_moral','no_candidate','second_matter','outside_scope','empty_scope','wrong_scholar','missing_pupil','not_profession'):
        valid_case=variant not in ('missing_pupil','not_profession')
        negative=variant in ('baseline','unwarranted','not_moral','no_candidate','outside_scope','empty_scope')
        expected=[valid_case,negative,not valid_case or variant!='wrong_scholar' and negative]
        actual=run_current('whole_claim',doc,whole_claim_model(doc,variant),people,scenes)
        assert actual==expected,(variant,actual,expected);rows[variant]=actual
    refused=[]
    for name in ('h246f','zchoosebelief','h247k','fa','se','fb','h247h','h247i','h247j','h247d','cd'):
        try:run_current('whole_claim',doc,whole_claim_model(doc,'warranted')|{name:unknown},people,scenes)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
        refused.append(name)
    result=dict(contrasts=rows,unknown_required_inputs_refused=refused,actual_case_and_negative_scope_connected=True,
        rank_two_arrangement_and_ten_bindings_retained=True,quoted_norms_not_executed=True,
        outer_query_binders_instantiated=True,source_definitions_unmodified=True,full_domain_proof=False)
    RESULTS['whole_claim']=result;return result


def expanded_public_query(node):
    from scripts import check_kant_clerical_public_freedom_content_visible as public
    current_freedom=FunctionType(public.freedom_instance.__code__,dict(vars(public))|{'recovered':recovered})
    def expand(value):
        if isinstance(value,list):return [expand(v) for v in value]
        if not isinstance(value,dict):return value
        if value.get('kind')=='call' and value['symbol']=='r37j':return current_freedom(value['arguments'])
        if value.get('kind')=='call' and value['symbol']=='r37l':
            definition=recovered()['r37l']
            body=substituted(definition['body'],{p['name']:arg for p,arg in zip(definition['parameters'],value['arguments'])})
            return expand(body)
        return {k:expand(v) for k,v in value.items()}
    return expand(node)


@lru_cache(None)
def whole_arrangement_document():
    from scripts import check_confessional_teaching as case,check_scholarly_mission as mission
    from scripts.shared_modality import call
    extras,providers=shared_extras();names=(*case.NAMES,'scholar')
    d,point,variables,inner=arrangement_parts()
    sequence=dict(kind='sequence',element='individual',items=[call('z'+n) for n in names])
    mapping={d['parameters'][0]['name']:sequence,d['parameters'][1]['name']:call('zref')}
    mapping.update({n:call('z'+value) for n,value in zip(variables,names)})
    content=expanded_public_query(dict(kind='content',variable=point,body=substituted(inner,mapping)))
    args=[call('z'+n) for n in case.NAMES]+[call('zref')]
    public_args=[call('z'+n) for n in mission.NAMES]+[call('zref')]
    ev=lambda n:dict(kind='evaluate',content=n,situation=call('zpoint'))
    nodes=[call('r35t',*args),call('cd',call('zscholar'),call('zref')),ev(call('r36h',*args)),
        ev(expanded_public_query(call('r37l',*public_args))),ev(content)]
    doc=current_fixture([dict(kind='ask',body=n) for n in nodes],extras,providers=providers)
    for declaration in doc['declarations']:
        if declaration['name'] in recovered():assert declaration==recovered()[declaration['name']],declaration['name']
    return doc


def whole_arrangement_model(doc,variant='baseline'):
    from scripts import check_kant_clerical_public_freedom_content_visible as public
    from scripts import check_kant_clerical_obligation_content_visible as teaching
    from scripts.check_motive_causes import unknown,symbol
    values=public.whole_model(doc,variant)
    bits=(True,True,variant!='no_appointment',True,variant!='no_duty')
    appointment=teaching.appointment_model(doc,'norm_issuer' if variant=='wrong_church_norm' else variant,bits)
    active={n:f for n,f in appointment.items() if not n.startswith('z') and f is not unknown}
    assert set(active)=={'ia','ic','h223k','h246m','h237z','dg','cf'},set(active)
    inward={'now':'reference','future':'now'}
    def mapped(fn):
        def result(*args):return fn(*(inward.get(a,a) if isinstance(a,str) else a for a in args))
        return result
    a={n:mapped(f) for n,f in active.items()}
    old={n:values[n] for n in ('ia','ic','h237z','dg','cf')}
    values.update(h223k=a['h223k'],h246m=a['h246m'],
        ia=lambda person,anchor,at:a['ia'](person,anchor,at) if anchor=='future' else old['ia'](person,anchor,at),
        ic=lambda first,last,anchor:a['ic'](first,last,anchor) if anchor=='future' else old['ic'](first,last,anchor),
        dg=lambda act,at:a['dg'](act,at) if act in ('event','other') else old['dg'](act,at),
        cf=lambda person,role,at:a['cf'](person,role,at),
        h237z=lambda *args:a['h237z'](*args) if symbol(args[3])=='r36e' else old['h237z'](*args))
    if variant=='not_scholar':values['cd']=lambda *args:False
    return values


@lru_cache(None)
def whole_arrangement_checks():
    from scripts import check_kant_clerical_public_freedom_content_visible as public
    from scripts.check_motive_causes import unknown
    doc=whole_arrangement_document();people=tuple(dict.fromkeys((*public.whole_people(),'event')));scenes=('past','now','future');rows={}
    cases=('baseline','no_duty','no_appointment','wrong_church_norm','terms_binding_creed','not_called',
        'no_public_candidate','thought_banned','proposal_banned','wrong_norm_source','missing_pupil','not_scholar')
    for variant in cases:
        case=variant!='missing_pupil';scholar=variant!='not_scholar'
        teaching=variant not in ('no_duty','no_appointment','wrong_church_norm','terms_binding_creed')
        mission=variant not in ('not_called','no_public_candidate','thought_banned','proposal_banned','wrong_norm_source','not_scholar')
        expected=[case,scholar,teaching,mission,case and scholar and teaching and mission]
        actual=run_current('whole_arrangement',doc,whole_arrangement_model(doc,variant),people,scenes)
        assert actual==expected,(variant,actual,expected);rows[variant]=actual
    refused=[]
    for name in ('h223k','h246m','cf','ia','ic','h237z','h245c'):
        try:run_current('whole_arrangement',doc,whole_arrangement_model(doc)|{name:unknown},people,scenes)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
        refused.append(name)
    result=dict(contrasts=rows,unknown_required_inputs_refused=refused,actual_case_teaching_appointment_public_norms_connected=True,
        distinct_norm_sources_and_history_anchors=True,source_definitions_unmodified=True,
        existential_and_item_query_binders_instantiated=True,quoted_policy_and_truth_not_executed=True,
        separate_from_negative_claim=True,full_domain_proof=False)
    RESULTS['whole_arrangement']=result;return result

def build_report():
    arrangement_binding_checks();outer_binding_checks();appointment_checks();whole_claim_checks();whole_arrangement_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-clerical-conscience-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        required_remaining_gates=['actual_svg_production','independent_cli','full_audit'],
        limitations=['Finite binding diagnostics and explicit query instances are not full-domain proofs.',
            'Quoted arrangement and actual negative claim are evaluated separately.',
            'Native evidence alone does not complete visible production or semantic-equivalence proof.'])
