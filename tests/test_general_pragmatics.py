import pytest
from scripts.check_general_pragmatics import *


def test_same_event_and_description_binding_in_every_relational_slot():
    rows=diagnostics()
    assert len(rows)==10 and sum(r['slot_diagnostics'] for r in rows)>100


@pytest.mark.parametrize('name',['expressivepresentation','declarativepresentation','ironicreading','metaphoricalreading'])
def test_presented_descriptions_do_not_execute_their_contents(name):
    d,m,_,values=fixture(name)
    for role in ('attitude','status','literal','intended','echoed'):
        if role in values:m[values[role]]=unknown
    assert value(d,m) is True


def test_expression_does_not_imply_sincerity():
    d,m,_,values=fixture('expressivesincere')
    m[values['attitude']]=lambda x:Content(('now','later'),(False,False))
    assert value(d,m) is False
    d['statements'][0]['body']['symbol']='expressivepresentation'
    assert value(d,m) is True


def test_declaration_without_authority_or_effect_is_not_effective():
    d,m,_,values=fixture('declarativeeffective')
    assert value(d,{**m,'fixtureauthorized':lambda *xs:False}) is False
    assert value(d,{**m,values['status']:lambda:Content(('now','later'),(True,False))}) is False
    with pytest.raises(ValueError,match='Unknown'):
        value(d,{**m,values['status']:unknown})


def test_fiction_does_not_change_real_world_truth():
    d,m,_,values=fixture('fictionalclaim')
    m[values['content']]=lambda:Content(('now','later'),(True,False))
    assert value(d,m) is True
    assert m[values['content']]().values[1] is False
    m['fixtureworld']=lambda:'later'
    assert value(d,m) is False


def test_metaphor_needs_nonempty_features_and_mapping_but_not_identity():
    d,m,_,values=fixture('metaphoricalreading')
    assert values['source']!=values['target'] and value(d,m) is True
    assert value(d,{**m,'fixturemapping':lambda x:'a'}) is False
    d['statements'][0]['body']['arguments'][2]['items']=[]
    assert value(d,m) is False
