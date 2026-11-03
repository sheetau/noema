import pytest
from scripts.check_kant_saved_declarations import cases,checked
from scripts.check_kant_declarations import canonical,reader_without_target,inputs
from scripts import kant_public_fragment as writing
from scripts.check_visible_syntax import call
from scripts.kant_lexical_context import LexicalContext,use_context


@pytest.mark.parametrize('index',range(len(cases())))
def test_actual_saved_declaration_without_target_oracle(index):checked(index)


def test_indirect_self_dependency_cannot_import_the_old_target():
    # A legitimate independent definition of book supplies the dependency;
    # redefining book through that definition would import book itself.
    source,published=canonical(dict(kind='definition',name=inputs()[0][2]['name'],
        parameters=[],result='individual',body=call('book')))
    invalid=dict(kind='definition',name=call('book')['symbol'],parameters=[],result='individual',
        body=dict(kind='call',symbol=source['name'],arguments=[]))
    with use_context(LexicalContext.from_published(published)):
        with pytest.raises(ValueError,match='Declaration cannot depend on itself indirectly'):
            writing.validate_declaration(invalid)
