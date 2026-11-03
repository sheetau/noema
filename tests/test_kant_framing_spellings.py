import json

from scripts.kant_page_public_context import framing_context,discourse_context,inputs,ROOT,FRAMING_SPELLINGS
from scripts.kant_lexical_context import LexicalContext


def test_framing_words_change_neither_definitions_nor_reference_identity():
    ctx=framing_context();prior=discourse_context()
    assert ctx.document==prior.document
    assert ctx.declarations==prior.declarations
    assert len(ctx.declared_spellings)==27
    spec=json.loads((ROOT/FRAMING_SPELLINGS).read_text(encoding='utf-8'))
    assert set(spec['entries'])=={'qa','qh','s3','s4','h3a','h3s'}
    for old in spec['entries']:
        token=inputs()['bridge']['mapping'][old]
        assert ctx.words[token]==prior.words[token]
        assert len(ctx.parts[token])<len(prior.parts[token])
    for parts,token in prior.full_spellings.items():
        assert ctx.spellings[parts]==token


def test_published_framing_dictionary_preserves_the_two_distinct_descriptions():
    ctx=framing_context();reader=LexicalContext.from_published(ctx.published())
    mapping=inputs()['bridge']['mapping']
    qh=reader.declarations[mapping['qh']]
    assert qh==discourse_context().declarations[mapping['qh']]
    assert reader.document['statements']==[]
    assert reader.declared_spellings[mapping['qa']]!=reader.declared_spellings[mapping['qh']]
