"""Fetch a fixed public GlossReader checkpoint; validate every range and the full checksum."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request

from noema.definition_probe import digest
from noema.semantics import require
from scripts.prepare_reference_corpus import write

ROOT = Path('artifacts/glossreader-source-v1')
REPORT = Path('reports/glossreader-source-v1')
URL = 'https://zenodo.org/api/records/10530146/files/best_model.ckpt/content'
SIZE = 4479483789
MD5 = 'fe0f589ab57e36e6eb88667ccf697742'
REVISION = '08f8a6141faa43f5ba84bbace8a9688e9ed22ae2'
SOURCE_URL = f'https://raw.githubusercontent.com/deniskokosss/deepchange_at_axolotl/{REVISION}/'


def file_md5(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'md5').hexdigest()


def fetch_segment(segment):
    a, b = segment['start'], segment['end']
    output = ROOT / segment['file']
    if output.exists():
        require(output.stat().st_size == b - a + 1, 'Existing segment length differs')
        return segment
    partial = output.with_suffix('.download')
    header = output.with_suffix('.headers')
    subprocess.run(['curl.exe', '--fail', '--silent', '--show-error', '--location', '--connect-timeout', '20',
                    '--speed-time', '120', '--speed-limit', '1024', '--range', f'{a}-{b}', '--max-filesize', str(b-a+1),
                    '--dump-header', str(header), '--output', str(partial), URL], check=True)
    headers = header.read_text(encoding='utf-8').lower()
    require(re.search(rf'content-range: bytes {a}-{b}/{SIZE}\s', headers) is not None, 'Server ignored requested range')
    require(partial.stat().st_size == b - a + 1, 'Incomplete model segment')
    partial.rename(output)
    return segment


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    record = ROOT / 'record.json'
    if not record.exists():
        subprocess.run(['curl.exe', '--fail', '--silent', '--show-error', '--connect-timeout', '20', '--max-time', '60',
                        '--output', str(record), 'https://zenodo.org/api/records/10530146'], check=True)
    metadata = json.loads(record.read_text(encoding='utf-8'))
    require(metadata['id'] == 10530146 and metadata['metadata']['license']['id'] == 'cc-by-4.0', 'Wrong model record or license')
    entry = next(f for f in metadata['files'] if f['key'] == 'best_model.ckpt')
    require(entry['size'] == SIZE and entry['checksum'] == 'md5:' + MD5 and entry['links']['self'] == URL,
            'Model source metadata changed')
    checkpoint = ROOT / 'best_model.ckpt'
    if args.verify_only:
        manifest = json.loads((REPORT / 'manifest.json').read_text(encoding='utf-8'))
        for name, sha in manifest['files_sha256'].items():
            require(digest(ROOT / name) == sha, 'GlossReader source changed')
        require(checkpoint.stat().st_size == SIZE and file_md5(checkpoint) == MD5, 'Full checkpoint checksum differs')
        write(REPORT / 'verification.json', {'size': SIZE, 'official_md5_exact': True, 'all_source_sha256_exact': True})
        print('GlossReader source verification passed', flush=True)
        return
    require(not REPORT.exists(), 'Source report already exists')
    if not checkpoint.exists():
        partition_path = ROOT / 'download-partition.json'
        if partition_path.exists():
            partition = json.loads(partition_path.read_text(encoding='utf-8'))
            require(partition['url'] == URL and partition['size'] == SIZE and partition['md5'] == MD5, 'Download identity changed')
        else:
            prefix = ROOT / 'best_model.ckpt.part'
            n = prefix.stat().st_size if prefix.exists() else 0
            require(0 <= n <= SIZE, 'Invalid retained prefix length')
            require(shutil.disk_usage(ROOT).free >= 2 * SIZE, 'Insufficient space for checkpoint assembly')
            segments = [{'start': a, 'end': min(a + 64 * 1024**2, SIZE) - 1, 'file': f'segment-{i:03d}.bin'}
                        for i, a in enumerate(range(n, SIZE, 64 * 1024**2))]
            partition = {'url': URL, 'size': SIZE, 'md5': MD5, 'prefix_bytes': n,
                         'prefix_sha256': digest(prefix) if n else None, 'segments': segments}
            write(partition_path, partition)
        prefix = ROOT / 'best_model.ckpt.part'
        if partition['prefix_bytes']:
            require(prefix.stat().st_size == partition['prefix_bytes'] and digest(prefix) == partition['prefix_sha256'],
                    'Retained prefix changed; stop any old download first')
        done = partition['prefix_bytes']
        with ThreadPoolExecutor(max_workers=8) as pool:
            tasks = [pool.submit(fetch_segment, segment) for segment in partition['segments']]
            for future in as_completed(tasks):
                segment = future.result()
                done += segment['end'] - segment['start'] + 1
                print('GlossReader bytes', done, '/', SIZE, flush=True)
        assembled = ROOT / 'assembled.part'
        with assembled.open('wb') as destination:
            paths = ([prefix] if partition['prefix_bytes'] else []) + [ROOT / s['file'] for s in partition['segments']]
            for path in paths:
                with path.open('rb') as source:
                    shutil.copyfileobj(source, destination, length=8 * 1024**2)
        require(assembled.stat().st_size == SIZE and file_md5(assembled) == MD5, 'Full downloaded checksum differs')
        assembled.rename(checkpoint)
    require(checkpoint.stat().st_size == SIZE and file_md5(checkpoint) == MD5, 'Existing checkpoint checksum differs')
    source_names = ['LICENSE', 'README.md', 'code/gr_vectorize.py', 'code/gr_wsd.py', 'code/repro.sh']
    for name in source_names:
        target = ROOT / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(SOURCE_URL + name, timeout=30) as response, target.open('xb') as output:
                output.write(response.read())
    REPORT.mkdir(parents=True)
    files = ['record.json', 'best_model.ckpt', *source_names]
    write(REPORT / 'manifest.json', {'record': 'https://zenodo.org/records/10530146', 'doi': '10.5281/zenodo.10530146',
          'license': 'CC BY 4.0', 'creators': metadata['metadata']['creators'], 'title': metadata['title'],
          'size': SIZE, 'official_md5': MD5, 'code_revision': REVISION, 'code_license': 'Apache-2.0',
          'files_sha256': {name: digest(ROOT / name) for name in files}})
    print('GlossReader checkpoint prepared and verified', flush=True)


if __name__ == '__main__':
    main()
