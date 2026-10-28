"""Independent conditions and opaque lookup for the three opening referents."""
from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed_discourse import normalize_document,function_sort
from noema.constructed_semantics import DescriptionValue,evaluate_document
from scripts import early_reference_visible_profile as profile
from scripts import early_individual_reference_roles as roles
from scripts.observer_time_contracts import CONTRACTS as PROPAGATION
from scripts.name_presentation_profile import library as presentation_library
from scripts.temporal_discourse_profile import TemporalReferences,library as temporal_library
from noema.meaning_catalog import _references


def call(n,*args):return dict(kind='call',symbol=n,arguments=list(args))
canonical=lambda node:json.dumps(node,sort_keys=True,separators=(',',':'))
def forbidden(*args):raise AssertionError('Propagation or quoted candidate role was executed')


def document():
    doc=deepcopy(profile.library())
    r=PROPAGATION['radiationpropagation']
    doc['declarations'].append(dict(kind='primitive',name='radiationpropagation',parameters=r['parameters'],result=r['result']))
    doc['declarations'] += [d for d in presentation_library()['declarations'] if d['name'] in ('presentationholds','nameapplies')]
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in
        [('earlyearthtoken','individual'),('earlyearthdesignation','individual'),('eisbx','individual'),
         ('subject','individual'),('point','situation')]]
    doc['declarations'] += list(roles.build_roles().values())
    return normalize_document(doc)


def run(role,handlers,subject='x',point='a'):
    doc=document();doc['statements']=[dict(kind='ask',body=call('earlyrole'+role,call('subject'),call('point')))]
    base={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    base.update(earlyearthtoken=lambda:'token',earlyearthdesignation=lambda:'name',eisbx=lambda:'earth',
                subject=lambda:subject,point=lambda:point)
    base.update(handlers)
    return evaluate_document(doc,individuals=('x','y','earth','name','token'),situations=('a','b'),primitives=base)[0]['value']


def propagation_description(value):
    assert isinstance(value,DescriptionValue) and value.rank==0
    assert json.loads(value.result_type)==function_sort(['individual','individual','situation'],'truth')
    return json.loads(value.syntax)==dict(kind='function_ref',symbol='radiationpropagation')


def test_parameter_requires_ratio_limit_and_complete_directions_separately():
    for ratio,limit,coverage in product((False,True),repeat=3):
        def ratio_relation(candidate,kind,point):
            return ratio and candidate=='x' and propagation_description(kind) and point=='a'
        handlers=dict(signalvelocityratioparameter=ratio_relation,
            directionpreservingscalelimit=lambda candidate,point:limit and candidate=='x' and point=='a',
            completeparameterdirections=lambda candidate,point:coverage and candidate=='x' and point=='a')
        assert run('eisbo',handlers) is (ratio and limit and coverage)
        assert run('eisbo',handlers,subject='y') is False
        assert run('eisbo',handlers,point='b') is False


def test_named_earth_keeps_use_designation_target_and_context_distinct():
    for use,applies in product((False,True),repeat=2):
        handlers=dict(presentationholds=lambda node,point:use and (node,point)==('token','a'),
            nameapplies=lambda node,name,target,point:applies and (node,name,target,point)==('token','name','earth','a'))
        assert run('eisbx',handlers,subject='earth') is (use and applies)
        assert run('eisbx',handlers,subject='y') is False
        assert run('eisbx',handlers,subject='earth',point='b') is False
    assert run('eisbx',dict(presentationholds=lambda *xs:True,nameapplies=lambda *xs:True),subject='name') is False


def test_medium_classification_is_quoted_and_not_the_earth():
    seen=[]
    def hypothetical(candidate,kind,point):
        seen.append((candidate,kind,point))
        return propagation_description(kind) and point=='a'
    assert run('eisby',dict(hypothesizedpropagationmedium=hypothetical)) is True
    assert run('eisby',dict(hypothesizedpropagationmedium=hypothetical),subject='earth') is False
    assert run('eisby',dict(hypothesizedpropagationmedium=hypothetical),point='b') is False
    assert run('eisby',dict(hypothesizedpropagationmedium=lambda *xs:False)) is False
    assert len(seen)==3


@pytest.mark.parametrize('candidate',roles.CANDIDATES)
def test_opaque_reference_retrieval_does_not_execute_or_assert_its_role(candidate):
    role=DescriptionValue(canonical(dict(kind='function_ref',symbol='earlyrole'+candidate)),
        canonical(function_sort(['individual','situation'],'truth')),0)
    key=('paper',roles.ANCHORS[candidate],role.syntax,'body')
    lookup=TemporalReferences({key:'chosen'}, {})
    assert lookup.described('paper',roles.ANCHORS[candidate],role,'body')=='chosen'
    for slot in range(4):
        args=['paper',roles.ANCHORS[candidate],role,'body']
        args[slot]=DescriptionValue(canonical(dict(kind='function_ref',symbol='otherrole')),role.result_type,0) if slot==2 else 'unknown'
        with pytest.raises(ValueError,match='Unknown temporal reference'):lookup.described(*args)
    doc=document()
    doc['declarations'] += [d for d in temporal_library()['declarations'] if d['name']=='describedreference']
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result='individual') for n in ('paper','anchor','chosen')]
    quote=dict(kind='quote',body=dict(kind='function_ref',symbol='earlyrole'+candidate))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[
        call('describedreference',call('paper'),call('anchor'),quote,call('point')),call('chosen')]))]
    handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    handlers['describedreference']=lookup.described
    handlers.update(paper=lambda:'paper',anchor=lambda:roles.ANCHORS[candidate],chosen=lambda:'chosen',point=lambda:'body')
    result=evaluate_document(doc,individuals=('paper','chosen',roles.ANCHORS[candidate]),situations=('body',),primitives=handlers)
    assert result[0]['value'] is True
    # All role predicates, even the medium's Earth dependency, remain forbidden.


def test_roles_are_acyclic_and_do_not_encode_the_original_source_assertions():
    assert roles.dependency_graph()=={'eisbo':[],'eisbx':[],'eisby':['eisbx']}
    for role in roles.build_roles().values():
        assert not _references(role['body'])&{'eifp','eifl','eigr','eifv','eisbn'}
