"""Small unchanged-ink junction checks, including lexical and scope boundaries."""
from functools import lru_cache
import hashlib, json
from scripts import kant_saved_item_join as joining, kant_folded_flow as folded, kant_ordered_pages as pages
from scripts import kant_public_fragment as writing, check_kant_statements as statements
from scripts.kant_incremental_dictionary import Reader, PublishedStatementReader
from scripts.kant_page_public_context import ROOT, inputs
from scripts.kant_structural_trial import prepare as trial, report
from scripts.check_kant_ordered_pages import pins as prior_pins
from scripts.visible_syntax_geometry import from_svg, to_svg

OUT = ROOT/'output/kant-saved-item-join'
RUN = ROOT/'.noema-project/runs/kant-saved-item-join-v2'
PREFIX = 'reports/kant-forty-body-prefix-v1.json'
BASELINE = 'reports/kant-presentation-spellings-v1.json'
DICTIONARY = 'output/kant-presentation-spellings/dictionary.json'
STATEMENTS = 'reports/kant-statements-v3.json'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def saved(path, evidence):
    raw = (ROOT/path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != read(evidence)['source_sha256'][path]:
        raise ValueError('Saved join input changed: '+path)
    return raw


@lru_cache(maxsize=1)
def fixtures():
    published = json.loads(saved(DICTIONARY, BASELINE))
    public = {r['statement']: r['public'] for r in inputs()['selected']}
    result = []
    for numbers in ((2, 3), (3, 4)):
        result.append(dict(key='kant-'+'-'.join(map(str, numbers)), label='保存本文 '+str(numbers),
            reader=PublishedStatementReader(published), records=[public[n] for n in numbers],
            shapes=[from_svg(saved(f'output/kant-forty-body-prefix/statement-{n}.svg', PREFIX).decode('utf-8')) for n in numbers],
            width=1420/.53))
    source = {k: s for k, _, s in statements.cases()}
    keys = ('sibling-binders', 'quote-boundary')
    result.append(dict(key='scope-junction', label='既存の束縛・引用・仮定を閉じて次の項目へ進む',
        reader=Reader(), records=[source[k] for k in keys],
        shapes=[from_svg(saved('output/kant-statements/'+k+'.svg', STATEMENTS).decode('utf-8')) for k in keys], width=700.))
    return result


def cases():
    return [(r['key'], r['label'], r['records']) for r in fixtures()]


@lru_cache(maxsize=3)
def checked(index):
    fixture = fixtures()[index]
    reader = fixture['reader']
    expected = reader.fork()
    for record in fixture['records']:
        expected.register(record)
    joined = joining.join(fixture['shapes'], reader=reader)
    svg = to_svg(joined['shapes'])
    actual, _ = writing.decode_run(list(reversed(from_svg(svg))), reader=reader)
    if actual.result(True) != expected.result(True):
        raise ValueError('Joined SVG differs from its saved source')
    folding = folded.fold(from_svg(svg), fixture['width'])
    page_svgs = [to_svg(s) for s in pages.paginate(folding['row_shapes'], 400.)]
    recovered = pages.decode_pages([list(reversed(from_svg(s))) for s in page_svgs], reader=reader, include_spellings=True)
    if recovered != expected.result(True):
        raise ValueError('Joined physical pages changed native syntax')
    return dict(key=fixture['key'], label=fixture['label'], svg=svg, source=fixture['records'],
        junctions=joined['junctions'], translations=joined['translations'],
        rows=len(folding['row_shapes']), pages=len(page_svgs), physical_page_svgs=page_svgs,
        folded_svg=to_svg(folding['shapes']), input_shapes=fixture['shapes'], exact=True)


def pins():
    result = prior_pins()
    names = {PREFIX, BASELINE, DICTIONARY, STATEMENTS,
        'scripts/kant_saved_item_join.py', 'scripts/check_kant_saved_item_join.py',
        'tests/test_kant_saved_item_join.py', 'docs/kant-saved-item-join.md',
        *('output/kant-forty-body-prefix/statement-'+str(n)+'.svg' for n in (2, 3, 4)),
        *('output/kant-statements/'+k+'.svg' for k in ('sibling-binders', 'quote-boundary'))}
    result.update({n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT, run_path=RUN, pins=pins, cases=cases, checked=checked,
        preserved=lambda _: None, preserved_count=0, schema='kant-saved-item-join-1',
        version='kant-saved-item-join-1', title='保存した本文を描き直さずに接続する',
        intro='円と内部の枝をそのまま保ち、接続・折返し・頁分割後も同じ項目列を読みます。',
        limits=['Three accepted junctions, not all 40 body junctions or final paragraph layout',
            'A cross-item lexical collision with unaligned seam endpoints is rejected by the bounded joiner',
            'Same published rails; only horizontal translation and joining strokes or existing lexical gaps',
            'A junction without an exact geometric reading fails; no hidden source map in the reader'])


def build_report():
    return report(OUT, pins)
