from functools import cache
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_worldlines import attribution_check, observation_checks, refusal_check
from scripts.compose_worldlines import ROOT, composed


def test_worldline_observations_reject_mixed_objects_units_and_conflicts():
    rows = observation_checks()
    assert len(rows) == 31
    assert all(row['actual'] == row['expected'] for row in rows.values())
    for name in ('wrong_object', 'wrong_context', 'wrong_time_unit',
                 'wrong_unit_dimension', 'contradictory_coordinates', 'contradictory_readings'):
        assert rows[name]['actual'] is False
    assert rows['alternate_length_scale']['actual'] is True
    # Uniqueness alone must not be mistaken for existence.
    assert rows['absent_second_coordinate_does_not_establish_existence']['actual'] is True
    assert rows['absent_second_reading_does_not_establish_existence']['actual'] is True


def test_clock_observation_premise_does_not_assume_the_integral_law():
    doc = parse(composed()[0])
    definitions = {d['name']: d for d in doc['declarations'] if d['kind'] == 'definition'}

    def calls(node):
        if isinstance(node, list):
            return set().union(*(calls(child) for child in node))
        if isinstance(node, dict):
            result = {node['symbol']} if node.get('kind') == 'call' else set()
            return result.union(*(calls(child) for child in node.values()))
        return set()

    @cache
    def reachable(name):
        direct = calls(definitions[name]['body']) if name in definitions else set()
        return direct.union(*(reachable(child) for child in direct))

    assert {'tf', 'tg', 'tj', 'tk', 'tl', 'se', 'sn'} <= reachable('sh')
    assert 'ne' not in reachable('sh')
    assert {'sh', 'ne'} <= reachable('qi')
    assert {'sh', 'qe'} <= reachable('qj')


def test_full_worldlines_refuse_finite_sampling_but_allow_unevaluated_attribution():
    assert 'rational number domain' in refusal_check()
    assert attribution_check() == {'premise': 'qi', 'conclusion': 'qj', 'contents_evaluated': False}


def test_worldline_basis_and_written_glyph_roundtrips():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (29, 96)
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')
    old = json.loads((ROOT / 'data/path-observations-basis-v1.json').read_text(encoding='utf-8'))
    previous = next(row for row in old['primitives'] if row['symbol'] == 'pe')
    current = next(row for row in basis['primitives'] if row['symbol'] == 'tl')
    assert current == dict(previous, symbol='tl', source_convention='path-observations-basis-v1:pe')
