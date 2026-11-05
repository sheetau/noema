"""Pinned, incremental dictionary publication; one durable step per record."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import time
from scripts.concept2_document import DocumentCodec,complete_public_dictionary,full_parts
from scripts import concept2_geometry_v5 as g,concept2_composition as composition
from scripts.long_run import LongRun,PauseRequested,atomic_json,fingerprint

ROOT=Path(__file__).resolve().parents[1]
SOURCE='output/kant-presentation-spellings/dictionary.json'


def records(published):
    result=[]
    aliases={}
    for row in published['aliases']:aliases.setdefault(row['symbol'],[]).append(row['parts'])
    for d in published['native']['declarations']:
        result.append(d)
        selected=published['selected_spellings'][d['name']]
        alternatives=[p for p in aliases[d['name']] if p!=full_parts(d['name'])]
        alternatives.sort(key=lambda p:(p==selected,p))
        result.extend(dict(kind='spelling',name=d['name'],parts=[composition.old.root_name(p) for p in parts]) for parts in alternatives)
    return result


def inputs():
    # Transitive code dependencies, rather than only entry-point mtimes.
    from scripts.build_concept2_trunk import pins
    paths=set(pins())|{SOURCE,'scripts/concept2_codec_v8.py','scripts/concept2_document.py',
        'scripts/build_concept2_dictionary.py','scripts/kant_lexical_context.py',
        'scripts/kant_public_lexicon.py','scripts/visible_word_forms.py','scripts/long_run.py'}
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--geometry',action='store_true');parser.add_argument('--resume',action='store_true')
    parser.add_argument('--stop-after',type=int);args=parser.parse_args()
    published=complete_public_dictionary(json.loads((ROOT/SOURCE).read_text(encoding='utf-8')))
    source=records(published);out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
    manifest=dict(schema='concept2-dictionary-run-1',sources=inputs(),geometry=args.geometry,
        records_sha256=fingerprint(source),output=args.out)
    writer=DocumentCodec();reader=DocumentCodec();results=[];start=time.perf_counter()
    with LongRun(ROOT/args.run,manifest,resume=args.resume) as run:
        for i,record in enumerate(source):
            if args.stop_after is not None and i>=args.stop_after:raise PauseRequested('Requested pilot boundary')
            run.emit('progress',stage=f'{record["kind"]} {i+1}/{len(source)}',completed=i,total=len(source))
            generated=False
            def generate():
                nonlocal generated
                t=time.perf_counter();tokens=writer.encode_record(record)
                result=dict(index=i,kind=record['kind'],name=record['name'],tokens=len(tokens))
                if args.geometry:
                    drawing=g.layout(writer.units(tokens))[0]
                    rows=g.fold([drawing],2200);shapes=[]
                    for j,row in enumerate(rows):shapes.extend(g.move(row['shapes'],80,80+170*j))
                    svg=composition.svg(shapes,width=2400,height=170*len(rows)+160)
                    recovered=reader.read_page(svg)['statements']
                    if recovered!=[record]:raise ValueError('Visible dictionary record changed native syntax')
                    file=f'record-{i+1:04d}.svg';(out/file).write_text(svg,encoding='utf-8',newline='\n')
                    result.update(svg=file,svg_sha256=hashlib.sha256(svg.encode()).hexdigest(),rows=len(rows))
                else:
                    if reader.parse(tokens)!=record:raise ValueError('Record grammar changed native syntax')
                generated=True
                return dict(result,recovered=record,seconds=round(time.perf_counter()-t,4))
            def validate(row):
                if row['recovered']!=record:raise ValueError('Checkpoint native differs')
                if args.geometry and hashlib.sha256((out/row['svg']).read_bytes()).hexdigest()!=row['svg_sha256']:
                    raise ValueError('Published SVG changed since checkpoint')
            result=run.step(f'record-{i+1:04d}',record,generate,validate=validate)
            if not generated:reader.register(result['recovered'])
            writer.register(record);results.append(result)
            if (i+1)%25==0:print(f'{i+1}/{len(source)} records; {time.perf_counter()-start:.1f}s',flush=True)
        if reader.document['declarations']!=published['native']['declarations']:raise ValueError('Dictionary declarations changed')
        expected={tuple(r['parts']):r['symbol'] for r in published['aliases']}
        if reader.aliases!=expected:raise ValueError('Dictionary aliases changed')
        if reader.dictionary['selected_spellings']!=published['selected_spellings']:raise ValueError('Selected spellings changed')
        atomic_json(out/'dictionary.json',published)
        report=dict(schema='concept2-dictionary-1',records=len(source),declarations=len(reader.declarations),
            aliases=len(reader.aliases),source_sha256=manifest['sources'],geometry_decoded=args.geometry,
            native_exact=True,alias_mapping_exact=True,items=results,seconds=round(time.perf_counter()-start,3))
        atomic_json(out/'report.json',report)
        if args.geometry:
            cards=[]
            for row in results:
                cards.append(f'<section><h2>{row["index"]+1}. {html.escape(row["kind"])} · {html.escape(row["name"])}</h2><a href="{row["svg"]}"><img loading="lazy" src="{row["svg"]}"></a></section>')
            (out/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>Noema 円文字辞書</title><style>body{margin:32px;font:15px system-ui}h2{font-size:13px;overflow-wrap:anywhere}img{width:100%;height:auto}section{margin:32px 0;border-top:1px solid #ddd}</style><h1>円文字の宣言・定義・綴り</h1><p>各項目を上から順に読み、後の項目で使用します。既知の語の番号や元の定義を復号器へ渡さず、図形から登録しています。</p>'+''.join(cards)+'</html>',encoding='utf-8',newline='\n')
        print(json.dumps({k:report[k] for k in ('records','declarations','aliases','geometry_decoded','native_exact','seconds')},ensure_ascii=False))


if __name__=='__main__':main()
