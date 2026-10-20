from copy import deepcopy
import json

import pytest

from noema.constructed import parse
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import selection_binding
from noema.review_registry import compact_index, load_reviews
from noema.validation_cache import ValidationCache
from test_semantic_reviews import corpus, write, pin


def publish(root, result, name='compact.json'):
    write(root, name, result)
    return load_reviews(root, name)


def next_basis(root, statement='s[k aa[]].'):
    (root / 'next.noema').write_text(
        'p:r aa[] c.r ab[] c.' + statement, encoding='utf-8')
    decl = parse((root / 'next.noema').read_text(encoding='utf-8'))['declarations'][-1]
    write(root, 'next.json', dict(document='next.noema', parent='text.noema',
        inherited_meaning_basis='basis.json',
        new_signatures={'ab': {k: decl[k] for k in ('parameters', 'result')}},
        primitives=[dict(symbol='ab', parameters=[], result='truth', arguments=[],
                         meaning_ja='Independent condition.')], definitions={}))


def test_compact_registration_reuses_original_review_without_copying(corpus):
    original = (corpus / 'review.json').read_bytes()
    compact = compact_index(corpus, 'index.json')
    assert compact['works']['sample']['reviews'] == [{'review': 'review.json', 'statements': [0]}]
    reviewed = publish(corpus, compact)
    assert len(reviewed['works']['sample']) == 1
    assert not reviewed['semantic_equivalence_automatically_proved']
    assert (corpus / 'review.json').read_bytes() == original
    assert set(compact['source_sha256']) == {'text.noema', 'basis.json', 'inventory.json', 'review.json'}


def test_unrelated_addition_carries_review_but_changed_selected_statement_requires_review(corpus):
    next_basis(corpus)
    result = compact_index(corpus, 'index.json', work='sample', basis='next.json')
    row = publish(corpus, result)['works']['sample'][0]
    assert row['document'] == 'next.noema' and row['review'] == 'review.json'
    next_basis(corpus, 's[k ab[]].')
    with pytest.raises(ValueError, match='requires rereading'):
        compact_index(corpus, 'index.json', work='sample', basis='next.json')


def test_reindexed_statements_can_be_explicitly_bound_without_new_judgment(corpus):
    next_basis(corpus, 's[k ab[]].s[k aa[]].')
    result = compact_index(corpus, 'index.json')
    active = result['works']['sample']
    active.update(document='next.noema', meaning_basis='next.json')
    active['reviews'][0]['statements'] = [1]
    result['source_sha256'].update({p: pin(corpus, p) for p in ('next.noema', 'next.json')})
    row = publish(corpus, result)['works']['sample'][0]
    assert row['selection']['statements'][0]['index'] == 1


def test_changed_original_evidence_invalidates_cached_compact_review(corpus):
    compact = compact_index(corpus, 'index.json')
    publish(corpus, compact)
    cache = ValidationCache(corpus)
    try:
        with cache.adapters():
            load_reviews(corpus, 'compact.json', cache)
            assert load_reviews(corpus, 'compact.json', cache)['works']['sample']
            (corpus / 'reading.md').write_text('Altered reading', encoding='utf-8')
            with pytest.raises(ValueError, match='input changed'):
                load_reviews(corpus, 'compact.json', cache)
    finally:
        cache.close()


@pytest.mark.parametrize('fault', ['duplicate', 'unpin', 'statement', 'source', 'basis'])
def test_compact_registry_cannot_bypass_old_review_guards(corpus, fault):
    result = compact_index(corpus, 'index.json')
    active = result['works']['sample']
    if fault == 'duplicate':
        active['reviews'] *= 2
    elif fault == 'unpin':
        del result['source_sha256']['review.json']
    elif fault == 'statement':
        active['reviews'][0]['statements'] = [False]
    elif fault == 'source':
        inventory = json.loads((corpus / 'inventory.json').read_text(encoding='utf-8'))
        inventory['units'][0]['text'] = 'Changed'
        write(corpus, 'inventory.json', inventory)
        result['source_sha256']['inventory.json'] = pin(corpus, 'inventory.json')
    else:
        basis = json.loads((corpus / 'basis.json').read_text(encoding='utf-8'))
        basis['primitives'][0]['meaning_ja'] = 'Changed convention'
        write(corpus, 'basis.json', basis)
        result['source_sha256']['basis.json'] = pin(corpus, 'basis.json')
    with pytest.raises(ValueError):
        publish(corpus, result)


def test_rebinding_rejects_changed_designation_forms(corpus):
    root = corpus
    text = 'p:r aa[a] c.r ac[] a.s[k aa[k ac[]]].'
    (root / 'text.noema').write_text(text, encoding='utf-8')
    write(root, 'basis.json', dict(document='text.noema', definitions={},
        primitives=[
            dict(symbol='aa', parameters=['individual'], result='truth',
                 arguments=['subject'], meaning_ja='Condition on a subject.'),
            dict(symbol='ac', parameters=[], result='individual',
                 arguments=[], meaning_ja='A designation.')]))
    annotations = dict(schema_version='noema-identifiers-1', document='text.noema',
        document_sha256=pin(root, 'text.noema'), entries=[
            dict(symbol='ac', role='designation',
                 forms=[dict(text='Name', language='en', role='name')])])
    write(root, 'names.json', annotations)
    write(root, 'evidence.json', dict(source_sha256={'text.noema': pin(root, 'text.noema')}))
    review = json.loads((root / 'review.json').read_text(encoding='utf-8'))
    review.update(identifier_annotations='names.json',
                  selection=selection_binding(load_catalog(root, 'basis.json'), [0]))
    review['source_sha256'] = {p: pin(root, p) for p in
        (*review['source_sha256'], 'names.json')}
    write(root, 'review.json', review)
    index = json.loads((root / 'index.json').read_text(encoding='utf-8'))
    index['works']['sample']['identifier_annotations'] = 'names.json'
    index['source_sha256'] = {p: pin(root, p) for p in (*index['source_sha256'], 'names.json')}
    write(root, 'index.json', index)
    assert publish(root, compact_index(root, 'index.json'))['works']['sample']
    (root / 'next.noema').write_text(text, encoding='utf-8')
    write(root, 'next.json', dict(document='next.noema', parent='text.noema',
        inherited_meaning_basis='basis.json', new_signatures={}, definitions={}))
    annotations.update(document='next.noema', document_sha256=pin(root, 'next.noema'))
    annotations['entries'][0]['forms'][0]['text'] = 'Other name'
    write(root, 'next-names.json', annotations)
    with pytest.raises(ValueError, match='identifier forms changed'):
        compact_index(root, 'index.json', work='sample', basis='next.json',
                      annotations='next-names.json')
