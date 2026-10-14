import hashlib
import json

import pytest

from noema.grammar import parse, format_graph
from scripts.check_rod_setup import guarded
from scripts.check_declining_hindrances import ROOT, REPORT, PARENT, REFS, setup, generic_model, source_model, values
from scripts.compose_declining_hindrances import SOURCE
from scripts.compose_limits import call as k


def document(source=False):
    stem = 'declining-hindrances-core' if source else 'declining-hindrances'
    return setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source)


def test_declining_counts_can_hide_replacement_but_the_stronger_condition_cannot():
    doc = document()
    members = (('one', 'two', 'three'), ('one', 'two'), ('three',), ())
    assert values(doc, generic_model(doc, membership=members)) == [True, True, True, False, True]


def test_a_single_abrupt_drop_is_not_multistep_even_with_a_large_bound():
    doc = document()
    assert values(doc, generic_model(doc, (3, 3, 0, 0), bound=3)) == [True, True, False, False, True]


def test_step_size_is_an_explicit_context_parameter():
    doc = document()
    assert values(doc, generic_model(doc, (3, 1, 1, 0), bound=1)) == [True, True, False, False, True]
    assert values(doc, generic_model(doc, (3, 1, 1, 0), bound=2)) == [True, True, True, True, True]


@pytest.mark.parametrize('bound', [0, -1])
def test_nonpositive_bounds_do_not_certify_gradual_decline(bound):
    doc = document()
    assert values(doc, generic_model(doc, bound=bound)) == [True, True, False, False, True]


def test_lower_endpoint_does_not_hide_an_intermediate_rebound():
    doc = document()
    assert values(doc, generic_model(doc, (3, 1, 2, 0), bound=3)) == [True, False, False, False, True]


def test_assessment_before_the_selected_interval_is_not_required_inside_it():
    doc = document(); model = generic_model(doc)
    model['jnstart'] = lambda: 'second'
    model['jnassessed'] = lambda obstacle, point: point != 'first'
    assert values(doc, model) == [True, True, True, True, True]
    model['jnstart'] = lambda: 'first'
    assert values(doc, model) == [False, False, False, False, True]


def test_identical_endpoints_are_not_a_decline():
    doc = document(); model = generic_model(doc)
    model['jnend'] = lambda: 'first'
    assert values(doc, model) == [False, False, False, False, True]


def test_unknown_capability_assessment_is_not_the_absence_of_an_obstacle():
    doc = document(True); model = source_model(doc)
    def unknown(*args): raise ValueError('Capability assessment unknown')
    model['ap'] = unknown
    with pytest.raises(ValueError, match='Capability assessment unknown'):
        values(doc, model, True)


def test_quoting_the_decline_does_not_execute_unknown_models_or_abilities():
    doc = document(True); doc['statements'] = []
    body = k('hze7', *(REFS[n] for n, _ in SOURCE))
    doc = parse(format_graph(doc, 'compact') + 'q[e[r[' + body + ']][r[' + body + ']]].')
    assert values(doc, guarded(doc), True) == [True]


def test_saved_evidence_preserves_history_and_does_not_claim_complete_translation():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-declining-hindrances.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 12
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
