"""Fetch one pinned annotation release and preserve source bytes and licensing."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

from noema.definition_probe import digest
from noema.semantics import require
from noema.wic_tsv_data import REVISION, REPOSITORY, parse_split, audit
from scripts.prepare_reference_corpus import write

ROOT = Path('artifacts/wic-tsv-source-v1')
REPORT = Path('reports/wic-tsv-source-v1')
FILES = ['LICENSE', 'data/README.md', 'data/en/LICENSE'] + [
    f'data/en/{folder}/{prefix}_{kind}.txt' for folder, prefix in (('Training', 'train'), ('Development', 'dev'))
    for kind in ('examples', 'definitions', 'labels')]


def read_source(root):
    return {prefix: parse_split(*[(root / f'data/en/{folder}/{prefix}_{kind}.txt').read_text(encoding='utf-8')
                                  for kind in ('examples', 'definitions', 'labels')], prefix)
            for folder, prefix in (('Training', 'train'), ('Development', 'dev'))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    sources = {p: digest(p) for p in ('noema/wic_tsv_data.py', 'scripts/prepare_wic_tsv.py')}
    if args.verify_only:
        manifest = json.loads((REPORT / 'manifest.json').read_text(encoding='utf-8'))
        require(manifest['code_sha256'] == sources, 'WiC adapter source changed')
        for path, sha in manifest['files_sha256'].items():
            require(digest(ROOT / path) == sha, 'WiC source or converted data changed')
    else:
        ROOT.mkdir(parents=True, exist_ok=False)
        REPORT.mkdir(parents=True, exist_ok=False)
        for name in FILES:
            url = f'https://raw.githubusercontent.com/{REPOSITORY}/{REVISION}/{name}'
            request = Request(url, headers={'User-Agent': 'Noema annotation research'})
            with urlopen(request, timeout=60) as response:
                data = response.read()
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as out:
                out.write(data)
    rows = read_source(ROOT)
    report = audit(rows)
    if args.verify_only:
        require(report == json.loads((REPORT / 'audit.json').read_text(encoding='utf-8')), 'WiC audit changed')
        for name, values in rows.items():
            require(values == json.loads((ROOT / f'{name}.json').read_text(encoding='utf-8')), 'WiC conversion changed')
        write(REPORT / 'verification.json', {'source_reparsed': True, 'rows': {k: len(v) for k, v in rows.items()},
                                            'code_sha256': sources})
    else:
        for name, values in rows.items():
            write(ROOT / f'{name}.json', values)
        write(REPORT / 'audit.json', report)
        write(REPORT / 'manifest.json', {'repository': f'https://github.com/{REPOSITORY}', 'revision': REVISION,
              'paper': 'https://aclanthology.org/2021.eacl-main.140/', 'data_license': 'CC-BY-4.0', 'repository_code_license': 'MIT',
              'attribution': 'Anna Breit, Artem Revenko, Kiamehr Rezaee, Mohammad Taher Pilehvar, Jose Camacho-Collados. WiC-TSV (EACL 2021).',
              'conversion': 'word indices to exact original character spans; definitions and labels preserved; no Noema mapping',
              'code_sha256': sources, 'files_sha256': {p: digest(ROOT / p) for p in [*FILES, 'train.json', 'dev.json']}})
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
