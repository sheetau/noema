"""Visible decoding of the additions and contrasting native uses, record by record."""
import argparse, json
from copy import deepcopy
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document
from scripts.general_language import entries, dependencies
from scripts.general_probability import raw as probability, num
from scripts.general_pragmatics import raw as pragmatics, lam, truth, I, T, v, call
from scripts.check_general_pragmatics import fixture, value
from scripts.two_work_assemble import renamed
from scripts.two_work_inventory import ROOT, sha, read
from scripts.two_work_repair import RepairWritingReader
from scripts.concept2_document import full_name
from scripts import concept2_composition as c, two_work_batch as batch
from scripts.long_run import LongRun, atomic_json, fingerprint


def prepare():
    added=probability()+pragmatics(); declarations=dependencies([d['name'] for d in added]); existing={d['name'] for d in declarations}
    statements=[]; examples=[]
    for index,declaration in enumerate(pragmatics()):
        name=declaration['name']; d,m,expected,values=fixture(name)
        assert value(d,m) is True
        mapping={n:'example'+chr(97+index)+n for n in m}
        for item in d['declarations']:
            item=renamed(item,mapping)
            if item['name'] not in existing:declarations.append(item);existing.add(item['name'])
        positive=renamed(d['statements'][0],mapping);negative=deepcopy(positive)
        # Replace one explicit input relation by the everywhere-false relation.
        relation=next(iter(expected))
        slot=next(i for i,p in enumerate(declaration['parameters']) if p['name']==relation)
        sort=declaration['parameters'][slot]['sort']
        negative['body']['arguments'][slot]=lam([('arg'+chr(97+i),t) for i,t in enumerate(sort['parameters'])],truth(False))
        altered=deepcopy(d);altered['statements'][0]['body']['arguments'][slot]=negative['body']['arguments'][slot]
        assert value(altered,m) is False
        examples.append(dict(name=name,positive=len(statements),negative=len(statements)+1,changed_relation=relation,
            expected=[True,False],scope='二値の解釈で同じ構成の成立と不成立を区別する機構例。自然文の翻訳済み判定ではない。'))
        statements.extend([positive,negative])
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=statements))
    lexical={n:r['symbol'] for n,r in entries().items()};occupied=set(lexical.values())
    roots=('home','above','give','inside','aki','nao','book','round','treeone','fruit','birdone','rain');serial=0
    local=[]
    for item in document['declarations']:
        name=item['name']
        if name in lexical:continue
        while True:
            n=serial;serial+=1;parts=('book','rain','inside',roots[n//144],roots[(n//12)%12],roots[n%12])
            symbol=full_name([c.old.root_symbol(p) for p in parts])
            if symbol not in occupied:break
        lexical[name]=symbol;occupied.add(symbol);local.append(dict(name=name,symbol=symbol,spelling=parts,
            role='対照用解釈の入力。共通概念の追加や自然文内容の代用ではない。'))
    visible=normalize_document(renamed(document,lexical))
    return document,visible,dict(examples=examples,local_inputs=local,mapping={d['name']:lexical[d['name']] for d in document['declarations']})


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');args=p.parse_args()
    pins=read('data/writing-freeze-v2.json')['source_sha256'].copy()
    for path,digest in pins.items():
        if sha(path)!=digest:raise ValueError('Frozen writer changed: '+path)
    for path in ['scripts/general_language_ink.py','scripts/general_language.py','scripts/general_pragmatics.py','scripts/general_probability.py',
                 'scripts/check_general_pragmatics.py','scripts/two_work_batch.py','scripts/two_work_repair.py','data/general-language-catalog-v1.json']:
        pins[path]=sha(path)
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
    with LongRun(ROOT/args.run,dict(source_sha256=pins,output=args.out),resume=args.resume) as run:
        source,visible,alignment=run.step('prepare',pins,prepare)
        atomic_json(out/'source.json',source);atomic_json(out/'document.json',visible);atomic_json(out/'examples.json',alignment)
        (out/'source.noema').write_text(format_graph(source,'compact')+'\n',encoding='utf-8',newline='\n')
        (out/'visible.noema').write_text(format_graph(visible,'compact')+'\n',encoding='utf-8',newline='\n')
        previous=batch.WritingReader;batch.WritingReader=RepairWritingReader
        try:report=batch.process_records(visible['declarations']+visible['statements'],out/'ink',run,fingerprint(pins))
        finally:batch.WritingReader=previous
        atomic_json(out/'report.json',dict(**report,source_sha256=pins,alignment=alignment))
        print(json.dumps(dict(records=len(report['records']),counts=report['counts'])))


if __name__=='__main__':main()
