"""Publish every dictionary declaration, reusing exact retained ink evidence."""
import argparse, json
from noema.constructed_discourse import normalize_document
from scripts.general_language import entries, dependencies
from scripts.two_work_assemble import renamed
from scripts.two_work_inventory import ROOT, read, sha
from scripts.two_work_repair import RepairWritingReader
from scripts import two_work_batch as batch
from scripts.long_run import LongRun, atomic_json, fingerprint


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');args=p.parse_args()
    catalog=entries();mapping={n:r['symbol'] for n,r in catalog.items()}
    document=normalize_document(renamed(dict(schema_version='0.16',lexicon_version='0.16',declarations=dependencies(catalog),statements=[]),mapping))
    freeze=read('data/writing-freeze-v2.json');pins=freeze['source_sha256'].copy()
    for path,digest in pins.items():
        if sha(path)!=digest:raise ValueError('Frozen implementation changed: '+path)
    implementation=fingerprint(dict(pins,batch=sha('scripts/two_work_batch.py')))
    for path in ['scripts/general_catalog_ink.py','scripts/general_language.py','scripts/two_work_assemble.py',
                 'scripts/two_work_batch.py','scripts/two_work_repair.py','data/general-language-catalog-v1.json']:
        pins[path]=sha(path)
    reuse=[ROOT/'output/two-work-final-v2'/work/'ink' for work in ('kant','einstein')]
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
    atomic_json(out/'document.json',document)
    with LongRun(ROOT/args.run,dict(source_sha256=pins,output=args.out,reuse=list(map(str,reuse))),resume=args.resume) as run:
        previous=batch.WritingReader;batch.WritingReader=RepairWritingReader
        try:result=batch.process_records(document['declarations'],out/'ink',run,implementation,reuse=reuse)
        finally:batch.WritingReader=previous
        atomic_json(out/'report.json',dict(**result,source_sha256=pins))
        print(json.dumps(dict(counts=result['counts'],inherited=sum(r.get('decoding')=='inherited-unchanged-content' for r in result['records']))))


if __name__=='__main__':main()
