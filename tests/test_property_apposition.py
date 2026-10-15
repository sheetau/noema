from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import format_graph
from noema.semantics import SemanticError
from noema.extraction import _references
from scripts.check_property_apposition import fixture,values,source_values,attribution,review_report,document
from scripts.compose_property_apposition import ROOT,PARENT,SOURCE,BASIS,READING,REVIEW,build,basis,reading,review,manuscript


@pytest.mark.parametrize('mentions,forward,reverse,clarifies',list(product(range(4),(False,True),(False,True),(False,True))))
def test_shared_reference_and_explanation_have_separate_requirements(mentions,forward,reverse,clarifies):
    assert values(mentions,forward=forward,reverse=reverse,clarifies=clarifies)==[mentions==3 and forward and not reverse and clarifies]


def test_equivalent_description_alias_and_same_mention_do_not_count():
    assert values(variant='alias')==values(variant='same_node')==[False]
    assert values(memoize=False)==values()==[True]


def test_property_referent_cannot_be_replaced_by_an_individual():
    doc=deepcopy(fixture())
    doc['statements'][0]['body']['arguments'][3]=dict(kind='call',symbol='jmauthor',arguments=[])
    with pytest.raises(SemanticError):format_graph(doc,'compact')


@pytest.mark.parametrize('lean,urge,assigned',list(product((False,True),repeat=3)))
def test_both_traits_belong_to_the_same_bearer_and_reading(lean,urge,assigned):
    expected=[lean and urge,lean and assigned]
    assert source_values(hits=3 if lean else 0,urge=urge,assigned=assigned,indices=(0,1,2,3))==expected+expected


@pytest.mark.parametrize('variant',('missing_latent','other_growth_person'))
def test_current_bundle_does_not_imply_a_development_process(variant):
    assert source_values(variant=variant,indices=(0,1,2,3))==[True,True,False,False]


@pytest.mark.parametrize('variant',('other_assignment_person','other_assignment_time'))
def test_another_person_or_time_cannot_supply_the_second_trait(variant):
    assert source_values(variant=variant,indices=(0,1,2,3))==[True,False,True,False]


def test_two_roles_remain_distinct():
    assert source_values(variant='same_features',indices=(0,1,2,3))==[False]*4


@pytest.mark.parametrize('variant',('wrong_author','wrong_scope','wrong_context','missing_mention','crossed','alias','missing_order','reverse_order','no_clarification'))
def test_actual_family_preserves_reference_identity_and_direction(variant):
    assert source_values(variant=variant,indices=(4,5,6,7))==[False]*4


def test_nominal_reference_does_not_execute_the_referred_property():
    assert source_values(variant='unknown_orientation',indices=(4,5,6,7))==[True]*4
    assert source_values(indices=(8,))==[False]
    with pytest.raises(ValueError,match='Unknown'):values(variant='unknown')
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_reference',indices=(4,))


def test_attribution_quotes_the_revised_template_without_executing_it():
    assert attribution()==[True] and attribution(True)==[False]


def test_source_keeps_previous_definitions_and_connects_apposition():
    old,new=document(PARENT),document(SOURCE);_,mapping=manuscript()
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert len(new['statements'])==22
    assert _references(new['statements'][-1])=={mapping[old['statements'][-1]['body']['symbol']]}
    packet=review_report();rows={r['id']:r for r in packet['obligations']}
    for name in ('germ','thinking_disposition','hard_cover','dignified_treatment'):
        assert rows[name]['unconnected_candidate_roots']==[]
    assert len(packet['templates'][0]['parameters'])==8
    assert not packet['semantic_completion'] and not packet['counts_as_translated_coverage']


def test_reproducible_text_and_interpretation():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    for path,value in ((BASIS,basis()),(READING,reading()),(REVIEW,review(files))):
        assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
