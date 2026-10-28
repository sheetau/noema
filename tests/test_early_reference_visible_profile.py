"""Keep separate physical constraints, typed quotations and the frozen parent."""
from scripts import early_reference_visible_profile as profile
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word
from noema.constructed_discourse import normalize_document


def test_all_reference_constraints_survive_actual_svg():
    vocabulary=profile.EarlyReferenceVisibleVocabulary()
    names=set(profile.EXTRA)|{'radiationpropagation'}
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(names),statements=[]))
    compiled=compile_collection(doc,Word('proper',('home','book')),vocabulary,payload=768)
    assert decode_collection([from_svg(to_svg(p['shapes'])) for p in compiled['pages']],vocabulary)['document']==doc
