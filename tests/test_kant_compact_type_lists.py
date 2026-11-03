import pytest
from scripts.kant_type_grammar import type_tokens,type_list_tokens,read_type,read_type_list
from scripts.check_kant_compact_type_lists import cases,checked,legacy_type_list_tokens
from scripts import kant_type_grammar as grammar
from unittest.mock import patch
from scripts.kant_public_fragment import compile_statement,decode
from scripts.visible_syntax_geometry import from_svg,to_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_old_and_compact_svg_preserve_the_exact_same_native_syntax(index):
    checked(index)


TYPES=['number',dict(kind='function',parameters=['individual',dict(kind='question',parameters=[])],
    result=dict(kind='description',result=dict(kind='sequence',element='content'),rank=2))]


@pytest.mark.parametrize('legacy',[False,True])
@pytest.mark.parametrize('values',[[],['individual'],TYPES])
def test_list_terminator_does_not_consume_following_type_or_expression(values,legacy):
    with patch.object(grammar,'type_list_tokens',legacy_type_list_tokens if legacy else type_list_tokens):
        tokens=grammar.type_list_tokens(values)
    stream=iter(tokens+['type_truth','not'])
    assert read_type_list(lambda:next(stream))==values
    assert read_type(lambda:next(stream))=='truth'
    assert list(stream)==['not']


@pytest.mark.parametrize('tokens,error',[
    (['lambda_typed','type_number','types_more','type_individual','types_end'],'Mixed type-list'),
    (['lambda_typed','types_more','type_number','type_individual','types_end'],'Mixed type-list'),
    (['lambda_typed','type_number'],'Incomplete visible type'),
    (['lambda_typed','type_function','types_end','types_end'],'Expected a public type'),
    (['lambda_typed','quote_raise','type_number','types_end'],'rank marker'),
    (['lambda_typed','type_number','bound0'],'Expected a type-list'),
])
def test_malformed_compact_lists_are_rejected_from_geometry(monkeypatch,tokens,error):
    stream=[dict(token=t,side=None,depth=i,path=[i]) for i,t in enumerate(tokens)]
    monkeypatch.setattr('scripts.kant_public_fragment.events',lambda *args:stream)
    drawing=compile_statement(None,silent=False)
    with pytest.raises(ValueError,match=error):decode(from_svg(to_svg(drawing['shapes'])))
