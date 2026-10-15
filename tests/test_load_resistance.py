from fractions import Fraction as F
from itertools import product
import json
import pytest
from noema.extraction import _references
from scripts.check_load_resistance import values,source_values,attribution,review_report,document
from scripts.compose_load_resistance import ROOT,PARENT,SOURCE,BASIS,READING,REVIEW,build,basis,reading,review,manuscript


@pytest.mark.parametrize('load,deformation',list(product((0,9,10,11),(F(-1,10),0,F(1,10),F(1,5)))))
def test_nonzero_loading_and_small_nonnegative_response(load,deformation):
    assert values(loads=(load,load),deformations=(deformation,deformation))==[load>=10 and 0<=deformation<=F(1,10)]


@pytest.mark.parametrize('variant',('empty','omitted','duplicate','unassessed','wrong_object','wrong_protocol',
    'wrong_loadunit','wrong_deformationunit','wrong_context'))
def test_complete_protocol_qualified_evidence_is_required(variant):
    assert values(variant=variant)==[False]


@pytest.mark.parametrize('minimum,maximum',[(0,F(1,10)),(-1,F(1,10)),(10,F(-1,10))])
def test_invalid_benchmarks_do_not_turn_no_load_into_hardness(minimum,maximum):
    assert values(minimum=minimum,maximum=maximum)==[False]


def test_zero_deformation_is_allowed_without_dividing_by_it():
    assert values(deformations=(0,0),maximum=0)==[True]
    assert values(deformations=(0,0),loads=(0,0),maximum=0)==[False]


@pytest.mark.parametrize('force_scale,deformation_scale',[(1,1000),(F(1,1000),1),(2,F(1,7))])
def test_positive_rescaling_of_each_reading_and_its_bound_preserves_result(force_scale,deformation_scale):
    assert values(force_scale=force_scale,deformation_scale=deformation_scale)==[True]
    assert values(deformations=(F(1,20),F(1,5)),force_scale=force_scale,deformation_scale=deformation_scale)==[False]


@pytest.mark.parametrize('variant',('unknown_assessment','unknown_load','unknown_deformation'))
def test_unknown_measurements_are_not_guessed(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant)


def test_cached_and_uncached_interpretations_agree():
    assert values(memoize=False)==values()==[True]


def test_one_failed_interior_stage_breaks_resistance_but_not_quoted_attribution():
    assert source_values()==[True]*3
    assert source_values('middle_failure')==[True,False,True]


def test_legacy_hardness_flag_does_not_control_new_explanation():
    assert source_values('legacy_false')==[False,True,True]


@pytest.mark.parametrize('variant',('empty','omitted','duplicate','unassessed','wrong_object','wrong_protocol','wrong_loadunit','wrong_deformationunit','wrong_context'))
def test_actual_cover_uses_the_same_checked_measurement_inputs(variant):
    assert source_values(variant)==[True,False,True]


def test_reference_and_fixed_discourse_benchmark_are_preserved():
    assert source_values('split_cover')==[False,False,True]
    calls=[];assert source_values(calls=calls)==[True]*3
    assert {row[-1] for row in calls}=={'start','middle','end'}
    assert all(row[0]=='cover' and row[2:5]==('protocol','forceunit','lengthunit') for row in calls)


def test_family_quotes_the_new_depiction_without_executing_measurements():
    assert source_values('old_depiction',indices=(2,))==[False]
    assert source_values('unknown_load',indices=(2,))==[True]
    assert attribution()==[True] and attribution(True)==[False]


def test_updated_manuscript_connects_explanation_and_preserves_history():
    old,new=document(PARENT),document(SOURCE);_,mapping=manuscript()
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert len(new['statements'])==22
    assert _references(new['statements'][-1])=={mapping['iaziayattribution']}
    packet=review_report();rows={r['id']:r for r in packet['obligations']}
    assert rows['hard_cover']['unconnected_candidate_roots']==[]
    assert packet['templates'][0]['symbol']==mapping['iaziayschema']
    assert len(packet['templates'][0]['parameters'])==8
    assert not packet['semantic_completion'] and not packet['counts_as_translated_coverage']


def test_reproducible_text_and_open_reading():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    for path,value in ((BASIS,basis()),(READING,reading()),(REVIEW,review(files))):
        assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
