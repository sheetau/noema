import hashlib
import json
import pytest
from noema.grammar import parse, format_graph
from scripts.check_action_standards import ROOT, REPORT, PARENT, STANDARD, setup, model_for, values
from scripts.check_rod_setup import guarded


def data(source=False, standards=None):
    stem = 'action-standards-core' if source else 'action-standards'
    return setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source, standards)


def only(item, indices):
    item['document']['statements'] = [item['document']['statements'][i] for i in indices]
    return item


def test_outer_approval_does_not_make_any_inner_claim_or_action_true():
    item = data(True)
    assert values(item, model_for(item)) == [False] * 6 + [True, False, True]


def test_actual_fit_does_not_require_the_person_to_approve():
    item = data()
    assert values(item, model_for(item, (True, False, False, False, False, False)))[6:] == [False, True, False]


def test_empty_standards_are_neither_failure_nor_evidence_of_fit():
    item = data(standards='l[' + STANDARD + '][]')
    assert values(item, model_for(item))[6:] == [False, False, False]


def test_a_second_failed_standard_prevents_fit_even_when_the_first_passes():
    item = data(); model = model_for(item, (True, True, False, False, False, False))
    model['jvsecond'] = lambda *args: False
    assert values(item, model)[6:] == [True, False, False]


def test_unknown_standards_are_not_filled_in_as_either_fit_or_failure():
    item = only(data(), (6, 7)); model = model_for(item)
    def unknown(*args): raise ValueError('Unknown standard')
    model['jvsecond'] = unknown
    with pytest.raises(ValueError, match='Unknown standard'): values(item, model)


def test_no_judgment_is_distinct_from_a_judgment_of_no_shortfall():
    item = data(True)
    assert values(item, model_for(item, (True, True, False, False, False, False), 'no_outer_judgment'))[6:] == [False, True, False]


def test_one_disagreeing_candidate_prevents_the_positive_judgment():
    item = data(); model = model_for(item)
    model['jvcandidates'] = lambda judgment, context, point: (judgment, context) == ('assessment', 'now') and point in ('belief', 'elsewhere')
    assert values(item, model)[8] is False


def test_actual_appraisal_does_not_execute_the_report_or_the_duty():
    item = only(data(True), (6, 7)); model = model_for(item); limited = guarded(item['document'])
    for name in ('jtperson', 'jtcontext', 'jvfirst', 'jvsecond'): limited[name] = model[name]
    assert values(item, limited) == [True, False]


def test_nested_appraisal_can_be_quoted_without_executing_any_primitive():
    item = data(True); base = item['document']; base['statements'] = []
    quoted = 'r[' + item['criterion'] + ']'
    item['document'] = parse(format_graph(base, 'compact') + 'q[e[' + quoted + '][' + quoted + ']].')
    assert values(item, guarded(item['document'])) == [True]


@pytest.mark.parametrize('bindings', ['l[a][]', 'l[a][k jtperson[] k jtperson[]]'])
def test_the_adapter_refuses_missing_or_extra_person_bindings(bindings):
    item = data(); base = item['document']; base['statements'] = []
    item['document'] = parse(format_graph(base, 'compact') + 'q[t[c[' + item['criterion'] + '][' + bindings + ']][k jtcontext[]]].')
    assert values(item, model_for(item)) == [False]


def test_a_different_bound_person_does_not_inherit_the_original_person_standards():
    item = data(); base = item['document']; base['statements'] = []
    item['document'] = parse(format_graph(base, 'compact') + 'q[t[c[' + item['criterion'] + '][l[a][k jtassessor[]]]][k jtcontext[]]].')
    assert values(item, model_for(item, (True, True, False, False, False, False))) == [False]


def test_order_and_duplicates_do_not_change_the_shortfall_result():
    first = 'i[person a action i[h[a a] e]][b point[k jvfirst[v person v action v point]]]'
    second = 'i[person a action i[h[a a] e]][b point[k jvsecond[v person v action v point]]]'
    for rules in ((first, second), (second, first), (first, second, first)):
        item = data(standards='l[' + STANDARD + '][' + ' '.join(rules) + ']')
        assert values(item, model_for(item))[6:] == [True, False, True]


def test_a_pure_noema_description_standard_is_not_a_lookup_for_a_word():
    initial = data()
    rule = 'i[person a action i[h[a a] e]][b point[e[v action][' + initial['action'] + ']]]'
    item = only(data(standards='l[' + STANDARD + '][' + rule + ']'), (6, 7))
    model = guarded(item['document']); model['jtperson'] = lambda: 'leader'; model['jtcontext'] = lambda: 'now'
    assert values(item, model) == [False, True]
    base = item['document']; base['statements'] = []
    alias = 'd jvactionalias[] h[a a] e[' + item['old']['action'] + '].'
    query = 'q[t[k rnf[k jtperson[] r[k jvactionalias[]] ' + item['standards'] + ']][k jtcontext[]]].'
    item['document'] = parse(format_graph(base, 'compact') + alias + query)
    assert values(item, model) == [False]


def test_evidence_preserves_history_and_does_not_claim_completed_dignity_semantics():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items(): assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-action-standards.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 3
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
