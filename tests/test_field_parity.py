from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_field_parity import polynomial_checks, signed_value_checks, source_checks, component_checks, attribution_checks, alignment
from scripts.compose_field_parity import ROOT, PARENT, generic_composed, composed


def test_nonzero_response_separates_sign_magnitude_and_even_factor():
    result=polynomial_checks();rows=result['claims'];assert len(rows)==7
    assert all(r['status']=='valid' for r in rows.values())
    assert result['physical_symmetry_not_proved']


def test_zero_or_unchanged_values_do_not_count_as_sign_reversal():
    result=signed_value_checks();rows=result['cases'];assert len(rows)==9
    assert rows['0,0']==rows['1,1']==rows['-1,-1']==rows['1,-2']==rows['0,1']==[False]
    assert rows['1,-1']==rows['-1,1']==rows['2,-2']==rows['-2,2']==[True]


def test_probe_keeps_all_five_zero_components_point_domain_and_context():
    result=source_checks();rows=result['cases'];assert len(rows)==17
    assert rows['baseline']==rows['negative_factor']==rows['negative_magnetic']==rows['negative_speed']==[True]*6
    assert rows['unequal_reciprocal']==[True,False,True,False,False,False]
    assert rows['opposite_factors']==[True,False,False,True,False,False]
    assert rows['zero_factors']==[True,False,False,True,False,True]
    for name in ('wrong_point','outside_region','wrong_context',*(f'nonzero_component_{i}' for i in range(5))):
        assert rows[name]==[False,True,True,True,False,True]
    assert rows['zero_speed']==rows['zero_magnetic']==[False,False,True,True,False,True]
    assert result['fields_are_not_required_to_be_constant_away_from_the_probe']
    assert result['negative_even_factor_not_excluded']


def test_reduced_formula_is_the_original_mixed_component_at_the_same_event():
    result=component_checks();assert len(result['cases'])==4
    assert all(value==[True,True] for value in result['cases'].values())
    assert result['same_old_event_compared_at_both_speeds']
    assert result['no_equal_numeric_new_coordinates_assumed']


def test_author_example_and_inference_do_not_execute_physical_claims():
    result=attribution_checks();rows=result['cases'];assert len(rows)==10
    assert all(value==[name.endswith(':baseline')] for name,value in rows.items())
    assert result['physical_claims_not_evaluated_during_attribution']


def test_footnote_link_and_ranges_exclude_the_unexplained_symmetry_reason():
    result=alignment();assert len(result['segments'])==5
    ranges=[r for r in result['segments'] if 'source' in r];assert len(ranges)==1
    assert 'Symmetriegründen' not in ranges[0]['source']
    assert result['reference_target']=='#cite_note-4'
    assert result['body_reference']=='einstein-1905:u0167'
    assert result['verified_full_units']==0


def test_generic_library_source_and_all_notations_preserve_prior_content():
    for builder,counts in ((generic_composed,(4,4,0)),(composed,(550,889,162))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements']
    byname={d['name']:d for d in doc['declarations']}
    assert all(d==byname[d['name']] for d in parse(generic_composed()[0])['declarations'])
