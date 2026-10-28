"""Differential scanner behavior, including errors and Unicode whitespace."""
from itertools import product
import random
import pytest
from noema import constructed_discourse as syntax
from scripts.constructed_tokenizer_scope import _ORIGINAL,tokenize,tokenizer_scope


def outcome(parser,text):
    try:return ('ok',parser(text))
    except Exception as error:return ('error',type(error),str(error))


def test_differential_short_inputs_and_invalid_boundaries():
    alphabet=('a','2','7','[',']','.',':',' ','\t','A','0','?')
    for size in range(4):
        for parts in product(alphabet,repeat=size):
            text=''.join(parts)
            assert outcome(tokenize,text)==outcome(_ORIGINAL,text),repr(text)
    for text in (None,0,False,b'a','\x00','a\x00','a  ? z',' a\n\nA','\ufeffa'):
        assert outcome(tokenize,text)==outcome(_ORIGINAL,text),repr(text)


def test_every_unicode_whitespace_and_mixed_token_streams():
    whitespace=[chr(n) for n in range(0x110000) if chr(n).isspace()]
    for space in whitespace:
        for text in (space,'a'+space,'a'+space+'[2].',space+'?',space+'a'+space+'?'):
            assert outcome(tokenize,text)==outcome(_ORIGINAL,text),repr(text)
    rng=random.Random(20261029)
    atoms=['a','abc27','[',']','.',':',' ','\n','\t','\r\n','\u3000']
    for _ in range(200):
        text=''.join(rng.choice(atoms) for _ in range(rng.randrange(10,100)))
        assert outcome(tokenize,text)==outcome(_ORIGINAL,text)


def test_scope_restores_on_success_failure_and_rejects_nesting():
    assert syntax.tokenize is _ORIGINAL
    with tokenizer_scope():
        assert syntax.tokenize is tokenize
        assert syntax.tokenize('a[ b ].')==['a','[','b',']','.']
        with pytest.raises(ValueError,match='already replaced'):
            with tokenizer_scope():pass
    assert syntax.tokenize is _ORIGINAL
    with pytest.raises(RuntimeError,match='deliberate'):
        with tokenizer_scope():raise RuntimeError('deliberate')
    assert syntax.tokenize is _ORIGINAL
