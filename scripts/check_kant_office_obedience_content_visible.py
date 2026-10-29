"""Replay retained finite content diagnostics on exact recovered source bodies."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType,SimpleNamespace
import importlib
import json
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.finite_semantics import evaluate_document as finite_evaluate
from scripts import check_kant_office_obedience_visible as check

CONTROLS='data/kant-office-obedience-visible-diagnostic-controls-v1.json'
GROUPS={'office': ('scripts.check_office_obedience',
            'reports/office-obedience-v1.json',
            [['obedience_checks', 'obedience'],
             ['permission_checks', 'permission'],
             ['requirement_checks', 'requirement'],
             ['adapter_checks', 'adapter'],
             ['scope_checks', 'scope'],
             ['discourse_checks', 'discourse']])}
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
    paths=set(check.source_pins())|{CONTROLS,'scripts/check_kant_office_obedience_content_visible.py',
        'tests/test_kant_office_obedience_content_visible.py','scripts/check_public_purpose_mechanism.py','scripts/check_mechanism_requirements.py'}
    for module,report,functions in GROUPS.values():
        paths.add(module.replace('.','/')+'.py');paths.add(report)
        paths.update(check.read(report)['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}



def whole_fixture():
    from scripts import check_public_purpose_mechanism as purpose,check_mechanism_requirements as requirements
    source={d['name']:deepcopy(d) for d in check.source_excerpt()['declarations']}
    office=namespace('office');scope=office['fixture']('scope')
    for doc in (scope,requirements.fixture('requirements'),purpose.fixture('purpose')):
        for d in doc['declarations']:
            if d['name'] not in source or d['name'] in ('h232f','h237k'):source[d['name']]=deepcopy(d)
    statements=deepcopy(scope['statements']);result=[];seen=set();visiting=set()
    def visit(name):
        if name in seen:return
        assert name not in visiting,('Dependency cycle',name)
        visiting.add(name);d=source[name]
        for dependency in sorted(_references(d.get('body'))):visit(dependency)
        visiting.remove(name);seen.add(name);result.append(d)
    for name in sorted(_references(statements)):visit(name)
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=result,statements=statements)


@lru_cache(None)
def whole_content_checks():
    from noema.constructed_semantics import FunctionValue
    from scripts.check_motive_causes import symbol
    doc=whole_fixture();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[n]==recovered()[n] for n in ('r3m','r3n','r3c','r2zx','r3j','r3l'))
    domain=('source','person','secondperson','office','secondoffice','work','first','second','mechanism','community','government','arrangement','other')
    scenes=('reference','later');roles={'person':'office','secondperson':'secondoffice'}
    def unknown(*args):raise ValueError('Unknown whole office input')
    def model(variant='baseline'):
        values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        values.update(zp=lambda:'person',zrole=lambda:'office',zwork=lambda:'work',zr=lambda:'reference',
            zt=lambda:'reference' if variant=='wrong_evaluation_point' else 'later',h232v=lambda:'reference',
            aa=lambda p:p in roles,
            h237y=lambda w,r:variant!='empty_work_scope' and (w,r)==('work','reference'),
            h237h=lambda w,r:'mechanism',h237i=lambda w,r:'community',
            h237d=lambda m,w,r:FunctionValue(('individual',),'truth',lambda p:variant!='empty_members' and p in roles and (m,w,r)==('mechanism','work','reference')),
            h237e=lambda p,m,w,r:'other' if variant=='wrong_selected_role' and p=='person' else roles.get(p,'other'),
            h237f=lambda p,role,m,w,r:p in roles and (role,m,w,r)==(roles[p],'mechanism','work','reference'),
            h237c=lambda p,c,r:p in roles and (c,r)==('community','reference') and not (variant=='nonmember' and p=='person'),
            h237g=lambda m,w,r:'other' if variant=='wrong_norm_source' else 'source',
            h236w=lambda w,c,r:(w,c,r)==('work','community','reference'),
            h236y=lambda m,c,w,r:variant!='missing_background' and (m,c,w,r)==('mechanism','community','work','reference'),
            h232e=lambda m,code,w,r:(m,symbol(code),code.rank,w,r)==('mechanism','r2zt',1,'work','reference'),
            zrequiredcode=lambda m,r,right,wrong:right,
            h237m=lambda w,r:'government',h237o=lambda m,w,r:'arrangement',zgoalcode=lambda w,r,goal,other:goal,
            h237n=lambda g,c,r:(g,c,r)==('government','community','reference'),
            h237l=lambda code,c,w,r:variant!='private_goal_only' and (symbol(code),c,w,r)==('zgoal','community','work','reference'),
            h237u=lambda m,w,means,end,r:variant!='missing_purpose' and (m,w,symbol(means),means.rank,symbol(end),end.rank,r)==('mechanism','work','r3b',1,'r3a',1,'reference'),
            ca=lambda p,act,r:p in roles and act in ('first','second') and r=='reference',
            h232p=lambda act,r:act in ('first','second') and r=='reference',
            cb=lambda p,act,role,r:p in roles and act in ('first','second') and (role,r)==(roles[p],'reference'),
            h237x=lambda p,role,w,act,r:p in roles and (role,w,act,r)==(roles[p],'work','first','reference'))
        def background_requirement(source,p,role,code,bindings,sign,r):
            return p in roles and (source,role,symbol(code),code.rank,tuple(bindings.items),sign,r)==('source',roles[p],'r2zv',0,(p,roles[p],'work'),True,'reference')
        def permission(source,p,role,act,code,sign,point):
            target='secondperson' if variant=='second_person_permission' else 'person'
            return variant in ('permission_present','second_person_permission') and p==target and (source,role,act,symbol(code),sign,point)==('source',roles[p],'first','zzq',True,'later')
        def requirement(source,p,role,code,bindings,r,sign,point):
            if p not in roles or variant=='second_requirement_absent' and p=='secondperson':return False
            expected_bindings=(roles[p],p,'work') if variant=='wrong_bindings' else (p,roles[p],'work')
            return (source,role,symbol(code),code.rank,tuple(bindings.items),r,sign,point)==('source',roles[p],'r3k',1,expected_bindings,'reference',True,'later')
        values.update(h7k=background_requirement,h7b=permission,h237z=requirement)
        return values
    def run(values):
        return [r['value'] for r in evaluated('whole',doc,primitives=values,individuals=domain,situations=scenes,max_steps=10000000,memoize_definitions=True,memoize_expressions=True)]
    expected={'baseline':[True,True],'empty_work_scope':[False,False],'empty_members':[False,False],
        'wrong_selected_role':[False,False],'nonmember':[False,False],'missing_background':[True,False],
        'wrong_norm_source':[True,False],'private_goal_only':[True,False],'missing_purpose':[True,False],
        'permission_present':[True,False],'second_person_permission':[True,False],'second_requirement_absent':[True,False],
        'wrong_bindings':[True,False],'wrong_evaluation_point':[True,False]}
    rows={}
    for variant,wanted in expected.items():
        actual=run(model(variant));assert actual==wanted,(variant,actual);rows[variant]=actual
    for name in ('h7a','h234b','cg','h236x','h236z','h237a','h237b','h237s','h237t','zgoal'):
        assert run(model()|{name:unknown})==[True,True]
    for name in ('h7b','h237z','h232e','h237u'):
        try:run(model()|{name:unknown})
        except ValueError as error:assert 'Unknown whole office input' in str(error)
        else:raise AssertionError(name)
    result=dict(contrasts=rows,current_background_and_office_content_connected=True,all_fixed_people_checked=True,
        fulfillment_and_goal_truth_not_executed=True,unknown_permission_not_denial=True,full_description_domain_verified=False)
    RESULTS['whole']=result
    return result


def build_report():
    whole_content_checks()
    for group,(_,_,functions) in GROUPS.items():
        for function,key in functions:
            if key not in RESULTS.get(group,{}):replay(group,function,key)
    return dict(schema='noema-kant-office-obedience-content-visible-check-1',results=RESULTS,
        recovered_evaluation_calls=EVALUATION_CALLS,
        structural_witness_declarations=[],
        recovered_definitions={k:sorted(v) for k,v in RECOVERED_DEFINITIONS.items()},
        historical_comparison_bodies={k:sorted(v) for k,v in HISTORICAL_COMPARISONS.items()},
        fixture_only_definitions={k:sorted(v) for k,v in FIXTURE_ONLY_DEFINITIONS.items()},
        source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['有限診断と元の意味判断を区別する。全領域の証明ではない。',
            '明示的に保存した過去の比較用定義を、回収した現在の本体の実行確認には数えない。',
            'Nativeか実SVG回収かは呼出し側のproduction evidenceに固定する。'])
