"""Offline course for the published circle grammar; separate learner and reviewer files."""
from copy import deepcopy
from functools import lru_cache
from html import escape
from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.visible_senses_vocabulary import SensesVocabulary,ROOT
from scripts.visible_senses_page import PublicWriter,compile_page,decode_page
from scripts.visible_syntax_geometry import render,to_svg,from_svg,recognize
from scripts.visible_syntax import Reader,END_GLYPH
from scripts.visible_syntax_vocabulary import KEYWORDS
from scripts.visible_sharing import SHARING
from scripts.visible_page import frame,FRAME_DIRECTIONS,packet
from scripts.visible_word_forms import Word,symbol,_marker
from scripts.shared_modality import call,v,op
from scripts.shared_reference import I,T,definition
from scripts.shared_time import q
from scripts.shared_focus import quote,disquote,eq

OUT=ROOT/'output/noema-reader-v1'
SOURCE='data/reader-course-v1.json'
SCHEMA='noema-reader-responses-1'

@lru_cache(maxsize=1)
def vocabulary():return SensesVocabulary()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def local(parts):return symbol(Word('compound',tuple(parts)),vocabulary())
def sequence(*xs):return dict(kind='sequence',element=I,items=list(xs))
def statement(body,kind='ask'):return dict(kind=kind,body=body)
def doc(statements,extra=()):
    names=set();local_names={d['name'] for d in extra}
    for x in [*statements,*extra]:names.update(_references(x))
    plain=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(names-local_names),statements=[])))
    plain['declarations']+=list(extra);plain['statements']=list(statements)
    return normalize_document(plain)

@lru_cache(maxsize=1)
def basic_documents():
    rain=call('rain',call('home'));red=lambda x:call('red',x)
    result={
        '01':doc([statement(call('above',call('aki'),call('nao')))]),
        '02':doc([statement(call('give',call('nao'),call('book'),call('aki')))]),
        '03':doc([statement(op('not',q('forall','person',I,red(v('person')))))]),
        '04':doc([statement(q('forall','person',I,op('not',red(v('person')))))]),
        '05':doc([statement(q('forall','person',I,q('exists','other',I,call('above',v('person'),v('other')))))]),
        '06':doc([statement(q('forall','person',I,q('exists','other',I,call('above',v('other'),v('person')))))]),
        '07':doc([statement(eq(quote(rain),quote(rain)))]),
        '08':doc([statement(rain)]),
        '11':doc([dict(kind='suppose',condition=rain,statements=[statement(red(call('book')))])]),
        '13':doc([statement(eq(sequence(call('aki'),call('nao')),sequence(call('nao'),call('aki'))))]),
        '14':doc([statement(disquote(quote(rain)))])}
    name=local(('rain','home','red'));result['09']=doc([], [definition(name,[],T,rain)])
    name=local(('fruit','red','round'));result['10']=doc([statement(call(name,call('book')))],
        [definition(name,[('item',I)],T,op('and',red(v('item')),call('round',v('item'))))])
    common=op('and',call('above',call('aki'),call('nao')),call('inside',call('book'),call('home')))
    result['12']=doc([statement(op('and',common,op('and',common,common)))])
    return dict(sorted(result.items()))

ADVANCED={'15':'senses-selection','16':'focus-topiccontrast','17':'senses-synonym'}
@lru_cache(maxsize=1)
def teaching_documents():
    return {'rain-town':doc([statement(call('rain',call('town')),'assert')]),
        'question-red':doc([statement(call('red',call('nao')))])}

@lru_cache(maxsize=1)
def curriculum():return json.loads((ROOT/SOURCE).read_text(encoding='utf-8'))

def sort_text(t):
    if isinstance(t,str):return dict(individual='I 個体',truth='T 真理値',situation='S 状況',number='N 数',content='C 内容',message='M 発話')[t]
    k=t['kind']
    if k=='sequence':return '列['+sort_text(t['element'])+']'
    if k=='description':return '記述'+str(t.get('rank',0))+'['+sort_text(t['result'])+']'
    return ('問い' if k=='question' else '関数')+'['+', '.join(sort_text(p) for p in t['parameters'])+']'+('' if k=='question' else ' → '+sort_text(t['result']))

def glyph_svg(kind,name):
    w=PublicWriter(vocabulary(),automatic=False)
    if kind=='word':w.name(vocabulary().declaration(name)['name'])
    elif kind=='keyword':w.keyword(name)
    elif kind=='number':w.natural(int(name))
    elif kind=='frame':w.glyphs=[frame(name)]
    elif kind=='end':w.glyphs=[END_GLYPH]
    elif kind=='marker':w.glyphs=[_marker(name,0.)]
    else:raise ValueError('Unknown course glyph kind')
    # A complete visible row frame supplies the large-circle scale anchor even
    # for a lone medium-circle word, numeral, or small terminator.
    svg=to_svg(render(packet(w.glyphs,0,final=True,vocabulary=vocabulary()))['shapes'])
    root=ET.fromstring(svg);x,y,width,height=map(float,root.get('viewBox').split())
    if y < -64 or y+height > 128:raise ValueError('Legend exceeds common vertical scale')
    root.set('viewBox',f'{x} -64 {width} 192')
    return ET.tostring(root,encoding='unicode')+'\n'

@lru_cache(maxsize=None)
def rendered_basic(key,training=False):
    source=(teaching_documents() if training else basic_documents())[key];encoded=vocabulary().encode(source)
    page=compile_page(encoded,vocabulary(),max_width=2200.)
    svg=to_svg(page['shapes']);decoded=decode_page(from_svg(svg),vocabulary())['document']
    if decoded!=encoded:raise ValueError('Course page differs: '+key)
    return dict(native=source,encoded=encoded,svg=svg,page=page)

CSS='''*{box-sizing:border-box}body{margin:0;background:#f3f0e9;color:#203438;font:17px/1.8 system-ui,"Yu Gothic",sans-serif}header,main,footer{max-width:1120px;margin:auto;padding:24px}header{border-bottom:1px solid #b4c4be}nav{display:flex;gap:22px;flex-wrap:wrap}a{color:#125e60}h1{font-size:2.1rem;line-height:1.4}h2{margin-top:46px;font-size:1.45rem}h3{font-size:1.1rem}p{max-width:78ch}.kicker{font-size:13px;letter-spacing:.13em;color:#52706c}.card,section.exercise{background:#fffdf8;border:1px solid #c6d1ca;border-radius:12px;padding:24px;margin:20px 0}figure{margin:14px 0;overflow:auto;background:white;padding:12px;border:1px solid #dde4df}figure svg{display:block;width:100%;height:auto;min-width:520px}.glyph,.smallglyph{overflow-x:auto}.glyph svg,.smallglyph svg{display:block;height:96px;width:auto;max-width:none}.smallglyph{min-width:240px}table{border-collapse:collapse;width:100%;background:#fffdf8}td,th{padding:12px;border-bottom:1px solid #d3ddd6;text-align:left;vertical-align:top}th{background:#e6ede6}.tablewrap{overflow:auto}code,pre{font:14px/1.6 ui-monospace,Consolas,monospace}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f3ec;padding:16px}summary{cursor:pointer;color:#125e60}input,select,textarea,button{font:inherit;max-width:100%}input,select,textarea{padding:10px;border:1px solid #78958b;border-radius:5px}label.choice{display:block;padding:9px;border-bottom:1px solid #edf0eb}button{background:#155d59;color:white;border:0;border-radius:6px;padding:12px 24px;cursor:pointer}.muted{color:#526b66;font-size:15px}.wordcard{break-inside:avoid}.wordcard h2{margin:0}.tags{font:14px/1.5 ui-monospace,monospace;color:#526b66}textarea{width:100%;min-height:75px}fieldset{border:0;padding:0;margin:16px 0}legend{font-weight:bold}.sticky{position:sticky;top:0;background:#f3f0e9;padding:12px 0;z-index:2}#status{min-height:2em;color:#155d59}@media(max-width:650px){header,main,footer{padding:16px}.card,section.exercise{padding:16px}h1{font-size:1.7rem}figure svg{min-width:800px}td,th{padding:8px}nav{gap:12px}}@media print{body{background:white}nav,.sticky,button{display:none}figure svg{min-width:0!important}.exercise{break-before:page}.card{break-inside:avoid}}'''

def page(title,body,script=''):
    return '<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>'+escape(title)+'</title><style>'+CSS+'</style><header><div class="kicker">NOEMA · CIRCLE READER · 0.16 / 12</div><h1>'+escape(title)+'</h1><nav><a href="index.html">読み方</a><a href="dictionary.html">375語の辞書</a><a href="exercises.html">読解課題</a></nav></header><main>'+body+'</main><footer>円文字読本 第1版。共有語彙第12版。オフラインで使用できます。</footer>'+('<script>'+script+'</script>' if script else '')+'</html>'

def table(headers,rows):
    return '<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+x+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def figure(svg,caption=''):
    return '<figure>'+svg+('<figcaption>'+escape(caption)+'</figcaption>' if caption else '')+'</figure>'
def paras(items):return ''.join('<p>'+escape(p)+'</p>' for p in items)

def guide_html():
    c=curriculum();out=paras(c['introduction'])
    out+='<div class="card"><strong>学ぶ順序</strong><ol>'+''.join('<li><a href="#'+x['id']+'">'+escape(x['title'])+'</a></li>' for x in c['lessons'])+'</ol></div>'
    for lesson in c['lessons']:
        out+='<section id="'+lesson['id']+'"><h2>'+escape(lesson['title'])+'</h2>'+paras(lesson['paragraphs'])
        kind=lesson.get('table')
        if kind=='frames':
            rows=[['<div class="smallglyph">'+glyph_svg('frame',k)+'</div>',escape(v)] for k,v in c['frames'].items()]
            rows += [['<div class="smallglyph">'+glyph_svg('marker',k)+'</div>',escape(v)] for k,v in c['markers'].items()]
            rows.append(['<div class="smallglyph">'+glyph_svg('end','')+'</div>','小円：今読んでいる可変長の列・名前・文書範囲の終端。文法上の位置で対象を決める。'])
            out+=table(['可視の形','読み'],rows)
        elif kind=='keywords':
            out+=table(['操作','形（分類＋操作）','続けて読むもの'],[[escape(k+' / '+v[0]),'<div class="smallglyph">'+glyph_svg('keyword',k)+'</div>',escape(v[1])] for k,v in c['keywords'].items()])
        elif kind=='numbers':out+=table(['自然数','可視の桁列'],[[str(n),'<div class="smallglyph">'+glyph_svg('number',str(n))+'</div>'] for n in (0,1,2,3,12,16)])
        if 'training' in lesson:
            key=lesson['training'];out+=figure(rendered_basic(key,True)['svg'])+paras(c['training_explanations'][key])
        out+='</section>'
    return page('円と線から読む Noema',out)

def dictionary_html():
    out=paras(curriculum()['dictionary_introduction'])+'<div class="sticky"><label>語・意味・役割を検索 <input id="search" type="search" placeholder="例：候補、主張、sense"></label><p id="count" class="muted">375語</p></div>'
    vocab=vocabulary()
    for n in sorted(vocab._words):
        e=vocab.entry(n);d=vocab._plain_declaration(n)
        rolelist=''.join('<li>'+escape(str(i+1)+'. '+role+' — '+sort_text(t))+'</li>' for i,(role,t) in enumerate(zip(e['roles'],e['parameters'],strict=True)))
        out+='<article class="card wordcard"><h2>'+escape(n)+'</h2><div class="tags">'+escape(' / '.join(vocab.word(n).parts))+'</div><div class="glyph">'+glyph_svg('word',n)+'</div><p>'+escape(e['meaning'])+'</p>'
        out+='<p><strong>結果型：</strong>'+escape(sort_text(e['result']))+'</p>'
        out+=('<ol style="list-style:none;padding-left:0">'+rolelist+'</ol>') if rolelist else '<p>引数なし。</p>'
        out+='<details><summary>入力規約・反例・定義</summary>'+paras(e['context'])+paras(e['contrast'])
        text=format_graph(dict(schema_version='0.16',lexicon_version='0.16',declarations=[d],statements=[])) if d['kind']=='primitive' else json.dumps(d,ensure_ascii=False,indent=2)
        out+='<pre>'+escape(text)+'</pre><p class="muted">定義欄の参照語はこの辞書で引けます。共有定義は依存を含めて導入します。</p></details></article>'
    script="const cards=[...document.querySelectorAll('.wordcard')];document.querySelector('#search').addEventListener('input',e=>{const q=e.target.value.toLocaleLowerCase();let n=0;for(const c of cards){c.hidden=!c.textContent.toLocaleLowerCase().includes(q);if(!c.hidden)n++;}document.querySelector('#count').textContent=n+'語';});"
    return page('語形と意味の辞書',out,script)

def exercise_assets():
    assets={key:[rendered_basic(key)['svg']] for key in basic_documents()}
    from scripts.check_visible_senses_library import saved_case
    for key,label in ADVANCED.items():assets[key]=saved_case(label)['svgs']
    return assets

def exercise_identity(assets):
    # Hashes identify the administered questions, never encode lexical shapes or answers.
    return digest(json.dumps(dict(edition=12,questions=[{k:x[k] for k in ('id','level','question','options')} for x in curriculum()['exercises']],
        pages={k:[digest(s.encode('utf-8')) for s in v] for k,v in assets.items()}),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())

def exercises_html(assets):
    c=curriculum();identity=exercise_identity(assets)
    out=paras(c['exercise_introduction'])+'<div class="card"><label>匿名の参加者コード <input id="participant" maxlength="64"></label><p><label>立場 <select id="role"><option value="unspecified">未指定</option><option value="author">設計・実装に関わった</option><option value="independent">設計・実装に関わっていない</option></select></label></p><label><input id="exposed" type="checkbox"> この課題の解答を以前に見た</label></div>'
    for exercise in c['exercises']:
        key=exercise['id'];out+='<section class="exercise" data-question="'+key+'"><div class="kicker">'+escape(exercise['level'])+'</div><h2>課題 '+key+'</h2><p>'+escape(exercise['question'])+'</p>'
        for i,svg in enumerate(assets[key]):out+=figure(svg,'図 '+key+'・'+str(i+1)+' / '+str(len(assets[key])))
        out+='<fieldset><legend>読みとして適切なものを一つ選んでください</legend>'
        for option in exercise['options']:
            out+='<label class="choice"><input type="radio" name="q'+key+'" value="'+option['id']+'"> '+escape(option['text'])+'</label>'
        out+='<label class="choice"><input type="radio" name="q'+key+'" value="unknown"> わからない</label></fieldset><label>判断に使った図形や、迷った箇所（任意）<textarea data-note="'+key+'"></textarea></label></section>'
    out+='<div class="card"><p>解答はこの画面から送信されません。下のボタンでJSONファイルを保存し、実施者へ渡してください。個人名の入力は不要です。</p><button id="download" type="button">解答を保存する</button><p id="status" role="status"></p></div>'
    script='''document.querySelector('#download').addEventListener('click',()=>{const answers={};for(const s of document.querySelectorAll('[data-question]')){const id=s.dataset.question;const selected=s.querySelector('input:checked');answers[id]={option:selected?selected.value:null,note:s.querySelector('textarea').value};}const result={schema:SCHEMA,exercise_sha256:IDENTITY,participant:document.querySelector('#participant').value,role:document.querySelector('#role').value,prior_answer_exposure:document.querySelector('#exposed').checked,answers};const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));a.download='noema-reader-responses.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);document.querySelector('#status').textContent='解答ファイルを作成しました。未回答は未回答のまま保存しています。';});'''.replace('SCHEMA',json.dumps(SCHEMA)).replace('IDENTITY',json.dumps(identity))
    return page('図形から読む課題',out,script)

def grade(response,identity):
    if not isinstance(response,dict) or set(response)!={'schema','exercise_sha256','participant','role','prior_answer_exposure','answers'}:raise ValueError('Invalid response fields')
    if response['schema']!=SCHEMA or response['exercise_sha256']!=identity:raise ValueError('Wrong exercise edition')
    if not isinstance(response['participant'],str) or len(response['participant'])>64 or response['role'] not in ('author','independent','unspecified') or type(response['prior_answer_exposure']) is not bool:raise ValueError('Invalid participant declaration')
    expected={x['id']:x for x in curriculum()['exercises']};answers=response['answers']
    if not isinstance(answers,dict) or set(answers)!=set(expected):raise ValueError('Missing or extra questions')
    rows=[]
    for key,question in expected.items():
        answer=answers[key]
        if not isinstance(answer,dict) or set(answer)!={'option','note'} or not isinstance(answer['note'],str):raise ValueError('Invalid answer fields')
        option=answer['option']
        if option not in {None,'unknown',*[x['id'] for x in question['options']]}:raise ValueError('Unknown answer option')
        status='unanswered' if option is None else 'unknown' if option=='unknown' else 'correct' if option==question['correct'] else 'incorrect'
        rows.append(dict(id=key,status=status,selected=option,expected=question['correct'],note=answer['note']))
    return dict(schema='noema-reader-grading-1',exercise_sha256=identity,participant=response['participant'],declared_role=response['role'],
        prior_answer_exposure=response['prior_answer_exposure'],independence='not_verified_by_software',
        counts={s:sum(r['status']==s for r in rows) for s in ('correct','incorrect','unknown','unanswered')},results=rows,
        limit='選択問題の一致だけを採点する。独立性、自由記述の妥当性、任意文書の読解能力、言語の完成は自動認定しない。')

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    different=path.exists() and path.read_text(encoding='utf-8')!=text
    if different and (not path.resolve().is_relative_to(OUT.resolve()) or (ROOT/'reports/reader-course-v1.json').exists()):
        raise ValueError('Existing course artifact differs: '+str(path))
    if different or not path.exists():path.write_text(text,encoding='utf-8',newline='\n')

def prepare():
    c=curriculum()
    if set(c['keywords'])!=set(KEYWORDS)|set(SHARING):raise ValueError('Incomplete grammar legend')
    if set(c['frames'])!=set(FRAME_DIRECTIONS):raise ValueError('Incomplete row legend')
    assets=exercise_assets()
    write(OUT/'learner/index.html',guide_html());print('Prepared reading guide',flush=True)
    write(OUT/'learner/dictionary.html',dictionary_html());print('Prepared 375-word dictionary',flush=True)
    write(OUT/'learner/exercises.html',exercises_html(assets));print('Prepared 17 exercises',flush=True)
    identity=exercise_identity(assets)
    answers=dict(exercise_sha256=identity,exercises=[dict(id=x['id'],correct=x['correct'],reason=x['reason']) for x in c['exercises']])
    write(OUT/'reviewer/answers.json',json.dumps(answers,ensure_ascii=False,indent=2)+'\n')
    for key,d in basic_documents().items():write(OUT/('reviewer/exercise-'+key+'.noema'),format_graph(d)+'\n')
    response=dict(schema=SCHEMA,exercise_sha256=identity,participant='',role='unspecified',prior_answer_exposure=False,
        answers={x['id']:dict(option=None,note='') for x in c['exercises']})
    write(OUT/'reviewer/blank-response.json',json.dumps(response,ensure_ascii=False,indent=2)+'\n')
    # Only the learner directory is distributed; answers and Native exam sources stay separate.
    with zipfile.ZipFile(OUT/'noema-reader-v1.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted((OUT/'learner').iterdir()):
            info=zipfile.ZipInfo(p.name,date_time=(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes())

def main(argv=None):
    import argparse
    cli=argparse.ArgumentParser(description=__doc__);sub=cli.add_subparsers(dest='command',required=True)
    sub.add_parser('build');g=sub.add_parser('grade');g.add_argument('response',type=Path);g.add_argument('output',type=Path)
    args=cli.parse_args(argv)
    if args.command=='build':prepare()
    else:
        from scripts.check_reader_course import verify_published
        key=verify_published()
        result=grade(json.loads(args.response.read_text(encoding='utf-8')),key)
        result['response_sha256']=digest(args.response.read_bytes())
        write(args.output,json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
