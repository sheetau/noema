import hashlib
import json
import pytest
from noema.grammar import parse
from scripts.check_recognized_benefits import select
from scripts.check_reasoned_responses import ROOT, REPORT, PARENT, setup, model_for, values
from scripts.check_rod_setup import guarded


def data(source=False, indices=None):
    stem = 'reasoned-responses-core' if source else 'reasoned-responses'
    result = setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source)
    return select(result, indices) if indices is not None else result


def test_coincident_recognition_appraisal_and_response_do_not_supply_a_reason_link():
    item = data(True, (0, 1, 2, 3, 4))
    assert values(item, model_for(item, (True, True, False, True, True, True))) == [False, False, True, False, False]


def test_using_a_reason_does_not_imply_that_it_supports_the_assessment():
    item = data(True, (0, 1, 2, 3, 4))
    assert values(item, model_for(item, (True, True, True, False, True, True))) == [True, False, True, True, False]


def test_support_does_not_imply_the_person_used_the_reason():
    item = data(indices=(0, 1, 3, 4))
    assert values(item, model_for(item, (True, True, False, True, True, True))) == [False] * 4


def test_evaluation_and_response_do_not_supply_the_motive_relation():
    item = data(True, (0, 1, 2, 3, 4))
    assert values(item, model_for(item, (True, True, True, True, True, False))) == [True, True, True, False, False]


def test_a_motive_and_judgments_do_not_imply_the_response_was_performed():
    item = data(True, (0, 1, 2, 3, 4))
    assert values(item, model_for(item, (True, True, True, True, False, True))) == [True, True, False, False, False]


def test_a_mistaken_benefit_belief_can_motivate_a_response():
    item = data(True, (0, 1, 3, 4, 6))
    assert values(item, model_for(item, actual=False)) == [True, True, True, True, False]


def test_recognizing_the_benefit_does_not_supply_positive_response_worthiness():
    item = data(True, (0, 1, 2, 3, 4))
    assert values(item, model_for(item, (True, False, True, True, True, True))) == [False, False, True, False, False]


@pytest.mark.parametrize('variant', ('other_judge', 'other_subject', 'wrong_assessment_description', 'empty_assessment_candidates'))
def test_the_same_judge_subject_description_and_nonempty_candidates_are_required(variant):
    item = data(True, (0, 1, 3, 4))
    assert values(item, model_for(item, variant=variant)) == [False] * 4


def test_reason_use_and_support_have_explicit_and_different_argument_directions():
    item = data(True, (0, 1, 3, 4))
    assert values(item, model_for(item, variant='reverse_use')) == [False] * 4
    assert values(item, model_for(item, variant='reverse_support')) == [True, False, True, False]


@pytest.mark.parametrize('variant', ('other_motive_person', 'other_motive_action', 'other_motive_judgment', 'other_motive_time'))
def test_a_motive_for_another_person_act_judgment_or_time_is_not_reused(variant):
    item = data(True, (0, 1, 2, 3, 4))
    assert values(item, model_for(item, variant=variant)) == [True, True, True, False, False]


def test_self_support_is_not_a_pair_of_distinct_judgments():
    item = data(indices=(0, 1)); model = model_for(item, variant='same_judgment')
    model['jslinked'] = lambda node, criterion, bindings, point: node == 'judgment' and point == 'now'
    model['jsuses'] = lambda assessment, reason, point: (assessment, reason, point) == ('judgment', 'judgment', 'now')
    model['jssupports'] = model['jsuses']
    assert values(item, model) == [False, False]


def test_a_quoted_motivated_response_does_not_run_the_judgments_or_response():
    item = data(True, (5,))
    assert item['disquotations_removed'] == 7
    assert values(item, guarded(item['document'])) == [True]


def test_reason_use_does_not_need_an_answer_to_the_separate_support_question():
    item = data(True, (0, 3)); model = model_for(item)
    model['fd'] = guarded(item['document'])['fd']
    assert values(item, model) == [True, True]


def test_unknown_motivation_is_not_silently_inferred_or_replaced_by_false():
    item = data(True, (3,)); model = model_for(item)
    model['jsmotivates'] = guarded(item['document'])['jsmotivates']
    with pytest.raises(ValueError, match='Unrelated primitive'): values(item, model)


def test_saved_record_preserves_the_parent_without_claiming_complete_gratitude():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items(): assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-reasoned-responses.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 6
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion'] and report['status'].endswith('not_complete_gratitude')
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    segment = report['alignment']['segments'][0]
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == segment['unit'])
    start, end = segment['range']
    assert unit['text'][start:end] == segment['text'] == 'dankbaren'
