"""Audit the final sentence against the actual attributed manuscript template."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from noema.constructed import parse
from noema.manuscript_obligations import audit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'data/kant-manuscript-obligations-v1.json'
REPORT = ROOT / 'reports/kant-manuscript-obligations-v1.json'


def build_report():
    review = json.loads((ROOT / MANIFEST).read_text(encoding='utf-8'))
    source = json.loads((ROOT / review['source_units']).read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == review['unit'])
    raw = (ROOT / review['document']).read_bytes()
    assert sha256(raw).hexdigest() == review['document_sha256'], 'Manuscript hash differs'
    result = audit(parse(raw.decode('utf-8')), unit, review)
    result['document'] = review['document']
    paths = [MANIFEST, review['document'], review['source_units'],
        'noema/manuscript_obligations.py', 'scripts/check_kant_manuscript_obligations.py',
        'tests/test_manuscript_obligations.py', 'docs/kant-manuscript-obligations-v1.md', *review['evidence_files']]
    # This is a review record, deliberately not an alignment/coverage report.
    result['input_sha256'] = {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only', action='store_true'); args = cli.parse_args()
    report = build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    missing = [r['id'] for r in report['obligations'] if not r['has_recorded_candidate']]
    detached = sorted({n for r in report['obligations'] for n in r['unconnected_candidate_roots']})
    print('Open obligations:', len(report['obligations']))
    print('Without a recorded candidate:', ', '.join(missing))
    print('Candidates outside the selected statement:', ', '.join(detached))


if __name__ == '__main__': main()
