from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_polygon_clock import (
    alignment, attribution_checks, fold_checks, infinite_checks,
    observed_totals_checks, physical_checks, polynomial_checks,
)
from scripts.compose_polygon_clock import ROOT, composed


def test_polygon_connections_and_sampled_geometry_are_not_just_endpoint_sums():
    result=physical_checks();rows=result['cases']
    assert len(rows)==28
    for name in ('baseline','triangle','diagonal','negative_times','common_dial_offset'):
        assert rows[name]==[True]*5
    assert rows['open_bend']==[True,True,True,True,False]
    for name in ('detour','uneven_progress','disconnected_equal_record','reordered','duplicate_leg'):
        assert rows[name]==[False,True,True,True,True]
    assert rows['reset_corner']==[True,True,False,True,True]
    assert rows['reset_last']==[True,True,False,False,True]
    assert rows['missing_midpoint']==[True]*5
    assert result['endpoint_conditions_do_not_establish_complete_trajectory']


def test_numeric_folds_keep_negative_terms_empty_values_and_arbitrary_lengths():
    rows=fold_checks()
    assert [r['length'] for r in rows]==[0,1,2,5,16,24]
    assert rows[0]['sum']=='0' and rows[1]['sum']=='-3/7'
    assert all(r['accepted']==[True,True] for r in rows)


def test_observed_totals_do_not_hide_a_corner_reset_or_duplicate_leg():
    result=observed_totals_checks();rows=result['cases']
    assert rows['baseline']['duration']=='10' and rows['baseline']['elapsed']=='8'
    assert rows['triangle']['duration']=='4' and rows['triangle']['elapsed']=='16/5'
    assert rows['reset_corner']==rows['baseline']
    assert rows['duplicate_leg']['duration']=='15' and rows['duplicate_leg']['elapsed']=='12'
    assert result['totals_alone_do_not_prove_path_or_interval_laws']


def test_telescoping_and_common_rate_have_distinct_premises():
    rows=polynomial_checks()
    assert len(rows)==6
    assert {n for n,r in rows.items() if r['status']=='invalid'}=={
        'different_rates_cannot_use_first_rate_for_total','same_position_does_not_imply_same_time'}


def test_full_time_and_full_sequence_domains_cannot_be_finitely_sampled():
    rows=infinite_checks()
    assert 'rational number domain' in rows['all_times']
    assert 'unbounded sequence domain' in rows['all_finite_paths']


def test_result_immediacy_and_return_are_distinct_attributions():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']==[True]*3
    assert rows['wrong_author']==rows['wrong_scope']==rows['wrong_context']==[False]*3
    assert rows['wrong_result']==[False,True,True]
    assert rows['wrong_clear']==[True,False,True]
    assert rows['wrong_return']==[True,True,False]


def test_polygon_unit_is_partial_and_keeps_common_speed_reading_explicit():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={'einstein-1905:u0127'}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M0233','M0234','M0235','M0236'}
    assert result['common_speed_inherited_from_previous_result']
    assert result['acceleration_response_not_derived']
    assert result['verified_full_units']==0 and not result['facsimile_checked']


def test_basis_and_script_roundtrip_preserve_all_parent_statements():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(435,627)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-clock-transfer.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-3]==parent['statements'] and len(doc['statements'])==121
