from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_reformulations import generic_checks, usage_checks, binding_checks, attribution_checks, alignment
from scripts.compose_reformulations import ROOT, PARENT, generic_composed, source_composed


def test_reformulation_is_directed_and_independent_of_both_truth_values():
    rows = generic_checks()
    assert len(rows) == 8
    assert sum(row['result'][2] for row in rows) == 4
    assert all(not row['result'][3] and not row['result'][4] for row in rows)
    assert any(row['first'] and row['second'] and row['adopted'] for row in rows)
    assert any(not row['first'] and not row['second'] and row['adopted'] for row in rows)


def test_misuse_requires_use_and_its_own_assessment_not_absence_of_rationality():
    rows = usage_checks()
    assert len(rows) == 16
    assert all(row['result'] == [False, False] for row in rows if not row['used'])
    assert any(row['natural'] and row['used'] and row['result'] == [False, False] for row in rows)
    assert any(row['result'] == [True, True] for row in rows)


def test_natural_faculty_owner_user_event_and_assessment_are_not_cross_bound():
    rows = binding_checks()
    assert len(rows) == 8
    assert rows['baseline'] == [True, True]
    assert all(row == [False, False] for name, row in rows.items() if name != 'baseline')


def test_source_statement_mentions_the_correction_without_executing_use_contents():
    result = attribution_checks()
    assert result['use_and_appraisal_primitives_never_executed']
    assert len(result['cases']) == 7
    assert [name for name, row in result['cases'].items() if row[0]] == ['baseline']


def test_source_scope_includes_qualification_without_claiming_its_grounding():
    row = alignment()
    assert 'oder vielmehr' in row['source'] and row['source'].endswith('Naturgaben')
    assert not row['full_semantic_equivalence']
    assert 'rationality and misuse criteria' in row['remaining']


def test_prior_statements_and_basis_are_preserved_with_one_attribution_added():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse(source_composed()[0])
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert child['statements'][:-1] == parent['statements']
    for builder, counts in ((generic_composed, (1, 1)), (source_composed, (183, 250))):
        text, basis = builder()
        report = audit_basis(parse(text), basis)
        assert (report['primitive_count'], report['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
