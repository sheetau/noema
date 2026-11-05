import pytest
from scripts.two_work_repair import RepairWritingReader
from scripts.concept2_writing import WritingReader
from scripts.two_work_batch import RecordReader,render_record,process_records
from scripts.long_run import LongRun
from scripts.concept2_document import empty_document
from tests.test_concept2_document import name,call,eq,assertion,primitive


def example():
    f=name('book','home','round','above','give')
    seed=dict(empty_document(),declarations=[primitive(name('aki')),primitive(f,['individual'],'individual')])
    value=call(name('aki'))
    for _ in range(7):value=call(f,value)
    return seed,assertion(eq(value,value))


def test_hidden_second_occurrence_uses_valid_local_sharing_and_strict_reader():
    seed,record=example()
    with pytest.raises(AssertionError,match='Unpaired dot'):WritingReader(seed).encode_record(record)
    writer=RepairWritingReader(seed);tokens=writer.encode_record(record)
    svg,_=render_record(writer,tokens,2200)
    assert RecordReader(seed).read_page(svg)['statements']==[record]
    assert any(t[0]=='local-definition' for t in tokens)


def test_successful_encodings_and_cross_producer_cache_are_unchanged(tmp_path,monkeypatch):
    from scripts import two_work_batch as batch
    seed,_=example();record=assertion(eq(call(name('aki')),call(name('aki'))))
    assert RepairWritingReader(seed).encode_record(record)==WritingReader(seed).encode_record(record)
    records=seed['declarations']+[record]
    with LongRun(tmp_path/'before-run',{}) as run:
        before=process_records(records,tmp_path/'before',run,'unchanged-reader-and-geometry')
    monkeypatch.setattr(batch,'WritingReader',RepairWritingReader)
    with LongRun(tmp_path/'after-run',{}) as run:
        after=process_records(records,tmp_path/'after',run,'unchanged-reader-and-geometry',reuse=tmp_path/'before')
    assert before['validation_success'] and after['validation_success']
    assert all(r['decoding']=='inherited-unchanged-content' for r in after['records'])
