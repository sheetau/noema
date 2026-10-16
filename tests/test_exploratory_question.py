import pytest
from scripts import check_exploratory_question as check


@pytest.fixture(scope='module')
def causal():return check.causal_checks()


@pytest.fixture(scope='module')
def presentation():return check.presentation_checks()


def test_question_candidates_require_possibility_and_content_in_the_same_case():
    assert check.modal_checks()['truth_combinations']==64


def test_chance_cause_agreement_and_occurrence_are_all_needed(causal):
    assert causal['condition_combinations']==16


def test_documents_extent_episode_and_context_cannot_be_mixed(causal):
    for variant in ('split_episodes','other_first_document','other_second_document','other_causal_extent','split_contexts'):
        assert causal['contrasts'][variant]==[False]


def test_possible_agreement_is_distinct_from_actual_agreement(causal):
    assert causal['contrasts']['baseline']==[True]
    assert causal['contrasts']['actual_only']==[False]
    assert causal['contrasts']['actual_possible']==[True]


def test_question_need_not_have_a_unique_or_maximal_answer(causal):
    assert causal['multiple_candidates_without_maximum']
    assert causal['contrasts']['empty_possible']==[False]


def test_presenting_a_question_does_not_evaluate_or_assert_its_answer(presentation):
    assert presentation['unknown_question_content_not_evaluated']
    assert presentation['contrasts']['baseline']==[True]


def test_only_as_a_trial_is_nonempty_and_scoped(presentation):
    rows=presentation['contrasts']
    assert rows['empty_roles']==rows['extra_role']==[False]
    for variant in ('other_person_role','other_document_role','other_context_role'):assert rows[variant]==[True]


def test_the_same_question_role_author_document_time_and_context_are_preserved(presentation):
    for variant in ('other_person','other_document','other_time','other_context','other_trial_role','other_question'):
        assert presentation['contrasts'][variant]==[False]
    assert presentation['question_description_preserved']


def test_unknown_answers_and_presentational_facts_are_not_invented(causal,presentation):
    assert causal['unknown_answers_refused'] and presentation['unknown_presentational_facts_refused']


def test_prior_manuscript_and_identifier_forms_are_unchanged():
    assert check.structure()['previous_statements_preserved']==22


def test_alignment_is_the_remaining_footnote_text():
    row=check.alignment()['segments'][0]
    assert row['source'].startswith('die jetzt nur zum Versuche') and row['source'].endswith('bringen könne.')
