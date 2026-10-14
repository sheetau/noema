import hashlib
import json

import pytest

from noema.grammar import parse, format_graph
from scripts.check_rod_setup import guarded
from scripts.check_scoped_nonprescription import ROOT, REPORT, PARENT, setup, model_for, values


def data(source=False):
    stem = 'scoped-nonprescription-core' if source else 'scoped-nonprescription'
    text = (ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8')
    return setup(text, source)


def test_silence_is_not_positive_freedom_or_actual_duty():
    item = data()
    assert values(item, model_for(item, (False, False, False, False, False, True))) == [True, True, True, False, False, True, False]


def test_compulsory_execution_conflicts_with_the_option_not_to_execute():
    item = data()
    assert values(item, model_for(item, (True, False, True, True, False, True))) == [True, True, False, False, False, True, False]


def test_permission_from_another_role_is_not_reused():
    item = data(); model = model_for(item)
    model['jtroles'] = lambda person: 'crown'
    assert values(item, model) == [True, True, True, False, False, True, False]


def test_another_regulators_requirements_do_not_change_this_regulators_policy():
    item = data(); model = model_for(item); old = model['jtinnerrequired']
    model['jtinnerrequired'] = lambda source, person, role, act, desc, sign, point: source == 'external' or old(source, person, role, act, desc, sign, point)
    assert values(item, model) == [True, True, True, True, False, True, True]


def test_outside_topic_activity_is_ignored_until_explicitly_included():
    item = data(); model = model_for(item); old = model['jtinnerrequired']
    model['jtinnerrequired'] = lambda source, person, role, act, desc, sign, point: act == 'otheract' or old(source, person, role, act, desc, sign, point)
    assert values(item, model) == [True, True, True, True, False, True, True]
    model['jtactivities'] = lambda person, act, topic, anchor: person in ('alice', 'bob') and act in ('act', 'otheract') and (topic, anchor) == ('faith', 'now')
    assert values(item, model) == [True, True, False, False, False, True, False]


def test_changing_the_topic_anchor_does_not_silently_reuse_the_scope():
    item = data(); model = model_for(item)
    model['jtanchor'] = lambda: 'elsewhere'
    assert values(item, model) == [True, False, False, False, False, True, False]


def test_a_duty_judgment_can_be_evaluated_without_running_its_policy():
    item = data(True); model = model_for(item)
    item['document']['statements'] = item['document']['statements'][4:6]
    unknown = guarded(item['document'])
    model['h7a'] = unknown['h7a']; model['h7b'] = unknown['h7b']
    assert values(item, model) == [False, True]


def test_a_candidate_set_containing_the_actual_counterexample_rejects_the_judgment():
    item = data(); model = model_for(item)
    model['jtcandidates'] = lambda judge, context, point: (judge, context) == ('judge', 'now') and point in ('now', 'belief')
    assert values(item, model) == [True, True, True, True, False, False, True]


@pytest.mark.parametrize('bindings', ['l[a][]', 'l[a][k jtperson[] k jtperson[]]', 'l[a][k jtassessor[]]'])
def test_policy_and_duty_preserve_one_exact_regulator_binding(bindings):
    item = data(); base = item['document']; base['statements'] = []
    queries = ['t[c[' + item[name] + '][' + bindings + ']][k jtcontext[]]' for name in ('policy', 'duty')]
    item['document'] = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    assert values(item, model_for(item, (False, False, True, True, True, True))) == [False, False]


def test_cyclic_office_order_does_not_certify_a_unique_head():
    item = data(); model = model_for(item)
    model['jtabove'] = lambda high, low, org, point: org == 'organization' and (high, low) in (('crown', 'suboffice'), ('suboffice', 'crown'))
    assert values(item, model) == [False, True, True, True, False, True, True]


def test_another_organizations_holder_does_not_destroy_local_uniqueness():
    item = data(); model = model_for(item); old = model['jtholders']
    model['jtholders'] = lambda person, role, org, point: old(person, role, org, point) or (person, role, org) == ('coholder', 'crown', 'external')
    assert values(item, model) == [True, True, True, True, False, True, True]


def test_unknown_norm_assessment_does_not_certify_nonprescription():
    item = data(); model = model_for(item)
    def unknown(*args): raise ValueError('Norm assessment unknown')
    model['jtassessed'] = unknown
    with pytest.raises(ValueError, match='Norm assessment unknown'):
        values(item, model)


def test_an_unknown_execution_is_not_run_to_infer_permission():
    item = data(True); model = model_for(item)
    def unknown(*args): raise ValueError('Execution is not established')
    model['jtexecution'] = unknown
    assert values(item, model) == [True, True, True, True, False, True, True]


def test_saved_evidence_preserves_history_and_marks_the_new_paragraph_partial():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-scoped-nonprescription.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 10
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert {row['unit'] for row in report['alignment']['segments']} == {'kant-1784:u0015'}
