from copy import deepcopy
from functools import lru_cache

import pytest

from noema.extraction import extract_document
from noema.grammar import parse
from scripts.compose_density_time import ROOT, FULL, CORE, PARENT, INDEX, review_packet
from scripts.check_density_time import structural_checks, clause_checks, zero_total_counterexample


@lru_cache(maxsize=1)
def documents():
    return tuple(parse((ROOT / name).read_text(encoding='utf-8')) for name in (FULL, PARENT, CORE))


@lru_cache(maxsize=1)
def probes():
    return clause_checks((ROOT / CORE).read_text(encoding='utf-8'))


def test_zero_charge_does_not_make_different_times_the_same():
    result = zero_total_counterexample((ROOT / CORE).read_text(encoding='utf-8'))
    assert result['old_adapter_accepts'] == {'baseline': True, 'clock_frame': True}
    assert result['amount'] == 0
    assert result['ball_time'] != result['charge_slice_time']
    assert not result['corrected_coordinate_clause']
    assert result['spatial_contracts_are_explicit_oracles']
    assert not result['full_spatial_or_density_model_certified']


def test_matching_signed_and_fractional_times_are_compared_by_value():
    rows = probes()['cases']
    assert rows['matching'] and rows['negative_matching']
    assert not rows['fractional_mismatch']


def test_mismatched_point_slice_and_time_unit_are_rejected():
    rows = probes()['cases']
    assert not any(rows[n] for n in ('wrong_slice', 'wrong_point_time', 'wrong_time_unit'))


def test_other_events_and_material_are_not_forced_to_share_time():
    rows = probes()['cases']
    assert all(rows[n] for n in ('unrelated_record', 'other_matter', 'other_frame', 'other_event', 'other_context'))


def test_one_matching_record_cannot_hide_a_second_conflicting_record():
    rows = probes()['cases']
    assert rows['matching']
    assert not rows['wrong_point_time']
    doc = documents()[0]
    guard = next(d for d in doc['declarations'] if d['name'] == 'seox')
    assert guard['body']['arguments'][1]['kind'] == 'forall'
    assert probes()['actual_universal_clause_instantiated']


def test_unknown_time_and_full_point_domain_are_not_replaced_with_false_or_samples():
    result = probes()
    assert result['unknown_clock_refused']
    assert 'rational number domain' in result['full_point_domain_refusal']
    assert not result['universal_agreement_proven']


def test_correction_is_in_the_source_quote_and_uses_no_new_primitive():
    doc, parent, _ = documents()
    result = structural_checks(doc, parent)
    assert all(result['dependency_paths'].values())
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert all(d['kind'] == 'definition' for d in doc['declarations'][len(parent['declarations']):])
    assert len(doc['statements']) == len(parent['statements']) == 175
    assert doc['statements'][:INDEX] == parent['statements'][:INDEX]


def test_standalone_document_preserves_the_actual_revised_statement():
    doc, _, core = documents()
    assert core == extract_document(doc, statement_indices=[INDEX]).document
    assert len(core['statements']) == 1


@pytest.mark.parametrize('change', ['one_point', 'clock_unit', 'record_event', 'missing_axis',
    'density_without_time', 'different_density_matter', 'different_charge_clock', 'old_source_quote'])
def test_lost_binding_or_scope_is_detected(change):
    original, parent, _ = documents()
    doc = deepcopy(original)
    ds = {d['name']: d for d in doc['declarations']}
    guard = ds['seox']['body']
    forall = guard['arguments'][1]
    if change == 'one_point':
        forall['kind'] = 'exists'
    elif change == 'clock_unit':
        clock = guard['arguments'][0]['arguments'][0]
        clock['arguments'][2] = deepcopy(clock['arguments'][0])
    elif change == 'record_event':
        record = forall['body']['arguments'][0]['arguments'][1]
        record['arguments'][2] = deepcopy(record['arguments'][0])
    elif change == 'missing_axis':
        premise = forall['body']['arguments'][0]
        premise['arguments'][0] = deepcopy(premise['arguments'][0]['arguments'][0])
    elif change == 'density_without_time':
        body = ds['seoy']['body']
        body['body'] = deepcopy(body['body']['arguments'][0])
    elif change == 'different_density_matter':
        bound = ds['seoy']['body']['body']['arguments'][1]
        bound['arguments'][0] = deepcopy(bound['arguments'][1])
    elif change == 'different_charge_clock':
        linked = ds['seoz']['body']['body']['arguments'][1]['content']['arguments'][1]
        linked['arguments'][-1] = deepcopy(linked['arguments'][0])
    else:
        doc['statements'][INDEX]['body']['arguments'][-1]['body']['symbol'] = 'seov'
    with pytest.raises(ValueError):
        structural_checks(doc, parent)


def test_review_records_correction_without_certifying_translation():
    packet = review_packet()
    assert packet['revised_content'] == 'seoz'
    checks = {row['id']: row for row in packet['checks']}
    assert checks['density_charge_time_connection']['status'] == 'structurally_connected_with_counterexample_check'
    assert checks['interpretation_conservativity']['status'] == 'open'
    assert checks['whole_unit_decision']['status'] == 'open'
    assert not packet['semantic_completion']
