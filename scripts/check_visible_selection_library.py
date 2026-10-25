"""Visible numeric selection and unequal positive portions without hidden fields."""
from functools import lru_cache
from pathlib import Path
from fractions import Fraction
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_selection_vocabulary import SelectionVocabulary,ROOT,MANIFEST
from scripts.visible_selection_page import PublicWriter,compile_page,decode_page,decode_document,to_svg,from_svg
from scripts.visible_syntax_geometry import render
from scripts.shared_selection import LIBRARY,BASIS,NEW_NAMES
from scripts.shared_quantities import I,S,T,MEMBERS,REGISTER,MEASURE,seq
from noema.constructed_discourse import function_sort as fn
from scripts.shared_reference import lam,truth
from scripts.shared_modality import v,call,op
from scripts.shared_time import q,allof
from scripts.shared_readings import num

OUT=ROOT/'output/visible-selection-library-v1'
SOURCE='examples/v016/visible-multipart-amounts-v1.noema'


@lru_cache(maxsize=1)
def vocabulary():return SelectionVocabulary()
def doc(names,statements=()):
    d=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(names),statements=[])))
    d['statements']=list(statements);return normalize_document(d)
def eq(a,b):return op('equal',a,b)
def apply_expr(fn,*args):return dict(kind='apply',function=fn,arguments=list(args))


def multipart_example(left=250,right=500,*,total_delta=0):
    parts=seq(v('first'),v('second'));whole=v('whole');world=v('world');kind=v('kind');unit=v('unit')
    dimension=call('dimensionless')
    numeric=call('selectnumber',eq(v('object'),v('first')),num(left),
        call('selectnumber',eq(v('object'),v('second')),num(right),num(left+right+total_delta)))
    readings=lam([('object',I),('point',S)],numeric)
    registry=lam(list(zip(('u','k','d','s','w'),REGISTER['parameters'])),allof(
        eq(v('u'),unit),eq(v('k'),kind),call('dimensionequal',v('d'),dimension),eq(v('s'),num(1)),eq(v('w'),world)))
    measurement=lam(list(zip(('o','k','u','n','w'),MEASURE['parameters'])),allof(
        call('memberof',seq(v('first'),v('second'),whole),v('o')),eq(v('k'),kind),eq(v('u'),unit),
        eq(v('n'),apply_expr(v('readings'),v('o'),v('w'))),eq(v('w'),world)))
    partof=lam([('part',I),('total',I),('w',S)],allof(call('memberof',parts,v('part')),eq(v('total'),whole),eq(v('w'),world)))
    disjoint=lam([('left',I),('right',I),('w',S)],op('and',op('not',eq(v('left'),v('right'))),eq(v('w'),world)))
    complete=lam([('parts',MEMBERS),('total',I),('w',S)],allof(eq(v('parts'),parts),eq(v('total'),whole),eq(v('w'),world)))
    body=call('amountsum',parts,whole,kind,unit,dimension,num(1),v('readings'),world,registry,measurement,partof,disjoint,complete)
    body=apply_expr(lam([('readings',fn([I,S],'number'))],body),readings)
    distinct=allof(op('not',eq(v('first'),v('second'))),op('not',eq(v('first'),whole)),op('not',eq(v('second'),whole)))
    body=op('implies',distinct,body)
    for name,sort in reversed([('first',I),('second',I),('whole',I),('kind',I),('unit',I),('world',S)]):body=q('forall',name,sort,body)
    return doc(['amountsum','selectnumber','dimensionless','dimensionequal','memberof'],[dict(kind='assert',body=body)])


def count_example():
    members=seq(v('first'),v('first'),v('second'))
    property=lam([('person',I)],eq(v('person'),v('first')))
    body=op('implies',op('not',eq(v('first'),v('second'))),allof(
        eq(call('occurrencecount',members,property),num(2)),op('not',call('countselected',members,property,num(2))),
        call('countselected',seq(v('first'),v('second')),property,num(1))))
    for name in ('second','first'):body=q('forall',name,I,body)
    return doc(['occurrencecount','countselected'],[dict(kind='assert',body=body)])


def model(document):
    table={'rationaladd':lambda a,b:a+b,'rationalmultiply':lambda a,b:a*b,'rationalbelow':lambda a,b:a<b,
           'rationalnegate':lambda a:-a,'truthindicator':lambda b:Fraction(int(b))}
    return {vocabulary().declaration(n)['name']:f for n,f in table.items()
            if vocabulary().declaration(n)['name'] in {d['name'] for d in document['declarations'] if d['kind']=='primitive'}}


@lru_cache(maxsize=1)
def cases():
    rows=[];v=vocabulary()
    for label,native in [('dictionary',doc(NEW_NAMES)),('counting',count_example()),
                         ('parts-250-500',multipart_example()),('parts-400-600',multipart_example(400,600))]:
        encoded=v.encode(native);page=compile_page(encoded,v,max_width=4800.)
        svg=to_svg(page['shapes']);decoded=decode_page(from_svg(svg),v)['document']
        if decoded!=encoded or v.decode_names(decoded)!=native:raise ValueError('Selection page differs: '+label)
        # Full diagram recovery is separate from binding diagnostics. For the
        # many quantified role parameters, vary kind and unit one at a time,
        # retaining every part/whole triple and both situation values.
        result=[];diagnostics=[]
        if label!='dictionary':
            evaluated=decoded
            if label.startswith('parts'):
                diagnostics=binding_diagnostics(decoded)
                result=diagnostics[0]['result']
            else:
                result=evaluate_document(evaluated,individuals=('a','b'),
                    situations=('now',),primitives=model(evaluated),max_steps=1000000)
            if not all(r['value'] for r in result):raise ValueError('Selection meaning differs: '+label)
        rows.append(dict(label=label,native=native,encoded=encoded,page=page,svg=svg,result=result,diagnostics=diagnostics))
    return rows


def diagnostic_instance(document,kind_slot=0,unit_slot=1):
    # Instantiate kind/unit using the chosen part/whole binder, while retaining
    # the situation binder. This is explicit instantiation of the
    # visible assertion, not a claim to have enumerated every role assignment.
    from copy import deepcopy
    d=deepcopy(document);node=d['statements'][0]['body'];outer=[]
    for _ in range(3):outer.append(node['variable']);node=node['body']
    kind=node['variable'];node=node['body'];unit=node['variable'];node=node['body']
    world=node['variable'];body=node['body']
    def substitute(x):
        if isinstance(x,list):return [substitute(y) for y in x]
        if not isinstance(x,dict):return x
        if x.get('kind')=='variable' and x['name'] in (kind,unit):return v(outer[kind_slot] if x['name']==kind else outer[unit_slot])
        return {k:substitute(y) for k,y in x.items()}
    body=q('forall',world,S,substitute(body))
    for name in reversed(outer):body=q('forall',name,I,body)
    d['statements'][0]['body']=body
    return normalize_document(d)


def binding_diagnostics(document):
    rows=[]
    for kind_slot,unit_slot in ((0,1),(1,1),(2,1),(0,0),(0,2)):
        d=diagnostic_instance(document,kind_slot,unit_slot)
        result=evaluate_document(d,individuals=('a','b','c'),situations=('now','then'),primitives=model(d),max_steps=1000000)
        if not all(r['value'] for r in result):raise ValueError('Multipart binding diagnostic failed')
        rows.append(dict(kind_slot=kind_slot,unit_slot=unit_slot,result=result))
    return rows


@lru_cache(maxsize=1)
def word_checks():
    rows=[];vocab=vocabulary()
    for name in NEW_NAMES:
        d=vocab.declaration(name);sorts=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        args=[v('arg'+chr(97+i)) for i in range(len(sorts))]
        invocation=dict(kind='call',symbol=d['name'],arguments=args);body=eq(invocation,invocation)
        for arg,sort in reversed(list(zip(args,sorts))):body=q('forall',arg['name'],sort,body)
        quote=dict(kind='quote',body=dict(kind='function_ref',symbol=d['name']))
        native=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=vocab.imports([name]),
            statements=[dict(kind='assert',body=body),dict(kind='assert',body=eq(quote,quote))]))
        writer=PublicWriter(vocab);writer.document(native);shapes=render(writer.glyphs)['shapes']
        if decode_document(from_svg(to_svg(shapes)),vocab)!=native:raise ValueError('Selection call differs')
        rows.append(dict(name=name,kind=d['kind'],glyphs=len(writer.glyphs),shapes=len(shapes)))
    return rows


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    text=format_graph(multipart_example())+'\n';target=ROOT/SOURCE
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published multipart source differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')
    for row in cases():(OUT/(row['label']+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')


def build_report():
    if parse((ROOT/SOURCE).read_text(encoding='utf-8'))!=multipart_example():raise ValueError('Published multipart source differs')
    result=dict(schema='noema-visible-selection-evidence-1',edition=6,words=176,shared_definitions=155,shared_primitives=21,
        new_primitive_meanings=0,new_single_glyphs=0,typed_call_shape_decoding=word_checks(),
        shape_decoding=[dict(label=r['label'],rows=r['page']['rows'],shapes=len(r['page']['shapes']),result=r['result'],diagnostics=r['diagnostics'],
            svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in cases()])
    preserved=['reports/visible-quantity-library-v1.json','reports/shared-selection-v1.json']
    paths=[MANIFEST,LIBRARY,BASIS,SOURCE,'scripts/visible_selection_vocabulary.py','scripts/visible_selection_page.py',
        'scripts/check_visible_selection_library.py','tests/test_visible_selection_library.py','docs/visible-selection-v1.md',*preserved]
    for report in preserved:
        hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend(hashes)
        for p,h in hashes.items():
            if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('Prior evidence changed: '+p)
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=['All visible variables, functions and scopes recover from geometry.',
        'Multipart binding diagnostics vary kind and unit one at a time over three object binders and retain two situation values; not a proof over all role domains.',
        'Examples stipulate positive dimensionless quantities in a common unit; they do not declare real-world measurements or replace physical quantity definitions.',
        'No raster OCR or third-party reading; resource limits unchanged.']
    return result
