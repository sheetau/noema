"""Inventory retained structural bridges without importing old semantic suites."""
import argparse,hashlib,json,time
from pathlib import Path
from scripts.long_run import LongRun,atomic_json

ROOT=Path(__file__).resolve().parents[1]
SOURCES={'kant':'examples/v016/kant-reviewed-complete-v1.noema',
         'einstein':'examples/v014/einstein-auxiliary-reference-order-v1.noema'}
NATIVE={'kant':'examples/v016/kant-clerical-conscience-visible-v1.noema',
        'einstein':'examples/v016/einstein-tenth-closing-visible-v1.noema'}


def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def key(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--resume',action='store_true');args=p.parse_args()
    from noema.constructed import parse
    paths=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'data').glob('*visible-bridge*.json'))
    pins={p:sha(p) for p in [*SOURCES.values(),*NATIVE.values(),*paths,'scripts/two_work_inventory.py']}
    documents={};bridges=[];start=time.perf_counter()
    with LongRun(ROOT/args.run,dict(sources=pins),resume=args.resume) as run:
        for work,path in {**SOURCES,**{k+'-visible':v for k,v in NATIVE.items()}}.items():
            run.emit('progress',stage='Parse '+work,completed=len(documents),total=len(paths)+4)
            documents[work]=run.step(work,dict(path=path,sha256=pins[path]),lambda:parse((ROOT/path).read_text(encoding='utf-8')))
            print(work,len(documents[work]['declarations']),len(documents[work]['statements']),flush=True)
        for i,path in enumerate(paths):
            run.emit('progress',stage=path,completed=i+4,total=len(paths)+4)
            def inspect():
                b=read(path);work=next((w for w in SOURCES if w in b.get('source_document','')),None)
                if work is None:return dict(path=path,work=None)
                source=documents[work];indices=b.get('source_statement_indices',[]);statements=b.get('source_statements',[])
                matched=[j for j,s in zip(indices,statements) if j<len(source['statements']) and s==source['statements'][j]]
                return dict(path=path,work=work,source=b.get('source_document'),matched=matched,
                    stated=indices,mapping=b.get('mapping',{}),visible_indices=b.get('visible_statement_indices'),
                    source_declarations={d['name']:key(d) for d in b.get('source_declarations',[])})
            bridges.append(run.step(path,dict(sha256=pins[path]),inspect))
        result={}
        for work,path in SOURCES.items():
            source=documents[work];selected=[b for b in bridges if b['work']==work];covered={j for b in selected for j in b['matched']}
            mappings={};conflicts={}
            for b in selected:
                for name,public in b['mapping'].items():
                    mappings.setdefault(name,set()).add(public)
            result[work]=dict(source=path,declarations=len(source['declarations']),statements=len(source['statements']),
                covered=sorted(covered),missing=sorted(set(range(len(source['statements'])))-covered),
                unmapped_declarations=[d['name'] for d in source['declarations'] if d['name'] not in mappings],
                mapping_conflicts={n:sorted(v) for n,v in mappings.items() if len(v)>1},
                mapping={n:next(iter(v)) for n,v in mappings.items() if len(v)==1},
                retained_visible=dict(path=NATIVE[work],declarations=len(documents[work+'-visible']['declarations']),statements=len(documents[work+'-visible']['statements'])))
        output=dict(schema='noema-two-work-inventory-1',source_sha256=pins,works=result,bridges=bridges,seconds=time.perf_counter()-start)
        atomic_json(ROOT/'output/two-work-inventory-v1.json',output)
        run.emit('progress',stage='Inventory complete',completed=len(paths)+4,total=len(paths)+4)
        print(json.dumps({w:{k:v for k,v in r.items() if k not in ('mapping','mapping_conflicts')} for w,r in result.items()},ensure_ascii=False))


if __name__=='__main__':main()
