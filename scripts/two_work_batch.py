"""Record-level ink verification with independent continuation and content reuse.

A failed declaration blocks only its dependants. A cached success is inherited
only with equal source, token tape, transitive dependencies and implementation,
and after hashing the actual SVG. It is never a new semantic judgment.
"""
import argparse,hashlib,json,time,traceback
from collections import Counter
from pathlib import Path
from scripts.concept2_writing import WritingReader
from scripts.concept2_document import references
from scripts import concept2_composition as c,concept2_geometry_v5 as g
from scripts.long_run import LongRun,atomic_json,fingerprint

ROOT=Path(__file__).resolve().parents[1]


class RecordReader(WritingReader):
    def register(self,record):
        # One logical record per SVG: commit only after exact comparison.
        return self.canonical_record(record)

    def commit(self,record):return super().register(record)


def render_record(writer,tokens,width):
    # Bound geometry checks to a physical row instead of building an unbounded
    # line and doing a quadratic whole-line check before folding it again.
    rows=g.layout(writer.units(tokens),max_width=width);shapes=[]
    for i,row in enumerate(rows):shapes.extend(g.move(row['shapes'],80,80+170*i))
    return c.svg(shapes,width=width+160,height=len(rows)*170+160),len(rows)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def process_records(records,out,run,implementation,*,width=2200,renderer=render_record,reuse=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    writer=WritingReader();reader=RecordReader();results=[];verified={};unavailable={};counts=Counter()
    reuse_paths=[Path(p) for p in (reuse if isinstance(reuse,(list,tuple)) else [reuse])] if reuse else []
    for index,record in enumerate(records):
        identity=record.get('name',f'statement-{index}');deps=references(record)
        missing=sorted(deps-set(verified));item=dict(index=index,identity=identity,kind=record['kind'])
        run.emit('progress',stage=identity,completed=index,total=len(records),issues=index-counts['passed'])
        source_key=fingerprint(record)
        def action():
            start=time.perf_counter()
            if missing:return dict(item,status='blocked_dependency',missing=missing,source_sha256=source_key)
            try:
                canonical=writer.canonical_record(record);tokens=writer.encode_record(canonical)
                dependency_hashes={name:verified[name] for name in sorted(deps)}
                cache_key=fingerprint(dict(record=canonical,tokens=tokens,dependencies=dependency_hashes,
                                           implementation=implementation,width=width))
                svg_name=cache_key+'.svg';prior=None
                for cached in reuse_paths:
                    if not (cached/(cache_key+'.json')).is_file():continue
                    try:
                        prior=json.loads((cached/(cache_key+'.json')).read_text(encoding='utf-8'))
                        if (not isinstance(prior,dict) or prior.get('status')!='passed' or prior.get('cache_key')!=cache_key or prior.get('native')!=canonical or
                                sha(cached/svg_name)!=prior.get('svg_sha256')):
                            prior=None
                    except (OSError,ValueError):
                        prior=None
                    if prior is not None:break
                if prior is not None:
                    raw=(cached/svg_name).read_bytes();(out/svg_name).write_bytes(raw)
                    native=prior['native'];rows=prior['rows'];decoding='inherited-unchanged-content'
                else:
                    raw,rows=renderer(writer,tokens,width)
                    decoded=reader.read_page(raw)['statements']
                    if decoded!=[canonical]:raise ValueError('Recovered syntax differs from source record')
                    native=decoded[0];decoding='fresh-ink'
                    (out/svg_name).write_text(raw,encoding='utf-8',newline='\n')
                result=dict(item,status='passed',source_sha256=source_key,cache_key=cache_key,svg=svg_name,
                    svg_sha256=sha(out/svg_name),native=native,rows=rows,tokens=len(tokens),decoding=decoding,
                    dependency_sha256=dependency_hashes,seconds=time.perf_counter()-start)
                atomic_json(out/(cache_key+'.json'),result)
                return result
            except Exception as error:
                return dict(item,status='failed',source_sha256=source_key,error_type=type(error).__name__,
                            error=str(error),traceback=traceback.format_exc(),seconds=time.perf_counter()-start)
        def validate(result):
            if result['source_sha256']!=source_key:raise ValueError('Checkpoint source changed')
            if result['status']=='passed':
                if sha(out/result['svg'])!=result['svg_sha256']:raise ValueError('Checkpoint ink changed')
                if result['native']!=record:raise ValueError('Checkpoint syntax changed')
        result=run.step(str(index),dict(record=record,verified_dependencies={n:verified.get(n) for n in sorted(deps)}),action,validate=validate)
        if result['status']=='passed':
            # The reader receives only recovered or hash-verified prior results.
            reader.commit(result['native']);writer.register(record)
            if record['kind'] in ('primitive','definition'):
                verified[record['name']]=fingerprint([record,result['dependency_sha256']])
        elif record['kind'] in ('primitive','definition'):
            unavailable[record['name']]=result['status']
        results.append(result)
        counts[result['status']]+=1
        if (index+1)%100==0:print(f'{index+1}/{len(records)}: {dict(counts)}',flush=True)
        atomic_json(out/'status.json',dict(completed=index+1,total=len(records),counts=dict(counts)))
    counts=dict(counts)
    report=dict(schema='noema-record-ink-batch-1',scan_complete=True,validation_success=counts.get('passed',0)==len(records),
        counts=counts,records=results,implementation=implementation,unavailable_declarations=unavailable)
    atomic_json(out/'report.json',report)
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True)
    p.add_argument('--run',required=True);p.add_argument('--reuse');p.add_argument('--resume',action='store_true');args=p.parse_args()
    source=Path(args.input);document=json.loads(source.read_text(encoding='utf-8'))
    records=document['declarations']+document['statements']
    freeze=json.loads((ROOT/'data/writing-freeze-v2.json').read_text(encoding='utf-8'))
    pins=dict(freeze['source_sha256'])
    for path,expected in pins.items():
        if sha(ROOT/path)!=expected:raise ValueError('Frozen implementation changed: '+path)
    pins['scripts/two_work_batch.py']=sha(Path(__file__))
    implementation=fingerprint(pins)
    with LongRun(ROOT/args.run,dict(input_sha256=sha(source),sources=pins,output=args.out,reuse=args.reuse),resume=args.resume) as run:
        result=process_records(records,ROOT/args.out,run,implementation,reuse=args.reuse)
        run.emit('progress',stage='Scan complete',completed=len(records),total=len(records),validation_success=result['validation_success'],counts=result['counts'])
        print(json.dumps({k:result[k] for k in ('scan_complete','validation_success','counts')}))


if __name__=='__main__':main()
