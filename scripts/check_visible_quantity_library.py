"""Visible arithmetic primitives, plural relations and explicit quantities."""
from functools import lru_cache
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_quantity_vocabulary import QuantityVocabulary,ROOT,MANIFEST,MODULES,PRIMITIVES
from scripts.visible_scope_vocabulary import ScopeVocabulary
from scripts.visible_compound_vocabulary import CompoundVocabulary
from scripts.visible_quantity_page import PublicWriter,compile_page,decode_page,decode_document,to_svg,from_svg
from scripts.visible_syntax_geometry import render
from scripts.shared_modality import v,call,op
from scripts.shared_reference import I,S,T,truth,lam
from scripts.shared_time import q,allof
from scripts.shared_readings import num
from scripts.shared_quantities import DIM,MEMBERS,REGISTER,MEASURE,seq

OUT=ROOT/'output/visible-quantity-library-v1'
SOURCE='examples/v016/visible-counted-contents-v1.noema'


@lru_cache(maxsize=1)
def vocabulary():return QuantityVocabulary()
def new_names():return list(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))['spellings'])
def doc(names,statements=()):
    d=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(names),statements=[])))
    d['statements']=list(statements);return normalize_document(d)
def asserted(body):return dict(kind='assert',body=body)
def ratio(n,d):return dict(kind='number',numerator=n,denominator=d)
def equal(a,b):return op('equal',a,b)
def neq(a,b):return op('not',equal(a,b))
def universally(body,parameters):
    for name,sort in reversed(parameters):body=q('forall',name,sort,body)
    return body


def arithmetic_example():
    body=allof(equal(call('rationaladd',ratio(1,3),ratio(2,3)),num(1)),
        equal(call('rationalmultiply',ratio(3,4),num(1000)),num(750)),
        equal(call('rationalnegate',num(2)),num(-2)),call('rationalbelow',ratio(3,2),num(2)))
    return doc(sorted(PRIMITIVES),[asserted(body)])


def conversion_example():
    scalar=call('dimensionless')
    def conversion(k,ls,rs,left,right):
        return call('quantityequal',v('kind'),k,scalar,scalar,ls,rs,left,right)
    body=allof(conversion(v('kind'),num(1),num(1000),num(750),ratio(3,4)),
        conversion(v('kind'),num(1),num(1000),num(1000),num(1)),
        op('implies',neq(v('kind'),v('other')),op('not',conversion(v('other'),num(1),num(1),num(1),num(1)))),
        op('not',conversion(v('kind'),num(0),num(1),num(1),num(0))))
    return doc(['quantityequal','dimensionless'],[asserted(universally(body,[('kind',I),('other',I)]))])


def actions_example():
    group=lam([('member',I)],op('or',equal(v('member'),v('first')),equal(v('member'),v('second'))))
    occurs=lam([('event',I),('at',S)],equal(v('at'),v('world')))
    common=lam([('actor',I),('event',I),('at',S)],allof(equal(v('event'),v('first')),equal(v('at'),v('world'))))
    separate=lam([('actor',I),('event',I),('at',S)],allof(equal(v('actor'),v('event')),equal(v('at'),v('world'))))
    body=op('implies',neq(v('first'),v('second')),allof(
        call('collectiveaction',group,v('world'),occurs,common),
        call('distributedaction',group,v('world'),occurs,separate),
        op('not',call('collectiveaction',group,v('world'),occurs,separate))))
    return doc(['collectiveaction','distributedaction'],[asserted(universally(body,[('first',I),('second',I),('world',S)]))])


def reciprocity_example():
    group=lam([('member',I)],op('or',equal(v('member'),v('first')),op('or',equal(v('member'),v('second')),equal(v('member'),v('third')))))
    pairs=[op('and',equal(v('actor'),v(a)),equal(v('target'),v(b))) for a,b in
           (('first','second'),('second','third'),('third','first'))]
    relation=lam([('actor',I),('target',I),('at',S)],op('and',equal(v('at'),v('world')),op('or',pairs[0],op('or',pairs[1],pairs[2]))))
    distinct=allof(*(neq(v(a),v(b)) for a,b in (('first','second'),('second','third'),('third','first'))))
    body=op('implies',distinct,allof(call('reciprocalneighbors',group,relation,v('world')),
        op('not',call('reciprocalpairs',group,relation,v('world'))),op('not',call('reciprocalall',group,relation,v('world')))))
    return doc(['reciprocalneighbors','reciprocalpairs','reciprocalall'],
        [asserted(universally(body,[('first',I),('second',I),('third',I),('world',S)]))])


def container_example():
    # One whole portion, with a positive explicit magnitude. No hidden numeric
    # lookup, unregistered relation or subject-specific primitive is inserted.
    member=v('portion');members=seq(member);world=v('world');scalar=call('dimensionless')
    assignment=lam([('container',I)],member)
    registry=lam(list(zip(('u','k','d','s','w'),REGISTER['parameters'])),allof(
        equal(v('u'),member),equal(v('k'),member),call('dimensionequal',v('d'),scalar),equal(v('s'),num(1)),equal(v('w'),world)))
    measurement=lam(list(zip(('o','k','u','n','w'),MEASURE['parameters'])),allof(
        equal(v('o'),member),equal(v('k'),member),equal(v('u'),member),equal(v('n'),num(1)),equal(v('w'),world)))
    readings=lam([('o',I),('w',S)],num(1))
    partof=lam([('part',I),('whole',I),('w',S)],allof(equal(v('part'),member),equal(v('whole'),member),equal(v('w'),world)))
    apart=lam([('left',I),('right',I),('w',S)],truth(False))
    complete=lam([('parts',MEMBERS),('whole',I),('w',S)],allof(equal(v('parts'),members),equal(v('whole'),member),equal(v('w'),world)))
    contains=lam([('part',I),('container',I),('w',S)],allof(equal(v('part'),member),equal(v('container'),v('vessel')),equal(v('w'),world)))
    body=call('containeramount',seq(v('vessel')),num(1),assignment,member,member,member,scalar,num(1),readings,
        world,registry,measurement,partof,apart,complete,contains)
    return doc(['containeramount','dimensionless','dimensionequal'],
        [asserted(universally(body,[('portion',I),('vessel',I),('world',S)]))])


def count_scope_example():
    members=seq(v('first'),v('second'))
    duplicated=seq(v('first'),v('first'))
    body=op('implies',neq(v('first'),v('second')),allof(call('membercount',members,num(2)),
        op('not',call('membercount',duplicated,num(2))),call('membercount',seq(),num(0))))
    return doc(['membercount'],[asserted(universally(body,[('first',I),('second',I)]))])


def question_example():
    query=dict(kind='question',function=lam([('member',I)],call('memberof',seq(call('aki'),call('nao')),v('member'))))
    return doc(['memberof','aki','nao'],[dict(kind='ask',body=query)])


def arithmetic_model(encoded=True):
    callbacks={'rationalbelow':lambda a,b:a<b,'rationaladd':lambda a,b:a+b,
               'rationalnegate':lambda a:-a,'rationalmultiply':lambda a,b:a*b,'aki':lambda:'a','nao':lambda:'b'}
    return {vocabulary().declaration(n)['name'] if encoded else n:f for n,f in callbacks.items()}


@lru_cache(maxsize=1)
def cases():
    v=vocabulary();old=CompoundVocabulary();parent=ScopeVocabulary()
    batches=[list(old._order),[n for n in parent._order if n not in old._order],new_names()]
    examples=[('dictionary-'+str(i+1),doc(ns)) for i,ns in enumerate(batches)]
    examples += [('arithmetic',arithmetic_example()),('conversion',conversion_example()),('actions',actions_example()),
                 ('reciprocity',reciprocity_example()),('contents',container_example()),('count-scope',count_scope_example()),('questions',question_example())]
    rows=[]
    for label,native in examples:
        encoded=v.encode(native);page=compile_page(encoded,v,max_width=3200.)
        svg=to_svg(page['shapes']);decoded=decode_page(from_svg(svg),v)['document']
        if decoded!=encoded or v.decode_names(decoded)!=native:raise ValueError('Visible quantity document differs: '+label)
        model=arithmetic_model()
        selected={} if label.startswith('dictionary') else {d['name']:model[d['name']] for d in decoded['declarations'] if d['kind']=='primitive'}
        people=('a','b','c') if label=='reciprocity' else ('a','b')
        budget=1000000 if label=='reciprocity' else 100000
        result=[] if label.startswith('dictionary') else evaluate_document(decoded,individuals=people,
            situations=('now','other'),primitives=selected,max_steps=budget)
        if result and label!='questions' and not all(r['value'] for r in result):raise ValueError('Visible quantity meaning differs: '+label)
        if label=='questions' and result!=[dict(kind='ask',answers=[['a'],['b']])]:raise ValueError('Visible question differs')
        rows.append(dict(label=label,native=native,encoded=encoded,page=page,svg=svg,result=result,individuals=list(people),evaluation_max_steps=budget))
    return rows


@lru_cache(maxsize=1)
def word_checks():
    rows=[];v=vocabulary()
    for name in new_names():
        d=v.declaration(name);imports=v.imports([name])
        sorts=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        args=[dict(kind='variable',name='arg'+chr(97+i)) for i in range(len(sorts))]
        invocation=dict(kind='call',symbol=d['name'],arguments=args);body=equal(invocation,invocation)
        for arg,sort in reversed(list(zip(args,sorts))):body=q('forall',arg['name'],sort,body)
        quoted=dict(kind='quote',body=dict(kind='function_ref',symbol=d['name']))
        document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=imports,
            statements=[asserted(body),asserted(equal(quoted,quoted))]))
        w=PublicWriter(v);w.document(document);shapes=render(w.glyphs)['shapes']
        if decode_document(from_svg(to_svg(shapes)),v)!=document:raise ValueError('Typed public call differs: '+name)
        rows.append(dict(name=name,kind=d['kind'],parts=list(v.word(name).parts),glyphs=len(w.glyphs),shapes=len(shapes),
                         dependency_imports=len(document['declarations'])))
    return rows


def prepare():
    from PIL import Image,ImageDraw
    OUT.mkdir(parents=True,exist_ok=True)
    text=format_graph(container_example())+'\n';target=ROOT/SOURCE
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published visible source differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')
    for row in cases():(OUT/(row['label']+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')
    names=new_names()
    for start in range(0,len(names),10):
        canvas=Image.new('RGB',(1180,850),'white');draw=ImageDraw.Draw(canvas)
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
        canvas.save(OUT/('quantity-forms-'+str(start//10+1)+'.png'))


def build_report():
    if parse((ROOT/SOURCE).read_text(encoding='utf-8'))!=container_example():raise ValueError('Published source differs')
    result=dict(schema='noema-visible-quantity-library-evidence-1',edition=5,root_words=30,shared_compounds=141,
        shared_definitions=151,shared_primitives=20,added_existing_arithmetic_primitives=4,new_primitive_meanings=0,
        new_single_glyphs=0,typed_call_shape_decoding=word_checks(),
        shape_decoding=[dict(label=r['label'],rows=r['page']['rows'],shapes=len(r['page']['shapes']),result=r['result'],
            individuals=r['individuals'],evaluation_max_steps=r['evaluation_max_steps'],
            svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in cases()])
    preserved=['reports/visible-scope-library-v1.json','reports/shared-plurality-v1.json','reports/shared-quantities-v1.json']
    paths=[*preserved,MANIFEST,SOURCE,'docs/visible-quantity-library-v1.md','scripts/visible_quantity_vocabulary.py',
        'scripts/visible_quantity_page.py','scripts/check_visible_quantity_library.py','tests/test_visible_quantity_library.py']
    for module in MODULES:paths.extend(module.values())
    for report in preserved:
        prior=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend(prior)
        for p,digest in prior.items():
            if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest:raise ValueError('Preserved evidence changed: '+p)
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=['Typed call identities check geometry and types, not all higher-order argument domains',
        'Circle/line SVG decoding is not raster OCR or third-party reading',
        'Positive contents page uses one whole portion with an explicit constant reading; multi-portion evidence remains in the preserved Native quantity report',
        'Dictionary inventory spans three independently framed documents; resource limits are unchanged']
    return result
