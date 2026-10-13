import pytest
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_earth_clocks import alignment, attribution_checks, checks
from scripts.compose_earth_clocks import ROOT, composed


@pytest.fixture(scope='module')
def comparison():
    return checks()


def test_balance_mechanism_requires_parts_and_regulating_use(comparison):
    rows=comparison['cases']
    assert len(rows)==25 and rows['baseline']==[True]*6
    for label in ('missing_spring','not_regulating_clock','pendulum_instead'):
        assert rows[label]==[False,True,True,True,False,True]


def test_identical_design_and_other_conditions_are_not_interchangeable(comparison):
    rows=comparison['cases']
    assert rows['different_structure']==[True,True,True,True,False,True]
    for label in ('different_conditions','empty_condition_scope','incomplete_conditions'):
        assert rows[label]==[True,False,True,True,False,True]
    assert rows['both_absent_condition']==[True]*6
    assert comparison['condition_scope_completeness_is_an_explicit_oracle']


def test_equator_and_both_poles_are_geometric_conditions(comparison):
    rows=comparison['cases']
    assert rows['south_pole']==[True]*6
    for label in ('not_surface','off_equator','negative_radius'):
        assert rows[label]==[True,True,False,True,False,True]
    for label in ('off_pole','at_center'):
        assert rows[label]==[True,True,True,False,False,True]
    assert not rows['not_fixed_to_body'][4] and not rows['wrong_rotation_axis'][4]


def test_small_slowing_requires_direction_degree_interval_and_unit(comparison):
    rows=comparison['cases']
    for label in ('equal_rates','reversed_rates','large_gap','zero_rate','degree_standard_rejects','wrong_rate_unit','wrong_rate_interval'):
        assert rows[label]==[True,True,True,True,True,False]
    assert rows['same_clock']==[True,True,True,True,False,False]
    assert comparison['source_has_no_numeric_threshold']
    assert comparison['mean_rates_not_absolute_dial_values']


def test_earth_conclusion_refers_to_prior_closed_curve_claim_without_executing_it():
    result=attribution_checks();rows=result['cases']
    assert len(rows)==6 and rows['baseline']==[True]
    assert all(row==[False] for name,row in rows.items() if name!='baseline')
    assert result['quoted_physical_claim_is_not_executed_or_endorsed']


def test_source_range_is_only_earth_sentence_and_still_partial():
    result=alignment();rows=result['segments']
    assert len(rows)==1 and rows[0]['unit']=='einstein-1905:u0128'
    assert rows[0]['source'].startswith('Man schließt daraus')
    assert all(word in rows[0]['source'] for word in ('Unruhuhr','genau gleich beschaffene','sonst gleichen Bedingungen','sehr kleinen','Erdpole'))
    assert result['verified_full_units']==0 and not result['facsimile_checked']


def test_basis_roundtrip_and_frozen_parent():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(458,650)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-curved-clock.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements'] and len(doc['statements'])==126
