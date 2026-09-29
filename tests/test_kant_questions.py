from pathlib import Path

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.compose_kant_v012 import composed
from scripts.check_written_v012 import build_report, question_checks


def test_composition_keeps_motto_and_connects_questions_to_earlier_definitions():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert audit['primitive_count'] == 18
    assert audit['definition_count'] == 11
    assert [s['kind'] for s in doc['statements']] == ['assert', 'ask', 'ask']
    assert 'ag' in audit['definition_dependencies']['statement_primitive_dependencies'][1]
    assert 'an' not in audit['definition_dependencies']['primitive_symbols']
    assert not audit['semantic_equivalence_to_source_proven']


def test_question_countermodels():
    result = question_checks()
    assert len(result) == 4
    assert result['harmful_neutral_helpful_conflicting']['expected_answers'] == [[['harmful'], ['both']], [['helpful']]]


def test_source_ranges_cover_whole_unit_without_claiming_completion():
    if not Path('artifacts/written-units-v1/kant-1784.json').exists():
        pytest.skip('Source artifact is prepared separately')
    report = build_report()
    assert report['verified_full_units'] == 0
    ranges = report['source_ranges']
    assert ranges[0]['start'] == 0
    assert all(a['end'] == b['start'] for a, b in zip(ranges, ranges[1:]))
    assert sum(r['status'] == 'partial' for r in ranges) == 2
    assert any(r['status'] == 'pending' for r in ranges)
