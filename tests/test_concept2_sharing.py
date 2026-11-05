from copy import deepcopy
import pytest
from scripts.concept2_document import DocumentCodec,empty_document
from scripts.concept2_document_reader import DocumentReader
from scripts.concept2_shared_document import SharedDocumentReader
from scripts.concept2_sharing import choose_plan,candidate_plan
from scripts import concept2_composition as c,concept2_geometry_v5 as g
from tests.test_concept2_document import name,call,var,eq,assertion,primitive


def both(*items):
    value=items[-1]
    for item in reversed(items[:-1]):value=dict(kind='and',arguments=[item,value])
    return value


def seed():
    return dict(empty_document(),declarations=[primitive(name('aki')),primitive(name('book','home','round'),['individual'],'individual'),primitive(name('give'),['individual']*3,'truth')])


def check_record(record,base):
    writer=SharedDocumentReader(base);reader=DocumentReader(base)
    record=writer.canonical_record(record);tokens=writer.encode_record(record)
    drawing=g.layout(writer.units(tokens))[0];shapes=[]
    for i,row in enumerate(g.fold([drawing],750)):shapes+=g.move(row['shapes'],80,80+i*170)
    assert reader.read_page(c.svg(shapes))['statements']==[record]
    return tokens,record


def test_complex_open_values_share_within_their_binder_scope():
    value=call(name('book','home','round'),var())
    body=both(eq(value,value),call(name('give'),value,value,value))
    record=assertion(dict(kind='forall',variable='va',sort='individual',body=body))
    tokens,_=check_record(record,seed())
    assert any(t[0]=='role-definition' for t in tokens)
    assert any(t[0]=='branch' for t in tokens)


def test_outer_and_inner_variables_cannot_share_their_value():
    f=name('book','home','round')
    outer=call(f,var('va'));inner=call(f,var('vb'))
    nested=dict(kind='forall',variable='vb',sort='individual',body=both(eq(inner,inner),eq(inner,outer),eq(outer,outer)))
    body=both(eq(outer,outer),nested,eq(outer,outer))
    check_record(assertion(dict(kind='forall',variable='va',sort='individual',body=body)),seed())


def test_quote_namespace_and_native_names_are_preserved():
    value=call(name('book','home','round'),var())
    quantified=dict(kind='forall',variable='va',sort='individual',body=both(eq(value,value),eq(value,value)))
    quoted=dict(kind='quote',body=quantified)
    check_record(assertion(both(eq(quoted,quoted),quantified)),seed())


def test_distant_bound_variables_use_shared_references():
    params=[dict(name='v'+chr(97+i),sort='individual') for i in range(18)]
    record=dict(kind='definition',name=name('rain','town'),parameters=params,result='truth',body=both(*[eq(var(),var('vb')) for _ in range(5)]))
    tokens,record=check_record(record,seed())
    assert len(tokens)<len(DocumentReader(seed()).encode_record(record))


def test_nested_candidates_drop_hidden_unpaired_inner_dots():
    value=call(name('book','home','round'),call(name('book','home','round'),call(name('aki'))))
    body=both(eq(value,value),eq(value,value),eq(value,value))
    plan=candidate_plan(assertion(body),DocumentReader(seed()).dictionary)
    assert c.expand_plan(plan['plan'],DocumentReader(seed()).dictionary)==assertion(body)
    check_record(assertion(body),seed())


def test_shared_regions_do_not_cross_assumption_children():
    value=call(name('book','home','round'),call(name('aki')))
    condition=both(eq(value,value),eq(value,value))
    check_record(dict(kind='suppose',condition=condition,statements=[assertion(condition),assertion(condition)]),seed())
