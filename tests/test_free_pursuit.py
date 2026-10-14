import hashlib
import json

import pytest

from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from scripts.check_free_pursuit import ROOT, REPORT, PARENT, SCENES, setup, model_for, values
from scripts.check_topical_enablement import model_for as capacity_model


def data(source=False):
    stem = 'free-pursuit-core' if source else 'free-pursuit'
    return setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source)


def with_goal_question(item):
    result = dict(item)
    result['document'] = parse(format_graph(item['document'], 'compact') +
        'q[t[c[s[r[' + item['goal'] + ']]][l[a][k jmperson[]]]][k jmcontext[]]].')
    return result


def test_opportunity_does_not_assert_either_present_effort_or_goal_truth():
    item = with_goal_question(data()); model = model_for(item)
    assert values(item, model) == [True, True, True, False, True, False]
    model['jmgoals'] = lambda person: Content(SCENES, (True,) * len(SCENES))
    assert values(item, model) == [True, True, True, False, True, True]


@pytest.mark.parametrize('source', [False, True])
def test_unknown_goal_is_describable_but_not_claimed_true(source):
    item = data(source); model = model_for(item)
    if source:
        known = capacity_model(item['document'], (False,) * 4)
        model.update({name: callback for name, callback in known.items()
            if name.startswith('jk') or name in ('ab', 'ac', 'fa', 'fb', 'fc', 'fd', 'ad')})
    def unknown(*args): raise ValueError('Target ability is unknown')
    model['jkavailable' if source else 'jmgoals'] = unknown
    assert values(item, model) == [True, True, True, False, True]
    queried = with_goal_question(item)
    with pytest.raises(ValueError, match='Target ability is unknown'):
        values(queried, model)


def test_permission_alone_does_not_execute_unknown_effort():
    item = data(); item['document']['statements'] = item['document']['statements'][:1]
    model = model_for(item)
    def unknown(*args): raise ValueError('Effort not assessed')
    for name in ('jmoccurs', 'jmparticipates', 'jmwork', 'jmaims', 'jmavailable', 'jmoutcomes'):
        model[name] = unknown
    assert values(item, model) == [True]


def test_goal_binding_requires_exactly_one_person():
    item = data(); base = item['document']; base['statements'] = []
    goal = item['goal']
    questions = ''.join('q[t[c[s[r[' + goal + ']]][' + bindings + ']][k jmcontext[]]].' for bindings in (
        'l[a][]', 'l[a][k jmperson[]]', 'l[a][k jmperson[] k jmactivity[]]', 'l[a][k jmactivity[]]'))
    item['document'] = parse(format_graph(base, 'compact') + questions)
    model = model_for(item)
    model['jmgoals'] = lambda person: Content(SCENES, tuple(person == 'alice' for _ in SCENES))
    assert values(item, model) == [False, True, False, False]


def test_permission_for_one_method_and_availability_of_another_do_not_combine():
    item = data(); model = model_for(item)
    model['jmavailable'] = lambda person, activity, point: activity == 'other' and point == 'now'
    assert values(item, model) == [True, False, False, False, False]


def test_empty_group_has_no_collective_opportunity():
    item = data(); model = model_for(item); model['jmscope'] = lambda person: False
    assert values(item, model) == [True, True, True, False, False]


def test_another_persons_participation_is_not_the_subjects_effort():
    item = data(); model = model_for(item)
    model['jmparticipates'] = lambda person, activity, point: person == 'bob' and activity == 'plan' and point == 'later'
    assert values(item, model) == [True, False, False, False, False]


def test_a_role_mismatch_for_one_member_blocks_the_group_not_the_other_person():
    item = data(); model = model_for(item)
    model['jmroles'] = lambda person: 'role' if person == 'alice' else 'other'
    assert values(item, model) == [True, True, True, False, False]


def test_saved_evidence_preserves_history_and_leaves_the_reading_partial():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-free-pursuit.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 10
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
