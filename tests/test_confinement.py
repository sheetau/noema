from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_confinement import (
    alignment, attribution_checks, boundary_checks, deletion_checks, depiction_checks,
    paragraph_review, reachability_checks, source_checks,
)
from scripts.compose_confinement import ROOT, generic_composed, source_composed


def test_finite_reachability_matches_independent_graph_search():
    result = reachability_checks()
    assert result['graphs'] == 64 and result['endpoint_queries'] == 576
    assert 0 < result['reachable_queries'] < 576


def test_confinement_depends_on_lost_exit_paths_not_just_inside_location():
    rows = deletion_checks()
    assert len(rows) == 27
    assert any(row['confined'] for row in rows)
    assert any(row['escape_with_restriction'] for row in rows)
    assert all(row['confined'] == (row['escape_without_restriction'] and not row['escape_with_restriction']) for row in rows)


def test_passage_scope_direction_and_boundary_cases_remain_distinct():
    rows = boundary_checks()
    assert len(rows) == 14
    assert [name for name, row in rows.items() if row['confined']] == ['baseline', 'permuted', 'duplicate']
    assert rows['already_outside']['escape_without_restriction']
    assert rows['boundary_start']['escape_without_restriction']
    assert rows['bypass']['escape_without_restriction']
    assert not rows['preexisting_inability']['escape_without_restriction']


def test_source_confinement_needs_same_event_restriction_person_carrier_and_scope():
    rows = source_checks()
    assert len(rows) == 16
    assert [name for name, accepted in rows.items() if accepted] == ['baseline']


def test_depiction_keeps_both_husbandry_and_confinement_without_literal_assertion():
    assert depiction_checks() == {'baseline': True, 'unowned': False, 'bypass': False}
    rows = attribution_checks()
    assert len(rows) == 4
    assert [name for name, row in rows.items() if row['framed']] == ['baseline']
    assert all(not row['contents_evaluated'] for row in rows.values())


def test_partial_confinement_does_not_discharge_walking_frame_meaning():
    review = paragraph_review()
    assert not review['semantic_completion'] and review['not_a_complete_obligation_inventory']
    assert all(row['status'] == 'open' for row in review['current_obligations'])
    assert next(row for row in review['current_obligations'] if row['id'] == 'walking_frame')['progress_ja']
    assert not alignment()['full_semantic_equivalence']
    assert parse(source_composed()[0])['statements'] == parse(
        (ROOT / 'examples/v014/kant-husbandry-depiction.noema').read_text(encoding='utf-8'))['statements']


def test_confinement_has_no_new_runtime_operators_and_roundtrips_in_its_alphabet():
    for compose, counts in ((generic_composed, (0, 5)), (source_composed, (163, 211))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
