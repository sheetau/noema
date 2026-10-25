"""Visible-sharing contrasts and exact expanded-syntax evidence."""
from functools import lru_cache
import hashlib
from pathlib import Path

from noema.constructed import parse,format_graph
from scripts.check_visible_syntax import doc,assertion,num,logic,vocabulary
from scripts.visible_syntax import Writer
from scripts.visible_sharing import SharedWriter,MAX_EXPANDED_NODES
from scripts.visible_shared_page import compile_page,decode_page,to_svg,from_svg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/visible-sharing-v1'
SOURCE='examples/v016/visible-shared-argument-v1.noema'


def integrated_document():
    sequence=dict(kind='sequence',element='number',items=[num(1),num(2),num(3)])
    checks=[dict(kind='position',sequence=sequence,index=num(i),value=num(i+1)) for i in range(3)]
    body=logic('and',checks[0],logic('and',checks[1],checks[2]))
    return doc(assertion(body),assertion(logic('equal',dict(kind='quote',body=body),dict(kind='quote',body=body))))


@lru_cache(maxsize=1)
def specimen():
    document=integrated_document()
    ordinary=Writer(vocabulary()); ordinary.document(document)
    shared=SharedWriter(vocabulary()); shared.document(document)
    page=compile_page(document,max_width=3000.,paragraph_starts=(0,1))
    svg=to_svg(page['shapes'])
    if decode_page(from_svg(svg))!=dict(document=document,paragraph_starts=[0,1]):
        raise ValueError('Shared document differs after expansion')
    if len(shared.glyphs)>=len(ordinary.glyphs): raise ValueError('Automatic sharing did not reduce this specimen')
    return dict(document=document,page=page,svg=svg,ordinary_glyphs=len(ordinary.glyphs),
                shared_glyphs=len(shared.glyphs),sharing_binders=shared.share_count)


def prepare():
    from PIL import Image,ImageDraw
    from scripts.visible_page import vertical_bounds
    OUT.mkdir(parents=True,exist_ok=True)
    entry=specimen(); page=entry['page']
    (OUT/'shared-page.svg').write_text(entry['svg'],encoding='utf-8',newline='\n')
    lo,hi=vertical_bounds(page['shapes']); scale=.6
    canvas=Image.new('RGB',(round(page['width']*scale+40),round((hi-lo)*scale+40)),'white')
    draw=ImageDraw.Draw(canvas)
    for s in page['shapes']:
        if s['kind']=='circle':
            x,y,r=s['x']*scale+20,(s['y']-lo)*scale+20,s['r']*scale
            draw.ellipse((x-r,y-r,x+r,y+r),outline='#203438',width=2)
        else: draw.line((s['x1']*scale+20,(s['y1']-lo)*scale+20,s['x2']*scale+20,(s['y2']-lo)*scale+20),fill='#203438',width=2)
    canvas.save(OUT/'shared-page.png')


def build_report():
    entry=specimen()
    if parse((ROOT/SOURCE).read_text(encoding='utf-8'))!=entry['document']: raise ValueError('Native source differs')
    pins=[SOURCE,'docs/visible-sharing-v1.md','scripts/visible_sharing.py','scripts/visible_shared_page.py',
          'scripts/check_visible_sharing.py','tests/test_visible_sharing.py','scripts/check_visible_syntax.py',
          'scripts/visible_page.py','scripts/visible_syntax.py','scripts/visible_syntax_geometry.py',
          'scripts/visible_syntax_vocabulary.py','scripts/visible_word_forms.py','scripts/visible_lexical_script.py',
          'noema/resources/visible-vocabulary-v1.json','noema/resources/visible-lexicon-v1.json',
          'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py',
          'noema/guarded_ranked_semantics.py','noema/grammar.py','noema/semantics.py',
          'scripts/balanced_circle_script.py','scripts/branch_circle_script.py','scripts/circle_contact_script.py']
    return dict(schema='noema-visible-sharing-evidence-1',status='explicit_sharing_with_exact_syntax_expansion',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in pins},
        ordinary_glyphs=entry['ordinary_glyphs'],shared_glyphs=entry['shared_glyphs'],
        sharing_binders=entry['sharing_binders'],rows=entry['page']['rows'],
        svg_sha256=hashlib.sha256(entry['svg'].encode()).hexdigest(),
        expansion_node_limit=MAX_EXPANDED_NODES,original_normalized_document_restored=True,
        new_semantic_primitives=0,
        limits=['Explicit sharing does not decode historical implicit fusion',
                'Small repeated terms can be shorter without sharing',
                'No human reading or raster OCR result','No general semantic-coverage claim'])
