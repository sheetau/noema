"""Function application read from visible geometry and public function types."""
from functools import lru_cache
import hashlib

from noema.constructed_discourse import function_sort
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_lexicon import vocabulary
from scripts.visible_word_forms import Word,symbol
from scripts.check_visible_syntax import call,logic,quant,variable,quote
from scripts.check_kant_public_fragment import canonical
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.check_kant_shared_application_branches import pins as prior_pins,preserved,preserved_rows
from scripts.kant_page_public_context import ROOT
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report

OUT=ROOT/'output/kant-function-application'
RUN=ROOT/'.noema-project/runs/kant-function-application-v1'


def ref(name):return dict(kind='function_ref',symbol=call(name)['symbol'])
def apply(function,*args):return dict(kind='apply',function=function,arguments=list(args))
def abstraction(parameters,body):return dict(kind='lambda',parameters=[dict(name=n,sort=t) for n,t in parameters],body=body)


@lru_cache(maxsize=1)
def fixture():
    unary=function_sort(['individual'],'truth')
    names=[symbol(Word('compound',(r,'home','book','treeone')),vocabulary()) for r in ('red','round')]
    factory=dict(kind='definition',name=names[0],parameters=[],result=unary,body=ref('red'))
    conditions=[apply(variable(n),variable('x')) for n in 'fgh']
    combined=dict(kind='definition',name=names[1],parameters=[dict(name=n,sort=unary) for n in 'fgh'],
        result='truth',body=quant('forall','x',logic('and',conditions[0],logic('and',*conditions[1:]))))
    context=LexicalContext(dict(schema_version='0.16',lexicon_version='0.16',declarations=[factory,combined],statements=[]),
        declared_spellings={names[0]:dict(parts=['book','nao','aki'],meaning_ja='redの関数参照を返す無引数の定義。'),
            names[1]:dict(parts=['nao','book','aki'],meaning_ja='任意の個体に対して三つの単項述語が全て成立する。')})
    return context,names


@lru_cache(maxsize=1)
def cases():
    context,names=fixture();a,b=call('aki'),call('nao');book=call('book')
    two=abstraction([('x','individual'),('y','individual')],call('above',variable('x'),variable('y')))
    curried=abstraction([('x','individual')],abstraction([('y','individual')],call('above',variable('x'),variable('y'))))
    unary=function_sort(['individual'],'truth')
    rows=[
        ('zero-reference','無引数の関数参照を適用する',call('red',apply(ref('book')))),
        ('one-reference','単項述語の関数参照を適用する',apply(ref('red'),book)),
        ('two-reference','二引数を枝へ配置する',apply(ref('above'),a,b)),
        ('exchanged','二つの引数を交換する',apply(ref('above'),b,a)),
        ('three-reference','三引数を公開枝順で読む',apply(ref('give'),a,book,b)),
        ('zero-lambda','無引数のラムダ式を適用する',apply(abstraction([],call('red',book)))),
        ('two-lambda','二引数のラムダ式を適用する',apply(two,a,b)),
        ('bound-function','型付きの関数変数を適用する',quant('forall','f',apply(variable('f'),a,b),function_sort(['individual','individual'],'truth'))),
        ('outer-function','外側の関数束縛と内側の個体束縛',quant('forall','f',quant('forall','x',apply(variable('f'),variable('x'))),unary)),
        ('function-valued-call','関数を返す定義の値を適用する',apply(dict(kind='call',symbol=names[0],arguments=[]),book)),
        ('returned-application','適用の結果として返った関数をさらに適用する',apply(apply(dict(kind='function_ref',symbol=names[0])),book)),
        ('returned-lambda','外側の個体を保持したラムダ式の適用',apply(apply(curried,a),b)),
        ('quoted','引用ごとに関数内の束縛を閉じる',logic('equal',quote(apply(two,a,b)),quote(apply(two,b,a)))),
        ('function-argument','関数そのものを引数にする',apply(abstraction([('f',unary)],apply(variable('f'),book)),ref('red'))),
        ('binder-order','枝の配置順によらず三つのラムダ式を元の順序で読む',
            apply(dict(kind='function_ref',symbol=names[1]),
                *(abstraction([(n,'individual')],call(p,variable(n))) for n,p in zip('abc',('red','round','bird'))))),
    ]
    with use_context(context):return [(key,label,canonical(body)) for key,label,body in rows]


@lru_cache(maxsize=20)
def checked(index):
    context,_=fixture();key,label,source=cases()[index]
    drawing=compile_statement(source,lexicon=context,multiple=True)
    svg=to_svg(drawing['shapes']);reader=LexicalContext.from_published(context.published())
    if decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:
        raise ValueError('Visible application changed native syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        syntax_sha256=syntax_hash(source),branch_limits=drawing['branch_limits'],
        unbranched_paths=drawing['unbranched_paths'],**measure(svg))


def pins():
    result=prior_pins()
    for name in ('scripts/kant_function_grammar.py','scripts/check_kant_function_application.py',
                 'tests/test_kant_function_application.py','docs/kant-function-application.md'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,
        preserved=preserved,preserved_count=len(preserved_rows()),schema='kant-function-application-1',version=VERSION,
        title='関数の型から引数を読む',
        intro='関数を本文側で先に読み、公開型から引数数を確定して枝を読みます。関数を評価せず、元の適用・引用・束縛を復元する試作です。',
        limits=['Function application examples; declarations and remaining native constructors are not yet complete'])


def build_report():return diagnostic_report(OUT,pins)
