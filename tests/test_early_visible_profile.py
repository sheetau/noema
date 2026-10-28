"""Recover the opening contracts from actual shapes, preserving their parent vocabulary."""
from scripts import early_visible_profile as profile
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word
from noema.constructed_discourse import normalize_document


def test_all_opening_contracts_and_inherited_arithmetic_survive_actual_svg():
    vocabulary=profile.EarlyVisibleVocabulary()
    names=set(profile.SOURCE_RELATIONS.values())|set(profile.MATH_ALIASES.values())
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(names),statements=[]))
    compiled=compile_collection(document,Word('proper',('home','book')),vocabulary,payload=768)
    recovered=decode_collection([from_svg(to_svg(p['shapes'])) for p in compiled['pages']],vocabulary)
    assert recovered['document']==document
    assert {vocabulary._symbols[n] for n in names}<={d['name'] for d in document['declarations']}
