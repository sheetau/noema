"""Keep rendered source snapshots for the two full-work language evaluations.

HTML is data only. A page revision does not freeze transcluded subpages; the
complete received bytes are hashed. Segmentation and facsimile review follow.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path('artifacts/written-sources-v1')
MANIFEST = Path('reports/written-sources-v1.json')
SOURCES = [
    {'id': 'einstein-1905', 'author': 'Albert Einstein', 'year': 1905,
     'title': 'Zur Elektrodynamik bewegter Körper',
     'url': 'https://de.wikisource.org/wiki/Zur_Elektrodynamik_bewegter_K%C3%B6rper',
     'publication': 'Annalen der Physik 17, 891–921'},
    {'id': 'kant-1784', 'author': 'Immanuel Kant', 'year': 1784,
     'title': 'Beantwortung der Frage: Was ist Aufklärung?',
     'url': 'https://de.wikisource.org/wiki/Beantwortung_der_Frage:_Was_ist_Aufkl%C3%A4rung%3F',
     'publication': 'Berlinische Monatsschrift 4, 481–494'},
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    if args.verify_only:
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        for record in manifest['sources']:
            raw = Path(record['snapshot']).read_bytes()
            if len(raw) != record['bytes'] or digest(raw) != record['sha256']:
                raise ValueError('Written source snapshot changed')
            raw.decode('utf-8')
        print('Two source snapshots verified; no claim of semantic coverage')
        return
    ROOT.mkdir(parents=True, exist_ok=False)
    if MANIFEST.exists():
        raise FileExistsError(MANIFEST)
    records = []
    for source in SOURCES:
        request = urllib.request.Request(source['url'], headers={'User-Agent': 'NoemaResearch/0.8 (local literary evaluation)'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw, final_url = response.read(), response.url
        html = raw.decode('utf-8')
        if 'mw-parser-output' not in html:
            raise ValueError('Missing rendered source body')
        revision = re.search(r'"wgRevisionId"\s*:\s*(\d+)', html)
        path = ROOT / (source['id'] + '.html')
        with path.open('xb') as stream:
            stream.write(raw)
        records.append({**source, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                        'final_url': final_url, 'page_revision': int(revision[1]) if revision else None,
                        'snapshot': path.as_posix(), 'bytes': len(raw), 'sha256': digest(raw),
                        'facsimile_review': 'pending', 'segmentation': 'pending',
                        'noema_full_text': 'not_started', 'source_language': 'de'})
        print(source['id'], len(raw), 'bytes saved', flush=True)
    with MANIFEST.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump({'scope': 'Rendered HTML snapshots, including site metadata and editorial apparatus; not yet a verified author-text corpus',
                   'source_notice': 'Original works dated 1905 and 1784. Retain Wikisource attribution and linked license notices for editorial/transcription contributions.',
                   'sources': records}, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
