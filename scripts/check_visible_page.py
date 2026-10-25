"""Evidence for visible continuation, paragraphs and immutable syntax."""
from functools import lru_cache
import hashlib
from pathlib import Path

from scripts.visible_page import compile_page,decode_page,to_svg,from_svg,MAX_ROWS
from scripts.check_visible_syntax import integrated_document,vocabulary

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/visible-page-v1'


@lru_cache(maxsize=1)
def specimens():
    doc=integrated_document()
    result=[]
    for width,paragraphs in ((1800.,()),(2400.,(0,2)),(3600.,(0,1,2,3))):
        page=compile_page(doc,vocabulary(),max_width=width,paragraph_starts=paragraphs)
        svg=to_svg(page['shapes'])
        expected=dict(document=doc,paragraph_starts=list(paragraphs))
        if decode_page(from_svg(svg),vocabulary())!=expected: raise ValueError('Page round trip differs')
        result.append(dict(label='width-'+str(int(width)),page=page,svg=svg,
                           paragraphs=list(paragraphs),max_width=width))
    return result


def prepare():
    from PIL import Image,ImageDraw
    OUT.mkdir(parents=True,exist_ok=True)
    for entry in specimens():
        (OUT/(entry['label']+'.svg')).write_text(entry['svg'],encoding='utf-8',newline='\n')
    entry=specimens()[1]
    page=entry['page']; scale=.75
    # A raster preview of the same plain SVG primitives. No added row IDs,
    # Latin source, AST or paragraph annotations are present on the page.
    from scripts.visible_page import vertical_bounds
    low,high=vertical_bounds(page['shapes'])
    canvas=Image.new('RGB',(round(page['width']*scale+40),round((high-low)*scale+40)),'white')
    draw=ImageDraw.Draw(canvas)
    for s in page['shapes']:
        if s['kind']=='circle':
            x,y,r=s['x']*scale+20,(s['y']-low)*scale+20,s['r']*scale
            draw.ellipse((x-r,y-r,x+r,y+r),outline='#203438',width=2)
        else:
            draw.line((s['x1']*scale+20,(s['y1']-low)*scale+20,
                       s['x2']*scale+20,(s['y2']-low)*scale+20),fill='#203438',width=2)
    canvas.save(OUT/'standalone-page.png')


def build_report():
    pins=['scripts/visible_page.py','scripts/check_visible_page.py','tests/test_visible_page.py',
          'docs/visible-page-v1.md','scripts/visible_syntax.py','scripts/visible_syntax_geometry.py',
          'scripts/visible_syntax_vocabulary.py','scripts/visible_word_forms.py','scripts/visible_lexical_script.py',
          'scripts/check_visible_syntax.py','noema/resources/visible-vocabulary-v1.json',
          'noema/resources/visible-lexicon-v1.json','noema/constructed_discourse.py','noema/constructed.py',
          'noema/grammar.py','noema/semantics.py','scripts/balanced_circle_script.py',
          'scripts/branch_circle_script.py','scripts/circle_contact_script.py',
          'examples/v016/visible-syntax-document-v1.noema']
    return dict(schema='noema-visible-page-evidence-1',status='visible_rows_and_paragraphs',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in pins},
        cases=[dict(label=e['label'],max_width=e['max_width'],rows=e['page']['rows'],
                    visible_primitives=len(e['page']['shapes']),paragraph_starts=e['paragraphs'],
                    svg_sha256=hashlib.sha256(e['svg'].encode()).hexdigest()) for e in specimens()],
        native_document_unchanged=True,maximum_rows=MAX_ROWS,
        normalization='Uniform scale, translation, row spacing and indent, rail placement and segment subdivision',
        rejection_contract=['Missing/repeated/reordered rows','Missing start or final row',
            'Broken keyword, word name or number','Paragraph inside a definition or nested scope',
            'Clipping, hidden SVG attributes, disconnected or cross-row ink'],
        limits=['No human reading or raster OCR result','No claim to decode frozen historical pages',
                'No shared-argument fusion yet','Row numbering is not an integrity signature'])
