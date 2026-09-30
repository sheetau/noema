import pytest

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_law_invariance import (
    alignment, attribution_checks, coordinate_examples, frame_checks,
    full_principle_checks, representation_checks, source_checks,
)
from scripts.compose_law_invariance import ROOT, generic_composed, source_composed


def test_every_corresponding_representation_preserves_admissibility():
    rows=representation_checks()
    assert len(rows)==256
    assert all(not row['preserved'] for row in rows if not any(row['available'][:2]) or not any(row['available'][2:]))
    inconsistent=next(row for row in rows if row['available']==[True]*4 and row['admissible']==[True,False,True,True])
    assert not inconsistent['preserved']
    rejected=next(row for row in rows if row['available']==[True]*4 and row['admissible']==[False]*4)
    assert rejected['preserved']


def test_coordinate_values_and_rest_can_change_while_a_condition_is_preserved():
    result=coordinate_examples()
    assert len(result['cases'])==243
    assert all(row['preserved'] for row in result['cases'])
    assert any(row['positions']!=row['transformed'] for row in result['cases'])
    assert not result['coordinate_rest_preserved']


def test_frame_scope_rejects_rotation_acceleration_and_missing_frames():
    rows=frame_checks()
    assert len(rows)==7
    assert [name for name,accepted in rows.items() if accepted]==['baseline']


def test_all_laws_and_histories_are_compared_without_filtering_invalid_candidates():
    rows=source_checks()
    assert len(rows)==16
    assert [name for name,accepted in rows.items() if accepted]==[
        'baseline','one_law_allows_and_another_rejects_all_candidates']
    assert not rows['unobserved_candidate_disagrees']
    assert not rows['different_history_cannot_fill_missing_representation']


def test_complete_principle_checks_both_frame_directions_on_its_explicit_model():
    result=full_principle_checks()
    assert len(result['cases'])==4
    assert [name for name,accepted in result['cases'].items() if accepted]==['baseline']
    assert result['individual_domain_size']==7
    assert not result['arbitrary_physical_systems_verified']


def test_defining_a_principle_does_not_execute_its_physical_contents():
    rows=attribution_checks()
    assert len(rows)==6
    assert [name for name,accepted in rows.items() if accepted]==['baseline']


def test_alignment_does_not_certify_the_full_meaning_of_relativity():
    report=alignment()
    assert report['verified_full_units']==0
    row,=report['segments']
    assert row['unit']=='einstein-1905:u0025'
    assert not row['full_semantic_equivalence']


@pytest.mark.parametrize('compose,counts',[(generic_composed,(0,3)),(source_composed,(65,46))])
def test_meaning_basis_and_notations_preserve_the_prior_source(compose,counts):
    text,basis=compose()
    doc=parse(text)
    audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-roundtrip-speed.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-1]==previous['statements']
        assert len(doc['statements'])==4
