"""Recover folded expressions across physically separate ordered SVG pages."""
from functools import lru_cache
import hashlib,json
from scripts import kant_ordered_pages as pages,check_kant_item_runs as source
from scripts.kant_item_rows import split_rows,pack_rows
from scripts.kant_folded_flow import translate
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.kant_structural_trial import prepare as trial,report
from scripts.check_kant_spacing_prefix import pins as prior_pins
from scripts.kant_page_public_context import ROOT

BASELINE='reports/kant-folded-flow-v4.json'
OUT=ROOT/'output/kant-ordered-pages'
RUN=ROOT/'.noema-project/runs/kant-ordered-pages-v1'


def fixtures():return [r for r in source.fixtures() if r['key'] in ('scope-junction','saved-subsequence','across-rows')]
def cases():return [(r['key'],r['label'],r['source']) for r in fixtures()]


@lru_cache(maxsize=4)
def checked(index):
    fixture=fixtures()[index];baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    path='output/kant-folded-flow/'+fixture['key']+'.svg';raw=(ROOT/path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=baseline['source_sha256'][path]:raise ValueError('Saved folded ink changed')
    rows=split_rows(from_svg(raw.decode('utf-8')))
    drawings=pages.paginate(rows,400)
    svgs=[to_svg(translate(s,25+i*13,40+i*19)) for i,s in enumerate(drawings)]
    recovered=pages.decode_pages([list(reversed(from_svg(s))) for s in svgs],seed=fixture['seed'],include_spellings=True)
    if recovered!=fixture['source']:raise ValueError('Page transition changed native document or spellings')
    return dict(key=fixture['key'],label=fixture['label'],source=fixture['source'],svg=to_svg(pack_rows(rows)),
        physical_page_svgs=svgs,pages=len(drawings),rows=len(rows),original_svg=path,exact=True)


def pins():
    result=prior_pins()
    names={BASELINE,'scripts/kant_ordered_pages.py','scripts/check_kant_ordered_pages.py','tests/test_kant_ordered_pages.py',
           'docs/kant-ordered-pages.md',*('output/kant-folded-flow/'+r['key']+'.svg' for r in fixtures())}
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-ordered-pages-1',version='kant-ordered-pages-1',title='頁をまたいで同じ構文を読む',
        intro='頁順と実際の行端の線から継続し、頁境界でも引用・束縛・宣言を分断しません。',
        limits=['Ordered physical pages are part of the document; no arbitrary page numbers are encoded',
                'Not a checksum detecting every deletion/reordering of independently complete items',
                'Three structural examples; final body page composition remains'])


def build_report():return report(OUT,pins)
