"""Read normal-case and degree examples from geometry, then evaluate them."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort
from noema.constructed_semantics import evaluate_document
from scripts.visible_generality_vocabulary import GeneralityVocabulary,ROOT,MANIFEST,LIBRARY,BASIS
from scripts.visible_generality_page import PublicWriter,compile_page,decode_page,decode_document,to_svg,from_svg
from scripts.visible_syntax_geometry import render
from scripts.shared_generality import I,S,T,GROUP,ORDER,ASSIGN
from scripts.shared_reference import lam
from scripts.shared_modality import v,call,app,op
from scripts.shared_time import q,allof

OUT=ROOT/'output/visible-generality-library-v1'
SOURCES={n:'examples/v016/visible-'+n+'-v1.noema' for n in ('generic-exception','kindwise-generic','degree-standards','modal-degree')}


@lru_cache(maxsize=1)
def vocabulary():return GeneralityVocabulary()
@lru_cache(maxsize=1)
def new_names():return tuple(d['name'] for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
def eq(a,b):return op('equal',a,b)
def neq(a,b):return op('not',eq(a,b))
def either(*xs):
    body=xs[-1]
    for x in reversed(xs[:-1]):body=op('or',x,body)
    return body
def let(parameters,arguments,body):return dict(kind='apply',function=lam(parameters,body),arguments=arguments)
def quantify(parameters,body):
    for n,t in reversed(parameters):body=q('forall',n,t,body)
    return body
def doc(names,body=None):
    result=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(names),statements=[])))
    if body is not None:result['statements']=[dict(kind='assert',body=body)]
    return normalize_document(result)


def generic_example(kindwise=False):
    a,b=v('first'),v('second')
    cases=lam([('x',I)],either(eq(v('x'),a),eq(v('x'),b)))
    first=lam([('x',I)],eq(v('x'),a));second=lam([('x',I)],eq(v('x'),b))
    preferred=lam([('x',I),('y',I)],op('and',eq(v('x'),a),eq(v('y'),b)))
    common=call('casegeneric',v('cases'),v('preferred'),v('firstcase'))
    if kindwise:
        body=op('and',common,op('not',call('kindwisegeneric',v('firstcase'),second,v('preferred'),v('firstcase'))))
        names=['casegeneric','kindwisegeneric']
    else:
        body=allof(common,op('not',call('caseuniversal',v('cases'),v('firstcase'))),
            call('caseexception',b,v('cases'),v('firstcase')))
        names=['casegeneric','caseuniversal','caseexception']
    body=let([('cases',GROUP),('preferred',ORDER),('firstcase',GROUP)],[cases,preferred,first],body)
    return doc(names,quantify([('first',I),('second',I)],op('implies',neq(a,b),body)))


def scale_parts():
    low,mid,high=v('low'),v('middle'),v('high')
    scale=lam([('x',I)],either(eq(v('x'),low),eq(v('x'),mid),eq(v('x'),high)))
    less=lam([('x',I),('y',I)],either(
        op('and',eq(v('x'),low),eq(v('y'),mid)),op('and',eq(v('x'),mid),eq(v('y'),high)),
        op('and',eq(v('x'),low),eq(v('y'),high))))
    distinct=allof(neq(low,mid),neq(low,high),neq(mid,high))
    return scale,less,distinct


def degree_example():
    scale,less,distinct=scale_parts()
    positive=lam([('x',I)],eq(v('x'),v('high')));negative=lam([('x',I)],eq(v('x'),v('low')))
    identity=lam([('x',I)],v('x'));criterion=lam([('x',I)],either(eq(v('x'),v('middle')),eq(v('x'),v('high'))))
    common=[v('assignment'),v('scale'),v('less'),v('positive'),v('negative')]
    body=allof(call('degreepositive',v('high'),*common),call('degreenegative',v('low'),*common),
        call('degreeborderline',v('middle'),*common),
        call('degreemore',v('middle'),v('low'),v('assignment'),v('scale'),v('less')),
        call('degreeenough',v('middle'),v('assignment'),v('scale'),v('less'),criterion))
    body=let([('scale',GROUP),('less',ORDER),('positive',GROUP),('negative',GROUP),('assignment',ASSIGN)],
        [scale,less,positive,negative,identity],body)
    return doc(['degreepositive','degreenegative','degreeborderline','degreemore','degreeenough'],
        quantify([('low',I),('middle',I),('high',I)],op('implies',distinct,body)))


def modal_example():
    scale,less,distinct=scale_parts();pred=function_sort([S],T)
    cases=lam([('w',S)],either(eq(v('w'),v('firstworld')),eq(v('w'),v('secondworld'))))
    goal=lam([('w',S)],eq(v('w'),v('firstworld')))
    def degree(n):return call('modaldegree',v('cases'),v('goal'),v('scale'),v(n),v('low'),v('high'))
    body=allof(call('boundedscale',v('scale'),v('less'),v('low'),v('high')),
        degree('middle'),op('not',degree('low')),op('not',degree('high')))
    body=let([('scale',GROUP),('less',ORDER),('cases',pred),('goal',pred)],[scale,less,cases,goal],body)
    return doc(['modaldegree','boundedscale'],quantify([('low',I),('middle',I),('high',I),('firstworld',S),('secondworld',S)],
        op('implies',op('and',distinct,neq(v('firstworld'),v('secondworld'))),body)))


@lru_cache(maxsize=1)
def cases():
    rows=[];vocab=vocabulary()
    examples=[('dictionary',doc(new_names())),('generic-exception',generic_example()),
        ('kindwise-generic',generic_example(True)),('degree-standards',degree_example()),('modal-degree',modal_example())]
    for label,native in examples:
        encoded=vocab.encode(native);writer=PublicWriter(vocab);writer.document(encoded)
        page=compile_page(encoded,vocab,max_width=4800.);svg=to_svg(page['shapes'])
        decoded=decode_page(from_svg(svg),vocab)['document']
        if decoded!=encoded or vocab.decode_names(decoded)!=native:raise ValueError('Generality shape decoding differs: '+label)
        result=[]
        if label!='dictionary':
            # Each source quantifies all of its slots, including both situations
            # in the modal example; no fixture callbacks supply omitted bodies.
            result=evaluate_document(decoded,individuals=('a','b','c'),situations=('now','later'),primitives={},max_steps=1000000)
            if result!=[dict(kind='assert',value=True)]:raise ValueError('Visible generality meaning differs: '+label)
        rows.append(dict(label=label,native=native,encoded=encoded,page=page,svg=svg,result=result,glyphs=len(writer.glyphs)))
    return rows


@lru_cache(maxsize=1)
def word_checks():
    rows=[];vocab=vocabulary()
    for name in new_names():
        d=vocab.declaration(name);parameters=[('arg'+chr(97+i),p['sort']) for i,p in enumerate(d['parameters'])]
        invocation=call(d['name'],*(v(n) for n,t in parameters));body=quantify(parameters,eq(invocation,invocation))
        quote=dict(kind='quote',body=dict(kind='function_ref',symbol=d['name']))
        native=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=vocab.imports([name]),
            statements=[dict(kind='assert',body=body),dict(kind='assert',body=eq(quote,quote))]))
        w=PublicWriter(vocab);w.document(native);shapes=render(w.glyphs)['shapes']
        if decode_document(from_svg(to_svg(shapes)),vocab)!=native:raise ValueError('Typed call decoding differs: '+name)
        rows.append(dict(name=name,parts=list(vocab.word(name).parts),glyphs=len(w.glyphs),shapes=len(shapes)))
    return rows


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    for row in cases():
        if row['label'] in SOURCES:
            target=ROOT/SOURCES[row['label']];text=format_graph(row['native'])+'\n'
            if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published visible example differs')
            if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')
        (OUT/(row['label']+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')
    preview()


def preview():
    from PIL import Image,ImageDraw
    for start in range(0,len(new_names()),10):
        canvas=Image.new('RGB',(1180,850),'white');draw=ImageDraw.Draw(canvas)
        for i,name in enumerate(new_names()[start:start+10]):
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
        canvas.save(OUT/('generality-forms-'+str(start//10+1)+'.png'))


def build_report():
    for row in cases():
        if row['label'] in SOURCES and parse((ROOT/SOURCES[row['label']]).read_text(encoding='utf-8'))!=row['native']:
            raise ValueError('Published visible source differs')
    result=dict(schema='noema-visible-generality-evidence-1',edition=7,words=199,root_words=30,shared_compounds=169,
        shared_definitions=178,shared_primitives=21,new_single_glyphs=0,new_primitive_meanings=0,
        typed_call_shape_decoding=word_checks(),shape_decoding=[dict(label=r['label'],glyphs=r['glyphs'],rows=r['page']['rows'],
            shapes=len(r['page']['shapes']),result=r['result'],svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in cases()])
    preserved=['reports/visible-selection-v1.json','reports/shared-generality-v1.json']
    paths=[MANIFEST,LIBRARY,BASIS,*SOURCES.values(),'scripts/visible_generality_vocabulary.py','scripts/visible_generality_page.py',
        'scripts/check_visible_generality_library.py','tests/test_visible_generality_library.py','docs/visible-generality-v1.md',*preserved]
    for report in preserved:
        hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend(hashes)
        for p,digest in hashes.items():
            if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest:raise ValueError('Prior evidence changed: '+p)
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=['SVG geometry restores every visible import, variable and lambda body without hidden AST metadata.',
        'Four closed examples evaluate their full quantified bodies on three individuals and two situations; not a proof over infinite domains.',
        'Typed higher-order call and quotation roundtrips validate syntax, not enumeration of all function values.',
        'Actual normality, scales and standards require evidence outside these stipulated examples.',
        'No raster OCR or third-party reading; frozen geometry and resource limits unchanged.']
    return result
