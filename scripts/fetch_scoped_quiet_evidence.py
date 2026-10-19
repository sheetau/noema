"""Pin primary historical senses without treating them as Kant intent proof."""
from datetime import datetime,timezone
from hashlib import sha256
import json
from urllib.request import urlopen
from scripts.fetch_pastoral_role_evidence import ROOT,entry

PATH='data/scoped-quiet-evidence-v1.json'
URL='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009133_6_2_2115'


def validate(record):
    assert record['url']==record['final_url']==URL
    assert sha256(record['original_html'].encode(record['original_encoding'])).hexdigest()==record['original_bytes_sha256']
    assert entry(record['original_html'])==record['entry_text']
    assert record['entry_text'].startswith('Ruhig')
    for phrase in ('Sich ruhig verhalten','andern nicht beschwerlich seyn','Gemüthes und der Empfindungen'):
        assert phrase in record['entry_text']
    return True


def main():
    p=ROOT/PATH
    if p.exists():validate(json.loads(p.read_text(encoding='utf-8')));return
    with urlopen(URL,timeout=30) as response:
        assert response.status==200
        raw=response.read();html=raw.decode('iso-8859-1')
        record=dict(url=URL,final_url=response.url,retrieved_at=datetime.now(timezone.utc).isoformat(),
            original_encoding='iso-8859-1',original_bytes_sha256=sha256(raw).hexdigest(),original_html=html,
            entry_text=entry(html),status='historical_senses_not_unique_kant_reading_or_complete_definition')
    validate(record)
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print('Historical quietness senses stored',flush=True)


if __name__=='__main__':main()
