"""Closed expression branches: small contrasts and the actual 40-sentence page."""
from functools import lru_cache
import hashlib,json,time

from scripts.check_kant_typed_binders import pins as old_pins
from scripts.check_kant_binding_scope import ROOT,preserved
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report
from scripts.check_kant_terminal_words import prepare_trial,build_report as page_report
from scripts.kant_page_public_context import inputs,framing_context
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_lexicon import vocabulary
from scripts.visible_word_forms import Word,symbol
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call,logic,quant,variable,quote
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_syntax_geometry import to_svg,from_svg

OUT=ROOT/'output/kant-expression-branches-v2'
BASELINE='reports/kant-lexical-contact-v1.json'
RUN=ROOT/'.noema-project/runs/kant-expression-branches-v2'


def fixture():
    names=[symbol(Word('compound',parts),vocabulary()) for parts in (
        ('red','book','treeone'),('round','book','treeone'),('above','book','treeone'))]
    declarations=[
        dict(kind='definition',name=names[0],parameters=[dict(name='x',sort='individual')],result='truth',body=call('red',variable('x'))),
        dict(kind='definition',name=names[1],parameters=[],result='individual',body=call('book')),
        dict(kind='definition',name=names[2],parameters=[dict(name=n,sort='individual') for n in ('x','y')],result='truth',body=call('above',variable('x'),variable('y'))),
    ]
    ctx=LexicalContext(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]),
        declared_spellings={n:dict(parts=list(p),meaning_ja=m) for n,p,m in zip(names,
            [('book','aki'),('book','aki','book'),('book','nao')],
            ['既存のred述語。','既存のbookを指す名。','既存のabove関係。'])})
    def apply(i,*args):return dict(kind='call',symbol=names[i],arguments=list(args))
    return ctx,apply


@lru_cache(maxsize=1)
def cases():
    ctx,f=fixture();rows=[]
    for variant in ('word-boundary','nested-logic','argument-order','quoted','bound'):
        rhs=f(0,call('book'))
        if variant=='nested-logic':rhs=logic('and',rhs,logic('not',f(2,call('aki'),call('nao'))))
        if variant=='argument-order':rhs=f(2,call('nao'),call('aki'))
        if variant=='bound':rhs=f(0,variable('x'))
        body=logic('or',call('rain',call('town')),rhs)
        if variant=='bound':body=quant('forall','x',body)
        if variant=='quoted':body=logic('equal',quote(body),quote(body))
        rows.append((variant,variant,body))
    rows += [
        ('large-predicate','大円を含む述語の部分式',logic('and',call('rain',call('home')),call('above',call('birdone'),call('treeone')))),
        ('large-quote','引用全体を一つの枝にする',logic('equal',quote(call('home')),quote(call('book')))),
        ('large-binders','枝の引用内で束縛を閉じる',logic('equal',quote(quant('forall','x',call('rain',variable('x')))),
            quote(quant('exists','x',call('red',variable('x')))))),
        ('final-compound','枝末の複合語と語内接触',logic('or',call('rain',call('home')),f(0,f(1)))),
    ]
    with use_context(ctx):return [(key,label,canonical(body)) for key,label,body in rows]


@lru_cache(maxsize=20)
def checked(index):
    ctx,_=fixture();reader=LexicalContext.from_published(ctx.published())
    key,label,source=cases()[index]
    drawings=[compile_statement(source,lexicon=ctx,subexpressions=enabled) for enabled in (True,False)]
    svgs=[to_svg(g['shapes']) for g in drawings]
    for svg in svgs:
        if decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:raise ValueError('Branch changed syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svgs[0],
        width=drawings[0]['width'],previous_width=drawings[1]['width'],
        expression_branches=sum(g['expression_branch'] for g in drawings[0]['groups']),
        unbranched_paths=drawings[0]['unbranched_paths'],
        syntax_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest())


@lru_cache(maxsize=1)
def reader():return LexicalContext.from_published(framing_context().published())


@lru_cache(maxsize=40)
def actual(index):
    row=inputs()['selected'][index];started=time.perf_counter()
    drawing=compile_statement(row['public'],lexicon=framing_context())
    svg=to_svg(drawing['shapes']);shapes=from_svg(svg)
    recovered=decode(shapes,lexicon=reader())
    if recovered!=row['public']:raise ValueError('Page expression branch changed native syntax')
    geometry=read_geometry(shapes)
    flow=decompose_flow(geometry,terminal_words=True,branch_seams=True,large_branches=True)
    return dict(statement=row['statement'],status='matched',svg=svg,
        circles=sum(s['kind']=='circle' for s in shapes),width=drawing['width'],
        main_nuclei=len(flow['main']),branch_lengths=[len(s) for s in flow['side'] if s],
        expression_branches=sum(g['expression_branch'] for g in drawing['groups']),
        unbranched_paths=drawing['unbranched_paths'],
        lexical_contacts=sum(r['kind']=='tangent' for r in geometry['relations']),
        seconds=round(time.perf_counter()-started,3),
        syntax_sha256=hashlib.sha256(json.dumps(recovered,sort_keys=True).encode()).hexdigest())


def pins():
    result=old_pins()
    names=['scripts/check_kant_expression_branches.py','tests/test_kant_expression_branches.py',BASELINE]
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT/'diagnostics',run_path=RUN.with_name(RUN.name+'-diagnostics'),pins=pins,
        cases=cases,checked=checked,preserved=preserved,preserved_count=40,
        schema='kant-expression-branch-diagnostics-1',version=VERSION,title='部分式の枝の復号例',
        intro='主列と枝で同じ前置式を読み、枝ではちょうど一式を読み終えます。語境界・引数順・引用・束縛を保持します。検査用の見本であり、外観の固定候補ではありません。',
        limits=['Branches are linear prefix expressions; recursively forking side flows remain',
                'No visual freeze, page decoding or new semantic judgment'])
    prepare_trial(out=OUT,baseline=BASELINE,run_path=RUN,pin_function=pins,case_function=actual,
        schema='kant-expression-branches-1',context_factory=framing_context,reader_factory=reader,
        lexical_limit='One complete prefix expression per side branch; nested side forks remain',
        title='元の40文を部分式の枝で組む',intro='公開型で決まる引数位置の部分式を枝に置きます。大円を含む枝の外側は既定の45度線で通り、合法な接続を作れない枝は同じ構文のまま主列へ戻します。')


def build_report():
    page=page_report(out=OUT,pin_function=pins)
    diagnostics=diagnostic_report(OUT/'diagnostics',pins)
    page['diagnostics']=diagnostics['diagnostics']
    page['preserved_svg_syntax']=diagnostics['preserved_svg_syntax']
    page['source_sha256'].update(diagnostics['source_sha256'])
    page['limits']=['Linear complete-expression branches, including large circles, quotations and binders',
        'Shared fusion remains terminal; no nested physical side forks or multiple side slots yet',
        'No page decoding, new semantic judgment or visual freeze']
    if not any(c['expression_branches'] for c in page['cases']):raise ValueError('No page expression branch exercised')
    return page
