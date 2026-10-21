"""Pin archival title evidence; it corroborates form, not Kant's exact referent."""
from datetime import datetime, timezone
import json
from urllib.request import urlopen
from pypdf import PdfReader
from scripts.compose_grounded_step import ROOT
from noema.semantic_reviews import digest

URL='https://www.archive.nrw.de/sites/default/files/media/files/Duisburg_Classis_3__1736_1768.pdf'
PDF='artifacts/classis-title-v1/duisburg-1736-1768.pdf'
EVIDENCE='data/classis-title-evidence-v1.json'


def validate(record):
    assert record['url']==URL and digest((ROOT/PDF).read_bytes())==record['sha256']
    reader=PdfReader(ROOT/PDF)
    for item in record['anchors']:
        text=' '.join(reader.pages[item['pdf_page_index']].extract_text().split())
        assert item['text'] in text,item


def main():
    path=ROOT/EVIDENCE
    if path.exists():validate(json.loads(path.read_text(encoding='utf-8')));print('Stored title evidence validated');return
    target=ROOT/PDF;target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        with urlopen(URL,timeout=30) as response:target.write_bytes(response.read())
    record=dict(status='archival_honorific_usage_not_proof_of_dutch_identity_or_kant_intention',url=URL,path=PDF,
        retrieved_at=datetime.now(timezone.utc).isoformat(),sha256=digest(target.read_bytes()),
        title='Protokolle der reformierten Duisburger Klasse im 17. und 18. Jahrhundert, Band 3, 1736–1768; Erich Wittenborn',
        anchors=[dict(pdf_page_index=4,printed_page=5,text='veneranda [Classis], ehrwürdige Klasse'),
                 dict(pdf_page_index=50,printed_page=51,text='vener. Classis wird guthfinden')],
        reading_ja='編集者の略語表はvener.をveneranda [Classis]、ehrwürdige Klasseと説明し、記録本文でも敬称を伴うClassisへの言及がある。ehrwürdigを呼称の慣習的な敬意の形式として読む補助証拠。デュースブルクの史料をオランダそのものやカントの特定の参照先と同一視せず、これだけでカントの皮肉や心理的な敬愛を認定しない。')
    validate(record)
    with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print('Archival title evidence stored')


if __name__=='__main__':main()
