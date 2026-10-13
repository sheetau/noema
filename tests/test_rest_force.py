from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_rest_force import rest_regression, generic_checks, charge_checks, premise_checks, force_checks, attribution_checks, alignment
from scripts.compose_rest_force import ROOT, PARENT, composed, generic_composed, replace_symbol


def test_canonical_rest_and_motion_are_not_reinterpreted_by_the_fixture():
    result=rest_regression();rows=result['cases'];assert len(rows)==8
    assert rows['historical:rest=True:motion=False']==[False]
    assert rows['corrected:rest=True:motion=False']==[True]
    assert rows['historical:rest=False:motion=True']==[True]
    assert rows['corrected:rest=False:motion=True']==[False]
    assert '動いている' in result['canonical_contracts']['xm']
    assert '静止している' in result['canonical_contracts']['x4']


def test_pointwise_comparison_uses_time_and_only_selected_valid_components():
    rows=generic_checks()['cases'];assert len(rows)==8
    assert rows['baseline']==rows['different_function_same_values']==[True]
    assert all(value==[False] for name,value in rows.items() if name not in ('baseline','different_function_same_values'))


def test_unit_charge_requires_a_record_in_the_same_moving_frame():
    result=charge_checks();rows=result['cases'];assert len(rows)==9
    assert all(value==[name=='baseline'] for name,value in rows.items())
    assert result['invariance_not_derived_from_principle_alone']


def test_rest_conditionals_and_frame_local_force_roles_are_preserved():
    result=force_checks();rows=result['cases'];assert len(rows)==33
    for name in ('baseline','inactive_new_field','inactive_old_field','neither_rest_missing_fields','instantaneous_new_rest_without_interval_rest'):
        assert rows[name]==[True,True]
    for name in ('body','event','frame','context','unit','kind','record','point_time','outside','field_assignment','x','y','z'):
        assert rows['old_'+name]==[False,True]
        assert rows['new_'+name]==[True,False]
    assert result['different_frames_have_different_vector_values']
    assert result['force_event_not_identified_with_calibration_event']
    assert result['instantaneous_rest_does_not_require_interval_rest']


def test_calibration_and_relativity_are_separate_inference_premises():
    rows=premise_checks();assert len(rows)==4
    assert all(r['result']==[r['calibration'] and r['principle']] for r in rows)


def test_charge_inference_and_two_force_claims_keep_their_quoted_contents():
    result=attribution_checks();rows=result['cases'];assert len(rows)==8
    assert rows['none']==[True,True,True]
    assert rows['premise']==rows['charge']==[False,True,True]
    assert rows['old']==[True,False,True] and rows['new']==[True,True,False]
    assert rows['author']==rows['scope']==rows['context']==[False,False,False]
    assert result['quoted_contents_not_executed']


def test_corrected_range_and_new_force_ranges_are_still_partial():
    result=alignment();assert len(result['segments'])==5
    assert result['segments'][0]['correction']=='xm motion replaced by x4 rest'
    assert result['segments'][1]['source'].startswith('Nach dem Relativitätsprinzip')
    assert [s['math_id'] for s in result['segments'][2:]]==['M0315','M0316','M0317']
    assert result['verified_full_units']==0


def test_parent_changes_only_the_documented_rest_reference_and_preserves_roundtrips():
    for builder in (generic_composed,composed):
        text,basis=builder();doc=parse(text);audit_basis(doc,basis)
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['statements'][:-3]==parent['statements']
    changes=[(old,new) for old,new in zip(parent['declarations'],doc['declarations']) if old!=new]
    assert len(changes)==1
    old,new=changes[0];assert old['name']==new['name']=='sby2'
    assert replace_symbol(old,'xm','x4')==new
    byname={d['name']:d for d in doc['declarations']}
    assert all(d==byname[d['name']] for d in parse(generic_composed()[0])['declarations'])
