"""Publish the accepted alphabet and four paragraphs; reuse pinned ink evidence."""
import hashlib,html,json
from collections import Counter,defaultdict
from pathlib import Path
from scripts import concept2_composition as c,concept2_geometry_v5 as g
from scripts.concept2_writing import WritingReader
from scripts.long_run import atomic_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/noema-writing-v2'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def check_pins(report):
    for path,expected in source_pins(report).items():
        if digest(path)!=expected:raise ValueError('Evidence input changed: '+path)


def source_pins(report):
    pins=report.get('source_sha256',{})
    if report['schema']=='concept2-semantic-carry-1':
        return {report['baseline']:pins['report_sha256'],report['audit']:pins['completed_audit_sha256'],
                'scripts/check_concept2_semantic_carry.py':pins['implementation_sha256']}
    return pins


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    evidence_paths=['output/concept2-unified-reader-v1.json','output/concept2-dictionary-v3/report.json',
                    'output/kant-concept2-v9/report.json','output/concept2-semantic-carry-v1.json']
    evidence=[read(p) for p in evidence_paths]
    for report in evidence:check_pins(report)
    unified,dictionary,_,carry=evidence
    assert unified['all_native_exact'] and dictionary['native_exact'] and dictionary['alias_mapping_exact'] and carry['all_match']
    for item in unified['files']:
        if digest(item['path'])!=item['sha256']:raise ValueError('Verified ink changed: '+item['path'])
    native=read('output/concept2-dictionary-v3/dictionary.json')['native']
    codec=WritingReader(native)
    for item in dictionary['items']:
        if item['kind']=='spelling':codec.register(item['recovered'])
    trace=read('output/kant-concept2-v9/trace.json')['cases'];paragraphs=[]
    for paragraph in sorted({r['paragraph'] for r in trace}):
        cases=[r for r in trace if r['paragraph']==paragraph]
        drawings=[g.layout(codec.units([tuple(t) for t in r['tokens']]))[0] for r in cases]
        rows=g.fold(drawings,2200);shapes=[]
        for i,row in enumerate(rows):shapes+=g.move(row['shapes'],80,80+170*i)
        svg=c.svg(shapes,width=2360,height=170*len(rows)+160)
        if codec.read_page(svg)['statements']!=[r['public'] for r in cases]:raise ValueError('Paragraph fold changed syntax')
        name=f'paragraph-{paragraph+1}.svg';(OUT/name).write_text(svg,encoding='utf-8',newline='\n')
        paragraphs.append(dict(svg=name,rows=len(rows),statements=[r['statement'] for r in cases],sha256=digest('output/noema-writing-v2/'+name)))
        print(f'Paragraph {paragraph+1}: {len(rows)} rows, native exact',flush=True)
    families=defaultdict(list)
    for token,unit in codec.forms.items():
        g.ink_check(unit['shapes'])
        svg=c.svg(unit['shapes']);label=html.escape(' / '.join(map(str,token)))
        families[token[0]].append(f'<figure>{svg}<figcaption>{label}</figcaption></figure>')
    style='<style>body{max-width:1320px;margin:32px auto;padding:0 24px;font:15px system-ui;color:#263335}h1{font-size:26px}h2{font-size:19px}p{line-height:1.8}a{color:#246a78}img{width:100%;height:auto}section{margin:40px 0}details{border-top:1px solid #ccd4d6;padding:18px 0}summary{cursor:pointer}.grid{display:flex;flex-wrap:wrap;gap:20px}figure{margin:12px 0;width:210px;text-align:center}figure svg{max-width:200px;height:110px}figcaption{font-size:12px;overflow-wrap:anywhere}</style>'
    catalogue='<!doctype html><html lang="ja"><meta charset="utf-8"><title>Noema 字形表</title>'+style+'<h1>採用字形の全501形</h1><p>出現頻度ではなく、使用可能な系列を確認するための一覧です。記号名は解説であり、復号器への入力ではありません。</p><p><a href="index.html">本文へ戻る</a></p>'
    catalogue+=''.join(f'<details><summary>{html.escape(k)} — {len(v)}形</summary><div class="grid">'+''.join(v)+'</div></details>' for k,v in families.items())
    (OUT/'alphabet.html').write_text(catalogue+'</html>',encoding='utf-8',newline='\n')
    page='<!doctype html><html lang="ja"><meta charset="utf-8"><title>Noema 採用円文字</title>'+style+'<h1>Noema — 採用円文字</h1><p>kant-pageと同じ四段落・40項目。v4／v7の幹を維持し、短くなる箇所に式の共有を加えています。</p><p><a href="alphabet.html">全字形</a> · <a href="../concept2-dictionary-v3/index.html">公開辞書</a> · <a href="../kant-concept2-v9/index.html">長い枝と束縛の例</a> · <a href="../../docs/circle-writing-v2.md">共通規則</a></p>'
    page+=''.join(f'<section><h2>第{i+1}段落</h2><img alt="Noema 第{i+1}段落" src="{p["svg"]}"></section>' for i,p in enumerate(paragraphs))
    (OUT/'index.html').write_text(page+'</html>',encoding='utf-8',newline='\n')
    sources={p:digest(p) for p in evidence_paths+['scripts/build_concept2_release.py','docs/circle-writing-v2.md']}
    for e in evidence:sources.update(source_pins(e))
    report=dict(schema='noema-writing-release-2',source_sha256=sources,evidence_verified=True,
        adopted_alphabet='concept2-v7',entry='scripts.concept2_writing.WritingReader',glyphs=len(codec.forms),
        families=dict(Counter(t[0] for t in codec.forms)),paragraphs=paragraphs,kant_statements=40,
        paragraph_native_exact=True,unified_svg_files=unified['svg_files'],semantic_carry=carry['all_match'],
        scope='R1 common writing/decoding foundation; final publication of both source works remains separate')
    atomic_json(OUT/'report.json',report)
    print('Pinned evidence and four paragraphs verified; release written.',flush=True)


if __name__=='__main__':main()
