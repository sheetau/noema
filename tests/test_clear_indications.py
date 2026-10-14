import hashlib
import json
from fractions import Fraction

import pytest

from noema.finite_semantics import Content, SequenceValue
from noema.grammar import parse, format_graph
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_rod_setup import guarded
from scripts.check_clear_indications import ROOT, REPORT, PARENT, SCENES, REFS, setup, source_setup, finish, generic_model, source_model, values
from scripts.compose_clear_indications import INDICATIONS
from scripts.compose_limits import call as k


def data(source=False):
    stem = 'clear-indications-core' if source else 'clear-indications'
    text = (ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8')
    return source_setup(text) if source else setup(text)


@pytest.mark.parametrize('threshold', [1, 3, 4])
def test_threshold_is_strict_and_must_exceed_neutral_discrimination(threshold):
    item = data()
    assert values(item, generic_model(item, threshold=threshold)) == [False] * 5


def test_uniform_positive_rescaling_does_not_change_the_evidence_ratio():
    item = data()
    for weight in (Fraction(1, 7), Fraction(1), Fraction(1000)):
        assert values(item, generic_model(item, weight=weight)) == [True, True, True, False, False]


def test_no_contrast_class_cannot_certify_a_diagnostic_sign():
    item = data(); model = generic_model(item)
    model['jptarget'] = lambda: Content(SCENES, (True,) * len(SCENES))
    assert values(item, model) == [False, False, False, False, True]
    model['jptarget'] = lambda: Content(SCENES, (False,) * len(SCENES))
    assert values(item, model) == [False] * 5


@pytest.mark.parametrize('variant', ['duplicate', 'omitted', 'zero_weight'])
def test_invalid_comparison_inventory_does_not_support_the_sign(variant):
    item = data(); model = generic_model(item)
    if variant == 'zero_weight': model['jpweight'] = lambda point: Fraction(0 if point == 'negativeone' else 1)
    else:
        points = (*SCENES, SCENES[0]) if variant == 'duplicate' else SCENES[:-1]
        model['jppoints'] = lambda: SequenceValue(points, '"situation"')
    assert values(item, model) == [False] * 5


def test_an_unclassified_second_item_is_not_a_second_clear_sign():
    item = data(); model = generic_model(item)
    model['jpclassifications'] = lambda evidence, point: evidence != 'signtwo' or point != 'positiveone'
    assert values(item, model) == [True, False, False, False, False]


def test_diagnostic_content_that_did_not_occur_is_not_a_current_sign():
    item = data()
    assert values(item, generic_model(item, signal=(False, True, True, False, False))) == [False] * 5


def test_a_semantically_identical_alias_does_not_inherit_the_record_link():
    old = data(); base = old['document']; base['statements'] = []
    base = parse(format_graph(base, 'compact') + 'd jpalias[] e[k jptarget[]].')
    alias = finish(base, 'k jpalias[]')
    assert values(alias, generic_model(old)) == [False] * 5
    assert values(alias, generic_model(alias)) == [True, True, True, False, False]


def test_the_actual_context_need_not_be_in_the_chosen_comparison_model():
    item = data(); model = generic_model(item)
    model['jppoints'] = lambda: SequenceValue(SCENES[1:], '"situation"')
    model['jpscope'] = lambda point: point != 'actual'
    assert values(item, model) == [True, True, True, False, False]


def test_unknown_target_ability_prevents_evidence_evaluation():
    item = data(True); model = source_model(item)
    def unknown(*args): raise ValueError('Target ability assessment unknown')
    model['ap'] = unknown
    with pytest.raises(ValueError, match='Target ability assessment unknown'):
        values(item, model)


def test_a_claim_about_the_signs_can_be_quoted_without_executing_its_evidence():
    item = data(True); doc = item['document']; doc['statements'] = []
    index = next(i for i, (name, _) in enumerate(INDICATIONS) if name == 'target')
    specialized = specialize_definition(doc, 'rme', 'jpclaim', {index: description(doc, item['target'])})
    body = k('jpclaim', *(REFS[name] for name, _ in INDICATIONS if name != 'target'))
    item['document'] = parse(format_graph(specialized.document, 'compact') + 'q[e[r[' + body + ']][r[' + body + ']]].')
    assert values(item, guarded(item['document'])) == [True]


def test_saved_evidence_preserves_history_and_keeps_the_source_reading_partial():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-clear-indications.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 7
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
