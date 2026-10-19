"""Pin a historical entry and a short modern grammatical excerpt."""
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
import json
import re
from urllib.request import urlopen
from scripts.fetch_pastoral_role_evidence import ROOT, entry

PATH = 'data/recognizable-consequence-evidence-v1.json'
HISTORICAL = 'https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_5_0_2'
GRAMMAR = 'https://grammis.ids-mannheim.de/systematische-grammatik/1348'
EXCERPT = 'Ja besagt, dass der Sprecher den Sachverhalt als allgemein akzeptierte Tatsache versteht'


def validate(record):
    h, g = record['historical'], record['grammar']
    assert h['url'] == HISTORICAL and g['url'] == GRAMMAR
    assert sha256(h['original_html'].encode(h['original_encoding'])).hexdigest() == h['original_bytes_sha256']
    assert entry(h['original_html']) == h['entry_text']
    assert 'Wenn das ist, so haben sie ja nichts zu befürchten.' in h['entry_text']
    assert g['excerpt'] == EXCERPT and len(EXCERPT.split()) <= 25
    assert g['excerpt_sha256'] == sha256(EXCERPT.encode('utf-8')).hexdigest()
    assert len(g['retrieved_page_sha256']) == 64
    return True


def main():
    path = ROOT / PATH
    if path.exists():
        validate(json.loads(path.read_text(encoding='utf-8')))
        print('Stored particle evidence validated'); return
    with urlopen(HISTORICAL, timeout=30) as response:
        assert response.status == 200
        raw = response.read(); html = raw.decode('iso-8859-1')
        historical = dict(url=HISTORICAL, final_url=response.url, original_encoding='iso-8859-1',
            retrieved_at=datetime.now(timezone.utc).isoformat(), original_bytes_sha256=sha256(raw).hexdigest(),
            original_html=html, entry_text=entry(html))
    with urlopen(GRAMMAR, timeout=30) as response:
        assert response.status == 200
        raw = response.read(); html = raw.decode('utf-8')
        text = ' '.join(unescape(re.sub('<[^>]*>', ' ', html)).split())
        assert EXCERPT in text
        grammar = dict(url=GRAMMAR, final_url=response.url, retrieved_at=datetime.now(timezone.utc).isoformat(),
            retrieved_page_sha256=sha256(raw).hexdigest(), excerpt=EXCERPT,
            excerpt_sha256=sha256(EXCERPT.encode('utf-8')).hexdigest(),
            original_full_page_stored=False,
            evidence_limit='Only the short excerpt is retained. The full page hash records the retrieval, not an offline-verifiable saved page.')
    record = dict(status='historical_usage_and_modern_grammatical_evidence_not_unique_reading_proof', historical=historical, grammar=grammar)
    validate(record)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print('Particle evidence stored', flush=True)


if __name__ == '__main__':
    main()
