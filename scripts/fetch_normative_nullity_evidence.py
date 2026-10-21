"""Pin the historical lexical evidence for null und nichtig."""
from datetime import datetime,timezone
from html import unescape
import json,re
from urllib.request import urlopen
from scripts.compose_grounded_step import ROOT
from noema.semantic_reviews import digest

URL='https://lexika.digitale-sammlungen.de/adelung//lemma/bsb00009133_2_0_887'
PATH='artifacts/normative-nullity-v1/adelung-nichtig.html'
RECORD='data/normative-nullity-evidence-v1.json'
ANCHOR='Etwas null und nichtig machen, völlig unkräftig.'

def validate(record):
    assert record['url']==URL and record['path']==PATH
    raw=(ROOT/PATH).read_bytes();assert digest(raw)==record['sha256']
    text=' '.join(unescape(re.sub('<[^>]+>',' ',raw.decode('utf-8'))).split())
    assert record['anchor']==ANCHOR and ANCHOR in text

def main():
    target=ROOT/RECORD
    if target.exists():validate(json.loads(target.read_text(encoding='utf-8')));return
    source=ROOT/PATH;source.parent.mkdir(parents=True,exist_ok=True)
    if not source.exists():
        with urlopen(URL,timeout=30) as response:source.write_bytes(response.read())
    record=dict(url=URL,path=PATH,sha256=digest(source.read_bytes()),retrieved_at=datetime.now(timezone.utc).isoformat(),
        title='Adelung, Grammatisch-kritisches Wörterbuch der Hochdeutschen Mundart, Nichtig, 485–486',anchor=ANCHOR,
        reading_ja='無効を強調する一まとまりとして読む補助根拠。現代法の無効の全効果や、カントの正当性の基準を辞書だけから導くものではない。原文の後続にある人間の本性・後続世代と承認への譲歩を踏まえ、正当な規範上の効力と事実上の強制を区別する。')
    validate(record)
    with target.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
