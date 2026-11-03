"""Resumable actual-page structural trial using explicitly published definitions.

Each sentence is a checkpoint. The supplied dictionary is separate from the
SVG; the reader never receives source ASTs, bridge mappings, or layout groups.
This produces structural evidence, not a writing freeze or semantic judgment.
"""
import argparse
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import time

from scripts.long_run import LongRun, atomic_json
from scripts.kant_page_public_context import inputs, context, SOURCE, NATIVE, BRIDGE, EVIDENCE
from scripts.kant_lexical_context import use_context, LexicalContext
from scripts.kant_public_fragment import compile_statement, decode, events, VERSION
from scripts.kant_public_lexicon import source_paths
from scripts.visible_syntax_geometry import to_svg, from_svg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/kant-public-context'


def pins():
    names=set(source_paths())|{SOURCE,NATIVE,BRIDGE,EVIDENCE,
        'scripts/check_kant_page_public_context.py','scripts/kant_page_public_context.py',
        'scripts/kant_lexical_context.py','scripts/kant_public_fragment.py',
        'scripts/kant_geometry_rules.py','scripts/kant_geometry_reader.py',
        'scripts/kant_flow_reader.py','scripts/kant_readable_flow.py',
        'scripts/balanced_circle_script.py','scripts/branch_circle_script.py',
        'scripts/circle_contact_script.py','scripts/contextual_opening_script.py',
        'scripts/check_kant_geometry_reader.py','scripts/visible_syntax_geometry.py',
        'scripts/visible_lexical_script.py','scripts/visible_syntax_vocabulary.py',
        'scripts/long_run.py','tests/test_kant_lexical_context.py',
        'data/writing-freeze-v1.json','output/kant-page-script-v3/provenance.json'}
    freeze=json.loads((ROOT/'data/writing-freeze-v1.json').read_text(encoding='utf-8'))
    names.update(freeze['source_sha256'])
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(names)}


def checked(row, ctx):
    started=time.perf_counter()
    with use_context(ctx):
        count=len(events(row['public']))
    drawing=compile_statement(row['public'],lexicon=ctx)
    svg=to_svg(drawing['shapes'])
    recovered=decode(from_svg(svg),lexicon=ctx)
    if recovered != row['public']:
        raise ValueError('Actual SVG did not recover the exact public syntax')
    return dict(statement=row['statement'],status='matched',events=count,
        circles=sum(s['kind']=='circle' for s in drawing['shapes']),width=drawing['width'],
        seconds=round(time.perf_counter()-started,3),svg=svg,
        syntax_sha256=hashlib.sha256(json.dumps(recovered,sort_keys=True).encode()).hexdigest())


def attempt(row,ctx):
    try:
        return checked(row,ctx)
    except ValueError as error:
        return dict(statement=row['statement'],status='unsupported',error=str(error))


def publish(rows,ctx,source_pins):
    OUT.mkdir(parents=True,exist_ok=True)
    # This is public lexical input, not a hidden table attached to each figure.
    dictionary=ctx.published()
    atomic_json(OUT/'dictionary.json',dictionary)
    cards=[]
    for row in rows:
        if row['status']=='matched':
            (OUT/('statement-'+str(row['statement'])+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')
            body='<div class="ink">'+row['svg']+'</div>'
        else:
            body='<p>'+html.escape(row['error'])+'</p>'
        cards.append('<section><h2>元の主張 '+str(row['statement'])+'</h2>'+body+'</section>')
    markup='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>Kant 公開定義接続の検査</title>
<style>body{font:16px/1.8 "Yu Gothic",sans-serif;max-width:1500px;margin:auto;padding:24px;background:#f7f6f1;color:#203438}section{padding:18px;background:#fffffe;margin:18px 0}h2{font-size:18px}.ink{overflow:auto}svg{height:130px;max-width:none}</style>
<h1>元の kant-page の40主張を公開定義へ接続する</h1>
<p>同じ原稿と同じ定義展開を使った復号試作です。文の内容・語義・参照先を保ち、実SVGから公開構文へ戻します。各文は横スクロールできます。</p>
<p>公開された名前と略記は<a href="dictionary.json">共通辞書</a>に記載します。元原稿との対応表や付属構文を図形読取へ渡しません。</p>
<p><strong>外観の固定候補ではありません。</strong>長い名前の冗長さ、行・頁の組版と復号、一般の型と束縛には残件があります。</p>
'''+''.join(cards)+'</html>\n'
    (OUT/'index.html').write_text(markup,encoding='utf-8',newline='\n')
    report=dict(schema='kant-page-public-context-1',version=VERSION,
        exact_public_roundtrips=sum(r['status']=='matched' for r in rows),total=len(rows),
        exact_source_name_and_expansion_matches=len(inputs()['selected']),
        lexical_context=ctx.fingerprint,word_count=len(ctx.words),
        selected_spelling_lengths=dict(sorted(Counter(map(len,ctx.parts.values())).items())),
        cases=[{k:v for k,v in r.items() if k!='svg'} for r in rows],
        limits=['Structural bridge and actual SVG decoding only, no new semantic judgment',
                'Explicit public dictionary is required; no page or dictionary-geometry decoding yet',
                'Appearance is not approved; long names remain too repetitive',
                'Arbitrary native syntax, sorts and binding depths remain incomplete'],
        source_sha256=source_pins)
    atomic_json(OUT/'structural-report.json',report)
    return report


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--run-dir',required=True)
    cli.add_argument('--resume',action='store_true')
    args=cli.parse_args()
    source_pins=pins()
    manifest=dict(schema='kant-page-context-run-1',source_sha256=source_pins)
    with LongRun(args.run_dir,manifest,resume=args.resume) as run:
        with run.activity('Verify saved public bridge and explicit dictionary'):
            rows=inputs()['selected']
            ctx=LexicalContext.from_published(json.loads(json.dumps(context().published())))
        results=[]
        for i,row in enumerate(rows):
            run.emit('progress',stage='Actual SVG roundtrip',completed=i,total=len(rows),statement=row['statement'])
            result=run.step('statement-'+str(row['statement']),dict(context=ctx.fingerprint,row=row),
                            lambda row=row:attempt(row,ctx))
            results.append(result)
            print(json.dumps({k:v for k,v in result.items() if k!='svg'}),flush=True)
        if pins()!=source_pins:
            raise ValueError('Input or implementation changed during this run')
        report=publish(results,ctx,source_pins)
        run.emit('progress',stage='Published structural trial',completed=len(rows),total=len(rows))
    print(json.dumps(dict(matched=report['exact_public_roundtrips'],total=report['total'])),flush=True)


def build_report():
    report=json.loads((OUT/'structural-report.json').read_text(encoding='utf-8'))
    if report['source_sha256']!=pins():
        raise ValueError('Stored structural trial is stale')
    return report


if __name__=='__main__':
    main()
