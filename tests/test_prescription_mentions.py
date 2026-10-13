from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_prescription_mentions import equivalence_checks, mention_checks
from scripts.compose_prescription_mentions import ROOT, PARENT, composed


def test_original_and_specialized_rule_evaluators_agree_in_all_fixture_states():
    rows = equivalence_checks()
    assert len(rows) == 32
    assert all(r['values'][::2] == r['values'][1::2] for r in rows)
    assert any(r['values'][-1] for r in rows)
    assert any(not r['values'][0] for r in rows)


def test_applicability_compliance_and_violation_can_be_mentioned_without_evaluating():
    result = mention_checks()
    assert result['all_primitives_except_mention_relation_guarded_against_execution']
    assert result['cases'] == {'he2': [True, False, False], 'hf2': [False, True, False], 'hg2': [False, False, True]}


def test_specialization_keeps_parent_and_does_not_attribute_example_norm_to_author():
    text, basis = composed()
    doc = parse(text)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:-3] == parent['declarations'] and doc['statements'] == parent['statements']
    assert basis['specialization']['new_assertions'] == 0
    assert basis['specialization']['example_rule_not_attributed_to_kant']
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (178, 246)
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
