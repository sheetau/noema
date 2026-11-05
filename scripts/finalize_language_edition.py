"""Seal selected evidence and copy an independently readable edition in small steps.

No source meaning or geometry is regenerated. A changed pinned input fails closed.
"""
import hashlib
import json
import os
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from scripts.long_run import LongRun, atomic_json
from scripts.project_notes import Ledger, DEFAULT_DB
from scripts.verify_language_edition import confined, digest, verify, LOCK, REPORT

ROOT = Path(__file__).resolve().parents[1]
SELECT = 'data/language-release-v1.json'
RUN = '.noema-project/runs/language-edition-1.0-v3'
OUT = 'output/noema-1.0'
FOLDERS = ('output/two-work-final-v2', 'output/general-language-v1',
           'output/general-language-catalog-ink-v1', 'output/semantic-boundaries-v1',
           'output/noema-writing-v2', 'output/concept2-dictionary-v3')
EXTRA = ('README.md','docs/STATUS.md','docs/language-edition-v1.md',
         'docs/language-completion.md','docs/semantic-review-v1.md',
         'docs/general-language-v1.md','docs/semantic-boundaries-v1.md',
         'docs/spec-v014.md','docs/ranked-quotation-v1.md','docs/quotation-construction-v1.md',
         'data/general-language-release-v2.json','data/general-language-release-v1.json',
         'data/work-state.json','scripts/finalize_language_edition.py',
         'scripts/verify_language_edition.py','tests/test_language_edition.py','pyproject.toml',
         '.noema-project/eighth-pin-snapshot-full-audit-v1-process.log')


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def selection_only(old, new):
    """Only general-language pointers may differ, never the reviewed manuscripts."""
    old = json.loads(json.dumps(old)); new = json.loads(json.dumps(new))
    for value in (old,new):
        for key in ('general_language','general_language_audit'):
            value.get('verification',{}).pop(key,None)
    return old == new


def old_selection(expected, *, diagnostic_carry=False):
    commits = subprocess.check_output(['git','log','-n','20','--format=%H','--','data/work-state.json'],cwd=ROOT,text=True).split()
    for commit in commits:
        raw = subprocess.check_output(['git','show',commit+':data/work-state.json'],cwd=ROOT)
        if digest(raw) == expected:
            if not diagnostic_carry and not selection_only(json.loads(raw),read('data/work-state.json')):
                raise ValueError('Old evidence differs beyond general-language selection')
            return raw
    raise ValueError('Original selection bytes unavailable: '+expected)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.targets=[]
    def handle_starttag(self,tag,attrs):
        if tag not in ('a','img','script','link','iframe'):return
        for key,value in attrs:
            if key in ('href','src') and value:self.targets.append(value)


def entry():
    links = [('二作品の本文・原文対応・数式','output/two-work-final-v2/index.html'),
             ('共通辞書 1,909項目','output/general-language-v1/index.html'),
             ('追加43定義と意味の対照例','output/semantic-boundaries-v1/index.html'),
             ('統合辞書 1,952項目','data/general-language-catalog-v2.json'),
             ('採用した円文字と字形表','output/noema-writing-v2/index.html'),
             ('完成範囲と仕様の案内','docs/language-edition-v1.md'),
             ('版の選択記録',SELECT),('完成照合',REPORT),('内容ハッシュ一覧',LOCK)]
    return ('<!doctype html><html lang="ja"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Noema 1.0</title><style>body{font:18px/1.8 system-ui,sans-serif;max-width:850px;margin:6vh auto;padding:0 24px;color:#202b30;background:#fafaf7}a{color:#175963}li{margin:.7em 0}small{color:#526063}</style>'
            '<h1>Noema 1.0</h1><p>円と線で記す言語。意味の構成規則、辞書、二作品、検証証拠をまとめた完成版です。</p>'
            '<p><small>2026年11月5日確定 · カント20単位／アインシュタイン282単位 · 固定円文字501字形</small></p><ul>'
            + ''.join('<li><a href="'+url+'">'+label+'</a></li>' for label,url in links)
            + '</ul><p>意味判断は明示した解釈の下で保持しています。人が読んで受ける効果、全自然文の網羅証明、自動翻訳器は完成範囲に含めません。</p></html>\n').encode('utf-8')


def prepare():
    roots = [SELECT,*EXTRA,*read(SELECT)['evidence']]
    rootpins = {p:digest((ROOT/p).read_bytes()) for p in roots}
    with LongRun(ROOT/RUN,dict(source_sha256=rootpins,folders=list(FOLDERS)),resume=(ROOT/RUN).exists()) as run:
        ledger = Ledger(DEFAULT_DB)
        try:
            expected = {}; generated = {'index.html':entry(),
                OUT+'/index.html':b'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../../index.html"><a href="../../index.html">Noema 1.0</a>\n'}; carries=[]
            def add(name,h):
                confined(ROOT,name)
                if name in expected and expected[name]!=h:raise ValueError('Conflicting evidence: '+name)
                expected[name]=h
            def source(name):
                if name in generated:return generated[name]
                path=confined(ROOT,name)
                return path.read_bytes() if path.is_file() else bytes(ledger.document(name)['raw'])
            reports = list(read(SELECT)['evidence'])
            prior_carries={r['report']:r for r in read('reports/general-language-completion-v1.json')['evidence']}
            reports += list(prior_carries)
            reports += ['reports/written-progress-v433.json','output/two-work-final-v2/report.json',
                        'output/general-language-v1/report.json','output/general-language-catalog-ink-v1/report.json',
                        'output/semantic-boundaries-v1/report.json']
            for p in sorted(set(reports)):
                data=read(p);add(p,digest((ROOT/p).read_bytes()))
                for name,h in data.get('source_sha256',{}).items():
                    if name=='data/work-state.json' and digest(source(name))!=h:
                        prior=prior_carries.get(p)
                        diagnostic=bool(prior and prior['changed_inputs']==['data/work-state.json']
                                        and prior['sha256']==digest((ROOT/p).read_bytes())
                                        and prior['carry']=='fixed-input diagnostics only; active-manuscript selection is not carried')
                        old=old_selection(h,diagnostic_carry=diagnostic);saved='evidence/selection-history/'+h+'.json'
                        generated[saved]=old;add(saved,h)
                        carries.append(dict(report=p,original_path=name,original_sha256=h,saved_as=saved,
                                            scope='Prior audited fixed-input diagnostics only; historical active selection is not carried' if diagnostic
                                            else 'Fixed meaning inputs retained; only general-language selection changed'))
                    else:add(name,h)
            for p,h in rootpins.items():add(p,h)
            for criterion in read(SELECT)['completion_criteria']:
                for p in criterion['evidence']:add(p,digest(source(p)))
            for folder in FOLDERS:
                for path in (ROOT/folder).rglob('*'):
                    if path.is_file():expected.setdefault(path.relative_to(ROOT).as_posix(),None)
            for path in (ROOT/'noema').rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts:expected.setdefault(path.relative_to(ROOT).as_posix(),None)
            # Keep local dependencies of the selected HTML readers, without fetching websites.
            queue=[p for p in expected if p.startswith('output/') and p.endswith('.html')];seen=set()
            while queue:
                p=queue.pop()
                if p in seen:continue
                seen.add(p);parser=Links();parser.feed(source(p).decode('utf-8'))
                for href in parser.targets:
                    url=urlsplit(href)
                    if url.scheme or url.netloc or not url.path:continue
                    target=confined(ROOT,str(Path(p).parent/unquote(url.path)))
                    name=target.relative_to(ROOT).as_posix()
                    if not target.is_file():raise ValueError('Missing reader dependency: '+name)
                    expected.setdefault(name,None)
                    if name.startswith('output/') and name.endswith('.html'):queue.append(name)
            for p,raw in generated.items():add(p,digest(raw))
            inventory={}; archived=[]; names=sorted(expected)
            for i in range(0,len(names),128):
                chunk=names[i:i+128];run.emit('progress',stage='Pin evidence and artifacts',completed=i,total=len(names))
                current={}
                for p in chunk:
                    h=digest(source(p))
                    if expected[p] is not None and expected[p]!=h:raise ValueError('Pinned content changed: '+p)
                    current[p]=h
                    if p not in generated and not (ROOT/p).is_file():archived.append(p)
                def validate(old,current=current):
                    if old!=current:raise ValueError('Input changed since checkpoint')
                inventory.update(run.step('inventory-'+str(i),chunk,lambda current=current:current,validate=validate))
            # Preserve exact successful geometry records, including every SVG byte.
            geometry=[]
            for folder in (*[FOLDERS[0]+'/'+w+'/ink' for w in ('kant','einstein')],
                           FOLDERS[1],FOLDERS[2],FOLDERS[3]):
                report=read(folder+'/report.json')
                if not report['scan_complete'] or not report['validation_success']:raise ValueError('Incomplete geometry evidence')
                records=report['records']
                if report['counts']!={'passed':len(records)}:raise ValueError('Failed geometry record')
                for row in records:
                    p=folder+('/' if folder.endswith('/ink') else '/ink/')+row['cache_key']+'.svg'
                    if inventory[p]!=row['svg_sha256']:raise ValueError('Changed decoded geometry: '+p)
                geometry.append(dict(report=folder+'/report.json',records=len(records),unchanged=True))
            baseline=read('reports/written-progress-v433.json');audit=read('.noema-project/eighth-pin-snapshot-full-audit-v1-process.log')
            if audit.get('full') is not True or audit.get('verified')!='reports/written-progress-v433.json':raise ValueError('Full baseline unavailable')
            if len(baseline['source_sha256'])!=8510:raise ValueError('Unexpected semantic baseline')
            if not read('reports/two-work-final-publication-v1.json')['complete']:raise ValueError('Incomplete works')
            if len(read('data/general-language-catalog-v2.json')['entries'])!=1952:raise ValueError('Incomplete catalog')
            if read(SELECT)['unresolved_completion_items']:raise ValueError('Unresolved completion items')
            lock=dict(schema='noema-edition-artifact-lock-1',edition='1.0',files=inventory,
                      archived_originals=archived,selection_history=carries)
            lockpath=ROOT/LOCK
            if lockpath.exists() and read(LOCK)!=lock:raise ValueError('Existing seal differs; create a new edition')
            if not lockpath.exists():atomic_json(lockpath,lock)
            out=ROOT/OUT;out.mkdir(parents=True,exist_ok=True)
            total_bytes=0
            for i in range(0,len(names),64):
                chunk=names[i:i+64];run.emit('progress',stage='Save immutable edition',completed=i,total=len(names))
                hashes={p:inventory[p] for p in chunk}
                def validate_copy(result,hashes=hashes):
                    for p,h in hashes.items():
                        if digest(confined(out,p).read_bytes())!=h:raise ValueError('Snapshot copy changed: '+p)
                def copy(chunk=chunk,hashes=hashes):
                    count=0
                    for p in chunk:
                        raw=source(p)
                        if digest(raw)!=hashes[p]:raise ValueError('Input changed while saving: '+p)
                        target=confined(out,p);target.parent.mkdir(parents=True,exist_ok=True)
                        if target.exists():
                            if digest(target.read_bytes())!=hashes[p]:raise ValueError('Existing snapshot differs: '+p)
                        else:
                            tmp=target.with_name(target.name+'.release-tmp');tmp.write_bytes(raw);os.replace(tmp,target)
                        count+=len(raw)
                    return dict(files=len(chunk),bytes=count)
                total_bytes+=run.step('copy-'+str(i),hashes,copy,validate=validate_copy)['bytes']
            report=dict(schema='noema-language-completion-1',edition='1.0',status='complete_under_stated_scope',
                        selection=SELECT,artifact_lock=LOCK,artifact_lock_sha256=digest(lockpath.read_bytes()),
                        source_sha256=dict(rootpins,**{LOCK:digest(lockpath.read_bytes())}),
                        files=len(inventory),bytes=total_bytes,archived_originals=len(archived),
                        semantic_input_files=8510,source_units=302,source_assertions=402,catalog_entries=1952,
                        visible_evidence=geometry,selection_history=carries,
                        completion_criteria=[dict(id=c['id'],decision='satisfied_under_stated_scope',evidence=c['evidence']) for c in read(SELECT)['completion_criteria']],
                        unresolved_completion_items=[],new_semantic_judgments=0,geometry_reexecuted=False,
                        method='Exact content carry and snapshot verification; retain source judgments, syntax correspondence and actual geometry evidence separately')
            if (ROOT/REPORT).exists() and read(REPORT)!=report:raise ValueError('Existing completion report differs')
            if not (ROOT/REPORT).exists():atomic_json(ROOT/REPORT,report)
            for p in (LOCK,REPORT):
                target=confined(out,p);target.parent.mkdir(parents=True,exist_ok=True)
                raw=(ROOT/p).read_bytes()
                if target.exists() and target.read_bytes()!=raw:raise ValueError('Snapshot seal differs')
                target.write_bytes(raw)
            parser=Links();parser.feed((out/'index.html').read_text(encoding='utf-8'))
            for href in parser.targets:
                if not confined(out,href).is_file():raise ValueError('Missing final entry link: '+href)
            # Verify the actual detached copy, not the source worktree.
            result=verify(out,lambda done,total:run.emit('progress',stage='Verify saved edition',completed=done,total=total))
            atomic_json(ROOT/RUN/'result.json',report)
            run.emit('progress',stage='Edition sealed',completed=len(names),total=len(names),verification=result)
        finally:ledger.close()


def build_report():
    return read(RUN+'/result.json')


if __name__=='__main__':
    prepare()
    print(json.dumps({k:v for k,v in build_report().items() if k not in ('completion_criteria','selection_history')},ensure_ascii=False))
