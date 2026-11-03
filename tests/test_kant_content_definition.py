from scripts.check_kant_content_definition import checked,inputs
from scripts.check_kant_multiple_arguments import syntax_hash


def test_existing_content_definition_body_and_parameter_scope():
    _,declaration,_=inputs();row=checked(0)
    assert row['declaration_sha256']==syntax_hash(declaration)
    assert row['body_sha256']==syntax_hash(declaration['body'])
