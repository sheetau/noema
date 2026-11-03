"""Read saved complete row previews as pages, not an externally split SVG list."""
from functools import lru_cache
import hashlib,json
from scripts import check_kant_incremental_dictionary as prior
from scripts.kant_item_rows import decode_page,split_rows,pack_rows
from scripts.visible_syntax_geometry import from_svg
from scripts.kant_page_public_context import ROOT
from scripts.kant_structural_trial import prepare as trial,report
from scripts.kant_public_fragment import VERSION

OUT=ROOT/'output/kant-item-rows'
RUN=ROOT/'.noema-project/runs/kant-item-rows-v1'
BASELINE='reports/kant-incremental-dictionary-v2.json'


def cases():return prior.cases()


@lru_cache(maxsize=8)
def checked(index):
    key,label,source=cases()[index]
    old=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    path='output/kant-incremental-dictionary/'+key+'.svg';raw=(ROOT/path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=old['source_sha256'][path]:raise ValueError('Saved page ink changed')
    svg=raw.decode('utf-8');shapes=list(reversed(from_svg(svg)))
    if decode_page(shapes)!=source:raise ValueError('Page geometry changed document')
    before=next(d for d in old['diagnostics'] if d['key']==key)
    return dict(key=key,label=label,source=source,svg=svg,width=before['width'],
        syntax_sha256=before['syntax_sha256'],circles=before['circles'],branches=before['branches'],
        recovered_rows=len(split_rows(shapes)),expected_items=before['items'],
        input_boundaries='Recovered from blank horizontal bands in one SVG; no groups or item-order metadata',
        original_svg=path)


def pins():
    result=prior.pins()
    for path in (BASELINE,'scripts/kant_item_rows.py','scripts/check_kant_item_rows.py',
                 'tests/test_kant_item_rows.py','docs/kant-page-item-boundaries.md',
                 *('output/kant-incremental-dictionary/'+k+'.svg' for k,_,_ in cases())):
        result[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-item-rows-1',version=VERSION,title='一枚のSVGから宣言と本文を順に読む',
        intro='保存済みの図形を再描画せず、空白帯から行を分けて未知の語と依存順を復元します。',
        limits=['One item per row; no line wrapping, multiple items per row or page continuation',
                'Wide row spacing is provisional, not final Kant page appearance or writing freeze'])


def build_report():return report(OUT,pins)
