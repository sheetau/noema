"""Recover item boundaries and incremental names from connected circle rows."""
from functools import lru_cache
import hashlib,json
from scripts import check_kant_spelling_records as prior,check_kant_statements as statements
from scripts import kant_public_fragment as writing,kant_item_runs as runs
from scripts.kant_incremental_dictionary import Reader
from scripts.kant_item_rows import pack_rows
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_page_public_context import ROOT
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-item-runs'
RUN=ROOT/'.noema-project/runs/kant-item-runs-v2'
BASELINE='reports/kant-spelling-records-v1.json'


@lru_cache(maxsize=1)
def fixtures():
    result=[]
    a=lambda x:dict(kind='assert',body=x)
    book=prior.prior.call('book')
    red=prior.prior.call('red',book);round_=prior.prior.call('round',book)
    def add(key,label,records,groups=None,seed=None):
        reader=Reader(seed)
        for item in records:reader.register(item)
        result.append(dict(key=key,label=label,records=records,groups=groups or [len(records)],seed=seed,
                           source=reader.result(True)))
    add('adjacent','開始形を足さず複数の文を読む',
        [a(red),a(prior.prior.logic('equal',book,prior.prior.call('town'))),dict(kind='ask',body=red)])
    add('lexical-junction','文末と次の文頭の間で語の最長一致を止める',
        [a(red),a(round_)])
    saved={k:s for k,_,s in statements.cases()}
    add('scope-junction','仮定・引用・次の文の束縛を別々に閉じる',
        [saved['sibling-binders'],saved['quote-boundary'],saved['ask-question']])
    for key in ('later-definition','two-spellings','saved-semantic','saved-subsequence'):
        row=next(r for r in prior.fixtures() if r['key']==key)
        add(key,row['label'],row['records'],seed=row['seed'])
    row=next(r for r in prior.fixtures() if r['key']=='later-definition')
    add('across-rows','二つの項目を同じ行で読み、次行の依存先へ登録する',row['records'],[2,3])
    return result


def cases():return [(r['key'],r['label'],r['source']) for r in fixtures()]


@lru_cache(maxsize=16)
def checked(index):
    row=fixtures()[index];writer=Reader(row['seed']);drawings=[];offset=0
    for length in row['groups']:
        drawing,writer=runs.compile_run(row['records'][offset:offset+length],reader=writer,multiple=True)
        drawings.append(drawing);offset+=length
    assert offset==len(row['records'])
    svg=to_svg(pack_rows([d['shapes'] for d in drawings]))
    recovered=runs.decode_page(list(reversed(from_svg(svg))),seed=row['seed'],include_spellings=True)
    if recovered!=row['source']:raise ValueError('Connected item run changed native document or spellings')
    row_svgs=[to_svg(d['shapes']) for d in drawings]
    measurements=[measure(s) for s in row_svgs]
    return dict(key=row['key'],label=row['label'],source=row['source'],svg=svg,
        syntax_sha256=syntax_hash(recovered),items=len(row['records']),rows=len(drawings),
        items_per_row=row['groups'],width=max(d['width'] for d in drawings),
        row_svgs=row_svgs,circles=sum(m['circles'] for m in measurements),
        branches=sum(m['branches'] for m in measurements),row_measurements=measurements)


def preserved_count():return prior.preserved_count()+len(prior.fixtures())


@lru_cache(maxsize=80)
def preserved(index):
    if index<prior.preserved_count():return prior.preserved(index)
    fixture=prior.fixtures()[index-prior.preserved_count()]
    saved=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    path='output/kant-spelling-records/'+fixture['key']+'.svg'
    raw=(ROOT/path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=saved['source_sha256'][path]:raise ValueError('Preserved page changed')
    actual=runs.decode_page(list(reversed(from_svg(raw.decode('utf-8')))),seed=fixture['seed'],include_spellings=True)
    expected=dict(native=fixture['native'],spellings=fixture['spellings'])
    if actual!=expected:raise ValueError('Run reader changed old one-item rows')
    return dict(svg=path,syntax_sha256=syntax_hash(actual))


def pins():
    result=prior.pins()
    names={BASELINE,'scripts/kant_item_runs.py','scripts/check_kant_item_runs.py',
           'tests/test_kant_item_runs.py','docs/kant-item-runs.md',
           *('output/kant-spelling-records/'+r['key']+'.svg' for r in prior.fixtures())}
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,preserved_count=preserved_count(),
        schema='kant-item-runs-1',version=writing.VERSION,title='複数の項目を一行の円文字から読む',
        intro='項目の引数と終端から境界を復元し、先に読んだ宣言・綴りだけを後続に使います。',
        limits=['Complete items may share a row; long-item wrapping and page continuation remain',
                'Row width and blank bands are provisional; this is not a final visual approval candidate',
                'Explicit seed dependencies are allowed; recovered names and spellings are not preloaded'])


def build_report():return report(OUT,pins)
