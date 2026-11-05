"""Retire explicit local files in journaled, bounded steps; never recurse-delete."""
import argparse
import hashlib
import json
import stat
from collections import Counter
from pathlib import Path
from scripts.long_run import LongRun, atomic_json
from scripts.verify_language_edition import confined

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for raw in iter(lambda:stream.read(4*1024*1024),b''):h.update(raw)
    return h.hexdigest()


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--plan',required=True);cli.add_argument('--run',required=True)
    args=cli.parse_args();planpath=confined(ROOT,args.plan);plan=json.loads(planpath.read_text(encoding='utf-8'))
    keep=set(plan['kept_files']);protected=[confined(ROOT,p) for p in plan['protected_dirs']]
    directory=confined(ROOT,args.run)
    def safe(name,checked):
        relative=Path(name)
        if relative.is_absolute() or relative.drive or '..' in relative.parts:raise ValueError('Nonlocal cleanup path')
        p=ROOT/relative
        if p==ROOT or name in keep or any(p==x or p.is_relative_to(x) for x in protected):raise ValueError('Protected cleanup path: '+name)
        if name.startswith('.noema-project/ledger.sqlite') or p==directory or p.is_relative_to(directory):raise ValueError('Authoritative or active run path')
        if p.parent not in checked:
            if p.parent.resolve()!=p.parent:raise ValueError('Linked cleanup directory: '+name)
            checked.add(p.parent)
        return p
    chunks=[];chunk=[];size=0
    for row in plan['files']:
        if chunk and (len(chunk)>=256 or size+row['bytes']>256*1024*1024):chunks.append(chunk);chunk=[];size=0
        chunk.append(row['path']);size+=row['bytes']
    if chunk:chunks.append(chunk)
    if len({r['path'] for r in plan['files']})!=len(plan['files']):raise ValueError('Duplicate cleanup path')
    manifest=dict(plan_sha256=sha(planpath),implementation_sha256=sha(Path(__file__)),root=str(ROOT))
    removed=Counter();bytes_removed=0;failures=[];parents=set();completed=0
    with LongRun(directory,manifest,resume=directory.exists()) as run:
        journals=directory/'candidates';journals.mkdir(exist_ok=True)
        for i,names in enumerate(chunks):
            run.emit('progress',stage='Pin and remove retired files',completed=completed,total=len(plan['files']))
            def action(names=names,i=i):
                journal=journals/(str(i)+'.json');prior=json.loads(journal.read_text(encoding='utf-8')) if journal.exists() else None
                rows={};states={};checked=set();errors=[]
                for name in names:
                    p=safe(name,checked)
                    try:s=p.lstat()
                    except FileNotFoundError:
                        if prior is None:raise
                        rows[name]=prior[name];continue
                    if getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ValueError('Linked candidate: '+name)
                    h=sha(p)
                    if prior is not None and h!=prior[name]['sha256']:raise ValueError('Candidate changed during interrupted step: '+name)
                    rows[name]=dict(sha256=h,bytes=s.st_size);states[name]=(s.st_size,s.st_mtime_ns,s.st_ino)
                if prior is None:atomic_json(journal,rows)
                checked=set()
                for name in names:
                    p=safe(name,checked)
                    try:s=p.lstat()
                    except FileNotFoundError:continue
                    if getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ValueError('Candidate replaced with link')
                    # The full hash was freshly read in this small step. A change
                    # in the interval requires another content check, not a cache hit.
                    if states.get(name)!=(s.st_size,s.st_mtime_ns,s.st_ino) and sha(p)!=rows[name]['sha256']:raise ValueError('Candidate changed before deletion')
                    try:
                        try:p.unlink()
                        except PermissionError:
                            p.chmod(s.st_mode|stat.S_IWRITE);p.unlink()
                    except OSError as error:errors.append(dict(path=name,error=str(error)))
                failed={r['path'] for r in errors}
                return dict(failures=errors,bytes=sum(r['bytes'] for n,r in rows.items() if n not in failed))
            def validate(result,names=names):
                failed={r['path'] for r in result['failures']};checked=set()
                for name in names:
                    if name not in failed and safe(name,checked).exists():raise ValueError('Retired file reappeared: '+name)
            result=run.step('delete-'+str(i),names,action,validate=validate)
            failures.extend(result['failures']);bytes_removed+=result['bytes'];failed={r['path'] for r in result['failures']}
            for name in names:
                if name not in failed:removed[name.split('/')[0]]+=1
                parents.update(p for p in (ROOT/name).parents if p!=ROOT and p.is_relative_to(ROOT))
            completed+=len(names)
        for p in sorted(parents,key=lambda p:len(p.parts),reverse=True):
            if any(p==x or p.is_relative_to(x) for x in protected) or p==directory or p.is_relative_to(directory):continue
            if p.resolve()!=p:continue
            try:p.rmdir()
            except OSError:pass
        report=dict(schema='noema-retirement-1',release='1.0',plan_sha256=manifest['plan_sha256'],
            candidates=len(plan['files']),removed_files=sum(removed.values()),removed_bytes=bytes_removed,
            by_top=dict(removed),failures=failures,protected_edition_files=40294,
            preserved_dirty=plan['protected_dirty'],preserved_untracked=plan['protected_untracked'],
            semantics_changed=False,method='Retire files outside the fixed edition and retained code/document dependencies; preserve completed edition and ledger')
        atomic_json(ROOT/'reports/cleanup-v1.json',report)
        run.emit('progress',stage='Retirement complete',completed=completed,total=completed,failures=len(failures))
        print(json.dumps({k:v for k,v in report.items() if k not in ('preserved_dirty','preserved_untracked')},ensure_ascii=False))


if __name__=='__main__':main()
