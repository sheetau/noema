import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_velocity_components import alignment, attribution_checks, equation_checks, graph_checks, polynomial_checks
from scripts.compose_velocity_components import ROOT, composed


@pytest.fixture(scope='module')
def equations():
    return equation_checks()['cases']


@pytest.fixture(scope='module')
def graphs():
    return graph_checks()['cases']


def test_substitution_and_signed_domain_have_algebraic_evidence():
    result=polynomial_checks()
    claims=result['claims']
    assert len(claims)==7
    assert claims['coordinate_substitution_preserves_both_motion_equations']['status']=='valid'
    assert claims['nonzero_time_determines_both_components']['status']=='valid'
    assert claims['ordinary_vector_addition_is_exact']['status']=='invalid'
    assert claims['transverse_component_is_unchanged']['status']=='invalid'
    assert not result['real_cut_field_laws_proved']


def test_velocity_signs_and_zero_denominator_are_retained(equations):
    for name in ('baseline','stationary','negative_frame_velocity','negative_transverse','negative_denominator','origin_is_not_enough_to_identify_velocity'):
        assert equations[name]['accepted']==[True]
    for name in ('zero_denominator_at_origin','ordinary_addition','unchanged_transverse','nonplanar','wrong_beta_branch','invalid_component','different_time'):
        assert equations[name]['accepted']==[False]


def test_same_constants_apply_at_every_event(graphs):
    assert graphs['baseline']==graphs['negative_transverse']==[True]*4
    assert graphs['wrong_fixed_component']==[False,True,False,False]
    assert graphs['changed_later_motion']==[False,False,False,True]
    assert graphs['wrong_frame_motion']==graphs['wrong_axis']==[False,True,False,True]


def test_same_point_event_frame_and_all_records_matter(graphs):
    for name in ('empty_history','wrong_point','wrong_setting'):
        assert graphs[name]==[False]*4
    assert graphs['missing_moving_record']==[False,False,False,True]
    assert graphs['missing_rest_record']==[True,False,False,False]
    assert graphs['extra_bad_record']==[True,False,False,False]
    assert graphs['different_event_pair']==[True,False,False,True]


def test_attribution_does_not_evaluate_or_endorse_quoted_equations():
    result=attribution_checks();rows=result['cases']
    assert len(rows)==7 and rows['baseline']==[True,True]
    assert rows['wrong_setup']==[False,True]
    assert rows['wrong_premise']==rows['wrong_result']==[True,False]
    assert result['quoted_physics_is_not_executed_or_endorsed']


def test_source_question_is_not_counted_as_written():
    result=alignment();rows=result['segments']
    unit=[r for r in rows if r['unit']=='einstein-1905:u0133']
    assert unit[0]['source'].startswith('Führt man') and unit[0]['start']>0
    assert {r['math_id'] for r in rows if 'math_id' in r}=={f'M{i:04}' for i in range(242,252)}-{'M0249'}
    assert result['task_question_unwritten'] and result['verified_full_units']==0
    assert not result['facsimile_checked']


def test_existing_language_and_parent_are_preserved():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(466,662)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-earth-clocks.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements'] and len(doc['statements'])==128
