from scripts.check_kant_function_definition_body import checked,inputs
from scripts.check_kant_multiple_arguments import syntax_hash


def test_existing_definition_preserves_parameter_scope_and_body():
    _,declaration,_=inputs();row=checked(0)
    assert row['declaration_sha256']==syntax_hash(declaration)
    assert row['body_sha256']==syntax_hash(declaration['body'])
    # Branch reduction is recorded by the report, not certified as complete.
