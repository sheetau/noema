"""Static reading edition from record-level ink results; failures stay visible."""
from html import escape
import hashlib,json,re
from pathlib import Path
from scripts.long_run import atomic_json
from scripts.two_work_inventory import read

TITLES={'kant':'カント — 啓蒙とは何か','einstein':'アインシュタイン — 運動物体の電気力学について'}
STYLE='''body{margin:0;background:#f7f5ef;color:#242824;font:17px/1.8 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:40px 28px}a{color:#285d59}nav{display:flex;gap:22px;flex-wrap:wrap;font-size:14px}h1{font-size:30px;font-weight:500}h2{font-size:21px;font-weight:500}article{background:white;padding:24px;margin:24px 0;border:1px solid #dfdfd5;border-radius:5px}.source{font-family:Georgia,serif;font-size:20px;line-height:1.8;overflow-wrap:anywhere}.ink{display:block;width:100%;height:auto;margin:16px 0}small,.muted{color:#68716a}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}details{margin:12px 0}.issue{border-left:4px solid #b66737;padding:14px;background:#fff2e8}ol{padding-left:25px}li{margin:8px 0}code{overflow-wrap:anywhere}.dictionary-ink{max-height:700px;overflow:auto}math{font-size:1em}table{border-collapse:collapse;width:100%}td,th{padding:10px;border-bottom:1px solid #ddd;text-align:left}@media(max-width:600px){main{padding:20px 12px}article{padding:12px}.source{font-size:18px}}'''


def write_page(path,title,body,nav=''):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        +'<title>'+escape(title)+'</title><style>'+STYLE+'</style><main><nav>'+nav+'</nav><h1>'+escape(title)+'</h1>'+body+'</main></html>',encoding='utf-8',newline='\n')


def source_html(unit,maths):
    def replace(match):
        row=maths[match.group(1)];raw=row['mathml']
        if hashlib.sha256(raw.encode()).hexdigest()!=row['sha256']:raise ValueError('Source MathML changed')
        if re.search(r'<\s*(script|iframe|object)|\bon\w+\s*=|javascript:',raw,re.I):raise ValueError('Unsafe source MathML')
        return raw
    return re.sub(r'\[(M\d+)\]',replace,escape(unit['text']))


def ink(result,prefix='ink/'):
    if result is None:return '<p class="issue">検証待ち</p>'
    if result['status']!='passed':
        return '<div class="issue">未確認：'+escape(result['status'])+'<pre>'+escape(result.get('error',str(result.get('missing',[]))))+'</pre></div>'
    return '<a href="'+prefix+result['svg']+'"><img class="ink" loading="lazy" src="'+prefix+result['svg']+'" alt="Noema 円文字"></a>'


def details(label,value):
    return '<details><summary>'+escape(label)+'</summary><pre>'+escape(json.dumps(value,ensure_ascii=False,indent=2))+'</pre></details>'


def publish_work(out,work,document,toc,catalog,bridge,report):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    results={r['index']:r for r in report.get('records',[])};ds=document['declarations'];n=len(ds)
    nav='<a href="../index.html">二作品</a><a href="index.html">目次</a><a href="dictionary-000.html">辞書</a><a href="annotations.html">注記・識別表記</a>'
    first={}
    for u in toc['units']:
        for i in u['edition_first_occurrence']:first[i]=u['id'].split(':')[-1]+'.html#s'+str(i)
    maths={m['id']:m for m in toc['math']};links=[];rendered=set()
    for pos,u in enumerate(toc['units']):
        filename=u['id'].split(':')[-1]+'.html';short=re.sub(r'\s+',' ',u['text'])[:85]
        links.append('<li><a href="'+filename+'">'+escape(short)+'</a> <small>'+escape(u['kind'])+'</small></li>')
        body='<p class="muted">'+escape(u['id'])+'</p><article class="source" lang="de">'+source_html(u,maths)+'</article>'
        for i in u['edition_statements']:
            if i in u['edition_first_occurrence']:
                body+='<article id="s'+str(i)+'"><small>Noema '+str(i+1)+'</small>'+ink(results.get(n+i))+details('構文',document['statements'][i])+'</article>';rendered.add(i)
            else:body+='<p><a href="'+first[i]+'">この単位と共通する意味群：Noema '+str(i+1)+'</a></p>'
        if u['annotation_ids']:body+=details('原文の注・参照', [a for a in toc['annotations'] if a['id'] in u['annotation_ids']])
        adjacent=[]
        for delta,label in ((-1,'前へ'),(1,'次へ')):
            if 0<=pos+delta<len(toc['units']):adjacent.append('<a href="'+toc['units'][pos+delta]['id'].split(':')[-1]+'.html">'+label+'</a>')
        write_page(out/filename,TITLES[work],body+'<nav>'+' '.join(adjacent)+'</nav>',nav)
    if rendered!=set(range(toc['main_statements'])):raise ValueError('Reading edition omitted a main assertion')
    state='全図形の復号一致' if report.get('validation_success') else '検証中・未確認項目あり'
    write_page(out/'index.html',TITLES[work],'<p>'+state+'。原文 '+str(len(toc['units']))+' 単位／本文 '+str(toc['main_statements'])+' 主張。</p>'
        +'<p>原文と共通する意味群を対照して読む版です。同じ意味群を参照する単位では、最初の掲載箇所へリンクします。原文の数式・著者脚注と、Noema側の補助注記を保持しています。</p><ol>'+''.join(links)+'</ol>',nav)
    name_links={d['name']:f'dictionary-{i//80:03d}.html#d{i}' for i,d in enumerate(ds)}
    for start in range(0,n,80):
        body='<p>宣言 '+str(start+1)+'–'+str(min(start+80,n))+' / '+str(n)+'</p>'
        for i in range(start,min(start+80,n)):
            d=ds[i];entry=catalog.get(d['name'],{});contract=entry.get('contract',{})
            meaning=contract.get('meaning_ja',contract.get('meaning',''))
            body+='<article id="d'+str(i)+'"><h2>'+escape(entry.get('label',d['kind']))+'</h2><p>'+escape(meaning)+'</p><details><summary>円文字で読む</summary><div class="dictionary-ink">'+ink(results.get(i))+'</div></details>'
            body+=details('宣言と既存の語義',dict(declaration=d,meaning=entry))+'</article>'
        paging=' '.join('<a href="dictionary-'+f'{i//80:03d}'+'.html">'+str(i+1)+'</a>' for i in range(0,n,80))
        write_page(out/f'dictionary-{start//80:03d}.html',TITLES[work]+' — 辞書',body+'<nav>'+paging+'</nav>',nav)
    body='<h2>補助注記</h2>'
    for i in range(toc['main_statements'],len(document['statements'])):
        body+='<article><small>注記 '+str(i-toc['main_statements']+1)+'</small>'+ink(results.get(n+i))+details('構文',document['statements'][i])+'</article>'
    body+='<h2>識別表記</h2><p>原文の綴りと、本文で参照する語の対応です。</p>'
    for row in toc['identifiers']['entries']:
        target=bridge['mapping'].get(row['symbol']);label=' / '.join(f['text'] for f in row['forms'])
        body+='<p>'+escape(label)
        if target in name_links:body+=' — <a href="'+name_links[target]+'">辞書の参照先</a>'
        else:body+=' — <code>'+escape(row['symbol'])+'</code>'
        body+='</p>'+details('保存された識別表記',row)
    body+=details('原文の注・参照一覧',toc['annotations'])
    write_page(out/'annotations.html',TITLES[work]+' — 注記・識別表記',body,nav)
    atomic_json(out/'source-alignment.json',toc);atomic_json(out/'meanings.json',catalog)
    atomic_json(out/'prepared-document.json',document)
    if report.get('validation_success'):
        recovered=dict(document,declarations=[results[i]['native'] for i in range(n)],statements=[results[n+i]['native'] for i in range(len(document['statements']))])
        if recovered!=document:raise ValueError('Whole recovered document differs')
        atomic_json(out/'recovered-document.json',recovered)
        from noema.constructed import format_graph
        (out/'recovered.noema').write_text(format_graph(recovered),encoding='utf-8',newline='\n')
    return dict(units=len(toc['units']),main_assertions=len(rendered),declarations=n,
                auxiliary_assertions=len(document['statements'])-toc['main_statements'],math=len(maths),validation_success=report.get('validation_success',False))


def publish_index(out,report):
    body='<p>固定した円文字による二作品の統合版。原文の採用解釈は既存の判断を引き継ぎ、実際の円・線から構文を復号して照合します。</p>'
    for work in ('kant','einstein'):
        row=report.get('works',{}).get(work,{})
        body+='<article><h2><a href="'+work+'/index.html">'+TITLES[work]+'</a></h2><p>'+escape(row.get('stage','待機中'))+'</p>'+details('検証集計',row)+'</article>'
    body+='<p><a href="report.json">全体報告</a> · <a href="status.json">進捗</a></p>'
    write_page(Path(out)/'index.html','Noema — 二作品の統合版',body)
