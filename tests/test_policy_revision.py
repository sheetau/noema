from itertools import product
import json
import pytest
from noema.extraction import _references
from scripts.check_policy_revision import values,source_values,source_fixture,integration_checks,attribution,review_report,document
from scripts.compose_policy_revision import ROOT,PARENT,SOURCE,CORE,BASIS,REVIEW,build,basis,review,manuscript


@pytest.mark.parametrize('old,new',list(product(range(4),repeat=2)))
def test_all_normative_states_partition_revision_into_three_exclusive_forms(old,new):
    replacement,change,addition,retirement,fulfilled=values(old,new)
    assert replacement==(old==1 and new==2)
    assert addition==(old==3 and new==2)
    assert retirement==(old==1 and new==3)
    assert change==(bool(old&1) and bool(new&2) and not (bool(old&2) and bool(new&1)))
    assert sum((replacement,addition,retirement))==int(change)
    assert not fulfilled


@pytest.mark.parametrize('old,new',[(1,2),(3,2),(1,3)])
@pytest.mark.parametrize('variant',('other_source','other_actor','other_office','wrong_bindings','negative_polarity',
    'same_context','equivalent','empty_probes'))
def test_changes_keep_exact_identity_positive_requirement_and_content_difference(old,new,variant):
    assert values(old,new,variant=variant)==[False]*5


@pytest.mark.parametrize('variant',('unknown_norm','unknown_content','unknown_probes'))
def test_unknown_relations_are_not_filled_in(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant)


def test_normative_adoption_does_not_assert_actual_fulfillment():
    assert values(old=3,new=2)==[False,True,True,False,False]
    assert values(old=1,new=3)==[False,True,False,True,False]


def test_cached_and_uncached_evaluation_agree():
    assert values(old=3,memoize=False)==values(old=3)==[False,True,True,False,False]


def test_source_adapter_keeps_strict_replacement_separate():
    assert source_values('replacement')==[True,True]
    assert source_values('addition')==[True,False]
    assert source_values('retirement')==[True,False]
    assert source_values('unchanged')==[False,False]


def test_full_conditional_accepts_addition_and_retirement_but_rejects_independent_change():
    result=integration_checks()
    assert result['baseline']['schema'] and result['baseline']['strict_replacement']
    assert not result['baseline']['actual_benefit']
    assert result['cases']==dict(addition=[True,True,True,False],retirement=[True,True,True,False],
        unchanged=[False,False],independent_change=[False,True])


def test_actual_source_definitions_are_used_without_truth_stubs():
    actual={d['name']:d for d in source_fixture()['declarations']}
    assert all(actual[d['name']]==d for d in document(CORE)['declarations'])
    assert 'ibfchange' in _references(actual['ibfeffect'])
    assert 'ibfeffect' in _references(actual['ibfcausal'])


def test_attribution_does_not_execute_normative_change():
    assert attribution()==[True] and attribution(True)==[False]


def test_history_and_open_semantic_obligations_are_preserved():
    old,new=document(PARENT),document(SOURCE);_,mapping=manuscript()
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert len(new['statements'])==22 and _references(new['statements'][-1])=={'ibfattribution'}
    assert mapping['ibeschema']=='ibfschema'
    packet=review_report()
    assert all(not row['unconnected_candidate_roots'] for row in packet['obligations'])
    assert len(packet['templates'][0]['parameters'])==8
    assert not packet['semantic_completion'] and not packet['counts_as_translated_coverage']


def test_reproducible_documents_and_interpretation():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    for path,value in ((BASIS,basis()),(REVIEW,review(files))):
        assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
