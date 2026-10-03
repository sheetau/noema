import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_coordinate_frames import alignment, attribution_checks, direction_checks, polynomial_checks, source_checks
from scripts.compose_coordinate_frames import ROOT, generic_composed, source_composed


def test_zero_vectors_are_not_axes_and_antiparallel_directions_can_be_parallel():
    rows=direction_checks()
    assert len(rows)==11
    assert rows['orthogonal_oblique_axes']==[True,False]
    assert rows['opposite_direction']==rows['fractional_parallel']==[False,True]
    assert rows['zero_first']==rows['zero_second']==rows['both_zero']==[False,False]


def test_direction_symmetries_do_not_collapse_parallel_vectors_to_identical_values():
    rows=polynomial_checks()
    assert len(rows)==5 and sum(r['status']=='valid' for r in rows.values())==4
    assert rows['parallel_directions_must_have_identical_components']['status']=='invalid'


def test_axis_configuration_is_stronger_than_constant_relative_orientation():
    result=source_checks();rows=result['cases']
    assert len(rows)==28 and rows['baseline']==rows['antiparallel_y']==[True]*5
    for name in ('fixed_rotated_axes','parallel_but_offset_x','nonorthogonal_triad','wrong_axis_role'):
        assert rows[name]==[False,True,False,False,True]
    assert rows['second_frame_already_moving']==[True,True,False,True,True]
    assert rows['zero_relative_speed']==[True,True,True,False,False]
    assert result['distinct_origins_and_distinct_axis_objects_accepted']
    assert result['initial_rest_and_nonzero_motion_use_different_contexts']
    assert not result['full_real_geometry_evaluated']


def test_instrument_agreement_covers_all_clocks_and_keeps_individuals_distinct():
    result=source_checks();rows=result['cases']
    for name in ('one_clock_different','only_some_clocks_match','same_ruler_instance','no_second_clocks'):
        assert rows[name]==[True,False,False,True,True]
    assert rows['outside_clock_different']==[True]*5
    assert not result['clock_reading_primitive_executed']


def test_adopted_initial_setup_is_not_evaluated_as_actual_physics():
    rows=attribution_checks()
    assert len(rows)==5 and {k for k,v in rows.items() if v}=={'baseline'}


def test_source_alignment_stops_before_the_later_motion_and_measurement():
    result=alignment();rows=result['segments']
    assert len(rows)==4 and {r['unit'] for r in rows}=={'einstein-1905:u0043'}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M0063','M0064','M0065'}
    assert not result['facsimile_checked'] and result['verified_full_units']==0
    assert all(not r['full_semantic_equivalence'] for r in rows)


def test_only_inherited_comparison_is_refined_and_its_previous_condition_is_retained():
    old=parse((ROOT/'examples/v014/einstein-relative-simultaneity.noema').read_text(encoding='utf-8'))
    new=parse(source_composed()[0])
    before={d['name']:d for d in old['declarations']};after={d['name']:d for d in new['declarations']}
    assert {name for name,d in before.items() if after[name]!=d}=={'sel'}
    assert after['sel']['body']['kind']=='and'
    assert after['sel']['body']['arguments'][0]==before['sel']['body']
    assert after['sel']['body']['arguments'][1]['symbol']=='sfc'
    assert new['statements'][:-1]==old['statements'] and len(new['statements'])==26


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,8)),(source_composed,(218,157))])
def test_basis_notation_and_glyph_roundtrips(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
