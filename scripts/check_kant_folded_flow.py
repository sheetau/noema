"""Fold saved connected runs; recover exact ink and syntax without cut metadata."""
from functools import lru_cache
import hashlib,json
from scripts import check_kant_item_runs as prior,kant_folded_flow as folded
from scripts.kant_item_rows import pack_rows
from scripts.kant_geometry_rules import merged_lines
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.kant_page_public_context import ROOT
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-folded-flow'
RUN=ROOT/'.noema-project/runs/kant-folded-flow-v4'
BASELINE='reports/kant-item-runs-v2.json'
WIDTHS=[420,250,1330,1000,700,1100,1400,800]


def ink_key(shapes):
    circles=[s for s in shapes if s['kind']=='circle']
    dx=min(s['x'] for s in circles);dy=min(s['y'] for s in circles)
    normalized=folded.translate(circles+merged_lines(shapes),-dx,-dy)
    return sorted(json.dumps({k:(round(float(v),5) or 0.) if isinstance(v,(float,int)) else v for k,v in s.items()},sort_keys=True) for s in normalized)


@lru_cache(maxsize=1)
def saved():
    report=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for row in report['diagnostics']:
        path='output/kant-item-runs/'+row['key']+'.svg'
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=report['source_sha256'][path]:
            raise ValueError('Saved source page changed')
    return report['diagnostics']


def cases():return prior.cases()


@lru_cache(maxsize=16)
def checked(index):
    fixture=prior.fixtures()[index];old=saved()[index];rows=[];counts=[]
    originals=[from_svg(s) for s in old['row_svgs']]
    for shapes in originals:
        drawing=folded.fold(shapes,WIDTHS[index])
        rows+=drawing['row_shapes'];counts.append(len(drawing['row_shapes']))
    svg=to_svg(pack_rows(rows));shapes=list(reversed(from_svg(svg)))
    recovered=folded.unfold(shapes)
    if len(recovered)!=len(originals) or any(ink_key(a)!=ink_key(b) for a,b in zip(recovered,originals)):
        raise ValueError('Folding changed original visible ink')
    if folded.decode_page(shapes,seed=fixture['seed'],include_spellings=True)!=fixture['source']:
        raise ValueError('Folded page changed native document or spelling records')
    return dict(key=fixture['key'],label=fixture['label'],source=fixture['source'],svg=svg,
        width_limit=WIDTHS[index],rows=len(rows),rows_per_flow=counts,items=len(fixture['records']),
        circles=old['circles'],branches=old['branches'],syntax_sha256=old['syntax_sha256'],
        ink_exact=True,row_svgs=[to_svg(row) for row in rows])


@lru_cache(maxsize=16)
def preserved(index):
    fixture=prior.fixtures()[index];path='output/kant-item-runs/'+fixture['key']+'.svg'
    if folded.decode_page(from_svg((ROOT/path).read_text(encoding='utf-8')),seed=fixture['seed'],include_spellings=True)!=fixture['source']:
        raise ValueError('Unfolded page changed under continuation reader')
    return dict(svg=path,syntax_sha256=saved()[index]['syntax_sha256'])


def pins():
    result=prior.pins()
    names={BASELINE,'scripts/kant_folded_flow.py','scripts/check_kant_folded_flow.py','tests/test_kant_folded_flow.py',
           'docs/kant-folded-flow.md','scripts/proof_kant_page_script_v3.py',
           *('output/kant-item-runs/'+r['key']+'.svg' for r in prior.fixtures())}
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,preserved_count=len(cases()),
        schema='kant-folded-flow-1',version='kant-folded-flow-1',title='線の継続から折り返し前の構文を読む',
        intro='円を切らずに折り返し、行端の線の対応から元の接続と構文を復元します。',
        limits=['Saved bounded runs are folded without relayout; full page scale and flow batching remain',
                'Physical rows are ordered top to bottom; cross-page continuation remains',
                'No row numbers, original cuts, source syntax or groups are given to the decoder'])


def build_report():return report(OUT,pins)
