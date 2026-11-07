import pytest
from scripts.check_kant_forty_body_layout import OUT,read,selected,reader,published
from scripts.kant_incremental_dictionary import PublishedStatementReader


def test_all_original_page_items_have_exact_geometry_receipts():
    report=read(OUT/'structural-report.json')
    assert len(report['bodies'])==40
    assert [r['statement'] for r in report['bodies']]==[r['statement'] for r in selected()]
    assert all(r['circles']>0 and r['rows']>0 for r in report['bodies'])


def test_public_body_dictionary_has_no_source_statements_and_cannot_be_changed():
    value=reader();before=value.result(True)
    assert published()['native']['statements']==[]
    with pytest.raises(ValueError,match='requires statements'):
        value.register(published()['native']['declarations'][0])
    assert value.result(True)==before
    assert isinstance(value.fork(),PublishedStatementReader)
