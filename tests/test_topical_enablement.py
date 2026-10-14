import hashlib
import json

import pytest

from noema.grammar import parse
from noema.higher_order_semantics import evaluate_document
from scripts.check_topical_enablement import ROOT, REPORT, PARENT, DOMAIN, SCENES, setup, model_for, values


def core(): return (ROOT / 'examples/v014/topical-enablement-core.noema').read_text(encoding='utf-8')


def test_topic_scope_cannot_shrink_inside_the_enabling_outcome():
    doc = setup(core(), True); model = model_for(doc, (False, False, True, True), 'split_results')
    assert values(doc, model)[:4] == [True, False, True, False]
    # Explicitly selecting another anchor asks a different, weaker question.
    model['jkanchor'] = lambda: 'trained'
    assert values(doc, model)[:4] == [True, False, True, True]


def test_one_persons_future_ability_is_not_anothers():
    doc = setup(core(), True); model = model_for(doc, (False, False, False, True))
    assert values(doc, model)[:4] == [True, False, True, False]
    model['jkperson'] = lambda: 'bob'
    assert values(doc, model)[:4] == [True, False, True, True]


def test_enabler_is_explicit_and_can_be_the_target_person():
    doc = setup(core(), True); model = model_for(doc, (False, False, True, True), 'wrong_enabler')
    assert values(doc, model)[3] is False
    model['jkenabler'] = lambda: 'alice'
    assert values(doc, model)[3] is True


@pytest.mark.parametrize('bits,variant', [
    ((False,) * 4, 'no_effects'), ((True, False, False, False), 'empty_selected'),
])
def test_an_unassessed_population_is_not_counted_as_zero_ability(bits, variant):
    doc = setup(core(), True)
    assert values(doc, model_for(doc, (False,) * 4))[-1] is True
    assert values(doc, model_for(doc, bits, variant))[-1] is False


def test_no_relevant_matters_does_not_certify_ability():
    doc = setup(core(), True); model = model_for(doc, (True,) * 4)
    model['jktopics'] = lambda *args: False
    assert values(doc, model) == [False, False, True, False, False]


def test_complete_population_check_is_independent_of_the_upper_bound():
    doc = setup(core(), True)
    assert values(doc, model_for(doc, (False,) * 4, upper=1))[-1] is True
    assert values(doc, model_for(doc, (False,) * 4, population=('alice',), upper=1))[-1] is False


def test_unknown_support_does_not_prevent_scope_assessment_but_refuses_ability_evaluation():
    doc = setup(core(), True); model = model_for(doc, (True,) * 4)
    def unknown(*args): raise ValueError('Judgment support unknown')
    model['fd'] = model['jksupport'] = unknown
    assessment = {**doc, 'statements': doc['statements'][:1]}
    assert values(assessment, model) == [True]
    with pytest.raises(ValueError, match='Judgment support unknown'):
        values(doc, model)


def test_each_matter_can_use_its_own_method():
    doc = setup(core(), True); model = model_for(doc, (True,) * 4); original = model['jkavailable']
    plans = {'matterone': 'planone', 'mattertwo': 'plantwo'}
    def available(person, matter, plan, point):
        return plans.get(matter) == plan and original(person, matter, 'plan', point)
    def outcomes(person, matter, plan, start, end):
        return available(person, matter, plan, start) and end == 'judged'
    model.update(jkavailable=available, jkoutcomes=outcomes, jkselected=outcomes)
    rows = evaluate_document(doc, primitives=model, individuals=(*DOMAIN, *plans.values()), situations=SCENES, max_steps=16_000_000)
    assert [row['value'] for row in rows] == [True, True, True, True, False]


def test_saved_evidence_preserves_history_and_marks_the_reading_partial():
    r = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in r['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-topical-enablement.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 11
    assert child['statements'] == parent['statements']
    assert r['new_primitives'] == r['new_author_statements'] == 0
    assert not r['alignment']['semantic_completion']
    assert r['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
