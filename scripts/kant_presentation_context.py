"""Short spellings for existing presentation relations, with unchanged meanings."""
from functools import lru_cache

from scripts.kant_page_public_context import framing_context,load_semantic_spellings
from scripts.kant_lexical_context import LexicalContext

SPELLINGS='data/kant-presentation-spellings-v1.json'


@lru_cache(maxsize=2)
def presentation_context(compact=True):
    prior=framing_context(compact)
    extra,_=load_semantic_spellings(SPELLINGS)
    if prior.declared_spellings.keys() & extra.keys():
        raise ValueError('Repeated presentation spelling')
    result=LexicalContext(prior.document,compact=compact,
        declared_spellings=prior.declared_spellings|extra)
    if result.document!=prior.document or result.declarations!=prior.declarations:
        raise ValueError('Spelling changed native meanings or declarations')
    return result
