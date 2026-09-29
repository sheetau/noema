"""Reproducible source-unit inventory for the complete two-work evaluation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from noema.source_units import segment

ROOT = Path('artifacts/written-units-v1')
REPORT = Path('reports/written-units-v1.json')
MANIFEST = Path('reports/written-sources-v1.json')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    sources = json.loads(MANIFEST.read_text(encoding='utf-8'))['sources']
    report = {'source_manifest_sha256': sha(MANIFEST),
              'code_sha256': {p: sha(p) for p in ('noema/source_units.py', 'scripts/segment_written_sources.py')},
              'scope': 'Loss accounting inside selected rendered work boundaries; facsimile review and Noema semantic alignment are pending',
              'works': {}}
    if not args.verify_only:
        if REPORT.exists():
            raise FileExistsError(REPORT)
        ROOT.mkdir(parents=True, exist_ok=False)
    for record in sources:
        path = Path(record['snapshot'])
        if sha(path) != record['sha256']:
            raise ValueError('Source snapshot changed')
        result = segment(path.read_text(encoding='utf-8'), record['id'])
        output = ROOT / (record['id'] + '.json')
        if args.verify_only:
            if result != json.loads(output.read_text(encoding='utf-8')):
                raise ValueError('Source segmentation replay differs')
        else:
            with output.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
        report['works'][record['id']] = {
            'source_sha256': record['sha256'], 'units_artifact': output.as_posix(), 'units_sha256': sha(output),
            'counts': dict(Counter(u['kind'] for u in result['units'])), 'audit': result['audit'],
            'page_markers': [a['source_id'] for a in result['annotations'] if a['kind'] == 'page'],
            'inventory': [{'id': u['id'], 'kind': u['kind'], 'text_sha256': u['text_sha256'], 'math_ids': u['math_ids']}
                          for u in result['units']],
            'required_units': sum(u['kind'] != 'editorial' for u in result['units']),
            'noema_verified_units': 0}
        print(record['id'], report['works'][record['id']]['counts'], 'MathML:', len(result['math']), flush=True)
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Source inventory replay differs')
        print('Source units and report replay exactly; no claim of translation completion')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')


if __name__ == '__main__':
    main()
