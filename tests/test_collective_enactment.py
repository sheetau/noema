from copy import deepcopy
from itertools import product
import json

import pytest

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from scripts.check_collective_enactment import (values,document,model,DOMAIN,SCENES,
    APPROVAL_CONTRASTS,CHANGE_CONTRASTS,ACTUAL_CONTRASTS)
from scripts.compose_collective_enactment import ROOT,PARENT,LIBRARY,BASIS,build,basis


@pytest.mark.parametrize('flags',list(product((False,True),repeat=5)))
def test_approval_control_and_recognized_change_are_distinct(flags):
    options=dict(zip(('mandated','approved','controlled','recognized','changed'),flags))
    assert values(**options)==[all(flags[:2]),all(flags),all(flags),all(flags),True]


@pytest.mark.parametrize('flags',list(product((False,True),repeat=3)))
def test_actual_input_execution_and_realization_are_independent(flags):
    assert values(**dict(zip(('cast','performed','realized'),flags)))==[True,True,True,all(flags),True]


@pytest.mark.parametrize('variant',APPROVAL_CONTRASTS)
def test_decision_applies_to_the_same_complete_office_and_exercise(variant):
    assert values(variant=variant)==[False]*4+[True]


@pytest.mark.parametrize('variant',CHANGE_CONTRASTS)
def test_an_approval_is_not_a_change_for_another_actor_code_norm_or_endpoint(variant):
    assert values(variant=variant)==[True,False,False,False,True]


@pytest.mark.parametrize('variant',ACTUAL_CONTRASTS+('missing_ballot',))
def test_actual_enactment_requires_matching_records_even_for_a_negative_vote(variant):
    assert values(variant=variant)==[True,True,True,False,True]


@pytest.mark.parametrize('variant',('same_state','alternative'))
def test_power_can_have_a_witness_other_than_the_given_failed_endpoint(variant):
    assert values(variant=variant)==[True,False,True,False,True]


@pytest.mark.parametrize('status,polarity',list(product((False,True),repeat=2)))
def test_repealing_a_norm_does_not_negate_its_content(status,polarity):
    assert values(status=status,polarity=polarity)==[True]*5


@pytest.mark.parametrize('variant',('unknown_mandate','unknown_control','unknown_recognition','unknown_norm',
                                  'unknown_cast','unknown_performed','unknown_realized'))
def test_quotation_can_preserve_unknowns_but_execution_cannot_guess_them(variant):
    assert values(variant=variant,indices=(4,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(3,))


@pytest.mark.parametrize('variant',('unknown_cast','unknown_performed','unknown_realized'))
def test_institutional_power_does_not_need_actual_enactment_records(variant):
    assert values(variant=variant,indices=(2,))==[True]


def test_policy_and_exercise_can_be_false_or_unknown_without_blocking_the_norm_change():
    # Default model raises if either content is executed. Also make them
    # explicitly false: enacting a demand does not make its content true.
    assert values()==[True]*5
    doc=deepcopy(document());primitives=model()
    primitives.update(jceexercisetruth=lambda *a:False,jcetargettruth=lambda *a:False)
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    result=evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives={n:primitives[n] for n in names},
        max_steps=2_000_000,memoize_definitions=True,memoize_expressions=True)
    assert [row['value'] for row in result]==[True]*5


def test_human_holder_and_collective_actor_are_distinct():
    primitives=model()
    assert primitives['jcepersons']('organization') is False
    assert all(primitives['jcepersons'](p) for p in ('p1','p2','p3'))
    assert primitives['jceorganization']()=='organization'
    assert primitives['jceexercisebindings']().items[0]=='organization'


@pytest.mark.parametrize('original,alias,expected',[
    ('jceexercise','jcealias',[False,False,False,False,True]),
    ('jcetarget','jceother',[True,False,False,False,True])])
def test_equal_truth_aliases_cannot_borrow_the_original_institutional_records(original,alias,expected):
    doc=deepcopy(document())
    def replace(node):
        if isinstance(node,dict):
            if node.get('kind')=='function_ref' and node.get('symbol')==original:node['symbol']=alias
            for value in node.values():replace(value)
        elif isinstance(node,list):
            for value in node:replace(value)
    replace(doc['statements'])
    doc=parse(format_graph(doc,'compact'));primitives=model()
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    result=evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives={n:primitives[n] for n in names},
        max_steps=2_000_000,memoize_definitions=True,memoize_expressions=True)
    assert [row['value'] for row in result]==expected


def test_parent_definitions_are_reused_and_no_primitive_is_added_to_the_library():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));new=document(LIBRARY)
    old_by_name={d['name']:d for d in old['declarations']}
    for d in new['declarations']:
        if d['name'] in old_by_name:assert d==old_by_name[d['name']]
        else:assert d['kind']=='definition'
    assert not new['statements']


def test_documents_and_basis_reproduce_and_cache_is_not_required():
    assert values(memoize=False)==values()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for text in build().values():
        doc=parse(text)
        assert parse(format_graph(doc,'full'))==doc
