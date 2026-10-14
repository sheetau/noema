import hashlib
import json

import pytest

from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from scripts.check_enlightening_epoch import (
    ROOT, REPORT, PARENT, SCENES, setup, source_setup, generic_model,
    source_model, values, discourse_setup, discourse_model,
)
from scripts.compose_limits import call as k


def data(source=False):
    stem = 'enlightening-epoch-core' if source else 'enlightening-epoch'
    text = (ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8')
    return source_setup(text) if source else setup(text)


def test_missing_assessment_is_not_evidence_of_nonattainment():
    item = data()
    assert values(item, generic_model(item, (True, False, False, False, True))) == [False, False, True, False, False]


def test_attainment_can_coexist_with_continuing_progress():
    item = data()
    assert values(item, generic_model(item, (True, True, True, True, True))) == [True, True, True, False, False]


def test_current_attainment_does_not_require_past_or_future_attainment():
    item = data(); model = generic_model(item)
    model['jqcapable'] = lambda person: Content(SCENES, (False, True, False))
    assert values(item, model) == [True, True, True, False, False]


def test_future_progress_does_not_answer_a_question_about_now():
    item = data(); model = generic_model(item)
    model['jqprogress'] = lambda: Content(SCENES, (False, False, True))
    assert values(item, model) == [True, False, False, False, False]


@pytest.mark.parametrize('variant', ['hole', 'empty_people', 'absent_person'])
def test_epoch_and_nonempty_current_population_must_be_valid(variant):
    item = data()
    assert values(item, generic_model(item, variant=variant)) == [False] * 5


def test_same_content_does_not_erase_the_difference_between_question_and_assertion():
    item = data(); original = item['document']; original['statements'] = []
    truth = 'e[n p a b][n p a b]'
    args = ('k jqprogress[]', truth)
    expr = 'e[' + k('rij', *args) + '][' + k('rik', *args) + ']'
    # These pre-existing constructors are included through rmm and rmn.
    item['document'] = parse(format_graph(original, 'compact') + 'q[' + expr + '].')
    assert values(item, generic_model(item)) == [False]


def test_unknown_ability_is_refused_instead_of_becoming_a_negative_answer():
    item = data(True); model = source_model(item)
    def unknown(*args): raise ValueError('Current ability assessment unknown')
    model['ap'] = unknown
    with pytest.raises(ValueError, match='Current ability assessment unknown'):
        values(item, model)


def test_quoting_the_dialogue_does_not_execute_its_unknown_contents():
    item, question, answer = discourse_setup(data(True))
    assert values(item, discourse_model(item, question, answer)) == [True]


@pytest.mark.parametrize('variant', ['wrong_answer', 'reversed_order', 'unrelated_response'])
def test_a_different_or_unrelated_answer_is_not_attributed_to_this_question(variant):
    item, question, answer = discourse_setup(data(True))
    assert values(item, discourse_model(item, question, answer, variant)) == [False]


def test_saved_evidence_does_not_promote_the_candidate_to_a_completed_translation():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-enlightening-epoch.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 11
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
