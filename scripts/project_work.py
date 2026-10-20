"""Single-process project workflow; no server, scheduler or autonomous goal."""
import argparse
import importlib
import json
from pathlib import Path
import sys
import time

from noema.validation_cache import ValidationCache, digest, partial_report
from noema import review_registry
from noema.semantic_reviews import path_in, require

ROOT = Path(__file__).resolve().parents[1]
STATE = 'data/work-state.json'


def read(root, name):
    return json.loads(path_in(root, name).read_text(encoding='utf-8'))


def write_new(root, name, value):
    path = path_in(root, name)
    body = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    if path.exists():
        require(path.read_text(encoding='utf-8') == body,
                'Existing evidence differs; choose a new version: ' + name)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(body)


def audit(cache, index):
    from scripts.audit_written_progress_reviewed import apply_reviews
    reviewed = review_registry.load_reviews(cache.root, index, cache)
    for work, rows in reviewed['works'].items():
        for row in rows:
            require(row['source_inventory'] == 'artifacts/written-units-v1/' + work + '.json',
                    'Reviewed source differs from draft inventory')
    result = apply_reviews(partial_report(cache), reviewed)
    for name in ('scripts/audit_written_progress_reviewed.py', 'noema/semantic_reviews.py',
                 'tests/test_semantic_reviews.py', 'docs/unit-semantic-review-v1.md'):
        result['source_sha256'][name] = digest((cache.root / name).read_bytes())
    if read(cache.root, index)['schema_version'] == review_registry.SCHEMA:
        # New reports also pin the new validation path. Historical v1 output
        # remains exactly reproducible for differential comparison.
        review_registry.merge_pins(result['source_sha256'], cache.code)
        for name in ('tests/test_validation_cache.py', 'tests/test_review_registry.py',
                     'tests/test_project_work.py'):
            result['source_sha256'][name] = digest((cache.root / name).read_bytes())
    # Check every output dependency again before publishing/reusing the result.
    require(cache.hashes(result['source_sha256']) == result['source_sha256'],
            'Input changed during final audit')
    cache.assert_engine_unchanged()
    return result


def brief(root):
    state = read(root, STATE)
    index = read(root, state['review_index'])
    summary = {k: state[k] for k in ('objective', 'review_index', 'progress_report',
                                     'next_work', 'verification', 'limits')}
    summary['active_manuscripts'] = {
        work: {k: active[k] for k in ('document', 'meaning_basis', 'identifier_annotations')}
        for work, active in index['works'].items()}
    report = read(root, state['progress_report'])
    summary['progress'] = {
        work: {k: row[k] for k in ('author_unit_count', 'units_with_partial_drafts',
                                  'explicit_text_range_percent', 'verified_semantic_units')}
        for work, row in report['works'].items()}
    return summary


def history(cache, query, limit):
    """Rebuildable index; archived Markdown and Git remain authoritative."""
    require(cache.connection is not None, 'History search needs the local SQLite index')
    paths = ('README.history.md', 'docs/written-progress-history-through-20261020.md')
    for name in paths:
        raw = path_in(cache.root, name).read_bytes()
        stamp = digest(raw)
        old = cache.connection.execute(
            'SELECT source_sha256 FROM history WHERE path=? LIMIT 1', (name,)).fetchone()
        if old is None or old[0] != stamp:
            text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
            paragraphs = [p for p in text.split('\n\n') if p.strip()]
            with cache.connection:
                cache.connection.execute('DELETE FROM history WHERE path=?', (name,))
                cache.connection.executemany('INSERT INTO history VALUES (?,?,?,?)',
                    [(name, i, stamp, body) for i, body in enumerate(paragraphs)])
    terms = query.split()
    require(bool(terms), 'Supply a history search term')
    sql = 'SELECT path,part,body FROM history WHERE ' + ' AND '.join(
        'instr(lower(body),lower(?))>0' for _ in terms) + ' ORDER BY path,part LIMIT ?'
    return [dict(path=p, paragraph=i, text=body[:3000], truncated=len(body) > 3000) for p, i, body in
            cache.connection.execute(sql, (*terms, limit))]


def check(cache, args):
    # Import AFTER installing adapters so from-import aliases use cached loaders.
    module = importlib.import_module(args.module) if args.module else None
    if args.prepare:
        require(module is not None, '--prepare needs --module')
        module.prepare()
    if args.tests:
        import pytest
        code = pytest.main([*args.tests, '-q'])
        require(code == 0, 'Selected tests failed (exit ' + str(code) + ')')
    if args.verify or args.write_report:
        require(module is not None, 'Report check needs --module')
        with cache.hash_transaction():
            result = module.build_report()
        require(isinstance(result, dict) and result.get('source_sha256'),
                'Report must pin its inputs')
        require(cache.hashes(result['source_sha256']) == result['source_sha256'],
                'Report inputs changed during validation')
        cache.assert_engine_unchanged()
        if args.verify:
            require(result == read(cache.root, args.verify), 'Stored report differs')
        else:
            write_new(cache.root, args.write_report, result)
    require(bool(args.tests or args.verify or args.write_report), 'No check requested')
    return dict(selected_tests_passed=bool(args.tests), report_verified=args.verify,
                report_written=args.write_report)


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest='command', required=True)
    commands.add_parser('brief')
    search = commands.add_parser('history')
    search.add_argument('query')
    search.add_argument('--limit', type=int, default=5)
    commands.add_parser('runs')
    reg = commands.add_parser('register')
    reg.add_argument('--index')
    reg.add_argument('--work')
    reg.add_argument('--basis')
    reg.add_argument('--annotations')
    reg.add_argument('--review', action='append', default=[])
    reg.add_argument('--output', required=True)
    audit_cli = commands.add_parser('audit')
    audit_cli.add_argument('--index')
    audit_cli.add_argument('--full', action='store_true',
                           help='Bypass every persistent result, including parsed ASTs')
    target = audit_cli.add_mutually_exclusive_group()
    target.add_argument('--verify', metavar='REPORT')
    target.add_argument('--output', metavar='NEW_REPORT')
    check_cli = commands.add_parser('check')
    check_cli.add_argument('--module')
    check_cli.add_argument('--tests', nargs='+')
    check_cli.add_argument('--prepare', action='store_true')
    check_cli.add_argument('--full', action='store_true')
    target = check_cli.add_mutually_exclusive_group()
    target.add_argument('--verify', metavar='REPORT')
    target.add_argument('--write-report', metavar='NEW_REPORT')
    return cli


def main(argv=None, root=ROOT):
    args = parser().parse_args(argv)
    if args.command == 'brief':
        print(json.dumps(brief(root), ensure_ascii=False, indent=2))
        return 0
    started = time.perf_counter()
    cache = ValidationCache(root, enabled=not getattr(args, 'full', False))
    success = False
    details = {}
    try:
        with cache.adapters():
            if args.command == 'history':
                require(1 <= args.limit <= 30, 'History limit must be 1..30')
                details = dict(matches=history(cache, args.query, args.limit))
            elif args.command == 'runs':
                details = dict(runs=[
                    dict(id=i, started=s, command=c, seconds=round(t, 3), success=bool(ok),
                         details=json.loads(d)) for i, s, c, t, ok, d in cache.connection.execute(
                        'SELECT id,started,command,seconds,success,details FROM runs ORDER BY id DESC LIMIT 8')])
            elif args.command == 'check':
                details = check(cache, args)
            elif args.command == 'register':
                index = args.index or read(root, STATE)['review_index']
                with cache.hash_transaction():
                    result = review_registry.compact_index(root, index, work=args.work,
                        basis=args.basis, annotations=args.annotations, reviews=args.review)
                cache.assert_engine_unchanged()
                write_new(root, args.output, result)
                verified = review_registry.load_reviews(root, args.output, cache)
                details = dict(index=args.output,
                    reviewed_units={w: len(rows) for w, rows in verified['works'].items()})
            else:
                index = args.index or read(root, STATE)['review_index']
                result = audit(cache, index)
                if args.verify:
                    require(result == read(root, args.verify), 'Stored aggregate differs')
                if args.output:
                    write_new(root, args.output, result)
                details = dict(index=index, parsed_documents=result['parsed_noema_documents'],
                    alignment_reports=len(result['inspected_alignment_reports']),
                    reviewed_units={w: v['verified_semantic_units'] for w, v in result['works'].items()},
                    result_sha256=digest(json.dumps(result, ensure_ascii=False, sort_keys=True).encode('utf-8')),
                    full=getattr(args, 'full', False), verified=args.verify, output=args.output)
            cache.assert_engine_unchanged()
            success = True
        print(json.dumps(dict(details, seconds=round(time.perf_counter() - started, 3),
                              cache=cache.stats), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as error:
        details['error'] = str(error)
        print(str(error), file=sys.stderr)
        return 1
    finally:
        cache.record_run(args.command, started, success, details)
        cache.close()


if __name__ == '__main__':
    raise SystemExit(main())
