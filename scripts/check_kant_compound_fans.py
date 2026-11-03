"""Keep a fan's compound words together without changing the public reader."""
from functools import lru_cache
import hashlib

from scripts.check_kant_multiple_arguments import fixture as fan_fixture, measure, syntax_hash
from scripts.check_kant_nested_branches import fixture as nested_fixture
from scripts.check_visible_syntax import call, logic, quant, variable, quote
from scripts.check_kant_public_fragment import canonical
from scripts.kant_lexical_context import LexicalContext, use_context
from scripts.kant_public_fragment import compile_statement, decode, VERSION
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.kant_structural_trial import prepare as diagnostic_trial, report as diagnostic_report
from scripts.check_kant_multiple_arguments import pins as prior_pins
from scripts.kant_page_public_context import ROOT

OUT=ROOT/'output/kant-compound-fans'
RUN=ROOT/'.noema-project/runs/kant-compound-fans-v3'


@lru_cache(maxsize=1)
def fixture():
    base,names=fan_fixture();nested,f,select=nested_fixture()
    context=LexicalContext(dict(base.document,
        declarations=base.document['declarations']+nested.document['declarations']),
        declared_spellings=base.declared_spellings|nested.declared_spellings)
    def four(*args):return dict(kind='call',symbol=names[-1],arguments=list(args))
    return context,four,lambda:f(1),select


@lru_cache(maxsize=1)
def cases():
    context,four,book,select=fixture()
    rows=[
        ('four-compounds','三部品の語を四つの引数にする',four(*(book() for _ in range(4)))),
        ('give-compounds','渡す対象と受け手を複合語にする',call('give',call('aki'),book(),book())),
        ('bound-compounds','複合語の枝と外側の変数参照',quant('forall','x',four(book(),variable('x'),book(),book()))),
        ('quoted-compounds','引用内の複合語と複数枝',logic('equal',quote(call('give',call('aki'),book(),book())),quote(call('red',call('home'))))),
        ('nested-compounds','複数枝の内部にも引数の枝を置く',four(book(),book(),select(call('aki'),book()),book())),
    ]
    with use_context(context):return [(key,label,canonical(body)) for key,label,body in rows]


@lru_cache(maxsize=8)
def checked(index):
    context,*_=fixture();key,label,source=cases()[index]
    drawing=compile_statement(source,lexicon=context,multiple=True)
    svg=to_svg(drawing['shapes'])
    reader=LexicalContext.from_published(context.published())
    if decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:
        raise ValueError('Compound fan changed native syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        syntax_sha256=syntax_hash(source),branch_limits=drawing['branch_limits'],
        unbranched_paths=drawing['unbranched_paths'],**measure(svg))


def pins():
    result=prior_pins()
    for name in ('scripts/check_kant_compound_fans.py','tests/test_kant_compound_fans.py'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,
        preserved=lambda _:None,preserved_count=0,schema='kant-compound-fans-1',version=VERSION,
        title='複合語を含む複数枝の配置',
        intro='複合語を末尾まで配置してから別の枝へ移ります。公開の読順・語義・引数順は変更しません。本文全体への適用と外観の完成は別途確認します。',
        limits=['Compound fan diagnostics; not a completed page or a visual freeze'])


def build_report():
    return diagnostic_report(OUT,pins)
