import pytest
from scripts.check_attached_note import VARIANTS,document,model,evaluate,checks,structure,generic_checks


@pytest.mark.parametrize('variant',VARIANTS)
def test_note_requires_its_own_document_anchor_and_author_credit(variant):
    doc=document()
    assert evaluate(doc,model(doc,variant))==[variant=='baseline']


def test_generic_membership_and_presentation_conditions():
    assert generic_checks()==32


def test_joint_claims_unknowns_and_no_explanation_entailment():
    assert len(checks()['combined_eight_statement_contrasts'])==9


def test_old_content_and_name_annotations_are_preserved():
    assert structure()['previous_statements_preserved']==25
