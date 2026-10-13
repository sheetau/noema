import json

import pytest

from noema.grammar import parse
from scripts.check_prescribed_teaching import REPORT, build_report
from scripts.compose_prescribed_teaching import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_requirements_compliance_and_public_permission_are_separate(result):
    rows = result['teaching']['cases']
    assert len(rows) == 64
    for row in rows:
        required, allowed, forbidden, delivered, first, second = row['states']
        actual = delivered and first and second
        assert row['results'] == [required, required and not actual, required and allowed and not forbidden, actual]


def test_institution_and_role_cannot_be_swapped(result):
    rows = result['teaching']['contrasts']
    for name in ('service_person','service_principal','service_role','service_context',
                 'adoption_principal','adoption_standard','adoption_context','unadopted',
                 'no_entrusted_office','wrong_activity_role'):
        assert rows[name] == [True,True,True,False]


def test_message_and_audience_identity_are_preserved(result):
    rows = result['teaching']['contrasts']
    for name in ('delivery_activity','delivery_recipient','delivery_subject','delivery_context',
                 'delivery_description','criterion_subject','criterion_description',
                 'missing_student','missing_member','empty_audiences'):
        assert rows[name] == [True,True,True,False]
    for name in ('only_congregation','overlapping_audiences'):
        assert rows[name] == [True,False,True,True]


def test_a_requirement_for_one_description_is_not_transferred_to_another(result):
    rows = result['teaching']['contrasts']
    for field in ('issuer','person','role','activity','context','description'):
        assert rows['norm_'+field] == [False,False,False,True]
    assert result['teaching']['norms_do_not_execute_target']
    assert result['teaching']['unassessed_criterion_refused']


def test_official_teaching_does_not_require_personal_endorsement_or_truth(result):
    rows = result['teaching']['independent_truth_and_endorsement']
    assert len(rows) == 4
    assert {(row['truth'],row['endorsed']) for row in rows} == {(False,False),(False,True),(True,False),(True,True)}
    assert all(row['results'] == [True,False,True,True] for row in rows)
    assert result['teaching']['unassessed_truth_and_endorsement_not_executed']


def test_public_permission_is_for_the_separate_activity(result):
    for name in ('private_audience','speech_is_official','same_activity'):
        assert result['teaching']['contrasts'][name] == [True,False,False,True]


def test_empty_and_repeated_criteria_have_explicit_behavior(result):
    rows = result['teaching']['criterion_lists']
    assert [row['criteria'] for row in rows] == [[],['zt'],['zt','zt'],['zt','zu','zt']]
    assert [row['results'][-1] for row in rows] == [True,True,True,False]
    assert result['teaching']['adoption_fixture_checks_referents_and_list_length_only']
    assert not result['teaching']['general_criterion_function_identity_proved']


def test_source_remains_a_partial_interpretation(result):
    assert len(result['alignment']['segments']) == 2
    assert all(row['unit'] == 'kant-1784:u0012' and row['status'] == 'partial' for row in result['alignment']['segments'])
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784':0,'einstein-1905':0}


def test_parent_and_language_are_preserved(result):
    text,_ = source_composed(); doc = parse(text)
    parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['declarations']) == len(parent['declarations'])+6
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['teaching']['standalone_agrees']


def test_report_and_notation_are_reproducible(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
