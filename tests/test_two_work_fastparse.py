import pytest
from noema import constructed_discourse as native
from noema.constructed import parse
from scripts.two_work_fastparse import tokenize,parse_source,linear_tokenizer


@pytest.mark.parametrize('text',['',' \t\r\n','p:\nr aa[a] c.\nr ab[] a.\ns[k aa[k ab]].',
    'a2 z7 [ ] . :\u2003','a!','a\n8','a\x00b','α','[x] @'])
def test_tokens_or_failure_are_identical(text):
    try:expected=native.tokenize(text)
    except Exception as error:
        with pytest.raises(type(error),match=str(error)):tokenize(text)
    else:assert tokenize(text)==expected


def test_parser_and_checks_remain_identical_and_patch_is_restored():
    original=native.tokenize
    for text in ['p:\nr aa[] a.','n:\nr aa[a] c.','p:\nr aa[a] c.\nd ab[va a] c[k aa[v va]].']:
        assert parse_source(text)==parse(text)
        assert native.tokenize is original
    with pytest.raises(ValueError):parse_source('p:\nr aa[] missing.')
    assert native.tokenize is original
    with pytest.raises(RuntimeError):
        with linear_tokenizer():raise RuntimeError('interrupt')
    assert native.tokenize is original
