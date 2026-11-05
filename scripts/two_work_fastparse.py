"""Linear-offset tokenizer adapter; native grammar and type checks are unchanged."""
from contextlib import contextmanager
import re
from noema import constructed_discourse as native
from noema.constructed import parse

TOKEN=re.compile(r'\s*([a-z2-7]+|[\[\].:])')
SPACE=re.compile(r'\s*\Z')


def tokenize(text):
    native.require(isinstance(text,str),'Expected Noema text')
    tokens=[];offset=0
    while offset<len(text):
        match=TOKEN.match(text,offset)
        if match is None:
            if SPACE.match(text,offset):break
            native.require(False,f'Invalid definition-language token at {offset}')
        tokens.append(match[1]);offset=match.end()
    return tokens


@contextmanager
def linear_tokenizer():
    original=native.tokenize;native.tokenize=tokenize
    try:yield
    finally:native.tokenize=original


def parse_source(text):
    # Scoped to this interpreter; callers must not share it with parsing threads.
    with linear_tokenizer():return parse(text)
