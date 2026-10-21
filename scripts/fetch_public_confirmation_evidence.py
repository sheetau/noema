"""Preserve lexical and institutional sources used by public confirmation."""
from datetime import datetime,timezone
from html import unescape
import json,re
from urllib.request import urlopen
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT

RECORD='data/public-confirmation-evidence-v1.json'
SOURCES=(
 ('obrigkeit','https://lexika.digitale-sammlungen.de/adelung//lemma/bsb00009133_3_0_199',
  'Die höchste Obrigkeit, die hohe Landesobrigkeit, welche die höchste Gewalt in einem Lande hat.',
  'Adelung, Obrigkeit, 571–572','同じ国での最高権限とその担い手を読む補助根拠。政治的管轄の正当性を辞書から導かない。'),
 ('feyerlich','https://lexika.digitale-sammlungen.de/adelung//lemma/bsb00009132_1_1_1259',
  'Der Friede wurde sehr feyerlich bekannt gemacht.',
  'Adelung, Feyerlich, 139–140','重要な事柄を記憶させる付随的な言葉・儀礼・手続という語義と和平公示の用例を採る。最上級の比較方式はこの読解で明示する。'),
 ('reichsabschied','https://germanhistorydocs.org/de/das-heilige-roemische-reich-1648-1815/der-juengste-reichsabschied-von-1654-17-mai-1654',
  'mit gesamter Hand vollends beschlossen',
  'Der jüngste Reichsabschied von 1654, §§178–185, GHDI掲載転写',
  '帝国共通の事柄についての身分との審議・共同決定を一次史料本文で確認する。個別の防衛政策や税制、近代語への転写上の表記を1784年本文に追加しない。'),
)

def validate(record):
    assert len(record['sources'])==len(SOURCES)
    for row,(key,url,anchor,title,reading) in zip(record['sources'],SOURCES):
        assert (row['key'],row['url'],row['anchor'],row['title'],row['reading_ja'])==(key,url,anchor,title,reading)
        assert row['path']=='artifacts/public-confirmation-v1/'+key+'.html'
        raw=(ROOT/row['path']).read_bytes();assert digest(raw)==row['sha256']
        text=' '.join(unescape(re.sub('<[^>]+>',' ',raw.decode('utf-8'))).split())
        assert anchor in text

def main():
    path=ROOT/RECORD
    if path.exists():validate(json.loads(path.read_text(encoding='utf-8')));return
    rows=[]
    for key,url,anchor,title,reading in SOURCES:
        target=ROOT/('artifacts/public-confirmation-v1/'+key+'.html');target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with urlopen(url,timeout=30) as response:target.write_bytes(response.read())
        rows.append(dict(key=key,url=url,anchor=anchor,title=title,reading_ja=reading,path=target.relative_to(ROOT).as_posix(),sha256=digest(target.read_bytes())))
    record=dict(retrieved_at=datetime.now(timezone.utc).isoformat(),sources=rows);validate(record)
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
