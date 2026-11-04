"""The same forty assertions, with all v2 composition mechanisms enabled."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import time

from scripts import concept2_composition as c
from scripts import build_concept2_kant as baseline
from scripts.concept2_controls import controls,geometry_controls
from scripts.long_run import LongRun,atomic_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/kant-concept2-v2'


def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,text):path.write_text(text,encoding='utf-8',newline='\n')


def pins():
    names=[*baseline.INPUTS,'scripts/concept2_composition.py','scripts/concept2_controls.py','scripts/build_concept2_composition.py',
           'docs/alphabet-concept2-composition-v2.md','concept/noema-alphabet-concept2-examples.png',
           'concept/noema-alphabet-concept2.png']
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'noema').glob('*.py')]
    return {p:sha(p) for p in names}


def checked(row,dictionary):
    started=time.perf_counter();p=c.make_plan(row['public'],dictionary)
    units=c.plan_units(p['plan']);drawing=c.compile_units(units)
    raw=c.svg(drawing['shapes']);ink=c.from_svg(raw)
    y=Counter(round(s['y'],4) for s in ink if s['kind']=='arc' and s['r']>=c.L-c.EPS).most_common(1)[0][0]
    c.ink_check(c.move(ink,dy=-y))
    assert c.expand_plan(p['plan'],dictionary)==row['public']
    return dict(row,**p,drawing=drawing,svg=raw,seconds=time.perf_counter()-started,
                native_expansion_exact=True,svg_native_decode=False)


def scaled(shapes,scale,dx,dy):return baseline.scaled(shapes,scale,dx,dy)


def publish(rows,old,dictionary,source_pins):
    OUT.mkdir(parents=True,exist_ok=True)
    for r in rows:write(OUT/f'statement-{r["statement"]}.svg',r['svg'])
    features=Counter();fused=0;radius_checks=0;shapes=Counter()
    for r in rows:
        features.update(r['features']);fused+=r['drawing']['fused_role_ports'];radius_checks+=r['drawing']['connection_radii_checked']
        shapes.update(u['name'] for u in r['drawing']['placed'])
    paragraphs=[c.fold([r['drawing'] for r in rows if r['paragraph']==i],2200.) for i in range(4)]
    paragraph_cards=[];allshapes=[];y=80.
    for i,para in enumerate(paragraphs):
        local=[];local_y=80.
        for row in para:
            local.extend(c.move(row['shapes'],80,local_y));local_y+=170
            allshapes.extend(c.move(row['shapes'],80,y));y+=170
        y+=65
        name=f'paragraph-{i+1}.svg';width=max(2400,max(r['width'] for r in para)+160)
        write(OUT/name,c.svg(local,width=width,height=local_y-50))
        paragraph_cards.append(f'<section><h2>第{i+1}段落</h2><a href="{name}"><img src="{name}" loading="lazy"></a><details><summary>原文</summary><p>{html.escape(old["paragraphs"][i]["source_text"])}</p></details></section>')
    write(OUT/'kant-reading.svg',c.svg(allshapes,width=max(2400,max(c.bounds(r['shapes'])[2] for p in paragraphs for r in p)+160),height=y))
    for hundredths in range(65,14,-1):
        scale=hundredths/100
        overview=[c.fold([r['drawing'] for r in rows if r['paragraph']==i],1420/scale) for i in range(4)]
        if (sum(map(len,overview))*170+3*65+120)*scale<=2083:break
    page=[];py=80.
    for para in overview:
        for row in para:page.extend(scaled(row['shapes'],scale,90,90+py*scale));py+=170
        py+=65
    write(OUT/'kant-page.svg',c.svg(page,width=1600,height=2263,pen=c.PEN*scale))
    c.png(page,OUT/'kant-page.png',1600,2263,pen=c.PEN*scale)
    controls_report=publish_controls(dictionary)
    forms=[]
    for n,s in c.ROOT_FORMS.items():forms.append((n,s))
    for n,s in c.LIGATURES.items():forms.append(('/'.join(n),s))
    for lane in (-1,0,1):
        for defining in (False,True):forms.append((f'段 {lane}: '+('宣言' if defining else '共有'),c.role_shape(lane,defining)))
    for label in (0,1):
        for source in (True,False):forms.append((f'ドット {label}: '+('出力の定義' if source else '入力'),c.dot_shape(label,source)))
    for label in range(4):
        for defining in (True,False):forms.append((f'局所略記 {label}: '+('定義' if defining else '呼出し'),c.alias_shape(label,defining)))
    cards=''.join('<figure>'+c.svg(s)+f'<figcaption>{html.escape(n)}</figcaption></figure>' for n,s in forms)
    write(OUT/'forms.html','<!doctype html><html lang="ja"><meta charset="utf-8"><title>Concept 2 v2 の構成</title><style>body{font:14px/1.8 sans-serif;margin:32px;color:#203438}main{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}figure{margin:0;padding:12px;border:1px solid #ddd}svg{width:100%;height:130px}figcaption{overflow-wrap:anywhere}</style><h1>根語・合字・共有・略記・ドット</h1><p>同じ語義・綴りへ戻る構成を公開しています。局所略記の番号はこの一覧の説明用で、本文には書きません。</p><main>'+cards+'</main></html>')
    atomic_json(OUT/'composition-trace.json',dict(schema='concept2-composition-trace-2',cases=[{k:v for k,v in r.items() if k not in ('drawing','svg')} for r in rows]))
    report=dict(schema='concept2-composition-preview-2',count=40,paragraphs=4,features=dict(features),
        fused_role_ports=fused,radius_connections_checked=radius_checks,reading_rows=sum(map(len,paragraphs)),overview_rows=sum(map(len,overview)),
        overview_scale=scale,source_sha256=source_pins,shape_usage=dict(shapes),
        native_expansion_exact=40,svg_ink_geometry_checked=40,svg_native_decode=0,controls=controls_report,
        limits=['Visual approval pending; not frozen.','Native AST equality is from composition expansion, not SVG decoding.',
                'Same original four paragraphs and shared public dictionary; dictionary definitions are separate.',
                'The radius connection checker and ink checks are not a proof of unique optical parsing.'])
    atomic_json(OUT/'report.json',report)
    write(OUT/'index.html',f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Noema — concept 2 / 構成 v2</title>
<style>body{{margin:0;background:#f5f4ef;color:#203438;font:16px/1.85 "Yu Gothic",sans-serif}}main{{max-width:1560px;margin:auto;padding:36px}}h1{{font-size:28px}}h2{{font-size:18px}}a{{color:#245e65}}p{{max-width:1080px}}section{{background:#fffffe;padding:24px;margin:24px 0}}img{{width:100%;height:auto;display:block}}.compare{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}nav{{display:flex;gap:24px;flex-wrap:wrap}}@media(max-width:700px){{.compare{{grid-template-columns:1fr}}main{{padding:16px}}}}</style>
<main><h1>Noema · 意味に応じた構成 v2</h1><p>元の kant-page と同じ4段落・40項目。中大円の区切りを修正し、共有・局所略記・引用の役割・ドットを含めた試作です。接続の端と改行の端は中円半径で組み立てます。</p>
<nav><a href="kant-reading.svg">全範囲を拡大</a><a href="forms.html">構成と字形</a><a href="controls.html">範囲・束縛・接続の対照例</a><a href="report.json">確認結果</a><a href="../kant-concept2/index.html">前回の試作</a></nav>
<p>構成の展開で40項目の構文一致を確認し、SVGの円弧・線・ドットを再読込して幾何条件を検査しています。図形だけから構文を読む復号の完成とは区別しています。外観は未固定です。</p>
<div class="compare"><section><h2>基準の kant-page</h2><img src="../kant-page-script-v3/kant-page.png"></section><section><h2>今回の試作</h2><a href="kant-page.svg"><img src="kant-page.png"></a></section></div>
<p>以下は拡大用の4段落です。共有の使用口のうち{fused}箇所を語形へ直接合成しています。</p>{''.join(paragraph_cards)}</main></html>''')
    return report


def publish_controls(dictionary):
    from noema.constructed_discourse import normalize_document
    mapping=read('data/kant-public-revolution-visible-bridge-v1.json')['mapping']
    examples=controls(dictionary,*(mapping[n] for n in ('wa','h226h','r2pv')))
    declarations={d['name']:d for d in dictionary['native']['declarations']};ordered=[];seen=set()
    def dependencies(v):
        if isinstance(v,list):
            for x in v:dependencies(x)
        elif isinstance(v,dict):
            if 'symbol' in v and v['symbol'] not in seen:
                name=v['symbol'];seen.add(name);d=declarations[name];dependencies(d);ordered.append(d)
            for x in v.values():dependencies(x)
    expected=[x['expected'] for x in examples];dependencies(expected)
    normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ordered,statements=expected))
    cards=[]
    for i,example in enumerate(examples):
        folded=c.fold([example['drawing']],1700);shapes=[]
        for j,row in enumerate(folded):shapes.extend(c.move(row['shapes'],60,80+j*170))
        filename=f'control-{i+1}.svg';write(OUT/filename,c.svg(shapes,width=1820,height=160+170*(len(folded)-1)))
        cards.append(f'<section><h2>{html.escape(example["title"])}</h2><a href="{filename}"><img src="{filename}"></a></section>')
    geometry=geometry_controls()
    geometry_html=''.join('<figure>'+c.svg(s)+f'<figcaption>{html.escape(title)}</figcaption></figure>' for title,s in geometry)
    write(OUT/'controls.html','''<!doctype html><html lang="ja"><meta charset="utf-8"><title>構成と接続の対照例</title>
<style>body{font:15px/1.8 sans-serif;margin:32px;color:#203438}section{border-top:1px solid #ddd;margin:30px 0;padding-top:14px}h2{font-size:18px}img{width:100%}.geometry{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px}figure{margin:0}figure svg{width:100%;height:140px}</style>
<h1>範囲・束縛・接続の対照例</h1><p><a href="index.html">本文との比較へ戻る</a></p>
<p>既存辞書の値 a・b と一引数述語 P を使った構成の対照例です。カントの本文ではありません。構成からの展開一致と型の検査を行っています。</p>'''+''.join(cards)+
        '<h2>作図の選択肢</h2><p>以下は幾何規則の対照です。八方向の全てに言語上の参照先を実装したという意味ではありません。本文で選択されるものと、作図のみの例を区別しています。</p><div class="geometry">'+geometry_html+'</div></html>')
    atomic_json(OUT/'controls-trace.json',dict(cases=[{k:v for k,v in x.items() if k!='drawing'} for x in examples],typed=True,svg_native_decode=False))
    return dict(typed_composition_cases=len(examples),geometry_cases=len(geometry))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--resume',action='store_true');parser.add_argument('--limit',type=int);args=parser.parse_args()
    fixed=pins()
    with LongRun(ROOT/args.run,dict(schema='concept2-composition-run-2',pins=fixed,limit=args.limit),resume=args.resume) as run:
        run.emit('progress',stage='Read unchanged source and public dictionary',completed=0,total=40)
        old,dictionary,_,selection=baseline.load();rows=[]
        for i,row in enumerate(selection[:args.limit]):
            run.emit('progress',stage=f'Composition and ink: item {row["statement"]}',completed=i,total=len(selection[:args.limit]))
            result=run.step(f'item-{row["statement"]}',row,lambda row=row:checked(row,dictionary));rows.append(result)
            print(f'{i+1}/{len(selection[:args.limit])}: {row["statement"]} / {result["seconds"]:.3f}s',flush=True)
        assert pins()==fixed
        if not args.limit:
            run.emit('progress',stage='Radius-preserving line breaks and pages',completed=40,total=40)
            report=publish(rows,old,dictionary,fixed)
            print(json.dumps({k:report[k] for k in ('count','features','fused_role_ports','overview_rows','overview_scale')},ensure_ascii=False,indent=2))
        else:
            OUT.mkdir(parents=True,exist_ok=True)
            for r in rows:write(OUT/f'trial-{r["statement"]}.svg',r['svg'])


if __name__=='__main__':main()
