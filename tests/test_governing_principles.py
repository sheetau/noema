from itertools import product
import json
import pytest
from scripts.check_governing_principles import values, document, alignment
from scripts.compose_governing_principles import ROOT, PARENT, SOURCE, CORE, BASIS, build, basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('condition,first,second', list(product(range(4), repeat=3)))
def test_conditional_content_and_witness_are_separate(condition, first, second):
    one, two = condition & ~first == 0, condition & ~second == 0
    assert values(condition, first, second, indices=(0, 1, 2, 7)) == [one, two, bool(condition), one != two]


@pytest.mark.parametrize('old,new', list(product(range(4), repeat=2)))
def test_adoption_state_change_and_replacement(old, new):
    assert values(old=old, new=new, indices=(3, 4, 5, 6, 8)) == [bool(old & 2), False, old == 1, new == 2, old == 1 and new == 2]


@pytest.mark.parametrize('path', (CORE, SOURCE))
def test_existing_norm_relation_source_adapter_keeps_the_same_arguments(path):
    calls = []
    assert values(path=path, calls=calls, indices=(5, 6, 8)) == [True, True, True]
    norms = [row for row in calls if row[0] == 'norm']
    assert norms and all(row[1:4] == ('source', 'government', 'office') and row[5:7] == ((), True) for row in norms)
    assert all(code_is(row[4], 'jgfirst') or code_is(row[4], 'jgsecond') for row in norms)
    treatments = [row for row in calls if row[0] == 'treatment']
    assert treatments and all(row[2] == 'government' for row in treatments)


def test_fulfillment_requires_the_same_content_but_adoption_does_not_execute_it():
    calls = []
    assert values(old=3, variant='unknown_treatment', indices=(3,), calls=calls) == [True]
    assert not any(row[0] == 'treatment' for row in calls)
    with pytest.raises(ValueError, match='Unknown treatment'):
        values(old=3, variant='unknown_treatment', indices=(4,))
    assert values(old=3, first=3, indices=(3, 4)) == [True, True]
    assert values(old=0, first=3, indices=(3, 4)) == [False, False]


@pytest.mark.parametrize('variant', ('empty_people', 'duplicate_people', 'omitted_person'))
def test_inconsistent_subject_inventory_is_not_a_vacuous_general_principle(variant):
    assert values(condition=0, variant=variant, indices=(0, 1, 2)) == [False, False, False]


def test_false_antecedent_has_no_actual_instance_or_needed_treatment():
    assert values(condition=0, variant='unknown_treatment', indices=(0, 1, 2, 7)) == [True, True, False, False]


def test_changing_application_does_not_imply_changing_principle_adoption():
    assert values(variant='changing_application', old=3, new=0, indices=(0, 12, 5, 6, 8)) == [False, True, False, False, False]


def test_cross_context_truth_difference_cannot_witness_a_same_context_content_difference():
    assert values(variant='cross_context', indices=(0, 12, 7, 8)) == [True, False, False, False]


def test_different_description_is_not_evidence_of_different_meaning():
    assert values(indices=(9, 11)) == [False, True]
    # The two contents can both be false despite treating different people.
    # Failure to witness a difference is deliberately not an equivalence claim.
    assert values(first=1, second=2, indices=(0, 1, 7, 8)) == [False, False, False, False]


@pytest.mark.parametrize('variant', ('empty_probes', 'same_context', 'other_source', 'other_actor', 'other_office', 'wrong_bindings', 'negative_polarity'))
def test_missing_comparison_or_wrong_normative_identity_does_not_establish_replacement(variant):
    assert values(variant=variant, indices=(8,)) == [False]


@pytest.mark.parametrize('variant,index', (('unknown_norm', 3), ('unknown_condition', 0), ('unknown_treatment', 7), ('unknown_probes', 7)))
def test_unknown_required_input_is_not_treated_as_false(variant, index):
    with pytest.raises(ValueError, match='Unknown'):
        values(variant=variant, indices=(index,))


def test_extra_binding_is_rejected_instead_of_discarded():
    assert values(first=3, indices=(0, 10)) == [True, False]


def test_parent_assertions_primitives_and_builds_are_preserved():
    old, new = document(PARENT), document(SOURCE)
    assert new['statements'] == old['statements']
    assert new['declarations'][:len(old['declarations'])] == old['declarations']
    assert [d for d in new['declarations'] if d['kind'] == 'primitive'] == [d for d in old['declarations'] if d['kind'] == 'primitive']
    assert not alignment()['adds_new_text_coverage'] and not alignment()['semantic_completion']
    assert all((ROOT / p).read_text(encoding='utf-8') == text for p, text in build().items())
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    assert values(memoize=False) == values()
