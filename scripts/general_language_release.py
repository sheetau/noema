"""Prepare the reusable catalog, native additions and cross-domain review packet."""
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from noema.constructed import format_graph
from scripts.two_work_inventory import ROOT, read, sha
from scripts.long_run import atomic_json
from scripts.concept2_document import full_name, references
from scripts import concept2_composition as c
from scripts import general_probability as probability, general_pragmatics as pragmatics

CATALOG='data/general-language-catalog-v1.json'
SELECTORS = '''caseprioractorgroup casepriorparticipants caseincitingparticipants casepriorinfluenceact
casepriorinfluencepoint caseincitingpresentation caseincitementpoint caseprospectivepressureact
caseaffectedparticipants casehistorydescription caseprecedencedescription casepressurestartdescription
caseretentionenddescription caseretentionassessment casepressureactdescription caseoriginlinkedtargets
caseadoptionoriginator caseadoptionproductionact caseadoptionrecipient caseopinionreferent caseopiniondescription
caseadoptionpriorpoint caseadoptionpriordescription casetargetoutcomepoint casetargetsuccessionrole
casetargetcoursedescription casetargetprecedencedescription'''.split()


def save_text(path, text):
    path=ROOT/path
    if path.exists() and path.read_text(encoding='utf-8') != text:
        raise ValueError('Published content differs; select a new version: '+str(path))
    if not path.exists(): path.write_text(text,encoding='utf-8',newline='\n')


def prepare():
    original=read('output/general-language-inventory-v2/inventory.json')
    for path, digest in original['source_sha256'].items():
        if sha(path)!=digest: raise ValueError('Inventory input changed: '+path)
    entries=deepcopy(original['entries']); used={tuple(r['spelling']) for r in entries.values()}
    for n,r in entries.items():
        r['portability']='source-selector' if n in SELECTORS else 'shared-core' if r['layer']=='core' else 'domain-contract'
        r['usage']='作品内の固定対象の選択。共通語数には含めず、別文書では参照先を明示して置換する。' if n in SELECTORS else (
            '型・引数役割・語義・文脈条件を保って再利用する。基本宣言は定義済み概念とは数えない。')
    modules=[('probability',probability),('pragmatics',pragmatics)]
    roots=('home','above','give','inside','aki','nao','book','round','treeone','fruit','birdone','rain')
    serial=0
    for family,module in modules:
        library='examples/v016/general-'+family+'-v1.noema'; basis='data/general-'+family+'-basis-v1.json'
        save_text(library,format_graph(module.composed(),'compact')+'\n')
        save_text(basis,json.dumps(module.basis(),ensure_ascii=False,indent=2)+'\n')
        for d in module.raw():
            while True:
                parts=('book','rain','above',roots[serial//12],roots[serial%12]); serial+=1
                if parts not in used:break
            used.add(parts)
            entries[d['name']]=dict(name=d['name'],layer='extension',portability='shared-extension',
                declaration=d,spelling=list(parts),symbol=full_name([c.old.root_symbol(p) for p in parts]),
                meaning=module.MEANINGS[d['name']],roles=[p['name'] for p in d['parameters']],
                context=module.basis().get('limits',module.basis().get('interpretation',[])),contrast=[],sources=[library,basis],
                usage='既存の型・構文から合成した定義。関係入力の意味規約と未知入力の拒否を保持する。')
    assert set(SELECTORS)<=set(entries)
    for n,r in entries.items():
        if references(r['declaration'])-set(entries):raise ValueError('Missing dependency '+n)
    pins={**original['source_sha256']}
    for family,module in modules:
        for path in ('scripts/general_'+family+'.py','examples/v016/general-'+family+'-v1.noema','data/general-'+family+'-basis-v1.json'):pins[path]=sha(path)
    result=dict(schema='noema-general-catalog-1',entries=entries,source_sha256=pins,issues=[],spelling_collisions=[],
        counts=dict(entries=len(entries),portability=dict(Counter(r['portability'] for r in entries.values())),
                    kinds=dict(Counter(r['declaration']['kind'] for r in entries.values()))),
        boundary='作品内の参照補助を汎用語数から除外。domain-contractは分野・型・文脈を保つ再利用であり、全項目の別分野での意味確認ではない。')
    save_text(CATALOG,json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps(result['counts'],ensure_ascii=False))


if __name__=='__main__':prepare()
