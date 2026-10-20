import json
import os
from pathlib import Path

import pytest

from noema.meaning_catalog import load_catalog, BasisError
from noema.semantic_reviews import load_reviews
from noema.validation_cache import ValidationCache
from test_meaning_catalog import bundle, write
from test_semantic_reviews import corpus, change_review


def test_cache_rehashes_content_even_when_size_and_mtime_are_restored(tmp_path):
    path = tmp_path / 'input.txt'
    path.write_bytes(b'first')
    cache = ValidationCache(tmp_path)
    try:
        cache.put('sample', 'entry', {'ok': True}, cache.hashes(['input.txt']))
        assert cache.get('sample', 'entry') == {'ok': True}
        stat = path.stat()
        path.write_bytes(b'other')
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert cache.get('sample', 'entry') is None
        path.unlink()
        assert cache.get('sample', 'entry') is None
    finally:
        cache.close()


def test_disk_reuse_returns_independent_values_and_ignores_corrupt_payload(tmp_path):
    cache = ValidationCache(tmp_path)
    cache.put('sample', 'entry', {'nested': [1], 'before': {'z': 1, 'a': 2}})
    cache.close()
    cache = ValidationCache(tmp_path)
    try:
        first = cache.get('sample', 'entry')
        first['nested'].append(2)
        assert cache.get('sample', 'entry') == {'nested': [1], 'before': {'z': 1, 'a': 2}}
        assert list(cache.get('sample', 'entry')) == ['nested', 'before']
        assert list(cache.get('sample', 'entry')['before']) == ['z', 'a']
        cache.connection.execute("UPDATE artifacts SET value=x'1234'")
        cache.connection.commit()
        assert cache.get('sample', 'entry') is None
    finally:
        cache.close()


def test_validator_identity_and_full_mode_prevent_cache_reuse(tmp_path):
    cache = ValidationCache(tmp_path)
    cache.put('sample', 'entry', [1])
    cache.engine = 'different-implementation'
    assert cache.get('sample', 'entry') is None
    cache.code = {}
    with pytest.raises(ValueError, match='Validator changed'):
        cache.assert_engine_unchanged()
    cache.close()
    cache = ValidationCache(tmp_path, enabled=False)
    assert cache.get('sample', 'entry') is None
    assert cache.connection is None


def test_cached_catalog_exactly_matches_uncached_chain_and_projection(tmp_path):
    bundle(tmp_path)
    expected = load_catalog(tmp_path, 'delta.json')
    cache = ValidationCache(tmp_path)
    try:
        with cache.adapters():
            from noema import meaning_catalog
            first = meaning_catalog.load_catalog(tmp_path, 'delta.json')
            assert first == expected
            first.entries['ac']['meaning_ja'] = 'Mutation by a caller'
            second = meaning_catalog.load_catalog(tmp_path, 'delta.json')
            assert second == expected
            assert cache.stats['hits'] > 0
            # A changed convention remains visible even if the AST is cached.
            delta = json.loads((tmp_path / 'delta.json').read_text(encoding='utf-8'))
            delta['definitions']['ac'] = 'Changed meaning'
            write(tmp_path / 'delta.json', delta)
            assert meaning_catalog.load_catalog(tmp_path, 'delta.json').entries['ac']['meaning_ja'] == 'Changed meaning'
            delta['inherited_meaning_basis'] = 'delta.json'
            write(tmp_path / 'delta.json', delta)
            with pytest.raises(BasisError, match='Cyclic'):
                meaning_catalog.load_catalog(tmp_path, 'delta.json')
        assert meaning_catalog.load_catalog is load_catalog
    finally:
        cache.close()


def test_cached_review_revalidates_evidence_and_review_decision(corpus):
    cache = ValidationCache(corpus)
    expected = load_reviews(corpus, 'index.json')
    try:
        with cache.adapters():
            from noema import semantic_reviews
            assert semantic_reviews.load_reviews(corpus, 'index.json') == expected
            assert semantic_reviews.load_reviews(corpus, 'index.json') == expected
            change_review(corpus, lambda row: row.update(unresolved=['Still partial']))
            with pytest.raises(ValueError, match='unresolved'):
                semantic_reviews.load_reviews(corpus, 'index.json')
        assert semantic_reviews.load_reviews is load_reviews
    finally:
        cache.close()


def test_context_restores_legacy_functions_after_failure(tmp_path):
    cache = ValidationCache(tmp_path)
    try:
        with pytest.raises(RuntimeError):
            with cache.adapters():
                raise RuntimeError('Task failed')
        from noema import meaning_catalog
        assert meaning_catalog.load_catalog is load_catalog
    finally:
        cache.close()


def test_shared_hash_transaction_detects_changes_before_returning(tmp_path):
    from noema import semantic_reviews
    path = tmp_path / 'evidence.txt'
    path.write_bytes(b'original')
    cache = ValidationCache(tmp_path)
    pins = cache.hashes(['evidence.txt'])
    try:
        with cache.adapters():
            with pytest.raises(ValueError, match='changed during review validation'):
                with cache.hash_transaction():
                    semantic_reviews.validate_hashes(tmp_path, pins)
                    path.write_bytes(b'modified')
                    # The union is always rehashed before accepting the batch.
                    semantic_reviews.validate_hashes(tmp_path, pins)
            with pytest.raises(ValueError, match='Review input changed'):
                semantic_reviews.validate_hashes(tmp_path, pins)
    finally:
        cache.close()


def test_helper_source_change_invalidates_persistent_results(tmp_path, monkeypatch):
    from noema import validation_cache
    implementation = tmp_path / 'implementation' / 'noema'
    implementation.mkdir(parents=True)
    helper = implementation / 'parser_helper.py'
    helper.write_text('VERSION = 1\n', encoding='utf-8')
    monkeypatch.setattr(validation_cache, '__file__', str(implementation / 'validation_cache.py'))
    cache = ValidationCache(tmp_path)
    cache.put('sample', 'entry', {'passed': True})
    previous = cache.engine
    cache.close()
    helper.write_text('VERSION = 2\n', encoding='utf-8')
    cache = ValidationCache(tmp_path)
    try:
        assert cache.engine != previous
        assert cache.get('sample', 'entry') is None
    finally:
        cache.close()


def test_cached_projection_rejects_a_later_changed_declaration(tmp_path):
    from noema.constructed import format_graph
    from noema import meaning_catalog
    _, _, document, _ = bundle(tmp_path)
    projection = json.loads(json.dumps(document))
    projection['declarations'] = projection['declarations'][:3]
    projection['statements'] = []
    write(tmp_path / 'projection.noema', format_graph(projection, 'compact'))
    expected = load_catalog(tmp_path, 'delta.json', document_path=Path('projection.noema'))
    cache = ValidationCache(tmp_path)
    try:
        with cache.adapters():
            assert meaning_catalog.load_catalog(tmp_path, 'delta.json',
                document_path=Path('projection.noema')) == expected
            assert meaning_catalog.load_catalog(tmp_path, 'delta.json',
                document_path=Path('projection.noema')) == expected
            write(tmp_path / 'projection.noema', 'p:r aa[] c.')
            with pytest.raises(BasisError, match='Projection adds, changes'):
                meaning_catalog.load_catalog(tmp_path, 'delta.json',
                    document_path=Path('projection.noema'))
    finally:
        cache.close()
