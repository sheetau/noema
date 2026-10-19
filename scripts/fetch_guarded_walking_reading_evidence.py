"""Pin historical lexical evidence; tests only read the stored public-domain entries."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from urllib.request import urlopen
from scripts.fetch_pastoral_role_evidence import ROOT, entry

PATH='data/guarded-walking-reading-evidence-v1.json'
ENTRIES={
    'gehen':('bsb00009132_2_0_858','den Ort vermittelst der Füße verändern'),
    'vieh':('bsb00009134_5_1_1140','Hunde und Katzen'),
    'geschoepf':('bsb00009132_2_1_1648','im Scherze oder aus Verachtung von Personen'),
    'zahm':('bsb00009134_9_0_45','Bienen'),
}


def validate(record):
    assert set(record['pages'])==set(ENTRIES)
    for name,(suffix,marker) in ENTRIES.items():
        page=record['pages'][name]
        assert page['url']=='https://lexika.digitale-sammlungen.de/adelung/lemma/'+suffix
        assert sha256(page['original_html'].encode(page['original_encoding'])).hexdigest()==page['original_bytes_sha256']
        assert entry(page['original_html'])==page['entry_text'] and marker in page['entry_text']
    return True


def main():
    path=ROOT/PATH
    if path.exists():
        validate(json.loads(path.read_text(encoding='utf-8')));print('Stored lexical evidence validated');return
    pages={}
    for name,(suffix,_) in ENTRIES.items():
        url='https://lexika.digitale-sammlungen.de/adelung/lemma/'+suffix
        with urlopen(url,timeout=30) as response:
            assert response.status==200
            raw=response.read();html=raw.decode('iso-8859-1')
            pages[name]=dict(url=url,final_url=response.url,retrieved_at=datetime.now(timezone.utc).isoformat(),
                original_encoding='iso-8859-1',original_bytes_sha256=sha256(raw).hexdigest(),
                original_html=html,entry_text=entry(html))
        print(name+' fetched',flush=True)
    record=dict(status='historical_lexical_evidence_not_proof_of_unique_kant_reading',pages=pages)
    validate(record)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
