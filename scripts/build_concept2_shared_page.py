"""Publish the unchanged Kant selection with measured sharing and branch controls."""
import argparse,hashlib,html,json,shutil,time
from collections import Counter
from pathlib import Path
from scripts import build_concept2_kant as baseline,concept2_composition as c,concept2_geometry_v5 as g
from scripts.concept2_document import complete_public_dictionary
from scripts.concept2_assembly_reader import AssemblyCodec
from scripts.concept2_assembly import assemble_call,expand_plan
from scripts.concept2_sharing import choose_plan
from scripts.long_run import LongRun,atomic_json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'output/kant-concept2-v7'


def folded_svg(drawings,width):
    rows=g.fold(drawings,width);shapes=[]
    for i,row in enumerate(rows):shapes+=g.move(row['shapes'],80,80+i*170)
    return c.svg(shapes,width=width+160,height=170*len(rows)+160),len(rows)


def controls(codec):
    call=lambda n,*args:dict(kind='call',symbol=n,arguments=list(args))
    params=lambda d:d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
    f=next(d['name'] for d in codec.declarations.values() if params(d)==['individual']*2 and d['result']=='individual')
    a=call(c.old.root_symbol('aki'));give=c.old.root_symbol('give');values=[]
    for n in (2,5,9):
        value=a
        for i in range(n):value=call(f,value,a)
        values.append(value)
    source=call(give,*values);rows=[]
    for lanes,title in [((-1,0,1),'長い三つの引数を上・中・下の参照へ'),((1,-1,0),'幹をたどって下・上・中の順に読む')]:
        plan=dict(form='scope',quotation=True,body=dict(kind='assert',body=assemble_call(source,codec.dictionary,lanes=lanes)))
        rows.append(dict(title=title,plan=plan,native=dict(kind='assert',body=source)))
    nested=assemble_call(source,codec.dictionary)
    nested['bindings'][0]['value']=assemble_call(values[0],codec.dictionary,lanes=(1,-1))
    plan=dict(form='scope',quotation=True,body=dict(kind='assert',body=nested))
    rows.append(dict(title='引数の定義中に別の分岐を入れる',plan=plan,native=expand_plan(plan,codec.dictionary)))
    variable=dict(kind='variable',name='va');bound=call(give,variable,call(f,variable,a),variable)
    plan=dict(form='scope',quotation=True,body=dict(kind='assert',body=dict(kind='forall',variable='va',sort='individual',
        body=assemble_call(bound,codec.dictionary,lanes=(1,-1,0)))))
    rows.append(dict(title='外側の束縛先を維持した引数の分岐',plan=plan,native=expand_plan(plan,codec.dictionary)))
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');args=p.parse_args()
    old,dictionary,_,selection=baseline.load();dictionary=complete_public_dictionary(dictionary);codec=AssemblyCodec(dictionary)
    trace=json.loads((BASE/'trace.json').read_text(encoding='utf-8'))['cases'];oldrows={r['statement']:r for r in trace}
    from scripts.build_concept2_trunk import pins as oldpins
    pins=oldpins()
    for path in ('scripts/build_concept2_shared_page.py','scripts/concept2_sharing.py','scripts/concept2_assembly.py',
                 'scripts/concept2_codec_v9.py','scripts/concept2_assembly_reader.py','scripts/concept2_compact.py',
                 'scripts/concept2_fast_reader.py','scripts/concept2_document.py','output/kant-concept2-v7/trace.json'):
        pins[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True);results=[];start=time.perf_counter()
    with LongRun(ROOT/args.run,dict(schema='concept2-shared-page-1',sources=pins,output=args.out),resume=args.resume) as run:
        for i,row in enumerate(selection):
            run.emit('progress',stage=f'Kant {i+1}/40',completed=i,total=45)
            def generate():
                chosen=choose_plan(row['public'],codec);tokens=codec.encode(chosen['plan'])
                previous=[tuple(t) for t in oldrows[row['statement']]['tokens']]
                drawing=g.layout(codec.units(tokens))[0]
                previous_svg=(BASE/f'statement-{row["statement"]}.svg').read_text(encoding='utf-8')
                width=lambda shapes:g.bounds(shapes)[2]-g.bounds(shapes)[0]
                if width(drawing['shapes'])>=width(g.from_svg(previous_svg))-1e-3:
                    tokens=previous;drawing=g.layout(codec.units(tokens))[0];chosen['policy']='retained-v7'
                svg=c.svg(drawing['shapes'])
                if codec.read_svg(svg)['native']!=row['public']:raise ValueError('Kant SVG changed native syntax')
                return dict(row,tokens=tokens,drawing=drawing,svg=svg,policy=chosen['policy'])
            result=run.step(f'kant-{row["statement"]}',row,generate);results.append(result)
            (out/f'statement-{row["statement"]}.svg').write_text(result['svg'],encoding='utf-8',newline='\n')
        whole,rows=folded_svg([r['drawing'] for r in results],2200)
        recovered=run.step('whole',dict(svg_sha256=hashlib.sha256(whole.encode()).hexdigest()),lambda:codec.read_page(whole))
        if recovered['statements']!=[r['public'] for r in results]:raise ValueError('Folded Kant changed syntax')
        (out/'kant-reading.svg').write_text(whole,encoding='utf-8',newline='\n')
        examples=controls(codec);cards=[]
        for i,example in enumerate(examples):
            def generate_control():
                tokens=codec.encode(example['plan']);drawing=g.layout(codec.units(tokens))[0]
                svg,rows=folded_svg([drawing],1250)
                if codec.read_page(svg)['statements']!=[example['native']]:raise ValueError('Branch scope or order changed')
                return dict(example,svg=svg,rows=rows,tokens=tokens)
            result=run.step(f'control-{i}',example,generate_control)
            (out/f'branch-{i+1}.svg').write_text(result['svg'],encoding='utf-8',newline='\n')
            cards.append(f'<section><h2>{html.escape(example["title"])}</h2><img src="branch-{i+1}.svg"></section>')
        style='<style>body{margin:32px auto;max-width:1400px;padding:0 24px;font:15px system-ui;color:#283335}h1{font-size:24px}h2{font-size:18px}p{line-height:1.8}img{width:100%;height:auto}section{border-top:1px solid #ddd;margin:32px 0}</style>'
        (out/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>Noema 共有と分岐</title>'+style+'<h1>共有する式と、幹で読む引数</h1><p>カントの元の40項目を保ち、短くなる共有だけを加えています。幹の字形はv4／v7のままです。</p><p><a href="kant-reading.svg">カント四段落</a> · <a href="../kant-concept2-v7/index.html">採用済みv7</a> · <a href="../concept2-dictionary-v3/index.html">共有を広げた辞書</a></p><h2>長い引数を分岐へ渡す</h2><p>以下は構文の対照例です。先に値を局所定義し、その値を幹の参照順で渡します。各定義が複数行に及んでも、順序・束縛・範囲を維持します。</p>'+''.join(cards)+'</html>',encoding='utf-8',newline='\n')
        report=dict(schema='concept2-shared-page-1',source_sha256=pins,kant_native_exact=True,kant_count=40,
            controls_native_exact=True,controls=len(examples),rows=rows,policies=dict(Counter(r['policy'] for r in results)),
            token_counts=dict(Counter(t[0] for r in results for t in r['tokens'])),seconds=time.perf_counter()-start)
        atomic_json(out/'report.json',report);atomic_json(out/'trace.json',dict(cases=[{k:v for k,v in r.items() if k not in ('drawing','svg')} for r in results],controls=examples))
        run.emit('progress',stage='Kant and branch scopes complete',completed=45,total=45)
        print(json.dumps({k:report[k] for k in ('kant_count','controls','policies','seconds')}))


if __name__=='__main__':main()
