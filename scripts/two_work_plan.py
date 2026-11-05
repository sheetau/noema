"""Complete source/bridge inventory and meaning-preserving extension plan.

Read saved contracts directly after verifying the completed semantic audit's
content pins. Do not recursively parse historical manuscripts or run models.
"""
import argparse,json,time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from scripts.two_work_inventory import ROOT,SOURCES,sha,read,key
from scripts.two_work_fastparse import parse_source
from scripts.concept2_document import references
from scripts.long_run import LongRun,atomic_json

VISIBLE={'kant':'examples/v016/kant-clerical-conscience-visible-v1.noema',
         'einstein':'examples/v016/einstein-early-visible-v1.noema'}


def meanings(path,pins):
    chain=[];seen=set();entries={}
    while path:
        if path in seen:raise ValueError('Cyclic meaning basis')
        seen.add(path)
        if path not in pins or sha(path)!=pins[path]:raise ValueError('Meaning basis lacks matching audit evidence: '+path)
        b=read(path);chain.append((path,b));path=b.get('inherited_meaning_basis')
    for path,b in reversed(chain):
        primitive=b.get('primitives',{})
        if isinstance(primitive,list):primitive={r['symbol']:r for r in primitive}
        for name,row in primitive.items():
            if name in entries:raise ValueError('Meaning redefinition: '+name)
            entries[name]=dict(kind='primitive',basis=path,contract=deepcopy(row))
        for name,description in b.get('definitions',{}).items():
            if name in entries:raise ValueError('Meaning redefinition: '+name)
            entries[name]=dict(kind='definition',basis=path,meaning_ja=description)
    return entries,[path for path,b in chain]


def closure(statements,declarations):
    seen=set();pending=references(statements)
    while pending:
        name=pending.pop()
        if name not in declarations:raise ValueError('Missing source dependency: '+name)
        if name in seen:continue
        seen.add(name);pending.update(references(declarations[name]))
    return seen


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args()
    state=read('data/work-state.json');index=read(state['review_index']);audit=read(state['progress_report'])
    paths=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'data').glob('*bridge*.json') if 'kant-' in p.name or 'einstein-' in p.name)
    pins={p:sha(p) for p in [*SOURCES.values(),*VISIBLE.values(),*paths,'scripts/two_work_plan.py','scripts/two_work_fastparse.py',state['review_index'],state['progress_report']]}
    output={};start=time.perf_counter();bridges=[]
    with LongRun(ROOT/args.run,dict(source_sha256=pins)) as run:
        docs={}
        for work,path in SOURCES.items():
            run.emit('progress',stage='Active source '+work,completed=len(docs),total=len(paths)+4)
            docs[work]=run.step('source-'+work,dict(path=path,sha256=pins[path]),lambda:parse_source((ROOT/path).read_text(encoding='utf-8')))
        for i,path in enumerate(paths):
            run.emit('progress',stage=path,completed=i+2,total=len(paths)+4)
            def inspect():
                b=read(path);work=next(w for w in SOURCES if w+'-' in Path(path).name)
                indices=b.get('source_statement_indices',[b['source_statement_index']] if 'source_statement_index' in b else [])
                statements=b.get('source_statements',[b['source_assertion']] if 'source_assertion' in b else [])
                matched=[j for j,s in zip(indices,statements) if j<len(docs[work]['statements']) and s==docs[work]['statements'][j]]
                return dict(path=path,work=work,matched=matched,mapping=b.get('local_names',{})|b.get('mapping',{}))
            bridges.append(run.step(path,pins[path],inspect))
        for work,path in VISIBLE.items():
            run.emit('progress',stage='Retained visible '+work,completed=len(paths)+2,total=len(paths)+4)
            visible=run.step('visible-'+work,pins[path],lambda:parse_source((ROOT/path).read_text(encoding='utf-8')))
            ds={d['name']:d for d in docs[work]['declarations']};public={d['name']:d for d in visible['declarations']}
            mapping={};conflicts={};covered=set()
            for b in bridges:
                if b['work']!=work:continue
                covered.update(b['matched'])
                for old,new in b['mapping'].items():
                    if old not in ds or new not in public:continue
                    if old in mapping and mapping[old]!=new:conflicts.setdefault(old,set()).update((mapping[old],new))
                    mapping[old]=new
            entries,chain=meanings(index['works'][work+'-'+('1784' if work=='kant' else '1905')]['meaning_basis'],audit['source_sha256'])
            needed=closure(docs[work]['statements'],ds);unmapped=needed-set(mapping)
            for name in needed:
                row=entries[name];declaration=ds[name]
                if row['kind']!=declaration['kind']:raise ValueError('Meaning kind mismatch')
                if row['kind']=='primitive' and any(row['contract'][k]!=declaration[k] for k in ('parameters','result')):
                    raise ValueError('Meaning signature mismatch: '+name)
            missing=sorted(set(range(len(docs[work]['statements'])))-covered)
            groups=[]
            for i in missing:
                deps=closure([docs[work]['statements'][i]],ds)-set(mapping)
                groups.append(dict(statement=i,root_symbols=sorted(references(docs[work]['statements'][i])),
                    missing_declarations=sorted(deps),basis_counts=dict(Counter(entries[n]['basis'] for n in deps))))
            output[work]=dict(source=SOURCES[work],visible=path,source_declarations=len(ds),source_statements=len(docs[work]['statements']),
                covered=sorted(covered),missing=missing,needed_declarations=len(needed),mapping=mapping,
                mapping_conflicts={n:sorted(v) for n,v in conflicts.items()},unmapped=sorted(unmapped),
                unmapped_kinds=dict(Counter(ds[n]['kind'] for n in unmapped)),
                nullary_primitives=[n for n in sorted(unmapped) if ds[n]['kind']=='primitive' and not ds[n]['parameters']],
                groups=groups,meanings={n:entries[n] for n in sorted(needed)},meaning_sources={p:sha(p) for p in chain},
                visible_declarations=len(public),visible_statements=len(visible['statements']))
            print(work,'source',len(docs[work]['statements']),'covered',len(covered),'missing',missing,
                'unmapped',output[work]['unmapped_kinds'],'conflicts',len(conflicts),flush=True)
        atomic_json(ROOT/'output/two-work-plan-v1.json',dict(schema='noema-two-work-plan-1',source_sha256=pins,works=output,bridges=bridges,seconds=time.perf_counter()-start))
        run.emit('progress',stage='Structural plan complete',completed=len(paths)+4,total=len(paths)+4)


if __name__=='__main__':main()
