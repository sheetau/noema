"""Pin the historical lexical distinction between promise and solemn invocation."""
from datetime import datetime, timezone
from html import unescape
import json
import re
from urllib.request import urlopen
from scripts.compose_grounded_step import ROOT
from noema.semantic_reviews import digest

URL='https://lexika.digitale-sammlungen.de/adelung//lemma/bsb00009133_7_3_3548'
PATH='artifacts/promissory-oath-v1/adelung-schwoeren.html'
RECORD='data/promissory-oath-evidence-v1.json'
ANCHOR='Gott feyerlich zum Zeugen der Wahrheit und Rächer des Betruges anrufen'


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
        title='Adelung, Grammatisch-kritisches Wörterbuch der Hochdeutschen Mundart, Schwören, 1757–1758',anchor=ANCHOR,
        reading_ja='宗教的な宣誓では、厳粛な表明に、真実の証人と不誠実への裁き手を呼ぶ働きがあるという採用解釈の補助根拠。1784年のこの文で実際に用いる文言、呼びかけ先の固有名、制裁の種類、全文化の宣誓の必要十分条件を指定する証拠ではない。約束については将来の履行と表明の誠実さを区別し、履行の単なる不成功を故意の裏切りに置き換えない。')
    validate(record)
    with target.open('x',encoding='utf-8',newline='\n') as out:out.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print('Historical oath evidence stored')


if __name__=='__main__':main()
