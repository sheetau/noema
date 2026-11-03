"""Visible quotation construction, lifting and type-directed disquotation."""
from functools import lru_cache
import hashlib

from noema.constructed_discourse import description_sort,function_sort
from scripts.check_kant_function_application import fixture,ref,apply,abstraction,pins as prior_pins
from scripts.check_kant_shared_application_branches import preserved,preserved_rows
from scripts.check_visible_syntax import call,logic,quant,variable,quote
from scripts.check_kant_public_fragment import canonical
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_page_public_context import ROOT
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report

OUT=ROOT/'output/kant-quotation-operations'
RUN=ROOT/'.noema-project/runs/kant-quotation-operations-v1'


def assemble(function,*arguments):return dict(kind='quoted_application',function=function,arguments=list(arguments))
def lift(description):return dict(kind='quoted_lift',description=description)
def disquote(description):return dict(kind='disquote',description=description)


@lru_cache(maxsize=1)
def cases():
    context,names=fixture();a,b=call('aki'),call('nao');book=call('book')
    unary=function_sort(['individual'],'truth')
    two=abstraction([('x','individual'),('y','individual')],call('above',variable('x'),variable('y')))
    factory=dict(kind='function_ref',symbol=names[0])
    returned=assemble(quote(factory))
    rows=[
        ('two-arguments','引用された関数へ二つの引用を組み立てる',disquote(assemble(quote(ref('above')),quote(a),quote(b)))),
        ('exchanged','二つの引用引数を交換する',disquote(assemble(quote(ref('above')),quote(b),quote(a)))),
        ('zero-arguments','無引数の関数から記述を作り、解く',call('red',disquote(assemble(quote(ref('book')))))),
        ('three-arguments','三つの引用引数を同じ枝順で読む',disquote(assemble(quote(ref('give')),quote(a),quote(book),quote(b)))),
        ('lambda','引用されたラムダ式へ引用を適用する',disquote(assemble(quote(two),quote(a),quote(b)))),
        ('lift','引用を一段包む操作と入れ子の引用',logic('equal',lift(quote(book)),quote(quote(book)))),
        ('bound-description','外側で束縛した記述を組み立てに使う',quant('forall','q',
            disquote(assemble(quote(ref('red')),variable('q'))),description_sort('individual'))),
        ('bound-function-description','記述された関数変数から引数数を決める',quant('forall','f',
            disquote(assemble(variable('f'),quote(book))),description_sort(unary))),
        ('mixed-ranks','関数と引数の最大順位を結果に引き継ぐ',disquote(assemble(quote(ref('red'),1),quote(book,2)))),
        ('lower-rank','順位一の引用内で順位零の記述を解く',logic('equal',quote(disquote(quote(call('red',book))),1),quote(call('red',book),1))),
        ('lift-binding','引用の持ち上げは外側の記述束縛を保持する',quant('forall','q',
            logic('equal',disquote(lift(variable('q'))),variable('q')),description_sort('individual'))),
        ('returned-function','引用適用の結果の関数記述へさらに適用する',disquote(assemble(returned,quote(book)))),
        ('ordinary-application','解いた関数を通常の関数適用に使う',apply(disquote(quote(ref('red'))),book)),
        ('normal-returned-description','通常の適用が返した関数記述を使う',disquote(assemble(apply(abstraction([],returned)),quote(book)))),
        ('constructed-argument','組み立てた記述を別の引用適用へ渡す',disquote(assemble(quote(ref('red')),assemble(quote(ref('book')))))),
        ('lifted-rank','持ち上げた順位二の記述を二段解く',call('red',disquote(disquote(lift(quote(book,2))))))]
    with use_context(context):return [(key,label,canonical(body)) for key,label,body in rows]


@lru_cache(maxsize=20)
def checked(index):
    context,_=fixture();key,label,source=cases()[index]
    drawing=compile_statement(source,lexicon=context,multiple=True);svg=to_svg(drawing['shapes'])
    if decode(list(reversed(from_svg(svg))),lexicon=LexicalContext.from_published(context.published()))!=source:
        raise ValueError('Quotation operation changed native syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        syntax_sha256=syntax_hash(source),branch_limits=drawing['branch_limits'],
        unbranched_paths=drawing['unbranched_paths'],**measure(svg))


def pins():
    result=prior_pins()
    for name in ('scripts/check_kant_quotation_operations.py','tests/test_kant_quotation_operations.py',
                 'docs/kant-quotation-operations.md'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,
        preserved=preserved,preserved_count=len(preserved_rows()),schema='kant-quotation-operations-1',version=VERSION,
        title='引用の組み立て・持ち上げ・復号',
        intro='公開型と実際の円・線から引数数と引用順位を復元します。新しい三字形は、小円中心が大円円周上にある上下段の配置です。',
        limits=['Quotation operators and three additional legal circle placements; full writing system and visual approval remain incomplete'])


def build_report():return diagnostic_report(OUT,pins)
