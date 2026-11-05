"""Both complete works in one durable run, continuing past individual failures.

Resume is for interrupted identical inputs. Repairs use a new run and --reuse
pointing at a previous output; only matching successful ink artifacts carry on.
"""
import argparse,json,traceback
from pathlib import Path
from scripts.two_work_inventory import ROOT,read,sha
from scripts.two_work_batch import process_records
from scripts.two_work_publish import publish_work,publish_index
from scripts.long_run import LongRun,PauseRequested,atomic_json,fingerprint
from scripts.project_notes import Ledger,DEFAULT_DB

BASE='output/two-work-edition-v1/'


def checked_pins():
    pins={}
    for report in (BASE+'report.json',BASE+'catalog-report.json','data/writing-freeze-v2.json'):
        pins.update(read(report)['source_sha256']);pins[report]=sha(report)
    for work in ('kant','einstein'):
        for suffix in ('.json','-toc.json','-catalog.json'):pins[BASE+work+suffix]=sha(BASE+work+suffix)
    for name in ('two_work_run','two_work_batch','two_work_publish','long_run'):
        p='scripts/'+name+'.py';pins[p]=sha(p)
    log='.noema-project/eighth-pin-snapshot-full-audit-v1-process.log';pins[log]=sha(log)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Pinned preparation input changed: '+p)
    return pins


def semantic_inputs(run):
    baseline=read('reports/written-progress-v433.json')
    audit=read('.noema-project/eighth-pin-snapshot-full-audit-v1-process.log')
    if audit.get('verified')!='reports/written-progress-v433.json' or audit.get('full') is not True:
        raise ValueError('Completed baseline audit is missing')
    pins=sorted(baseline['source_sha256'].items());db=Ledger(DEFAULT_DB);results=[]
    def check(chunk):
        import hashlib
        failures=[]
        for p,h in chunk:
            try:
                raw=(ROOT/p).read_bytes() if (ROOT/p).is_file() else db.document(p)['raw']
                if hashlib.sha256(raw).hexdigest()!=h:failures.append(dict(path=p,error='content changed'))
            except Exception as error:failures.append(dict(path=p,error=str(error)))
        return dict(files=len(chunk),issues=failures)
    try:
        for i in range(0,len(pins),128):
            chunk=pins[i:i+128];run.emit('progress',stage='Existing semantic evidence',completed=i,total=len(pins))
            current=check(chunk)
            results.append(run.step('semantic-'+str(i),chunk,lambda:current,
                validate=lambda old: None if old==current else (_ for _ in ()).throw(ValueError('Semantic evidence changed on resume'))))
    finally:db.close()
    issues=[r for result in results for r in result['issues']]
    return dict(baseline='reports/written-progress-v433.json',checked_files=len(pins),issues=issues,
                unchanged=not issues,reviewed_units=audit['reviewed_units'],new_semantic_judgments=0)


def run_work(work,out,directory,pins,implementation,*,resume=False,reuse=()):
    document=read(BASE+work+'.json');toc=read(BASE+work+'-toc.json');catalog=read(BASE+work+'-catalog.json')
    bridge=read('output/two-work-assembly-v2/'+work+'-bridge.json');records=document['declarations']+document['statements']
    manifest=dict(work=work,source_sha256=pins,output=str(out),reuse=[str(p) for p in reuse])
    with LongRun(directory,manifest,resume=resume and (directory/'manifest.json').is_file()) as run:
        result=process_records(records,out/'ink',run,implementation,reuse=reuse)
        run.emit('progress',stage='Publish reading edition',completed=len(records),total=len(records))
        publication=publish_work(out,work,document,toc,catalog,bridge,result)
    return dict(stage='完了' if result['validation_success'] else '走査完了・要修正',scan_complete=True,
        validation_success=result['validation_success'],counts=result['counts'],publication=publication,
        issues=[{k:v for k,v in r.items() if k!='traceback'} for r in result['records'] if r['status']!='passed'])


def run_both(callback,report,update):
    for work in ('kant','einstein'):
        report['works'][work]=dict(stage='図形復号中');update()
        try:report['works'][work]=callback(work)
        except (PauseRequested,KeyboardInterrupt):raise
        except Exception as error:
            report['works'][work]=dict(stage='実行エラー・次作品へ継続',scan_complete=False,validation_success=False,
                error=str(error),traceback=traceback.format_exc())
        update()


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True)
    p.add_argument('--reuse',action='append',default=[]);p.add_argument('--resume',action='store_true');args=p.parse_args()
    out=ROOT/args.out;directory=ROOT/args.run
    if out.exists() and not args.resume:raise ValueError('Use a new output directory for a new run')
    pins=checked_pins();out.mkdir(parents=True,exist_ok=True)
    freeze=read('data/writing-freeze-v2.json')
    implementation=fingerprint(dict(freeze['source_sha256'],batch=sha('scripts/two_work_batch.py')))
    report=dict(schema='noema-two-work-integration-1',source_sha256=pins,works={},complete=False)
    def update():
        atomic_json(out/'report.json',report);atomic_json(out/'status.json',{k:v for k,v in report.items() if k!='source_sha256'})
        publish_index(out,report)
    with LongRun(directory,dict(source_sha256=pins,output=args.out,reuse=args.reuse),resume=args.resume) as run:
        report['semantic_carry']=semantic_inputs(run);update()
        # Build complete navigation now; missing ink is explicitly pending.
        for work in ('kant','einstein'):
            publish_work(out/work,work,read(BASE+work+'.json'),read(BASE+work+'-toc.json'),read(BASE+work+'-catalog.json'),
                read('output/two-work-assembly-v2/'+work+'-bridge.json'),{})
        def execute(work):
            run.emit('progress',stage=work+' — see child status.json',completed=0 if work=='kant' else 1,total=2)
            reuse=[ROOT/path/work/'ink' for path in args.reuse]
            if work=='einstein':reuse.append(out/'kant/ink')
            return run_work(work,out/work,directory/work,pins,implementation,resume=args.resume,reuse=reuse)
        run_both(execute,report,update)
        changed=[]
        for path,h in pins.items():
            try:
                if sha(path)!=h:changed.append(path)
            except OSError:changed.append(path)
        report['changed_inputs']=changed
        report['scan_complete']=all(r.get('scan_complete') for r in report['works'].values())
        report['complete']=bool(report['semantic_carry']['unchanged'] and not changed and all(r.get('validation_success') for r in report['works'].values()))
        update();run.emit('progress',stage='Both works scanned',completed=2,total=2,integration_complete=report['complete'])
        print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','works')},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
