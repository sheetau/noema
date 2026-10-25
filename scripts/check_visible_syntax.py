"""Evidence for explicit visible syntax; separate from original paper review."""
from functools import lru_cache
import hashlib
from pathlib import Path

from noema.constructed import parse, format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_syntax import compile_document, decode_document, to_svg, from_svg
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_word_forms import Word, symbol

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/visible-syntax-v1'
SOURCE='examples/v016/visible-syntax-document-v1.noema'


@lru_cache(maxsize=1)
def vocabulary(): return Vocabulary()


def named(name): return symbol(Word('root',(name,)),vocabulary())


def call(name,*args): return dict(kind='call',symbol=named(name),arguments=list(args))


def variable(name): return dict(kind='variable',name=name)


def num(n,d=1): return dict(kind='number',numerator=n,denominator=d)


def logic(kind,*args): return dict(kind=kind,arguments=list(args))


def quant(kind,name,body,sort='individual'): return dict(kind=kind,variable=name,sort=sort,body=body)


def quote(body,rank=0): return dict(kind='quote',body=body,**({'rank':rank} if rank else {}))


def doc(*statements, roots=(), definitions=()):
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[vocabulary().declaration(n) for n in roots]+list(definitions),
        statements=list(statements)))


def assertion(body): return dict(kind='assert',body=body)


def integrated_document():
    name = symbol(Word('compound',('rain','home')),vocabulary())
    definition = dict(kind='definition',name=name,parameters=[],result='truth',body=call('rain',call('home')))
    return doc(assertion(dict(kind='call',symbol=name,arguments=[])),
        assertion(logic('equal',num(2,4),num(1,2))),
        assertion(logic('equal',quote(quote(num(1,2))),quote(quote(num(1,2))))),
        dict(kind='suppose',condition=call('rain',call('home')),statements=[dict(kind='ask',body=call('rain',call('home')))]),
        roots=('rain','home'),definitions=(definition,))


@lru_cache(maxsize=1)
def specimens():
    definitions = [
        ('above-bird-tree',doc(assertion(call('above',call('birdone'),call('treeone'))),roots=('above','birdone','treeone'))),
        ('above-aki-nao',doc(assertion(call('above',call('aki'),call('nao'))),roots=('above','aki','nao'))),
        ('above-tree-bird',doc(assertion(call('above',call('treeone'),call('birdone'))),roots=('above','birdone','treeone'))),
        ('not-all',doc(assertion(logic('not',quant('forall','x',call('rain',variable('x'))))),roots=('rain',))),
        ('all-not',doc(assertion(quant('forall','x',logic('not',call('rain',variable('x'))))),roots=('rain',))),
        ('standalone-document',integrated_document()),
    ]
    result=[]
    for label,document in definitions:
        compiled=compile_document(document,vocabulary())
        svg=to_svg(compiled['shapes'])
        if decode_document(from_svg(svg),vocabulary())!=document: raise ValueError('Visible document differs')
        result.append(dict(label=label,document=document,compiled=compiled,svg=svg))
    return result


def semantic_contrasts():
    rows=[]
    for at_a,at_b in ((False,False),(False,True),(True,False),(True,True)):
        values=[]
        for entry in specimens()[3:5]:
            result=evaluate_document(entry['document'],individuals=('a','b'),situations=('now',),
                                     primitives={named('rain'):lambda x:at_a if x=='a' else at_b})
            values.append(result[0]['value'])
        expected=[not(at_a and at_b),not at_a and not at_b]
        if values!=expected: raise ValueError('Scope contrast lost')
        rows.append(dict(rain_a=at_a,rain_b=at_b,not_all=values[0],all_not=values[1]))
    return rows


def prepare():
    from PIL import Image,ImageDraw
    OUT.mkdir(parents=True,exist_ok=True)
    entries=specimens()
    for entry in entries: (OUT/(entry['label']+'.svg')).write_text(entry['svg'],encoding='utf-8',newline='\n')
    # A readable crop of the actual final statement, with its visible assert
    # marker and roots. Standalone source SVGs retain the entire document.
    from scripts.visible_syntax import Writer
    from scripts.visible_syntax_geometry import render
    previews=[]
    for entry in entries[:5]:
        w=Writer(vocabulary()); w.statement(entry['document']['statements'][0])
        previews.append((entry['label'],render(w.glyphs)))
    width=round(max(v['width'] for _,v in previews)*1.5+60)
    canvas=Image.new('RGB',(width,len(previews)*210),'white'); draw=ImageDraw.Draw(canvas)
    for row,(label,compiled) in enumerate(previews):
        draw.text((20,row*210+8),label,fill='#203438')
        for s in compiled['shapes']:
            if s['kind']=='circle':
                x,y,r=s['x']*1.5+20,s['y']*1.5+row*210+60,s['r']*1.5
                draw.ellipse((x-r,y-r,x+r,y+r),outline='#203438',width=3)
            else: draw.line((s['x1']*1.5+20,s['y1']*1.5+row*210+60,s['x2']*1.5+20,s['y2']*1.5+row*210+60),fill='#203438',width=3)
    canvas.save(OUT/'syntax-contrasts.png')


def build_report():
    source=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    if source!=integrated_document() or parse(format_graph(source))!=source: raise ValueError('Integrated source differs')
    pins=[SOURCE,'docs/visible-syntax-v1.md','scripts/visible_syntax.py','scripts/visible_syntax_geometry.py',
          'scripts/visible_syntax_vocabulary.py','scripts/check_visible_syntax.py','tests/test_visible_syntax.py',
          'scripts/visible_word_forms.py','scripts/visible_lexical_script.py',
          'noema/resources/visible-vocabulary-v1.json','noema/resources/visible-lexicon-v1.json',
          'scripts/balanced_circle_script.py','scripts/branch_circle_script.py','scripts/circle_contact_script.py',
          'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py',
          'noema/guarded_ranked_semantics.py','noema/semantics.py','noema/grammar.py','noema/script.py']
    return dict(schema='noema-visible-syntax-evidence-1',status='single_line_native_document_decoding',
        specimen_count=len(specimens()),specimens=[dict(label=e['label'],
        visible_primitives=len(e['compiled']['shapes']),width=e['compiled']['width'],
        svg_sha256=hashlib.sha256(e['svg'].encode()).hexdigest()) for e in specimens()],
        scope_models=semantic_contrasts(),
        runtime_bounds=dict(visible_primitives=4096,glyphs=768,natural_bits=256,nesting=128),
        input_contract='Visible circles and lines plus shared grammar/vocabulary; no document sidecar',
        limits=['No raster OCR or human reading result','No old paper page decoding claim',
                'Line/paragraph continuation and shared-argument fusion remain unverified',
                'Explicit public roots cover examples, not the complete semantic vocabulary',
                'Finite model diagnostics do not prove equivalence over every interpretation'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in pins})
