"""Same-content Kant probe: original layout plus separated entry/exit ports."""
from collections import Counter
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

from scripts.check_kant_geometry_reader import source_entries,observed
from scripts.kant_readable_flow import compile_expression,VERSION
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.proof_kant_page_script_v3 import paragraph_view
from scripts.balanced_circle_script import pack_lines,STROKE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/kant-port-flow-probe'


def matches_flow(flow,compiled):
    expected=[([g['x'],g['y']],[[s['x'],s['y']] for s in g['satellites']]) for g in compiled['groups']]
    actual=[(flow['nuclei'][i]['center'],[flow['nuclei'][s]['center'] for s in side])
            for i,side in zip(flow['main'],flow['side'])]
    return len(actual)==len(expected) and all(math.dist(a[0],b[0])<1e-5 and len(a[1])==len(b[1])
        and all(math.dist(x,y)<1e-5 for x,y in zip(a[1],b[1])) for a,b in zip(actual,expected))


@lru_cache(maxsize=40)
def checked(index):
    original=source_entries()[index]['compiled']
    candidate=compile_expression(original['source'],reference_order=original['reference_order'])
    svg=to_svg(candidate['shapes'])
    flow=decompose_flow(read_geometry(from_svg(svg)))
    if not matches_flow(flow,candidate):raise ValueError('Visible main flow/side dependencies differ')
    old=decompose_flow(observed(index)['geometry'])
    return dict(statement=source_entries()[index]['statement'],compiled=candidate,svg=svg,
        original_flow_matches=matches_flow(old,original),flow=flow)


@lru_cache(maxsize=1)
def page():
    old=json.loads((ROOT/'output/kant-page-script-v3/provenance.json').read_text(encoding='utf-8'))
    paragraphs=[];offset=0
    for p in old['paragraphs']:
        entries=[dict(compiled=checked(offset+i)['compiled']) for i in range(len(p['entries']))]
        offset+=len(entries);paragraphs.append(dict(view=paragraph_view(entries),unit=p['unit']))
    width,height,margin=old['width'],old['height'],90
    # Exactly the original page packer's search and inter-paragraph spacing.
    for hundredths in range(120,39,-1):
        scale=hundredths/100
        rows=[pack_lines(p['view'],width-2*margin,scale) for p in paragraphs]
        pitch=210*scale
        used=sum(map(len,rows))*pitch+(len(paragraphs)-1)*28*scale
        if used<=height-2*margin:break
    else:raise ValueError('Page exceeds original packing range')
    y=margin+30*scale
    for p,lines in zip(paragraphs,rows):
        p['rows']=[dict(row,x=margin,y=y+i*pitch) for i,row in enumerate(lines)]
        y+=len(lines)*pitch+28*scale
    return dict(width=width,height=height,scale=scale,original_scale=old['scale'],paragraphs=paragraphs,
                rows=sum(map(len,rows)))


def prepare():
    from PIL import Image,ImageDraw
    OUT.mkdir(parents=True,exist_ok=True);data=page()
    ss=2;im=Image.new('RGB',(data['width']*ss,data['height']*ss),'#fffffe');draw=ImageDraw.Draw(im)
    scale=data['scale'];pen=STROKE*scale;elements=[]
    for p in data['paragraphs']:
        for row in p['rows']:
            x,y=row['x'],row['y']
            for s in row['shapes']:
                if s['kind']=='circle':
                    cx,cy,r=x+s['x']*scale,y+s['y']*scale,s['r']*scale;bound=r+pen/2
                    draw.ellipse(tuple(round(v*ss) for v in (cx-bound,cy-bound,cx+bound,cy+bound)),
                                 outline='#203438',width=max(1,round(pen*ss)))
                    elements.append(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>')
                else:
                    a=(x+s['x1']*scale,y+s['y1']*scale);b=(x+s['x2']*scale,y+s['y2']*scale)
                    draw.line([tuple(round(v*ss) for v in q) for q in (a,b)],fill='#203438',width=max(1,round(pen*ss)))
                    elements.append(f'<path d="M {a[0]} {a[1]} L {b[0]} {b[1]}"/>')
    im.resize((data['width'],data['height']),Image.Resampling.LANCZOS).save(OUT/'kant-page.png')
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{data["width"]}" height="{data["height"]}" viewBox="0 0 {data["width"]} {data["height"]}"><g stroke="#203438" stroke-width="{pen}" fill="none">'+''.join(elements)+'</g></svg>\n'
    (OUT/'kant-page.svg').write_text(svg,encoding='utf-8',newline='\n')
    markup='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>kant-page 同内容・局所変更の比較</title>
<style>body{font:16px/1.8 "Yu Gothic",sans-serif;max-width:1500px;padding:24px;margin:auto;background:#f7f6f1;color:#203438}.compare{display:grid;grid-template-columns:1fr 1fr;gap:24px}img{width:100%;height:auto}h1{font-size:25px}h2{font-size:18px}</style>
<h1>元の生成器へ入口・出口の区別だけを加えた比較</h1>
<p>同じカント40主張・同じ参照と語義・同じ描画規則です。元の文頭分類、実引数の横枝、接触、面積重心の調整、段落の組版を保持し、通過する円の入口と出口が同じ点になる経路を除外しました。番号ヘッダーや定型の二叉は追加していません。</p>
<p><strong>未完成の技術試作です。</strong>円・線から主な連なりと横枝を戻せますが、公開語識別・引用と束縛を含む構文全体の復号・頁全体の復号は未完です。元からある語の図形衝突も残っています。見た目の承認候補ではありません。</p>
<div class="compare"><div><h2>元のkant-page</h2><img src="../kant-page-script-v3/kant-page.png"></div><div><h2>入口・出口を分けた生成結果</h2><a href="kant-page.svg"><img src="kant-page.png"></a></div></div></html>\n'''
    (OUT/'index.html').write_text(markup,encoding='utf-8',newline='\n')


def build_report():
    rows=[checked(i) for i in range(40)];p=page()
    pins=['scripts/kant_readable_flow.py','scripts/kant_flow_reader.py','scripts/check_kant_readable_flow.py',
          'scripts/kant_geometry_reader.py','scripts/check_kant_geometry_reader.py',
          'tests/test_kant_readable_flow.py','docs/kant-port-flow-probe.md',
          'scripts/contextual_opening_script.py','scripts/balanced_circle_script.py',
          'scripts/circle_contact_script.py','scripts/branch_circle_script.py',
          'scripts/proof_kant_page_script_v3.py','scripts/visible_syntax_geometry.py',
          'scripts/visible_lexical_script.py','concept/alphabet-concept.md','data/writing-freeze-v1.json',
          'output/kant-page-script-v3/provenance.json']
    return dict(schema='noema-kant-port-separated-flow-1',version=VERSION,status='flow-only-not-native-syntax',
        statements=40,old_flow_matches=sum(r['original_flow_matches'] for r in rows),new_flow_matches=40,
        recovered_main_nuclei=sum(len(r['flow']['main']) for r in rows),
        recovered_side_dependencies=sum(sum(map(len,r['flow']['side'])) for r in rows),
        page=dict(rows=p['rows'],scale=p['scale'],original_scale=p['original_scale']),
        source_ast_unchanged=all(r['compiled']['source']==e['compiled']['source'] for r,e in zip(rows,source_entries())),
        source_references_unchanged=all(r['compiled']['reference_order']==e['compiled']['reference_order'] for r,e in zip(rows,source_entries())),
        cases=[dict(statement=r['statement'],old_flow_matches=r['original_flow_matches'],
            svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in rows],
        limits=['Public lexical identity remains unresolved','Native syntax, quoting and binding not decoded yet',
            'Page is a rendered comparison; decoding tests use complete unwrapped statement SVGs',
            'No new primitive or meaning judgment','No visual freeze or approval request'],
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in pins})


if __name__=='__main__':
    prepare();print(json.dumps(dict(output=str(OUT),rows=page()['rows'],scale=page()['scale'])))
