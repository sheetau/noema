from itertools import product
import json
import pytest
from scripts.check_closed_claim_policies import values,source_values,fixture,document,alignment
from scripts.compose_closed_claim_policies import ROOT,PARENT,SOURCE,BASIS,build,basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('norms',list(product(range(4),repeat=3)))
def test_dynamic_and_compiled_policies_agree_for_all_two_claim_norm_profiles(norms):
    assert values(norms)==[norms==(3,3,3)]*2+[True]


@pytest.mark.parametrize('fulfilled',range(4))
def test_dynamic_and_compiled_policies_agree_for_partial_fulfillment(fulfilled):
    assert values(fulfilled=fulfilled)==[fulfilled==3]*2+[True]


@pytest.mark.parametrize('variant',('other_person','wrong_scope','empty_cases'))
def test_compilation_does_not_remove_identity_inventory_or_scope_checks(variant):
    assert values(variant=variant)==[False,False,True]


def test_literal_alias_identity_and_duplicate_criteria_are_preserved():
    assert values(names=('jvalias','jvtwo'))==[False,False,True]
    assert values(names=('jvone','jvone'))==[True,True,True]
    assert values(names=())==[False,False,True]


def test_compiled_policy_flows_through_norm_replacement_appraisal_and_collective_conditional():
    calls=[]
    assert source_values(calls=calls)==[True,False,True]
    norms=[r for r in calls if r[0]=='norm']
    assert any(code_is(r[1],'jpnew') and r[2]==() for r in norms)
    for claim in ('jvone','jvtwo'):
        assert any(code_is(r[1],claim) and r[2]==('government','person') for r in norms)
    content=[r for r in calls if r[0]=='content']
    assert content and all(r[2:4]==('government','person') for r in content)


@pytest.mark.parametrize('variant',('missing_requirement','missing_fulfillment'))
def test_concrete_claim_failure_is_not_hidden_by_a_favorable_appraisal(variant):
    assert source_values(variant=variant,indices=(0,3))==[False,False]


def test_reproducibility_original_author_assertions_and_compilation_trace():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements']==old['statements']
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    _,trace=fixture();assert trace.disquotations_removed==2 and trace.literal_fold_steps==4
    assert values(memoize=False)==values()
    assert alignment()['rank_zero_policy_bridge_demonstrated'] and not alignment()['semantic_completion']
