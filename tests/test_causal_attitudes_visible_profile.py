"""Actual visible forms preserve the selected relation and quotation types."""
from copy import deepcopy
import json
import pytest
from noema.constructed_discourse import normalize_document
from scripts import causal_attitudes_visible_profile as profile
from scripts.shared_modality import renamed
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_contracts_survive_actual_svg():
    vocabulary=profile.CausalAttitudesVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','round','above')),vocabulary,payload=768)['pages']
    restored=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert restored==document and len(restored['declarations'])==26


@pytest.mark.parametrize('name,slot',[
    ('factoroccasionnormality',1),('acceptsdescribedownstate',1),
    ('concessionexpectationcandidate',2),('adoptsavoidancefactor',2),
    ('nonliteralpropertypresentation',2),('nonliteralpropertypresentation',3),
    ('declaresdescribedstatus',2)])
def test_description_slots_do_not_accept_evaluated_content(name,slot):
    # A quoted property/relation is not interchangeable with its evaluated result.
    vocabulary=profile.CausalAttitudesVisibleVocabulary()
    actual=deepcopy(vocabulary.declaration(name))
    parameters=[dict(name='arg'+str(i),sort=deepcopy(s)) for i,s in enumerate(actual['parameters'])]
    assert parameters[slot]['sort']['kind']=='description'
    parameters[slot]['sort']='content'
    invalid=dict(kind='definition',name='wrongdescription',parameters=parameters,result=actual['result'],
        body=dict(kind='call',symbol=actual['name'],arguments=[dict(kind='variable',name=p['name']) for p in parameters]))
    with pytest.raises(ValueError):
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[actual,invalid],statements=[]))


def test_existing_arithmetic_and_temporal_definitions_are_reused_exactly():
    from noema.meaning_catalog import load_catalog
    root=profile.ROOT
    state=json.loads((root/'data/work-state.json').read_text(encoding='utf-8'))
    active=json.loads((root/state['review_index']).read_text(encoding='utf-8'))['works']['kant-1784']
    catalog=load_catalog(root,active['meaning_basis'],document_path=active['document'])
    source={d['name']:d for d in catalog.document['declarations']}
    voc=profile.CausalAttitudesVisibleVocabulary()
    reused=dict(he='indicatorvalid',hf='occurrencecount',ta='chronology',tb='timewindow',
        tc='holdsall',tg='processextent',th='becomes')
    names=profile.MATH_ALIASES|reused
    for old,new in names.items():
        assert renamed(source[old],names)==voc._plain_declaration(new)
