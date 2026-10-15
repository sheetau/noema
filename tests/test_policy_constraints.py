from itertools import product
import json
import pytest
from noema.extraction import _references
from scripts.check_policy_constraints import (
    values, source_values, realization_values, wrapper_values, attribution,
    review_report, document,
)
from scripts.compose_policy_constraints import ROOT,PARENT,SOURCE,BASIS,REVIEW,build,basis,review


@pytest.mark.parametrize('policy,constraint',list(product(range(8),repeat=2)))
def test_inclusion_and_independent_witness(policy,constraint):
    assert values(policy,constraint)==[not bool(policy&~constraint),bool(policy)]


def test_empty_comparison_is_rejected_and_cache_does_not_change_truth():
    assert values(empty=True)==[False,False]
    assert values(memoize=False)==values()==[True,True]


@pytest.mark.parametrize('policy,permission',[(0,0),(0,7),(1,1),(1,5),(1,4),(5,5),(7,7),(7,5)])
def test_concrete_permission_inclusion_without_equivalence(policy,permission):
    assert source_values(policy,permission)==[
        not bool(policy&~permission),bool(policy&4),bool(permission&4),bool(policy)]


@pytest.mark.parametrize('variant',('other_beneficiary','other_source','other_office','empty_people','empty_cases','missing_requirement'))
def test_same_beneficiary_and_norm_identity_are_required(variant):
    assert source_values(variant=variant)==[False,False,False,True]


def test_equivalent_policy_text_does_not_transfer_norm_metadata():
    assert source_values(policy_name='jzalias')==[False,False,False,True]


def test_unknown_permission_is_not_guessed():
    with pytest.raises(ValueError,match='Unknown permission'):
        source_values(variant='unknown_permission')


def test_policy_can_have_extra_conditions_and_need_not_hold_now():
    assert source_values()==[True,False,True,True]


def test_impossible_policy_is_vacuously_inclusive_but_not_realizable():
    assert source_values(policy=0)==[True,False,True,False]
    assert realization_values(policy=0)==[True,False]
    assert realization_values()==[True,True]


def test_realizability_does_not_replace_the_required_content():
    assert realization_values(variant='missing_requirement')==[False,True]


def test_empty_metadata_is_rejected_even_for_impossible_policy():
    assert source_values(policy=0,variant='empty_people')[0] is False
    assert source_values(policy=0,variant='empty_cases')[0] is False


def test_parent_interface_preserves_remaining_and_same_policy():
    # This is an interface test with a recording parent, not a full causal rerun.
    assert wrapper_values()==[True]
    assert wrapper_values(remaining=False)==[False]
    assert wrapper_values(variant='missing_requirement')==[False]


@pytest.mark.parametrize('variant,expected',[('baseline',True),('old',False),('author',False)])
def test_attribution_quotes_new_template_without_executing_it(variant,expected):
    assert attribution(variant)==[expected]


def test_manuscript_preserves_history_and_connects_criterion():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert len(new['statements'])==22
    assert _references(new['statements'][-1])=={'iayattribution'}
    packet=review_report();rows={r['id']:r for r in packet['obligations']}
    assert len(rows)==14
    for name in ('human_patient','dignified_treatment','more_than_machine','tender_care'):
        assert rows[name]['unconnected_candidate_roots']==[]
    assert packet['templates'][0]['symbol']=='iayschema'
    assert len(packet['templates'][0]['parameters'])==8
    assert not packet['semantic_completion'] and not packet['counts_as_translated_coverage']


def test_reproducible_text_and_review():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==review(files)
