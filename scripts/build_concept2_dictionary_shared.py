"""Render only changed record tapes; inherit pinned identical ink evidence."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil
import time
from scripts.build_concept2_dictionary import ROOT,SOURCE,records,inputs
from scripts.concept2_document import DocumentCodec,complete_public_dictionary,full_parts
from scripts.concept2_document_reader import DocumentReader
from scripts.concept2_shared_document import SharedDocumentReader
from scripts import concept2_geometry_v5 as g,concept2_composition as composition
from scripts.long_run import LongRun,atomic_json,fingerprint

BASE=ROOT/'output/concept2-dictionary-v2'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def ink_width(raw):
    bands=[]
    for s in sorted(g.from_svg(raw),key=lambda s:g.bounds([s])[1]):
        left,top,right,bottom=g.bounds([s])
        if not bands or top>bands[-1][1]+1e-3:bands.append([left,bottom,right])
        else:
            bands[-1][0]=min(bands[-1][0],left);bands[-1][1]=max(bands[-1][1],bottom);bands[-1][2]=max(bands[-1][2],right)
    return sum(right-left for left,_,right in bands)


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');args=p.parse_args()
    baseline=json.loads((BASE/'report.json').read_text(encoding='utf-8'))
    if not baseline['native_exact'] or baseline['changed_svg']+baseline['inherited_svg']!=baseline['records']:
        raise ValueError('A completed geometry baseline is required')
    for path,sha in baseline['source_sha256'].items():
        if digest(ROOT/path)!=sha:raise ValueError('Prior geometry implementation or input changed: '+path)
    published=complete_public_dictionary(json.loads((ROOT/SOURCE).read_text(encoding='utf-8')))
    source=records(published);out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
    pins=inputs()
    for path in ('scripts/build_concept2_dictionary_shared.py','scripts/concept2_compact.py','scripts/concept2_fast_reader.py',
                 'scripts/concept2_sharing.py','scripts/concept2_shared_document.py','scripts/concept2_document_reader.py',
                 'tests/test_concept2_sharing.py','output/concept2-dictionary-v2/report.json'):
        pins[path]=digest(ROOT/path)
    manifest=dict(schema='concept2-dictionary-shared-run-1',sources=pins,records_sha256=fingerprint(source),output=args.out)
    old=DocumentReader();writer=SharedDocumentReader();reader=DocumentReader()
    if old.forms!=writer.forms:raise ValueError('Geometry reuse requires identical glyphs')
    results=[];start=time.perf_counter()
    with LongRun(ROOT/args.run,manifest,resume=args.resume) as run:
        for i,(record,prior) in enumerate(zip(source,baseline['items'],strict=True)):
            run.emit('progress',stage=f'{record["kind"]} {i+1}/{len(source)}',completed=i,total=len(source))
            if prior['recovered']!=record:raise ValueError('Baseline statement differs')
            generated=False
            def generate():
                nonlocal generated
                before=old.encode_record(record);after=writer.encode_record(record)
                if digest(BASE/prior['svg'])!=prior['svg_sha256']:raise ValueError('Prior SVG changed')
                file=f'record-{i+1:04d}.svg';unchanged=before==after;rejected=False
                svg=None
                if not unchanged:
                    drawing=g.layout(writer.units(after))[0];folded=g.fold([drawing],2200);shapes=[]
                    for j,row in enumerate(folded):shapes.extend(g.move(row['shapes'],80,80+170*j))
                    svg=composition.svg(shapes,width=2400,height=170*len(folded)+160)
                    if ink_width(svg)>=ink_width((BASE/prior['svg']).read_text(encoding='utf-8'))-1e-3:
                        unchanged=True;rejected=True;after=before
                if unchanged:
                    shutil.copyfile(BASE/prior['svg'],out/file)
                    reader.register(record);rows=prior['rows']
                else:
                    if reader.read_page(svg)['statements']!=[record]:raise ValueError('Changed SVG record differs')
                    (out/file).write_text(svg,encoding='utf-8',newline='\n');rows=len(folded)
                generated=True
                return dict(index=i,kind=record['kind'],name=record['name'],tokens=len(after),previous_tokens=len(before),
                    rows=rows,previous_rows=prior['rows'],svg=file,svg_sha256=digest(out/file),
                    decoding='inherited-identical-tape-and-glyphs' if unchanged else 'fresh-svg',recovered=record,layout_rejected=rejected)
            def validate(result):
                if result['recovered']!=record or digest(out/result['svg'])!=result['svg_sha256']:raise ValueError('Checkpoint content changed')
            result=run.step(f'record-{i+1:04d}',record,generate,validate=validate)
            if not generated:reader.register(result['recovered'])
            old.register(record);writer.register(record);results.append(result)
            if (i+1)%100==0:print(f'{i+1}/{len(source)}; {time.perf_counter()-start:.1f}s',flush=True)
        if reader.document['declarations']!=published['native']['declarations']:raise ValueError('Declarations changed')
        if reader.aliases!={tuple(r['parts']):r['symbol'] for r in published['aliases']}:raise ValueError('Aliases changed')
        if reader.dictionary['selected_spellings']!=published['selected_spellings']:raise ValueError('Selected spelling changed')
        report=dict(schema='concept2-dictionary-shared-1',source_sha256=pins,native_exact=True,alias_mapping_exact=True,
            records=len(source),declarations=len(reader.declarations),aliases=len(reader.aliases),
            changed_svg=sum(r['decoding']=='fresh-svg' for r in results),inherited_svg=sum(r['decoding']!='fresh-svg' for r in results),
            tokens=sum(r['tokens'] for r in results),previous_tokens=sum(r['previous_tokens'] for r in results),
            rows=sum(r['rows'] for r in results),previous_rows=sum(r['previous_rows'] for r in results),
            items=results,seconds=round(time.perf_counter()-start,3))
        atomic_json(out/'dictionary.json',published);atomic_json(out/'report.json',report)
        cards=[]
        kinds={'primitive':'宣言','definition':'定義','spelling':'綴り'}
        for r in results:
            title=' · '.join(composition.old.root_name(p) for p in full_parts(r['name']))
            cards.append(f'<section><h2>{r["index"]+1}. {kinds[r["kind"]]}：{html.escape(title)}</h2><a href="{r["svg"]}"><img loading="lazy" src="{r["svg"]}"></a></section>')
        (out/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>Noema 円文字辞書</title><style>body{margin:32px;font:15px system-ui}h2{font-size:13px;overflow-wrap:anywhere}img{width:100%;height:auto}section{margin:32px 0;border-top:1px solid #ddd}</style><h1>円文字の宣言・定義・綴り</h1><p>上から順に語を登録して読みます。型の反復と長い変数参照を既存の反復記法でまとめています。</p>'+''.join(cards)+'</html>',encoding='utf-8',newline='\n')
        run.emit('progress',stage='Dictionary complete',completed=len(source),total=len(source))
        print(json.dumps({k:report[k] for k in ('records','changed_svg','inherited_svg','tokens','previous_tokens','rows','previous_rows','seconds')}))


if __name__=='__main__':main()
