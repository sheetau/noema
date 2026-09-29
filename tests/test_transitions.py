from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_transitions import generic_checks, source_checks, source_alignment
from scripts.compose_transitions import ROOT, generic_composed, source_composed


def test_state_change_requires_a_linked_process_and_a_changed_truth_value():
    result = generic_checks()
    assert len(result['truth_cases']) == 8
    assert sum(row['became_true'] for row in result['truth_cases']) == 1
    assert any(row['after'] and not row['process_exists'] and not row['became_true'] for row in result['truth_cases'])
    assert any(row['before'] and row['after'] and row['linked'] and not row['became_true'] for row in result['truth_cases'])
    assert len(result['invalid_bindings']) == 5
    assert all(values == [False, False] for values in result['invalid_bindings'].values())


def test_release_binds_the_affected_person_and_changes_the_old_prior_condition():
    result = source_checks()
    rows = result['witnesses']
    assert len(rows) == 12
    assert [name for name, row in rows.items() if row['transition']] == ['baseline']
    for name in ('no_process', 'wrong_process', 'no_affected_subject', 'wrong_affected_subject', 'no_prior_dependence'):
        assert rows[name]['later_state']
    assert result['old_vs_new']['baseline'] == {'new_transition_prior': True, 'old_state_only_prior': True}
    for name in ('no_process', 'no_prior_dependence'):
        assert result['old_vs_new'][name] == {'new_transition_prior': False, 'old_state_only_prior': True}
    assert result['population_and_concession_baseline']


def test_source_alignment_preserves_the_interpretation_and_unresolved_metaphor():
    alignment = source_alignment()
    assert alignment['unit'] == 'kant-1784:u0009'
    assert alignment['previous_dependence_is_an_explicit_reading']
    assert alignment['definitions'] == ['kl', 'km', 'kf']
    assert 'natural maturation mechanism' in alignment['remaining']
    assert 'personification and declaration metaphor' in alignment['remaining']


def test_transition_basis_written_forms_and_quotation_without_execution():
    for compose, counts in ((generic_composed, (0, 10)), (source_composed, (51, 68))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
    doc['statements'] = []
    quoted = parse(format_graph(doc, 'compact') + '\nq[e[r[p kf]][r[p kf]]].')
    def forbidden(*args):
        raise ValueError('Quoted transition executed a primitive')
    primitives = {d['name']: forbidden for d in quoted['declarations'] if d['kind'] == 'primitive'}
    assert evaluate_document(quoted, individuals=('reader',), situations=('text',), primitives=primitives) == [{'kind': 'ask', 'value': True}]
