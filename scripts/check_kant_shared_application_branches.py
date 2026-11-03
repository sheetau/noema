"""Visible branches of predicates whose public context argument is shared."""
from functools import lru_cache
import hashlib,json

from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_lexicon import vocabulary
from scripts.visible_word_forms import Word,symbol
from scripts.check_visible_syntax import call,logic,quant,variable,quote
from scripts.check_kant_public_fragment import canonical
from scripts.kant_public_fragment import compile_statement,decode,events,event_sides,VERSION
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.check_kant_compound_fans import pins as prior_pins
from scripts.kant_page_public_context import ROOT
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report

OUT=ROOT/'output/kant-shared-application-branches'
RUN=ROOT/'.noema-project/runs/kant-shared-application-branches-v1'


@lru_cache(maxsize=1)
def fixture():
    names=[symbol(Word('compound',(r,'treeone','book','fruit')),vocabulary()) for r in ('red','round','above','rain')]
    orders=[('s','a','b','c'),('a','s','b','c'),('a','b','s'),('s','a','t','b','c')]
    bodies=[call('give',*(variable(n) for n in 'abc')),call('give',*(variable(n) for n in 'cba')),
            call('above',variable('a'),variable('b')),
            logic('and',call('give',*(variable(n) for n in 'abc')),logic('equal',variable('s'),variable('t')))]
    declarations=[dict(kind='definition',name=n,
        parameters=[dict(name=p,sort='situation' if p in ('s','t') else 'individual') for p in order],
        result='truth',body=body) for n,order,body in zip(names,orders,bodies)]
    parts=[['aki','book'],['nao','book'],['book','aki'],['book','nao']]
    meanings=['give(a,b,c)を返す共有位置の検査用定義。sは本体で使わない。',
              'give(c,b,a)を返す共有位置の検査用定義。sは本体で使わない。',
              'above(a,b)を返す共有位置の検査用定義。sは本体で使わない。',
              'give(a,b,c)と二状況s,tの同一性を連言する。']
    context=LexicalContext(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]),
        declared_spellings={n:dict(parts=p,meaning_ja=m) for n,p,m in zip(names,parts,meanings)})
    def apply(i,*args):return dict(kind='call',symbol=names[i],arguments=list(args))
    return context,apply,names


@lru_cache(maxsize=1)
def cases():
    context,f,_=fixture();s=variable('s');a,b,c=call('aki'),call('book'),call('nao')
    close=lambda body:quant('forall','s',body,'situation')
    pair=lambda first,last:logic('and',f(0,s,first,b,last),f(1,call('home'),s,c,b))
    rows=[('first-middle','第一・第二位置の状況を共有し、各述語に二枝を付ける',close(pair(a,c))),
        ('exchanged','第一述語の主体と受け手を交換する',close(pair(c,a))),
        ('different-arity','共有位置と引数数の異なる二述語',close(logic('and',f(0,s,a,b,c),f(2,c,a,s)))),
        ('bound','共有状況の外側にある個体の束縛を参照',quant('forall','x',
            close(logic('and',f(0,s,variable('x'),b,c),f(1,call('home'),s,c,variable('x')))))),
        ('quoted','引用ごとに共有状況と枝の束縛を閉じる',logic('equal',quote(close(pair(a,c))),quote(close(pair(c,a))))),
        ('last-situation','複数の状況引数のうち最後を共有する',quant('forall','s',quant('forall','t',
            logic('and',f(3,s,a,variable('t'),b,c),f(1,call('home'),variable('t'),c,b)),'situation'),'situation'))]
    with use_context(context):return [(key,label,canonical(body)) for key,label,body in rows]


def shared_heads(stream):
    return sum(e['token']=='and_shared' for e in stream)+sum(shared_heads(side)
        for e in stream for side in event_sides(e) if isinstance(side,list))


@lru_cache(maxsize=8)
def checked(index):
    context,_,_=fixture();key,label,source=cases()[index]
    drawing=compile_statement(source,lexicon=context,multiple=True)
    svg=to_svg(drawing['shapes']);reader=LexicalContext.from_published(context.published())
    if decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:
        raise ValueError('Shared application branches changed syntax: '+key)
    with use_context(context):heads=shared_heads(events(source,multiple=True))
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        syntax_sha256=syntax_hash(source),shared_heads=heads,branch_limits=drawing['branch_limits'],
        unbranched_paths=drawing['unbranched_paths'],**measure(svg))


@lru_cache(maxsize=1)
def preserved_rows():
    report='reports/kant-compound-fan-page-v2.json'
    row=json.loads((ROOT/report).read_text(encoding='utf-8'))['diagnostics'][0]
    shared_report='reports/kant-presentation-spellings-v1.json'
    shared=next(r for r in json.loads((ROOT/shared_report).read_text(encoding='utf-8'))['cases'] if r['statement']==13)
    return [('output/kant-compound-fan-page-v2/statement-1.svg',row['syntax_sha256'],report),
            ('output/kant-presentation-spellings/statement-13.svg',shared['syntax_sha256'],shared_report)]


def preserved(index):
    from scripts.kant_presentation_context import presentation_context
    path,expected,report=preserved_rows()[index]
    prior=json.loads((ROOT/report).read_text(encoding='utf-8'));raw=(ROOT/path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=prior['source_sha256'][path]:raise ValueError('Preserved SVG changed')
    result=decode(from_svg(raw.decode('utf-8')),lexicon=LexicalContext.from_published(presentation_context().published()))
    if syntax_hash(result)!=expected:raise ValueError('Previous seven-branch syntax changed')
    return dict(svg=path,syntax_sha256=expected)


def pins():
    result=prior_pins()
    names={'scripts/check_kant_shared_application_branches.py','tests/test_kant_shared_application_branches.py',
           'docs/kant-shared-context.md'}
    for path,_,report in preserved_rows():names.update((path,report))
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,
        preserved=preserved,preserved_count=len(preserved_rows()),schema='kant-shared-application-branches-1',version=VERSION,
        title='共有した述語の引数も枝にする',
        intro='共有済みの引数位置を除き、残る引数を通常の公開順序で枝と本文へ配置します。元の語義・引数順・引用・束縛を維持する試作です。',
        limits=['Independent shared-application examples; page integration and visual completion remain'])


def build_report():return diagnostic_report(OUT,pins)
