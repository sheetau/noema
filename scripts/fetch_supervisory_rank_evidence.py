"""Pin historical highest-supervision and direction-of-conduct entries."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from urllib.request import urlopen
from scripts.fetch_pastoral_role_evidence import ROOT, entry

PATH = 'data/supervisory-rank-evidence-v1.json'
SOURCES = {
    'Oberaufsicht': ('https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009133_3_0_22', 'die oberste Aufsicht über eine Sache'),
    'Aufsicht': ('https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009131_3_3_3699', 'Besonders die Bestimmung des Verhaltens anderer'),
}


def validate(record):
    assert set(record['entries']) == set(SOURCES)
    for name, (url, phrase) in SOURCES.items():
        r = record['entries'][name]
        assert r['url'] == url
        assert sha256(r['original_html'].encode(r['original_encoding'])).hexdigest() == r['original_bytes_sha256']
        assert entry(r['original_html']) == r['entry_text'] and phrase in r['entry_text']
    return True


def main():
    path = ROOT / PATH
    if path.exists(): validate(json.loads(path.read_text(encoding='utf-8'))); return
    record = dict(status='historical_highest_supervision_not_a_mandatory_intermediate_tier', entries={})
    for name, (url, _) in SOURCES.items():
        with urlopen(url, timeout=30) as response:
            assert response.status == 200
            raw = response.read(); html = raw.decode('iso-8859-1')
            record['entries'][name] = dict(url=url, final_url=response.url, retrieved_at=datetime.now(timezone.utc).isoformat(),
                original_encoding='iso-8859-1', original_bytes_sha256=sha256(raw).hexdigest(), original_html=html, entry_text=entry(html))
    validate(record)
    with path.open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    print('Historical supervision entries pinned', flush=True)


if __name__ == '__main__': main()
