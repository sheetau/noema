"""A new spelling must not consume an adjacent old word at a shared prefix."""
from scripts.kant_lexical_context import use_context
from scripts.kant_passage_anchor_context import passage_context,SPELLINGS
from scripts.kant_page_public_context import load_semantic_spellings
from scripts.kant_public_lexicon import mark_boundaries,read_word,root_words


def recovered_words(context,expected):
    stream=[]
    for word in expected:
        for i,part in enumerate(context.parts[word]):
            stream.append(dict(token=part,side=None,**({'word':word} if i==0 else {})))
    with use_context(context):
        mark_boundaries(stream)
        stops={i for i,event in enumerate(stream) if event.get('lexical_seam')}
        tokens=[event['token'] for event in stream]
        result=[];position=0
        while position<len(tokens):
            word,position=read_word(tokens,position,stops=stops)
            result.append(word)
    return result


def test_new_alias_and_each_following_root_stay_separate():
    context=passage_context();extra,_=load_semantic_spellings(SPELLINGS)
    for name in extra:
        for root in root_words():
            assert recovered_words(context,[name,root])==[name,root]


def test_parts_of_a_new_alias_can_still_be_independent_old_words():
    context=passage_context();extra,_=load_semantic_spellings(SPELLINGS)
    for name in extra:
        parts=list(context.parts[name])
        assert recovered_words(context,parts)==parts
