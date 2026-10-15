from itertools import product
import pytest
from scripts.check_collective_protection import values, oracle, ASSIGNMENTS
from scripts.compose_collective_protection import ROOT, build


@pytest.mark.parametrize('corners', list(product((False,True),repeat=4)))
def test_successful_joint_plan_requires_the_same_protective_mechanism(corners):
    table = tuple(corners[2*int(p)+int(t)] for p,t,s in ASSIGNMENTS)
    assert values(table) == [False,True,oracle(table),oracle(table),oracle(table),oracle(table),True]


@pytest.mark.parametrize('variant', ('comparison_member_mismatch','comparison_activity_mismatch','comparison_threat_mismatch',
    'wrong_worlds','same_factors','duplicate_variable','missing_threat'))
def test_joint_success_is_insufficient_when_mechanism_or_content_does_not_match(variant):
    assert values(variant=variant) == [False,True,False,False,False,False,True]


@pytest.mark.parametrize('variant', ('missing_member_activity','wrong_planner','wrong_group','wrong_plan','wrong_anchor',
    'duplicate_member','missing_member','empty_members','empty_selected','outside_outcomes','unavailable'))
def test_protection_cannot_repair_invalid_joint_readiness(variant):
    assert values(variant=variant) == [False,False,False,False,False,False,True]


@pytest.mark.parametrize('negate',(False,True))
def test_multiple_solutions_and_no_solution_do_not_prove_a_guarantee(negate):
    table = tuple(row[2] != negate for row in ASSIGNMENTS)
    assert not oracle(table)
    assert values(table) == [False,True,False,False,False,False,True]


@pytest.mark.parametrize('variant',('unknown_execution','unknown_mechanism','unknown_record'))
def test_quoted_claim_preserves_unknown_mechanism_without_executing_it(variant):
    assert values(variant=variant,indices=(6,)) == [True]
    with pytest.raises(ValueError,match='Unknown'): values(variant=variant,indices=(4,))


def test_full_protection_is_the_same_without_evaluation_caches():
    assert values(indices=(4,),memoize=False) == [True]


@pytest.mark.parametrize('variant',('wrong_record','record_outside_variables','unintervened_mismatch','one_bad_record'))
def test_evaluated_outcome_records_must_fit_the_unintervened_mechanism(variant):
    assert values(variant=variant) == [False,True,True,True,False,False,True]


def test_preventive_protection_does_not_require_actual_threat_or_current_activity():
    assert values(variant='preventive') == [False,True,True,True,True,True,True]


def test_existential_claim_can_use_a_different_plan_without_repairing_the_fixed_one():
    assert values(variant='only_other_plan') == [False,False,False,True,False,True,True]


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8') == text for path,text in build().items())
