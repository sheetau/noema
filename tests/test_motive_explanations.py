from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_motive_explanations import episode_checks, motive_checks, explanation_checks, attribution_check
from scripts.compose_motive_explanations import ROOT, generic_composed, source_composed


def test_avoidance_motive_needs_the_same_action_factor_and_adopted_reason():
    result = episode_checks()
    assert len(result['cases']) == 16
    assert sum(row['episode'] for row in result['cases']) == 1
    assert result['different_action_rejected']


def test_effort_and_fear_patterns_can_belong_to_different_people():
    rows = motive_checks()
    assert len(rows) == 10
    assert rows['both_different_people'] == {'effort_pattern_present': True, 'fear_pattern_present': True}
    assert rows['effort_only'] == {'effort_pattern_present': True, 'fear_pattern_present': False}
    assert rows['fear_only'] == {'effort_pattern_present': False, 'fear_pattern_present': True}
    assert all(not any(row.values()) for name, row in rows.items() if name not in ('both_different_people', 'effort_only', 'fear_only'))


def test_cause_adoption_and_author_attribution_do_not_execute_their_contents():
    result = explanation_checks()
    assert len(result['cases']) == 9 and result['empty_list_rejected']
    assert [name for name, row in result['cases'].items() if row['adopted']] == ['both']
    assert all(not row['contents_evaluated'] for row in result['cases'].values())
    assert result['cases']['both']['references'] == [
        ['group', 'mq', 'group', 'ms', 'text'], ['group', 'mr', 'group', 'ms', 'text']]
    attributed = attribution_check()
    assert attributed['claims'][-1] == ['explanation', 'mx']
    assert not attributed['explanation_and_contents_evaluated']


def test_motive_explanation_basis_and_written_forms():
    for compose, counts in ((generic_composed, (1, 3)), (source_composed, (60, 81))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
