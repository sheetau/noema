import hashlib
import json
import pytest
from noema.grammar import parse
from scripts.check_retained_duties import ROOT, REPORT, PARENT, setup, select, model_for, values
from scripts.check_rod_setup import guarded


def data(source=False, indices=None):
    stem = 'retained-duties-core' if source else 'retained-duties'
    item = setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source)
    return select(item, indices) if indices is not None else item


def test_permission_to_speak_does_not_waive_an_office_duty():
    item = data(True, (2, 6, 7))
    assert values(item, model_for(item, (True, True, False, True, True, False))) == [False, True, False]


def test_retaining_duties_does_not_grant_permission_to_speak():
    item = data(True, (2, 6, 7))
    assert values(item, model_for(item, permitted=False)) == [True, False, False]


def test_retaining_a_requirement_is_not_fulfilling_it():
    item = data(True, (1, 2, 4, 5, 7))
    assert values(item, model_for(item, (True, True, True, True, False, False))) == [True, True, False, False, True]


def test_negative_requirements_are_not_replaced_by_positive_ones():
    item = data(True, (1, 4, 5))
    assert values(item, model_for(item, (True, True, True, True, True, True))) == [True, False, False]
    assert values(item, model_for(item, variant='flipped_sign')) == [False, False, False]


def test_disappearing_obligations_do_not_count_as_vacuous_fulfillment():
    item = data(True, (1, 4, 5))
    assert values(item, model_for(item, (True, True, False, False, True, False))) == [False, False, False]


def test_empty_reference_requirements_do_not_establish_preservation():
    item = data(True, (0, 1, 2, 5))
    assert values(item, model_for(item, variant='empty_items')) == [False] * 4


def test_an_empty_comparison_scope_is_not_a_verified_conditional():
    item = data(True, (2, 3, 5))
    assert values(item, model_for(item, variant='empty_cases')) == [False] * 3


def test_a_conditional_without_activity_instances_is_not_an_applicable_case():
    item = data(True, (2, 3, 5, 7))
    assert values(item, model_for(item, variant='no_instance')) == [True, False, False, True]


def test_activity_and_fulfillment_in_different_candidates_do_not_establish_compatibility():
    item = data(True, (2, 3, 4, 5))
    assert values(item, model_for(item, variant='split_fulfillment')) == [True, True, False, False]


def test_conflicting_requirements_can_remain_but_cannot_both_be_fulfilled():
    item = data(True, (0, 1, 2, 4, 5))
    assert values(item, model_for(item, variant='conflicting')) == [True, True, True, False, False]


@pytest.mark.parametrize('variant', ('other_person', 'other_office', 'other_issuer', 'other_description'))
def test_preservation_keeps_the_same_person_role_source_and_description(variant):
    item = data(True, (0, 1, 2, 7))
    assert values(item, model_for(item, variant=variant)) == [True, False, False, False]


def test_retention_does_not_require_evaluating_any_duty_description():
    item = data(True, (0, 1, 2, 3, 7)); model = model_for(item); forbidden = guarded(item['document'])
    for name in ('jxfirst', 'jxsecond', 'jxalias'): model[name] = forbidden[name]
    assert values(item, model) == [True] * 5


def test_quoting_the_permission_and_retention_condition_does_not_execute_it():
    item = data(True, (8,))
    assert item['disquotations_removed'] == 1
    assert values(item, guarded(item['document'])) == [True]


def test_fulfillment_rejects_unknown_execution_values():
    item = data(True, (4,)); model = model_for(item)
    model['jxfirst'] = guarded(item['document'])['jxfirst']
    with pytest.raises(ValueError, match='Unrelated primitive'): values(item, model)


def test_the_explicit_catalog_is_not_silently_treated_as_all_office_requirements():
    item = data(True, (2, 7)); model = model_for(item); original = model['h7a']
    def with_unlisted_duty(source, person, role, act, desc, sign, point):
        return original(source, person, role, act, desc, sign, point) or (
            (source, person, role, act, sign, point) == ('issuer', 'person', 'office', 'speechact', True, 'anchor') and desc.syntax == item['alias_syntax'])
    model['h7a'] = with_unlisted_duty
    assert values(item, model) == [True, True]


def test_opposed_public_requirement_blocks_permission_even_when_duties_are_retained():
    item = data(True, (2, 6, 7))
    assert values(item, model_for(item, variant='public_prohibited')) == [True, False, False]


def test_saved_evidence_preserves_history_and_limits_the_source_claim():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items(): assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-retained-duties.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 10
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    segment = report['alignment']['segments'][0]
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == segment['unit'])
    start, end = segment['range']
    assert unit['text'][start:end] == segment['text'] == 'unbeschadet ihrer Amtspflicht'
