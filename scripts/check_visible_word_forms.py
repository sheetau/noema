"""Native naming and geometry-only word spelling evidence; not a full document decoder."""
from dataclasses import asdict
from functools import lru_cache
import hashlib
from itertools import product
import json
from pathlib import Path

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from scripts.visible_word_forms import (
    Word, symbol, compile_word, decode_word, to_svg, from_svg, MAX_PARTS,
)
from scripts.visible_lexical_script import STROKE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/visible-word-forms-v1'
SOURCE='examples/v016/visible-word-definitions-v1.noema'


def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def specimens():
    words=[Word('compound',('rain','home')),Word('compound',('home','rain')),
           Word('proper',('rain','home')),Word('proper',('home','town')),
           Word('compound',('home','town','rain','home'))]
    result=[]
    for word in words:
        compiled=compile_word(word)
        svg=to_svg(compiled['shapes'])
        recovered=decode_word(from_svg(svg))
        if recovered!=word:raise ValueError('Visible spelling differs')
        result.append(dict(word=word,compiled=compiled,svg=svg))
    return result


def prepare():
    from PIL import Image, ImageDraw
    OUT.mkdir(parents=True,exist_ok=True)
    scale,margin,row_height=2.,30,260
    entries=specimens()
    width=max(round(e['compiled']['width']*scale+margin*2) for e in entries)
    canvas=Image.new('RGB',(width,len(entries)*row_height),'white')
    draw=ImageDraw.Draw(canvas)
    for row,entry in enumerate(entries):
        name=symbol(entry['word'])
        (OUT/(name+'.svg')).write_text(entry['svg'],encoding='utf-8',newline='\n')
        # Labels identify specimens for inspection; the standalone SVGs contain
        # visible ink only, and those are what the decoder reads.
        draw.text((margin,row*row_height+12),
                  entry['word'].kind+': '+' + '.join(entry['word'].parts),fill='#203438')
        for s in entry['compiled']['shapes']:
            if s['kind']=='circle':
                x,y,r=s['x']*scale+margin,s['y']*scale+row*row_height+75,s['r']*scale
                draw.ellipse((x-r,y-r,x+r,y+r),outline='#203438',width=round(STROKE*scale))
            else:
                draw.line((s['x1']*scale+margin,s['y1']*scale+row*row_height+75,
                           s['x2']*scale+margin,s['y2']*scale+row*row_height+75),
                          fill='#203438',width=round(STROKE*scale))
    canvas.save(OUT/'word-forms.png')


def build_report():
    rows=[]
    for entry in specimens():
        word=entry['word']
        variants=0
        for branch,rail in product((False,True),(0,2)):
            shapes=compile_word(word,branch=branch,first_rail=rail)['shapes']
            if decode_word(shapes)!=word:raise ValueError('Layout changes word')
            variants+=1
        rows.append(dict(word=asdict(word),native_symbol=symbol(word),
                         svg_sha256=hashlib.sha256(entry['svg'].encode()).hexdigest(),
                         visible_primitives=len(entry['compiled']['shapes']),
                         readable_layouts=variants))
    long_word=Word('compound',('home','town','rain')*(MAX_PARTS//3))
    if decode_word(compile_word(long_word)['shapes'])!=long_word:raise ValueError('Long name differs')
    doc=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    if parse(format_graph(doc))!=doc:raise ValueError('Native document round trip differs')
    home,town,rain=[symbol(Word('root',(s,))) for s in ('home','town','rain')]
    models=[]
    for at_home,at_town in product((False,True),repeat=2):
        result=evaluate_document(doc,individuals=('home','town'),situations=('now',),primitives={
            home:lambda:'home',town:lambda:'town',
            rain:lambda who:at_home if who=='home' else at_town})
        values=[row['value'] for row in result]
        if values!=[True,at_home,at_town]:raise ValueError('Naming added or lost a property')
        models.append(dict(rain_home=at_home,rain_town=at_town,statement_values=values))
    pins=[SOURCE,'docs/visible-word-formation-v1.md','scripts/visible_word_forms.py',
          'scripts/check_visible_word_forms.py','tests/test_visible_word_forms.py',
          'scripts/visible_lexical_script.py','noema/resources/visible-lexicon-v1.json',
          'noema/constructed_discourse.py','noema/constructed_semantics.py',
          'noema/guarded_ranked_semantics.py','noema/constructed.py','noema/semantics.py',
          'noema/script.py','scripts/balanced_circle_script.py','scripts/branch_circle_script.py',
          'scripts/circle_contact_script.py']
    return dict(schema='noema-visible-word-formation-evidence-1',
                status='compositional_spellings_and_native_definitions_connected',
                new_primitive_count=0,shared_primitives=3,native_definitions=4,
                syntax_component_count='arbitrary finite sequence',runtime_component_limit=MAX_PARTS,
                maximum_runtime_length_decoded=True,cases=rows,model_contrasts=models,
                whole_definition_document_visually_decodable=False,
                source_sha256={p:digest(p) for p in pins},
                limits=[
                    'Spelling components provide naming cues; exact meaning is supplied by native definitions.',
                    'Proper names here name an already designated individual; general referent introduction remains open.',
                    'Only word envelopes are visibly decoded; definition bodies/types/statements still use native text.',
                    'Finite model contrasts test naming behavior, not new natural-language semantic equivalence.',
                    'General sentence boundaries, scope, quotations and independent human reading remain open.',
                ])
