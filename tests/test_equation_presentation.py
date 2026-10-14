from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_equation_presentation import REPORT,build_report,structural_checks
from scripts.compose_equation_presentation import ROOT,PARENT,CASES,source_composed


@pytest.fixture(scope='module')
def result():return build_report()


@pytest.fixture(scope='module')
def source():return parse(source_composed()[0])


def test_case_quantifiers_do_not_quantify_the_interpretation(result):
    structure=result['structure']
    assert structure['case_parameters']==len(CASES)==18
    assert structure['fixed_interpretations']==['assigned','electricassigned','frames']
    assert structure['fixed_light']
    assert structure['existential_derivative_table']
    assert structure['no_universal_claim_over_arbitrary_assignments']
    assert structure['conditional_case_scope']


@pytest.mark.parametrize('change',['universal_jet','wrong_witness','quantified_interpretation','unconditional'])
def test_meaning_changing_scope_mutations_are_rejected(source,change):
    doc=deepcopy(source);defs={d['name']:d for d in doc['declarations']}
    if change=='universal_jet':defs['senw']['body']['kind']='forall'
    elif change=='wrong_witness':
        defs['senw']['body']['body']['arguments'][11]=defs['senw']['body']['body']['arguments'][0]
    elif change=='quantified_interpretation':
        defs['senx']['body']['body']['variable']=defs['senx']['parameters'][0]['name']
    else:
        body=defs['senx']['body']['body']
        for _ in CASES:body=body['body']
        body['kind']='and'
    with pytest.raises(ValueError):structural_checks(doc)


def test_presentation_explanation_order_and_truth_are_separate(result):
    cases=result['generic']['cases'];assert len(cases)==16
    for row in cases:
        assert row['results']==[row['present'] and row['explain'] and row['order'],False,row['truth'],row['truth']]
    assert any(row['results'][0] and not row['truth'] for row in cases)
    assert result['generic']['same_node_rejected']
    assert result['generic']['coextensive_descriptions_not_substituted']


def test_source_author_scope_order_and_fixed_relation_descriptions_are_preserved(result):
    cases=result['source']['cases'];assert len(cases)==12
    for label,row in cases.items():assert row==[label=='baseline',False,False,False,False]
    assert result['source']['quoted_quantity_electric_and_frame_relations_distinguished']
    assert result['source']['content_and_physical_relations_not_executed']
    assert result['source']['unknown_discourse_relations_refused']


def test_full_real_content_is_not_certified_by_finite_enumeration(result):
    assert result['unbounded']['rejected']
    assert result['unbounded']['finite_samples_not_a_universal_proof']
    assert 'rational number domain' in result['unbounded']['reason']


def test_existing_author_statements_and_source_formula_are_retained(result,source):
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+11
    assert source['statements'][:-1]==parent['statements']
    assert len(source['statements'])==175
    assert result['new_definitions']==3 and result['new_primitives']==8 and result['new_author_statements']==1
    first,second=result['alignment']['segments']
    assert (first['unit'],first['text'],first['status'])==('einstein-1905:u0235','wobei','explicit_interpretive_annotation')
    assert (second['unit'],second['math_id'])==('einstein-1905:u0236','M0390')
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
