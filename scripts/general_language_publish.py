"""Offline public dictionary and expression map, linking exact visible evidence."""
import html, json, os
from collections import Counter
from noema.constructed_discourse import normalize_document
from scripts.general_language import entries, dependencies
from scripts.general_language_cases import cases
from scripts.two_work_assemble import renamed
from scripts.two_work_inventory import ROOT, read, sha
from scripts.concept2_document import references
from scripts.long_run import atomic_json

OUT=ROOT/'output/general-language-v1'
E=html.escape


def link(path,label):
    target=os.path.relpath(ROOT/path,OUT).replace('\\','/')
    return '<a href="'+E(target,quote=True)+'">'+E(label)+'</a>'


def main():
    catalog=entries();mapping={n:r['symbol'] for n,r in catalog.items()}
    ds=dependencies(catalog)
    canonical=normalize_document(renamed(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[]),mapping))
    records={d['name']:d for d in canonical['declarations']};visible={};inputs={}
    for folder in ['output/two-work-final-v2/kant','output/two-work-final-v2/einstein','output/general-language-v1','output/general-language-catalog-ink-v1']:
        path=folder+'/ink/report.json'
        if not (ROOT/path).is_file():continue
        inputs[path]=sha(path)
        for row in read(path)['records']:
            native=row.get('native',{});name=native.get('name')
            if row['status']=='passed' and name in records and native==records[name]:
                svg=folder+'/ink/'+row['cache_key']+'.svg'
                if sha(svg)!=row['svg_sha256']:raise ValueError('Ink changed: '+svg)
                visible[name]=svg
    labels={'shared-core':'共通語','shared-extension':'共通追加','domain-contract':'分野別の意味規約','source-selector':'作品内参照'}
    sections=[]
    for name,row in catalog.items():
        d=row['declaration'];ps=d['parameters'];types=[p['sort'] if isinstance(p,dict) and 'name' in p else p for p in ps]
        roles=' → '.join(f'{i+1}. {role}' for i,role in enumerate(row['roles'])) or '引数なし'
        source=' / '.join(link(p,p) for p in row['sources'])
        deps=' '.join('<a href="#'+E(n)+'">'+E(n)+'</a>' for n in sorted(references(d))) or '依存語なし'
        ink=link(visible[row['symbol']],'実図形と構文の一致を確認済み') if row['symbol'] in visible else '既存の語形登録を参照（このカタログ内の宣言との図形一致は未収録）'
        content='<h3>'+E(name)+'</h3><p>'+E(str(row['meaning']))+'</p><p>'+E(roles)+'</p>'
        content+='<p>'+E(row['usage'])+'</p><p>'+ink+'</p><p>依存語：'+deps+'</p><p>'+source+'</p>'
        content+='<details><summary>型・固定綴り・構文</summary><pre>'+E(json.dumps(dict(parameters=types,result=d['result'],spelling=row['spelling'],symbol=row['symbol'],declaration=d),ensure_ascii=False,indent=2))+'</pre></details>'
        if row.get('context'):content+='<p>'+E(str(row['context']))+'</p>'
        sections.append('<article id="'+E(name)+'" data-layer="'+row['portability']+'"><small>'+labels[row['portability']]+' · '+d['kind']+'</small>'+content+'</article>')
    review={r['id']:r for r in read('reports/general-language-review-v2.json')['cases']};casecards=[]
    for row in cases():
        r=review[row['id']]
        evidence=link(row['evidence'],'既存の検査記録') if row['evidence'] else link('reports/general-probability-v1.json','有限確率の区別検査')
        state='入力一致で継承' if r['retained_evidence']=='input-identical' else '作業対象の選択ファイルのみ変更。旧証拠を保持し、変更点を一覧へ記録' if r.get('changed_inputs')==['data/work-state.json'] else '個別の検査記録を参照'
        words=' '.join('<a href="#'+E(n)+'">'+E(n)+'</a>' for n in row['entries'])
        casecards.append('<article><h3>'+E(row['label'])+'</h3><p>'+E(row['distinction'])+'</p><p>応用の設計例：'+E(' ／ '.join(row['applications']))+'</p><p>'+words+'</p><p>'+link(row['native'],'実際のNoema文書')+' / '+evidence+'</p><small>'+E(state+'。'+row['application_status'])+'</small></article>')
    example_report=read('output/general-language-v1/report.json');examplecards=[]
    for row in example_report['alignment']['examples']:
        actual=read('output/general-language-v1/document.json');offset=len(actual['declarations'])
        images=[]
        for key in ('positive','negative'):
            record=example_report['records'][offset+row[key]]
            images.append('<figure><figcaption>'+('成立する入力' if key=='positive' else '関係 '+E(row['changed_relation'])+' を満たさない入力')+'</figcaption><img loading="lazy" src="ink/'+record['cache_key']+'.svg"></figure>')
        examplecards.append('<article><h3>'+E(row['name'])+'</h3><p>'+E(row['scope'])+'</p>'+''.join(images)+'</article>')
    css='''body{margin:auto;max-width:1180px;padding:28px;font:16px/1.75 system-ui;background:#f4f2ec;color:#222b2a}h1{font-size:36px}h2{margin-top:48px}a{color:#16635b}article{background:white;border:1px solid #deded4;padding:20px;margin:14px 0;border-radius:8px;overflow-wrap:anywhere}input,select{font:inherit;padding:10px;border:1px solid #aaa;border-radius:4px}input{width:min(600px,75%)}small{color:#68716c}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}img{width:100%;height:auto}figure{margin:14px 0}nav{position:sticky;top:0;background:#f4f2ec;padding:10px 0}article[hidden]{display:none}'''
    script='''const search=document.querySelector('#search'),layer=document.querySelector('#layer');function filter(){let n=0;const term=search.value.toLowerCase();document.querySelectorAll('#dictionary>article').forEach(a=>{a.hidden=!(a.textContent.toLowerCase().includes(term)&&(!layer.value||a.dataset.layer===layer.value));if(!a.hidden)n++});document.querySelector('#count').textContent=n+'項目'}function reveal(){const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(target&&target.matches('#dictionary>article')&&target.hidden){search.value='';layer.value='';filter();target.scrollIntoView()}}search.addEventListener('input',filter);layer.addEventListener('change',filter);window.addEventListener('hashchange',reveal);filter();reveal();'''
    page='<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Noema 共通仕様・辞書・表現例</title><style>'+css+'</style><h1>Noema 共通仕様・辞書・表現例</h1>'
    page+='<p>作品を越えて、意味の区別を保って組み立てるための入口。</p><p>'+link('docs/general-language-v1.md','共通仕様を読む')+' / '+link('output/two-work-final-v2/index.html','完成済みの二作品')+' / '+link('data/general-language-catalog-v1.json','版を固定したカタログ')+'</p>'
    page+='<nav><a href="#capabilities">表現分野</a> · <a href="#examples">新しい構成の対照例</a> · <a href="#dictionary">辞書</a></nav>'
    page+='<p>共通語375、共通追加19、分野別の意味規約1,488、作品内参照27。基本宣言と合成定義を区別しています。有限の検査を、あらゆる自然言語の意味を網羅した証明とは扱いません。</p>'
    page+='<h2 id="capabilities">表現分野と残すべき区別</h2>'+''.join(casecards)
    page+='<h2 id="examples">新しい構成の対照例</h2><p>追加語彙と使用例の148記録を実図形から復号し、準備した構文との完全一致を確認しました。以下は関係入力を変えた機構例です。</p>'+''.join(examplecards)
    page+='<h2>共通辞書</h2><p><input id="search" type="search" placeholder="語・意味・役割を検索" aria-label="辞書を検索"> <select id="layer" aria-label="辞書の層"><option value="">全て</option>'+''.join('<option value="'+k+'">'+v+'</option>' for k,v in labels.items())+'</select></p><p id="count"></p><div id="dictionary">'+''.join(sections)+'</div><script>'+script+'</script></html>'
    (OUT/'index.html').write_text(page,encoding='utf-8',newline='\n')
    report=dict(entries=len(catalog),visible_declaration_matches=len(visible),without_current_ink=[n for n,r in catalog.items() if r['symbol'] not in visible],
                source_sha256=inputs,index_sha256=sha('output/general-language-v1/index.html'),scope='既存の実図形と同じ宣言の照合。新しい意味判断ではない。')
    atomic_json(OUT/'publication.json',report)
    print(json.dumps({k:report[k] for k in ('entries','visible_declaration_matches','without_current_ink')},ensure_ascii=False))


if __name__=='__main__':main()
