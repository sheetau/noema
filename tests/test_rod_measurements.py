import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_rod_measurements import ARITHMETIC, alignment, attribution_checks, direct_checks, source_checks
from scripts.compose_rod_measurements import ROOT, generic_composed, source_composed


def test_direct_measurement_requires_the_same_roles_and_comoving_setting():
    rows=direct_checks()
    assert len(rows)==256 and sum(row['accepted'] for row in rows)==1
    assert next(row for row in rows if row['accepted'])['conditions']==[True]*8


def test_two_settings_keep_the_same_rod_and_ruler_without_equating_results():
    result=source_checks()
    rows=result['cases']
    assert len(rows)==27
    assert [name for name,values in rows.items() if all(values)]==[
        'different_values_in_distinct_settings','equal_values_are_not_forbidden','observer_may_move_in_method_b']
    assert rows['mix_measurement_contexts']==[False,False]
    assert rows['different_endpoint_times']==rows['equal_times_but_not_the_specified_time']==[True,False]
    assert rows['different_ruler']==[False,False]
    assert not result['full_real_cut_physics_evaluated']
    assert not result['lorentz_contraction_relation_derived']


def test_method_descriptions_do_not_execute_measurements_or_invent_results():
    rows=attribution_checks()
    assert len(rows)==6 and rows['baseline']==[True,True]
    assert rows['missing_first']==[False,True] and rows['missing_second']==[True,False]
    assert rows['swapped_methods']==rows['wrong_scope']==[False,False]


def test_two_partial_operations_and_specified_time_remain_unverified_as_full_units():
    result=alignment()
    assert result['verified_full_units']==0 and len(result['segments'])==3
    assert {r['unit'] for r in result['segments']}=={'einstein-1905:u0030','einstein-1905:u0031'}
    assert result['segments'][-1]['math_id']=='M0048'
    assert all(not row['full_semantic_equivalence'] for row in result['segments'])


def test_positive_real_length_does_not_use_finite_sampling():
    doc=parse(generic_composed()[0]+'q[k sbg[k bb[n p f b]]].')
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('object',),situations=('text',),primitives=ARITHMETIC,memoize_expressions=True)


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,22)),(source_composed,(116,60))])
def test_basis_and_notations_preserve_the_existing_source(compose,counts):
    text,basis=compose()
    doc=parse(text)
    audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-emitted-light.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-2]==previous['statements']
        assert len(doc['statements'])==8
