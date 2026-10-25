"""Geometry evidence for normative targets and scoped referents in edition four."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_scope_vocabulary import ScopeVocabulary,ROOT,MANIFEST,MODULES
from scripts.visible_compound_vocabulary import CompoundVocabulary
from scripts.visible_language_page import PublicWriter,compile_page,decode_page,decode_document,to_svg,from_svg
from scripts.visible_syntax_geometry import render
from scripts.shared_modality import v,call,op
from scripts.shared_reference import truth,lam,content
from scripts.shared_time import q,allof
from scripts.shared_norms import I,S,T,TARGET
from scripts.shared_discourse import empty
from scripts.shared_readings import num

OUT=ROOT/'output/visible-scope-library-v1'
SOURCE='examples/v016/visible-scoped-language-v1.noema'


@lru_cache(maxsize=1)
def vocabulary():return ScopeVocabulary()
def new_names():return list(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))['spellings'])
def doc(names,statements=()):
    d=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(names),statements=[])))
    d['statements']=list(statements)
    return normalize_document(d)
def asserted(body):return dict(kind='assert',body=body)


def norms_example():
    description=dict(kind='quote',body=lam([('person',I),('activity',I)],content(truth(False))))
    rule=lam(TARGET,v('polarity'))
    args=[v('person')]*4+[description,truth(True),v('world'),rule,rule]
    body=allof(call('permissionclear',*args),call('normrequired',*args),call('normviolated',*args),
               op('not',call('normfulfilled',*args)))
    body=q('forall','person',I,q('forall','world',S,body))
    return doc(['permissionclear','normrequired','normviolated','normfulfilled'],[asserted(body)])


def comparisons_example():
    antecedent=lam([('point',S)],op('not',op('equal',v('point'),v('actual'))))
    consequence=lam([('point',S)],op('equal',v('point'),v('success')))
    eligible=lam([('base',S),('candidate',S)],op('not',op('equal',v('base'),v('candidate'))))
    closer=lam([('base',S),('left',S),('right',S)],truth(False))
    args=[v('actual'),antecedent,consequence,eligible,closer]
    distinct=allof(*(op('not',op('equal',v(a),v(b))) for a,b in (('actual','success'),('actual','failure'),('success','failure'))))
    body=op('implies',distinct,op('and',op('not',call('orderedconditional',*args)),call('orderedmight',*args)))
    for name in ('failure','success','actual'):body=q('forall',name,S,body)
    return doc(['orderedconditional','orderedmight'],[asserted(body)])


def introduction():return call('introducereferent',lam([('person',I),('scene',S)],truth(True)))
def narrowed():
    test=call('discoursetest',call('referenttest',num(0),lam([('person',I),('scene',S)],op('equal',v('person'),v('known')))))
    return call('sequencediscourse',introduction(),test)
def scope_example():
    chain=narrowed()
    checks=[call('discourseholds',chain,empty(),v('world')),call('discourseunique',chain,empty(),num(0),v('world')),
            call('discourseidentified',chain,empty(),num(0),v('known'),v('world'))]
    body=q('forall','known',I,q('forall','world',S,allof(*checks)))
    return doc(['introducereferent','discoursetest','referenttest','sequencediscourse','discourseholds',
                'discourseunique','discourseidentified'],[asserted(body)])


def boundaries_example():
    closed=call('closeddiscourse',introduction())
    consequent=call('discoursetest',call('referenttest',num(0),lam([('person',I),('scene',S)],op('equal',v('person'),v('known')))))
    conditional=call('conditionaldiscourse',introduction(),consequent)
    other=q('exists','other',I,op('not',op('equal',v('known'),v('other'))))
    body=allof(call('discourseholds',closed,empty(),v('world')),
        op('not',call('discoursecandidate',closed,empty(),num(0),v('known'),v('world'))),
        op('implies',other,op('not',call('discourseholds',conditional,empty(),v('world')))))
    body=q('forall','known',I,q('forall','world',S,body))
    return doc(['closeddiscourse','introducereferent','conditionaldiscourse','discoursetest','referenttest',
                'discourseholds','discoursecandidate'],[asserted(body)])


def questions_example():
    question=call('referentquestion',introduction(),empty(),num(0),v('world'))
    match=dict(kind='answer_matches',question=question,arguments=[v('person')])
    query=dict(kind='question',function=lam([('person',I),('world',S)],match))
    # The inner question retains the same discourse and reference index. The
    # outer question supplies an explicit world instead of inventing a constant.
    return doc(['referentquestion','introducereferent'],[dict(kind='ask',body=query)])


@lru_cache(maxsize=1)
def cases():
    v=vocabulary();old=CompoundVocabulary()
    examples=[('dictionary-existing',doc(old._order)),('dictionary-added',doc(new_names())),
              ('norms',norms_example()),('comparisons',comparisons_example()),('referents',scope_example()),
              ('boundaries',boundaries_example()),('questions',questions_example())]
    rows=[]
    for label,native in examples:
        encoded=v.encode(native);page=compile_page(encoded,v,max_width=3200.)
        svg=to_svg(page['shapes']);decoded=decode_page(from_svg(svg))['document']
        if decoded!=encoded or v.decode_names(decoded)!=native:raise ValueError('Visible scope document differs: '+label)
        budget=1000000 if label=='comparisons' else 100000
        result=[] if label.startswith('dictionary') else evaluate_document(decoded,individuals=('a','b'),
            situations=('now','left','right'),primitives={},max_steps=budget)
        if result and label!='questions' and not all(r['value'] for r in result):raise ValueError('Visible scope meaning differs: '+label)
        if label=='questions' and result!=[dict(kind='ask',answers=[[i,w] for i in ('a','b') for w in ('now','left','right')])]:
            raise ValueError('Visible typed question differs')
        rows.append(dict(label=label,native=native,encoded=encoded,page=page,svg=svg,result=result,evaluation_max_steps=budget))
    return rows


@lru_cache(maxsize=1)
def word_checks():
    rows=[];v=vocabulary()
    def evaluation_rank(node):
        if isinstance(node,list):return max((evaluation_rank(x) for x in node),default=0)
        if not isinstance(node,dict):return 0
        own=node.get('rank',0)+1 if node.get('kind')=='disquote' else 0
        return max(own,max((evaluation_rank(x) for x in node.values()),default=0))
    for name in new_names():
        d=v.declaration(name);imports=v.imports([name])
        args=[dict(kind='variable',name='arg'+chr(97+i)) for i,p in enumerate(d['parameters'])]
        invocation=dict(kind='call',symbol=d['name'],arguments=args);body=op('equal',invocation,invocation)
        for arg,p in reversed(list(zip(args,d['parameters']))):body=q('forall',arg['name'],p['sort'],body)
        # Imports include the complete transitive dependency closure, so the
        # greatest explicit disquote rank there also covers referenced bodies.
        rank=evaluation_rank(imports)
        quoted=dict(kind='quote',body=dict(kind='function_ref',symbol=d['name']),**({'rank':rank} if rank else {}))
        document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=imports,
            statements=[asserted(body),asserted(op('equal',quoted,quoted))]))
        w=PublicWriter(v);w.document(document);shapes=render(w.glyphs)['shapes']
        if decode_document(from_svg(to_svg(shapes)),v)!=document:raise ValueError('Typed public call differs: '+name)
        rows.append(dict(name=name,parts=list(v.word(name).parts),glyphs=len(w.glyphs),shapes=len(shapes),quote_rank=rank,
                         dependency_imports=len(document['declarations'])))
    return rows


def prepare():
    from PIL import Image,ImageDraw
    OUT.mkdir(parents=True,exist_ok=True)
    text=format_graph(scope_example())+'\n';target=ROOT/SOURCE
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
        canvas.save(OUT/('scope-forms-'+str(start//10+1)+'.png'))


def build_report():
    if parse((ROOT/SOURCE).read_text(encoding='utf-8'))!=scope_example():raise ValueError('Published source differs')
    result=dict(schema='noema-visible-scope-library-evidence-1',edition=4,root_words=30,shared_compounds=90,
        shared_definitions=104,new_primitives=0,new_single_glyphs=0,typed_call_shape_decoding=word_checks(),
        shape_decoding=[dict(label=r['label'],rows=r['page']['rows'],shapes=len(r['page']['shapes']),result=r['result'],
            evaluation_max_steps=r['evaluation_max_steps'],
            svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in cases()])
    # Preserve the previous report's public-library dependencies rather than
    # copying or editing its judgments. Hash them again in this new evidence.
    preserved=['reports/visible-compound-library-v1.json','reports/shared-norms-v1.json','reports/shared-discourse-v1.json']
    paths=[*preserved,MANIFEST,SOURCE,'docs/visible-scope-library-v1.md','scripts/visible_scope_vocabulary.py',
        'scripts/visible_language_page.py','scripts/check_visible_scope_library.py','tests/test_visible_scope_library.py',
        'scripts/shared_norms.py','scripts/shared_discourse.py']
    for module in MODULES:paths.extend(module.values())
    for report in preserved:
        prior=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256']
        paths.extend(prior)
        for p,digest in prior.items():
            if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest:raise ValueError('Preserved evidence changed: '+p)
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=['Forty typed calls and seven documents decode circle/line SVG; typed identities do not evaluate higher-order domains',
        'Dictionary inventory is shown in two independently framed documents; resource limits are unchanged',
        'No raster OCR or third-party reading result; complete paper conversion remains unfinished']
    return result
