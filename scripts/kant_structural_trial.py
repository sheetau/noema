"""Small resumable grammar trials, preserving immutable prior SVG evidence."""
import hashlib
import html
import json
from pathlib import Path

from scripts.long_run import LongRun, atomic_json

ROOT=Path(__file__).resolve().parents[1]


def prepare(*, out, run_path, pins, cases, checked, preserved, preserved_count, schema, version, title, intro, limits):
    source_pins=pins()
    with LongRun(run_path,dict(schema=schema,source_sha256=source_pins),resume=run_path.exists()) as run:
        rows=[]
        for i,(key,_,source) in enumerate(cases()):
            run.emit('progress',stage='Read grammar diagnostics',completed=i,total=len(cases()))
            rows.append(run.step(key,source,lambda i=i:checked(i)))
        old=[]
        for i in range(preserved_count):
            run.emit('progress',stage='Read preserved SVGs',completed=i,total=preserved_count)
            old.append(run.step('preserved-'+str(i),dict(index=i),lambda i=i:preserved(i)))
        if pins()!=source_pins:raise ValueError('Trial inputs changed')
        out.mkdir(parents=True,exist_ok=True)
        cards=[]
        for row in rows:
            target=out/(row['key']+'.svg')
            target.write_text(row['svg'],encoding='utf-8',newline='\n')
            source_pins[target.relative_to(ROOT).as_posix()]=hashlib.sha256(target.read_bytes()).hexdigest()
            cards.append('<section><h2>'+html.escape(row['label'])+'</h2><div>'+row['svg']+'</div></section>')
        markup='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>'''+html.escape(title)+'''</title>
<style>body{font:16px/1.8 sans-serif;max-width:1500px;margin:auto;padding:24px;background:#f7f6f1;color:#203438}section{background:white;padding:16px;margin:16px 0}section div{overflow:auto}svg{height:130px;max-width:none}h2{font-size:17px}</style>
<h1>'''+html.escape(title)+'</h1><p>'+html.escape(intro)+'</p>'+''.join(cards)+'</html>\n'
        (out/'index.html').write_text(markup,encoding='utf-8',newline='\n')
        atomic_json(out/'structural-report.json',dict(schema=schema,version=version,
            diagnostics=[{k:v for k,v in r.items() if k not in ('source','svg')} for r in rows],
            preserved_svg_syntax=old,source_sha256=dict(sorted(source_pins.items())),limits=limits))
        run.emit('progress',stage='Grammar report saved',completed=len(rows)+len(old),total=len(rows)+len(old))


def report(out,pins):
    result=json.loads((out/'structural-report.json').read_text(encoding='utf-8'))
    if any(result['source_sha256'].get(n)!=v for n,v in pins().items()):
        raise ValueError('Trial implementation changed')
    for name,stamp in result['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=stamp:
            raise ValueError('Trial artifact changed: '+name)
    return result
