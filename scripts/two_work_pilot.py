"""Bounded preflight on large definitions, type headers and full assertions."""
import argparse,json,time
from pathlib import Path
from scripts.two_work_inventory import ROOT,read,sha
from scripts.two_work_batch import RecordReader,render_record
from scripts.concept2_writing import WritingReader
from scripts.long_run import LongRun,atomic_json


def nodes(v):
    if isinstance(v,list):return sum(nodes(x) for x in v)
    if isinstance(v,dict):return 1+sum(nodes(x) for x in v.values())
    return 0


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args()
    docs={w:read(f'output/two-work-presentation-v1/{w}.json') for w in ('kant','einstein')};items=[]
    for work,doc in docs.items():
        definitions=sorted(((nodes(d),i) for i,d in enumerate(doc['declarations']) if d['kind']=='definition'),reverse=True)
        typed=sorted(((nodes(d['parameters'])+nodes(d['result']),i) for i,d in enumerate(doc['declarations'])),reverse=True)
        assertions=sorted(((nodes(s),i) for i,s in enumerate(doc['statements'])),reverse=True)
        chosen={('declaration',i) for _,i in definitions[:2]+typed[:1]}|{('statement',i) for _,i in assertions[:2]}
        for kind,index in sorted(chosen):items.append(dict(work=work,kind=kind,index=index))
    paths=['scripts/two_work_pilot.py','scripts/two_work_batch.py','data/writing-freeze-v2.json',*[f'output/two-work-presentation-v1/{w}.json' for w in docs]]
    out=ROOT/'output/two-work-pilot-v1';out.mkdir(parents=True,exist_ok=True);results=[]
    with LongRun(ROOT/args.run,dict(sources={p:sha(p) for p in paths},items=items)) as run:
        for j,item in enumerate(items):
            run.emit('progress',stage=str(item),completed=j,total=len(items))
            def generate():
                doc=docs[item['work']];kind=item['kind'];i=item['index']
                record=doc['declarations' if kind=='declaration' else 'statements'][i]
                seed=dict(doc,declarations=doc['declarations'][:i] if kind=='declaration' else doc['declarations'],statements=[])
                writer=WritingReader(seed);reader=RecordReader(seed);start=time.perf_counter()
                tokens=writer.encode_record(record);encoded=time.perf_counter()
                raw,rows=render_record(writer,tokens,2200);rendered=time.perf_counter()
                recovered=reader.read_page(raw)['statements']
                if recovered!=[record]:raise ValueError('Pilot syntax changed')
                finished=time.perf_counter();file=f'{item["work"]}-{kind}-{i}.svg'
                (out/file).write_text(raw,encoding='utf-8',newline='\n')
                return dict(item,native_exact=True,nodes=nodes(record),tokens=len(tokens),rows=rows,svg=file,
                    encode_seconds=encoded-start,render_seconds=rendered-encoded,decode_seconds=finished-rendered)
            try:
                result=run.step(str(j),item,generate)
            except Exception as error:
                result=dict(item,native_exact=False,error=str(error),error_type=type(error).__name__)
            results.append(result);print(json.dumps(result),flush=True)
        atomic_json(out/'report.json',dict(schema='noema-two-work-pilot-1',all_native_exact=all(r['native_exact'] for r in results),cases=results))
        run.emit('progress',stage='Pilot complete',completed=len(items),total=len(items))


if __name__=='__main__':main()
