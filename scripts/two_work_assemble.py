"""Join retained visible documents with unchanged, explicitly named source terms.

This is a structural publication adapter. It does not create source primitives,
invent meanings, replace definitions with atoms, or rerun semantic evaluations.
Every newly published term keeps its existing declaration and reviewed contract.
"""
import argparse,json,time
from collections import defaultdict,deque
from copy import deepcopy
from pathlib import Path
from scripts.two_work_inventory import ROOT,SOURCES,sha,read
from scripts.two_work_plan import closure
from scripts.two_work_fastparse import parse_source
from scripts.concept2_document import full_name,full_parts,references
from scripts import concept2_composition as c
from scripts.visible_word_forms import read_symbol
from scripts.kant_public_lexicon import vocabulary
from noema.constructed_discourse import normalize_document
from scripts.long_run import LongRun,atomic_json,fingerprint


def renamed(value,mapping):
    if isinstance(value,list):return [renamed(v,mapping) for v in value]
    if isinstance(value,dict):return {k:(mapping.get(v,v) if k=='symbol' or k=='name' and value.get('kind') in ('primitive','definition') else renamed(v,mapping)) for k,v in value.items()}
    return deepcopy(value)


def allocate(declarations,existing,work):
    # Ordinary root-composed lexical names, each explicitly declared. No hidden
    # document row number enters either the glyph reader or lexical meaning.
    roots=('home','above','give','inside','aki','nao','book','round','treeone','fruit','birdone','rain')
    prefix=('treeone','book','home' if work=='kant' else 'give')
    mapping={};serial=0
    for d in declarations:
        while True:
            n=serial;serial+=1;tail=[]
            for _ in range(4):tail.append(roots[n%len(roots)]);n//=len(roots)
            if n:raise ValueError('Lexical allocation exhausted; expand explicitly')
            name=full_name([c.old.root_symbol(p) for p in (*prefix,*reversed(tail))])
            if name not in existing:break
        existing.add(name);mapping[d['name']]=name
    return mapping


def source_order(source_statements,visible_statements,mapping):
    available=defaultdict(deque)
    for i,statement in enumerate(visible_statements):available[fingerprint(statement)].append(i)
    selected=[]
    for statement in source_statements:
        expected=renamed(statement,mapping);matches=available[fingerprint(expected)]
        if not matches:raise ValueError('Missing exact source assertion in assembled document')
        selected.append(matches.popleft())
    used=set(selected);order=selected+[i for i in range(len(visible_statements)) if i not in used]
    inverse={old:new for new,old in enumerate(order)}
    return [visible_statements[i] for i in order],selected,inverse


def assemble(work,plan):
    source=parse_source((ROOT/plan['source']).read_text(encoding='utf-8'))
    visible=parse_source((ROOT/plan['visible']).read_text(encoding='utf-8'))
    original_visible=deepcopy(visible)
    ds={d['name']:d for d in source['declarations']};mapping=dict(plan['mapping'])
    missing=closure([source['statements'][i] for i in plan['missing']],ds)-set(mapping)
    added=[d for d in source['declarations'] if d['name'] in missing]
    extension=allocate(added,{d['name'] for d in visible['declarations']},work);mapping.update(extension)
    # Earlier proper-name spelling envelopes are replaced by explicit compound
    # names. Referent definitions and all uses are alpha-renamed together.
    proper={};reserved={d['name'] for d in visible['declarations']}|set(extension.values())
    for d in visible['declarations']:
        if not d['name'].startswith('wp'):continue
        parts=read_symbol(d['name'],vocabulary()).parts
        name=full_name([c.old.root_symbol(p) for p in ('aki','book','inside',*parts)])
        if name in reserved:raise ValueError('Proper-name adapter collision')
        reserved.add(name);proper[d['name']]=name
    visible=renamed(visible,proper);mapping={a:proper.get(b,b) for a,b in mapping.items()}
    new_declarations=renamed(added,mapping)
    combined=dict(visible,declarations=visible['declarations']+new_declarations,
        statements=visible['statements']+renamed([source['statements'][i] for i in plan['missing']],mapping))
    combined['schema_version']=combined['lexicon_version']='0.16'
    combined=normalize_document(combined)
    # Exact structural preservation, separately from any old bridge's semantic
    # abstraction or reference specialization.
    if renamed(dict(combined,declarations=combined['declarations'][:len(visible['declarations'])],
                    statements=combined['statements'][:len(visible['statements'])]),{v:k for k,v in proper.items()})!=original_visible:
        raise ValueError('Retained native document changed')
    inverse={v:k for k,v in mapping.items()}
    if renamed(combined['declarations'][len(visible['declarations']):],inverse)!=added:
        raise ValueError('Extension declarations did not backproject exactly')
    if renamed(combined['statements'][len(visible['statements']):],inverse)!=[source['statements'][i] for i in plan['missing']]:
        raise ValueError('Extension statements did not backproject exactly')
    for d in combined['declarations']:full_parts(d['name'])
    contracts={mapping[d['name']]:dict(source_symbol=d['name'],source_declaration=d,
        published_declaration=renamed(d,mapping),**plan['meanings'][d['name']]) for d in added}
    combined['statements'],selected,positions=source_order(source['statements'],combined['statements'],mapping)
    source_links={str(i):dict(kind='new-exact-projection' if i in plan['missing'] else 'retained-bridge',
                            statement=i,previous_statement=old) for i,old in enumerate(selected)}
    if [combined['statements'][positions[i]] for i in range(len(visible['statements']))]!=visible['statements']:
        raise ValueError('Source ordering lost retained statements')
    return dict(document=combined,mapping=mapping,proper_names=proper,extension_contracts=contracts,
        source_links=source_links,retained_positions=positions,source_statement_count=len(source['statements']),
        retained=dict(declarations=len(visible['declarations']),statements=len(visible['statements'])),
        added=dict(declarations=len(added),primitives=sum(d['kind']=='primitive' for d in added),statements=len(plan['missing'])),
        new_source_primitives=0,retained_native_exact=True,extension_backprojection_exact=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args()
    plan=read('output/two-work-plan-v1.json');out=ROOT/'output/two-work-assembly-v2';out.mkdir(parents=True,exist_ok=True)
    pins=dict(plan['source_sha256'])
    for w in plan['works'].values():pins.update(w['meaning_sources'])
    for p in ('scripts/two_work_assemble.py','output/two-work-plan-v1.json'):pins[p]=sha(p)
    for path,expected in pins.items():
        if sha(path)!=expected:raise ValueError('Preparation input changed: '+path)
    reports={}
    with LongRun(ROOT/args.run,dict(source_sha256=pins)) as run:
        for i,(work,p) in enumerate(plan['works'].items()):
            run.emit('progress',stage='Assemble '+work,completed=i,total=2)
            result=run.step(work,dict(source_sha256=pins,plan=fingerprint(p)),lambda:assemble(work,p))
            atomic_json(out/(work+'.json'),result['document'])
            atomic_json(out/(work+'-bridge.json'),{k:v for k,v in result.items() if k!='document'})
            reports[work]={k:v for k,v in result.items() if k not in ('document','mapping','proper_names','extension_contracts','source_links','retained_positions')}
            print(work,reports[work],flush=True)
        atomic_json(out/'report.json',dict(schema='noema-two-work-assembly-1',source_sha256=pins,works=reports,
            status='structural_assembly_only_visible_decoding_pending'))
        run.emit('progress',stage='Structural assembly complete',completed=2,total=2)


if __name__=='__main__':main()
