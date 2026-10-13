import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_retained_attitudes import generic_checks, source_checks, connection_checks, alignment
from scripts.compose_retained_attitudes import ROOT, PARENT, generic_composed, source_composed


def test_acquisition_requires_change_affected_subject_and_unbroken_retention():
    rows = generic_checks()
    assert len(rows) == 64
    assert sum(row['result'] for row in rows) == 1
    accepted = next(row for row in rows if row['result'])
    assert not accepted['prior'] and all(accepted[k] for k in ('later', 'middle', 'current', 'change', 'affected'))
    assert json.loads(json.dumps(rows)) == rows


def test_current_preference_is_not_acquisition_and_difficulty_is_not_success():
    rows = source_checks()
    assert len(rows) == 17
    assert rows['baseline'] == [True, True]
    assert rows['already_liked'] == rows['lost_middle'] == rows['no_change'] == [False, True]
    assert rows['different_person'] == rows['different_process'] == [False, True]
    assert rows['different_attitude_target'] == [False, True]
    assert rows['future_liked'] == [True, True]
    assert rows['already_capable'] == [False, False]
    assert rows['low_burden'] == rows['different_burden_goal'] == [True, False]


def test_partial_paragraph_connection_keeps_three_independent_conditions():
    rows = connection_checks()
    assert len(rows) == 8
    assert sum(row['result'][0] for row in rows) == 1


def test_source_ranges_keep_unrepresented_qualifiers_explicit():
    result = alignment()
    assert len(result['segments']) == 2
    assert all(row['unit'] == 'kant-1784:u0010' and not row['full_semantic_equivalence'] for row in result['segments'])
    assert 'almost become nature' in result['unrepresented_meanings_inside_ranges']
    assert result['generalization_and_inference_not_claimed']


def test_reused_primitives_prior_content_and_alphabet_roundtrips():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse(source_composed()[0])
    assert child['statements'] == parent['statements']
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert [d for d in child['declarations'] if d['kind'] == 'primitive'] == [d for d in parent['declarations'] if d['kind'] == 'primitive']
    for builder, counts in ((generic_composed, (0, 4)), (source_composed, (146, 212))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
