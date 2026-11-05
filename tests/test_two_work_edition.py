import pytest
from scripts.two_work_edition import review_order
from scripts.long_run import fingerprint


def test_author_note_stays_separate_from_body_but_both_bindings_are_checked():
    statements=[dict(body='body'),dict(body='note')]
    review=dict(selection=dict(statements=[dict(index=7,sha256=fingerprint(statements[0])),dict(index=8,sha256=fingerprint(statements[1]))]),
                source_order_statements=[7],attached_note_statements=[8])
    entry=dict(statements=[0,1],review='example');source=dict(statements=statements)
    assert review_order(review,entry,source,'body')==[0]
    assert review_order(review,entry,source,'author_note')==[1]
    review['attached_note_statements']=[]
    with pytest.raises(ValueError,match='Incomplete'):review_order(review,entry,source,'body')


def test_equal_statement_occurrences_are_not_collapsed():
    statement=dict(body='same');review=dict(selection=dict(statements=[dict(index=i,sha256=fingerprint(statement)) for i in (4,5)]))
    assert review_order(review,dict(statements=[0,1],review='example'),dict(statements=[statement,statement]),'body')==[0,1]
