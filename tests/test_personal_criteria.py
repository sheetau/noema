import hashlib
import json

import pytest

from noema.grammar import parse, format_graph
from noema.higher_order_semantics import evaluate_document
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_personal_criteria import (
    ROOT, REPORT, PARENT, DOMAIN, setup, model_for, values, policy_setup, add_criteria_model, prior,
)


def core(): return (ROOT / 'examples/v014/personal-criteria-core.noema').read_text(encoding='utf-8')


@pytest.mark.parametrize('items, expected', [
    (('alice', 'alpha', 'old', 'new'), True),
    (('bob', 'alpha', 'old', 'new'), False),
    (('alice', 'beta', 'old', 'new'), False),
    (('alice', 'alpha', 'new', 'old'), False),
    (('alice', 'alice', 'alice', 'alice'), True),
    ((), False),
    (('alice', 'alpha', 'old'), False),
    (('alice', 'alpha', 'old', 'new', 'alice'), False),
])
def test_four_positions_are_not_dropped_reordered_or_deduplicated(items, expected):
    extra = '''r jstest[a a a a d] c.
d jscomparison[person a community a older a newer a] e[b point[k jstest[v person v community v older v newer v point]]].
r jspoint[] d.'''
    extra += ''.join('r jsslot' + chr(97 + i) + '[] a.' for i in range(len(items)))
    sequence = 'l[a][' + ' '.join('k jsslot' + chr(97 + i) + '[]' for i in range(len(items))) + ']'
    doc = candidate(core(), extra + 'q[t[c[k rli[p jscomparison]][' + sequence + ']][k jspoint[]]].')
    model = guarded(doc)
    model['jstest'] = lambda person, community, older, newer, point: (person, community, older, newer) in (
        ('alice', 'alpha', 'old', 'new'), ('alice', 'alice', 'alice', 'alice'))
    model['jspoint'] = lambda: 'now'
    for i, item in enumerate(items): model['jsslot' + chr(97 + i)] = lambda item=item: item
    assert evaluate_document(doc, individuals=DOMAIN, situations=('now',), primitives=model)[0]['value'] is expected


def test_the_second_person_can_adopt_a_different_substantive_criterion():
    data = setup(core(), True, True)
    assert values(data, model_for(data)) == [True, True, False]
    replacement = parse('n:d jsalias[] h[j[a]] e[i[bindings j[a]][b point[e[n p a b][n p b b]]]].')['declarations'][0]
    doc = data['document']
    doc['declarations'] = [replacement if row['name'] == 'jsalias' else row for row in doc['declarations']]
    data['document'] = parse(format_graph(doc, 'compact'))
    # Bob's adopted description remains the same; its content now differs.
    assert values(data, model_for(data)) == [True, False, False]


def test_a_future_justification_does_not_retroactively_justify_the_current_agreement():
    data = setup(core(), True); model = model_for(data)
    # Past undertakings still establish the ordinary agreement. Matching reasons
    # exist only for additional future undertakings, after the assessment point.
    for name in ('jnoccurs', 'jnperforms', 'jndeclares'):
        old = model[name]
        model[name] = lambda *args, old=old: old(*args[:-1], 'past' if args[-1] == 'later' else args[-1])
    model['dg'] = model['jnoccurs']; model['f3'] = model['jnperforms']
    for name in ('jsjudgments', 'jsmatters', 'jslinked', 'jsadopted', 'jsused'):
        old = model[name]
        model[name] = lambda *args, old=old: args[-1] == 'later' and old(*args[:-1], 'past')
    old_candidates = model['jscandidates']
    model['jscandidates'] = lambda judgment, point, candidate: point == 'later' and old_candidates(judgment, 'past', candidate)
    model['fa'] = model['jsjudgments']; model['fb'] = model['jsmatters']
    assert values(data, model) == [True, False, False]


def test_unknown_support_is_not_filled_from_the_persons_judgment():
    data = setup(core(), True); model = model_for(data)
    def unknown(*args): raise ValueError('Support is unknown')
    model['jssupported'] = unknown
    with pytest.raises(ValueError, match='Support is unknown'):
        values(data, model)


def test_truth_without_support_is_not_the_adopted_information_improvement():
    data = setup(core(), True)
    assert values(data, model_for(data, bits=(True,) * 5)) == [True, True, True]
    model = model_for(data, bits=(True,) * 5, variant='unsupported')
    assert values(data, model) == [True, False, False]


def test_an_unselected_community_is_not_given_an_unconditional_protection_requirement():
    data = policy_setup(core())
    model, scenes = prior.policy_model(data, 'wrong_activity')
    model = add_criteria_model(data, model, scenes, bits=(True, True, False, True, False), policy=True)
    assert values(data, model, scenes, max_steps=64_000_000) == [False, True]


def test_saved_parent_and_evidence_do_not_promote_partial_reading_to_completion():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-personal-criteria.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 6
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
