"""Bounded structural contrasts and a reviewable draft specimen gallery."""
from functools import lru_cache
from pathlib import Path
import hashlib
import html
import json
import time
from noema.constructed_discourse import normalize_document

from scripts.check_visible_syntax import (
    vocabulary, named, call, variable, num, logic, quant, quote, doc,
    assertion, integrated_document,
)
from scripts.structural_circle import (
    compile_document, compile_statement, decode, to_svg, from_svg, VERSION,
    catalogue, StructuralReader, PublicWriter, _shape_set,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/structural-circle-draft-1'


@lru_cache(maxsize=1)
def full_vocabulary():
    from scripts.visible_senses_vocabulary import SensesVocabulary
    return SensesVocabulary()


def cases():
    one, two = num(1), num(2)
    eq = logic('equal', one, two)
    lam = dict(kind='lambda', parameters=[dict(name='x', sort='number')], body=variable('x'))
    pred = dict(kind='lambda', parameters=[dict(name='x', sort='number')], body=logic('equal', variable('x'), one))
    seq = dict(kind='sequence', element='number', items=[one, two])
    content = dict(kind='content', variable='w', body=eq)
    message = dict(kind='message', force='direct', content=content)
    rows = [
        ('two-arguments', '二引数：鳥が木より上にある', doc(assertion(call('above',call('birdone'),call('treeone'))),roots=('above','birdone','treeone'))),
        ('arguments-reversed', '引数を交換：木が鳥より上にある', doc(assertion(call('above',call('treeone'),call('birdone'))),roots=('above','birdone','treeone'))),
        ('three-arguments', '三引数：渡す人・相手・物', doc(assertion(call('give',call('aki'),call('nao'),call('book'))),roots=('give','aki','nao','book'))),
        ('not-all', '否定の内側に全称量化', doc(assertion(logic('not',quant('forall','x',call('rain',variable('x'))))),roots=('rain',))),
        ('all-not', '全称量化の内側に否定', doc(assertion(quant('forall','x',logic('not',call('rain',variable('x'))))),roots=('rain',))),
        ('binding-outer', '内側から外側の束縛を参照', doc(assertion(quant('forall','x',quant('exists','y',logic('equal',variable('x'),variable('y'))))))),
        ('binding-inner', '内側の束縛を二度参照', doc(assertion(quant('forall','x',quant('exists','y',logic('equal',variable('y'),variable('y'))))))),
        ('function-reference', '関数への参照を使う質問', doc(dict(kind='ask',body=dict(kind='question',function=dict(kind='function_ref',symbol=named('rain')))),roots=('rain',))),
        ('integrated', '定義・引用・仮定を含む文書', integrated_document()),
    ]
    expressions = [(k, logic(k,eq,*(() if k=='not' else (logic('equal',two,two),)))) for k in ('not','and','or','implies','iff')]
    expressions += [
        ('negative', logic('equal',num(-7,3),num(-14,6))),
        ('apply', logic('equal',dict(kind='apply',function=lam,arguments=[two]),two)),
        ('disquote', logic('equal',dict(kind='disquote',description=quote(one)),one)),
        ('ranked-quote', logic('equal',quote(dict(kind='disquote',description=quote(one)),1),quote(dict(kind='disquote',description=quote(one)),1))),
        ('lift', logic('equal',dict(kind='quoted_lift',description=quote(one)),quote(quote(one)))),
        ('quoted-apply', logic('equal',dict(kind='quoted_application',function=quote(lam),arguments=[quote(two)]),quote(dict(kind='apply',function=lam,arguments=[two])))),
        ('answer', dict(kind='answer_matches',question=dict(kind='question',function=pred),arguments=[one])),
        ('length', logic('equal',dict(kind='length',sequence=seq),two)),
        ('position', dict(kind='position',sequence=seq,index=num(0),value=one)),
        ('concat', logic('equal',dict(kind='concat',left=seq,right=dict(kind='sequence',element='number',items=[])),seq)),
        ('fold', logic('equal',dict(kind='fold',sequence=seq,initial=one,step=dict(kind='lambda',parameters=[dict(name='a',sort='number'),dict(name='b',sort='number')],body=variable('b'))),two)),
        ('message-content', logic('equal',dict(kind='message_content',message=message),content)),
        ('evaluation', quant('forall','w',dict(kind='evaluate',content=content,situation=variable('w')),sort='situation')),
        ('closed-quote', logic('equal',quote(quant('forall','x',logic('equal',variable('x'),variable('x')))),quote(quant('forall','y',logic('equal',variable('y'),variable('y')))))),
    ]
    rows += [(key, key, doc(assertion(body))) for key,body in expressions]
    sorts = ['individual','number','truth','situation','content','message',
             dict(kind='function',parameters=['number'],result='number'),
             dict(kind='sequence',element='individual'),dict(kind='question',parameters=['number','individual']),
             dict(kind='description',result='truth'),dict(kind='description',rank=2,result='number')]
    rows += [('type-'+str(i), '型 '+str(i), doc(assertion(quant('forall','x',logic('equal',variable('x'),variable('x')),sort=t)))) for i,t in enumerate(sorts)]
    rows += [('perform', '発話の実行', doc(dict(kind='perform',body=message)))]
    return rows


@lru_cache(maxsize=1)
def specimens():
    rows = []
    for key, label, document in cases():
        compiled = compile_document(document, vocabulary())
        svg = to_svg(compiled['shapes'])
        recovered = decode(from_svg(svg), vocabulary())
        if recovered != document:
            raise ValueError('Structural document differs: '+key)
        statement = compile_statement(document['statements'][0], vocabulary())
        statement_svg = to_svg(statement['shapes'])
        # Parse independently from the stand-alone statement geometry.
        restored = decode(from_svg(statement_svg), vocabulary(), mode='statement')
        normalized = normalize_document(dict(document, statements=[restored]))
        if normalized['statements'][0] != document['statements'][0]:
            raise ValueError('Structural statement differs: '+key)
        rows.append(dict(key=key,label=label,document=document,svg=svg,statement_svg=statement_svg,
                         glyphs=compiled['glyphs'],shapes=len(compiled['shapes']),forks=compiled['forks']))
    return rows


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    rows = specimens()
    for row in rows:
        (OUT/(row['key']+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')
    selected = ['two-arguments','arguments-reversed','three-arguments','and','not-all','all-not',
                'binding-outer','binding-inner','function-reference','closed-quote','evaluation','quoted-apply','fold']
    cards = []
    for key in selected:
        row = next(r for r in rows if r['key']==key)
        square = to_svg(compile_statement(row['document']['statements'][0],vocabulary(),corners='square')['shapes'])
        cards.append('<section><h2>'+html.escape(row['label'])+'</h2><div class="drawing">'+row['statement_svg']+'</div><details><summary>直角の枝と比較する</summary><div class="drawing">'+square+'</div></details><a href="'+key+'.svg">定義・宣言を含む文書全体</a></section>')
    used = set()
    for _,_,d in cases():
        w=PublicWriter(vocabulary(),automatic=False);w.document(d)
        used.update(_shape_set(g['shapes']) for g in w.glyphs)
    atlas = []
    for index,(signature,g) in enumerate(catalogue(full_vocabulary()).items()):
        status='本文見本で使用' if signature in used else '字形単独の検査で使用'
        atlas.append('<div class="glyph">'+to_svg(g['shapes'])+'<small>'+status+'</small></div>')
    page = '''<!doctype html><html lang="ja"><meta charset="utf-8"><title>Noema 構造表記案</title>
<style>body{font:16px/1.8 "Yu Gothic",sans-serif;background:#f4f2eb;color:#243c3e;margin:40px auto;max-width:1300px;padding:0 28px}h1{font-size:30px}h2{font-size:18px}section{background:#fffdf8;margin:28px 0;padding:24px;border-radius:8px}.drawing{overflow:auto}.drawing svg{height:220px;min-width:100%;width:auto}a{color:#366367}p{max-width:900px}button{padding:8px 16px;margin-right:12px}.atlas{display:grid;grid-template-columns:repeat(6,1fr);gap:20px}.glyph svg{height:90px;width:100%}.glyph small{display:block;font-size:11px;text-align:center}</style>
<h1>Noema — 構文の枝を読む表記案</h1><p>未固定の試案です。円の語形と意味は既存辞書を使い、枝を構文に合わせて組みます。左から右へ親子をたどり、同じ親から出た枝は上から順に読みます。引用と束縛は公開文法の標識で区別します。</p>
<p>見ていただきたい点：分岐の種類による違い、文頭の反復、線の直角、余白、引用・束縛の長さ。各見本は短い独立例で、カント本文の完成版ではありません。</p>
<button onclick="document.querySelectorAll('.drawing svg').forEach(s=>s.style.height='220px')">一覧</button><button onclick="document.querySelectorAll('.drawing svg').forEach(s=>s.style.height='420px')">拡大</button>
'''+''.join(cards)+'<section><h2>現試案で許容する全字形</h2><p>共有375語の語形部品と文法標識を含む全42字形を図形から識別する検査を行っています。通常の本文見本に現れない字形も区別して表示します。旧kant-pageの不可視接続、共有引数の図形融合、円周外だけの斜線はこの試案では使いません。</p><div class="atlas">'+''.join(atlas)+'</div></section></html>\n'
    (OUT/'index.html').write_text(page,encoding='utf-8',newline='\n')
    # Preview is a faithful rasterization of the same primitives, not imagegen.
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc', 22)
    chosen = [next(r for r in rows if r['key']==key) for key in selected[:10]]
    canvas = Image.new('RGB',(1800,340*len(chosen)), '#fffdf8')
    draw = ImageDraw.Draw(canvas)
    for index,row in enumerate(chosen):
        draw.text((32,index*340+14),row['label'],fill='#243c3e',font=font)
        shapes = from_svg(row['statement_svg'])
        circles = [s for s in shapes if s['kind']=='circle']
        minx = min(c['x']-c['r'] for c in circles); maxx = max(c['x']+c['r'] for c in circles)
        miny = min(c['y']-c['r'] for c in circles); maxy = max(c['y']+c['r'] for c in circles)
        scale = min(1720/(maxx-minx),245/(maxy-miny),1.3)
        for s in shapes:
            def point(x,y): return (40+(x-minx)*scale,index*340+70+(y-miny)*scale)
            if s['kind']=='circle':
                x,y = point(s['x'],s['y']); r=s['r']*scale
                draw.ellipse((x-r,y-r,x+r,y+r),outline='#243c3e',width=2)
            else: draw.line((*point(s['x1'],s['y1']),*point(s['x2'],s['y2'])),fill='#243c3e',width=2)
    canvas.save(OUT/'preview.png')


def build_report():
    rows = specimens()
    pins = ['scripts/structural_circle.py','scripts/check_structural_circle.py','tests/test_structural_circle.py',
            'docs/structural-circle-draft-1.md','scripts/visible_syntax.py','scripts/visible_public_page.py',
            'scripts/visible_sharing.py','scripts/visible_syntax_geometry.py','scripts/visible_syntax_vocabulary.py',
            'scripts/visible_word_forms.py','scripts/visible_lexical_script.py','scripts/balanced_circle_script.py',
            'scripts/check_visible_syntax.py','noema/resources/visible-vocabulary-v1.json','noema/resources/visible-lexicon-v1.json']
    state=json.loads((ROOT/'data/work-state.json').read_text(encoding='utf-8'))
    old=json.loads((ROOT/state['progress_report']).read_text(encoding='utf-8'))
    index=json.loads((ROOT/state['review_index']).read_text(encoding='utf-8'))
    receipt_path='.noema-project/eighth-pin-snapshot-full-audit-v1-process.log'
    receipt=json.loads((ROOT/receipt_path).read_text(encoding='utf-8'))
    old_digest=hashlib.sha256(json.dumps(old,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()
    if receipt['result_sha256']!=old_digest or receipt['verified']!=state['progress_report'] or receipt['index']!=state['review_index']:
        raise ValueError('Saved full audit does not identify the selected baseline')
    selected=[state['review_index']]+[a[k] for a in index['works'].values() for k in ('document','meaning_basis','identifier_annotations') if a.get(k)]
    selected += [p for p in pins if p in old['source_sha256']]
    for p in selected:
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=old['source_sha256'][p]:
            raise ValueError('Selected existing evidence dependency changed: '+p)
    pins += selected+['data/work-state.json',state['progress_report']]
    return dict(schema='noema-structural-circle-evidence-1',status='draft-awaiting-visual-review',version=VERSION,
                public_glyph_inventory=len(catalogue(full_vocabulary())),grammar_operations=49,
                public_vocabulary_sha256=hashlib.sha256(json.dumps(full_vocabulary().document(),ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest(),
                preserved_baseline=dict(report=state['progress_report'],receipt_result_sha256=old_digest,
                                        checked_dependencies=sorted(set(selected)),scope='Selected unchanged inputs only; not a new whole-history audit'),
                cases=[{k:r[k] for k in ('key','glyphs','shapes','forks')} | dict(svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in rows],
                semantics='Exact normalized syntax only; no new source semantic judgments',
                geometry='Visible circle/segment SVG; no metadata or source AST supplied to decoder',
                limits=['Bounded documents, no page continuation yet','No raster OCR','Not a fixed visual standard','No full manuscript conversion'],
                source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in pins})


if __name__=='__main__':
    start=time.perf_counter();prepare()
    print(json.dumps(dict(cases=len(specimens()),seconds=time.perf_counter()-start,preview=str(OUT/'index.html'))))
