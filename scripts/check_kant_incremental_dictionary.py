"""Unknown names and dependency order from individually bounded geometry items."""
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from noema.constructed_discourse import normalize_document,function_sort
from scripts import kant_public_fragment as writing,kant_incremental_dictionary as document
from scripts import check_kant_type_references as previous
from scripts.check_kant_function_definition_body import DICTIONARY,BASELINE
from scripts.kant_page_public_context import ROOT,BRIDGE
from scripts.shared_modality import renamed
from scripts.check_visible_syntax import call,logic,variable,quant
from scripts.visible_word_forms import Word,symbol
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-incremental-dictionary'
RUN=ROOT/'.noema-project/runs/kant-incremental-dictionary-v2'


def name(*parts):return symbol(Word('compound',parts),writing.vocabulary())
def invoke(n,*args):return dict(kind='call',symbol=n,arguments=list(args))
def primitive(n,parameters,result):return dict(kind='primitive',name=n,parameters=parameters,result=result)
def definition(n,parameters,result,body):return dict(kind='definition',name=n,
    parameters=[dict(name=p,sort=t) for p,t in parameters],result=result,body=body)


def canonical(declarations,statements):
    names={d['name'] for d in declarations}
    used=writing.used_words([declarations,statements])-names
    deps=writing.declarations_for(tuple(sorted(used)))
    doc=normalize_document(dict(document.empty_document(),declarations=[*deps,*declarations],statements=statements))
    doc['declarations']=doc['declarations'][len(deps):]
    return doc


@lru_cache(maxsize=1)
def actual():
    baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for path in (DICTIONARY,BRIDGE):
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=baseline['source_sha256'][path]:
            raise ValueError('Saved source dictionary changed')
    published=json.loads((ROOT/DICTIONARY).read_text(encoding='utf-8'))
    bridge=json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'));rows=[]
    for original in ('dg','rqye'):
        source=next(d for d in bridge['source_declarations'] if d['name']==original)
        target=next(d for d in published['native']['declarations'] if d['name']==bridge['mapping'][original])
        if renamed(source,bridge['mapping'])!=target:raise ValueError('Source declaration/name bridge mismatch')
        rows.append(target)
    return rows


@lru_cache(maxsize=1)
def cases():
    p=name('book','town','book','town');q=name('book','town','book','town','book')
    v=variable;book=call('book');town=call('town')
    a=lambda body:dict(kind='assert',body=body)
    relation=primitive(p,['individual'],'truth')
    alias=definition(q,[('x','individual')],'truth',invoke(p,v('x')))
    ds=actual();term=invoke(ds[-1]['name'],book)
    rows=[
        ('new-primitive','未知の完全名を読む',[relation],[]),
        ('dependency-chain','復号済み原始語を定義と文から参照する',[relation,alias],[a(invoke(q,book))]),
        ('nullary','引数のない定義から次の定義へ',[definition(p,[],'individual',book),
            definition(q,[],'truth',call('red',invoke(p)))],[a(invoke(q))]),
        ('ordered-arguments','宣言を越えて引数の交換を保持する',[primitive(p,['individual','individual'],'truth'),
            definition(q,[('x','individual'),('y','individual')],'truth',invoke(p,v('y'),v('x')))],[dict(kind='ask',body=invoke(q,book,town))]),
        ('prefix-collision','完全名が別名の接頭部でも語を分ける',[primitive(p,[],'individual'),primitive(q,[],'individual')],
            [a(logic('equal',invoke(p),invoke(q)))]),
        ('assumption','追加した語を仮定の内側で読む',[relation,alias],[dict(kind='suppose',condition=invoke(p,book),
            statements=[dict(kind='ask',body=invoke(q,town)),a(invoke(p,town))])]),
        ('saved-dependencies','保存宣言 dg → rqye を順に読む',ds,[a(logic('equal',term,term))]),
    ]
    result=[]
    seed=document.Reader()
    for key,label,decls,statements in rows:
        if any(d['name'] in seed.context.declarations for d in decls):raise ValueError('Fixture target already in public seed')
        result.append((key,label,canonical(decls,statements)))
    return result


def stacked(items):
    shapes=[];bottom=0.
    for index,svg in enumerate(items):
        parts=from_svg(svg)
        low=min(s['y']-s['r'] if s['kind']=='circle' else min(s['y1'],s['y2']) for s in parts)
        high=max(s['y']+s['r'] if s['kind']=='circle' else max(s['y1'],s['y2']) for s in parts)
        dy=bottom-low
        for s in parts:
            s=dict(s)
            for key in ('y',) if s['kind']=='circle' else ('y1','y2'):s[key]+=dy
            shapes.append(s)
        bottom+=high-low+128
    return to_svg(shapes)


@lru_cache(maxsize=8)
def checked(index):
    key,label,source=cases()[index]
    drawings=document.compile_items(source,multiple=True)
    items=[to_svg(d['shapes']) for d in drawings]
    recovered=document.decode_items([list(reversed(from_svg(svg))) for svg in items])
    if recovered!=source:raise ValueError('Incremental reading changed native document: '+key)
    return dict(key=key,label=label,source=source,svg=stacked(items),width=max(d['width'] for d in drawings),
        syntax_sha256=syntax_hash(source),item_svgs=items,items=len(items),
        new_declarations=len(source['declarations']),statements=len(source['statements']),
        input_boundaries='Ordered separately bounded SVG items; not page segmentation',
        circles=sum(measure(svg)['circles'] for svg in items),branches=sum(measure(svg)['branches'] for svg in items),
        branch_limits=[d.get('branch_limits',[]) for d in drawings],unbranched_paths=[d.get('unbranched_paths',[]) for d in drawings])


def pins():
    result=previous.pins()
    for path in ('scripts/kant_incremental_dictionary.py','scripts/check_kant_incremental_dictionary.py',
                 'tests/test_kant_incremental_dictionary.py','docs/kant-incremental-dictionary.md',DICTIONARY,BASELINE,BRIDGE):
        result[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=previous.preserved,
        preserved_count=len(previous.preserved_rows()),schema='kant-incremental-dictionary-1',version=writing.VERSION,
        title='未登録の綴りと宣言を順に読む',intro='公開基礎辞書だけから始め、各項目の図形を読み終えるごとに語を登録します。項目境界は入力で与えています。',
        limits=['Item sequence with supplied boundaries/order; page boundaries are not reconstructed',
                'Actual saved declarations retained; trailing equality is a structural diagnostic, not a new source claim',
                'Aliases, public meaning text, full dictionary/page integration and visual approval remain'])


def build_report():return report(OUT,pins)
