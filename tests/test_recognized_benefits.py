import hashlib
import json
import pytest
from noema.grammar import parse, format_graph
from scripts.check_recognized_benefits import ROOT, REPORT, PARENT, setup, select, model_for, values
from scripts.check_rod_setup import guarded


def data(source=False, indices=None):
    stem = 'recognized-benefits-core' if source else 'recognized-benefits'
    item = setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source)
    return select(item, indices) if indices is not None else item


def test_an_actual_favorable_result_does_not_make_the_recipient_recognize_its_agent():
    item = data(True, (0, 1, 2, 3))
    assert values(item, model_for(item, (True, True, True, True, False, True))) == [True, False, True, False]


def test_mistaken_recognition_does_not_require_an_actual_achievement():
    item = data(True, (0, 1, 2, 3))
    assert values(item, model_for(item, (False, True, True, True, True, True))) == [False, True, True, True]


def test_recognition_does_not_imply_an_actual_response():
    item = data(True, (0, 1, 2, 3))
    assert values(item, model_for(item, (True, True, True, True, True, False))) == [True, True, False, False]


def test_liking_the_result_is_distinct_from_both_achievement_and_recognition():
    item = data(indices=(0, 1))
    assert values(item, model_for(item, (False, True, False, True, True, False))) == [False, False]
    assert values(item, model_for(item, (True, False, True, True, True, False))) == [False, True]


def test_a_future_achievement_is_not_a_completed_benefit_at_the_current_time():
    item = data(True, (0, 1))
    assert values(item, model_for(item, variant='future_achievement')) == [False, True]


@pytest.mark.parametrize('variant', ('wrong_activity_link', 'wrong_criterion', 'wrong_judgment_subject', 'empty_candidates'))
def test_recognition_preserves_the_same_criterion_roles_event_and_candidate_scope(variant):
    item = data(True, (0, 1, 3))
    assert values(item, model_for(item, variant=variant)) == [True, False, False]


def test_a_single_counterexample_candidate_prevents_positive_recognition():
    item = data(indices=(0, 1)); bits = (False, True, True, True, True, False)
    assert values(item, model_for(item, bits)) == [False, True]
    assert values(item, model_for(item, bits, 'mixed_candidates')) == [False, False]


def test_an_actual_state_change_without_causal_production_does_not_establish_the_benefactor():
    item = data(True, (0, 1, 2, 3))
    assert values(item, model_for(item, variant='no_cause')) == [False, False, True, False]


def test_agent_and_recipient_cannot_be_swapped_and_missing_slots_are_not_inferred():
    item = data(True, (0, 5, 6))
    assert values(item, model_for(item)) == [True, False, False]


def test_the_three_argument_adapter_preserves_duplicate_individuals():
    item = data(); base = item['document']; base['statements'] = []
    relation = 'i[target a person a activity a][b point[w[e[v target][v person]][u[e[v person][v activity]]]]]'
    criterion = 'k roq[' + relation + ']'
    queries = ['t[c[' + criterion + '][l[a][k jrtarget[] k jrtarget[] k jractivity[]]]][k jrcontext[]]',
        't[c[' + criterion + '][l[a][k jrtarget[] k jractivity[] k jrtarget[]]]][k jrcontext[]]']
    item['document'] = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    assert values(item, model_for(item)) == [True, False]


@pytest.mark.parametrize('variant', ('wrong_response_subject', 'outside_cohort'))
def test_recognizing_a_benefit_does_not_replace_the_response_subject_or_speaker_scope(variant):
    item = data(True, (0, 1, 2, 3))
    assert values(item, model_for(item, variant=variant)) == [True, True, False, False]


def test_quoting_a_recognition_condition_never_evaluates_the_benefit_or_response():
    item = data(True, (4,))
    assert item['disquotations_removed'] >= 2
    assert values(item, guarded(item['document'])) == [True]


def test_unknown_affective_inputs_are_not_filled_with_false():
    item = data(True, (0,)); model = model_for(item)
    model['id'] = guarded(item['document'])['id']
    with pytest.raises(ValueError, match='Unrelated primitive'): values(item, model)


def test_another_persons_involvement_does_not_establish_the_named_benefactor():
    item = data(True, (0,)); model = model_for(item)
    model['df'] = lambda person, activity, point: (person, activity, point) == ('other', 'benefit', 'done')
    assert values(item, model) == [False]


def test_saved_evidence_keeps_historical_parent_and_marks_gratitude_incomplete():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items(): assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-recognized-benefits.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 7
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['status'].endswith('not_complete_gratitude')
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    segment = report['alignment']['segments'][0]
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == segment['unit'])
    start, end = segment['range']
    assert unit['text'][start:end] == segment['text'] == 'dankbaren'
