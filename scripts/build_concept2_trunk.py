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
from scripts import concept2_geometry_v5 as g
from scripts.concept2_codec_v7 import Codec
from scripts.concept2_controls import controls
from scripts.concept2_extended_controls import cases as extended_cases
from scripts.long_run import LongRun,atomic_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/kant-concept2-v7'


def write(path,text):path.write_text(text,encoding='utf-8',newline='\n')


def pins():
    paths=[*baseline.INPUTS,'scripts/concept2_composition.py','scripts/concept2_controls.py',
        'scripts/concept2_geometry_v5.py','scripts/concept2_codec_v7.py','scripts/build_concept2_trunk.py',
        'scripts/concept2_codec_v6.py',
        'scripts/concept2_extended_controls.py','scripts/kant_type_grammar.py','noema/constructed_discourse.py',
        'docs/alphabet-concept2-trunk-v7.md','concept/noema-alphabet-concept2-examples.png']
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}


def checked(row,codec):
    start=time.perf_counter();plan=v2.make_plan(row['public'],codec.dictionary)
    tokens=codec.encode(plan['plan']);drawing=g.layout(codec.units(tokens))[0]
    svg=v2.svg(drawing['shapes'])
    recovered=codec.read_svg(svg)
    if recovered['native']!=row['public']:raise ValueError('SVG recovered a different native syntax')
    return dict(row,plan=plan['plan'],features=plan['features'],tokens=tokens,svg=svg,drawing=drawing,
                glyphs=recovered['glyphs'],svg_native_exact=True,seconds=time.perf_counter()-start)


def confluence_controls(dictionary,a,b,combine):
    """A typed binary constructor is reused; no source-specific primitive."""
    def call(name,*args):return dict(kind='call',symbol=dict(form='word',parts=dictionary['selected_spellings'][name]),arguments=list(args))
    def use(lane):return dict(form='role-use',lane=lane)
    def define(lane,value):return dict(form='role-definition',lane=lane,value=value)
    def eq(a,b):return dict(kind='equal',arguments=[a,b])
    def both(a,b):return dict(kind='and',arguments=[a,b])
    def scope(v):return dict(form='scope',quotation=True,body=v)
    av,bv=call(a),call(b)
    def context(body):return both(eq(define(-1,av),av),both(eq(define(1,bv),bv),body))
    merged=call(combine,use(1),use(-1))
    chain=context(both(eq(define(0,merged),call(combine,bv,av)),eq(call(combine,use(1),use(0)),call(combine,bv,call(combine,bv,av)))))
    variable=dict(kind='variable',name='va')
    bound=dict(kind='forall',variable='va',sort='individual',body=both(eq(define(0,variable),variable),eq(call(combine,use(0),use(-1)),call(combine,variable,av))))
    quoted=dict(kind='quote',body=scope(context(eq(call(combine,use(1),use(-1)),call(combine,bv,av)))))
    bodies=[
        ('二段合流・上から下が引数順',context(eq(merged,call(combine,bv,av)))),
        ('同じ参照を二つの引数として合流',context(eq(call(combine,use(-1),use(-1)),call(combine,av,av)))),
        ('合流結果を宣言し、次の合流で再使用',chain),
        ('束縛内の合流と、引用を出た後の参照復帰',context(both(bound,both(eq(quoted,quoted),eq(merged,call(combine,bv,av)))))),
    ]
    return [dict(title=title,plan=(plan:=scope(dict(kind='assert',body=body))),expected=v2.expand_plan(plan,dictionary)) for title,body in bodies]


def publish_extended(codec,bridge,run,style):
    examples=extended_cases(codec,bridge['wa'],bridge['h226h'],bridge['r2pv']);rows=[];cards=[]
    for i,example in enumerate(examples):
        run.emit('progress',stage='Extended SVG: '+example['key'],completed=i,total=len(examples))
        def generate():
            plan=v2.make_plan(example['source'],codec.dictionary,sharing=False)['plan']
            drawing=g.layout(codec.units(codec.encode(plan)))[0];svg=v2.svg(drawing['shapes'])
            assert codec.read_svg(svg)['native']==example['source'],example['key']
            return dict(example,drawing=drawing,svg=svg)
        row=run.step('extended-'+example['key'],example,generate);rows.append(row)
        name='extended-'+example['key']+'.svg';write(OUT/name,row['svg'])
        cards.append(f'<section><h2>{html.escape(example["title"])}</h2><a href="{name}"><img src="{name}" loading="lazy"></a></section>')
    shapes=[]
    folded=g.fold([r['drawing'] for r in rows],2200)
    for i,row in enumerate(folded):shapes.extend(g.move(row['shapes'],80,80+i*170))
    svg=v2.svg(shapes,width=2400,height=170*len(folded)+160);write(OUT/'extended-reading.svg',svg)
    decoded=run.step('decode-extended-page',dict(svg_sha256=hashlib.sha256(svg.encode()).hexdigest()),lambda:codec.read_page(svg))
    assert decoded['statements']==[e['source'] for e in examples]
    gallery=[]
    from scripts.concept2_codec_v7 import EXTRA_OPERATORS
    for t,u in codec.forms.items():
        if t[0]=='type' or t[0]=='op' and t[1] in EXTRA_OPERATORS:
            gallery.append('<figure>'+v2.svg(u['shapes'])+'<figcaption>'+html.escape(t[1])+'</figcaption></figure>')
    write(OUT/'extended.html','<!doctype html><html lang="ja"><meta charset="utf-8"><title>型と構文の追加対照</title>'+style+'<h1>型と構文の追加対照</h1><p>型・引数順・束縛・引用・列・数・内容・質問・メッセージを、既存の言語仕様で検査しています。各SVGと改行した全体から元の構文を回収しました。長い例は画像を開くと拡大できます。</p><p><a href="extended-reading.svg">追加対照の全範囲</a> · <a href="index.html">本文に戻る</a></p>'+''.join(cards)+'<h2>型と構文の記号案</h2><p>新しい記号も外観未固定です。中心からの方向指定とは区別し、円周から伸びる線と外側の円弧を組み合わせています。</p><div class="forms">'+''.join(gallery)+'</div></html>')
    atomic_json(OUT/'extended-trace.json',dict(cases=examples))
    run.emit('progress',stage='Extended corpus complete',completed=len(rows),total=len(rows))
    return len(rows),len(folded)


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
    examples=controls(codec.dictionary,*(bridge[n] for n in ('wa','h226h','r2pv')))
    combine=next(d['name'] for d in codec.dictionary['native']['declarations'] if d['parameters']==['individual','individual'] and d['result']=='individual')
    examples+=confluence_controls(codec.dictionary,bridge['wa'],bridge['h226h'],combine);control_cards=[]
    for i,ex in enumerate(examples):
        tokens=codec.encode(ex['plan']);drawing=g.layout(codec.units(tokens))[0];svg=v2.svg(drawing['shapes'])
        assert codec.read_svg(svg)['native']==ex['expected'],ex['title']
        filename=f'control-{i+1}.svg';write(OUT/filename,svg)
        title=ex['title'].replace('合流','幹での参照')
        control_cards.append(f'<section><h2>{html.escape(title)}</h2><a href="{filename}"><img src="{filename}"></a></section>')
    gallery=[]
    lane_names={-1:'上段',0:'中段',1:'下段'}
    for t,u in codec.forms.items():
        if t[0]=='word-use' and t[1] in codec.backward_word_keys:
            title=f'前の語宣言を参照・キー{t[1]}（中心の小円なし）'
        elif t[0]=='branch':
            if t[1:] not in ((-1,1),(1,-1),(0,1),(-1,0,1),(1,0,-1),(1,1)):continue
            title='幹の順に '+ ' → '.join(lane_names[x] for x in t[1:])+' を参照'
        elif t[0]=='select':title='小円で '+ ' → '.join(lane_names[x] for x in t[1:])+' を選択'
        elif t[0]=='select-directed':
            if t[1:] not in ((-1,1),(1,-1),(0,1,-1)):continue
            title='任意表記：中心線から '+ ' → '.join(lane_names[x] for x in t[1:])+' を参照'
        elif t[0]=='merge':
            if t[1:] not in ((-1,1),(1,-1),(-1,-1),(-1,0,1),(-1,1,0),(1,1,-1)):continue
            title='任意表記：上から順に '+ ' → '.join(lane_names[x] for x in t[1:])+' を合流'
        elif t[0]=='dot' and t[1] in (0,1,6,129,153,255):title=f'対応ドット {t[1]}'+('・左右の中円弧' if t[1]==0 else '・中円弧なし' if t[1]==153 else '・中円弧と接続口')
        elif t[0]=='dot-bare':title='対応ドット153・裸の対応先'
        elif t[0]=='repeat':title=f'直前の形を計{t[1]}回'
        elif t[0]=='separator':title={'values':'値の群','quoted':'引用を含む群','references':'参照の群'}[t[1]]+('・最終群' if t[2] else '・後続群あり')
        elif t[0] in ('role-definition','template-definition'):title=lane_names[t[1]]+('に値を宣言' if t[0]=='role-definition' else 'に操作を宣言')
        elif t[0] in ('lig','lig-alt'):title='合字：'+' / '.join(t[1:])+('（異体）' if t[0]=='lig-alt' else '')
        else:continue
        gallery.append('<figure>'+v2.svg(u['shapes'])+f'<figcaption>{html.escape(title)}</figcaption></figure>')
    style='<style>body{font:15px/1.8 sans-serif;margin:32px;color:#203438}h2{font-size:18px}img{width:100%}section{margin:32px 0;padding:20px;background:white}.forms{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px}figure{margin:0}figure svg{width:100%;height:140px}</style>'
    changes=[]
    for title,shapes in [('v6：合流へ置換していた参照順',codec.forms[('merge',-1,1,0)]['shapes']),('今回：v4の幹をたどる形へ復元',codec.forms[('branch',-1,1,0)]['shapes'])]:
        changes.append('<figure>'+v2.svg(shapes)+'<figcaption>'+title+'</figcaption></figure>')
    for key in codec.backward_word_keys:
        t=('word-use',key)
        for title,form in [('以前：中心に小円',codec.previous_word_forms[t]),('今回：中心から前の語宣言を参照',codec.forms[t])]:
            changes.append('<figure>'+v2.svg(form['shapes'])+f'<figcaption>{title}・キー{key}</figcaption></figure>')
    write(OUT/'changes.html','<!doctype html><html lang="ja"><meta charset="utf-8"><title>今回の字形変更</title>'+style+'<h1>今回の字形変更</h1><p>幹はv4へ戻しました。中心の小円を外す変更は、前の語宣言を呼び出す一部の形に限定しています。</p><div class="forms" style="grid-template-columns:1fr 1fr">'+''.join(changes)+'</div></html>')
    write(OUT/'controls.html','<!doctype html><html lang="ja"><meta charset="utf-8"><title>復号できる対照例</title>'+style+'<h1>構成・復号の対照例</h1><p>SVGの円・円弧・線・ドットだけから構文を回収し、元の構文と一致した例です。本文の専用対応表は使いません。</p>'+''.join(control_cards)+'<h2>分岐・回数・円を含む区切り・交差</h2><div class="forms">'+''.join(gallery)+'</div></html>')
    extended_count,extended_rows=publish_extended(codec,bridge,run,style)
    counts=Counter(t[0] for r in rows for t in r['tokens'])
    report=dict(schema='concept2-trunk-7',count=len(rows),paragraphs=4,svg_native_exact=len(rows),reading_svg_native_exact=len(rows),overview_svg_native_exact=len(rows),control_svg_native_exact=len(examples),
                counts=dict(counts),reading_rows=sum(map(len,reading)),overview_rows=sum(map(len,overview)),overview_scale=scale,
                backward_word_keys=codec.backward_word_keys,backward_word_occurrences=sum(t[0]=='word-use' and t[1] in codec.backward_word_keys for r in rows for t in r['tokens']),
                extended_svg_native_exact=extended_count,extended_page_native_exact=extended_count,extended_rows=extended_rows,
                source_sha256=source_pins,decoder_inputs=['SVG geometric primitives','shared public dictionary','public glyph and grammar rules'],
                decoder_excludes=['source AST','statement id','placement table','SVG element order','hidden metadata'],
                limits=['Not frozen; visual approval pending.','Exact vector primitives, not raster OCR or handwriting.',
                        'Native expression and statement constructors supported; declaration pages and arbitrary branch payload layouts remain.',
                        'Native depth limit 128; visible description type rank limit 128.'])
    atomic_json(OUT/'report.json',report)
    atomic_json(OUT/'trace.json',dict(cases=[{k:v for k,v in r.items() if k not in ('svg','drawing')} for r in rows]))
    write(OUT/'index.html','''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Noema · concept 2 v7</title>
<style>body{margin:0;background:#f5f4ef;color:#203438;font:16px/1.85 "Yu Gothic",sans-serif}main{max-width:1560px;margin:auto;padding:36px}h1{font-size:28px}h2{font-size:18px}a{color:#245e65}section{background:#fffffe;padding:24px;margin:24px 0}img{width:100%;display:block}.compare{display:grid;grid-template-columns:1fr 1fr;gap:24px}nav{display:flex;gap:24px;flex-wrap:wrap}@media(max-width:700px){main{padding:16px}.compare{grid-template-columns:1fr}}</style>
<main><h1>Noema · 円の規則と復号 v7</h1><p>元のkant-pageと同じ4段落・40項目。参照順はv4の幹と選択形へ戻しました。一部の語参照では中心の小円を外し、中心から左へ伸びる線で前の宣言を指します。任意型・複数束縛などの対応は維持しています。外観は未固定です。</p>
<nav><a href="changes.html">今回の字形変更を比較</a><a href="kant-reading.svg">全範囲を拡大</a><a href="controls.html">復号と構成の対照例</a><a href="extended.html">型・束縛・構文の追加対照</a><a href="report.json">確認結果</a><a href="../kant-concept2-v4/index.html">v4</a><a href="../kant-concept2-v6/index.html">前回の試作</a></nav>
<p>各項目のSVGに加え、改行後の全範囲と縮小した一枚概観からも、40項目の構文が元どおりに戻ることを確認しています。復号には見える円・円弧・線・ドットと共有辞書を使います。画素画像・手書きの認識とは区別しています。</p>
<div class="compare"><section><h2>基準のkant-page</h2><img src="../kant-page-script-v3/kant-page.png"></section><section><h2>今回の試作</h2><a href="kant-page.svg"><img src="kant-page.png"></a></section></div>'''+''.join(cards)+'</main></html>')
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--resume',action='store_true');parser.add_argument('--limit',type=int);args=parser.parse_args()
    fixed=pins()
    with LongRun(ROOT/args.run,dict(schema='concept2-trunk-run-7',pins=fixed,limit=args.limit),resume=args.resume) as run:
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
