from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_easy_roles import easy_checks, role_checks, target_interface_checks, explanation_checks, attribution_checks
from scripts.compose_easy_roles import ROOT, generic_composed, source_composed


def test_easy_attainment_uses_the_same_successful_low_burden_method():
    result = easy_checks()
    assert len(result['cases']) == 256
    assert result['method_binding'] == {'different_methods': False, 'same_method': True}
    assert all(not row['easy'] for row in result['cases'] if not row['selected'])


def test_assumed_role_ease_actuality_and_targets_are_distinct():
    rows = role_checks()
    assert len(rows) == 16
    assert rows['baseline'] == {'easy_for_pair': True, 'currently_assumed': False, 'cohort_condition': True}
    assert rows['already_done_without_method'] == {'easy_for_pair': False, 'currently_assumed': True, 'cohort_condition': False}
    assert [name for name, row in rows.items() if row['cohort_condition']] == ['baseline']
    targets = target_interface_checks()
    assert targets['prior_property_is_stubbed'] and not targets['full_kg_semantics_reverified']
    assert sum(row['target'] for row in targets['cases']) == 1


def test_both_results_keep_both_causes_and_author_order_without_content_execution():
    rows = explanation_checks()
    assert len(rows) == 5
    assert [name for name, row in rows.items() if row['adopted']] == ['all']
    assert rows['all']['references'] == [['mq', 'ms'], ['mr', 'ms'], ['mq', 'ok'], ['mr', 'ok']]
    assert attribution_checks() == {'baseline': True, 'missing_order': False, 'wrong_author': False}


def test_easy_role_basis_and_written_forms():
    for compose, counts in ((generic_composed, (0, 8)), (source_composed, (65, 88))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
