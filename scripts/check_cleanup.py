"""Post-retirement proof carry, dependency/link checks and saved-edition hashes."""
import json
from pathlib import Path
from scripts.long_run import LongRun,atomic_json
from scripts.two_work_run import semantic_inputs
from scripts.clean_retired_files import sha
from scripts.verify_language_edition import confined

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'.noema-project/runs/cleanup-verification-v2'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


def prepare():
    paths=['scripts/check_cleanup.py','scripts/clean_retired_files.py','scripts/verify_language_edition.py',
           'tests/test_retirement.py','tests/test_language_edition.py','reports/cleanup-v1.json',
           'data/language-release-lock-v1.json','.noema-project/cleanup-plan-v1.json',
           '.noema-project/cleanup-links-before-v1.json']
    pins={p:sha(ROOT/p) for p in paths}
    with LongRun(RUN,dict(source_sha256=pins),resume=RUN.exists()) as run:
        report=read('reports/cleanup-v1.json')
        if report['failures']:raise ValueError('Retirement has unresolved failures')
        semantic=semantic_inputs(run)
        if not semantic['unchanged']:raise ValueError('Semantic evidence changed')
        plan=read('.noema-project/cleanup-plan-v1.json')
        missing=[e for e in plan['import_edges'] if not (ROOT/e[1]).is_file()]
        if missing:raise ValueError('Retained code dependency missing: '+str(missing[:5]))
        links=read('.noema-project/cleanup-links-before-v1.json')
        retired=report.get('retired_document_links',[])
        lock=read('data/language-release-lock-v1.json')
        if any(a in lock['files'] or b in lock['files'] for a,b in retired):raise ValueError('Cannot retire completed-edition links')
        missing=[p for p in links if not (ROOT/p[1]).is_file() and p not in retired]
        if missing:raise ValueError('New documentation link break: '+str(missing[:5]))
        for p in plan['protected_dirty']+plan['protected_untracked']:
            if not (ROOT/p).is_file():raise ValueError('Unrelated work removed: '+p)
        lock=read('data/language-release-lock-v1.json');items=list(lock['files'].items());saved=ROOT/'output/noema-1.0'
        for i in range(0,len(items),256):
            chunk=items[i:i+256];run.emit('progress',stage='Verify completed edition after cleanup',completed=i,total=len(items))
            def check(old,chunk=chunk):
                for p,h in chunk:
                    if sha(confined(saved,p))!=h:raise ValueError('Saved edition changed: '+p)
            run.step('edition-'+str(i),chunk,lambda chunk=chunk:dict(files=len(chunk)),validate=check)
        result=dict(schema='noema-cleanup-verification-1',passed=True,semantic_carry=semantic,
                    saved_edition_files=len(items),retained_import_edges=len(plan['import_edges']),
                    retained_documentation_links=len(links)-len(retired),retired_prototype_links=len(retired),new_broken_links=[],
                    unrelated_work_preserved=True,source_sha256=pins)
        atomic_json(RUN/'result.json',result)
        run.emit('progress',stage='Cleanup verified',completed=len(items),total=len(items))


def build_report():return read(RUN.relative_to(ROOT).as_posix()+'/result.json')
