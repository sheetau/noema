"""Public definitions imported visibly, with no new semantic primitives."""
from copy import deepcopy
from functools import lru_cache
import hashlib
from pathlib import Path

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_library import compile_page,decode_page,to_svg,from_svg
from scripts.shared_modality import ROOT,composed,call,v,op,quant

OUT=ROOT/'output/visible-library-v1'
SOURCE='examples/v016/visible-shared-library-v1.noema'


@lru_cache(maxsize=1)
def vocabulary(): return DefinedVocabulary()


def boolean(value):
    a=dict(kind='number',numerator=0,denominator=1)
    return op('equal',a,dict(kind='number',numerator=0 if value else 1,denominator=1))


def function(parameters,body):
    return dict(kind='lambda',parameters=[dict(name=n,sort=t) for n,t in parameters],body=body)


def candidate_examples():
    d=deepcopy(composed())
    content=dict(kind='content',variable='world',body=op('equal',v('world'),v('context')))
    select=function([('p','content'),('c','situation'),('w','situation')],op('equal',v('w'),v('c')))
    empty=function([('p','content'),('c','situation'),('w','situation')],boolean(False))
    for name,selector,positive in (('candidatepossible',select,True),('candidatenecessary',select,True),
                                   ('candidateexists',empty,False),('candidateexcluded',empty,False)):
        body=call(name,content,v('context'),selector)
        d['statements'].append(dict(kind='assert',body=quant('forall','context',body if positive else op('not',body))))
    return normalize_document(d)


def ability_examples():
    d=deepcopy(composed())
    goal=dict(kind='content',variable='world',body=boolean(True))
    unavailable=function([('a','individual'),('m','individual'),('c','situation')],boolean(False))
    available=function([('a','individual'),('m','individual'),('c','situation')],boolean(True))
    outcomes=function([('a','individual'),('m','individual'),('c','situation'),('w','situation')],boolean(True))
    selected=function([('a','individual'),('m','individual'),('c','situation'),('w','situation')],boolean(False))
    for name,feasible,positive in (('methodpossible',unavailable,False),('methodguaranteed',available,True),
                                  ('assessedability',available,False),('assessedinability',available,False)):
        args=[v('person'),goal,v('context'),feasible,outcomes]
        if name in ('assessedability','assessedinability'):args.append(selected)
        body=call(name,*args)
        scoped=quant('forall','context',body if positive else op('not',body))
        d['statements'].append(dict(kind='assert',body=dict(kind='forall',variable='person',sort='individual',body=scoped)))
    return normalize_document(d)


@lru_cache(maxsize=1)
def specimens():
    result=[]
    for label,native in (('dictionary',composed()),('candidates',candidate_examples()),('ability',ability_examples())):
        encoded=vocabulary().encode(native)
        page=compile_page(encoded,vocabulary(),max_width=3000.)
        svg=to_svg(page['shapes'])
        recovered=decode_page(from_svg(svg))['document']
        if recovered!=encoded or vocabulary().decode_names(recovered)!=native:raise ValueError('Public definitions changed')
        values=evaluate_document(recovered,individuals=('a','b'),situations=('now','later'),primitives={})
        if not all(r['value'] for r in values): raise ValueError('Visible shared statement differs')
        result.append(dict(label=label,native=native,encoded=encoded,page=page,svg=svg,values=[r['value'] for r in values]))
    return result


def prepare():
    from PIL import Image,ImageDraw
    from scripts.visible_lexical_script import _glyph
    OUT.mkdir(parents=True,exist_ok=True)
    for row in specimens(): (OUT/(row['label']+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')
    # All 14 learned forms, labeled for study. Standalone documents carry no
    # labels or dictionary sidecars; their visible edition selects this table.
    names=list(vocabulary().document()['definitions'])
    canvas=Image.new('RGB',(1080,7*125),'white'); draw=ImageDraw.Draw(canvas)
    for i,name in enumerate(names):
        col,row=i//7,i%7
        glyph=_glyph(vocabulary().resolve(name)[1]['form'],55.,35.)
        dx,dy=col*540,row*125+20
        for s in glyph['shapes']:
            if s['kind']=='circle':
                x,y,r=s['x']+dx,s['y']+dy,s['r']
                draw.ellipse((x-r,y-r,x+r,y+r),outline='#203438',width=2)
            else: draw.line((s['x1']+dx,s['y1']+dy,s['x2']+dx,s['y2']+dy),fill='#203438',width=2)
        draw.text((dx+105,dy+28),name,fill='#203438')
    canvas.save(OUT/'defined-word-forms.png')


def build_report():
    if parse((ROOT/SOURCE).read_text(encoding='utf-8'))!=candidate_examples(): raise ValueError('Published example differs')
    paths=[SOURCE,'docs/visible-defined-vocabulary-v1.md','noema/resources/visible-defined-vocabulary-v1.json',
        'examples/v016/shared-modality-v1.noema','data/shared-modality-basis-v1.json','scripts/visible_defined_vocabulary.py',
        'scripts/visible_library.py','scripts/check_visible_library.py','tests/test_visible_library.py',
        'scripts/shared_modality.py','scripts/visible_shared_page.py','scripts/visible_sharing.py','scripts/visible_page.py',
        'scripts/visible_syntax.py','scripts/visible_syntax_vocabulary.py','scripts/visible_syntax_geometry.py',
        'scripts/visible_lexical_script.py','scripts/visible_word_forms.py',
        'noema/resources/visible-lexicon-v1.json','noema/resources/visible-vocabulary-v1.json',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py',
        'noema/grammar.py','noema/semantics.py','scripts/balanced_circle_script.py','scripts/branch_circle_script.py',
        'scripts/circle_contact_script.py']
    return dict(schema='noema-visible-library-evidence-1',status='shared_definitions_visibly_imported',
        edition=2,preserved_primitive_words=16,shared_defined_words=14,new_semantic_primitives=0,
        cases=[dict(label=e['label'],rows=e['page']['rows'],visible_primitives=len(e['page']['shapes']),
                    statement_values=e['values'],svg_sha256=hashlib.sha256(e['svg'].encode()).hexdigest()) for e in specimens()],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        limits=['Shared definitions are learned public vocabulary, not document-specific hidden data',
                'No human reading or raster OCR result','Other semantic domains and complete paper rendering remain unfinished'])
