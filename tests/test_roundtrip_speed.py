import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_roundtrip_speed import (
    ARITHMETIC, alignment, attribution_checks, constancy_checks, numeric_checks,
    polynomial_checks, source_checks,
)
from scripts.compose_roundtrip_speed import ROOT, generic_composed, source_composed


def test_roundtrip_values_units_origins_and_degenerate_cases():
    rows=numeric_checks()
    assert len(rows)==17
    assert sum(rows.values())==6
    assert not rows['one_way_instead_of_roundtrip']
    assert not rows['zero_duration']


def test_rational_speed_is_unique_and_unit_changes_need_compensation():
    rows=polynomial_checks()
    assert len(rows)==9
    assert rows['scaling_time_and_speed_together_preserves_rate']['status']=='invalid'
    assert all(row['status']=='valid' for name,row in rows.items()
               if name!='scaling_time_and_speed_together_preserves_rate')


def test_universal_scope_requires_one_shared_value_not_one_value_per_trial():
    rows=constancy_checks()
    assert len(rows)==64
    split=next(row for row in rows if row['selected']==[True,True] and row['matches']==[True,False,False,True])
    assert split['common_candidates']==[False,False]
    assert all(row['common_candidates']==[False,False] for row in rows if row['selected']==[False,False])


def test_physical_trials_share_rate_but_do_not_require_synchronized_remote_clock():
    result=source_checks()
    assert len(result['cases'])==22
    assert [name for name,accepted in result['cases'].items() if accepted]==[
        'baseline','reflection_clock_offset_does_not_change_roundtrip_rate']
    assert not result['full_real_cut_law_evaluated']


def test_empirical_adoption_does_not_execute_or_prove_the_adopted_law():
    rows=attribution_checks()
    assert len(rows)==7
    assert [name for name,accepted in rows.items() if accepted]==['baseline']


def test_source_prose_and_formula_remain_partial():
    result=alignment()
    assert result['verified_full_units']==0
    assert [row['unit'] for row in result['segments']]==[f'einstein-1905:u{i:04d}' for i in (19,20,21)]
    assert result['segments'][1]['math_id']=='M0040'
    assert all(not row['full_semantic_equivalence'] for row in result['segments'])


def test_positive_cut_product_is_reused_and_never_finitely_sampled():
    doc=parse(generic_composed()[0])
    previous=parse((ROOT/'examples/v011/real-products.noema').read_text(encoding='utf-8'))
    product=next(d for d in doc['declarations'] if d['name']=='sah')
    old=next(d for d in previous['declarations'] if d['name']=='cc')
    assert product['parameters']==old['parameters'] and product['body']==old['body']
    query=parse(generic_composed()[0]+'q[k sai[k bb[n p g b] k bb[n p a b] k bb[n p e b] k bb[n p d b]]].')
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(query,individuals=('object',),situations=('text',),primitives=ARITHMETIC)


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,16)),(source_composed,(53,39))])
def test_meaning_basis_notation_and_prior_definitions_remain_intact(compose,counts):
    text,basis=compose()
    doc=parse(text)
    audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-event-time.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-1]==previous['statements']
        assert len(doc['statements'])==3
