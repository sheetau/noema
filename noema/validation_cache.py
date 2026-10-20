"""Disposable, content-verified SQLite acceleration for immutable validators.

The historical validators stay byte-for-byte unchanged. The opt-in runner
temporarily installs memoized adapters before importing task modules. A cache
hit still hashes every dependency; timestamps never establish validity.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
import time
import zlib


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def digest(raw):
    return sha256(raw).hexdigest()


class ValidationCache:
    def __init__(self, root, *, enabled=True, path=None):
        self.root = Path(root).resolve()
        self.enabled = enabled
        self.path = Path(path) if path else self.root / '.noema-cache/validation.sqlite'
        self.stats = dict(hits=0, misses=0, invalidations=0, hashed_bytes=0)
        self.connection = None
        self._hash_snapshot = None
        self.code = self.engine_inputs()
        self.engine = digest(encoded(dict(code=self.code, python=sys.version)))
        if enabled:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(self.path, timeout=30)
            self.connection.execute('PRAGMA journal_mode=WAL')
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    engine TEXT NOT NULL, kind TEXT NOT NULL, key TEXT NOT NULL,
                    dependencies TEXT NOT NULL, value BLOB NOT NULL,
                    value_sha256 TEXT NOT NULL, PRIMARY KEY(engine, kind, key));
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY, started TEXT NOT NULL,
                    command TEXT NOT NULL, seconds REAL NOT NULL,
                    success INTEGER NOT NULL, engine TEXT NOT NULL,
                    details TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS history (
                    path TEXT NOT NULL, part INTEGER NOT NULL, source_sha256 TEXT NOT NULL,
                    body TEXT NOT NULL, PRIMARY KEY(path, part));
            """)

    def engine_inputs(self):
        # Include all language implementations, not just the dispatch function:
        # a parser/evaluator helper edit must invalidate previously parsed ASTs.
        implementation = Path(__file__).resolve().parent.parent
        files = list((implementation / 'noema').rglob('*.py'))
        files += [implementation / 'scripts' / name for name in (
            'audit_written_progress.py', 'audit_written_progress_extended.py',
            'audit_written_progress_reviewed.py', 'project_work.py')]
        files.append(implementation / 'pyproject.toml')
        return {p.relative_to(implementation).as_posix(): digest(p.read_bytes())
                for p in sorted(files) if p.is_file()}

    def assert_engine_unchanged(self):
        if self.engine_inputs() != self.code:
            raise ValueError('Validator changed during execution; rerun before publishing')

    def file(self, name):
        from .semantic_reviews import path_in
        return path_in(self.root, name)

    def hashes(self, names):
        result = {}
        for name in sorted(set(names)):
            raw = self.file(name).read_bytes()
            self.stats['hashed_bytes'] += len(raw)
            result[name] = digest(raw)
        return result

    @contextmanager
    def hash_transaction(self):
        """Deduplicate overlapping manifests, then rehash the union on exit.

        Limited to one synchronous validation operation, never the whole agent
        session. A changed input aborts before a result can be published.
        """
        if self._hash_snapshot is not None or not self.enabled:
            yield
            return
        snapshot = {}
        self._hash_snapshot = snapshot
        try:
            yield
            if self.hashes(snapshot) != snapshot:
                raise ValueError('Input changed during review validation')
        finally:
            self._hash_snapshot = None

    def validate_hashes(self, validator, root, hashes):
        from .semantic_reviews import require
        if self._hash_snapshot is None or Path(root).resolve() != self.root:
            return validator(root, hashes)
        require(isinstance(hashes, dict) and bool(hashes), 'Missing review input hashes')
        for name, expected in hashes.items():
            require(isinstance(expected, str) and len(expected) == 64, 'Invalid review input digest')
            # New names are confined to root by hashes(); the union is resolved
            # again on exit, including paths reached through changed symlinks.
            if name not in self._hash_snapshot:
                self._hash_snapshot.update(self.hashes([name]))
            require(self._hash_snapshot[name] == expected, 'Review input changed: ' + name)

    def get(self, kind, key):
        if not self.enabled:
            self.stats['misses'] += 1
            return None
        row = self.connection.execute(
            'SELECT dependencies,value,value_sha256 FROM artifacts '
            'WHERE engine=? AND kind=? AND key=?', (self.engine, kind, key)).fetchone()
        if row:
            try:
                dependencies = json.loads(row[0])
                valid = self.hashes(dependencies) == dependencies
                raw = zlib.decompress(row[1])
                valid = valid and digest(raw) == row[2]
                value = json.loads(raw)
            except (OSError, ValueError, zlib.error, TypeError):
                valid = False
            if valid:
                self.stats['hits'] += 1
                return value
            self.stats['invalidations'] += 1
        self.stats['misses'] += 1
        return None

    def put(self, kind, key, value, dependencies=None):
        if self.enabled:
            # Existing producers compare regenerated JSON byte-for-byte. Keep
            # insertion order in values, including nested AST/type dictionaries.
            raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            self.connection.execute(
                'INSERT OR REPLACE INTO artifacts VALUES (?,?,?,?,?,?)',
                (self.engine, kind, key, encoded(dependencies or {}).decode('utf-8'),
                 zlib.compress(raw), digest(raw)))
            self.connection.commit()
        return value

    def parse(self, parser, text, namespace):
        key = digest(text.encode('utf-8'))
        result = self.get('parse:' + namespace, key)
        if result is None:
            result = parser(text)
            self.put('parse:' + namespace, key, result)
        return result

    def symbols(self, parser, text):
        """The inventory only needs names after a complete successful parse."""
        key = digest(text.encode('utf-8'))
        result = self.get('alignment-symbols', key)
        if result is None:
            document = parser(text)
            result = {'declarations': [{'name': row['name']}
                                      for row in document['declarations']]}
            self.put('alignment-symbols', key, result)
        return result

    def catalog(self, loader, root, basis_path, *, document_path=None):
        from .meaning_catalog import Catalog
        if not self.enabled or Path(root).resolve() != self.root:
            return loader(root, basis_path, document_path=document_path)
        key = encoded([str(basis_path), str(document_path) if document_path is not None else None]).decode('utf-8')
        result = self.get('catalog', key)
        if result is None:
            catalog = loader(root, basis_path, document_path=document_path)
            result = asdict(catalog)
            self.put('catalog', key, result, catalog.source_sha256)
        return Catalog(**result)

    def reviews(self, loader, root, index_path):
        if not self.enabled or Path(root).resolve() != self.root:
            return loader(root, index_path)
        key = str(index_path)
        result = self.get('reviews', key)
        if result is None:
            with self.hash_transaction():
                result = loader(root, index_path)
            self.put('reviews', key, result, result['source_sha256'])
        return result

    @contextmanager
    def adapters(self):
        """Single-process, single-thread task scope; restore globals on failure.

        Task modules must be imported inside this context. Nothing is patched on
        disk, and the original functions always handle cache misses.
        """
        from . import meaning_catalog as meanings, identifiers, semantic_reviews as reviews, review_registry
        from scripts import audit_written_progress_extended as partial
        from scripts import audit_written_progress_reviewed as reviewed
        original_catalog = meanings.load_catalog
        original_reviews = reviews.load_reviews
        original_parse = meanings._parse
        original_partial_parse = partial.parse
        original_validate_hashes = reviews.validate_hashes
        original_registry = review_registry.load_reviews

        def catalog(root, basis_path, *, document_path=None):
            return self.catalog(original_catalog, root, basis_path, document_path=document_path)

        def load_reviews(root, index_path):
            return self.reviews(original_reviews, root, index_path)

        replacements = [
            (meanings, '_parse', lambda text: self.parse(original_parse, text, 'meaning')),
            (partial, 'parse', lambda text: self.parse(original_partial_parse, text, 'all-editions')),
            (meanings, 'load_catalog', catalog), (identifiers, 'load_catalog', catalog),
            (reviews, 'load_catalog', catalog),
            (reviews, 'load_reviews', load_reviews), (reviewed, 'load_reviews', load_reviews),
            (reviews, 'validate_hashes', lambda root, hashes:
                self.validate_hashes(original_validate_hashes, root, hashes)),
            (review_registry, 'load_reviews', lambda root, index_path, cache=None:
                original_registry(root, index_path, cache if cache is not None else
                                  (self if Path(root).resolve() == self.root else None))),
        ]
        old = [(module, name, getattr(module, name)) for module, name, _ in replacements]
        try:
            for module, name, function in replacements:
                setattr(module, name, function)
            yield self
        finally:
            for module, name, function in reversed(old):
                setattr(module, name, function)

    def record_run(self, command, started, success, details):
        if self.connection:
            seconds = time.perf_counter() - started
            timestamp = (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()
            self.connection.execute(
                "INSERT INTO runs(started,command,seconds,success,engine,details) "
                "VALUES (?,?,?,?,?,?)",
                (timestamp, command, seconds, int(success),
                 self.engine, encoded(dict(details, cache=self.stats)).decode('utf-8')))
            self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()


def partial_report(cache):
    """Reuse a complete draft audit only if membership AND content still match."""
    from scripts import audit_written_progress_extended as audit_module
    build_report = audit_module.build_report
    if not cache.enabled:
        return build_report(cache.root)
    # v1/v2 aggregates are outputs, not alignment evidence. Validate that fact.
    names = []
    for path in sorted((cache.root / 'reports').glob('*.json')):
        name = path.relative_to(cache.root).as_posix()
        if path.name in ('written-progress-v1.json', 'written-progress-v2.json'):
            row = json.loads(path.read_text(encoding='utf-8'))
            if any(k in row for k in ('alignment', 'source_alignment', 'source_ranges')):
                raise ValueError('Progress output unexpectedly contains alignment evidence')
        else:
            names.append(name)
    membership = digest(encoded(names))
    result = cache.get('partial-audit', membership)
    if result is None:
        before = cache.hashes(names)
        # The immutable audit accesses parsed documents only for declaration
        # names and distinct document counts. Keep those summaries in memory;
        # parsing/type/scope checks still happen before creating a summary.
        parser = audit_module.parse
        try:
            audit_module.parse = lambda text: cache.symbols(parser, text)
            result = build_report(cache.root)
        finally:
            audit_module.parse = parser
        dependencies = dict(before, **result['source_sha256'])
        if cache.hashes(dependencies) != dependencies:
            raise ValueError('Input changed during draft audit')
        cache.put('partial-audit', membership, result, dependencies)
    return deepcopy(result)
