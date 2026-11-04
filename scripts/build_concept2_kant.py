"""Generate all four original Kant paragraphs as a non-frozen concept-2 trial."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import time

from scripts import concept2_preview as c
from scripts.long_run import LongRun, atomic_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/kant-concept2'
OLD='output/kant-page-script-v3/provenance.json'
DICTIONARY='output/kant-presentation-spellings/dictionary.json'
BRIDGE='data/kant-public-revolution-visible-bridge-v1.json'
SOURCE='examples/v016/kant-reviewed-complete-v1.noema'
NATIVE='examples/v016/kant-public-revolution-visible-v1.noema'
INPUTS=[OLD,DICTIONARY,BRIDGE,SOURCE,NATIVE,'data/writing-freeze-v1.json',
        'reports/kant-presentation-spellings-v1.json','reports/kant-public-revolution-visible-v1.json',
        'concept/alphabet-concept.md','concept/alphabet-concept2.md','docs/alphabet-concept2-proposal-v1.md',
        'docs/concept2-kant-preview.md','tests/test_concept2_preview.py',
        'scripts/concept2_preview.py','scripts/build_concept2_kant.py','scripts/long_run.py']


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def load():
    from noema.constructed import parse
    old=read(OLD);dictionary=read(DICTIONARY);bridge=read(BRIDGE)
    assert sha(OLD)==read('data/writing-freeze-v1.json')['output_sha256'][OLD]
    assert sha(DICTIONARY)==read('reports/kant-presentation-spellings-v1.json')['source_sha256'][DICTIONARY]
    evidence=read('reports/kant-public-revolution-visible-v1.json')
    assert all(sha(p)==evidence['source_sha256'][p] for p in (SOURCE,BRIDGE,NATIVE))
    source=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    decl={d['name']:d for d in source['declarations']}
    public={d['name']:d for d in dictionary['native']['declarations']}
    assert dictionary['native']['statements']==[]
    native=parse((ROOT/NATIVE).read_text(encoding='utf-8'))
    assert dictionary['native']['declarations']==native['declarations']
    mapping=bridge['mapping']
    def rename(x):
        if isinstance(x,list):return [rename(v) for v in x]
        if isinstance(x,dict):return {k:(mapping[v] if k=='symbol' else rename(v)) for k,v in x.items()}
        return x
    selected=[]
    for pi,p in enumerate(old['paragraphs']):
        for e in p['entries']:
            expected=deepcopy(source['statements'][e['statement']]);expanded=e.get('expanded_definition')
            if expanded:
                d=decl[expanded];assert d['kind']=='definition' and not d['parameters']
                assert expected['body']==dict(kind='call',symbol=expanded,arguments=[])
                expected['body']=deepcopy(d['body'])
            assert expected==e['compiled']['source']
            slot=bridge['source_statement_indices'].index(e['statement'])
            assert source['statements'][e['statement']]==bridge['source_statements'][slot]
            assert rename(source['statements'][e['statement']])==native['statements'][bridge['visible_statement_indices'][slot]]
            selected.append(dict(paragraph=pi,statement=e['statement'],original=expected,public=rename(expected)))
    assert len(selected)==40 and len(old['paragraphs'])==4
    return old,dictionary,public,selected


def checked(row,dictionary,declarations):
    start=time.perf_counter()
    tape=c.to_tape(row['public'],dictionary['selected_spellings'])
    aliases={tuple(r['parts']):r['symbol'] for r in dictionary['aliases']}
    recovered=c.from_tape(tape,declarations,aliases)
    assert recovered==row['public'],'Syntax tape changed the selected assertion'
    drawing=c.compile_tape(tape)
    metrics=c.validate_geometry(drawing['shapes'])
    raw=c.svg(drawing['shapes']);ink=c.from_svg(raw)
    # Exported SVG, not the private layout grouping, supplies these positions.
    middle=Counter(round(s['y'],5) for s in ink if s['kind']=='arc' and s['r']>=c.L-c.EPS).most_common(1)[0][0]
    c.validate_geometry(c.move(ink,dy=-middle))
    assert len(ink)==len(drawing['shapes'])
    return dict(row,tape=tape,drawing=drawing,svg=raw,metrics=metrics,
                syntax_tape_roundtrip=True,visible_syntax_roundtrip=False,seconds=time.perf_counter()-start)


def write_text(path,value):
    path.write_text(value,encoding='utf-8',newline='\n')


def scaled(shapes,scale,dx,dy):
    result=deepcopy(shapes)
    for s in result:
        for k in ('x','x1','x2'):
            if k in s:s[k]=s[k]*scale+dx
        for k in ('y','y1','y2'):
            if k in s:s[k]=s[k]*scale+dy
        if 'r' in s:s['r']*=scale
    return result


def publish(rows,old,pins):
    OUT.mkdir(parents=True,exist_ok=True)
    paragraphs=[];shape_counts=Counter();features=Counter()
    for pi in range(4):
        selected=[r for r in rows if r['paragraph']==pi]
        folded=c.fold_paragraph([r['drawing'] for r in selected])
        paragraphs.append(folded)
        for r in selected:
            for u in r['drawing']['placed']:shape_counts[u['key']]+=1
            features.update(t['kind'] if t['kind']!='word' else t['mode'] for t in r['tape'])
            write_text(OUT/f'statement-{r["statement"]}.svg',r['svg'])
    # The overview retains the same four paragraphs on one portrait sheet.
    # A second, larger reading view avoids hiding the real density difference.
    count=sum(map(len,paragraphs)); native_height=count*165+3*55+100
    width=2400.;height=native_height;allshapes=[];y=80.
    paragraph_svgs=[]
    for pi,folded in enumerate(paragraphs):
        local=[];ly=80.
        for row in folded:
            allshapes.extend(c.move(row['shapes'],80,y));y+=165
            local.extend(c.move(row['shapes'],80,ly));ly+=165
        y+=55
        raw=c.svg(local,width=width,height=ly-60)
        name=f'paragraph-{pi+1}.svg';write_text(OUT/name,raw);paragraph_svgs.append(name)
    write_text(OUT/'kant-reading.svg',c.svg(allshapes,width=width,height=height))
    # Reflow at the target scale, rather than shrinking a very tall strip into
    # a narrow column. The circle ratios remain unchanged in both views.
    for hundredths in range(65,14,-1):
        overview_scale=hundredths/100
        overview=[c.fold_paragraph([r['drawing'] for r in rows if r['paragraph']==pi],1420/overview_scale) for pi in range(4)]
        if (sum(map(len,overview))*165+3*55+100)*overview_scale<=2083:break
    view=[];vy=75.
    for p in overview:
        for row in p:
            view.extend(scaled(row['shapes'],overview_scale,90,90+vy*overview_scale));vy+=165
        vy+=55
    write_text(OUT/'kant-page.svg',c.svg(view,width=1600,height=2263,pen=c.PEN*overview_scale))
    c.png(view,OUT/'kant-page.png',1600,2263,pen=c.PEN*overview_scale)
    atlas=[]
    for name,shape in c.ROOT_FORMS.items():atlas.append((name,[c.root_symbol(name)],shape))
    for parts,shape in c.LIGATURES.items():atlas.append(('/'.join(parts),list(map(c.root_symbol,parts)),shape))
    atlas_html=''.join('<figure>'+c.svg(s)+f'<figcaption>{html.escape(n)}</figcaption></figure>' for n,_,s in atlas)
    write_text(OUT/'forms.html','<!doctype html><meta charset="utf-8"><title>Concept 2 公開合字表</title><style>body{font:14px sans-serif;margin:32px;color:#203438}main{display:grid;grid-template-columns:repeat(5,1fr);gap:20px}figure{margin:0;padding:12px;border:1px solid #ddd}svg{width:100%;height:120px}figcaption{overflow-wrap:anywhere}</style><h1>根語と合字</h1><p>合字名の / は元の根語の順序です。文番号や登録順から字形を作っていません。</p><main>'+atlas_html+'</main>')
    operator_html=''.join('<figure>'+c.svg(s)+f'<figcaption>{html.escape(n)}</figcaption></figure>' for n,s in c.OPERATORS.items())
    write_text(OUT/'operators.html','<!doctype html><meta charset="utf-8"><title>構文の形</title><style>body{font:14px sans-serif;margin:32px}main{display:grid;grid-template-columns:repeat(5,1fr);gap:20px}figure{margin:0;padding:12px}svg{width:100%;height:140px}</style><h1>構文と未充足の役割</h1><p>lambda・forall の内包小円は接続のない役割の導入。variable はその役割の使用を区別します。</p><main>'+operator_html+'</main>')
    atomic_json(OUT/'spelling-forms.json',dict(roots=c.ROOT_FORMS,ligatures=[dict(parts=p,shapes=s) for _,p,s in atlas if len(p)>1],operators=c.OPERATORS))
    atomic_json(OUT/'syntax-trace.json',dict(schema='concept2-appearance-trace-1',cases=[{k:v for k,v in r.items() if k not in ('drawing','svg')} for r in rows]))
    limits=[
        'Appearance prototype; not adopted or frozen.',
        'All 40 assertions use the original page display expansion and the saved public dictionary.',
        'Exact syntax recovery is from the public-spelling tape, NOT from SVG geometry.',
        'SVG ink checks cover circle relations and radial line incidence; complete spacing/topology and optical syntax decoding remain separate.',
        'Trial binder fragment is one individual binder named va; other binding forms fail closed.',
        'Rail declarations, general local aliases and dot pairing are not implemented in this appearance trial.',
        'The complete shared dictionary is referenced separately, as in the original page; its definitions are not expanded into the body.'
    ]
    report=dict(schema='concept2-kant-preview-1',count=40,paragraphs=4,rows=count,
        syntax_tape_roundtrips=40,visible_syntax_roundtrips=0,
        output_ink_geometry_checked=40,source_sha256=pins,
        shape_usage=dict(shape_counts),features=dict(features),
        limits=limits,overview_scale=overview_scale,
        output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.suffix in ('.svg','.png')})
    atomic_json(OUT/'report.json',report)
    cards=''.join(f'<section><h2>第{i+1}段落</h2><a href="{name}"><img src="{name}" loading="lazy"></a><details><summary>原文</summary><p>{html.escape(old["paragraphs"][i]["source_text"])}</p></details></section>' for i,name in enumerate(paragraph_svgs))
    write_text(OUT/'index.html',f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Noema — concept 2 / Kant</title>
<style>body{{margin:0;background:#f5f4ef;color:#203438;font:16px/1.85 "Yu Gothic",sans-serif}}main{{max-width:1560px;margin:auto;padding:36px}}h1{{font-size:28px}}h2{{font-size:18px}}a{{color:#245e65}}.lead{{max-width:950px}}.compare{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}section{{background:#fffffe;padding:24px;margin:24px 0}}img{{width:100%;height:auto;display:block}}.links{{display:flex;gap:24px;flex-wrap:wrap}}details p{{max-width:1000px}}@media(max-width:700px){{.compare{{grid-template-columns:1fr}}main{{padding:16px}}}}</style>
<main><h1>Noema · concept 2</h1><p class="lead">元の kant-page と同じ4段落・40項目。新しい円弧・直交する円・合字を使った外観試作です。採用前の候補としてご覧ください。</p>
<p class="lead">構成用の綴りと構文から元の40項目へ戻ること、出力SVGの円の関係・線の直交を確認しました。図形だけから語と構文を読む復号器は未実装です。局所略記・ドット接続・段の役割宣言も今回は実装していません。</p>
<nav class="links"><a href="kant-reading.svg">全範囲を拡大</a><a href="kant-page.svg">一枚の概観</a><a href="forms.html">根語・合字の形</a><a href="operators.html">構文・未充足の形</a><a href="report.json">確認結果</a></nav>
<div class="compare"><section><h2>基準の kant-page</h2><img src="../kant-page-script-v3/kant-page.png"></section><section><h2>concept 2 の試作</h2><a href="kant-page.svg"><img src="kant-page.png"></a></section></div>
<p>以下は読みやすい大きさでの段落別表示です。対象範囲は同じですが、語の識別と引用の区別を描いているため、元ページより分量が増えています。段落別の拡大表示は計{count}行です。</p>{cards}</main></html>''')
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',default='.noema-project/runs/concept2-kant-v1');parser.add_argument('--resume',action='store_true');parser.add_argument('--limit',type=int);args=parser.parse_args()
    pin_names=INPUTS+[p.relative_to(ROOT).as_posix() for p in (ROOT/'noema').glob('*.py')]
    pins={p:sha(p) for p in pin_names}
    with LongRun(ROOT/args.run,dict(schema='concept2-preview-run-1',pins=pins,limit=args.limit),resume=args.resume) as run:
        run.emit('progress',stage='Pinned 4-paragraph source and dictionary',completed=0,total=40)
        old,dictionary,declarations,selected=load();rows=[]
        for i,row in enumerate(selected[:args.limit]):
            run.emit('progress',stage=f'Generate item {row["statement"]}',completed=i,total=len(selected[:args.limit]))
            result=run.step('statement-'+str(row['statement']),row,lambda row=row:checked(row,dictionary,declarations))
            rows.append(result);print(f'{i+1}/{len(selected[:args.limit])}: {row["statement"]}, {result["seconds"]:.3f}s',flush=True)
        assert pins=={p:sha(p) for p in pin_names},'Inputs changed during generation'
        if args.limit:
            OUT.mkdir(parents=True,exist_ok=True)
            for row in rows:write_text(OUT/f'trial-{row["statement"]}.svg',row['svg'])
        else:
            run.emit('progress',stage='Compose four paragraphs and comparison page',completed=40,total=40)
            report=publish(rows,old,pins);print(json.dumps({k:report[k] for k in ('count','paragraphs','rows','overview_scale')},indent=2))


if __name__=='__main__':main()
