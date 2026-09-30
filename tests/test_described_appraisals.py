from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_described_appraisals import (
    alignment, generic_checks, majority_checks, prospect_checks, source_checks, target_checks,
)
from scripts.compose_described_appraisals import ROOT, generic_composed, source_composed


def test_nonempty_judgments_can_be_false_in_actual_context():
    rows = generic_checks()
    assert len(rows) == 32
    assert any(r['judgment'] and not r['actual_truth'] for r in rows)
    assert any(not r['judgment'] and r['actual_truth'] for r in rows)
    assert all(not r['judgment'] for r in rows if not any(r['candidates']))
    assert all(not r['judgment'] for r in rows if r['candidates'] == [True, True]
               and not all(r['candidate_truths']))


def test_adversity_degree_and_prospects_share_the_same_arguments():
    rows = prospect_checks()
    assert len(rows) == 11
    assert [name for name, row in rows.items() if row['high_degree']] == ['baseline']
    assert not rows['split_outcomes']['adverse_possibility']
    assert rows['low_degree']['adverse_possibility']


def test_source_distinguishes_belief_truth_burden_and_recognized_description():
    rows = source_checks()
    assert len(rows) == 12
    assert rows['false_but_accepted']['combined'] and not rows['false_but_accepted']['actual_risk']
    assert rows['true_but_rejected']['actual_risk'] and not rows['true_but_rejected']['judgment']
    assert rows['not_burdensome']['judgment'] and not rows['not_burdensome']['combined']
    assert not rows['unrecognized']['judgment'] and not rows['empty_candidates']['judgment']
    assert all(r['descriptions_distinct'] and not r['alias_recognized'] for r in rows.values())
    assert all(r['alias_actual_risk'] == r['actual_risk'] for r in rows.values())


def test_large_share_requires_a_valid_population_and_more_than_a_majority():
    rows = majority_checks()
    assert len(rows) == 8
    assert [name for name, accepted in rows.items() if accepted] == ['all', 'stronger_context_accepts']


def test_autonomy_target_uses_existing_ability_without_asserting_an_actual_transition():
    rows = target_checks()
    assert len(rows) == 6
    assert [name for name, accepted in rows.items() if accepted] == ['self_directed']


def test_alignment_leaves_the_aside_and_causal_main_clause_unwritten():
    row = alignment()
    assert not row['full_semantic_equivalence']
    segments = row['segments']
    assert [s['status'] for s in segments] == ['partial_explicit_reading', 'pending',
                                             'partial_explicit_reading', 'pending']
    assert segments[1]['source'].startswith('(darunter')
    assert segments[-1]['source'].startswith(': dafür')
    source = parse(source_composed()[0])
    previous = parse((ROOT / 'examples/v014/kant-state-convenience.noema').read_text(encoding='utf-8'))
    assert source['statements'] == previous['statements']


def test_appraisal_basis_roundtrips_and_independent_glyphs():
    for compose, counts in ((generic_composed, (0, 3)), (source_composed, (106, 138))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            formatted = format_graph(doc, notation)
            assert parse(formatted) == parse(decode(encode(formatted, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
