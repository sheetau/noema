import json
from pathlib import Path
import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_kant_roles import compose, composed_basis
from scripts.check_kant_roles import normative_checks, role_checks, build_report


def test_obligation_permission_actuality_and_conflicting_sources_remain_separate():
    cases = normative_checks()
    assert len(cases) == 12
    assert all(c['expected'] == c['actual'] for c in cases.values())
    assert cases['required_but_unfulfilled']['actual'] is True
    assert cases['no_prohibition_is_not_authorization']['actual'] is False
    assert cases['opposing_requirements_do_not_impose_unrelated_content']['actual'] is False


def test_same_person_can_reason_in_different_capacities_without_execution_or_permission_being_confused():
    cases = role_checks()
    assert len(cases) == 17
    assert all(c['expected'] == c['actual'] for c in cases.values())
    assert cases['public_classification_does_not_require_execution']['actual'] is True
    assert cases['permission_to_restrict_is_not_actual_restriction']['actual'] is False
    assert cases['one_context_does_not_establish_always']['actual'] is False


def test_general_normative_module_and_kant_composition_have_complete_basis_and_roundtrip():
    base = parse(Path('examples/v011/normative-roles.noema').read_text(encoding='utf-8'))
    assert audit_basis(base, json.loads(Path('data/normative-roles-basis-v1.json').read_text(encoding='utf-8')))['primitive_count'] == 2
    combined = parse(compose())
    assert combined == parse(Path('examples/v011/kant-public-private.noema').read_text(encoding='utf-8'))
    audit = audit_basis(combined, composed_basis())
    assert audit['primitive_count'] == 9 and audit['definition_count'] == 15
    for doc in (base, combined):
        for notation in ('full', 'compact'):
            text = format_graph(doc, notation)
            assert parse(text) == doc
            assert parse(decode(encode(text, 'v2'))) == doc


@pytest.mark.skipif(not Path('artifacts/written-units-v1/kant-1784.json').exists(), reason='Requires pinned source snapshot')
def test_partial_alignment_accounts_for_the_rest_of_the_large_source_paragraph():
    report = build_report()
    ranges = report['source_ranges']
    assert ranges[0]['start'] == 0
    assert all(left['end'] == right['start'] for left, right in zip(ranges, ranges[1:]))
    source = json.loads(Path('artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == report['source_unit'])
    assert ranges[-1]['end'] == len(unit['text'])
    assert sum(r['status'] == 'partial' for r in ranges) == 4
    assert any(r['status'] == 'pending' for r in ranges)
    assert report['verified_full_units'] == 0
