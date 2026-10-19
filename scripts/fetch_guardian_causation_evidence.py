"""Preserve care/arrangement usage without claiming success from the verb alone."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from urllib.request import urlopen
from scripts.fetch_pastoral_role_evidence import ROOT, entry

PATH = 'data/guardian-causation-evidence-v1.json'
URL = 'https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_2_1_1140'


def validate(record):
    assert record['url'] == URL
    assert sha256(record['original_html'].encode(record['original_encoding'])).hexdigest() == record['original_bytes_sha256']
    assert entry(record['original_html']) == record['entry_text']
    for phrase in ('Sorgen', 'ernstlich darauf bedacht seyn, es zu veranstalten suchen', 'Dafür laß mich sorgen.'):
        assert phrase in record['entry_text']
    return True


def main():
    path = ROOT / PATH
    if path.exists():
        validate(json.loads(path.read_text(encoding='utf-8'))); print('Stored Sorgen entry validated'); return
    with urlopen(URL, timeout=30) as response:
        assert response.status == 200
        raw = response.read(); html = raw.decode('iso-8859-1')
        record = dict(url=URL, final_url=response.url, retrieved_at=datetime.now(timezone.utc).isoformat(),
            status='historical_usage_includes_effort_not_an_automatic_success_entailment', original_encoding='iso-8859-1',
            original_bytes_sha256=sha256(raw).hexdigest(), original_html=html, entry_text=entry(html))
    validate(record)
    with path.open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    print('Historical Sorgen evidence stored', flush=True)


if __name__ == '__main__': main()
