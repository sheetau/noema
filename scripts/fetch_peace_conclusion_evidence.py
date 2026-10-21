"""Preserve the historical dictionary senses of concluding peace."""
from datetime import datetime,timezone
from html import unescape
import json,re
from urllib.request import urlopen
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT

RECORD='data/peace-conclusion-evidence-v1.json'
SOURCES=(
 ('friedensschluss','https://lexika.digitale-sammlungen.de/adelung//lemma/bsb00009132_1_2_2776',
  'zwischen Mächten, welche bis dahin in Kriege verwickelt gewesen',
  'Adelung, Der Friedensschluß, 305–306','従前に戦争にあった勢力の間の和平締結とそれを含む文書を説明する。合意とその文書の読みを結ぶ根拠。'),
 ('friede','https://lexika.digitale-sammlungen.de/adelung//lemma/bsb00009132_1_2_2757',
  'die Wiederherstellung der öffentlichen Ruhe zwischen Staaten nach vorher gegangenem Kriege',
  'Adelung, Der Friede, 303–304','従前の戦争の後の国家間の公的な平穏の回復と、そのための合意という語義を採る。後の条約の履行や道徳的正当性を辞書から推定しない。'),
)

def validate(record):
    assert len(record['sources'])==len(SOURCES)
    for row,(key,url,anchor,title,reading) in zip(record['sources'],SOURCES):
        assert (row['key'],row['url'],row['anchor'],row['title'],row['reading_ja'])==(key,url,anchor,title,reading)
        assert row['path']=='artifacts/peace-conclusion-v1/'+key+'.html'
        raw=(ROOT/row['path']).read_bytes();assert digest(raw)==row['sha256']
        text=' '.join(unescape(re.sub('<[^>]+>',' ',raw.decode('utf-8'))).split());assert anchor in text

def main():
    path=ROOT/RECORD
    if path.exists():validate(json.loads(path.read_text(encoding='utf-8')));return
    rows=[]
    for key,url,anchor,title,reading in SOURCES:
        target=ROOT/('artifacts/peace-conclusion-v1/'+key+'.html');target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with urlopen(url,timeout=30) as response:target.write_bytes(response.read())
        rows.append(dict(key=key,url=url,anchor=anchor,title=title,reading_ja=reading,path=target.relative_to(ROOT).as_posix(),sha256=digest(target.read_bytes())))
    record=dict(retrieved_at=datetime.now(timezone.utc).isoformat(),sources=rows);validate(record)
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
