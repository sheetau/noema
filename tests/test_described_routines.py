from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_described_routines import instance_checks, use_checks, binding_checks, unbounded_refusal, alignment
from scripts.compose_described_routines import ROOT, PARENT, generic_composed, source_composed


def test_instances_preserve_the_pattern_argument_and_application_syntax_without_execution():
    row = instance_checks()
    assert row['result'] == [True, False, False, False, False]
    assert row['all_interpretations_except_structural_matcher_unexecuted']


def test_having_a_formula_using_it_and_examining_it_are_different():
    rows = use_checks()
    assert len(rows) == 64
    assert any(row['result'] == [True, False, False] and row['reviewed'] for row in rows)
    assert any(row['result'] == [True, True, False] and not row['natural'] for row in rows)
    assert any(row['result'] == [True, True, True] for row in rows)
    assert all(not any(row['result']) for row in rows if not (row['stored'] and row['used'] and row['applied']))


def test_examination_is_about_the_same_person_form_and_use():
    rows = binding_checks()
    assert len(rows) == 27
    assert all(result == [True, True, True] for name, result in rows.items()
               if name.startswith(('judgment_', 'matter_', 'review_')))
    assert all(result == [True, True, False] for name, result in rows.items()
               if name.startswith(('natural_', 'facultyuse_')))


def test_formula_category_does_not_replace_all_descriptions_by_a_known_finite_list():
    assert unbounded_refusal()['refused']


def test_partial_source_reading_does_not_claim_the_whole_metaphor():
    row = alignment()
    assert [part['source'] for part in row['segments']] == ['Formeln', 'diese mechanischen Werkzeuge']
    assert all(not part['full_semantic_equivalence'] for part in row['segments'])
    assert 'fetters and enduring immaturity' in row['remaining']


def test_prior_source_content_and_all_basis_entries_are_preserved():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (1, 4)), (source_composed, (188, 272))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
