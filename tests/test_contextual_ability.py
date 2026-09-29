from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_contextual_ability import exhaustive_checks, contrast_checks, source_checks, attribution_check
from scripts.compose_contextual_ability import ROOT, generic_composed, source_composed


def test_ability_standards_against_exhaustive_finite_set_semantics():
    result = exhaustive_checks()
    assert result['models'] == 128
    assert result['all_match_independent_set_semantics']
    rows = contrast_checks()
    assert len(rows) == 11
    scoped = rows['exception_outside_selected_scope']
    assert scoped['assessed_ability'] and not scoped['guaranteed']
    failed = rows['failure_inside_selected_scope']
    assert failed['possible'] and failed['assessed_inability']
    unknown = rows['empty_scope_is_unknown_not_inability']
    assert not any(unknown[k] for k in ('assessed_ability', 'assessed_inability', 'decisive'))
    known = rows['successful_method_suffices_despite_other_missing_assessment']
    assert known['assessed_ability'] and known['decisive'] and not known['all_methods_assessable']
    incomplete = rows['missing_assessment_prevents_inability_claim']
    assert not incomplete['assessed_inability'] and not incomplete['decisive']


def test_source_does_not_turn_missing_assessments_into_incapacity_or_exit():
    rows = source_checks()
    assert len(rows) == 6
    assert not rows['exception_outside_scope']['old_guarantee']
    assert not rows['exception_outside_scope']['immaturity']
    assert rows['failure_inside_scope']['immaturity']
    assert rows['valid_exit']['exit']
    assert not rows['missing_assessment_not_exit']['exit']
    assert not rows['foreign_assessment_not_exit']['exit']
    assert not rows['missing_assessment_not_immaturity']['immaturity']


def test_source_can_attribute_new_reading_without_evaluating_it():
    result = attribution_check()
    assert len(result['references']) == 6
    assert result['references'][1] == ['second', 'bf']
    assert not result['underlying_contents_evaluated']


def test_ability_definitions_need_no_new_grammar_or_generic_primitives():
    for compose, counts in ((generic_composed, (0, 7)), (source_composed, (29, 26))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
