import hashlib
import json

import pytest

from noema.grammar import parse, format_graph
from scripts.check_rod_setup import guarded
from scripts.check_self_reports import ROOT, REPORT, PARENT, setup, model_for, values


def data(source=False):
    stem = 'self-reports-core' if source else 'self-reports'
    return setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source)


def test_a_delivered_self_report_can_be_false_at_every_inner_level():
    item = data()
    assert values(item, model_for(item, (True, True, True, False, False, False))) == [True, False, False, False, True, False]


def test_holding_a_judgment_does_not_mean_reporting_it():
    item = data()
    assert values(item, model_for(item, (False, False, False, True, False, True))) == [False, True, False, True, False, False]


def test_swapping_the_report_subject_does_not_change_the_speakers_judgment():
    item = data(True)
    assert values(item, model_for(item, variant='wrong_subject')) == [False, True, False, True, False, False]


def test_all_members_of_the_claimed_audience_need_the_same_presentation():
    item = data(); model = model_for(item); old = model['juconveys']
    model['juaudience'] = lambda person: person in ('listener', 'coholder')
    assert values(item, model) == [False, True, False, True, False, False]
    model['juconveys'] = lambda act, listener, subject, desc, point: old(act, 'listener' if listener == 'coholder' else listener, subject, desc, point)
    assert values(item, model) == [True, True, False, True, True, False]


def test_the_speaker_can_also_be_the_listener_without_changing_the_subject():
    item = data(); model = model_for(item); old = model['juconveys']
    model['juaudience'] = lambda person: person == 'leader'
    model['juconveys'] = lambda act, listener, subject, desc, point: listener == 'leader' and old(act, 'listener', subject, desc, point)
    assert values(item, model) == [True, True, False, True, True, False]


def test_a_report_record_does_not_execute_its_unknown_judgment_or_norms():
    item = data(True); model = model_for(item)
    item['document']['statements'] = [item['document']['statements'][i] for i in (0, 4)]
    limited = guarded(item['document'])
    for name in ('jtperson', 'jtcontext', 'juactivity', 'juaudience', 'dg', 'f3', 'f2'):
        limited[name] = model[name]
    assert values(item, limited) == [True, True]


def test_quoting_a_report_action_does_not_assert_that_it_happened():
    item = data(True); base = item['document']; base['statements'] = []
    action = item['action']
    item['document'] = parse(format_graph(base, 'compact') + 'q[e[r[' + action + ']][r[' + action + ']]].')
    assert values(item, guarded(item['document'])) == [True]


def test_a_semantically_identical_message_alias_does_not_inherit_the_delivery_record():
    item = data(True); base = item['document']; base['statements'] = []
    alias = 'd jureportalias[] h[a] f[' + item['message'] + '].'
    report = 'k hzft[k jtperson[] k juactivity[] p juaudience r[k jureportalias[]] k jtcontext[]]'
    item['document'] = parse(format_graph(base, 'compact') + alias + 'q[' + report + '].')
    assert values(item, model_for(item)) == [False]


def test_one_valid_judgment_is_enough_even_if_another_judgment_fails():
    item = data(); model = model_for(item)
    model['jtjudgments'] = lambda person, judgment, point: person == 'leader' and judgment in ('judge', 'otheract') and point == 'now'
    model['jtmatters'] = lambda judgment, subject, point: judgment in ('judge', 'otheract') and subject == 'leader' and point == 'now'
    assert values(item, model) == [True, True, False, True, True, False]


def test_evaluating_the_reported_judgment_requires_its_own_norm_inputs():
    item = data(True); model = model_for(item)
    item['document']['statements'] = [item['document']['statements'][1]]
    def unknown(*args): raise ValueError('Judgment target unknown')
    model['h7k'] = unknown
    with pytest.raises(ValueError, match='Judgment target unknown'):
        values(item, model)


def test_a_report_at_another_context_does_not_count_as_current_delivery():
    item = data(True)
    assert values(item, model_for(item, variant='other_context')) == [False, True, False, True, False, False]


def test_saved_evidence_keeps_the_infinitive_condition_separate_from_an_author_assertion():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-self-reports.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 8
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
