from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.shared_reference import lam
from scripts.shared_generality import *
from scripts.check_shared_generality import (
    ref,doc,model,values,unknown,PEOPLE,THREE,generic,degree,compare,scale_args,
    generic_checks,kind_checks,order_checks,criterion_checks,standard_checks,comparison_checks,modal_checks,
    modal_composition_checks,example,example_model,EXAMPLE)


def test_ten_previous_definitions_and_meanings_are_exactly_reused():
    shared={d['name']:d for d in composed()['declarations']};b=basis();count=0
    for source in SOURCES:
        old=parse((ROOT/source['document']).read_text(encoding='utf-8'))
        meanings=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))['definitions']
        for d in old['declarations']:
            if d['name'] in source['names']:
                target=source['names'][d['name']]
                assert shared[target]==renamed(d,source['names'])
                assert b['definitions'][target]==meanings[d['name']]
                count+=1
    assert count==10 and len(shared)==23
    assert all(d['kind']=='definition' for d in shared.values())


def test_published_native_and_contracts_preserve_all_roles_and_types():
    d=composed();b=basis()
    assert d==parse(format_graph(d))==parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    assert b==json.loads((ROOT/BASIS).read_text(encoding='utf-8'))
    assert set(b['definitions'])==set(b['public_contracts'])=={x['name'] for x in d['declarations']}
    for declaration in d['declarations']:
        contract=b['public_contracts'][declaration['name']]
        assert [r['sort'] for r in contract['arguments']]==[p['sort'] for p in declaration['parameters']]
        assert len({r['role'] for r in contract['arguments']})==len(declaration['parameters'])
        assert contract['result']==declaration['result']


def test_normal_case_and_kindwise_models():
    assert generic_checks()['models']==256
    assert kind_checks()['models']==1024


def test_scale_order_criteria_classification_and_comparison_models():
    assert order_checks()==dict(models=512,domain_size=3,accepted=6,bounded_accepted=1)
    assert criterion_checks()['models']==64
    assert standard_checks()['models']==64
    assert comparison_checks()['models']==36


def test_reused_modal_definitions_preserve_all_six_compositions():
    assert modal_checks()['models']==48
    rows=modal_composition_checks()
    assert len(rows)==27 and all(len(r['result'])==6 for r in rows)


def test_integrated_birds_and_height_readings():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model(),THREE)==[True,False,True,False,False,True,True,True,True,True]


def test_empty_generalization_is_not_vacuous_universal():
    m=example_model();m['cases']=lambda x:False
    assert values(doc([generic(),call('caseuniversal',ref('cases'),ref('response'))]),m)==[False,True]


def test_exception_does_not_follow_for_an_unclassified_individual():
    m=example_model();m.update(cases=lambda x:x=='a',response=lambda x:x=='a')
    assert values(doc([call('caseexception',call('bob'),ref('cases'),ref('response'))]),m)==[False]


def test_incomparable_normal_counterexample_invalidates_generalization():
    m=example_model();m['preferred']=lambda x,y:False
    assert values(doc([generic()]),m)==[False]


def test_pooling_kinds_cannot_hide_an_entire_kind():
    m=example_model();m.update(cases=lambda x:x=='a',secondcases=lambda x:x=='b')
    pooled=lam([('item',I)],op('or',call('cases',v('item')),call('secondcases',v('item'))))
    # A successful first kind dominates a failing second kind in the pool.
    d=doc([call('casegeneric',pooled,ref('preferred'),ref('response')),
        call('kindwisegeneric',ref('cases'),ref('secondcases'),ref('preferred'),ref('response'))])
    assert values(d,m)==[True,False]


def test_three_case_nontransitive_priority_is_rejected():
    m=example_model();m.update(cases=lambda x:True,response=lambda x:True,
        preferred=lambda x,y:(x,y) in {('a','b'),('b','c')})
    assert values(doc([call('normalorder',ref('cases'),ref('preferred')),generic()]),m,THREE)==[False,False]


def test_generalization_is_not_a_majority_vote():
    m=example_model();m.update(cases=lambda x:True,response=lambda x:x=='a',
        preferred=lambda x,y:x=='a' and y!='a')
    assert values(doc([generic(),call('caseuniversal',ref('cases'),ref('response'))]),m,THREE)==[True,False]


def test_comparison_can_hold_below_positive_standard_and_goal_can_differ():
    m=example_model();m['assignment']=lambda x:'b' if x=='a' else 'a'
    assert values(doc([compare('degreemore'),degree('degreepositive'),degree('degreeborderline'),
        call('degreeenough',call('alice'),ref('assignment'),*scale_args(),ref('criterion'))]),m,THREE)==[True,False,True,True]


def test_same_degree_does_not_require_same_subject():
    m=example_model();m['assignment']=lambda x:'b'
    assert values(doc([compare('degreeequal'),compare('degreemore'),compare('degreenotless')]),m,THREE)==[True,False,True]


def test_outside_scale_is_not_borderline_or_enough():
    m=example_model();m.update(scale=lambda x:x!='b',positive=lambda x:x=='c',negative=lambda x:x=='a',criterion=lambda x:x=='c')
    assert values(doc([degree(n,'bob') for n in ('degreepositive','degreenegative','degreeborderline')]+[
        call('degreeenough',call('bob'),ref('assignment'),*scale_args(),ref('criterion'))]),m,THREE)==[False]*4


def test_overlap_and_nonmonotone_standards_do_not_classify():
    for pos,neg in (({'a','b','c'},{'a'}),({'b'},{'a'}),({'c'},{'b'})):
        m=example_model();m.update(positive=lambda x:x in pos,negative=lambda x:x in neg)
        assert values(doc([call('standardsvalid',*scale_args(),ref('positive'),ref('negative')),
            degree('degreeborderline','bob')]),m,THREE)==[False,False]


@pytest.mark.parametrize('name',['cases','preferred','response'])
def test_unknown_generic_input_is_not_false(name):
    m=example_model();m[name]=unknown
    with pytest.raises(ValueError,match='Unknown'):values(doc([generic()]),m)


@pytest.mark.parametrize('name',['assignment','scale','less','positive','negative'])
def test_unknown_degree_input_is_not_borderline(name):
    m=example_model();m[name]=unknown
    with pytest.raises(ValueError,match='Unknown'):values(doc([degree('degreeborderline','bob')]),m,THREE)


def test_unknown_purpose_is_not_adjective_negation():
    m=example_model();m['criterion']=unknown
    assert values(doc([degree('degreepositive','charlie')]),m,THREE)==[True]
    with pytest.raises(ValueError,match='Unknown'):
        values(doc([call('degreeenough',call('bob'),ref('assignment'),*scale_args(),ref('criterion'))]),m,THREE)


def test_subject_and_criterion_slots_are_distinguished():
    # Hold other interpretations fixed; vary each slot over two values/functions.
    m=example_model();m.update(positive=lambda x:x=='b',negative=lambda x:x=='a',criterion=lambda x:x=='b')
    assert values(doc([degree('degreepositive',s) for s in ('alice','bob')]),m)==[False,True]
    d=doc([call('degreeenough',call('bob'),ref('assignment'),*scale_args(),ref(n)) for n in ('positive','negative')])
    # The downward negative set is not an upward purpose criterion.
    assert values(d,m)==[True,False]
    m['assignment']=lambda x:'b' if x=='a' else 'a'
    assert values(doc([degree('degreepositive',s) for s in ('alice','bob')]),m)==[True,False]
