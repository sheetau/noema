import pytest
from scripts.check_projected_classification import VARIANTS,document,model,evaluate,checks,structure


@pytest.mark.parametrize('variant',VARIANTS)
def test_honorific_classification_uses_the_same_person_and_source_occurrence(variant):
    doc=document()
    assert evaluate(doc,model(doc,variant))==[variant=='baseline']


def test_description_is_not_an_assertion_of_actual_membership():
    result=checks()
    assert result['actual_membership_independent']=={'False':[True,False],'True':[True,True]}
    assert result['actual_membership_unknown_until_queried']


def test_no_new_referents_or_binary_complement_assumption():
    result=structure()
    assert result['new_local_references']==0
    assert result['female_negation_and_adult_threshold_absent']
