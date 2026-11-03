"""Recover native situation-content binders from visible ink."""
from functools import lru_cache
import hashlib
from noema.constructed_discourse import function_sort
from scripts.check_visible_syntax import call,logic,quant,variable,quote
from scripts.check_kant_public_fragment import canonical
from scripts.check_kant_function_application import apply,abstraction
from scripts.check_kant_quotation_operations import assemble,disquote
from scripts.check_kant_shared_application_branches import preserved,preserved_rows
from scripts.check_kant_compact_type_lists import pins as prior_pins
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_page_public_context import ROOT
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report

OUT=ROOT/'output/kant-content-binding'
RUN=ROOT/'.noema-project/runs/kant-content-binding-v1'


def content(name,body):return dict(kind='content',variable=name,body=body)
def evaluate(value,situation):return dict(kind='evaluate',content=value,situation=situation)
def situation(name,body):return quant('forall',name,body,'situation')


@lru_cache(maxsize=1)
def cases():
    v=variable;book=call('book')
    same=lambda name:content(name,logic('equal',v(name),v(name)))
    at=lambda value:situation('s',evaluate(value,v('s')))
    two=lambda body:content('t',body)
    returning=abstraction([('x','individual')],content('t',call('red',v('x'))))
    rows=[
        ('local','内容の状況束縛を読む',at(same('t'))),
        ('outer-situation','内容から外側の状況を参照する',at(two(logic('equal',v('t'),v('s'))))),
        ('exchanged','内側と外側の状況の順序を交換する',at(two(logic('equal',v('s'),v('t'))))),
        ('outer-individual','外側の個体を内容本体へ保持する',quant('forall','x',at(two(call('red',v('x')))))),
        ('outer-function','外側の状況述語を内容内で適用する',quant('forall','f',at(two(apply(v('f'),v('t')))),function_sort(['situation'],'truth'))),
        ('nested','内容の入れ子で二つの状況を区別する',at(two(evaluate(content('u',logic('equal',v('t'),v('u'))),v('t'))))),
        ('quoted','引用ごとに内容の束縛を閉じる',logic('equal',quote(same('t')),quote(same('u')))),
        ('disquoted','引用を解いて得た内容を評価する',at(disquote(quote(same('t'))))),
        ('quote-inside','内容内の引用から戻った後に状況を参照する',at(two(logic('and',logic('equal',quote(book),quote(book)),logic('equal',v('t'),v('s')))))),
        ('returned','ラムダ式が返す内容を評価する',at(apply(returning,book))),
        ('quoted-application','引用適用が返す内容記述を解いて評価する',at(disquote(assemble(quote(returning),quote(book))))),
        ('siblings','隣の内容同士で束縛を引き継がない',logic('equal',same('s'),same('t'))),
        ('outward','個体と状況をまたいで外側の束縛へ戻る',quant('forall','x',at(two(quant('forall','y',quant('exists','u',
            logic('and',logic('equal',v('t'),v('u')),call('above',v('x'),v('y'))),'situation')))))),
    ]
    return [(key,label,canonical(body)) for key,label,body in rows]


@lru_cache(maxsize=20)
def checked(index):
    key,label,source=cases()[index]
    drawing=compile_statement(source,multiple=True);svg=to_svg(drawing['shapes'])
    if decode(list(reversed(from_svg(svg))))!=source:raise ValueError('Content binding changed native syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],syntax_sha256=syntax_hash(source),
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


def pins():
    result=prior_pins()
    for name in ('scripts/check_kant_content_binding.py','tests/test_kant_content_binding.py','docs/kant-content-binding.md',
                 'reports/kant-compact-type-lists-v2.json'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,
        preserved_count=len(preserved_rows()),schema='kant-content-binding-1',version=VERSION,
        title='状況を束縛して内容を作る',
        intro='contentは状況変数を一つ束縛し、外側の参照を保ちます。型を表す追加見出しは使わず、既存の引用・評価・関数適用へ接続します。',
        limits=['Content binders and their use in evaluation; document declarations, remaining expressions and visual completion are incomplete'])


def build_report():return diagnostic_report(OUT,pins)
