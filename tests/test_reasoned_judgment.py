import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_reasoned_judgment import judgment_checks, matter_checks, source_checks, attribution_check
from scripts.compose_reasoned_judgment import ROOT, generic_composed, source_composed


def test_judgment_requires_bound_reason_support_and_covers_each_relevant_matter():
    rows = judgment_checks()
    assert len(rows) == 8 and sum(rows.values()) == 1
    assert rows['baseline']
    matters = matter_checks()
    assert len(matters) == 6
    assert matters['different_methods_for_each_matter']
    assert matters['only_first_matter_relevant']
    assert not matters['second_method_unavailable']
    assert not matters['failures_in_scope']
    assert not matters['second_reason_unsupported']
    assert not matters['no_relevant_matters']


def test_latin_goal_is_not_an_alias_of_the_german_gloss():
    rows = source_checks()
    assert len(rows) == 11
    latin = rows['discernment_without_current_own_use']
    german = rows['own_use_without_support']
    assert latin['latin_goal'] and not latin['german_goal']
    assert german['german_goal'] and not german['latin_goal']
    assert latin['latin_directive_content'] and not latin['german_directive_content']
    assert german['german_directive_content'] and not german['latin_directive_content']
    assert all(r['descriptions_distinct'] and r['directive_not_assertion'] for r in rows.values())
    assert rows['courage_absent']['latin_goal'] and not rows['courage_absent']['latin_directive_content']


def test_independent_reading_preserves_attribution_and_marks_interpretive_limits():
    result = attribution_check()
    assert result['explanation_direction'] == ['latin', 'german']
    assert len(result['references']) == 6 and not result['contents_evaluated']
    review = json.loads((ROOT / 'data/latin-motto-review-v1.json').read_text(encoding='utf-8'))
    assert not review['runtime_lexical_lookup']
    assert not review['source_entails_all_formal_conditions']
    assert not review['full_latin_semantics_verified']


def test_reasoned_judgment_composition_and_glyph_roundtrips():
    for compose, counts in ((generic_composed, (0, 9)), (source_composed, (35, 35))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
