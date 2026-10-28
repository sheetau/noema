"""Opt-in linear scanning for the unchanged constructed-language parser.

Historical parser files remain untouched. This scope changes only how the
same token stream is obtained, and always restores the original tokenizer.
Callers must pin this module and its differential evidence before adoption.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import re
from noema import constructed_discourse as syntax

_ORIGINAL=syntax.tokenize
_TOKEN=re.compile(r'\s*([a-z2-7]+|[\[\].:])')


def tokenize(text):
    syntax.require(isinstance(text,str),'Expected Noema text')
    tokens=[];offset=0
    while offset<len(text):
        match=_TOKEN.match(text,offset)
        if match is None:
            # This suffix is examined only at EOF or the first rejected token.
            # Valid token boundaries never copy the remaining input.
            if text[offset:].isspace():break
            syntax.require(False,f'Invalid definition-language token at {offset}')
        tokens.append(match[1]);offset=match.end()
    return tokens


@contextmanager
def tokenizer_scope():
    """Use the fast scanner in this process only; reject nested replacement."""
    if syntax.tokenize is not _ORIGINAL:
        raise ValueError('Constructed tokenizer is already replaced')
    paths=(Path(syntax.__file__),Path(__file__))
    pins={p:sha256(p.read_bytes()).hexdigest() for p in paths}
    syntax.tokenize=tokenize
    try:
        yield
        if syntax.tokenize is not tokenize:
            raise ValueError('Constructed tokenizer changed during scope')
        if any(sha256(p.read_bytes()).hexdigest()!=h for p,h in pins.items()):
            raise ValueError('Constructed tokenizer inputs changed during scope')
    finally:
        syntax.tokenize=_ORIGINAL
