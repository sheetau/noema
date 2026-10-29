"""Every general hearing/source/recipient argument survives geometry and stays distinct."""
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts import heard_prohibition_visible_profile as profile
from scripts.shared_modality import call
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_contracts_survive_actual_svg():
    vocabulary=profile.HeardProhibitionVisibleVocabulary()
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(doc,Word('proper',('book','home','above','book')),vocabulary,payload=768)['pages']
    actual=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert actual==doc and len(actual['declarations'])==6


def test_all_typed_slots_are_distinct_and_unknown_inputs_are_refused():
    for name,row in profile.ALL_CONTRACTS.items():
        assert row['result']=='truth' and len(row['parameters']) in (2,3)
        names=['jarg'+c for c in 'abc'[:len(row['parameters'])]]
        declarations=[dict(kind='primitive',name=name,parameters=row['parameters'],result='truth')]
        declarations += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in zip(names,row['parameters'],strict=True)]
        doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,
            statements=[dict(kind='ask',body=call(name,*(call(n) for n in names)))]))
        def run(values):
            domain=tuple(names)+('other',)
            return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=domain,
                primitives=values,memoize_definitions=False,memoize_expressions=False)]
        def values(result):
            def relation(*args):
                if args!=tuple(names):raise ValueError('Unknown heard prohibition inputs')
                return result
            return {n:lambda n=n:n for n in names}|{name:relation}
        for result in (False,True):assert run(values(result))==[result]
        for slot,n in enumerate(names):
            with pytest.raises(ValueError,match='Unknown heard prohibition'):
                run(values(True)|{n:lambda:'other'})
        def unknown(*args):raise ValueError('Unspecified heard prohibition relation')
        with pytest.raises(ValueError,match='Unspecified heard prohibition'):run(values(True)|{name:unknown})
