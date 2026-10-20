from copy import deepcopy
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

from noema.validation_cache import ValidationCache, partial_report, digest
from scripts.audit_written_progress_extended import build_report
from scripts.project_work import check, history, write_new, audit
from test_semantic_reviews import corpus, write


@pytest.fixture
def draft_corpus(tmp_path):
    root = tmp_path
    for name in ('scripts/audit_written_progress.py', 'scripts/audit_written_progress_extended.py',
                 'noema/grammar.py', 'noema/discourse.py', 'noema/ranked.py',
                 'noema/ranked_discourse.py', 'noema/constructed.py',
                 'noema/constructed_discourse.py', 'noema/script.py'):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# Pinned fixture\n', encoding='utf-8')
    works = {}
    for work in ('kant-1784', 'einstein-1905'):
        unit = dict(id=work + ':u0001', text='ab cd', text_sha256=digest(b'ab cd'),
                    kind='body', math_ids=[])
        artifact = dict(units=[unit], math=[])
        write(root, 'artifacts/written-units-v1/' + work + '.json', artifact)
        works[work] = dict(inventory=[unit])
    write(root, 'reports/written-units-v1.json', dict(works=works))
    (root / 'example.noema').write_text('p:r aa[] c.s[k aa[]].', encoding='utf-8')
    write(root, 'reports/example.json', dict(
        alignment=dict(unit='kant-1784:u0001', status='partial', range=[0, 2],
                       definitions=['aa']),
        source_sha256={'example.noema': digest((root / 'example.noema').read_bytes())}))
    return root


def test_incremental_audit_matches_full_and_detects_new_changed_and_removed_reports(draft_corpus):
    root = draft_corpus
    cache = ValidationCache(root)
    try:
        with cache.adapters():
            expected = build_report(root)
            assert partial_report(cache) == expected
            hits = cache.stats['hits']
            assert partial_report(cache) == expected
            assert cache.stats['hits'] > hits
            extra = json.loads((root / 'reports/example.json').read_text(encoding='utf-8'))
            extra['alignment']['range'] = [3, 5]
            write(root, 'reports/extra.json', extra)
            assert partial_report(cache) == build_report(root)
            assert partial_report(cache)['works']['kant-1784']['text_characters_in_explicit_partial_ranges'] == 4
            extra['alignment']['range'] = [3, 4]
            write(root, 'reports/extra.json', extra)
            assert partial_report(cache) == build_report(root)
            (root / 'reports/extra.json').unlink()
            assert partial_report(cache) == expected
            # A formerly irrelevant JSON file gaining alignment also invalidates.
            write(root, 'reports/metadata.json', {'description': 'No evidence yet'})
            partial_report(cache)
            write(root, 'reports/metadata.json', extra)
            assert partial_report(cache) == build_report(root)
    finally:
        cache.close()


def test_cached_draft_cannot_hide_changed_historical_document(draft_corpus):
    cache = ValidationCache(draft_corpus)
    try:
        with cache.adapters():
            partial_report(cache)
            (draft_corpus / 'example.noema').write_text('p:r aa[] c.q[k aa[]].', encoding='utf-8')
            with pytest.raises(ValueError, match='Historical Noema document changed'):
                partial_report(cache)
    finally:
        cache.close()


def test_failed_tests_never_publish_a_report(tmp_path, monkeypatch):
    module = ModuleType('workflow_test_module')
    module.build_report = lambda: pytest.fail('Must not publish after failed tests')
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(pytest, 'main', lambda args: 1)
    cache = ValidationCache(tmp_path)
    try:
        args = SimpleNamespace(module=module.__name__, prepare=False, tests=['test.py'],
                               verify=None, write_report='report.json')
        with pytest.raises(ValueError, match='Selected tests failed'):
            check(cache, args)
        assert not (tmp_path / 'report.json').exists()
    finally:
        cache.close()


def test_evidence_is_not_overwritten_and_history_rebuilds_without_a_database(tmp_path):
    write_new(tmp_path, 'report.json', {'ok': True})
    before = (tmp_path / 'report.json').read_bytes()
    with pytest.raises(ValueError, match='Existing evidence differs'):
        write_new(tmp_path, 'report.json', {'ok': False})
    assert (tmp_path / 'report.json').read_bytes() == before
    (tmp_path / 'docs').mkdir()
    for name in ('README.history.md', 'docs/written-progress-history-through-20261020.md'):
        (tmp_path / name).write_bytes('Header\r\n\r\n因果の記録\r\n\r\nOther note\r\n'.encode('utf-8'))
    first = ValidationCache(tmp_path, path=tmp_path / 'first.sqlite')
    second = ValidationCache(tmp_path, path=tmp_path / 'second.sqlite')
    try:
        assert history(first, '因果', 2) == history(second, '因果', 2)
        assert all(row['text'] == '因果の記録' for row in history(first, '因果', 2))
        (tmp_path / 'README.history.md').write_text('Changed history', encoding='utf-8')
        assert len(history(first, '因果', 5)) == 1
    finally:
        first.close()
        second.close()
