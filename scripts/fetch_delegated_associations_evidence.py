"""Archive the historical church order once; checks never use the network."""
from datetime import datetime, timezone
from html import unescape
import json
import re
from urllib.request import Request, urlopen
from scripts.compose_grounded_step import ROOT
from noema.semantic_reviews import digest

EVIDENCE = 'data/delegated-associations-evidence-v1.json'
SOURCES = (
    ('dordrecht-1619', 'https://kerkrecht.nl/node/2149/'),
    ('classicale-acta', 'https://www.huygens.knaw.nl/resources/classicale-acta-1573-1620/'),
)


def plain(html):
    html = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', html, flags=re.S | re.I)
    return ' '.join(unescape(re.sub('<[^>]*>', ' ', html)).split())


def validate(record):
    assert [p['url'] for p in record['sources']] == [url for _, url in SOURCES]
    for p in record['sources']:
        raw = (ROOT / p['path']).read_bytes()
        assert digest(raw) == p['sha256']
        text = plain(raw.decode(p['encoding']))
        for phrase in p['verified_search_phrases']: assert phrase in text, phrase
    source = record['source']
    unit = next(u for u in json.loads((ROOT / source['inventory']).read_text(encoding='utf-8'))['units'] if u['id'] == source['unit'])
    assert unit['text_sha256'] == source['unit_sha256'] and unit['text'][:409] == source['text']
    page = record['primary_page']; assert digest((ROOT / page['path']).read_bytes()) == page['sha256']


def main():
    path = ROOT / EVIDENCE
    if path.exists():
        validate(json.loads(path.read_text(encoding='utf-8'))); print('Stored evidence validated'); return
    folder = ROOT / 'artifacts/delegated-associations-v1'; folder.mkdir(parents=True, exist_ok=True)
    sources = []
    for stem, url in SOURCES:
        with urlopen(Request(url, headers={'User-Agent': 'Noema source review'}), timeout=30) as response:
            raw = response.read(); encoding = response.headers.get_content_charset() or 'utf-8'
            target = folder / (stem + '.html')
            if target.exists(): assert target.read_bytes() == raw
            else: target.write_bytes(raw)
            sources.append(dict(url=url, final_url=response.url, path=target.relative_to(ROOT).as_posix(), encoding=encoding,
                retrieved_at=datetime.now(timezone.utc).isoformat(), sha256=digest(raw)))
    # Tiny search anchors, not excerpts presented as a translation of Kant.
    sources[0].update(verified_search_phrases=['XLI.', 'eenen Dienaer ende eenen Ouderling', 'met behoorlijcke Credentie'],
        reading_ja='ドルト教会規則第41条は、近隣の諸教会から牧師と長老を信任状付きで送る会議を規定する。牧師だけの構成としない。第33条の信任と第36条の制度段階も後続の読解で参照できる。')
    sources[1].update(verified_search_phrases=['bestuurlijke middenniveau', 'plaatselijke kerkenraad', 'provinciale synode'],
        reading_ja='史料編纂機関の説明は、classisを地方教会の会議と州のsynodeの間に位置する教会統治の会議としている。地域的な代表会議を読む補助資料であり、カントの全意図の証明ではない。')
    inventory = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inventory).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    record = dict(status='historical_constituency_evidence_not_whole_sentence_review', sources=sources,
        source=dict(inventory=inventory, unit=unit['id'], unit_sha256=unit['text_sha256'], range=[0,409], text=unit['text'][:409]),
        primary_page=dict(path='artifacts/spiritual-guardians-v1/page-488.jpg',
            sha256='59aea30d7cb2baa22795dbfb0fcab14a40704421f042bcfbef335a8677de943a',
            url='https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00528/full/full/0/default.jpg'))
    validate(record)
    with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print('Historical representation evidence stored')


if __name__ == '__main__': main()
