"""Avoid copying unrelated meanings when a syntax reader builds root lookup.

This optional synchronous adapter calls the original Reader constructor with
an isolated copy of the same lexical entries, then restores the real vocabulary
for all subsequent decoding. It caches neither tokens nor validation outcomes.
Historical readers and vocabulary.document() retain their original behavior.
"""
from contextlib import contextmanager
from copy import deepcopy
from threading import RLock,get_ident

from scripts.visible_lexical_script import Lexicon,require
from scripts.visible_syntax import Reader

_LOCK=RLock()


class _RootDocument:
    def __init__(self,entries):self.entries=entries
    def document(self):return {'entries':self.entries}


@contextmanager
def root_lookup_scope():
    """Optimize inherited Lexicon.document only; custom accessors fall back."""
    with _LOCK:
        original=Reader.__init__;owner=get_ident()

        def initialize(reader,signatures,vocabulary):
            require(get_ident()==owner,'Root lookup scope used from another thread')
            accessor=getattr(vocabulary,'document',None)
            if getattr(accessor,'__func__',None) is not Lexicon.document:
                return original(reader,signatures,vocabulary)
            # Lexicon.document is exactly deepcopy(_document). The original
            # constructor consumes only ['entries']; no source names or
            # meanings are substituted, and mutations are observed each call.
            entries=deepcopy(vocabulary._document['entries'])
            original(reader,signatures,_RootDocument(entries))
            reader.v=vocabulary

        Reader.__init__=initialize
        try:yield
        finally:Reader.__init__=original
