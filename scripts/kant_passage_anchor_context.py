"""Short semantic spellings of existing passage referents; no new primitives."""
from functools import lru_cache
from scripts.kant_page_public_context import load_semantic_spellings
from scripts.kant_reference_anchor_context import anchor_context
from scripts.kant_lexical_context import LexicalContext

SPELLINGS='data/kant-passage-anchor-spellings-v1.json'


@lru_cache(maxsize=1)
def passage_context():
    prior=anchor_context()
    extra,_=load_semantic_spellings(SPELLINGS)
    if prior.declared_spellings.keys() & extra.keys():
        raise ValueError('Repeated passage spelling')
    result=LexicalContext(prior.document,compact=prior.compact,
        declared_spellings=prior.declared_spellings|extra)
    if result.document!=prior.document or result.declarations!=prior.declarations:
        raise ValueError('Passage spelling changed meanings or declarations')
    if any(result.spellings.get(parts)!=name for parts,name in prior.spellings.items()):
        raise ValueError('Passage spelling displaced an existing alias')
    return result
