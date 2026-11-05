"""Carry forward a completed semantic audit by checking its actual source bytes."""
import argparse
import hashlib
import json
from pathlib import Path
from scripts.project_notes import Ledger,DEFAULT_DB
from scripts.long_run import LongRun,atomic_json

ROOT=Path(__file__).resolve().parents[1]
REPORT='reports/written-progress-v433.json'
LOG='.noema-project/eighth-pin-snapshot-full-audit-v1-process.log'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    baseline=json.loads((ROOT/REPORT).read_text(encoding='utf-8'))
    audit=json.loads((ROOT/LOG).read_text(encoding='utf-8'))
    if audit.get('verified')!=REPORT or audit.get('full') is not True:raise ValueError('Saved completed full audit is required')
    pins=sorted(baseline['source_sha256'].items());db=Ledger(DEFAULT_DB)
    manifest=dict(schema='concept2-semantic-carry-1',report_sha256=sha((ROOT/REPORT).read_bytes()),
        completed_audit_sha256=sha((ROOT/LOG).read_bytes()),implementation_sha256=sha(Path(__file__).read_bytes()))
    def verify(chunk):
        count=archived=0;total=0
        for name,expected in chunk:
            path=ROOT/name
            if path.is_file():raw=path.read_bytes()
            else:raw=db.document(name)['raw'];archived+=1
            if sha(raw)!=expected:raise ValueError('Semantic evidence input changed: '+name)
            count+=1;total+=len(raw)
        return dict(files=count,archived=archived,bytes=total)
    results=[]
    try:
        with LongRun(ROOT/args.run,manifest,resume=args.resume) as run:
            for i in range(0,len(pins),128):
                chunk=pins[i:i+128]
                run.emit('progress',stage=f'Semantic source bytes {i}/{len(pins)}',completed=i,total=len(pins))
                # A reused step still rehashes its current files; no mtime trust.
                checked=[]
                def action():checked.append(verify(chunk));return checked[0]
                def validate(value):
                    current=checked[0] if checked else verify(chunk)
                    if current!=value:raise ValueError('Semantic source bytes differ on resume')
                results.append(run.step(str(i),chunk,action,validate=validate))
            run.emit('progress',stage='Saved semantic audit inputs unchanged',completed=len(pins),total=len(pins))
            result=dict(schema='concept2-semantic-carry-1',method='Content hashes of the saved completed full-audit inputs; no new semantic judgments',
                baseline=REPORT,audit=LOG,source_sha256=manifest,unchanged_files=sum(r['files'] for r in results),
                archived_files=sum(r['archived'] for r in results),hashed_bytes=sum(r['bytes'] for r in results),
                reviewed_units=audit['reviewed_units'],all_match=True)
            atomic_json(ROOT/'output/concept2-semantic-carry-v1.json',result)
            print(json.dumps({k:result[k] for k in ('all_match','unchanged_files','archived_files','hashed_bytes','reviewed_units')}))
    finally:db.close()


if __name__=='__main__':main()
