"""Read the published dictionary, Kant and controls through the unified entry."""
import argparse,hashlib,json,time
from pathlib import Path
from scripts.concept2_writing import WritingReader
from scripts.long_run import LongRun,atomic_json

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--resume',action='store_true');args=p.parse_args()
    dictionary=read('output/concept2-dictionary-v3/report.json');kant=read('output/kant-concept2-v9/trace.json')
    extended=read('output/kant-concept2-v7/extended-trace.json')['cases'];items=[]
    for r in dictionary['items']:
        items.append(dict(path='output/concept2-dictionary-v3/'+r['svg'],sha256=r['svg_sha256'],expected=[r['recovered']]))
    items.append(dict(path='output/kant-concept2-v9/kant-reading.svg',expected=[r['public'] for r in kant['cases']]))
    for i,r in enumerate(kant['controls']):items.append(dict(path=f'output/kant-concept2-v9/branch-{i+1}.svg',expected=[r['native']]))
    for r in extended:items.append(dict(path='output/kant-concept2-v7/extended-'+r['key']+'.svg',expected=[r['source']]))
    for item in items:
        actual=digest(item['path'])
        if item.get('sha256',actual)!=actual:raise ValueError('Published SVG changed: '+item['path'])
        item['sha256']=actual
    paths=['scripts/check_concept2_writing.py','scripts/concept2_writing.py','scripts/concept2_codec_v9.py',
        'scripts/concept2_assembly.py','scripts/concept2_assembly_reader.py','scripts/concept2_shared_document.py',
        'scripts/concept2_document_reader.py','scripts/concept2_document.py','scripts/concept2_compact.py',
        'scripts/concept2_fast_reader.py','scripts/concept2_codec_v8.py','scripts/concept2_geometry_v5.py',
        'scripts/concept2_sharing.py','scripts/concept2_composition.py','scripts/kant_type_grammar.py',
        'noema/constructed_discourse.py','output/concept2-dictionary-v3/report.json',
        'output/kant-concept2-v9/trace.json','output/kant-concept2-v7/extended-trace.json']
    pins={path:digest(path) for path in paths};reader=WritingReader();results=[];start=time.perf_counter()
    with LongRun(ROOT/args.run,dict(schema='concept2-unified-reader-1',sources=pins,items=items),resume=args.resume) as run:
        for i,item in enumerate(items):
            run.emit('progress',stage=item['path'],completed=i,total=len(items));generated=False
            def generate():
                nonlocal generated
                recovered=reader.read_page((ROOT/item['path']).read_text(encoding='utf-8'))['statements']
                if recovered!=item['expected']:raise ValueError('Unified reader changed syntax: '+item['path'])
                generated=True
                return dict(path=item['path'],sha256=item['sha256'],native=recovered)
            def validate(result):
                if result['native']!=item['expected'] or digest(item['path'])!=result['sha256']:raise ValueError('Checkpoint differs')
            result=run.step(str(i),item,generate,validate=validate)
            if not generated:
                for record in result['native']:reader.register(record)
            results.append(dict(path=item['path'],sha256=item['sha256'],records=len(result['native'])))
            if (i+1)%200==0:print(f'{i+1}/{len(items)}; {time.perf_counter()-start:.1f}s',flush=True)
        report=dict(schema='concept2-unified-reader-1',source_sha256=pins,all_native_exact=True,svg_files=len(items),
            dictionary_records=len(dictionary['items']),declarations=len(reader.document['declarations']),
            spelling_records=len(reader.spellings),statements=len(reader.document['statements']),
            decoder_inputs='SVG ink and only the declarations/spellings recovered from earlier SVGs',
            files=results,seconds=round(time.perf_counter()-start,3))
        atomic_json(ROOT/'output/concept2-unified-reader-v1.json',report)
        run.emit('progress',stage='Unified reader complete',completed=len(items),total=len(items))
        print(json.dumps({k:report[k] for k in ('all_native_exact','svg_files','declarations','spelling_records','statements','seconds')}))


if __name__=='__main__':main()
