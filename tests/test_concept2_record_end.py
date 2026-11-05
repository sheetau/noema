from scripts.concept2_document_reader import DocumentReader
from scripts import concept2_composition as composition
from tests.test_concept2_document import name,drawing


def test_repeated_nested_type_closure_keeps_a_circle_record_end():
    result=dict(kind='question',parameters=[dict(kind='question',parameters=[])])
    record=dict(kind='primitive',name=name('rain','book'),parameters=[],result=result)
    writer=DocumentReader();tokens=writer.encode_record(record)
    assert tokens[-2:]==[('repeat',2),('word-end',)]
    assert DocumentReader().read_svg(composition.svg(drawing(writer,record)['shapes']))['native']==record


def test_alias_repeat_keeps_its_lexical_stop():
    writer=DocumentReader();reader=DocumentReader()
    decl=dict(kind='primitive',name=name('rain','book'),parameters=[],result='number')
    writer.register(decl);reader.register(decl)
    alias=dict(kind='spelling',name=decl['name'],parts=['home']*5)
    assert reader.read_svg(composition.svg(drawing(writer,alias)['shapes']))['native']==alias
