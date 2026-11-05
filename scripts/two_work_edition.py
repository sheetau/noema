"""Arrange both works by saved source-unit bindings, preserving all annotations."""
from collections import defaultdict
from copy import deepcopy
from scripts.two_work_inventory import ROOT,read,sha
from scripts.two_work_fastparse import parse_source
from scripts.long_run import atomic_json,fingerprint


def review_order(review,entry,source,kind):
    hashes={r['index']:r['sha256'] for r in review['selection']['statements']}
    active_hashes=defaultdict(list)
    for n in entry['statements']:active_hashes[fingerprint(source['statements'][n])].append(n)
    body=review.get('source_order_statements',list(hashes))
    notes=review.get('attached_note_statements',[])
    complete=list(dict.fromkeys(body+notes))
    if set(complete)!=set(hashes):raise ValueError('Incomplete recorded source order: '+entry['review'])
    mapped={}
    for old in complete:
        candidates=active_hashes.get(hashes[old],[])
        if not candidates:raise ValueError('Source-order binding no longer matches: '+entry['review'])
        mapped[old]=candidates.pop(0)
    if set(mapped.values())!=set(entry['statements']):raise ValueError('Source-order binding omits an active statement')
    selected=notes if kind=='author_note' and notes else body
    return [mapped[i] for i in selected]


def main():
    state=read('data/work-state.json');index=read(state['review_index'])
    out=ROOT/'output/two-work-edition-v1';out.mkdir(parents=True,exist_ok=True)
    prior=read('output/two-work-presentation-v1/report.json');pins=dict(prior['source_sha256']);works={}
    pins['scripts/two_work_edition.py']=sha('scripts/two_work_edition.py')
    for work,workid in (('kant','kant-1784'),('einstein','einstein-1905')):
        active=index['works'][workid];source=parse_source((ROOT/active['document']).read_text(encoding='utf-8'))
        document=read(f'output/two-work-presentation-v1/{work}.json')
        inventory=read(active['source_inventory']);bindings=defaultdict(list)
        kinds={u['id']:u['kind'] for u in inventory['units']}
        for entry in active['reviews']:
            review=read(entry['review']);pins[entry['review']]=sha(entry['review'])
            selected=review_order(review,entry,source,kinds[review['unit']])
            bindings[review['unit']].extend(n for n in selected if n not in bindings[review['unit']])
        seen=set();order=[];units=[]
        for unit in inventory['units']:
            if unit['kind']=='editorial':continue
            selected=bindings[unit['id']]
            if not selected:raise ValueError('No active review binding for source unit '+unit['id'])
            fresh=[i for i in selected if i not in seen];seen.update(fresh);order.extend(fresh)
            units.append(dict(unit,statements=selected,first_occurrence=fresh))
        if seen!=set(range(len(source['statements']))):raise ValueError('Source units do not cover all assertions')
        count=len(source['statements']);order+=list(range(count,len(document['statements'])))
        reordered=dict(document,statements=[deepcopy(document['statements'][i]) for i in order])
        positions={old:new for new,old in enumerate(order)}
        if [reordered['statements'][positions[i]] for i in range(len(order))]!=document['statements']:
            raise ValueError('Publication order changed syntax or annotations')
        for unit in units:
            unit['edition_statements']=[positions[i] for i in unit['statements']]
            unit['edition_first_occurrence']=[positions[i] for i in unit['first_occurrence']]
        identifiers=read(active['identifier_annotations'])
        atomic_json(out/(work+'.json'),reordered)
        atomic_json(out/(work+'-toc.json'),dict(work=workid,main_statements=count,source_to_edition=positions,
            units=units,math=inventory['math'],annotations=inventory['annotations'],identifiers=identifiers,
            interpretation='Preserved registered reading; this is source alignment, not a new semantic review.'))
        for path in (active['source_inventory'],active['identifier_annotations'],f'output/two-work-presentation-v1/{work}.json'):
            pins[path]=sha(path)
        works[work]=dict(main_statements=count,units=len(units),annotations=len(document['statements'])-count,
            declarations=len(document['declarations']),records=len(document['declarations'])+len(document['statements']),
            publication_order_backprojection_exact=True)
        print(work,works[work],flush=True)
    for path,expected in pins.items():
        if sha(path)!=expected:raise ValueError('Edition input changed: '+path)
    atomic_json(out/'report.json',dict(schema='noema-two-work-edition-1',source_sha256=pins,works=works))


if __name__=='__main__':main()
