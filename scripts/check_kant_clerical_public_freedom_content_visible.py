"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_clerical_public_freedom_visible as check

CONTROLS='data/kant-clerical-public-freedom-visible-diagnostic-controls-v1.json'
GROUPS={'review': ('scripts.check_reviewed_thoughts',
            'reports/reviewed-thoughts-v1.json',
            [['unknown_checks', 'unknown']]),
 'opinions': ('scripts.check_creed_opinions',
              'reports/creed-opinions-v1.json',
              [['identity_checks', 'identity'],
               ['expression_checks', 'expression'],
               ['unknown_checks', 'unknown']]),
 'proposals': ('scripts.check_reform_proposals',
               'reports/reform-proposals-v1.json',
               [['comparison_checks', 'comparison'],
                ['binding_checks', 'bindings'],
                ['public_checks', 'public'],
                ['unknown_checks', 'unknown']]),
 'mission': ('scripts.check_scholarly_mission',
             'reports/scholarly-mission-v1.json',
             [['norm_identity_checks', 'norm_identity']]),
 'integration': ('scripts.check_clerical_public_freedom',
                 'reports/clerical-public-freedom-v1.json',
                 [['discourse_checks', 'discourse']]),
 'qualification': ('scripts.check_reviewed_thoughts', 'reports/reviewed-thoughts-v1.json', []),
 'review_binding': ('scripts.check_reviewed_thoughts', 'reports/reviewed-thoughts-v1.json', []),
 'mission_scope': ('scripts.check_scholarly_mission', 'reports/scholarly-mission-v1.json', []),
 'mission_independence': ('scripts.check_scholarly_mission', 'reports/scholarly-mission-v1.json', []),
 'adapter_binding': ('scripts.check_scholarly_mission', 'reports/scholarly-mission-v1.json', []),
 'outer_binding': ('scripts.check_clerical_public_freedom', 'reports/clerical-public-freedom-v1.json', []),
 'selected_unknown': ('scripts.check_clerical_public_freedom', 'reports/clerical-public-freedom-v1.json', []),
 'whole': ('scripts.check_confessional_teaching', 'reports/confessional-teaching-v1.json', [])}
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
    assert not needed & {'r36t','r37l'},('Outside current closure',group,needed & {'r36t','r37l'})
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
    paths=set(check.source_pins())|{'scripts/compose_scholarly_mission.py','scripts/compose_clerical_public_freedom.py',CONTROLS,'scripts/check_kant_clerical_public_freedom_content_visible.py',
        'tests/test_kant_clerical_public_freedom_content_visible.py'}
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



@lru_cache(None)
def qualification_checks():
    from noema.constructed_semantics import Content
    from scripts import check_reviewed_thoughts as past
    saved=check.read(past.REPORT);doc=past.fixture();rows={}
    for variant,expected in saved['native']['contrasts'].items():
        actual=run_current('qualification',doc,past.model(doc,variant),past.DOMAIN,past.SCENES)
        assert actual==[expected],(variant,actual);rows[variant]=actual[0]
    for truth in (False,True):
        values=past.model(doc)|dict(zcontent=lambda s:Content(past.SCENES,(truth,)*3),hzxp=lambda *args:truth)
        assert run_current('qualification',doc,values,past.DOMAIN,past.SCENES)==[True]
    independent={}
    for variant,expected in saved['bindings']['independent_ownership_review_and_care'].items():
        actual=[]
        for name in ('r36m','r36n','r36q','r36r'):
            fixture=past.fixture(name);values=past.model(fixture,variant)
            if name=='r36n':values['znow']=lambda:'past'
            actual+=run_current('qualification',fixture,values,past.DOMAIN,past.SCENES)
        assert actual==expected,(variant,actual);independent[variant]=actual
    result=dict(contrasts=rows,independent_ownership_review_and_care=independent,
        actual_review_body_checked=True,content_truth_and_realized_benefit_not_required=True,
        outside_closure_r36t_not_used=True)
    RESULTS['qualification']=result;return result


def constants(names):
    return [dict(kind='primitive',name=name,parameters=[],result=sort) for name,sort in names]


@lru_cache(None)
def review_binding_checks():
    from noema.constructed import parse
    from scripts import check_reviewed_thoughts as past
    rows=[]
    for slot in range(2):
        bindings=tuple('person' if i==slot else 'thought' for i in range(2))
        old=past.fixture('r36o',bindings)
        extras=parse('p:'+past.EXTRA)['declarations']
        doc=current_fixture(old['statements'],extras,('r36n',))
        expected=tuple('x' if i==slot else 'y' for i in range(2));visits=set()
        def target(person,thought,review,at):
            visits.add((person,thought,review,at));return (person,thought,review,at)==(*expected,'x','now')
        values=dict(zperson=lambda:'x',zthought=lambda:'y',znow=lambda:'now',r36n=target)
        assert run_current('review_binding',doc,values,('x','y'),('now',))==[True]
        assert (*expected,'x','now') in visits
        wrong=list(expected);wrong[slot]='y'
        values['r36n']=lambda p,t,r,at:(p,t,r,at)==(*wrong,'x','now')
        assert run_current('review_binding',doc,values,('x','y'),('now',))==[False]
        rows.append(slot)
    for length in (0,1,3):
        old=past.fixture('r36o',('person',)*length)
        doc=current_fixture(old['statements'],extras,('r36n',))
        assert run_current('review_binding',doc,dict(zperson=lambda:'x',znow=lambda:'now',r36n=lambda *args:True),('x','y'),('now',))==[False]
    result=dict(independently_checked_positions=rows,wrong_lengths=[0,1,3],two_distinguishing_values=True,
        native_r36n_separately_checked=True,full_domain_proof=False)
    RESULTS['review_binding']=result;return result


@lru_cache(None)
def mission_document():
    from noema.constructed import parse
    from scripts import check_scholarly_mission as past
    from scripts.shared_modality import call
    args=[call('zx') for _ in past.NAMES]+[call('zref')]
    ev=lambda n,params:dict(kind='evaluate',content=call(n,*params),situation=call('zpoint'))
    freedom=ev('r37j',args);calling=ev('r37k',args)
    statements=[dict(kind='ask',body=n) for n in (freedom,calling,
        dict(kind='and',arguments=[deepcopy(freedom),deepcopy(calling)]),
        ev('r37h',[call('zx') for _ in past.POLICY]+[call('zref')]))]
    return current_fixture(statements,parse('p:'+past.EXTRA)['declarations'],past.BOUNDARIES)


@lru_cache(None)
def mission_scope_checks():
    from scripts import check_scholarly_mission as past
    doc=mission_document();rows={}
    for variant,expected in check.read(past.REPORT)['scope']['contrasts'].items():
        actual=run_current('mission_scope',doc,past.model(variant),past.DOMAIN,past.TIMES)
        assert actual==expected,(variant,actual);rows[variant]=actual
    result=dict(contrasts=rows,current_r37j_r37k_r37h_bodies=True,explicit_conjunction=True,
        excluded_r37l_not_executed=True,boundaries=list(past.BOUNDARIES),
        all_candidates_both_item_classes_and_periods_checked=True)
    RESULTS['mission_scope']=result;return result


@lru_cache(None)
def mission_independence_checks():
    from scripts import check_scholarly_mission as past
    from scripts.check_motive_causes import unknown
    rows=[];doc=mission_document()
    for row in check.read(past.REPORT)['independence']['truth_table']:
        bits=tuple(row[k] for k in ('allowed','banned','called'))
        actual=run_current('mission_independence',doc,past.model(bits=bits),past.DOMAIN,past.TIMES)
        assert actual==row['results'],(bits,actual);rows.append(row)
    doc=deepcopy(doc);doc['statements']=doc['statements'][:3];values=past.model()
    for name in ('r36y','r367','h7q','h7r','ic'):values[name]=unknown
    assert run_current('mission_independence',doc,values,past.DOMAIN,past.TIMES)==[True]*3
    result=dict(truth_table=rows,calling_and_freedom_independent=True,quoted_mission_not_executed=True)
    RESULTS['mission_independence']=result;return result


@lru_cache(None)
def adapter_binding_checks():
    from noema.constructed import parse
    from noema.constructed_semantics import Content
    from scripts import check_scholarly_mission as past
    from scripts.shared_modality import call
    rows={};extras=parse('p:'+past.EXTRA)['declarations']
    for target,inner,names in [('r37a','r36y',past.THOUGHT),('r37b','r367',past.PROPOSAL),('r37i','r37h',past.POLICY)]:
        definition=recovered()[target];body=deepcopy(definition['body']);assert body['kind']=='content'
        point=body['variable'];body=body['body'];variables=[]
        for _ in names:
            assert body['kind']=='exists' and body['sort']=='individual'
            variables.append(body['variable']);body=body['body']
        assert body['kind']=='and'
        slots=[]
        for position in range(len(names)):
            inputs=tuple('x' if i==position else 'y' for i in range(len(names)))
            original,actual_inner,_=past.adapter(target,inputs);assert actual_inner==inner
            invocation=original['statements'][0]['body']['content']
            assert invocation['symbol']==target
            mapping={p['name']:arg for p,arg in zip(definition['parameters'],invocation['arguments'])}
            mapping[point]=call('zpoint')
            mapping.update({n:call('zy') for i,n in enumerate(variables) if i!=position})
            node=dict(kind='exists',variable=variables[position],sort='individual',body=substituted(body,mapping))
            doc=current_fixture([dict(kind='ask',body=node)],extras,(inner,));visits=set()
            def result(*args):
                visits.add(args);return Content(past.TIMES,tuple(args==(*inputs,'reference') and at=='late' for at in past.TIMES))
            values=dict(zx=lambda:'x',zy=lambda:'y',zref=lambda:'reference',zpoint=lambda:'late');values[inner]=result
            assert run_current('adapter_binding',doc,values,past.DOMAIN,past.TIMES)==[True],(target,position)
            assert (*inputs,'reference') in visits
            assert all(len(args)==len(names)+1 and args[-1]=='reference' and all(value==('x' if i==position else 'y') or i==position and value=='y' for i,value in enumerate(args[:-1])) for args in visits)
            wrong=tuple('y' for _ in names)+('reference',)
            values[inner]=lambda *args:Content(past.TIMES,tuple(args==wrong for _ in past.TIMES))
            assert run_current('adapter_binding',doc,values,past.DOMAIN,past.TIMES)==[False],(target,position)
            slots.append(position)
        # The original adapter is also executed without query instantiation.
        for count in (len(names),0,len(names)-1,len(names)+1):
            original,_,_=past.adapter(target,('x',)*count)
            doc=current_fixture(original['statements'],extras,(inner,))
            values=dict(zx=lambda:'x',zy=lambda:'x',zref=lambda:'reference',zpoint=lambda:'late')
            values[inner]=lambda *args:Content(past.TIMES,(True,)*len(past.TIMES))
            assert run_current('adapter_binding',doc,values,('x',),past.TIMES)==[count==len(names)],(target,count)
        rows[target]=dict(independently_checked_positions=slots,wrong_lengths=[0,len(names)-1,len(names)+1],
            original_adapter_executed_on_single_value=True,other_existential_binders_instantiated=True,
            two_distinguishing_values_per_slot=True,full_cartesian_domain_enumerated=False)
    RESULTS['adapter_binding']=rows;return rows


def outer_document(name,slot=0):
    from scripts.shared_modality import call
    d,point,variables,body=quantified_parts(name,9)
    assert body['kind']=='implies' and body['arguments'][0]['symbol']=='r35t'
    extras=constants([('jfixed'+letter,'individual') for letter in 'abcdefghi']+[('jpoint','situation')])
    bindings={n:call('jfixed'+'abcdefghi'[i]) for i,n in enumerate(variables) if i!=slot}
    bindings[point]=call('jpoint')
    node=dict(kind='forall',variable=variables[slot],sort='individual',body=substituted(body,bindings))
    return current_fixture([dict(kind='ask',body=node)],extras,('r35t','r37j','r37k'))


def outer_values(name,slot=0,variant='baseline'):
    from noema.constructed_semantics import Content
    scenes=('reference','late');cases=set();forwarded=set();roles=set();selected=tuple('y' if i==slot else 'x' for i in range(9))
    candidates={tuple(value if i==slot else 'x' for i in range(9))+('reference',) for value in ('x','y')}
    expected=(selected[0],selected[0],selected[2],selected[6],selected[7],'reference')
    def case(*args):cases.add(args);return variant!='no_case' and args==(*selected,'reference')
    def scholar(person,ref):
        roles.add((person,ref));return ('y' if person=='x' else 'x') if variant=='wrong_scholar' else person
    def content(*args):
        forwarded.add(args)
        wanted=expected[:-1]+('other' if variant=='wrong_reference' else 'reference',)
        return Content(scenes,tuple(args==wanted and variant!='one_failure' and at==('reference' if variant=='wrong_point' else 'late') for at in scenes))
    values={'jfixed'+letter:(lambda:'x') for letter in 'abcdefghi'}
    values.update(jpoint=lambda:'late',h232v=lambda:'reference',r35t=case,h247d=scholar,
        cd=lambda role,ref:variant!='not_scholarly' and (role,ref)==(selected[0],'reference'))
    values['r37j' if name=='r37m' else 'r37k']=content
    return values,dict(cases=cases,forwarded=forwarded,roles=roles,candidates=candidates,expected=expected)


@lru_cache(None)
def outer_binding_checks():
    rows=[]
    for name in ('r37m','r37n'):
        for slot in range(9):
            doc=outer_document(name,slot);contrasts={}
            for variant in ('baseline','one_failure','wrong_reference','wrong_point','wrong_scholar','not_scholarly','no_case'):
                values,seen=outer_values(name,slot,variant)
                actual=run_current('outer_binding',doc,values,('x','y'),('reference','late'))
                assert actual==[variant in ('baseline','no_case')],(name,slot,variant,actual)
                assert seen['cases']<=seen['candidates']
                if variant in ('baseline','no_case'):assert seen['cases']==seen['candidates']
                if variant=='baseline':assert seen['expected'] in seen['forwarded']
                contrasts[variant]=actual[0]
            rows.append(dict(target=name,slot=slot,contrasts=contrasts))
    result=dict(slots=rows,current_binder_bodies_used=True,other_binders_instantiated=True,
        two_distinguishing_values=True,full_cartesian_domain_enumerated=False,unbounded_equivalence_proved=False)
    RESULTS['outer_binding']=result;return result


@lru_cache(None)
def selected_unknown_checks():
    from scripts import check_scholarly_mission as mission
    from scripts import check_clerical_public_freedom as integration
    from scripts.check_motive_causes import unknown
    cases=[(mission_document(),mission.model(),mission.DOMAIN,mission.TIMES,
        ('r36v','r364','r36x','r366','r36y','r367','h245c','h237z','h247b','h247c','h7q','h7r','ic'))]
    doc=outer_document('r37m');values,_=outer_values('r37m')
    cases.append((doc,values,('x','y'),('reference','late'),('r35t','h247d','cd','r37j')))
    doc=integration.fixture('r37q',())
    cases.append((doc,integration.discourse_model(doc),integration.DISCOURSE,integration.TIMES,('h236i','h245k','h236k','ue')))
    rows=[]
    for doc,values,people,scenes,names in cases:
        for name in names:
            try:run_current('selected_unknown',doc,values|{name:unknown},people,scenes)
            except ValueError as error:assert 'Unknown' in str(error),str(error)
            else:raise AssertionError(name)
            rows.append(name)
    result=dict(unknown_required_inputs_refused=rows,qualification_and_classification_unknowns_replayed_separately=True)
    RESULTS['selected_unknown']=result;return result

def build_report():
    qualification_checks();review_binding_checks();mission_scope_checks();mission_independence_checks()
    adapter_binding_checks();outer_binding_checks();selected_unknown_checks();whole_connection_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-clerical-public-freedom-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        required_remaining_gates=['actual_svg_production','independent_cli','full_audit'],
        limitations=['Finite binding diagnostics are not full-domain equivalence proofs.',
            'Native diagnostics do not complete visible production gates.'])


def freedom_instance(arguments):
    """One thought/proposal instance of the original r37j query body."""
    from scripts.shared_modality import call
    d=recovered()['r37j'];body=deepcopy(d['body']);assert body['kind']=='content'
    clauses=body['body'];assert clauses['kind']=='and' and len(clauses['arguments'])==2
    for i,names in enumerate((('thought','judgment','beneficiary'),('proposal','field','older','newer','standard'))):
        inner=clauses['arguments'][i];mapping={}
        for name in names:
            assert inner['kind']=='forall' and inner['sort']=='individual'
            mapping[inner['variable']]=call('z'+name);inner=inner['body']
        clauses['arguments'][i]=substituted(inner,mapping)
    return substituted(body,{p['name']:arg for p,arg in zip(d['parameters'],arguments)})


@lru_cache(None)
def whole_document():
    from noema.constructed import parse
    from scripts import check_confessional_teaching as confession,check_reviewed_thoughts as review
    from scripts import check_reform_proposals as proposal,check_scholarly_mission as mission
    from scripts.shared_modality import call
    all_extras=[]
    for text in (confession.EXTRA+confession.PROVIDERS,review.EXTRA+review.PROVIDER):
        all_extras+=parse('p:'+text)['declarations']
    # The proposal fixture's alternative-code alias is unused by this model
    # and has a different type from the thought fixture's content alias.
    all_extras+=constants([('z'+n,'individual') for n in proposal.DOMAIN]+[('zref','situation'),('zpoint','situation')])
    extras={};providers={}
    for d in all_extras:
        if d['name'] in ('h246e','h246j','h224y'):providers[d['name']]=d;continue
        if d['name'] in extras:assert d==extras[d['name']],d['name']
        extras[d['name']]=d
    ev=lambda node:dict(kind='evaluate',content=node,situation=call('zpoint'))
    case_args=[call('z'+n) for n in confession.NAMES]+[call('zref')]
    thought_args=[call('z'+n) for n in ('person','thought','judgment','beneficiary','creed')]+[call('zref')]
    proposal_args=[call('z'+n) for n in ('person','proposal','church','field','subject','older','newer','standard')]+[call('zref')]
    names_thought=('person','scholar','creed','thought','judgment','beneficiary')
    names_proposal=('person','scholar','church','subject','proposal','field','older','newer','standard')
    mission_args=[call('z'+n) for n in mission.NAMES]+[call('zref')]
    nodes=[call('r35t',*case_args),call('r36v',*thought_args),call('r364',*proposal_args),
        call('r36x',*([call('z'+n) for n in mission.THOUGHT]+[call('zref')])),
        call('r366',*([call('z'+n) for n in mission.PROPOSAL]+[call('zref')])),
        ev(call('r37d',*([call('z'+n) for n in names_thought]+[call('zref')]))),
        ev(call('r37e',*([call('z'+n) for n in names_proposal]+[call('zref')]))),
        ev(freedom_instance(mission_args)),ev(call('r37k',*mission_args))]
    def replace_freedom(node):
        if isinstance(node,list):return [replace_freedom(n) for n in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node['symbol']=='r37j':return freedom_instance(node['arguments'])
        return {k:replace_freedom(v) for k,v in node.items()}
    contents={}
    for name in ('r37m','r37n'):
        d,point,variables,inner=quantified_parts(name,9)
        content=dict(kind='content',variable=point,body=substituted(inner,
            {v:call('z'+n) for v,n in zip(variables,confession.NAMES)}))
        contents[name]=replace_freedom(content);nodes.append(ev(contents[name]))
    whole=deepcopy(recovered()['r37o']['body'])
    assert [arg['content'] for arg in whole['body']['arguments']]==[call('r37m'),call('r37n')]
    for arg,name in zip(whole['body']['arguments'],('r37m','r37n')):arg['content']=deepcopy(contents[name])
    nodes.append(ev(whole))
    doc=current_fixture([dict(kind='ask',body=node) for node in nodes],list(extras.values()),providers=providers.values())
    for d in doc['declarations']:
        if d['name'] in recovered():assert d==recovered()[d['name']],d['name']
    return doc


def whole_people():
    from scripts import check_confessional_teaching as confession,check_reviewed_thoughts as review
    from scripts import check_reform_proposals as proposal
    return tuple(dict.fromkeys((*confession.DOMAIN,*review.DOMAIN,*proposal.DOMAIN,'criterion','source','frame')))


def whole_model(doc,variant='baseline'):
    from scripts import check_confessional_teaching as confession,check_reviewed_thoughts as review
    from scripts import check_reform_proposals as proposal,check_scholarly_mission as mission
    from scripts.check_motive_causes import unknown,symbol
    raw_case=confession.model(doc,variant);reviewed=review.model(doc,variant);proposed=proposal.model(doc,variant)
    inward={'now':'reference','future':'outcome'};outward={'reference':'now','outcome':'future'}
    def remapped(fn):
        def result(*args):
            result=fn(*(inward.get(a,a) if isinstance(a,str) else a for a in args))
            return outward.get(result,result) if isinstance(result,str) else result
        return result
    case={n:remapped(f) if f is not unknown else unknown for n,f in raw_case.items()}
    groups={'case':case,'review':reviewed,'proposal':proposed}
    names=set().union(*(set(v) for v in groups.values()));shared={}
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for name in names:
        fs=[v[name] for v in groups.values() if name in v and v[name] is not unknown]
        if len(fs)==1:values[name]=fs[0]
        elif len(fs)>1 and not name.startswith('z'):shared[name]=fs
    assert set(shared)=={'aa','dg','f3','h245z','h246d','h246h','h6t'},set(shared)
    # These predicates have the same reference-bound institutional meaning.
    for name in ('h245z','h246d','h246h','f3'):values[name]=case[name]
    # The case needs its pupils and members in the person universe. The review
    # and proposal also require the same person, not a new person identifier.
    values['aa']=case['aa']
    values['dg']=lambda act,at:reviewed['dg'](act,at) or case['dg'](act,at) or proposed['dg'](act,at)
    values['h6t']=lambda audience,person,ref:(proposed['h6t'](audience,person,ref)
        if audience=='audience' else case['h6t'](audience,person,ref))
    for n in whole_people():values['z'+n]=lambda n=n:n
    values.update(zref=lambda:'now',znow=lambda:'now',zpoint=lambda:'future',h232v=lambda:'now')
    # All four concepts remain distinct in the model: employment role, public
    # scholarly role, employing church and the public normative source.
    values.update(ca=lambda person,activity,ref:(person,activity,ref)==('person','activity','now'),
        cb=lambda person,activity,role,ref:(person,activity,role,ref)==('person','activity','scholar','now'),
        cd=lambda role,ref:(role,ref)==('scholar','now'),
        cc=lambda activity,audience,ref:variant!='no_public_candidate' and (activity,audience,ref)==('activity','audience','now'),
        ce=lambda audience,ref:(audience,ref)==('audience','now'),
        h247d=lambda person,ref:'role' if variant=='wrong_scholar' else 'scholar',
        h247b=lambda person,scholar,ref:'church' if variant=='wrong_norm_source' else 'source',
        h247c=lambda person,scholar,ref:'frame',
        h243x=lambda thought,creed,criterion,code,ref:variant!='no_topic' and
            (thought,creed,criterion,symbol(code),code.rank,ref)==('thought','creed','criterion','r326',0,'now'))
    def correct(source,person,role,code,bindings,ref,sign,point,target):
        names=mission.THOUGHT if target=='r37a' else mission.PROPOSAL if target=='r37b' else mission.POLICY
        return (source,person,role,symbol(code),code.rank,tuple(bindings.items),ref,sign,point)==(
            'source','person','scholar',target,1,tuple(names),'now',True,'future')
    def permission(*args):
        target=symbol(args[3]);return target in ('r37a','r37b') and correct(*args,target) and variant!=(
            'no_thought_permission' if target=='r37a' else 'no_proposal_permission')
    def requirement(*args):
        target=symbol(args[3])
        if target=='r37i':return correct(*args,target) and variant!='not_called'
        if target not in ('r37a','r37b'):return False
        positive=(*args[:6],True,args[7])
        return not args[6] and correct(*positive,target) and variant==('thought_banned' if target=='r37a' else 'proposal_banned')
    values.update(h245c=permission,h237z=requirement)
    for name in ('zbelief','zcontent','h243u','h243v','h246y','h247a','h7q','h7r'):
        values[name]=unknown
    return values


@lru_cache(None)
def whole_connection_checks():
    from scripts.check_motive_causes import unknown
    doc=whole_document();people=whole_people();scenes=('past','now','future');rows={}
    cases=('baseline','missing_pupil','not_profession','unowned','unfinished','no_attention','no_goodwill',
        'no_topic','not_proposal','no_baseline','no_public_candidate','no_thought_permission',
        'no_proposal_permission','thought_banned','proposal_banned','not_called','wrong_scholar','wrong_norm_source')
    for variant in cases:
        case=variant not in ('missing_pupil','not_profession')
        thought=variant not in ('unowned','unfinished','no_attention','no_goodwill','no_topic')
        proposal=variant not in ('not_proposal','no_baseline')
        public=variant!='no_public_candidate'
        free_t=thought and public and variant not in ('no_thought_permission','thought_banned','wrong_norm_source')
        free_p=proposal and public and variant not in ('no_proposal_permission','proposal_banned','wrong_norm_source')
        free=(not thought or free_t) and (not proposal or free_p)
        called=variant not in ('not_called','wrong_norm_source');scholar=variant!='wrong_scholar'
        outer_free=not case or scholar and free;outer_call=not case or scholar and called
        expected=[case,thought,proposal,thought and public,proposal and public,free_t,free_p,
            free,called,outer_free,outer_call,outer_free and outer_call]
        actual=run_current('whole',doc,whole_model(doc,variant),people,scenes)
        assert actual==expected,(variant,actual,expected);rows[variant]=actual
    rejected=[]
    for name in ('h246f','zchoosebelief','hzv','h246t','h246u','h243x','h246z','ca','h247d','h247b','h245c','h237z'):
        try:run_current('whole',doc,whole_model(doc)|{name:unknown},people,scenes)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
        rejected.append(name)
    result=dict(contrasts=rows,unknown_required_inputs_refused=rejected,
        actual_case_qualification_proposal_public_candidate_and_norms_connected=True,
        source_definitions_unmodified=True,outer_and_item_query_binders_explicitly_instantiated=True,
        candidate_activity_and_audience_quantifiers_retained=True,
        role_church_scholar_and_norm_source_distinct=True,
        quoted_truth_improvement_and_mission_not_executed=True,full_domain_proof=False)
    RESULTS['whole_connection']=result;return result
