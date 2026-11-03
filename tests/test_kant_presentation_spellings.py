import json

from scripts.kant_presentation_context import presentation_context,SPELLINGS
from scripts.kant_page_public_context import framing_context,inputs,ROOT
from scripts.kant_lexical_context import LexicalContext


def test_presentation_spellings_preserve_native_declarations_and_old_names():
    before=framing_context();after=presentation_context()
    assert after.document==before.document and after.declarations==before.declarations
    assert after.document['statements']==[]
    spec=json.loads((ROOT/SPELLINGS).read_text(encoding='utf-8'))
    assert set(spec['entries'])=={'hzxu','rqzv','rqtv','rqvt'}
    assert len(after.declared_spellings)==31
    for old in spec['entries']:
        token=inputs()['bridge']['mapping'][old]
        assert after.words[token]==before.words[token]
        assert len(after.parts[token])<len(before.parts[token])
    for parts,token in before.full_spellings.items():assert after.spellings[parts]==token


def test_presentation_dictionary_is_independent_of_declaration_order():
    context=presentation_context()
    reverse=LexicalContext(dict(context.document,declarations=list(reversed(context.document['declarations']))),
        declared_spellings=context.declared_spellings)
    assert context.parts==reverse.parts and context.spellings==reverse.spellings
    published=LexicalContext.from_published(context.published())
    assert published.document['statements']==[] and published.parts==context.parts
