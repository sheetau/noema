"""Horizontal writing specimens; compare appearance with the saved Kant page."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,html
from noema.constructed_discourse import normalize_document
from scripts.check_structural_circle import cases,full_vocabulary
from scripts.check_visible_syntax import vocabulary
from scripts.flow_circle import compile_page,decode_page,to_svg,from_svg,FlowWriter,render_line,flow_packet
from scripts.flow_circle import compile_excerpt,decode_excerpt,compile_pages,decode_pages,alphabet,VERSION
from noema.constructed import parse
from scripts.visible_lexical_script import _shape_set,_translate

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/flow-circle-draft-1'
KANT='examples/v016/kant-first-paragraph-visible-v1.noema'


@lru_cache(maxsize=1)
def kant_excerpt():
    original=parse((ROOT/KANT).read_text(encoding='utf-8'))
    drawing=compile_excerpt(original['statements'],full_vocabulary(),line_atoms=32)
    svg=to_svg(drawing['shapes'])
    recovered=decode_excerpt(from_svg(svg),full_vocabulary())
    # Reading uses only geometry and public glyphs. The unchanged declarations
    # are used afterward for native typing/canonicalization, not to guess ink.
    checked=normalize_document(dict(original,statements=recovered))
    if checked!=original:raise ValueError('Existing Kant excerpt changed')
    return dict(drawing=drawing,svg=svg,statements=len(recovered))


def sample_document():
    selected=cases()[:8]+cases()[9:13]
    declarations={}
    statements=[]
    for _,_,d in selected:
        for declaration in d['declarations']:
            old=declarations.setdefault(declaration['name'],declaration)
            if old!=declaration:raise ValueError('Sample declaration conflict')
        statements+=d['statements']
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=list(declarations.values()),statements=statements))


@lru_cache(maxsize=40)
def specimen(index):
    key,label,document=cases()[index]
    drawing=compile_page(document,line_atoms=11)
    svg=to_svg(drawing['shapes'])
    if decode_page(from_svg(svg))!=document:raise ValueError('Flow contrast differs: '+key)
    return dict(key=key,label=label,document=document,drawing=drawing,svg=svg)


def used_shapes():
    used=set()
    for _,_,d in cases():
        w=FlowWriter(vocabulary());w.document(d)
        used.update(_shape_set(g['shapes']) for g in w.glyphs)
    return used


@lru_cache(maxsize=1)
def paged_specimen():
    document=cases()[8][2]
    pages=compile_pages(document,line_atoms=7,rows_per_page=2)
    svgs=[to_svg(_translate(p['shapes'],i*18,i*-23,1+i/8)) for i,p in enumerate(pages)]
    if decode_pages([from_svg(svg) for svg in svgs])!=document:raise ValueError('Paged flow document differs')
    return svgs


def raster(shapes,path,width=1600):
    from PIL import Image,ImageDraw
    circles=[s for s in shapes if s['kind']=='circle']
    minx=min(s['x']-s['r'] for s in circles);maxx=max(s['x']+s['r'] for s in circles)
    miny=min(s['y']-s['r'] for s in circles);maxy=max(s['y']+s['r'] for s in circles)
    scale=(width-180)/(maxx-minx);height=round((maxy-miny)*scale+180)
    ss=2;im=Image.new('RGB',(width*ss,height*ss),'#fffffe');draw=ImageDraw.Draw(im)
    def p(x,y):return ((90+(x-minx)*scale)*ss,(90+(y-miny)*scale)*ss)
    for s in shapes:
        if s['kind']=='circle':
            x,y=p(s['x'],s['y']);r=s['r']*scale*ss
            draw.ellipse((x-r,y-r,x+r,y+r),outline='#203438',width=max(1,round(1.9*scale*ss)))
        else:draw.line((*p(s['x1'],s['y1']),*p(s['x2'],s['y2'])),fill='#203438',width=max(1,round(1.9*scale*ss)))
    im.resize((width,height),Image.Resampling.LANCZOS).save(path)


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    d=sample_document();drawing=compile_page(d,line_atoms=32)
    svg=to_svg(drawing['shapes'])
    if decode_page(from_svg(svg))!=d:raise ValueError('Flow sample differs')
    (OUT/'sample.svg').write_text(svg,encoding='utf-8',newline='\n')
    raster(drawing['shapes'],OUT/'sample.png')
    kant=kant_excerpt()
    (OUT/'kant-excerpt.svg').write_text(kant['svg'],encoding='utf-8',newline='\n')
    raster(kant['drawing']['shapes'],OUT/'kant-excerpt.png')
    cards=[]
    for index in range(8):
        sample=specimen(index);key,label,document=(sample[k] for k in ('key','label','document'))
        w=FlowWriter(vocabulary(),automatic=False);w.statement(document['statements'][0])
        # A display excerpt; the complete document below retains declarations.
        shown=render_line(flow_packet(w.glyphs,0,final=True))
        (OUT/(key+'.svg')).write_text(sample['svg'],encoding='utf-8',newline='\n')
        cards.append('<section><h2>'+html.escape(label)+'</h2><div class="line">'+to_svg(shown['shapes'])+'</div><a href="'+key+'.svg">宣言を含む文書</a></section>')
    used=used_shapes();atlas=[]
    for signature,(g,_) in alphabet(full_vocabulary()).items():
        status='短文群に使用' if signature in used else '短文群には未使用（単独復号を検査）'
        atlas.append('<div class="glyph">'+to_svg(g['shapes'])+'<small>'+status+'</small></div>')
    page_links=[]
    for i,svg in enumerate(paged_specimen()):
        name='continuation-'+str(i+1)+'.svg'
        (OUT/name).write_text(svg,encoding='utf-8',newline='\n')
        page_links.append('<a href="'+name+'">'+str(i+1)+'頁</a>')
    page='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>Noema 横書き表記案</title>
<style>body{font:16px/1.8 "Yu Gothic",sans-serif;max-width:1450px;margin:36px auto;padding:0 26px;color:#203438;background:#f7f6f1}.compare{display:grid;grid-template-columns:1fr 1fr;gap:24px}.compare img{width:100%;height:auto;display:block;background:white}h1{font-size:26px}h2{font-size:18px}section{padding:20px;background:white;margin:25px 0}.line{overflow:auto}.line svg{height:110px;min-width:100%;width:auto}.atlas{display:grid;grid-template-columns:repeat(6,1fr);gap:24px}.glyph svg{height:80px;width:100%}.glyph small{display:block;font-size:11px}a{color:#35656b}p{max-width:980px}</style>
<h1>Noema — kant-pageの横書きに近づける案</h1><p>構文木を紙面に広げる案は不採用にしました。横の読順を基本とし、短い分岐・上下の揺れ・円の接触を行内に収めています。文法の二つ組は、長い線と短い線で区別できる合字にしました。語の綴りと意味は維持しています。未固定の試案です。</p>
<p>左は保存済みのkant-page、右は短い独立例をまとめた復号可能な見本です。内容と文字数は異なり、カント全文を新方式へ変換した比較ではありません。まず行の流れ、密度、円の大きさ、短い枝、文頭の反復を見比べてください。</p>
<div class="compare"><div><h2>基準：kant-page</h2><img src="../kant-page-script-v3/kant-page.png"></div><div><h2>横書きの試案</h2><a href="sample.svg"><img src="sample.png"></a></div></div>
<h2>既存のカント稿を同じ規則で書いた抜粋</h2><p>既存の円文字稿から、題名・著者・識別注記・冒頭段落への接続を表す4主張をそのまま描きました。図形から同じ構文へ戻ることを確認しています。参照される113宣言はこの抜粋画像には含まず、全文の自立した最終版ではありません。</p><a href="kant-excerpt.svg"><img src="kant-excerpt.png" style="width:100%"></a>
<p>読み順は左から右、同じ列の二字は上から下です。枝はこの読順を保つ字の配置であり、構文木を縦に描くものではありません。意味による違いは、語形・文法合字・引数列に現れます。現在は数値・変数参照の反復、二円の文法合字の密度、短い二叉の頻度が残る比較点です。</p>
<h2>意味の区別を保つ短文</h2>'''+''.join(cards)+'<section><h2>頁をまたぐ場合</h2><p>引用と束縛を含む同じ文書を、確認用に2行ごとに改頁しています。行番号は頁をまたいで連続し、最後だけ終了標識になります。頁ごとの拡大率と位置も変えて復号しています。</p>'+' / '.join(page_links)+'</section><section><h2>許容字形と使用状況</h2><p>公開辞書の語形部品、49の文法合字、数と境界、行番号・継続の全字形です。未使用はこの短文群についての表示です。旧kant-pageの不可視接続・文書別番号による語形・共有引数の融合・円周外だけの斜線は採用していません。</p><div class="atlas">'+''.join(atlas)+'</div></section></html>\n'
    (OUT/'index.html').write_text(page,encoding='utf-8',newline='\n')
    print(json.dumps(dict(rows=drawing['rows'],atoms=drawing['atoms'],forks=drawing['forks'],output=str(OUT))))


def build_report():
    rows=[specimen(i) for i in range(len(cases()))];v=full_vocabulary();kant=kant_excerpt()
    pins=['scripts/flow_circle.py','scripts/check_flow_circle.py','tests/test_flow_circle.py',
          'docs/flow-circle-draft-1.md','scripts/structural_circle.py','scripts/check_structural_circle.py',
          'scripts/check_visible_syntax.py','scripts/balanced_circle_script.py','scripts/circle_contact_script.py',
          'scripts/branch_circle_script.py',KANT]
    pins += ['scripts/visible_'+name+'.py' for name in ('syntax','syntax_vocabulary','syntax_geometry',
        'word_forms','lexical_script','public_page','sharing','page','shared_page')]
    extensions=('defined','compound','scope','quantity','selection','generality','speech',
                'conversation','deadline','evidence','senses')
    pins += ['scripts/visible_'+name+'_vocabulary.py' for name in extensions]
    manifests=['noema/resources/visible-'+name+'-v1.json' for name in
               ('lexicon','vocabulary',*(name+'-vocabulary' for name in extensions))]
    # Manifest references identify the actual public libraries and meanings;
    # no unrelated manuscript inventory is walked.
    def references(value):
        if isinstance(value,str):
            if value.startswith(('examples/','data/','noema/')) and value.endswith(('.json','.noema')):
                if not (ROOT/value).is_file():raise ValueError('Missing public vocabulary input: '+value)
                pins.append(value)
        elif isinstance(value,dict):
            for child in value.values():references(child)
        elif isinstance(value,list):
            for child in value:references(child)
    for path in manifests:
        references(json.loads((ROOT/path).read_text(encoding='utf-8')))
    pins+=manifests+['scripts/shared_modality.py','scripts/shared_selection.py',
                     'scripts/shared_generality.py','scripts/shared_speech.py']
    earlier_path='reports/structural-circle-draft-v1.json'
    earlier=json.loads((ROOT/earlier_path).read_text(encoding='utf-8'))
    vocabulary_hash=hashlib.sha256(json.dumps(v.document(),ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()
    if earlier['public_vocabulary_sha256']!=vocabulary_hash:
        raise ValueError('Public vocabulary meanings or references changed from the preceding candidate')
    pins.append(earlier_path)
    state=json.loads((ROOT/'data/work-state.json').read_text(encoding='utf-8'))
    old=json.loads((ROOT/state['progress_report']).read_text(encoding='utf-8'))
    index=json.loads((ROOT/state['review_index']).read_text(encoding='utf-8'))
    receipt_path='.noema-project/eighth-pin-snapshot-full-audit-v1-process.log'
    receipt=json.loads((ROOT/receipt_path).read_text(encoding='utf-8'))
    old_digest=hashlib.sha256(json.dumps(old,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()
    if receipt['result_sha256']!=old_digest or receipt['verified']!=state['progress_report'] or receipt['index']!=state['review_index']:
        raise ValueError('Saved full audit does not identify the selected baseline')
    selected=[state['review_index']]+[a[k] for a in index['works'].values() for k in ('document','meaning_basis','identifier_annotations') if a.get(k)]
    selected += [p for p in old['source_sha256'] if p.startswith(('scripts/visible_','scripts/shared_',
        'noema/resources/visible-','examples/v016/shared-','data/shared-'))]
    selected += [p for p in pins if p in old['source_sha256']]
    for p in selected:
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=old['source_sha256'][p]:
            raise ValueError('Selected existing evidence dependency changed: '+p)
    pins+=selected+['data/work-state.json',state['progress_report']]
    return dict(schema='noema-flow-circle-evidence-1',status='draft-awaiting-visual-review',version=VERSION,
        grammar_operations=49,public_glyph_inventory=len(alphabet(v)),
        public_vocabulary_sha256=vocabulary_hash,
        public_vocabulary_unchanged_from=earlier_path,
        preserved_baseline=dict(report=state['progress_report'],receipt_result_sha256=old_digest,
            checked_dependencies=sorted(set(selected)),scope='Unchanged selected inputs; saved whole-history audit reused, not rerun'),
        cases=[dict(key=r['key'],**{k:r['drawing'][k] for k in ('rows','atoms','forks')},
            svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in rows],
        kant_excerpt=dict(source=KANT,statements=kant['statements'],rows=kant['drawing']['rows'],
            svg_sha256=hashlib.sha256(kant['svg'].encode()).hexdigest(),
            scope='Four unchanged statements; declarations retained externally for post-decoding normalization'),
        page_continuation=dict(pages=len(paged_specimen()),rows_per_page=2,line_atoms=7,
            svg_sha256=[hashlib.sha256(svg.encode()).hexdigest() for svg in paged_specimen()]),
        geometry='Visible circles and segments only; x order, top-before-bottom ties, public prefix grammar',
        semantics='Exact normalized syntax plus unchanged meanings/references; no new source judgments',
        limits=['Bounded pages with visible continuous row numbers','No raster OCR or hand-drawn noise tolerance',
            'Automatic sharing disabled; explicit share/reuse can be decoded','No full manuscript conversion',
            'Finite contrasts are not an exhaustive proof','No visual freeze without user review'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(pins))})


if __name__=='__main__':prepare()
