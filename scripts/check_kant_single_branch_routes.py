"""Try continuation-preserving routes before reducing a single branch."""
from functools import lru_cache
import hashlib,html,json
import xml.etree.ElementTree as ET

from scripts import check_kant_content_binding as content,check_kant_content_definition as definition
from scripts import check_kant_function_definition_body as function,check_kant_quotation_definition as quotation
from scripts import check_kant_compound_fans as fans
from scripts.kant_public_fragment import decode,VERSION
from scripts.kant_lexical_context import LexicalContext
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report
from scripts.kant_page_public_context import ROOT

OUT=ROOT/'output/kant-single-branch-routes'
RUN=ROOT/'.noema-project/runs/kant-single-branch-routes-v3'
SAVED=ROOT/'output/kant-single-branch-routes-v2'


@lru_cache(maxsize=1)
def saved_evidence():
    """Reuse generated ink only when its production inputs are unchanged.

    The v2 geometry comparison passed all 19 cases. Its final test wrongly
    required fewer MAIN nuclei even when the recovered branch was nested.
    Preserve that report and its checker/test sources, then read the same ink
    again under the corrected tests instead of rerunning placement searches.
    """
    evidence=json.loads((SAVED/'structural-report.json').read_text(encoding='utf-8'))
    snapshots={'scripts/check_kant_single_branch_routes.py','tests/test_kant_single_branch_routes.py'}
    for name,stamp in evidence['source_sha256'].items():
        if name in snapshots:path=SAVED/'source'/name.rsplit('/',1)[-1]
        elif name.startswith('output/kant-single-branch-routes/'):path=SAVED/name.rsplit('/',1)[-1]
        else:path=ROOT/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=stamp:
            raise ValueError('Saved drawing input changed; a new placement trial is needed: '+name)
    return {r['key']:r for r in evidence['diagnostics']}


@lru_cache(maxsize=1)
def records():
    groups=[('content',content,'reports/kant-content-binding-v1.json',content.OUT,None,None),
        ('function',function,'reports/kant-compact-type-lists-v2.json',ROOT/'output/kant-compact-type-lists',
            LexicalContext.from_published(function.inputs()[0]),None),
        ('quotation',quotation,'reports/kant-compact-type-lists-v2.json',ROOT/'output/kant-compact-type-lists',
            LexicalContext.from_published(quotation.inputs()[0]),None),
        ('definition',definition,'reports/kant-content-definition-v1.json',definition.OUT,
            LexicalContext.from_published(definition.inputs()[0]),None),
        ('fans',fans,'reports/kant-compound-fans-v4.json',fans.OUT,fans.fixture()[0],{0,4,5})]
    rows=[]
    for family,module,baseline,directory,context,selection in groups:
        previous=json.loads((ROOT/baseline).read_text(encoding='utf-8'))
        by_key={r['key']:r for r in previous['diagnostics']}
        for i,(key,label,source) in enumerate(module.cases()):
            if selection is not None and i not in selection:continue
            saved_key=family+'-body-'+key if family in ('function','quotation') else key
            old=by_key[saved_key]
            if syntax_hash(source)!=old['syntax_sha256']:raise ValueError('Saved source changed: '+family+'/'+key)
            path=(directory/(saved_key+'.svg')).relative_to(ROOT).as_posix()
            rows.append(dict(key=family+'-'+key,label=label,source=source,previous=old,baseline=baseline,
                path=path,stamp=previous['source_sha256'][path],context=context))
    return rows


def cases():return [(r['key'],r['label'],r['source']) for r in records()]


@lru_cache(maxsize=24)
def checked(index):
    row=records()[index];old=row['previous'];source=row['source']
    raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Saved SVG changed')
    reader=LexicalContext.from_published(row['context'].published()) if row['context'] else None
    if decode(list(reversed(from_svg(raw.decode('utf-8')))),lexicon=reader)!=source:
        raise ValueError('Saved SVG no longer recovers its syntax')
    drawing=saved_evidence()[row['key']]
    if drawing['syntax_sha256']!=syntax_hash(source):raise ValueError('Saved drawing source changed')
    evidence_path=SAVED/(row['key']+'.svg')
    svg=evidence_path.read_text(encoding='utf-8');stats=measure(svg)
    if decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:
        raise ValueError('New route changed syntax')
    if stats['circles']!=old['circles'] or stats['branches']<old['branches']:
        raise ValueError('Routing changed tokens or reduced previously drawn branches')
    previous_fallback=bool(old.get('unbranched_paths') or old.get('branch_limits'))
    # Older reports omitted serial-fallback, which can preserve branch counts
    # after the interleaved attempt has failed. A successful retry proves that
    # this exact initial attempt failed; an empty reduction list alone cannot.
    retry=drawing.get('continuation_search_retry',False)
    if not previous_fallback and not retry and svg!=raw.decode('utf-8'):
        raise ValueError('Previously successful placement changed')
    return dict(key=row['key'],label=row['label'],source=source,svg=svg,width=drawing['width'],
        syntax_sha256=syntax_hash(source),previous_svg=row['path'],previous_width=old['width'],
        previous_branches=old['branches'],previous_main_nuclei=old['main_nuclei'],
        previous_unbranched_paths=old.get('unbranched_paths',[]),
        previous_branch_limits=old.get('branch_limits',[]),
        drawing_evidence_svg=evidence_path.relative_to(ROOT).as_posix(),
        identical_svg=svg==raw.decode('utf-8'),layout=drawing.get('layout','serial'),
        continuation_search_retry=retry,branch_limits=drawing.get('branch_limits',[]),
        unbranched_paths=drawing.get('unbranched_paths',[]),**stats)


def pins():
    result=definition.pins()
    names={'scripts/check_kant_single_branch_routes.py','tests/test_kant_single_branch_routes.py',
        'docs/kant-single-branch-routes.md','scripts/kant_interleaved_layout.py'}
    for row in records():names.update((row['baseline'],row['path']))
    saved_evidence()
    names.add((SAVED/'structural-report.json').relative_to(ROOT).as_posix())
    names.update(p.relative_to(ROOT).as_posix() for p in SAVED.glob('*.svg'))
    names.update(p.relative_to(ROOT).as_posix() for p in (SAVED/'source').glob('*.py'))
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def comparison():
    rows=json.loads((OUT/'structural-report.json').read_text(encoding='utf-8'))['diagnostics']
    cards=[]
    for row in rows:
        if row['identical_svg']:continue
        images=[]
        for label,path in [('従来',ROOT/row['previous_svg']),('今回',OUT/(row['key']+'.svg'))]:
            node=ET.fromstring(path.read_text(encoding='utf-8'));box=list(map(float,node.get('viewBox').split()))
            node.set('style',f'width:{box[2]*.53}px;height:{box[3]*.53}px')
            images.append('<p>'+label+'</p><div>'+ET.tostring(node,encoding='unicode')+'</div>')
        cards.append('<section><h2>'+html.escape(row['label'])+'</h2><p>'+str(row['previous_branches'])+'枝 → '+str(row['branches'])+'枝</p>'+''.join(images)+'</section>')
    (OUT/'comparison.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>一枝の後続を残す配置</title>'
        '<style>body{font:16px/1.8 sans-serif;margin:24px;color:#203438;background:#f7f6f1}section{background:white;padding:16px;margin:20px 0}section div{overflow:auto}h2{font-size:18px}</style>'
        '<h1>同じ構文・同じ倍率での比較</h1><p>すべて0.53倍。配置できない枝を本文へ戻す前に、後続の接続を保つ経路を探します。横幅が増える例もあり、外観の完成・固定ではありません。</p>'
        +''.join(cards)+'</html>\n',encoding='utf-8',newline='\n')


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-single-branch-routes-1',version=VERSION,title='一枝の後続を残す配置',
        intro='成功する既存配置を保ち、失敗時には一枝の入れ子でも後続の接続を保つ経路探索を行います。',
        limits=['Placement only; no changes to grammar, meanings, references or visible reader',
                'Representative diagnostics and saved definition bodies; not a full manuscript redraw',
                'Remaining constructors, declarations, page layout and visual approval are incomplete'])
    comparison()


def build_report():
    result=report(OUT,pins)
    result['drawing_evidence_report']=(SAVED/'structural-report.json').relative_to(ROOT).as_posix()
    result['evidence_scope']='Unchanged production inputs and saved SVGs re-read after correcting the nested-branch main-count test; no placement rerun'
    return result
