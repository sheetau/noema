"""Pinned, resumable generation and SVG-only decoding of the Kant selection."""
import argparse
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import time
from scripts import build_concept2_kant as baseline
from scripts import concept2_composition as v2
from scripts import concept2_geometry_v3 as g
from scripts.concept2_codec_v3 import Codec
from scripts.concept2_controls import controls
from scripts.long_run import LongRun,atomic_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/kant-concept2-v3'


def write(path,text):path.write_text(text,encoding='utf-8',newline='\n')


def pins():
    paths=[*baseline.INPUTS,'scripts/concept2_composition.py','scripts/concept2_controls.py',
        'scripts/concept2_geometry_v3.py','scripts/concept2_codec_v3.py','scripts/build_concept2_readable.py',
        'docs/alphabet-concept2-readable-v3.md','concept/noema-alphabet-concept2-examples.png']
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}


def checked(row,codec):
    start=time.perf_counter();plan=v2.make_plan(row['public'],codec.dictionary)
    tokens=codec.encode(plan['plan']);drawing=g.layout(codec.units(tokens))[0]
    svg=v2.svg(drawing['shapes'])
    recovered=codec.read_svg(svg)
    if recovered['native']!=row['public']:raise ValueError('SVG recovered a different native syntax')
    return dict(row,plan=plan['plan'],features=plan['features'],tokens=tokens,svg=svg,drawing=drawing,
                glyphs=recovered['glyphs'],svg_native_exact=True,seconds=time.perf_counter()-start)


def publish(rows,old,codec,source_pins,run):
    OUT.mkdir(parents=True,exist_ok=True)
    for r in rows:write(OUT/f'statement-{r["statement"]}.svg',r['svg'])
    def paragraphs(width):
        result=[]
        for pi in range(4):
            result.append(g.fold([r['drawing'] for r in rows if r['paragraph']==pi],width))
        return result
    reading=paragraphs(2200);cards=[];whole=[];yy=80.
    for i,para in enumerate(reading):
        shapes=[]
        for j,row in enumerate(para):
            shapes.extend(g.move(row['shapes'],80,80+j*170));whole.extend(g.move(row['shapes'],80,yy));yy+=170
        yy+=65
        filename=f'paragraph-{i+1}.svg';write(OUT/filename,v2.svg(shapes,width=2400,height=160+170*(len(para)-1)))
        cards.append(f'<section><h2>第{i+1}段落</h2><a href="{filename}"><img src="{filename}" loading="lazy"></a><details><summary>原文</summary><p>{html.escape(old["paragraphs"][i]["source_text"])}</p></details></section>')
    write(OUT/'kant-reading.svg',v2.svg(whole,width=2400,height=yy))
    run.emit('progress',stage='Decode the folded reading page',completed=40,total=40)
    reading_svg=(OUT/'kant-reading.svg').read_text(encoding='utf-8')
    recovered=run.step('decode-reading-page',dict(svg_sha256=hashlib.sha256(reading_svg.encode()).hexdigest()),lambda:codec.read_page(reading_svg))
    assert recovered['statements']==[r['public'] for r in rows]
    for hundredths in range(45,14,-1):
        scale=hundredths/100;overview=paragraphs(1420/scale)
        if (sum(map(len,overview))*170+3*65+120)*scale<=2083:break
    page=[];yy=80
    for para in overview:
        for row in para:page.extend(baseline.scaled(row['shapes'],scale,90,90+yy*scale));yy+=170
        yy+=65
    pen=max(.65,g.PEN*scale)
    write(OUT/'kant-page.svg',v2.svg(page,width=1600,height=2263,pen=pen));v2.png(page,OUT/'kant-page.png',1600,2263,pen=pen)
    run.emit('progress',stage='Decode the scaled overview',completed=40,total=40)
    overview_svg=(OUT/'kant-page.svg').read_text(encoding='utf-8')
    recovered=run.step('decode-overview',dict(svg_sha256=hashlib.sha256(overview_svg.encode()).hexdigest()),lambda:codec.read_page(overview_svg))
    assert recovered['statements']==[r['public'] for r in rows]
    bridge=json.loads((ROOT/'data/kant-public-revolution-visible-bridge-v1.json').read_text(encoding='utf-8'))['mapping']
    examples=controls(codec.dictionary,*(bridge[n] for n in ('wa','h226h','r2pv')));control_cards=[]
    for i,ex in enumerate(examples):
        tokens=codec.encode(ex['plan']);drawing=g.layout(codec.units(tokens))[0];svg=v2.svg(drawing['shapes'])
        assert codec.read_svg(svg)['native']==ex['expected'],ex['title']
        filename=f'control-{i+1}.svg';write(OUT/filename,svg)
        control_cards.append(f'<section><h2>{html.escape(ex["title"])}</h2><a href="{filename}"><img src="{filename}"></a></section>')
    gallery=[]
    lane_names={-1:'上段',0:'中段',1:'下段'}
    for t,u in codec.forms.items():
        if t[0]=='branch':
            if t[1:] not in ((-1,1),(1,-1),(0,1),(-1,0,1),(1,0,-1),(1,1)):continue
            title='幹の順に '+ ' → '.join(lane_names[x] for x in t[1:])+' を参照'
        elif t[0]=='repeat':title=f'直前の形を計{t[1]}回'
        elif t[0]=='separator':title={'values':'値の群','quoted':'引用を含む群','references':'参照の群'}[t[1]]+('・最終群' if t[2] else '・後続群あり')
        elif t[0] in ('role-definition','template-definition'):title=lane_names[t[1]]+('に値を宣言' if t[0]=='role-definition' else 'に操作を宣言')
        elif t[0] in ('lig','lig-alt'):title='合字：'+' / '.join(t[1:])+('（異体）' if t[0]=='lig-alt' else '')
        else:continue
        gallery.append('<figure>'+v2.svg(u['shapes'])+f'<figcaption>{html.escape(title)}</figcaption></figure>')
    style='<style>body{font:15px/1.8 sans-serif;margin:32px;color:#203438}h2{font-size:18px}img{width:100%}section{margin:32px 0;padding:20px;background:white}.forms{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px}figure{margin:0}figure svg{width:100%;height:140px}</style>'
    write(OUT/'controls.html','<!doctype html><html lang="ja"><meta charset="utf-8"><title>復号できる対照例</title>'+style+'<h1>構成・復号の対照例</h1><p>SVGの円・円弧・線・ドットだけから構文を回収し、元の構文と一致した例です。本文の専用対応表は使いません。</p>'+''.join(control_cards)+'<h2>分岐・回数・円を含む区切り・交差</h2><div class="forms">'+''.join(gallery)+'</div></html>')
    counts=Counter(t[0] for r in rows for t in r['tokens'])
    report=dict(schema='concept2-readable-3',count=len(rows),paragraphs=4,svg_native_exact=len(rows),reading_svg_native_exact=len(rows),overview_svg_native_exact=len(rows),control_svg_native_exact=len(examples),
                counts=dict(counts),reading_rows=sum(map(len,reading)),overview_rows=sum(map(len,overview)),overview_scale=scale,
                source_sha256=source_pins,decoder_inputs=['SVG geometric primitives','shared public dictionary','public glyph and grammar rules'],
                decoder_excludes=['source AST','statement id','placement table','SVG element order','hidden metadata'],
                limits=['Not frozen; visual approval pending.','Exact vector primitives, not raster OCR or handwriting.',
                        'One individual binder per constructor; other native syntax is rejected.'])
    atomic_json(OUT/'report.json',report)
    atomic_json(OUT/'trace.json',dict(cases=[{k:v for k,v in r.items() if k not in ('svg','drawing')} for r in rows]))
    write(OUT/'index.html','''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Noema · concept 2 v3</title>
<style>body{margin:0;background:#f5f4ef;color:#203438;font:16px/1.85 "Yu Gothic",sans-serif}main{max-width:1560px;margin:auto;padding:36px}h1{font-size:28px}h2{font-size:18px}a{color:#245e65}section{background:#fffffe;padding:24px;margin:24px 0}img{width:100%;display:block}.compare{display:grid;grid-template-columns:1fr 1fr;gap:24px}nav{display:flex;gap:24px;flex-wrap:wrap}@media(max-width:700px){main{padding:16px}.compare{grid-template-columns:1fr}}</style>
<main><h1>Noema · 円の規則と復号 v3</h1><p>元のkant-pageと同じ4段落・40項目。中円内の大円弧、開口に応じた半径線、小円への侵入を修正し、引数の分岐と回数表記を加えました。外観は未固定です。</p>
<nav><a href="kant-reading.svg">全範囲を拡大</a><a href="controls.html">復号と構成の対照例</a><a href="report.json">確認結果</a><a href="../kant-concept2-v2/index.html">前回の試作</a></nav>
<p>各項目のSVGに加え、改行後の全範囲と縮小した一枚概観からも、40項目の構文が元どおりに戻ることを確認しています。復号には見える円・円弧・線・ドットと共有辞書を使います。画素画像・手書きの認識とは区別しています。</p>
<div class="compare"><section><h2>基準のkant-page</h2><img src="../kant-page-script-v3/kant-page.png"></section><section><h2>今回の試作</h2><a href="kant-page.svg"><img src="kant-page.png"></a></section></div>'''+''.join(cards)+'</main></html>')
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--resume',action='store_true');parser.add_argument('--limit',type=int);args=parser.parse_args()
    fixed=pins()
    with LongRun(ROOT/args.run,dict(schema='concept2-readable-run-3',pins=fixed,limit=args.limit),resume=args.resume) as run:
        run.emit('progress',stage='Read pinned source and public dictionary',completed=0,total=40)
        old,dictionary,_,selection=baseline.load();codec=Codec(dictionary);rows=[]
        for i,row in enumerate(selection[:args.limit]):
            run.emit('progress',stage=f'Geometry and SVG decoding: {row["statement"]}',completed=i,total=len(selection[:args.limit]))
            result=run.step(f'item-{row["statement"]}',row,lambda row=row:checked(row,codec));rows.append(result)
            print(f'{i+1}/{len(selection[:args.limit])}: {row["statement"]} / {result["seconds"]:.3f}s / SVG exact',flush=True)
        assert pins()==fixed
        if not args.limit:
            run.emit('progress',stage='Fold paragraphs and controls',completed=40,total=40)
            report=publish(rows,old,codec,fixed,run);print(json.dumps({k:report[k] for k in ('count','counts','overview_rows','overview_scale')},indent=2))


if __name__=='__main__':main()
