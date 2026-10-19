"""Retain a short grammatical excerpt and reuse the pinned historical Ja entry."""
from datetime import datetime,timezone
from hashlib import sha256
from html import unescape
import json,re
from urllib.request import urlopen
from scripts.fetch_pastoral_role_evidence import ROOT
from scripts.fetch_recognizable_consequence_evidence import validate as validate_prior

PATH='data/insistent-framing-evidence-v1.json'
PRIOR='data/recognizable-consequence-evidence-v1.json'
URL='https://grammis.ids-mannheim.de/systematische-grammatik/1322'
EXCERPT='Die abtönende Wirkung kann aber auch eine Verstärkung sein.'
EXAMPLE='Mach das ja nicht noch einmal'


def validate(record):
    prior=json.loads((ROOT/PRIOR).read_text(encoding='utf-8'));validate_prior(prior)
    assert record['historical_evidence']==PRIOR
    assert record['historical_evidence_sha256']==sha256((ROOT/PRIOR).read_bytes()).hexdigest()
    assert 'Sage es ja niemanden.' in prior['historical']['entry_text']
    assert 'eine vertrauliche und angelegentliche Bitte, wie auch ein Verboth' in prior['historical']['entry_text']
    g=record['grammar'];assert g['url']==g['final_url']==URL
    assert g['excerpt']==EXCERPT and g['example']==EXAMPLE and len((EXCERPT+' '+EXAMPLE).split())<=25
    assert g['retained_text_sha256']==sha256((EXCERPT+'\n'+EXAMPLE).encode('utf-8')).hexdigest()
    assert len(g['retrieved_page_sha256'])==64 and not g['original_full_page_stored']
    return True


def main():
    p=ROOT/PATH
    if p.exists():validate(json.loads(p.read_text(encoding='utf-8')));return
    with urlopen(URL,timeout=30) as response:
        assert response.status==200
        raw=response.read();text=' '.join(unescape(re.sub('<[^>]*>',' ',raw.decode('utf-8'))).split())
        assert EXCERPT in text and EXAMPLE in text
        grammar=dict(url=URL,final_url=response.url,retrieved_at=datetime.now(timezone.utc).isoformat(),
            retrieved_page_sha256=sha256(raw).hexdigest(),excerpt=EXCERPT,example=EXAMPLE,
            retained_text_sha256=sha256((EXCERPT+'\n'+EXAMPLE).encode('utf-8')).hexdigest(),original_full_page_stored=False,
            evidence_limit='Only two short excerpts are retained. The full-page hash records a retrieval, not an offline-verifiable page.')
    record=dict(status='historical_and_modern_usage_not_unique_embedded_kant_reading_proof',
        historical_evidence=PRIOR,historical_evidence_sha256=sha256((ROOT/PRIOR).read_bytes()).hexdigest(),grammar=grammar)
    validate(record)
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print('Short grammatical evidence and historical provenance stored',flush=True)


if __name__=='__main__':main()
