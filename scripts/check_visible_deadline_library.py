"""Recover deadlines and retained breach from visible geometry before evaluation."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from fractions import Fraction
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from scripts.visible_deadline_vocabulary import DeadlineVocabulary,ROOT,MANIFEST,LIBRARIES
from scripts.visible_deadline_page import PublicWriter,compile_page,decode_page,decode_document,to_svg,from_svg
from scripts.visible_deadline_book import compile_book,decode_book
from scripts.visible_syntax_geometry import render
from scripts.visible_word_forms import Word,symbol
from scripts.shared_reference import I,S,T,C,lam,definition,truth
from scripts.shared_modality import v,call,op,renamed
from scripts.shared_time import q,allof
from scripts.check_shared_deadlines import example,EXAMPLE_RESULTS,TIMES,CONSTANTS

OUT=ROOT/'output/visible-deadline-library-v1'
LABELS=('history',)
SOURCES={label:'examples/v016/visible-deadline-'+label+'-v1.noema' for label in LABELS}
RANK_ONE={'deadlineachieved','deadlinerequired','deadlinefreedat','deadlinereleased','deadlinefulfilled',
    'deadlinepending','deadlinebreached','deadlinelate','promisedeadline'}
LOCAL_PARTS=dict(history='aki',order='nao',actform='fruit',promiseform='red',recognized='round',applicable='birdone',
    supports='treeone',authorized='candidateempty',releases='methodpossible',occurs='methodguaranteed',
    presents='assessedability',conveys='methodsassessable',targets='assessmentdecisive',undertakes='candidatepossible',
    issued='red',releasepoint='round',due='bird',assessment='fly',description='book')

@lru_cache(maxsize=1)
def vocabulary():return DeadlineVocabulary()
@lru_cache(maxsize=1)
def new_names():return tuple(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))['spellings'])
def local(name):
    prefix=('above','book') if name in ('issued','releasepoint','due','assessment','description') else ('book','above')
    return symbol(Word('compound',(*prefix,LOCAL_PARTS[name])),vocabulary())
def ref(n):return dict(kind='function_ref',symbol=n)
def quote(body):return dict(kind='quote',body=body)
def eq(a,b):return op('equal',a,b)
def quantify(ps,body):
    for n,t in reversed(ps):body=q('forall',n,t,body)
    return body
def number(n):return dict(kind='number',numerator=n,denominator=1)
def slot(n):return call('situationslot',call('aki'),number(n))

def doc(extra=(),body=None,names=()):
    locals_by_name={d['name']:d for d in extra};required=set(names);selected=set()
    def visit(n):
        if n in selected:return
        selected.add(n)
        if n in vocabulary()._words:required.add(n)
        elif n in locals_by_name:
            for dep in _references(locals_by_name[n]['body']):visit(dep)
        else:raise ValueError('Unknown visible fixture dependency: '+n)
    if body is not None:
        for n in _references(body):visit(n)
    d=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(required),statements=[])))
    d['declarations'] += [d for d in extra if d['name'] in selected]
    if body is not None:d['statements']=[dict(kind='ask',body=b) for b in (body if isinstance(body,list) else [body])]
    return normalize_document(d)

def native_examples():
    source=deepcopy(example());times=dict(issued=0,releasepoint=1,due=2,assessment=3)
    def substitute(x):
        if isinstance(x,list):return [substitute(y) for y in x]
        if not isinstance(x,dict):return x
        if x.get('kind')=='call':
            n=x['symbol']
            if n in times:return call(local(n))
            if n in CONSTANTS:return call('aki' if CONSTANTS[n]=='a' else 'nao')
            if n=='deadlinedescription':return call(local('description'))
        return {k:substitute(y) for k,y in x.items()}
    from scripts.check_shared_deadlines import query
    raw_description=query('deadlinedescription')
    converted=call('deadlinedescription',*[substitute(x) for x in raw_description['arguments']])
    source=renamed(substitute(source),{n:local(n) for n in LOCAL_PARTS})
    extra=[d for d in source['declarations'] if d['name'] in {local(n) for n in LOCAL_PARTS}]
    extra=[d for d in extra if d['kind']=='definition']
    aliases=[definition(local(n),[],S,slot(i)) for n,i in times.items()]
    description=definition(local('description'),[],dict(kind='description',result=dict(kind='function',parameters=[I,I],result=C)),
        renamed(converted,{n:local(n) for n in LOCAL_PARTS}))
    index=next(i for i,d in enumerate(extra) if d['name']==local('recognized'))
    extra=aliases+extra[:index]+[description]+extra[index:]
    return [('history',doc(extra,[s['body'] for s in source['statements']]))]

def expected(label):return [dict(kind='ask',value=value) for value in EXAMPLE_RESULTS]
def model(document,*,assignment=TIMES):
    def address(context,index):
        if context!='a' or index not in tuple(Fraction(i) for i in range(4)):
            raise ValueError('Unknown situation address')
        return assignment[int(index)]
    known={'aki':lambda:'a','nao':lambda:'b','situationslot':address}
    return {d['name']:known[vocabulary()._by_symbol[d['name']]] for d in document['declarations'] if d['kind']=='primitive'}


@lru_cache(maxsize=1)
def cases():
    result=[];vocab=vocabulary()
    for label,native in [('dictionary',doc(names=new_names()))]+native_examples():
        encoded=vocab.encode(native);w=PublicWriter(vocab);w.document(encoded)
        pages=compile_book(encoded,vocab,max_width=4800.);svgs=[to_svg(p['shapes']) for p in pages]
        decoded=decode_book([from_svg(s) for s in svgs],vocab)['document']
        if decoded!=encoded or vocab.decode_names(decoded)!=native:raise ValueError('Deadline geometry differs: '+label)
        values=[]
        if label!='dictionary':
            values=evaluate_document(decoded,individuals=('a','b'),situations=TIMES,primitives=model(decoded),max_steps=2000000)
            if values!=expected(label):raise ValueError('Decoded deadline meaning differs: '+label)
        result.append(dict(label=label,native=native,encoded=encoded,pages=pages,svgs=svgs,result=values,glyphs=len(w.glyphs)))
    return result


@lru_cache(maxsize=1)
def word_checks():
    rows=[];vocab=vocabulary()
    for name in new_names():
        d=vocab.declaration(name);ps=[('arg'+chr(97+i),t) for i,t in enumerate(d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']])]
        invocation=call(d['name'],*(v(n) for n,t in ps));body=quantify(ps,eq(invocation,invocation))
        quoted=quote(ref(d['name']))
        if name in RANK_ONE:quoted['rank']=1
        native=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=vocab.imports([name]),
            statements=[dict(kind='assert',body=body),dict(kind='assert',body=eq(quoted,quoted))]))
        w=PublicWriter(vocab);w.document(native);shapes=render(w.glyphs)['shapes']
        if decode_document(from_svg(to_svg(shapes)),vocab)!=native:raise ValueError('Typed deadline call differs: '+name)
        rows.append(dict(name=name,parts=list(vocab.word(name).parts),quotation_rank=quoted.get('rank',0),glyphs=len(w.glyphs),shapes=len(shapes)))
    return rows


def preview():
    from PIL import Image,ImageDraw
    OUT.mkdir(parents=True,exist_ok=True)
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
        canvas.save(OUT/('deadline-forms-'+str(start//10+1)+'.png'))


def prepare():
    from scripts.shared_situation_reference import prepare as prepare_reference
    prepare_reference()
    OUT.mkdir(parents=True,exist_ok=True)
    for row in cases():
        if row['label'] in SOURCES:
            target=ROOT/SOURCES[row['label']];text=format_graph(row['native'])+'\n'
            if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published visible deadline differs')
            if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')
        for i,svg in enumerate(row['svgs']):
            (OUT/(row['label']+'-'+str(i+1)+'.svg')).write_text(svg,encoding='utf-8',newline='\n')
    preview()


def build_report():
    for row in cases():
        if row['label'] in SOURCES and parse((ROOT/SOURCES[row['label']]).read_text(encoding='utf-8'))!=row['native']:
            raise ValueError('Published deadline example differs')
    result=dict(schema='noema-visible-deadline-evidence-1',edition=10,words=267,root_words=30,shared_compounds=237,
        shared_definitions=245,shared_primitives=22,new_single_glyphs=0,new_primitive_declarations=1,
        typed_call_shape_decoding=word_checks(),shape_decoding=[dict(label=r['label'],glyphs=r['glyphs'],result=r['result'],pages=[
            dict(rows=p['rows'],glyphs=p['glyphs'],shapes=len(p['shapes']),svg_sha256=hashlib.sha256(svg.encode()).hexdigest())
            for p,svg in zip(r['pages'],r['svgs'])]) for r in cases()])
    preserved=['reports/visible-conversation-v1.json','reports/shared-deadlines-v1.json']
    paths=[MANIFEST,*SOURCES.values(),'scripts/visible_deadline_vocabulary.py','scripts/visible_deadline_page.py',
        'scripts/check_visible_deadline_library.py','scripts/visible_deadline_book.py','scripts/shared_situation_reference.py','tests/test_visible_deadline_library.py','docs/visible-deadline-v1.md',*preserved]
    for spec in LIBRARIES:paths.extend(spec.values())
    for report in preserved:
        hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend(hashes)
        for path,digest in hashes.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Earlier evidence changed: '+path)
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=['All declarations and statements decode from circle and line geometry before evaluation.',
        'One shared situation-address primitive explicitly interprets a context and rational address; it supplies no ordering or normative status.',
        'Only two individual names and situation-address bindings have host interpretations. All temporal, normative and speech relations have Native bodies.',
        'Typed calls and quotations do not exhaust higher-order function or description domains.',
        'Finite stipulated examples do not establish real authority, compliance, completeness or continuous-time theorems.',
        'The book adapter retains 768 payload glyphs and 4096 shapes per page, 128 rows and 8192 expanded nodes per document; at most eight pages.',
        'Original single-page decoders and budgets are unchanged. The book adapter explicitly accepts a larger total glyph stream across bounded pages.',
        'No raster OCR or third-party reading; frozen glyphs remain unchanged.']
    return result
