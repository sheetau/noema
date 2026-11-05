"""Inventory public reusable entries without importing cumulative validators."""
import argparse,json
from collections import Counter
from pathlib import Path
from scripts.two_work_inventory import ROOT,read,sha
from scripts.two_work_fastparse import parse_source
from scripts.kant_public_lexicon import vocabulary
from scripts.visible_word_forms import symbol
from scripts.concept2_document import full_name,references
from scripts import concept2_composition as c
from scripts.long_run import LongRun,atomic_json,fingerprint


def core():
    v=vocabulary();result={}
    for name in v._order:
        d=v._plain_declaration(name);entry=v.entry(name)
        result[name]=dict(name=name,layer='core',declaration=d,spelling=list(v.word(name).parts),
            symbol=symbol(v.word(name),v),meaning=entry['meaning'],roles=entry['roles'],
            context=entry.get('context',[]),contrast=entry.get('contrast',[]),sources=['noema/resources/visible-senses-vocabulary-v1.json'])
    return result


def profile(path):
    m=read(path);b=read(m['basis']);document=parse_source((ROOT/m['library']).read_text(encoding='utf-8'))
    ds={d['name']:d for d in document['declarations']};primitives=b.get('primitives',{})
    if isinstance(primitives,list):primitives={r['symbol']:r for r in primitives}
    entries={}
    for name,parts in m['spellings'].items():
        d=ds[name];contract=primitives.get(name,{})
        meaning=contract.get('meaning_ja',b.get('definitions',{}).get(name))
        if not meaning:raise ValueError('Missing public meaning: '+name)
        roles=contract.get('arguments',[r['role'] for r in b.get('public_contracts',{}).get(name,{}).get('arguments',[])])
        if len(roles)!=len(d['parameters']):raise ValueError('Role arity differs: '+name)
        entries[name]=dict(name=name,layer='optional',declaration=d,spelling=parts,
            symbol=full_name([c.old.root_symbol(p) for p in parts]),meaning=meaning,roles=roles,
            context=b.get('public_contracts',{}).get(name,{}).get('interpretation_inputs',[]),
            contrast=b.get('limits',[]),sources=[path,m['basis'],m['library']],profile=m['edition'])
    return entries


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--run',required=True);cli.add_argument('--out',required=True);args=cli.parse_args()
    paths=[];pins={'scripts/general_language_inventory.py':sha('scripts/general_language_inventory.py')}
    for p in sorted((ROOT/'noema/resources').glob('visible-*.json')):
        m=read(p)
        if m.get('spellings') and m.get('basis') and m.get('edition',0)>12:
            path=p.relative_to(ROOT).as_posix();paths.append(path)
            for source in (path,m['basis'],m['library']):pins[source]=sha(source)
    # Core vocabulary already validates its own saved manifests and libraries.
    freeze=read('data/writing-freeze-v2.json');pins.update(freeze['source_sha256'])
    output=ROOT/args.out;output.mkdir(parents=True,exist_ok=False)
    with LongRun(ROOT/args.run,dict(source_sha256=pins)) as run:
        entries=run.step('core',pins,core);duplicates=[];issues=[]
        for i,path in enumerate(paths):
            run.emit('progress',stage=path,completed=i,total=len(paths))
            try:additional=run.step(path,pins[path],lambda:profile(path))
            except Exception as error:issues.append(dict(path=path,error=str(error)));continue
            for name,row in additional.items():
                if name in entries:
                    if entries[name]['declaration']!=row['declaration'] or entries[name]['spelling']!=row['spelling']:
                        issues.append(dict(name=name,path=path,error='Conflicting public declaration or spelling'))
                    else:duplicates.append(dict(name=name,path=path))
                else:entries[name]=row
        spellings={};collisions=[]
        for name,row in entries.items():
            key=tuple(row['spelling'])
            if key in spellings and spellings[key]!=name:collisions.append([spellings[key],name])
            spellings[key]=name
            missing=references(row['declaration'])-set(entries)
            if missing:issues.append(dict(name=name,error='Missing public dependency',missing=sorted(missing)))
        result=dict(schema='noema-general-language-inventory-1',source_sha256=pins,entries=entries,issues=issues,
            duplicate_sources=duplicates,spelling_collisions=collisions,
            counts=dict(entries=len(entries),layers=dict(Counter(e['layer'] for e in entries.values())),
                        kinds=dict(Counter(e['declaration']['kind'] for e in entries.values()))))
        atomic_json(output/'inventory.json',result)
        print(json.dumps({k:result[k] for k in ('counts','issues','spelling_collisions')},ensure_ascii=False))


if __name__=='__main__':main()
