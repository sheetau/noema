"""Recover complete evidence and revision examples from visible geometry."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from pathlib import Path
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from scripts.visible_evidence_vocabulary import EvidenceVocabulary,ROOT,MANIFEST,LIBRARIES
from scripts.visible_evidence_page import PublicWriter,compile_page,decode_document,to_svg,from_svg
from scripts.visible_evidence_book import compile_book,decode_book
from scripts.visible_syntax_geometry import render
from scripts.visible_word_forms import Word,symbol
from scripts.shared_reference import S,definition
from scripts.shared_modality import call,renamed
from scripts.check_visible_deadline_library import ref,quote,eq,quantify,number
from scripts import check_shared_revision as revision,check_shared_evidence as evidence

OUT=ROOT/'output/visible-evidence-library-v1'
LABELS=tuple('revision-'+n for n in revision.EXAMPLES)+tuple('evidence-'+n for n in evidence.EXAMPLES)
SOURCES={label:'examples/v016/visible-'+label+'-v1.noema' for label in LABELS}
LOCAL_PARTS=dict(claims='book',recordclaims='fruit',orders='above',parents='treeone',local='assessmentvalid',
    scope='inside',comparisons='town',corpus='candidatenecessary',supported='methodguaranteed',received='give',
    adopts='methodpossible',precedence='fly',available='home',aware='candidatepossible',alternatives='candidatecontingent',
    firstform='red',secondform='round',claimform='bird',holders='aki',events='nao',recorded='rain',
    observed='birdone',relayed='candidateexists',inferred='assessedability',roots='assessmentdecisive')
TIME_PARTS=dict(before='aki',after='nao',assessment='book',otherworld='fruit',context='home',laterpoint='above')

@lru_cache(maxsize=1)
def vocabulary():return EvidenceVocabulary()
@lru_cache(maxsize=1)
def new_names():return tuple(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))['spellings'])
def local(name):
    return symbol(Word('compound',('home','round',TIME_PARTS[name]) if name in TIME_PARTS else ('home','book',LOCAL_PARTS[name])),vocabulary())
def slot(n):return call('situationslot',call('aki'),number(n))

def doc(extra=(),bodies=(),names=()):
    locals_by_name={d['name']:d for d in extra};required=set(names);selected=set()
    def visit(n):
        if n in selected:return
        selected.add(n)
        if n in vocabulary()._words:required.add(n)
        elif n in locals_by_name:
            for dep in _references(locals_by_name[n]['body']):visit(dep)
        else:raise ValueError('Unknown visible fixture dependency: '+n)
    for body in bodies:
        for n in _references(body):visit(n)
    d=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(required),statements=[])))
    d['declarations'] += [d for d in extra if d['name'] in selected]
    d['statements']=[dict(kind='ask',body=b) for b in bodies]
    return normalize_document(d)

def native_example(label):
    group,mode=label.split('-',1)
    if group=='revision':
        source=revision.example(mode);constants=revision.CONSTANTS|dict(record='b' if mode=='misleading' else 'a')
        times=dict(before=0,after=1,assessment=2,otherworld=3);aliases=dict(priorafter='after',nextbefore='after')
    else:
        source=evidence.example(mode);constants=evidence.CONSTANTS|dict(third='c')
        times=dict(context=0,assessment=0,laterpoint=1);aliases={}
    def substitute(x):
        if isinstance(x,list):return [substitute(y) for y in x]
        if not isinstance(x,dict):return x
        if x.get('kind')=='call':
            n=x['symbol']
            if n in constants:return call(dict(a='aki',b='nao',c='birdone')[constants[n]])
            if n in aliases:return call(local(aliases[n]))
        return {k:substitute(y) for k,y in x.items()}
    converted=renamed(substitute(source),{n:local(n) for n in (*LOCAL_PARTS,*TIME_PARTS)})
    extra=[definition(local(n),[],S,slot(i)) for n,i in times.items()]
    extra += [d for d in converted['declarations'] if d['kind']=='definition' and d['name'] in {local(n) for n in LOCAL_PARTS}]
    return doc(extra,[s['body'] for s in converted['statements']])

def expected(label):
    group,mode=label.split('-',1)
    return [dict(kind='ask',value=x) for x in (revision.example_expected(mode) if group=='revision' else evidence.example_expected(mode))]
def scenes(label):return revision.EXAMPLE_SCENES if label.startswith('revision-') else evidence.TIMES
def people(label):return ('a','b') if label.startswith('revision-') else ('a','b','c')
def model(document,label,*,assignment=None):
    assignment=scenes(label) if assignment is None else assignment
    def address(context,index):
        if context!='a' or index not in tuple(Fraction(i) for i in range(len(assignment))):raise ValueError('Unknown situation address')
        return assignment[int(index)]
    known={'aki':lambda:'a','nao':lambda:'b','birdone':lambda:'c','situationslot':address,'claimchoice':lambda c,a,b:a if c else b}
    return {d['name']:known[vocabulary()._by_symbol[d['name']]] for d in document['declarations'] if d['kind']=='primitive'}
def evaluate(document,label,**kwargs):
    return evaluate_document(document,individuals=people(label),situations=scenes(label),primitives=model(document,label,**kwargs),max_steps=2000000)

@lru_cache(maxsize=1)
def ranks():
    dependencies={}
    def level(x):
        if isinstance(x,list):return max((level(y) for y in x),default=0)
        if not isinstance(x,dict):return 0
        own=x.get('rank',0)+1 if x.get('kind')=='disquote' else dependencies.get(x.get('symbol'),0)
        return max(own,max((level(y) for y in x.values()),default=0))
    for name in vocabulary()._order:
        d=vocabulary()._plain_declaration(name);dependencies[name]=level(d.get('body'))
    return dependencies

@lru_cache(maxsize=1)
def word_checks():
    rows=[];vocab=vocabulary()
    for name in new_names():
        d=vocab.declaration(name);ps=[('arg'+chr(97+i),t) for i,t in enumerate(d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']])]
        invocation=call(d['name'],*(dict(kind='variable',name=n) for n,t in ps))
        quoted=quote(ref(d['name']))
        if ranks()[name]:quoted['rank']=ranks()[name]
        native=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=vocab.imports([name]),
            statements=[dict(kind='assert',body=quantify(ps,eq(invocation,invocation))),dict(kind='assert',body=eq(quoted,quoted))]))
        w=PublicWriter(vocab);w.document(native);shapes=render(w.glyphs)['shapes']
        if decode_document(from_svg(to_svg(shapes)),vocab)!=native:raise ValueError('Typed evidence call differs: '+name)
        rows.append(dict(name=name,parts=list(vocab.word(name).parts),quotation_rank=ranks()[name],glyphs=len(w.glyphs),shapes=len(shapes)))
    return rows

@lru_cache(maxsize=None)
def case(label):
    native=doc(names=new_names()) if label=='dictionary' else native_example(label)
    vocab=vocabulary();encoded=vocab.encode(native);writer=PublicWriter(vocab);writer.document(encoded)
    pages=compile_book(encoded,vocab,max_width=6400.);svgs=[to_svg(p['shapes']) for p in pages]
    decoded=decode_book([from_svg(svg) for svg in svgs])['document']
    if decoded!=encoded or vocab.decode_names(decoded)!=native:raise ValueError('Evidence geometry differs: '+label)
    result=[] if label=='dictionary' else evaluate(decoded,label)
    if label!='dictionary' and result!=expected(label):raise ValueError('Decoded evidence meaning differs: '+label)
    return dict(label=label,native=native,encoded=encoded,pages=pages,svgs=svgs,result=result,glyphs=len(writer.glyphs))
def cases():return [case(label) for label in ('dictionary',*LABELS)]

def saved_case(label):
    """Inspect rendered artifacts directly; never restore cached judgments."""
    from scripts.visible_page import split_rows
    from scripts.visible_syntax_geometry import recognize
    from scripts.visible_syntax import Reader
    from scripts.visible_syntax_vocabulary import Vocabulary
    paths=sorted(OUT.glob(label+'-*.svg'))
    if not paths or paths!=[OUT/(label+'-'+str(i+1)+'.svg') for i in range(len(paths))]:
        raise ValueError('Missing or unexpected rendered evidence pages: '+label)
    svgs=[p.read_text(encoding='utf-8') for p in paths];shapes=[from_svg(s) for s in svgs]
    decoded=decode_book(shapes)['document'];native=doc(names=new_names()) if label=='dictionary' else native_example(label)
    encoded=vocabulary().encode(native)
    if decoded!=encoded or vocabulary().decode_names(decoded)!=native:raise ValueError('Saved evidence geometry differs: '+label)
    pages=[]
    for page in shapes:
        rows=split_rows(page);count=0
        for row in rows:
            tokens=recognize(row);reader=Reader(tokens,Vocabulary());reader.take();reader.natural()
            count+=len(tokens)-reader.i-1
        pages.append(dict(shapes=page,rows=len(rows),glyphs=count))
    writer=PublicWriter(vocabulary());writer.document(encoded)
    if sum(p['glyphs'] for p in pages)!=len(writer.glyphs):raise ValueError('Saved evidence payload differs')
    result=[] if label=='dictionary' else evaluate(decoded,label)
    if label!='dictionary' and result!=expected(label):raise ValueError('Saved evidence meaning differs: '+label)
    return dict(label=label,native=native,encoded=encoded,pages=pages,svgs=svgs,result=result,glyphs=len(writer.glyphs))

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    for label in ('dictionary',*LABELS):
        row=case(label)
        if row['label'] in SOURCES:
            target=ROOT/SOURCES[row['label']];text=format_graph(row['native'])+'\n'
            if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published visible evidence differs')
            if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')
        for i,svg in enumerate(row['svgs']):(OUT/(row['label']+'-'+str(i+1)+'.svg')).write_text(svg,encoding='utf-8',newline='\n')
        print('Prepared visible '+label+': '+str(len(row['pages']))+' pages',flush=True)

def build_report():
    rows=[saved_case(label) for label in ('dictionary',*LABELS)]
    for row in rows:
        if row['label'] in SOURCES and parse((ROOT/SOURCES[row['label']]).read_text(encoding='utf-8'))!=row['native']:
            raise ValueError('Published evidence example differs')
    result=dict(schema='noema-visible-evidence-report-1',edition=11,words=312,root_words=30,shared_compounds=282,
        shared_definitions=289,shared_primitives=23,new_single_glyphs=0,new_primitive_declarations=1,
        typed_call_shape_decoding=word_checks(),shape_decoding=[dict(label=r['label'],glyphs=r['glyphs'],result=r['result'],pages=[
            dict(rows=p['rows'],glyphs=p['glyphs'],shapes=len(p['shapes']),svg_sha256=hashlib.sha256(svg.encode()).hexdigest())
            for p,svg in zip(r['pages'],r['svgs'])]) for r in rows])
    preserved=['reports/visible-deadline-v1.json','reports/shared-revision-v1.json','reports/shared-evidence-v1.json']
    paths=[MANIFEST,*SOURCES.values(),'scripts/visible_evidence_vocabulary.py','scripts/visible_evidence_page.py',
        'scripts/visible_evidence_book.py','scripts/check_visible_evidence_library.py','tests/test_visible_evidence_library.py',
        'tests/test_visible_evidence_artifacts.py','docs/visible-evidence-v1.md',*preserved]
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
    result['limits']=['Circle and line geometry determines declarations, imports and statements before evaluation; no hidden document AST.',
        'Names Aki, Nao and the designated bird, explicit situation addresses and typed claim choice have host interpretations; other relations have Native bodies.',
        'The designated bird supplies the third entity of the evidence models; these stipulated models claim no real-world observation, communication or reasoning ability.',
        'Proof validity, belief uptake and actual content truth remain separate; provenance disjointness is not statistical independence.',
        'Per-page limits remain 768 payload glyphs and 4096 shapes; books retain eight pages, 128 rows and 8192 expanded nodes.',
        'Typed calls and quotations do not exhaust function domains. The eight finite examples do not prove unbounded semantic equivalence.',
        'No raster OCR or third-party reading; frozen glyphs and prior decoders remain unchanged.']
    return result
