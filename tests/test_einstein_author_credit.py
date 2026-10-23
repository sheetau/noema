from scripts.check_einstein_author_credit import finite_checks, structure_checks


def test_name_application_and_author_credit_bindings():
    finite_checks()


def test_inherited_manuscript_generic_definition_and_source_pins():
    structure_checks()
