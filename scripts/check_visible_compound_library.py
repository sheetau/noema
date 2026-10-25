"""Evidence for public compounds: visible geometry and native meanings."""
from functools import lru_cache
import hashlib
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_compound_vocabulary import CompoundVocabulary,ROOT,MANIFEST,MODULES
from scripts.visible_public_page import PublicWriter,compile_page,decode_page,decode_document,to_svg,from_svg
from scripts.visible_syntax_geometry import render
from scripts.shared_modality import v,call,op
from scripts.shared_reference import truth,lam,content
from scripts.shared_time import q

OUT=ROOT/'output/visible-compound-library-v1'
SOURCE='examples/v016/visible-common-vocabulary-v1.noema'


@lru_cache(maxsize=1)
def vocabulary():return CompoundVocabulary()
def doc(names,statements):
    document=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(names),statements=[])))
    document['statements']=statements
    return normalize_document(document)


def temporal_example():
    H=lam([('p','situation')],op('or',op('equal',v('p'),v('early')),op('equal',v('p'),v('late'))))
    order=lam([('a','situation'),('b','situation')],op('and',op('equal',v('a'),v('early')),op('equal',v('b'),v('late'))))
    trace=lam([('e','individual'),('p','situation')],op('and',op('equal',v('e'),v('person')),
        op('or',op('equal',v('p'),v('early')),op('equal',v('p'),v('late')))))
    culmination=lam([('e','individual'),('p','situation')],truth(False))
    body=call('eventunderway',H,order,v('person'),trace,v('late'),culmination)
    body=op('implies',op('not',op('equal',v('early'),v('late'))),body)
    body=q('forall','person','individual',q('forall','early','situation',q('forall','late','situation',body)))
    return doc(['eventunderway'],[dict(kind='assert',body=body)])


def reference_example():
    candidates=lam([('x','individual'),('w','situation')],op('equal',v('x'),v('person')))
    property=lam([('x','individual'),('w','situation')],truth(False))
    pair=call('definitestatement',candidates,property)
    body=op('and',call('licensednegative',pair,v('scene')),op('not',call('licensedpositive',pair,v('scene'))))
    body=q('forall','person','individual',q('forall','scene','situation',body))
    return doc(['definitestatement','licensednegative','licensedpositive'],[dict(kind='assert',body=body)])


def readings_example():
    # Infinite number quantification cannot be evaluated by the finite engine,
    # but its closed message description can be retained and compared.
    body=q('forall','n','number',op('equal',v('n'),v('n')))
    a=dict(kind='quote',body=dict(kind='message',force='assert',content=content(body)))
    b=dict(kind='quote',body=dict(kind='message',force='assert',content=content(op('not',body))))
    from scripts.shared_readings import D
    sequence=dict(kind='sequence',element=D,items=[a,b])
    singleton=dict(kind='sequence',element=D,items=[a])
    checks=[call('readingsambiguous',sequence),op('not',call('readingsresolved',singleton,truth(False)))]
    return doc(['readingsambiguous','readingsresolved'],[dict(kind='assert',body=b) for b in checks])


@lru_cache(maxsize=1)
def cases():
    v=vocabulary()
    all_words=v.decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=v.imports(v._order),statements=[])))
    result=[]
    for label,native in (('dictionary',all_words),('time',temporal_example()),('reference',reference_example()),('readings',readings_example())):
        encoded=v.encode(native);page=compile_page(encoded,v,max_width=3200.)
        svg=to_svg(page['shapes']);decoded=decode_page(from_svg(svg))['document']
        if decoded!=encoded or v.decode_names(decoded)!=native:raise ValueError('Visible compound document differs')
        checked=[] if label=='dictionary' else [r['value'] for r in evaluate_document(decoded,
            individuals=('first','second'),situations=('early','late'),primitives={})]
        if not all(checked):raise ValueError('Visible common meaning differs')
        result.append(dict(label=label,native=native,encoded=encoded,page=page,svg=svg,values=checked))
    return result


@lru_cache(maxsize=1)
def word_checks():
    rows=[];v=vocabulary()
    for name in v.document()['compounds']:
        d=v.declaration(name)
        args=[dict(kind='variable',name='arg'+chr(97+i)) for i,p in enumerate(d['parameters'])]
        invocation=dict(kind='call',symbol=d['name'],arguments=args)
        body=op('equal',invocation,invocation)
        for arg,p in reversed(list(zip(args,d['parameters']))):body=q('forall',arg['name'],p['sort'],body)
        quoted=dict(kind='quote',body=dict(kind='function_ref',symbol=d['name']))
        document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=v.imports([name]),
            statements=[dict(kind='assert',body=body),dict(kind='assert',body=op('equal',quoted,quoted))]))
        w=PublicWriter(v);w.document(document)
        shapes=render(w.glyphs)['shapes']
        if decode_document(from_svg(to_svg(shapes)),v)!=document:
            raise ValueError('Typed compound call or quoted reference differs: '+name)
        rows.append(dict(name=name,parts=list(v.word(name).parts),glyphs=len(w.glyphs),shapes=len(shapes),
                         dependency_imports=len(document['declarations'])))
    return rows


def prepare():
    from PIL import Image,ImageDraw
    OUT.mkdir(parents=True,exist_ok=True)
    source=format_graph(temporal_example())+'\n';target=ROOT/SOURCE
    if target.exists() and target.read_text(encoding='utf-8')!=source:raise ValueError('Published temporal example differs')
    if not target.exists():target.write_text(source,encoding='utf-8',newline='\n')
    for row in cases():(OUT/(row['label']+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')
    names=list(vocabulary().document()['compounds'])
    for start in range(0,len(names),10):
        canvas=Image.new('RGB',(1180,5*170),'white');draw=ImageDraw.Draw(canvas)
        for i,name in enumerate(names[start:start+10]):
            x,y=(i%2)*590+24,(i//2)*170+12
            w=PublicWriter(vocabulary());w.name(vocabulary().declaration(name)['name'])
            shapes=render(w.glyphs)['shapes'];scale=.8
            lo=min(s['y']-s['r'] if s['kind']=='circle' else min(s['y1'],s['y2']) for s in shapes)
            for s in shapes:
                if s['kind']=='circle':
                    cx,cy,r=x+s['x']*scale,y+30+(s['y']-lo)*scale,s['r']*scale
                    draw.ellipse((cx-r,cy-r,cx+r,cy+r),outline='#203438',width=2)
                else:draw.line((x+s['x1']*scale,y+30+(s['y1']-lo)*scale,x+s['x2']*scale,y+30+(s['y2']-lo)*scale),fill='#203438',width=2)
            draw.text((x,y),name,fill='#203438')
        canvas.save(OUT/('compound-forms-'+str(start//10+1)+'.png'))


def build_report():
    if parse((ROOT/SOURCE).read_text(encoding='utf-8'))!=temporal_example():raise ValueError('Published visible example differs')
    result=dict(schema='noema-visible-compound-library-evidence-1',edition=3,root_words=30,shared_compounds=50,
        shared_definitions=64,new_primitives=0,new_single_glyphs=0,
        typed_call_shape_decoding=word_checks(),
        shape_decoding=[dict(label=r['label'],rows=r['page']['rows'],shapes=len(r['page']['shapes']),
            values=r['values'],svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in cases()])
    paths=[MANIFEST,SOURCE,'docs/visible-compound-library-v1.md','scripts/visible_compound_vocabulary.py',
        'scripts/visible_public_page.py','scripts/check_visible_compound_library.py','tests/test_visible_compound_library.py',
        'scripts/shared_reference.py','scripts/shared_time.py','scripts/shared_readings.py','scripts/shared_modality.py',
        'scripts/visible_defined_vocabulary.py','scripts/visible_syntax.py','scripts/visible_sharing.py',
        'scripts/visible_syntax_vocabulary.py','scripts/visible_syntax_geometry.py','scripts/visible_shared_page.py','scripts/visible_page.py',
        'scripts/visible_lexical_script.py','scripts/visible_word_forms.py','scripts/balanced_circle_script.py',
        'scripts/branch_circle_script.py','scripts/circle_contact_script.py','noema/resources/visible-lexicon-v1.json',
        'noema/resources/visible-vocabulary-v1.json','noema/resources/visible-defined-vocabulary-v1.json',
        'examples/v016/shared-modality-v1.noema','data/shared-modality-basis-v1.json']
    for module in MODULES:paths.extend(module.values())
    import sys
    from pathlib import Path
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=['50 typed call/reference checks and four pages decode SVG circle/line geometry; typed identities do not evaluate higher-order domains',
                     'No human reading or raster OCR result','Other semantic domains and complete paper rendering remain unfinished']
    return result
