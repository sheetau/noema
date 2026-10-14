import hashlib
import json
import pytest
from scripts.check_cohort_responses import ROOT, REPORT, PARENT, setup, select, model_for, values
from scripts.check_rod_setup import guarded
from noema.grammar import parse


def data(source=False, indices=None, **kwargs):
    stem = 'cohort-responses-core' if source else 'cohort-responses'
    item = setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source, **kwargs)
    return select(item, indices) if indices is not None else item


def test_different_people_can_respond_at_different_times_without_unanimity_at_one_time():
    item = data(indices=(1, 2, 3, 4, 5))
    assert values(item, model_for(item)) == [True, False, True, False, True]


def test_simultaneous_unanimity_is_stronger_than_memberwise_eventual_response():
    item = data(indices=(1, 2, 3, 4, 5))
    assert values(item, model_for(item, (True, True, True, False, True, False))) == [True, True, False, False, True]


def test_one_response_does_not_make_an_entire_group_respond():
    item = data(indices=(1, 2, 5))
    assert values(item, model_for(item, (True, True, True, False, False, False))) == [True, False, False]


def test_empty_groups_do_not_supply_vacuous_unanimity():
    item = data(indices=(1, 2, 3, 4, 5))
    assert values(item, model_for(item, (False, False, True, True, True, True))) == [False] * 5


def test_outsiders_responses_do_not_replace_members_responses():
    item = data(indices=(1, 2, 3, 4, 5))
    assert values(item, model_for(item, (True, False, False, False, True, True))) == [False] * 5


def test_posterity_need_not_be_the_immediately_following_epoch():
    item = data(indices=(0,))
    # The modeled history has an intervening 'gap' point outside either epoch.
    assert values(item, model_for(item)) == [True]


def test_temporal_cohorts_may_share_all_their_members():
    item = data(True, (0,))
    assert values(item, model_for(item)) == [True]


@pytest.mark.parametrize('variant', ('missing_member', 'extra_member', 'changed_population', 'overlapping_periods', 'future_context'))
def test_cohort_description_requires_consistent_membership_and_temporal_anchor(variant):
    item = data(True, (0,))
    assert values(item, model_for(item, variant=variant)) == [False]


def test_current_and_later_membership_are_bound_to_the_corresponding_periods():
    item = data(True, (8, 9)); model = model_for(item)
    model['jqbelongs'] = lambda group, person, context: context == 'now' and (group, person) in (('oldgroup', 'alice'), ('newgroup', 'bob'))
    assert values(item, model) == [True, False]


def test_deserving_a_scoped_response_does_not_make_it_occur():
    item = data(True, (7, 8, 9))
    assert values(item, model_for(item, variant='no_occurrence')) == [True, False, False]


def test_actual_responses_need_not_be_deserved():
    item = data(True, (7, 8, 9))
    assert values(item, model_for(item, ground=False)) == [False, True, True]
    assert values(item, model_for(item, worthy=False)) == [False, True, True]


def test_empty_criteria_do_not_certify_response_worthiness():
    item = data(True, (7,), empty_standards=True)
    assert values(item, model_for(item)) == [False]


def test_response_worthiness_can_be_checked_without_running_any_response():
    item = data(True, (7,)); model = model_for(item); limited = guarded(item['document'])
    for name in ('jqground', 'jqstandard', 'jqsubject', 'jqcontext'): limited[name] = model[name]
    assert item['disquotations_removed'] == 1
    assert values(item, limited) == [True]


def test_a_description_of_current_and_later_responses_does_not_assert_them():
    item = data(True, (6,))
    assert values(item, guarded(item['document'])) == [True]


@pytest.mark.parametrize('variant', ('wrong_subject', 'wrong_message', 'empty_audience'))
def test_response_binding_preserves_subject_message_and_audience(variant):
    item = data(True, (7, 8, 9))
    assert values(item, model_for(item, variant=variant)) == [True, False, False]


def test_unknown_outsider_responses_are_not_silently_filled_in():
    item = data(indices=(1,)); model = model_for(item); original = model['jqresponse']
    def unknown(speaker, activity, subject):
        if speaker == 'oldgroup': raise ValueError('Unknown outsider response')
        return original(speaker, activity, subject)
    model['jqresponse'] = unknown
    with pytest.raises(ValueError, match='Unknown outsider response'): values(item, model)


def test_saved_evidence_preserves_history_and_keeps_source_alignment_partial():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items(): assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-cohort-responses.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 7
    assert child['statements'] == parent['statements']
    assert report['new_definitions'] == 7 and report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    segment = report['alignment']['segments'][0]
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == segment['unit'])
    start, end = segment['range']
    assert unit['text'][start:end] == segment['text'] == 'Welt und Nachwelt'
