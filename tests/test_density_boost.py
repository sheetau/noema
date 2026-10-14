from fractions import Fraction as F
import json

import pytest

from noema.grammar import parse
from scripts.check_density_boost import REPORT,build_report,setup_document,model_for,evaluate,SYMBOLS
from scripts.check_rod_setup import callbacks
from scripts.compose_density_boost import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_current_and_velocity_transformations_have_distinct_invariants(result):
    rows=result['polynomial']['claims']
    assert len(rows)==9
    rejected={'zero_density_factorization_determines_velocity','current_transform_requires_single_velocity','density_is_always_invariant'}
    assert {n for n,row in rows.items() if row['status']=='invalid'}==rejected
    assert all(row['status']=='valid' for n,row in rows.items() if n not in rejected)


def test_density_follows_divergence_without_assuming_zero_magnetic_divergence(result):
    assert len(result['residuals']['identities'])==8
    assert all(row['status']=='valid' for row in result['residuals']['identities'].values())
    rows=result['binding']['cases']
    assert len(rows)==36
    for row in rows:
        assert row['results'][:6]==[True]*6
        assert row['results'][6]==(row['zero_magnetic_divergence'] or row['speed']=='0')
        assert row['results'][7]==row['zero_magnetic_divergence']
        assert row['results'][8:]==[True,False]


def test_zero_density_is_not_a_zero_denominator(result):
    rows=[row for row in result['binding']['cases'] if row['density']=='0']
    assert rows and all(row['results'][0] and row['newdensity']=='0' for row in rows)
    assert any(any(F(x)!=0 for x in row['newvelocity']) for row in rows)
    singular=result['binding']['edge_cases']['zero_denominator']
    assert singular[:4]==[False,True,False,False]
    assert not any(singular[4:9])


def test_formal_superluminal_input_is_not_silently_given_causal_sign_guarantees(result):
    row=result['binding']['edge_cases']['negative_denominator']
    assert row['results'][:9]==[True]*9
    assert F(row['newdensity'])<0


def test_zero_density_nonzero_current_is_a_valid_independent_current_input():
    doc=setup_document((ROOT/'examples/v014/density-boost-core.noema').read_text(encoding='utf-8'))
    model,_=model_for(doc,density=F(0))
    for name,value in zip(('jx','jy','jz','kx','ky','kz'),(F(1),F(0),F(0),F(5,4),F(0),F(0))):
        model[SYMBOLS[name]]=lambda value=value:model['bb'](value)
    callbacks(doc,model,{SYMBOLS['newdensityfield']:lambda *xs:model['bb'](F(-3,20))})
    assert evaluate(doc,model,range(4))==[False,True,False,False]


def test_each_side_keeps_its_field_partial_frame_point_and_quantity(result):
    rows=result['binding']['contrasts']
    assert all(not row[8] for row in rows.values())
    assert all(f'{prefix}_jet_{field}_{i}_{j}' in rows for prefix in ('old','new') for field in ('E','H') for i in range(3) for j in range(4))
    assert rows['old_missing_magnetic_diagonal'][:6]==[True]*6
    assert rows['new_missing_magnetic_diagonal'][:6]==[True]*6
    assert all(row==[True,False,False,False] for row in result['binding']['current_contrasts'].values())


def test_reference_evidence_preserves_printed_velocity_and_density_factors(result):
    review=result['facsimile']
    assert review['reviewed_math_ids']==['M0390']
    assert review['images'][0]['printed_page']==916
    assert not review['snapshot_modified'] and not review['whole_page_semantics_verified']
    assert result['residuals']['zero_magnetic_divergence_is_an_extra_condition']
    assert not result['residuals']['full_real_derivative_chain_rule_proved']
    assert not result['binding']['full_real_field_transformation_proved']
    assert result['binding']['unknown_inputs_refused'] and result['binding']['standalone_agrees']


def test_append_only_source_and_roundtrip_do_not_promote_semantic_completion(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+13
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['roundtrips'] and not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
