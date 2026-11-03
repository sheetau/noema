"""Short existing discourse references without changing names or referents."""
from functools import lru_cache
import hashlib, json
from scripts.kant_page_public_context import ROOT, load_semantic_spellings
from scripts.kant_lexical_context import LexicalContext

SPELLINGS = 'data/kant-reference-anchor-spellings-v1.json'
BASELINE = 'reports/kant-presentation-spellings-v1.json'
DICTIONARY = 'output/kant-presentation-spellings/dictionary.json'


@lru_cache(maxsize=1)
def previous_context():
    evidence = json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    raw = (ROOT/DICTIONARY).read_bytes()
    if hashlib.sha256(raw).hexdigest() != evidence['source_sha256'][DICTIONARY]:
        raise ValueError('Saved public dictionary changed')
    return LexicalContext.from_published(json.loads(raw))


@lru_cache(maxsize=1)
def anchor_context():
    prior = previous_context()
    extra, _ = load_semantic_spellings(SPELLINGS)
    if prior.declared_spellings.keys() & extra.keys():
        raise ValueError('Repeated explicit spelling')
    result = LexicalContext(prior.document, compact=prior.compact,
        declared_spellings=prior.declared_spellings | extra)
    if result.document != prior.document or result.declarations != prior.declarations:
        raise ValueError('Reference spelling changed meanings or referents')
    if any(result.spellings.get(parts) != token for parts, token in prior.spellings.items()):
        raise ValueError('Reference spelling displaced an existing alias')
    return result
