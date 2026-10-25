from copy import deepcopy
import json
import pytest

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.shared_modality import (ROOT,LIBRARY,ABILITY_SOURCE,MODAL_SOURCE,ABILITY_NAMES,MODAL_NAMES,
                                    composed,renamed,inventory)
from scripts.check_shared_modality import finite_checks,contexts,source_mapping,interpret,harness,binding_diagnostics


def test_common_definition_is_used_in_both_selected_manuscripts_and_collisions_are_kept():
    evidence=source_mapping()
    assert set(evidence['source_uses'])=={'kant-1784','einstein-1905'}
    assert all(v['statement_indices'] for v in evidence['source_uses'].values())
    assert {r['symbol'] for r in evidence['intersection'] if r['decision']=='keep_distinct_meanings'}=={'zac','zai'}


def test_existing_definitions_are_exactly_preserved_under_symbol_renaming():
    shared={d['name']:d for d in composed()['declarations']}
    for path,mapping in ((ABILITY_SOURCE,ABILITY_NAMES),(MODAL_SOURCE,MODAL_NAMES)):
        source=parse((ROOT/path).read_text(encoding='utf-8'))
        for old in source['declarations']:
            if old['name'] in mapping:
                actual=shared[mapping[old['name']]]
                assert renamed(actual,{v:k for k,v in mapping.items()})==old
    assert all(d['kind']=='definition' for d in shared.values())


def test_native_source_and_public_contracts_are_complete():
    source=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    assert source==composed()==parse(format_graph(source))
    basis=json.loads((ROOT/'data/shared-modality-basis-v1.json').read_text(encoding='utf-8'))
    assert set(basis['definitions'])==set(basis['public_contracts'])=={d['name'] for d in source['declarations']}
    for d in source['declarations']:
        contract=basis['public_contracts'][d['name']]
        assert [r['sort'] for r in contract['arguments']]==[p['sort'] for p in d['parameters']]
        assert len({r['role'] for r in contract['arguments']})==len(d['parameters'])


def test_finite_candidate_and_ability_models_match_independent_set_conditions():
    evidence=finite_checks()
    assert len(evidence['candidate_models'])==32
    assert evidence['ability_models']==128


def test_empty_candidates_are_not_vacuous_necessity_or_exclusion():
    result=interpret(candidate=set(),success={'left'},actual=True)
    assert result['candidateempty']
    assert not any(result[n] for n in ('candidatepossible','candidatenecessary','candidateexcluded','candidatecontingent','necessaryactual'))
    with pytest.raises(ValueError,match='Missing'): interpret(candidate=None,success={'left'})


def test_necessity_does_not_assert_actual_truth():
    a=interpret(candidate={'left'},success={'left'},actual=False)
    b=interpret(candidate={'left'},success={'left'},actual=True)
    assert a['candidatenecessary'] and b['candidatenecessary']
    assert not a['necessaryactual'] and b['necessaryactual']


def test_two_topics_distinguish_possible_guaranteed_and_assessed_ability():
    rows={r['name']:r for r in contexts()}
    assert {r['topic'] for r in rows.values()}=={'移動','装置操作'}
    a=rows['travel_without_an_available_route']
    assert a['candidates']['candidatepossible'] and not a['ability']['methodpossible']
    b=rows['travel_possible_but_not_guaranteed']['ability']
    assert b['methodpossible'] and not b['methodguaranteed']
    missing=rows['device_missing_assessment']['ability']
    failure=rows['device_failure_in_assessed_results']['ability']
    assert not missing['assessedability'] and not missing['assessedinability'] and not missing['assessmentdecisive']
    assert failure['assessedinability'] and failure['assessmentdecisive']
    assert rows['device_alternative_method']['ability']['methodguaranteed']


def test_same_truth_with_different_candidate_channels_is_not_same_modality():
    physical=interpret(candidate={'left','right'},success={'left'})
    normative=interpret(candidate={'right'},success={'left'})
    assert physical['candidatepossible'] and normative['candidateexcluded']
    # Neither result supplies the missing interpretation of permission.
    assert 'permission' not in physical and 'permission' not in normative


def test_foreign_selected_result_is_not_valid_assessment():
    result=interpret(candidate={'left'},success={'left','right'},available={'plan'},
                     outcomes={'plan':{'left'}},selected={'plan':{'right'}},ability=True)
    assert result['methodguaranteed']
    assert not result['methodsassessable'] and not result['assessedability'] and not result['assessedinability']


def test_method_witness_cannot_change_between_success_and_outcome_conditions():
    result=interpret(candidate={'left','right'},success={'left'},available={'plan'},
        outcomes={'plan':{'right'},'backup':{'left'}},selected={'plan':{'right'},'backup':{'left'}},ability=True)
    assert not result['methodpossible'] and result['assessedinability']


def test_symbol_renaming_preserves_binders_and_quote_references():
    node=dict(kind='lambda',parameters=[dict(name='s5k',sort='individual')],body={
        'kind':'quote','body':dict(kind='function_ref',symbol='s5k')})
    result=renamed(node,{'s5k':'candidatenecessary'})
    assert result['parameters'][0]['name']=='s5k'
    assert result['body']['body']['symbol']=='candidatenecessary'


def test_every_candidate_and_method_outcome_slot_has_a_distinguishing_case():
    rows=binding_diagnostics()
    assert len(rows)==9
    assert sum(r['value'] for r in rows)==2
