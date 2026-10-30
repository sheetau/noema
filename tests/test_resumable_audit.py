import json
import os
from pathlib import Path

import pytest

from noema.meaning_catalog import load_catalog
from noema.review_registry import compact_index
from noema.semantic_reviews import REQUIREMENTS, selection_binding
from noema.validation_cache import ValidationCache
from scripts import project_work, resumable_audit
from scripts.long_run import LongRun, PauseRequested
from test_project_work import draft_corpus
from test_semantic_reviews import write, pin


@pytest.fixture
def audit_fixture(draft_corpus):
    root = draft_corpus
    for name in ('scripts/audit_written_progress_reviewed.py', 'noema/semantic_reviews.py',
                 'tests/test_semantic_reviews.py', 'docs/unit-semantic-review-v1.md',
                 'tests/test_validation_cache.py', 'tests/test_review_registry.py', 'tests/test_project_work.py'):
        p = root / name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('# Pinned fixture\n', encoding='utf-8')
    write(root, 'basis.json', dict(document='example.noema', primitives=[dict(
        symbol='aa', parameters=[], result='truth', arguments=[], meaning_ja='A condition.')], definitions={}))
    (root / 'reading.md').write_text('An explicit whole-unit reading.\n', encoding='utf-8')
    write(root, 'evidence.json', dict(source_sha256={'example.noema': pin(root, 'example.noema')}))
    selection = selection_binding(load_catalog(root, 'basis.json'), [0])
    works = {}; pins = {}
    for work in ('kant-1784', 'einstein-1905'):
        source = f'artifacts/written-units-v1/{work}.json'
        unit = json.loads((root / source).read_text())['units'][0]
        name = work + '-review.json'
        paths = ['example.noema', 'basis.json', source, 'reading.md', 'evidence.json']
        review = dict(schema_version='noema-semantic-review-1', work=work, unit=unit['id'],
                      document='example.noema', meaning_basis='basis.json', identifier_annotations=None,
                      source=dict(inventory=source, unit_sha256=unit['text_sha256'], text=unit['text'],
                                  range=[0, len(unit['text'])], math=[]), selection=selection,
                      decision='equivalent_under_stated_reading', reviewer='assistant_review',
                      interpretation=['Explicit reading.'], limits=['No automated equivalence proof.'], unresolved=[],
                      requirements=[dict(id=n, decision='satisfied', reason='Explicit reasoning.') for n in REQUIREMENTS],
                      evidence=dict(source_reading=['reading.md'], formal_checks=['evidence.json'], semantic_reading=['reading.md']),
                      source_sha256={p: pin(root, p) for p in paths})
        write(root, name, review)
        works[work] = dict(document='example.noema', meaning_basis='basis.json', identifier_annotations=None,
                           source_inventory=source, reviews=[name])
        pins.update({p: pin(root, p) for p in paths + [name]})
    write(root, 'old-index.json', dict(schema_version='noema-semantic-review-index-1', works=works, source_sha256=pins))
    write(root, 'index.json', compact_index(root, 'old-index.json'))
    cache = ValidationCache(root, enabled=False)
    implementation = Path(__file__).resolve().parents[1]
    for name in cache.code:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((implementation / name).read_bytes())
    with cache.adapters(): expected = project_work.audit(cache, 'index.json')
    cache.close()
    write(root, 'reports/expected.json', expected)
    return root


def test_real_audit_pause_resume_matches_legacy_full(audit_fixture, monkeypatch):
    root = audit_fixture; path = root / 'run'
    inputs = resumable_audit.manifest(root, 'index.json', 'reports/expected.json')
    emit = LongRun.emit
    def pause_after_first(self, event, **updates):
        emit(self, event, **updates)
        if event == 'review_complete' and updates['completed'] == 1:
            (self.directory / 'PAUSE').touch()
    with monkeypatch.context() as patch:
        patch.setattr(LongRun, 'emit', pause_after_first)
        with pytest.raises(PauseRequested):
            with LongRun(path, inputs) as run:
                resumable_audit.perform(root, 'index.json', 'reports/expected.json', run)
    assert not (path / 'result.json').exists()
    (path / 'PAUSE').unlink()
    with LongRun(path, inputs, resume=True) as run:
        receipt = resumable_audit.perform(root, 'index.json', 'reports/expected.json', run)
        assert run.state['reused'] == 1
    assert receipt['legacy_full'] is False
    assert receipt['verified'] == 'reports/expected.json'
    assert not (root / '.noema-cache/validation.sqlite').exists()
    events = [json.loads(line) for line in (path / 'events.jsonl').read_text().splitlines()]
    assert any(row['event'] == 'document_complete' and row['completed'] == 1 and row['total'] == 1 for row in events)


def test_same_size_same_mtime_edit_blocks_resume(audit_fixture):
    root = audit_fixture; path = root / 'run'
    before = resumable_audit.manifest(root, 'index.json', 'reports/expected.json')
    with LongRun(path, before): pass
    target = root / 'reading.md'; stat = target.stat()
    target.write_bytes(target.read_bytes().replace(b'explicit', b'implicit'))
    os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    after = resumable_audit.manifest(root, 'index.json', 'reports/expected.json')
    with pytest.raises(ValueError, match='changed'):
        with LongRun(path, after, resume=True): pass


def test_changed_input_during_run_cannot_publish(audit_fixture, monkeypatch):
    root = audit_fixture
    inputs = resumable_audit.manifest(root, 'index.json', 'reports/expected.json')
    original = project_work.audit
    def altered(*args):
        result = original(*args)
        (root / 'reading.md').write_text('Changed evidence', encoding='utf-8')
        return result
    monkeypatch.setattr(project_work, 'audit', altered)
    with pytest.raises(ValueError, match='Inputs changed'):
        with LongRun(root / 'run', inputs) as run:
            resumable_audit.perform(root, 'index.json', 'reports/expected.json', run)
    assert not (root / 'run/result.json').exists()
