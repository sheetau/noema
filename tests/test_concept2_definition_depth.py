from copy import deepcopy
import pytest
from noema.constructed_discourse import normalize_document
from scripts.concept2_writing import WritingReader
from scripts.concept2_document import empty_document
from scripts import concept2_composition as c,concept2_geometry_v5 as g
from tests.test_concept2_document import primitive,name,call


def declaration(depth):
    p=primitive(name('rain'),result='truth');body=call(p['name'])
    for _ in range(depth):body=dict(kind='not',arguments=[body])
    d=dict(kind='definition',name=name('rain','home'),parameters=[],result='truth',body=body)
    return p,d


def test_native_maximum_definition_depth_is_preserved_in_visible_reading():
    p,d=declaration(128)
    assert normalize_document(dict(empty_document(),declarations=[p,d]))['declarations'][-1]==d
    seed=dict(empty_document(),declarations=[p]);writer=WritingReader(seed)
    tokens=writer.encode_record(d)
    drawing=g.layout(writer.units(tokens))[0];shapes=[]
    for i,row in enumerate(g.fold([drawing],850)):shapes+=g.move(row['shapes'],80,80+170*i)
    assert WritingReader(seed).read_document(c.svg(shapes))['native']['declarations']==[d]
    assert writer._definition_transaction is False


def test_native_limit_and_wrong_result_reject_without_registration():
    for depth,result in [(129,'truth'),(128,'individual')]:
        p,d=declaration(depth);d['result']=result
        writer=WritingReader(dict(empty_document(),declarations=[p]))
        with pytest.raises(ValueError):writer.encode_record(d)
        assert writer._definition_transaction is False
        assert writer.document['declarations']==[]


def test_deferred_parse_still_checks_result_type_and_restores_transaction():
    p,d=declaration(5);seed=dict(empty_document(),declarations=[p]);tokens=WritingReader(seed).encode_record(d)
    i=tokens.index(('type','type_truth'));tokens[i]=('type','type_individual')
    reader=WritingReader(seed)
    with pytest.raises(ValueError):reader.parse(tokens)
    assert reader._definition_transaction is False
    assert reader.document['declarations']==[]


def test_definition_transaction_does_not_hide_indirect_quote_rank_failure():
    a=primitive(name('aki'))
    unwrap=dict(kind='definition',name=name('round','home'),parameters=[],result='individual',
        body=dict(kind='disquote',description=dict(kind='quote',body=call(a['name']))))
    seed=dict(empty_document(),declarations=[a,unwrap]);writer=WritingReader(seed)
    quoted=dict(kind='quote',body=call(unwrap['name']))
    d=dict(kind='definition',name=name('rain','home'),parameters=[],result='truth',body=dict(kind='equal',arguments=[quoted,quoted]))
    with pytest.raises(ValueError,match='lower ranks'):writer.encode_record(d)
    quoted['rank']=1;tokens=writer.encode_record(d)
    assert WritingReader(seed).parse(tokens)==d
    bad=[t for t in tokens if t!=('op','quotation-rank')]
    reader=WritingReader(seed)
    with pytest.raises(ValueError,match='lower ranks'):reader.parse(bad)
    assert reader.document['declarations']==[]
    assert reader._definition_transaction is False
