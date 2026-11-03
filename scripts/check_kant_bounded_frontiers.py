"""Bound waiting connections; reuse ink outside the changed scheduling scope."""
from functools import lru_cache
import hashlib,html,json
import xml.etree.ElementTree as ET

from scripts.check_kant_shared_stems import records as source_records,ink,pins as inherited_pins
from scripts import kant_public_fragment as writing
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report
from scripts.kant_page_public_context import ROOT

BASELINE='reports/kant-shared-stems-v1.json'
PREVIOUS=ROOT/'output/kant-shared-stems'
OUT=ROOT/'output/kant-bounded-frontiers'
RUN=ROOT/'.noema-project/runs/kant-bounded-frontiers-v2'


@lru_cache(maxsize=1)
def records():
    saved=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    changed=[name for name,stamp in saved['source_sha256'].items()
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=stamp]
    if changed!=['scripts/kant_interleaved_layout.py']:
        raise ValueError('Reuse requires exactly the isolated layout change: '+str(changed))
    by_key={r['key']:r for r in saved['diagnostics']}
    rows=[]
    for source in source_records():
        old=by_key[source['key']]
        if syntax_hash(source['source'])!=old['syntax_sha256']:raise ValueError('Saved native input changed')
        path=(PREVIOUS/(source['key']+'.svg')).relative_to(ROOT).as_posix()
        rows.append(dict(source,previous=old,path=path,stamp=saved['source_sha256'][path]))
    return rows


def cases():return [(r['key'],r['label'],r['source']) for r in records()]


def scheduling_scope(row):
    with use_context(row['context']):
        stream=writing.events(row['source'],multiple=True)
        def has_multiple(chain):
            return any(e.get('extra_sides') or any(has_multiple(s) for s in writing.event_sides(e) if isinstance(s,list)) for e in chain)
        previous=row['previous']
        if (not has_multiple(stream) and not previous['continuation_search_retry']
            and previous['layout'] in ('serial','interleaved')
            and not previous['branch_limits'] and not previous['unbranched_paths']):
            return 'ordinary-layout'
        # Each side is finished by the mandatory entrance/word sequence.
        # No unfinished side remains when the scheduler can choose a flow.
        # The main continuation waits for the last side entrance, so the
        # changed, non-forced choice cannot choose between two pending flows.
        def atomic(side):
            if isinstance(side,str):return True
            if not side or any(writing.event_sides(e) for e in side):return False
            if len(side)==1:return True
            word=side[0].get('word')
            return bool(word) and [e['token'] for e in side]==list(writing.parts_for().get(word,(word,)))
        if all(atomic(s) for e in stream for s in writing.event_sides(e)):
            return 'atomic-branches'
    return 'competing-frontiers'


@lru_cache(maxsize=24)
def checked(index):
    row=records()[index];source=row['source'];old=row['previous']
    raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Saved ink changed')
    before=raw.decode('utf-8')
    reader=LexicalContext.from_published(row['context'].published()) if row['context'] else None
    if writing.decode(list(reversed(from_svg(before))),lexicon=reader)!=source:raise ValueError('Saved ink changed syntax')
    scope=scheduling_scope(row)
    control=row['key']=='fans-four-compounds'
    if scope=='competing-frontiers' or control:
        drawing=writing.compile_statement(source,lexicon=row['context'],multiple=True)
        svg=to_svg(drawing['shapes']);width=drawing['width']
        limits=drawing.get('branch_limits',[]);unbranched=drawing.get('unbranched_paths',[])
        yields=drawing.get('frontier_yields',0);fallback=drawing.get('frontier_window_fallback',False)
        rejected=drawing.get('frontier_window_rejected',False)
        action='redrawn-control' if control else 'redrawn'
    else:
        svg=before;width=old['width'];limits=old['branch_limits'];unbranched=old['unbranched_paths']
        yields=0;fallback=False;rejected=False;action='reused-svg'
    if writing.decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:raise ValueError('Bounded frontier changed syntax')
    stats=measure(svg)
    if stats['circles']!=old['circles'] or stats['branches']<old['branches']:
        raise ValueError('Bounded frontier changed circles or reduced existing branches')
    if control and svg!=before:raise ValueError('Atomic-branch control changed despite reuse criterion')
    return dict(key=row['key'],label=row['label'],source=source,svg=svg,width=width,
        syntax_sha256=syntax_hash(source),previous_svg=row['path'],previous_width=old['width'],
        previous_branches=old['branches'],previous_ink=ink(before),ink=ink(svg),
        scheduling_scope=scope,action=action,identical_svg=svg==before,frontier_yields=yields,
        frontier_window_fallback=fallback,frontier_window_rejected=rejected,
        branch_limits=limits,unbranched_paths=unbranched,**stats)


def pins():
    result=inherited_pins()
    names={BASELINE,'scripts/check_kant_bounded_frontiers.py','tests/test_kant_bounded_frontiers.py',
        'docs/kant-bounded-frontiers.md','scripts/kant_interleaved_layout.py'}
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
    (OUT/'comparison.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>接続元を長く待たせない配置</title>'
        '<style>body{font:16px/1.8 sans-serif;margin:24px;color:#203438;background:#f7f6f1}section{background:white;margin:20px 0;padding:16px}section div{overflow:auto}h2{font-size:18px}</style>'
        '<h1>同じ構文・同じ倍率での比較</h1><p>すべて0.53倍。枝を先に置く基本順を保ち、待たせた接続が長くなったときにその続きを置きます。張り出しが小さくても線の総延長や幅が増える例があり、外観は未固定です。</p>'+''.join(cards)+'</html>\n',encoding='utf-8',newline='\n')


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-bounded-frontiers-1',version=writing.VERSION,title='接続元を長く待たせない配置',
        intro='語の連続と枝の入口順を保ち、接続元から離れすぎる前に未完の経路を進めます。',
        limits=['No changes to grammar, meanings, references, glyphs or geometric legality',
                'Unchanged scheduling scopes reuse saved ink; one atomic control is redrawn',
                'Width and total line length can increase; full page and visual completion remain'])
    comparison()


def build_report():return report(OUT,pins)
