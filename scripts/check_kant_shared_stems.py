"""One side and its continuation can fork along the same visible stem."""
from functools import lru_cache
import hashlib,html,json,math
import xml.etree.ElementTree as ET

from scripts.check_kant_single_branch_routes import records as source_records
from scripts.check_kant_content_definition import pins as inherited_pins
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_geometry_rules import merged_lines
from scripts.kant_geometry_reader import read_geometry
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report
from scripts.kant_page_public_context import ROOT

BASELINE='reports/kant-single-branch-routes-v3.json'
PREVIOUS=ROOT/'output/kant-single-branch-routes'
OUT=ROOT/'output/kant-shared-stems'
RUN=ROOT/'.noema-project/runs/kant-shared-stems-v1'


@lru_cache(maxsize=1)
def records():
    saved=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    by_key={r['key']:r for r in saved['diagnostics']}
    rows=[]
    for source in source_records():
        old=by_key[source['key']]
        if syntax_hash(source['source'])!=old['syntax_sha256']:raise ValueError('Saved native input changed')
        path=(PREVIOUS/(source['key']+'.svg')).relative_to(ROOT).as_posix()
        rows.append(dict(source,previous=old,path=path,stamp=saved['source_sha256'][path]))
    return rows


def cases():return [(r['key'],r['label'],r['source']) for r in records()]


def ink(svg):
    shapes=from_svg(svg);lines=merged_lines(shapes)
    geometry=read_geometry(shapes);degrees=[0]*len(geometry['vertices'])
    for a,b in geometry['edges']:degrees[a]+=1;degrees[b]+=1
    return dict(line_length=sum(math.hypot(s['x2']-s['x1'],s['y2']-s['y1']) for s in lines),
        excursion=max((max(0.,-s['y1'],s['y1']-64.,-s['y2'],s['y2']-64.) for s in lines),default=0.),
        stem_junctions=sum(degrees[i]>=3 and not v['centers'] and not v['rims'] for i,v in enumerate(geometry['vertices'])))


@lru_cache(maxsize=24)
def checked(index):
    row=records()[index];source=row['source'];old=row['previous']
    raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Saved ink changed')
    reader=LexicalContext.from_published(row['context'].published()) if row['context'] else None
    before=raw.decode('utf-8')
    if decode(list(reversed(from_svg(before))),lexicon=reader)!=source:raise ValueError('Saved ink changed syntax')
    drawing=compile_statement(source,lexicon=row['context'],multiple=True)
    svg=to_svg(drawing['shapes']);stats=measure(svg)
    if decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:raise ValueError('Shared stem changed syntax')
    if stats['circles']!=old['circles']:raise ValueError('Shared stem changed circle count')
    if stats['branches']<old['branches']:raise ValueError('Shared stem reduced existing branches')
    return dict(key=row['key'],label=row['label'],source=source,svg=svg,width=drawing['width'],
        syntax_sha256=syntax_hash(source),previous_svg=row['path'],previous_width=old['width'],
        previous_branches=old['branches'],previous_ink=ink(before),ink=ink(svg),
        identical_svg=svg==before,layout=drawing.get('layout','serial'),
        continuation_search_retry=drawing.get('continuation_search_retry',False),
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing.get('unbranched_paths',[]),**stats)


def pins():
    result=inherited_pins()
    names={BASELINE,'scripts/check_kant_shared_stems.py','scripts/check_kant_single_branch_routes.py',
        'tests/test_kant_shared_stems.py','docs/kant-shared-stems.md','scripts/kant_interleaved_layout.py'}
    names.update(r['path'] for r in records())
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def comparison():
    rows=json.loads((OUT/'structural-report.json').read_text(encoding='utf-8'))['diagnostics']
    cards=[]
    for row in rows:
        if row['identical_svg']:continue
        pictures=[]
        for label,path in [('従来',ROOT/row['previous_svg']),('今回',OUT/(row['key']+'.svg'))]:
            node=ET.fromstring(path.read_text(encoding='utf-8'));box=list(map(float,node.get('viewBox').split()))
            node.set('style',f'width:{box[2]*.53}px;height:{box[3]*.53}px')
            pictures.append('<p>'+label+'</p><div>'+ET.tostring(node,encoding='unicode')+'</div>')
        cards.append('<section><h2>'+html.escape(row['label'])+'</h2>'+''.join(pictures)+'</section>')
    (OUT/'comparison.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>一枝でも線を共有する</title>'
        '<style>body{font:16px/1.8 sans-serif;margin:24px;color:#203438;background:#f7f6f1}section{background:white;margin:20px 0;padding:16px}section div{overflow:auto}h2{font-size:18px}</style>'
        '<h1>同じ構文・同じ倍率での比較</h1><p>すべて0.53倍。円から出た線の途中で枝と主列を分けます。長い迂回や型語の反復は残り、外観の固定前です。</p>'+''.join(cards)+'</html>\n',encoding='utf-8',newline='\n')


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-shared-stems-1',version=VERSION,title='一枝でも線を共有する',
        intro='枝が一本のときも、主列との共通の線を使い途中で分岐できます。最初に到達する円の位置から従来の規則で順序を読みます。',
        limits=['No changes to grammar, meanings, references, glyphs or geometric legality',
                'Representative examples and existing definition bodies, not a full manuscript redraw',
                'Long detours, type repetition, remaining syntax and visual completion are unresolved'])
    comparison()


def build_report():return report(OUT,pins)
