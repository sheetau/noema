import hashlib
import json
import pytest
from noema.grammar import parse
from scripts.check_personal_matter_freedom import ROOT, REPORT, PARENT, setup, select, model_for, values
from scripts.check_rod_setup import guarded


def data(source=False, indices=None):
    stem = 'personal-matter-freedom-core' if source else 'personal-matter-freedom'
    item = setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source)
    return select(item, indices) if indices is not None else item


def test_one_permitted_matter_per_person_does_not_mean_all_their_matters_are_free():
    item = data(indices=(0, 1))
    assert values(item, model_for(item, (True, True, True, False, False, True))) == [True, False]


def test_another_persons_permission_does_not_fill_a_gap():
    item = data(indices=(0, 1))
    assert values(item, model_for(item, (True, True, True, True, False, True))) == [True, False]
    assert values(item, model_for(item, (True, False, True, True, False, True))) == [True, True]


def test_people_can_have_different_matter_domains():
    item = data(True, (0, 1))
    assert values(item, model_for(item, (True, True, True, True, False, True))) == [True, True]
    assert values(item, model_for(item, variant='outside_denial')) == [True, True]


def test_empty_people_do_not_prove_freedom():
    item = data(indices=(0, 1))
    assert values(item, model_for(item, (False, False, True, True, True, True))) == [False, False]


@pytest.mark.parametrize('variant', ('empty_cases', 'empty_activities', 'unassessed', 'other_self'))
def test_missing_scope_activity_or_assessment_is_not_filled_with_permission(variant):
    item = data(True, (0, 1))
    assert values(item, model_for(item, variant=variant)) == [False, False]


@pytest.mark.parametrize('variant', ('negative_missing', 'opposing_requirement'))
def test_freedom_requires_both_directions_without_opposing_requirements(variant):
    item = data(True, (0, 1))
    assert values(item, model_for(item, variant=variant)) == [True, False]


def test_permission_does_not_execute_the_own_judgment_description():
    item = data(True, (0, 1, 2, 3))
    assert values(item, model_for(item)) == [True, True, False, False]


def test_normative_freedom_does_not_require_faculty_use_reasons_or_guidance_facts():
    item = data(True, (1,)); model = model_for(item); forbidden = guarded(item['document'])
    for name in ('ab', 'ac', 'fc', 'fd', 'ad'): model[name] = forbidden[name]
    assert values(item, model) == [True]


def test_action_descriptions_remain_specific_to_the_same_matter():
    item = data(True, (1, 2, 3))
    assert values(item, model_for(item, performed=True)) == [True, True, False]
    assert values(item, model_for(item, variant='other_actual_matter', performed=True)) == [True, False, True]


@pytest.mark.parametrize('variant', ('foreign_faculty', 'other_reason', 'guided'))
def test_own_reason_cannot_be_borrowed_from_another_owner_or_judgment(variant):
    item = data(True, (1, 2, 3))
    assert values(item, model_for(item, variant=variant, performed=True)) == [True, False, False]


def test_an_actual_judgment_does_not_supply_its_permission():
    item = data(True, (1, 2, 3))
    assert values(item, model_for(item, (True, True, False, False, False, False), performed=True)) == [False, True, False]


def test_a_closed_judgment_description_is_quotable_without_executing_it():
    item = data(True, (4,))
    assert values(item, guarded(item['document'])) == [True]


def test_unknown_moral_scope_is_not_assumed_empty():
    item = data(True, (1,)); model = model_for(item)
    model['se'] = guarded(item['document'])['se']
    with pytest.raises(ValueError, match='Unrelated primitive'): values(item, model)


def test_eager_evaluation_may_request_inputs_outside_the_classification_cases():
    item = data(True, (1,)); model = model_for(item); original = model['se']
    def unknown(judgment, person, point):
        if point == 'now': raise ValueError('Unknown outside-case self-assessment')
        return original(judgment, person, point)
    model['se'] = unknown
    with pytest.raises(ValueError, match='Unknown outside-case'): values(item, model)


def test_same_action_individual_does_not_erase_the_matter_in_the_norm_description():
    item = data(True, (1,)); model = model_for(item)
    original = model['h7b']
    model['h7b'] = lambda source, person, role, act, desc, sign, point: original(source, person, role, act, desc, sign, point) and desc.syntax == item['action_syntax'][0]
    assert values(item, model) == [False]


def test_saved_evidence_preserves_parent_and_marks_the_new_clause_partial():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items(): assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-personal-matter-freedom.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 7
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    segment = report['alignment']['segments'][0]
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == segment['unit'])
    start, end = segment['range']
    assert unit['text'][start:end] == segment['text']
    assert segment['text'].startswith('Jedem frei ließ') and segment['text'].endswith('Vernunft zu bedienen')
