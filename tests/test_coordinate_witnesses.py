from copy import deepcopy
from functools import lru_cache

import pytest
import z3

from noema.grammar import parse
from noema.integration_audit import referenced_symbols
from scripts.check_coordinate_witnesses import ROOT, FULL, PARENT, THEOREM, BASIS, REVIEW, Logic, solve, equality_lemma, coherence_proof, source_bindings, theorem_artifacts


@lru_cache(maxsize=1)
def source():
    return parse((ROOT / FULL).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def proof():
    return coherence_proof(source())


def test_four_coordinates_follow_from_the_actual_conditions():
    result = proof()
    assert result['status'] == 'unsat'
    assert result['cut_equality']['status'] == 'unsat'
    assert result['cut_equality']['meanings_expanded'] == ['sca', 'sag', 'bc']
    assert not result['cut_equality']['rational_order_or_cut_validity_assumed']


def test_missing_each_projected_premise_admits_a_countermodel():
    result = proof()['counterexamples']
    assert len(result) == 7
    assert all(row['status'] == 'sat' for row in result.values())
    assert all(row['coordinates']['velocity'] != row['coordinates']['target'] for row in result.values())


def test_same_physical_coordinates_do_not_imply_function_identity():
    assert proof()['distinct_representations_with_equal_coordinates'] == 'sat'


def test_density_and_source_points_have_same_referents_in_each_frame():
    result = source_bindings(source(), parse((ROOT / PARENT).read_text(encoding='utf-8')))
    assert result['density_center_same_tuple']
    assert result['source_points_same_tuple_in_each_frame']
    assert not result['cross_frame_coordinate_equality_claimed']
    assert not result['event_or_representation_identity_inferred']


@pytest.mark.parametrize('change', ['one_inclusion', 'wrong_inclusion'])
def test_cut_equality_is_proved_from_definitions_not_assumed_by_name(change):
    doc = deepcopy(source()); ds = {d['name']: d for d in doc['declarations']}
    if change == 'one_inclusion':
        ds['sag']['body'] = deepcopy(ds['sag']['body']['arguments'][0])
    else:
        ds['bc']['body']['body']['kind'] = 'or'
    with pytest.raises(ValueError, match='not extensional equality'):
        equality_lemma(doc)


@pytest.mark.parametrize('change', ['some_time', 'no_reverse', 'different_time', 'different_observed_event'])
def test_altered_physical_connections_are_not_certified(change):
    doc = deepcopy(source()); ds = {d['name']: d for d in doc['declarations']}
    from scripts.check_coordinate_witnesses import flatten
    if change == 'some_time':
        ds['seox']['body']['arguments'][1]['kind'] = 'exists'
    elif change == 'no_reverse':
        ds['seob']['body']['arguments'][1]['arguments'][1] = deepcopy(flatten(ds['seob']['body'])[1])
    elif change == 'different_time':
        interior = flatten(ds['seoc']['body'])[5]
        interior['arguments'][1] = dict(kind='variable', name=ds['seoc']['parameters'][7]['name'])
    else:
        observed = flatten(ds['seoc']['body'])[6]
        observed['arguments'][2] = deepcopy(observed['arguments'][0])
    with pytest.raises(ValueError):
        coherence_proof(doc)


def test_derived_theorem_is_written_in_noema_with_no_new_vocabulary():
    outputs = theorem_artifacts()
    doc = parse(outputs[THEOREM])
    assert len(doc['statements']) == 1
    assert doc['statements'][0]['kind'] == 'assert'
    body = doc['statements'][0]['body']; quantified = 0
    while body['kind'] == 'forall':
        quantified += 1; body = body['body']
    assert quantified == 13 and body['kind'] == 'implies'
    assert {'seoc', 'seox', 'zpb'} <= referenced_symbols(body['arguments'][0])
    assert 'sca' in referenced_symbols(body['arguments'][1])
    parent = {d['name']: d for d in source()['declarations']}
    assert all(d == parent[d['name']] for d in doc['declarations'])
    import json
    basis = json.loads(outputs[BASIS])
    assert not basis['derived_claim']['attributed_to_source_author']
    assert 'statement_indices' not in basis['extraction_source']
    review = json.loads(outputs[REVIEW])
    assert not review['semantic_completion']


def test_unknown_syntax_is_rejected_instead_of_assigned_a_truth_value():
    with pytest.raises(ValueError, match='Unsupported proof syntax'):
        Logic({}, {}, {}, set()).expr(dict(kind='unhandled'), {})


def test_solver_timeout_cannot_be_reported_as_a_proof(monkeypatch):
    class Unknown:
        def set(self, **kwargs): pass
        def add(self, formula): pass
        def check(self): return z3.unknown
        def reason_unknown(self): return 'timeout'
    monkeypatch.setattr(z3, 'Solver', Unknown)
    with pytest.raises(ValueError, match='Solver unknown: timeout'):
        solve(z3.BoolVal(True))
