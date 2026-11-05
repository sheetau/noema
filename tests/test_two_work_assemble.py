import pytest
from scripts.two_work_assemble import source_order,renamed,allocate


def value(name):return dict(kind='assert',body=dict(kind='call',symbol=name,arguments=[]))


def test_source_order_keeps_duplicate_occurrences_and_all_auxiliary_statements():
    source=[value('a'),value('b'),value('a')]
    visible=[value('note'),value('B'),value('A'),value('A'),value('note')]
    actual,selected,inverse=source_order(source,visible,{'a':'A','b':'B'})
    assert actual==[value('A'),value('B'),value('A'),value('note'),value('note')]
    assert len(set(selected))==3
    assert [actual[inverse[i]] for i in range(len(visible))]==visible
    with pytest.raises(ValueError):source_order(source,visible[:-2],{'a':'A','b':'B'})


def test_lexical_alpha_rename_preserves_binding_names_and_is_invertible():
    d=dict(kind='definition',name='a',parameters=[dict(name='a',sort='individual')],result='individual',
           body=dict(kind='call',symbol='b',arguments=[dict(kind='variable',name='a')]))
    m={'a':'A','b':'B'};actual=renamed(d,m)
    assert actual['parameters'][0]['name']=='a' and actual['body']['arguments'][0]['name']=='a'
    assert renamed(actual,{v:k for k,v in m.items()})==d


def test_allocation_is_injective_and_reserves_existing_words():
    declarations=[dict(name=str(i)) for i in range(180)]
    first=allocate(declarations,set(),'kant')
    second=allocate(declarations,set(first.values()),'kant')
    assert len(set(first.values()))==len(first)==180
    assert not set(first.values())&set(second.values())
