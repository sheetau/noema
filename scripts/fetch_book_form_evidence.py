"""Preserve the historical book entry used for the carrier-form interpretation."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from urllib.request import urlopen
from scripts.fetch_pastoral_role_evidence import ROOT, entry

PATH = 'data/book-form-evidence-v1.json'
URL = 'https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009131_4_4_4406'


def validate(record):
    assert record['url'] == URL
    assert sha256(record['original_html'].encode(record['original_encoding'])).hexdigest() == record['original_bytes_sha256']
    assert entry(record['original_html']) == record['entry_text']
    for text in ('zu einem Ganze verbundene Blätter', 'zu einem künftigen Buche bestimmt',
                 'ungebundenes Buch', 'gewissen größern Umfang'):
        assert text in record['entry_text']
    return True


def main():
    path = ROOT / PATH
    if path.exists():
        validate(json.loads(path.read_text(encoding='utf-8')))
        print('Stored book entry validated')
        return
    with urlopen(URL, timeout=30) as response:
        assert response.status == 200
        raw = response.read(); html = raw.decode('iso-8859-1')
        record = dict(url=URL, final_url=response.url, retrieved_at=datetime.now(timezone.utc).isoformat(),
            status='historical_lexical_evidence_not_authorial_intent_proof',
            original_encoding='iso-8859-1', original_bytes_sha256=sha256(raw).hexdigest(),
            original_html=html, entry_text=entry(html))
    validate(record)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print('Book entry stored', flush=True)


if __name__ == '__main__':
    main()
