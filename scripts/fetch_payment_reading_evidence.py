"""Preserve historical condition and assurance uses; tests remain offline."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from urllib.request import urlopen
from scripts.fetch_pastoral_role_evidence import ROOT, entry

PATH = 'data/payment-reading-evidence-v1.json'
URLS = ['https://lexika.digitale-sammlungen.de/adelung/lemma/' + s for s in (
    'bsb00009133_2_1_1192', 'bsb00009133_7_2_2627')]


def validate(record):
    assert [p['url'] for p in record['pages']] == URLS
    for p in record['pages']:
        assert sha256(p['original_html'].encode(p['original_encoding'])).hexdigest() == p['original_bytes_sha256']
        assert entry(p['original_html']) == p['entry_text']
    assert '2) Eine Bedingung.' in record['pages'][0]['entry_text']
    assert 'Einen mit besorgendem Zweifel verbundenen Wunsch' in record['pages'][0]['entry_text']
    assert 'Es wird schon reichen.' in record['pages'][1]['entry_text']
    assert 'eine Versicherung in Rücksicht auf einen vorher gegangenen Ausspruch' in record['pages'][1]['entry_text']
    return True


def main():
    path = ROOT / PATH
    if path.exists():
        validate(json.loads(path.read_text(encoding='utf-8'))); print('Stored particle evidence validated'); return
    pages = []
    for url in URLS:
        with urlopen(url, timeout=30) as response:
            assert response.status == 200
            raw = response.read(); html = raw.decode('iso-8859-1')
            pages.append(dict(url=url, final_url=response.url, retrieved_at=datetime.now(timezone.utc).isoformat(),
                original_encoding='iso-8859-1', original_bytes_sha256=sha256(raw).hexdigest(),
                original_html=html, entry_text=entry(html)))
    record = dict(status='historical_uses_not_unique_source_reading_proof', pages=pages)
    validate(record)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print('Historical particle evidence stored', flush=True)


if __name__ == '__main__':
    main()
