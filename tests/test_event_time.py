import pytest

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_event_time import alignment, attribution_checks, binding_checks, equality_checks
from scripts.compose_event_time import ROOT, generic_composed, source_composed


@pytest.mark.parametrize('source', [False, True])
def test_event_and_reception_use_their_own_local_reading_and_one_reference(source):
    result = binding_checks(source)
    assert len(result['cases']) == 20
    assert [name for name, accepted in result['cases'].items() if accepted] == ['local_event', 'local_reception']
    assert not result['cases']['remote_reception_is_not_source_time']
    assert not result['cases']['different_reference']
    assert not result['full_real_cut_synchrony_evaluated']


def test_equal_values_require_two_way_inclusion_and_a_common_origin_shift():
    pytest.importorskip('z3')
    rows = equality_checks()
    assert len(rows) == 4
    assert rows['one_way_inclusion_does_not_imply_equality']['status'] == 'invalid'
    assert all(row['status'] == 'valid' for name, row in rows.items()
               if name != 'one_way_inclusion_does_not_imply_equality')


def test_adopting_a_timestamp_rule_does_not_evaluate_the_physical_content():
    rows = attribution_checks()
    assert len(rows) == 6
    assert [name for name, accepted in rows.items() if accepted] == ['baseline']


def test_event_time_source_alignment_does_not_certify_the_whole_paragraph():
    report = alignment()
    assert report['verified_full_units'] == 0
    row, = report['segments']
    assert row['unit'] == 'einstein-1905:u0018'
    assert row['start'] > 0 and not row['full_semantic_equivalence']


@pytest.mark.parametrize('compose, counts', [(generic_composed, (0, 3)), (source_composed, (38, 31))])
def test_event_time_basis_and_notations_preserve_the_source_protocol(compose, counts):
    text, basis = compose()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == counts
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    for notation in ('compact', 'full'):
        form = format_graph(doc, notation)
        assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
    if compose == source_composed:
        previous = parse((ROOT / 'examples/v014/einstein-synchrony-network.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])] == previous['declarations']
        assert doc['statements'][:-1] == previous['statements']
        assert len(doc['statements']) == 2
        declarations = {d['name']:d for d in doc['declarations']}
        assert declarations['qu']['body']['kind'] == 'and'
        assert set(audit['definition_dependencies']['definition_primitive_dependencies']['qw']) >= {'ca','cb','ce','ra','rb','rc'}
