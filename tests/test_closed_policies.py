import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_closed_policies import REPORT, build_report
from scripts.compose_closed_policies import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_permission_does_not_evaluate_any_inner_typed_argument(result):
    rows = result['source']['guarded_permissions']
    assert len(rows) == 4
    assert {tuple(row['results']) for row in rows} == {(False, False), (True, False), (True, True)}
    assert result['source']['all_typed_arguments_remain_unevaluated_when_only_permission_is_queried']


def test_typed_target_identity_and_outer_norm_bindings_do_not_transfer(result):
    rows = result['source']['binding_contrasts']
    assert len(rows) == 10
    assert all(value == [False, False] for value in rows.values())
    assert rows['criterion_alias'] == [False, False]
    assert result['source']['empty_external_bindings_required']


def test_permission_opposition_and_actual_frequency_are_independent(result):
    rows = result['source']['actual_policy_cases']
    assert len(rows) == 8
    for row in rows:
        permitted, uncontested, actual, unused = row['results']
        assert permitted == row['allowed']
        assert uncontested == (row['allowed'] and not row['opposed'])
        assert actual == row['actual']
        assert unused == (row['allowed'] and not row['actual'])


def test_unknown_permission_and_unknown_actual_policy_are_not_false(result):
    assert result['source']['unknown_permission_and_actual_policy_refused']
    assert result['source']['generated_description_roundtrips']


def test_old_content_is_preserved_and_no_primitive_or_syntax_is_added():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    text, basis = source_composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (250, 467)
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    assert doc['schema_version'] == '0.14'
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text


def test_snapshot_preserves_partial_status_and_reproduces(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['new_primitives'] == result['new_source_assertions'] == 0
    assert result['parent_preserved'] and result['roundtrips']
    assert result['alignment']['semantic_completion'] is False
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
