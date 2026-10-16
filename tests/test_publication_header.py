import pytest
from scripts.check_publication_header import FALSE,document,model,evaluate,generic_checks,checks,structure


@pytest.mark.parametrize('variant,indices',FALSE.items())
def test_publication_fields_cannot_substitute_for_one_another(variant,indices):
    doc=document()
    assert evaluate(doc,model(doc,variant))==[i not in indices for i in range(4)]


def test_number_uniqueness_is_scoped_to_scheme_and_parent_path():
    assert generic_checks()==16


def test_header_and_footnote_keep_december_and_september_separate():
    assert len(checks()['combined_thirteen_statement_contrasts'])==7


def test_existing_meanings_names_and_reviews_are_preserved():
    assert structure()['previous_statements_preserved']==27
