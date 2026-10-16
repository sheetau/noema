import pytest
from scripts import check_class_restricted_roles as check


@pytest.fixture(scope='module')
def source():return check.source_checks()


def test_category_restriction_over_all_adoption_and_qualification_patterns():
    result=check.generic_checks()
    assert result['combinations']==64
    assert len(result['accepted_class_cases_rejected_by_singleton'])==5


def test_two_or_three_trials_for_the_same_question_are_accepted(source):
    for variant in ('two_trials','three_trials'):
        assert source['contrasts'][variant]=={'old':[False],'new':[True]}


def test_unrelated_roles_or_trials_for_a_different_question_are_rejected(source):
    for variant in ('second_not_trial','second_other_question','extra_role'):
        assert source['contrasts'][variant]['new']==[False]


def test_the_designated_role_is_still_an_adopted_witness(source):
    for variant in ('witness_missing','empty_roles'):
        assert source['contrasts'][variant]['new']==[False]


def test_only_applies_to_the_same_author_document_and_context(source):
    for variant in ('other_person_role','other_document_role','other_context_role'):
        assert source['contrasts'][variant]['new']==[True]


def test_unknown_adopted_qualifications_are_not_guessed(source):
    assert source['unknown_adopted_qualification_refused']


def test_unused_unknown_qualification_has_an_explicit_eager_evaluation_limit(source):
    assert source['unused_unknown_qualification_diagnostic_skipped']
    assert source['unused_unknown_qualification_eager_refused']


def test_question_is_preserved_as_a_description_without_evaluating_answers(source):
    assert source['question_description_preserved'] and source['question_content_not_evaluated']


def test_revision_changes_one_body_and_keeps_the_prior_singleton_operation():
    result=check.structure()
    assert result['changed_definition']=='hzle' and result['new_primitives']==0
    assert result['previous_statements_preserved']==23


def test_signature_meaning_is_unchanged_despite_new_basis_provenance():
    result=check.structure()['signature_comparison']
    assert result['before']['statements']==result['after']['statements']
    assert result['before']['dependencies']==result['after']['dependencies']


def test_source_range_is_an_already_covered_phrase():
    assert check.alignment()['segments'][0]['source']=='die jetzt nur zum Versuche da stehen mag, '
