"""Freeze additive semantics, example sources and visible records in one run."""
import argparse,json,html
from collections import Counter
from copy import deepcopy
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document
from scripts.semantic_boundaries import raw,composed,basis,MEANINGS
from scripts.check_semantic_boundaries import diagnose
from scripts.general_language import entries
from scripts.general_language_release import save_text
from scripts.two_work_assemble import renamed
from scripts.two_work_inventory import ROOT,read,sha
from scripts.concept2_document import full_name,references
from scripts.two_work_repair import RepairWritingReader
from scripts import concept2_composition as c,two_work_batch as batch
from scripts.long_run import LongRun,atomic_json,fingerprint


def prepare():
    catalog=deepcopy(read('data/general-language-catalog-v1.json'))
    definitions=raw();library='examples/v016/semantic-boundaries-v1.noema';contract='data/semantic-boundaries-basis-v1.json'
    save_text(library,format_graph(composed(),'compact')+'\n')
    save_text(contract,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')
    old=deepcopy(catalog['entries']);used={r['symbol'] for r in old.values()}
    roots=('home','above','give','inside','aki','nao','book','round','treeone','fruit','birdone','rain')
    serial=0
    def allocate(prefix):
        nonlocal serial
        while True:
            n=serial;serial+=1;parts=(*prefix,roots[(n//144)%12],roots[(n//12)%12],roots[n%12])
            symbol=full_name([c.old.root_symbol(x) for x in parts])
            if symbol not in used:used.add(symbol);return list(parts),symbol
    for d in definitions:
        parts,symbol=allocate(('book','rain','nao'))
        catalog['entries'][d['name']]=dict(name=d['name'],layer='extension',portability='shared-extension',declaration=d,spelling=parts,symbol=symbol,
            meaning=MEANINGS[d['name']],roles=[p['name'] for p in d['parameters']],context=basis()['limits'],contrast=[],sources=[library,contract],
            usage='意味の境界を明示する合成定義。前提、完全性、実在、記述と値、解の存在を区別する。')
    assert all(catalog['entries'][n]==r for n,r in old.items())
    for p in [library,contract,'scripts/semantic_boundaries.py']:catalog['source_sha256'][p]=sha(p)
    catalog['counts']=dict(entries=len(catalog['entries']),portability=dict(Counter(r['portability'] for r in catalog['entries'].values())),
                          kinds=dict(Counter(r['declaration']['kind'] for r in catalog['entries'].values())))
    save_text('data/general-language-catalog-v2.json',json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+'\n')
    _,examples=diagnose();declarations=composed()['declarations'];present={d['name']:d for d in declarations};statements=[];alignment=[]
    for index,(name,d,expected) in enumerate(examples):
        mapping={x['name']:'boundaryexample'+chr(97+index)+x['name'] for x in d['declarations'] if x['name'].startswith('fixture')}
        transformed=renamed(d,mapping)
        for item in transformed['declarations']:
            if item['name'] in present:
                if present[item['name']]!=item:raise ValueError('Meaning changed: '+item['name'])
            else:declarations.append(item);present[item['name']]=item
        alignment.append(dict(name=name,start=len(statements),count=len(transformed['statements']),expected=expected,
            interpretation='scripts/check_semantic_boundaries.py の同名の有限解釈。未知の内容を実行しない箇所も含む。'))
        statements.extend(transformed['statements'])
    source=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=statements))
    symbols={n:r['symbol'] for n,r in catalog['entries'].items()};locals_=[]
    for d in source['declarations']:
        if d['name'] not in symbols:
            parts,symbol=allocate(('book','rain','round'));symbols[d['name']]=symbol
            locals_.append(dict(name=d['name'],symbol=symbol,spelling=parts,role='有限解釈の入力。新しい共通基本概念には数えない。'))
    visible=normalize_document(renamed(source,symbols))
    return source,visible,dict(cases=alignment,local_inputs=locals_,names={d['name']:symbols[d['name']] for d in source['declarations']})


def publish(out,source,alignment,report):
    e=html.escape;catalog=read('data/general-language-catalog-v2.json')['entries'];records={r['native'].get('name'):r for r in report['records'] if r['status']=='passed'}
    rows=[]
    for d in raw():
        row=catalog[d['name']];r=records.get(row['symbol'])
        ink='<a href="ink/'+r['cache_key']+'.svg">復号確認済みの円文字</a>' if r else '復号未完'
        rows.append('<article id="'+d['name']+'"><h3>'+d['name']+'</h3><p>'+e(row['meaning'])+'</p><p>'+e(' → '.join(row['roles']))+'</p>'+ink+'</article>')
    cases=''.join('<li>'+e(r['name'])+'：'+str(r['count'])+'式、期待値 '+e(str(r['expected']))+'</li>' for r in alignment['cases'])
    page='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Noema 意味の境界と共通仕様</title><style>body{max-width:1000px;margin:auto;padding:24px;font:16px/1.8 system-ui;background:#f4f2ec;color:#24332e}a{color:#17685e}article{background:white;border:1px solid #ddd;padding:18px;margin:16px 0;overflow-wrap:anywhere}input{font:inherit;padding:10px;width:min(600px,90%)}article[hidden]{display:none}</style><h1>Noema 意味の境界と共通仕様</h1>'''
    page+='<p><a href="../../docs/semantic-boundaries-v1.md">補強した共通仕様</a> · <a href="../general-language-v1/index.html">これまでの辞書・36分野</a> · <a href="../../data/general-language-catalog-v2.json">統合カタログ</a></p>'
    page+='<p>既存1,909項目を保持し、43定義を追加。非実在・未定義・情報不足・相反する情報・名前のない束縛対象・意味の構成根拠・反復・自己言及を扱います。</p>'
    page+='<p><a href="source.noema">対照例のNoema文書</a> / <a href="examples.json">対応と解釈</a> / <a href="../../reports/semantic-boundaries-v3.json">意味診断</a> / <a href="report.json">実図形の検査</a></p><ul>'+cases+'</ul><h2>追加した共通定義</h2><input id="search" aria-label="追加語彙を検索" placeholder="語や意味を検索"><div id="dictionary">'+''.join(rows)+'</div>'
    page+='<script>document.querySelector("#search").addEventListener("input",e=>document.querySelectorAll("article").forEach(a=>a.hidden=!a.textContent.toLowerCase().includes(e.target.value.toLowerCase())))</script></html>'
    (out/'index.html').write_text(page,encoding='utf-8',newline='\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');args=p.parse_args()
    pins=read('data/writing-freeze-v2.json')['source_sha256'].copy()
    for path,h in pins.items():
        if sha(path)!=h:raise ValueError('Frozen input changed: '+path)
    implementation=fingerprint(dict(pins,batch=sha('scripts/two_work_batch.py')))
    for path in ['scripts/publish_semantic_boundaries.py','scripts/semantic_boundaries.py','scripts/check_semantic_boundaries.py',
                 'scripts/general_language.py','data/general-language-catalog-v1.json','scripts/two_work_batch.py','scripts/two_work_repair.py',
                 'reports/semantic-boundaries-v3.json']:pins[path]=sha(path)
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
    with LongRun(ROOT/args.run,dict(source_sha256=pins,output=args.out),resume=args.resume) as run:
        source,visible,alignment=run.step('prepare',pins,prepare)
        atomic_json(out/'source.json',source);atomic_json(out/'document.json',visible);atomic_json(out/'examples.json',alignment)
        (out/'source.noema').write_text(format_graph(source,'compact')+'\n',encoding='utf-8',newline='\n')
        previous=batch.WritingReader;batch.WritingReader=RepairWritingReader
        try:report=batch.process_records(visible['declarations']+visible['statements'],out/'ink',run,implementation,
            reuse=[ROOT/'output/general-language-catalog-ink-v1/ink'])
        finally:batch.WritingReader=previous
        atomic_json(out/'report.json',dict(**report,source_sha256=pins));publish(out,source,alignment,report)
        run.emit('progress',stage='Complete',completed=len(report['records']),total=len(report['records']))
        print(json.dumps(dict(counts=report['counts'],definitions=len(raw()),catalog=1952)))


if __name__=='__main__':main()
