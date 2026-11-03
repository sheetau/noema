"""Remove redundant type-list prefixes, preserving old SVG readability.

Only cases with changed event streams are redrawn. This compares pinned saved
ink, never regenerates an older layout to use as a decoding oracle.
"""
from functools import lru_cache
from unittest.mock import patch
import hashlib,html,json
import xml.etree.ElementTree as ET

from scripts import kant_type_grammar as types,kant_public_fragment as writing
from scripts import check_kant_typed_binders as typed,check_kant_function_application as application
from scripts import check_kant_quotation_operations as quotation,check_kant_function_definition_body as function_body
from scripts import check_kant_quotation_definition as quotation_body
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report
from scripts.kant_page_public_context import ROOT

OUT=ROOT/'output/kant-compact-type-lists'
RUN=ROOT/'.noema-project/runs/kant-compact-type-lists-v2'


@lru_cache(maxsize=1)
def records():
    context,_=application.fixture()
    groups=[('typed',typed,'reports/kant-typed-binders-v1.json',None,False),
        ('application',application,'reports/kant-function-application-v1.json',context,True),
        ('quotation',quotation,'reports/kant-quotation-operations-v1.json',context,True),
        ('function-body',function_body,'reports/kant-function-definition-body-v2.json',LexicalContext.from_published(function_body.inputs()[0]),True),
        ('quotation-body',quotation_body,'reports/kant-quotation-definition-v1.json',LexicalContext.from_published(quotation_body.inputs()[0]),True)]
    rows=[]
    for family,module,report,lexicon,multiple in groups:
        previous=json.loads((ROOT/report).read_text(encoding='utf-8'))
        by_key={r['key']:r for r in previous['diagnostics']}
        for key,label,source in module.cases():
            old=by_key[key]
            if syntax_hash(source)!=old['syntax_sha256']:raise ValueError('Saved native case changed: '+family+'/'+key)
            path=(module.OUT/(key+'.svg')).relative_to(ROOT).as_posix()
            rows.append(dict(key=family+'-'+key,label=label,source=source,previous=old,report=report,
                path=path,stamp=previous['source_sha256'][path],lexicon=lexicon,multiple=multiple))
    return rows


def cases():return [(r['key'],r['label'],r['source']) for r in records()]


def legacy_type_list_tokens(values):
    return [token for value in values for token in ('types_more',*types.type_tokens(value))]+['types_end']


def streams(row):
    with use_context(row['lexicon']):
        current=writing.events(row['source'],multiple=row['multiple'])
        with patch.object(types,'type_list_tokens',legacy_type_list_tokens),patch.object(writing,'type_list_tokens',legacy_type_list_tokens):
            previous=writing.events(row['source'],multiple=row['multiple'])
    return previous,current


def continuations(chain):
    return sum(e['token']=='types_more' for e in chain)+sum(continuations(side)
        for e in chain for side in writing.event_sides(e) if isinstance(side,list))


@lru_cache(maxsize=64)
def checked(index):
    row=records()[index];source=row['source'];old=row['previous']
    raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Saved type-list SVG changed')
    reader=LexicalContext.from_published(row['lexicon'].published()) if row['lexicon'] is not None else None
    if writing.decode(list(reversed(from_svg(raw.decode('utf-8')))),lexicon=reader)!=source:
        raise ValueError('Legacy type-list SVG no longer recovers its native syntax')
    before,after=streams(row);removed=continuations(before)
    if continuations(after):raise ValueError('Current writer still emits a type-list prefix')
    changed=before!=after
    if changed!=bool(removed):raise ValueError('Change exceeds the type-list prefix removal')
    if changed:
        drawing=writing.compile_statement(source,lexicon=row['lexicon'],multiple=row['multiple'])
        svg=to_svg(drawing['shapes']);width=drawing['width']
        limits=drawing.get('branch_limits',[]);unbranched=drawing.get('unbranched_paths',[])
    else:
        svg=raw.decode('utf-8');width=old['width']
        limits=old.get('branch_limits',[]);unbranched=old.get('unbranched_paths',[])
    if writing.decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:
        raise ValueError('Compact type-list SVG changed native syntax')
    stats=measure(svg)
    if stats['circles']!=old['circles']-2*removed:raise ValueError('Unexpected circle-count change')
    return dict(key=row['key'],label=row['label'],source=source,svg=svg,width=width,
        syntax_sha256=syntax_hash(source),action='redrawn' if changed else 'reused-svg',
        previous_svg=row['path'],previous_circles=old['circles'],previous_width=old['width'],
        removed_continuations=removed,branch_limits=limits,unbranched_paths=unbranched,**stats)


def pins():
    result=quotation_body.pins()
    names={'scripts/check_kant_compact_type_lists.py','tests/test_kant_compact_type_lists.py','docs/kant-compact-type-lists.md',
        'docs/kant-typed-binders.md','reports/kant-function-definition-body-v2.json','reports/kant-quotation-definition-v1.json'}
    for row in records():names.update((row['report'],row['path']))
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def comparison():
    report=json.loads((OUT/'structural-report.json').read_text(encoding='utf-8'))
    chosen={'function-body-definition-body','quotation-body-definition-body','typed-lambda-recursive','application-two-lambda'}
    cards=[]
    for row in report['diagnostics']:
        if row['key'] not in chosen:continue
        pictures=[]
        for label,path in [('従来',ROOT/row['previous_svg']),('今回',OUT/(row['key']+'.svg'))]:
            node=ET.fromstring(path.read_text(encoding='utf-8'));box=list(map(float,node.get('viewBox').split()))
            node.set('style',f'width:{box[2]*.53}px;height:{box[3]*.53}px')
            pictures.append('<p>'+label+'</p><div class="ink">'+ET.tostring(node,encoding='unicode')+'</div>')
        cards.append('<section><h2>'+html.escape(row['label'])+'</h2><p>'+str(row['previous_circles'])+'円 → '+str(row['circles'])+'円</p>'+''.join(pictures)+'</section>')
    (OUT/'comparison.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>型列の反復を減らす</title>'
        '<style>body{font:16px/1.8 sans-serif;margin:24px;color:#203438;background:#f7f6f1}section{background:white;margin:20px 0;padding:16px}.ink{overflow:auto}h2{font-size:18px}</style>'
        '<h1>同じ構文・同じ倍率での比較</h1><p>型列の継続記号を省いた試作です。すべて0.53倍で表示します。枝の縮退や大円の反復は残り、外観は未固定です。</p>'+''.join(cards)+'</html>\n',encoding='utf-8',newline='\n')


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,
        preserved_count=0,schema='kant-compact-type-lists-1',version=writing.VERSION,
        title='型ごとの継続記号を省いた型列',
        intro='型を一式ずつ読み、列の終端で閉じます。旧図形も復号し、描画指示が変わる例だけを再生成しています。',
        limits=['No change to types, binding, meanings or references',
                'Remaining native constructors, declaration writing, layout and visual approval are incomplete'])
    comparison()


def build_report():
    result=diagnostic_report(OUT,pins)
    rows=result['diagnostics']
    result['summary']=dict(cases=len(rows),redrawn=sum(r['action']=='redrawn' for r in rows),
        reused_svg=sum(r['action']=='reused-svg' for r in rows),
        previous_circles=sum(r['previous_circles'] for r in rows),circles=sum(r['circles'] for r in rows),
        removed_continuations=sum(r['removed_continuations'] for r in rows))
    return result
