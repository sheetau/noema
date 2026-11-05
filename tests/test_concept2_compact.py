from copy import deepcopy
import pytest
from scripts.concept2_compact import CompactDocumentCodec,compact_runs,expand_repeats
from scripts.concept2_document import DocumentCodec
from scripts import concept2_geometry_v5 as g,concept2_composition as composition
from tests.test_concept2_document import name,var,records,drawing


def test_type_and_distance_runs_preserve_every_slot():
    for count in (0,1,2,5,6,13):
        parameters=[dict(name='v'+chr(97+i),sort='individual') for i in range(count)]
        for slot in range(count or 1):
            body=var(parameters[slot]['name']) if count else dict(kind='number',numerator=0,denominator=1)
            record=dict(kind='definition',name=name('rain','home'),parameters=parameters,
                result='individual' if count else 'number',body=body)
            writer=CompactDocumentCodec();reader=CompactDocumentCodec()
            tokens=writer.encode_record(record)
            assert reader.parse(tokens)==record
            if count>5:
                assert len(tokens)<len(DocumentCodec().encode_record(record))


def test_long_definition_including_folded_reference_distance():
    parameters=[dict(name='v'+chr(97+i),sort='number') for i in range(18)]
    record=dict(kind='definition',name=name('rain','home'),parameters=parameters,result='number',body=var())
    writer=CompactDocumentCodec();d=drawing(writer,record);shapes=[]
    for i,row in enumerate(g.fold([d],520)):shapes+=g.move(row['shapes'],80,80+170*i)
    result=CompactDocumentCodec().read_document(composition.svg(shapes))
    assert result['native']['declarations']==[record]
    assert writer.encode_record(record).count(('repeat',5))>=6


def test_record_headers_and_word_spellings_are_compacted_too():
    record=dict(kind='primitive',name=name('round','round','round','round'),parameters=['number']*5,result='truth')
    writer=CompactDocumentCodec();tokens=writer.encode_record(record)
    assert ('repeat',5) in tokens
    assert CompactDocumentCodec().read_svg(composition.svg(drawing(writer,record)['shapes']))['native']==record


def test_repeat_excludes_bare_small_circle_and_invalid_chains():
    assert compact_runs([('root','aki')]*7)==[('root','aki')]*7
    for bad in ([('repeat',2)],[('root','aki'),('repeat',2)],
                [('type','type_number'),('repeat',5),('repeat',2)],
                [('op','scope-hop'),('repeat',6)]):
        with pytest.raises(ValueError):expand_repeats(bad)
    for n in range(1,42):
        source=[('op','scope-hop')]*n+[('op','group-close')]
        assert expand_repeats(compact_runs(source))==source
