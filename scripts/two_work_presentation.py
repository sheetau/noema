"""Show complete main assertions by unfolding explicit nullary definition heads.

This is the same kind of visible expansion used by kant-page. It never unfolds
inside quotation or changes a parameterized application. The exact unexpanded
assertion and definition chain remain available for structural backprojection.
"""
from copy import deepcopy
from pathlib import Path
from scripts.long_run import atomic_json
from scripts.two_work_inventory import ROOT,read,sha
from noema.constructed_discourse import normalize_document


def expand_head(statement,declarations):
    result=deepcopy(statement);steps=[];seen=set()
    if result.get('kind') not in ('assert','ask','perform'):return result,steps
    while result['body'].get('kind')=='call' and not result['body']['arguments']:
        name=result['body']['symbol'];d=declarations[name]
        if d['kind']!='definition' or d['parameters']:break
        if name in seen:raise ValueError('Cyclic head expansion')
        seen.add(name);steps.append(name);result['body']=deepcopy(d['body'])
    return result,steps


def main():
    base=ROOT/'output/two-work-assembly-v2';out=ROOT/'output/two-work-presentation-v1';out.mkdir(parents=True,exist_ok=True)
    report=read('output/two-work-assembly-v2/report.json');pins=dict(report['source_sha256']);results={}
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Assembly dependency changed: '+p)
    pins['scripts/two_work_presentation.py']=sha('scripts/two_work_presentation.py')
    for work in ('kant','einstein'):
        source=read(f'output/two-work-assembly-v2/{work}.json');bridge=read(f'output/two-work-assembly-v2/{work}-bridge.json')
        ds={d['name']:d for d in source['declarations']};document=deepcopy(source);expansions=[]
        for i in range(bridge['source_statement_count']):
            actual,steps=expand_head(source['statements'][i],ds);document['statements'][i]=actual
            expansions.append(dict(statement=i,definitions=steps,unexpanded=source['statements'][i]))
        canonical=normalize_document(document)
        if canonical!=document:raise ValueError('Display expansion changed binding normalization')
        # Reconstruct the complete prior document using only the recorded head
        # replacements after verifying them against the public definitions.
        recovered=deepcopy(document)
        for row in expansions:
            expected,steps=expand_head(row['unexpanded'],ds)
            if expected!=document['statements'][row['statement']] or steps!=row['definitions']:raise ValueError('Expansion evidence differs')
            recovered['statements'][row['statement']]=row['unexpanded']
        if recovered!=source:raise ValueError('Display expansion failed exact backprojection')
        atomic_json(out/(work+'.json'),document);atomic_json(out/(work+'-expansions.json'),expansions)
        for name in (work+'.json',work+'-bridge.json'):pins['output/two-work-assembly-v2/'+name]=sha('output/two-work-assembly-v2/'+name)
        results[work]=dict(main_statements=bridge['source_statement_count'],auxiliary_statements=len(source['statements'])-bridge['source_statement_count'],
            expanded_heads=sum(bool(r['definitions']) for r in expansions),backprojection_exact=True)
        print(work,results[work],flush=True)
    atomic_json(out/'report.json',dict(schema='noema-two-work-presentation-1',source_sha256=pins,works=results))


if __name__=='__main__':main()
