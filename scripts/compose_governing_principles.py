"""Represent a conditional principle separately from its normative adoption."""
from copy import deepcopy
import json
from noema.constructed import parse, format_graph
from scripts.compose_collective_conditional import ROOT, SOURCE as PARENT
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, app, both, op, quant, v
from scripts.compose_qualified_utterance import closure
from scripts.compose_policy_norms import DESCRIPTION, RULE, TRUE
from scripts.compose_collective_office import params, av

LIBRARY = 'examples/v016/governing-principles.noema'
SOURCE = 'examples/v016/kant-governing-principles.noema'
CORE = 'examples/v016/governing-principles-core.noema'
BASIS = 'data/governing-principles-basis-v1.json'
CONTENT = [('actor', 'a'), ('people', 'j[a]'), ('scope', 'h[a] c'),
    ('condition', 'h[a d] c'), ('treatment', 'h[a a d] c')]
ADOPTION = [('source', 'a'), ('actor', 'a'), ('office', 'a'), ('principle', DESCRIPTION),
    ('context', 'd'), ('required', RULE)]
CHANGE = ADOPTION[:4] + [('start', 'd'), ('end', 'd'), ('status', 'c'), ('required', RULE)]
COMPARE = [('first', DESCRIPTION), ('second', DESCRIPTION), ('probes', 'h[d] c')]
REPLACE = ADOPTION[:3] + COMPARE + [('start', 'd'), ('end', 'd'), ('required', RULE)]
ROOTS = ['rxv', 'rxw', 'rxx', 'rxy', 'rxz', 'rx2', 'rx3']
ADAPTERS = ['iaradoption', 'iarfulfillment', 'iarreplacement']


def actual(name, context):
    return op('t', app('s[' + v(name) + ']', 'l[a][]'), v(context))


def definitions():
    selected = app(v('scope'), v('person'))
    triggered = app(v('condition'), v('person'), v('context'))
    treatment = app(v('treatment'), v('actor'), v('person'), v('context'))
    inventory = k('rcm', v('people'), v('scope'))
    # A closed policy still has the existing j[a] -> e interface.  Its empty
    # outer bindings are checked rather than silently discarding extra inputs.
    rule = both(k('rdr', v('bindings'), 'n p a b'), inventory,
        quant('f', 'person', 'a', op('y', both(selected, triggered), treatment)))
    text = definition('rxv', params(CONTENT), 'i[bindings j[a]][b context[' + rule + ']]', 'h[j[a]] e')
    text += definition('rxw', params(CONTENT[:4] + [('context', 'd')]), both(inventory,
        quant('g', 'person', 'a', both(selected, triggered))))
    norm = app(v('required'), v('source'), v('actor'), v('office'), v('principle'),
        'l[a][]', TRUE, v('context'))
    text += definition('rxx', params(ADOPTION), norm)
    text += definition('rxy', params(ADOPTION), both(k('rxx', *av(ADOPTION)), actual('principle', 'context')))
    refs = dict(source=v('source'), person=v('actor'), role=v('office'), target=v('principle'),
        bindings='l[a][]', polarity=TRUE, start=v('start'), end=v('end'), status=v('status'),
        valid='i[bindings j[a]][k rdr[v bindings n p a b]]', relation=v('required'))
    from scripts.compose_normative_powers import EFFECT
    text += definition('rxz', params(CHANGE), k('riv', *[refs[n] for n, _ in EFFECT]))
    different = op('u', op('e', actual('first', 'candidate'), actual('second', 'candidate')))
    text += definition('rx2', params(COMPARE), quant('g', 'candidate', 'd',
        both(app(v('probes'), v('candidate')), different)))
    def change(which, status):
        return k('rxz', *[v(n) for n in ('source', 'actor', 'office')], v(which),
            v('start'), v('end'), status, v('required'))
    text += definition('rx3', params(REPLACE), both(change('first', op('u', TRUE)),
        change('second', TRUE), k('rx2', *av(COMPARE))))
    return text


def additions():
    text = ''
    for name, target, fields in (('iaradoption', 'rxx', ADOPTION),
            ('iarfulfillment', 'rxy', ADOPTION), ('iarreplacement', 'rx3', REPLACE)):
        text += definition(name, params(fields[:-1]), k(target, *av(fields[:-1]), 'p h7k'))
    return text


def build():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    lib = deepcopy(parent)
    lib['statements'] = []
    lib['declarations'] = closure(parent, ['rcm', 'rdr', 'riv'])
    lib = parse(format_graph(lib, 'compact') + definitions())
    doc = deepcopy(parent)
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions() + additions())
    doc['statements'] = statements
    core = deepcopy(doc)
    core['statements'] = []
    core['declarations'] = closure(doc, ROOTS + ADAPTERS)
    return {p: format_graph(d, 'compact') + '\n' for p, d in ((LIBRARY, lib), (SOURCE, doc), (CORE, core))}


def basis():
    return dict(status='conditional_principle_and_normative_replacement_scaffold', parent=PARENT, document=SOURCE,
        definitions={
            'rxv': '行為主体・非空の完全列挙された対象者・条件・扱いを組み合わせ、対象者が条件に該当するなら同じ主体がその扱いをするという一般原則の内容を作る。外側の引数列は空であることを検査する。',
            'rxw': '同じ対象範囲に、同じ文脈で原則の条件に該当する人が存在する。原則内容の成立から適用例の存在を導かないための別条件。',
            'rxx': '同じ規範源が同じ主体に同じ職務で、指定した原則内容を満たすよう要求する。規範上の採用を表す候補で、実行や原則の正当性を含めない。',
            'rxy': 'rxxの要求があり、同じ原則を空の引数列で適用した内容も同じ文脈で成立する。内容が全称条件なら、適用例のない履行もあり得る。',
            'rxz': '同じ規範源・主体・職務・原則記述について、異なる二状況の間で肯定内容への要求が指定の有無へ変わる。原則の肯否と要求の有無を混同しない。',
            'rx2': '指定された比較状況の中に、二つの原則内容の真偽が異なる例がある。比較は同じ状況と空の引数列を用いる。違う名前だけでは成立しない。',
            'rx3': '同じ規範源・主体・職務について、旧原則への要求が失われ新原則への要求が生じ、rx2の内容差の実例もある。追加採用や単なる改名とは異なる、要求の置換を表す強い候補。',
            'iaradoption/iarfulfillment/iarreplacement': '既存の記述付き要求関係h7kへ接続する。同じ規範源・主体・職務を全ての比較で保持し、新しい原始関係は追加しない。'},
        limitations=[
            '原則の候補を一般的な条件付き行為規範として構成する。信念、経験則、政策目標など全てのGrundsatzを義務へ還元する定義ではない。カントの語義をこの一候補へ確定していない。',
            '規範上の採用rxxは要求の存在である。採択行為や制度的な有効性、政府組織の定義、意思決定、権限、社会的承認、正当性は含まない。',
            'rxvの対象者と主体は閉じた記述の構成時に固定する。文脈によって変わる条件や扱いと、対象範囲そのものの交換を分ける。空の対象や不完全・重複のある列は受け付けないが、条件に該当する人がいない場合は一般原則を真とする。',
            '条件と扱いは型付きの関数引数であり、Noemaの定義を渡せる。尊厳に即した扱いの内容を未定義の関数名で完成扱いにしない。今回の有限例は条件付きの扱いの構造を検査するもので、尊厳の定義ではない。',
            'rx2の不成立は意味の同一性を証明しない。比較状況の不足や、両方とも偽となる全称内容の内側の違いを見逃し得る。異なる真偽の実例は十分な区別であり、完全な同義判定ではない。',
            '未知の比較内容は偽に補わない。採用rxxだけを確認する際は原則を実行しない。内容を評価する履行と比較は別操作である。',
            '前後状況は異なることだけを要求する。実際の時間的先後・変化の原因・制度上の移行をrxz/rx3だけから導かない。rx3は旧原則も残す追加や、同じ内容を再確認する更新とは別の形である。',
            '親の全宣言と全22主張を保存する。政府への作用、finallyに相当する時間関係、政府自身にとっての有益さ、機械との対比、尊厳、原文との意味一致は未完である。',
            '原文の追加の事実主張・原始記号・明示文字範囲は増やさない。言語の構成と有限例の確認を全文の意味確認として数えない。'])


def main():
    for name, body in (build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}).items():
        path = ROOT / name
        if path.exists():
            assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
        print(name, len(body))


if __name__ == '__main__':
    main()
