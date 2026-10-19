"""Preserve primary dictionary pages as UTF-8 JSON; never fetch during tests."""
from datetime import datetime,timezone
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
PATH='data/appointed-roles-evidence-v1.json'
URLS=['https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_2_0_'+s for s in ('955','956')]

def entry(html):
    return ' '.join(unescape(re.sub('<[^>]*>',' ',html.split('<h2 class="content">',1)[1].split('<form',1)[0])).split())

def validate(record):
    assert [p['url'] for p in record['pages']]==URLS
    for p in record['pages']:
        assert sha256(p['original_html'].encode(p['original_encoding'])).hexdigest()==p['original_bytes_sha256']
        assert entry(p['original_html'])==p['entry_text']
    assert 'zum öffentlichen Gottesdienste bestellet' in record['pages'][0]['entry_text']
    assert 'zur Besorgung des öffentlichen Gottesdienstes bestellten Personen' in record['pages'][1]['entry_text']
    return True

def main():
    path=ROOT/PATH
    if path.exists():
        validate(json.loads(path.read_text(encoding='utf-8')));print('Stored primary pages validated');return
    pages=[]
    for url in URLS:
        with urlopen(url,timeout=30) as response:
            raw=response.read();assert response.status==200
            html=raw.decode('iso-8859-1')
            pages.append(dict(url=url,final_url=response.url,retrieved_at=datetime.now(timezone.utc).isoformat(),
                original_encoding='iso-8859-1',original_bytes_sha256=sha256(raw).hexdigest(),
                original_html=html,entry_text=entry(html)))
    record=dict(status='primary_dictionary_transcriptions_not_kant_intent_proof',pages=pages)
    validate(record)
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print('Primary dictionary evidence stored',flush=True)

if __name__=='__main__':main()
