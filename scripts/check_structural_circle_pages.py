"""Bounded continuation evidence; historical draft-one report is preserved."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json

from scripts.check_structural_circle import cases
from scripts.structural_circle import to_svg,from_svg
from scripts.structural_circle_pages import compile_pages,decode_pages

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/structural-circle-review'


@lru_cache(maxsize=1)
def specimens():
    document=cases()[8][2]
    rows=[]
    for payload in (1,3,7,19,96,512):
        pages=compile_pages(document,payload=payload)
        svgs=[to_svg(p['shapes']) for p in pages]
        if decode_pages(from_svg(s) for s in svgs)!=document:
            raise ValueError('Continued syntax differs')
        rows.append(dict(payload=payload,pages=len(svgs),svgs=svgs))
    return rows


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    sample=next(r for r in specimens() if r['payload']==19)
    cards=[]
    for i,svg in enumerate(sample['svgs']):
        name='continuation-'+str(i+1)+'.svg'
        (OUT/name).write_text(svg,encoding='utf-8',newline='\n')
        cards.append('<section><h2>継続見本 '+str(i+1)+' / '+str(sample['pages'])+'</h2><div>'+svg+'</div></section>')
    page='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>Noema 表記案の確認</title>
<style>body{font:17px/1.9 "Yu Gothic",sans-serif;max-width:1300px;margin:40px auto;padding:0 28px;background:#f4f2eb;color:#243c3e}a{color:#366367}.primary{display:block;background:#243c3e;color:white;padding:22px;text-decoration:none;border-radius:8px;font-size:23px}section{padding:24px;background:#fffdf8;margin:28px 0}section div{overflow:auto}svg{height:260px;width:auto;min-width:100%}h2{font-size:18px}p{max-width:920px}</style>
<h1>Noema — 固定前の表記案</h1>
<a class="primary" href="../structural-circle-draft-1/index.html">文の見た目・構造の比較と全字形一覧を開く →</a>
<p>小文書の共通規則と行・頁継続を実装した未固定の試案です。円の語形・意味を保持し、構文の親子を可視の枝で示します。二作品全体の最終描画はまだ行っていません。</p>
<p>確認していただきたい点は、文頭の共通形、構文ごとの分岐、直角と45度の選択、長い引用・束縛の見た目、許容字形の使われ方です。</p>
<h2>行・頁の継続</h2><p>下は境界を確認するため、短い文書を19字形ずつに分割した見本です。番号や継続位置も円文字で書くため、この極端な分割ではヘッダーの割合が大きくなります。大きい区画にまとめれば繰り返しを減らせます。枠の枝は区画の順序、本文の枝は構文の関係を表します。</p>
'''+''.join(cards)+'</html>\n'
    (OUT/'index.html').write_text(page,encoding='utf-8',newline='\n')


def build_report():
    baseline='reports/structural-circle-draft-v1.json'
    previous=json.loads((ROOT/baseline).read_text(encoding='utf-8'))
    # Reuse its unchanged exact scope; do not rerun its semantic/corpus history.
    for p,digest in previous['source_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest:
            raise ValueError('Draft-one dependency changed: '+p)
    pins=[baseline,'scripts/structural_circle_pages.py','scripts/check_structural_circle_pages.py',
          'tests/test_structural_circle_pages.py','docs/structural-circle-pages-draft-1.md']
    return dict(schema='noema-structural-circle-pages-evidence-1',status='draft-awaiting-visual-review',
                payloads=[dict(payload=r['payload'],pages=r['pages'],svg_sha256=[hashlib.sha256(s.encode('utf-8')).hexdigest() for s in r['svgs']]) for r in specimens()],
                inherited_evidence=baseline,limits=['No full manuscript output','No raster OCR','No authenticity certification','16384 tokens / 512 frames'],
                source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in pins})
