"""Recover convenience composition, keeping the state abstraction explicit."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType
import json
from noema.constructed_discourse import normalize_document
from noema.finite_semantics import evaluate_document
from noema.constructed_semantics import evaluate_document as constructed_evaluate
from noema.meaning_catalog import _references
from scripts import check_kant_convenience_visible as check
from scripts import check_state_convenience as retained
from scripts.shared_modality import call, v

RESULTS={}
RECOVERED=set()


@lru_cache(None)
def recovered():
    actual=check.restored()['document']
    assert check.backprojection(actual)==check.source_excerpt()
    result=check.specialized_backprojection(actual)
    assert result==check.specialized_source()
    return {d['name']:d for d in result['declarations']}


def select(doc):
    ds={d['name']:d for d in doc['declarations']};needed=set();pending=_references(doc['statements'])
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.update(_references(ds[name].get('body')))
    result=deepcopy(doc)
    result['declarations']=[d for d in result['declarations'] if d['name'] in needed]
    result['declarations'].sort(key=lambda d:d['kind']!='primitive')
    return normalize_document(result)


def generic_state_checks():
    ns=dict(vars(retained))
    for name,fn in vars(retained).items():
        if isinstance(fn,FunctionType) and fn.__module__==retained.__name__:
            copied=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__)
            copied.__kwdefaults__=fn.__kwdefaults__;ns[name]=copied
    def evaluated(doc,*,primitives,**options):
        actual=select(doc)
        for index,d in enumerate(actual['declarations']):
            if d['kind']=='definition':
                assert d['name'] in recovered() and d==recovered()[d['name']],d['name']
                actual['declarations'][index]=deepcopy(recovered()[d['name']]);RECOVERED.add(d['name'])
        selected={d['name']:primitives[d['name']] for d in actual['declarations'] if d['kind']=='primitive'}
        return evaluate_document(actual,primitives=selected,**options)
    ns['evaluate_document']=evaluated
    result=ns['state_checks']()
    assert result==check.read('reports/state-convenience-v1.json')['state']
    RESULTS['state']=result
    return result


def primitive(name,parameters,result):
    return dict(kind='primitive',name=name,parameters=parameters,result=result)


def fixture():
    ds=deepcopy(recovered());bf=ds['bf'];person=bf['parameters'][0]['name']
    assert bf['body']['kind']=='content'
    scene=bf['body']['variable']
    # Only the lower state predicate is abstracted. In particular uj, rk, ul,
    # un and the selected-method conditions retain their recovered bodies.
    bf['body']=dict(kind='content',variable=scene,body=call('jstate',v(person),v(scene)))
    extra=[primitive('jstate',['individual','situation'],'truth'),
        primitive('jperson',[],'individual'),primitive('jcontext',[],'situation')]
    statements=[dict(kind='ask',body=dict(kind='evaluate',content=call(name,*args),situation=call('jcontext')))
        for name,args in [('ul',[call('jperson')]),('un',[])]]
    return select(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=extra+list(ds.values()),statements=statements))


def model(doc,variant='baseline',person='first',context='first',case='first'):
    result='second' if case=='first' else 'first';other='second' if person=='first' else 'first'
    seen=[]
    def forbidden(*args):raise ValueError('Unspecified convenience interpretation')
    values={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def candidates(subject,description,setting,scene):
        syntax=json.loads(description.syntax);seen.append((subject,syntax,setting,scene))
        assert syntax==dict(kind='function_ref',symbol='bf'),'State description changed'
        wanted=(other if variant=='wrong_case_person' else person,
            ('second' if context=='first' else 'first') if variant=='wrong_case_context' else context,
            result if variant=='wrong_case_scene' else case)
        return variant!='empty_cases' and ((subject,setting,scene)==wanted or
            (variant=='bad_second_case' and (subject,setting,scene)==(person,context,result)))
    def outcomes(subject,method,start,end):return (subject,method,start,end)==(person,'second',case,result)
    values.update(jperson=lambda:person,jcontext=lambda:context,
        jstate=lambda subject,scene:subject==person and not (
            variant=='initial_state_false' and scene==case or variant=='result_state_false' and scene==result),
        aa=lambda subject:variant!='not_human' and subject==person,
        stateconveniencecandidate=candidates,
        ae=lambda subject,method,start:variant!='no_method' and (subject,method,start)==(person,'second',case),
        af=outcomes,ap=lambda *args:variant!='empty_results' and outcomes(*args),
        oc=lambda *args:retained.Fraction(9 if variant=='high_burden' else 1),
        sj=lambda subject,scene:variant!='failed_goal' and (subject,scene)==(person,result),
        uk=lambda burden,setting:burden<=2 and setting==(
            ('second' if context=='first' else 'first') if variant=='wrong_standard_context' else context),
        um=lambda subject,setting:variant!='empty_people' and setting==context and (
            subject==person or variant=='bad_second_person'))
    return {name:values[name] for name in values if name in {d['name'] for d in doc['declarations'] if d['kind']=='primitive'}},seen


def run(doc,values):
    return [r['value'] for r in constructed_evaluate(doc,individuals=('first','second'),situations=('first','second'),
        primitives=values,max_steps=200000,memoize_definitions=False,memoize_expressions=False)]


def composition_checks():
    doc=fixture();rows={}
    variants=('baseline','initial_state_false','result_state_false','high_burden','failed_goal','no_method',
        'not_human','empty_results','empty_cases','empty_people','wrong_case_person','wrong_case_context',
        'wrong_case_scene','wrong_standard_context','bad_second_case','bad_second_person')
    for variant in variants:
        values,seen=model(doc,variant);actual=run(doc,values)
        expected=[variant in ('baseline','not_human','empty_people','bad_second_person'),variant=='baseline']
        assert actual==expected,(variant,actual,expected)
        assert seen
        rows[variant]=actual
    RESULTS['composition']=rows
    return rows


def source_pins():
    paths=set(check.source_pins())|{'scripts/check_kant_convenience_content_visible.py',
        'tests/test_kant_convenience_content_visible.py','reports/state-convenience-v1.json'}
    paths.update(check.read('reports/state-convenience-v1.json')['source_sha256'])
    return {p:check.digest(p) for p in sorted(paths)}


def build_report():
    if 'state' not in RESULTS:generic_state_checks()
    if 'composition' not in RESULTS:composition_checks()
    return dict(schema='noema-kant-convenience-content-visible-check-1',results=RESULTS,
        generic_recovered_definitions=sorted(RECOVERED),
        composition_recovered_definitions=[d['name'] for d in fixture()['declarations'] if d['kind']=='definition' and d['name']!='bf'],
        explicit_abstractions={'bf':'Only lower state truth is replaced by jstate; no current ability proof is claimed.'},
        legacy_source_checks_replayed=False,actual_uj_definition_executed=True,
        unknown_input_rejection=True,source_sha256=source_pins(),formal_integration_credit=0,
        limitations=['Finite binding and composition diagnostics, not a proof over the full domain.',
            'Current bf remains exact in backprojection; its ability semantics retain prior evidence.',
            'The caller fixes whether recovery used Native or actual SVG.'])
