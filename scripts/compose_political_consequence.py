"""Connect later normative replacement to the same collective causal model."""
from copy import deepcopy
import json
from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_governing_principles import ROOT, SOURCE as PARENT, DESCRIPTION
from scripts.compose_joint_development import HIGH, STATE, EQUATIONS, CONTEXT, params, av, fixed
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, app, both, op, quant, v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY = 'examples/v016/political-consequence.noema'
SOURCE = 'examples/v016/kant-political-consequence.noema'
CORE = 'examples/v016/political-consequence-core.noema'
BASIS = 'data/political-consequence-basis-v1.json'
SCOPE = [('contributors', 'j[a]'), ('people', 'h[a] c'), ('factors', 'h[a] a'), ('variables', 'j[a]')]
FIELDS = SCOPE + [('equations', EQUATIONS), ('premise', 'h[a ' + STATE + '] c'),
    ('checked', 'h[' + STATE + '] c'), ('effect', 'h[' + STATE + '] c'), ('observed', STATE)]
GOV = [('source', 'a'), ('actor', 'a'), ('office', 'a'), ('first', DESCRIPTION), ('second', DESCRIPTION), ('probes', 'h[d] c')]
LOCAL = CONTEXT + GOV
REST = 'h[' + HIGH + ' a j[a] d d d d] c'
SCHEMA = [('reading', HIGH)] + GOV + [('remaining', REST)]


def definitions():
    selected = lambda person: app(v('people'), v(person))
    factor = lambda person: app(v('factors'), v(person))
    valid = quant('f', 'person', 'a', op('y', selected('person'), k('rz', v('variables'), factor('person'))))
    distinct = quant('f', 'left', 'a', quant('f', 'right', 'a', op('y',
        both(selected('left'), selected('right'), op('e', factor('left'), factor('right'))), op('e', v('left'), v('right')))))
    text = definition('rx4', params(SCOPE), both(k('rcm', v('contributors'), v('people')), valid, distinct))
    mask = 'i[variable a][' + quant('g', 'person', 'a', both(selected('person'), op('e', v('variable'), factor('person')))) + ']'
    matched = quant('f', 'person', 'a', op('y', selected('person'),
        op('z', app(v('premise'), v('person'), v('state')), app(v('state'), factor('person')))))
    def side(flag):
        effect = app(v('effect'), v('state'))
        return k('rw', v('variables'), v('equations'), mask, fixed(flag), 'i[state ' + STATE + '][' +
            both(app(v('checked'), v('state')), matched, effect if flag else op('u', effect)) + ']')
    actual = both(k('ru', v('variables'), v('equations'), fixed(False), fixed(False), v('observed')),
        quant('f', 'person', 'a', op('y', selected('person'), both(app(v('observed'), factor('person')),
            app(v('premise'), v('person'), v('observed'))))),
        app(v('checked'), v('observed')), app(v('effect'), v('observed')))
    text += definition('rx5', params(FIELDS), both(k('rx4', *av(SCOPE)), actual, side(False), side(True)))
    return text


def additions():
    text = ''.join(primitive('ias' + name, sort) for name, sort in (
        ('last', 'h[a d d ' + STATE + '] d'), ('normpoint', 'h[a d d ' + STATE + ' d] d'),
        ('reviewed', 'h[a a a ' + DESCRIPTION + ' d] c')))
    ctx = av(CONTEXT)
    state = v('state')
    start, end, last = [k(name, *ctx, state) for name in ('ianbegin', 'ianend', 'iaslast')]
    history = 'i[point d][' + k('ianhistory', *ctx, state, v('point')) + ']'
    before = 'i[left d right d][' + k('ianbefore', *ctx, state, v('left'), v('right')) + ']'
    normpoint = lambda point: k('iasnormpoint', *ctx, state, point)
    review = [k('iasreviewed', v('source'), v('actor'), v('office'), v(policy), normpoint(point))
        for policy in ('first', 'second') for point in (start, last)]
    checked = both(k('ta', history, before), *[app(history, point) for point in (start, end, last)],
        app(before, start, end), app(before, end, last), k('rx2', v('first'), v('second'), v('probes')), *review)
    text += definition('iaschecked', params(LOCAL) + ' state ' + STATE, checked)
    text += definition('iaseffect', params(LOCAL) + ' state ' + STATE,
        k('iarreplacement', *av(GOV), normpoint(start), normpoint(last)))
    people = 'i[person a][k iappeople[v community v person v start]]'
    bindings = dict(contributors=k('iapcontributors', v('community'), v('start')), people=people,
        factors='i[person a][' + k('iapfactors', *ctx, v('person')) + ']', variables=k('iapvariables', *ctx),
        equations='i[variable a state ' + STATE + '][' + k('iapequations', *ctx, v('variable'), state) + ']',
        premise='i[person a state ' + STATE + '][' + op('t', app('s[v reading]', v('person')), start) + ']',
        checked='i[state ' + STATE + '][' + k('iaschecked', *av(LOCAL), state) + ']',
        effect='i[state ' + STATE + '][' + k('iaseffect', *av(LOCAL), state) + ']', observed=k('iapobserved', *ctx))
    members = quant('f', 'person', 'a', op('y', app(people, v('person')), both(k('aa', v('person')),
        k('ianmembers', v('community'), v('person'), v('start')))))
    aligned = both(op('e', k('ianbegin', *ctx, bindings['observed']), v('start')),
        op('e', k('ianend', *ctx, bindings['observed']), v('end')))
    text += definition('iascausal', 'reading ' + HIGH + ' ' + params(LOCAL),
        both(members, aligned, k('rx5', *[bindings[n] for n, _ in FIELDS])))
    remaining = app(v('remaining'), v('reading'), v('community'), v('contributors'), v('anchor'), v('start'), v('end'),
        k('iaslast', *ctx, bindings['observed']))
    result = 'i[reading ' + HIGH + ' community a contributors j[a] anchor d start d end d][' + both(
        k('iascausal', v('reading'), *av(LOCAL)), remaining) + ']'
    text += definition('iasschema', params(SCHEMA), k('iaqschema', v('reading'), result))
    sort = 'h[' + ' '.join(t for n, t in SCHEMA) + '] c'
    text += 'r iasreport[a a i c[' + sort + '] a d] c.'
    text += definition('iasattribution', '', k('iasreport', k('iagnode'), k('wa'), 'r c[p iasschema]', k('iagscope'), k('wh')))
    return text


def build():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    lib = deepcopy(parent); lib['statements'] = []; lib['declarations'] = closure(parent, ['rcm', 'rz', 'ru', 'rw'])
    lib = parse(format_graph(lib, 'compact') + definitions())
    doc = deepcopy(parent); doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions() + additions() + 's[k iasattribution[]].')
    doc['statements'] = parent['statements'][:-1] + doc['statements']
    core = deepcopy(doc); core['statements'] = core['statements'][-1:]
    core['declarations'] = closure(doc, _references(core['statements']))
    return {p: format_graph(d, 'compact') + '\n' for p, d in ((LIBRARY, lib), (SOURCE, doc), (CORE, core))}


def basis():
    return dict(status='collective_conditional_with_later_normative_causal_consequence', parent=PARENT, document=SOURCE,
        definitions={
            'rx4': '非空で完全列挙した同じ人々を、宣言済みの相異なる原因変数へ対応させる。媒介変数は指定しない。',
            'rx5': '観測で全員の前件と結果が成立し、全原因を一緒に偽・真へ固定した両側に解がある。両側の全解が評価済みで、各人の前件が本人の変数と一致し、結果は偽側で不成立・真側で成立する。',
            'iaschecked': '同じ因果モデルの履歴で、集団の終点より後に指定の政治的終点がある。旧・新原則の内容差の実例と、同じ規範源・主体・職務に対する両原則の前後の要求の評価を確認する。',
            'iaseffect': '同じ旧・新原則について、同じ解の始点と政治的終点に対応する規範文脈でiarreplacementを評価する。規範の当事者や原則を介入ごとに交換しない。',
            'iascausal': '前段の集団の変化と同じ原因側・変数・方程式・観測割当て・履歴を使い、原則の置換へのrx5の依存を要求する。前件には同じ発展の読みを各解の始点で実行する。',
            'iasschema': '集合的な条件文の後件にiascausalを追加し、残余条件へ同じ読み・集団・原因側・基準文脈・始点・集団終点・政治的終点を渡す。',
            'iasattribution': '同じ著者・箇所・文脈への階数2のひな形帰属を更新する。親の全宣言と先行21主張を保存する。'},
        inputs={
            'last': '同じ集団・区間・構造モデルの解に対応する政治的終点。仮定ごとに異なる時刻でもよいが、同じ履歴内で集団終点より後でなければならない。',
            'normpoint': 'その解の履歴上の時点に対応する、既存の要求関係h7kを評価する文脈。政治的変化そのものを真偽で渡す原始関係ではない。',
            'reviewed': '同じ規範源・主体・職務・原則記述・文脈について、肯定内容への要求の有無が評価されている。未評価を要求なしへ変換しないための条件。',
            'source/actor/office/first/second/probes': '同じ条件文の中で固定した規範源・主体・職務・旧新の原則記述・内容比較範囲。原則の具体的内容と政府の資格は未充足である。'},
        limitations=[
            '全原因をまとめて変えた強いモデル内依存の候補である。政府側の変化に各人が必要であること、媒介経路、確率的寄与、現実の機構を主張しない。民衆の態度を政府側変化の必要な媒介とする条件も追加しない。',
            '政府側と民衆側で同じ構造モデルを使用するが、両結果の間の因果関係は要求しない。独立に発生した原則置換を、時間的に後であるというだけで原因側の効果にしない。',
            '政治的終点が集団終点より後という候補を採用する。原文のendlichから両過程の開始時刻や非重複まで導かず、この時間解釈の適合は未確認である。',
            '原則置換は旧原則の要求消失と新原則の要求成立である。追加・部分改訂・実行の変更を全て網羅する原則への作用の一般定義ではなく、原文が置換を明示したとはしない。',
            '政府という組織・職務と当該共同体の統治関係、具体的な原則、自らにとっての有益さ、人間と機械の対比、尊厳に即した扱いは未完である。関数引数の名前だけで記述済みにはしない。',
            '原始関係の解釈と現実の対応は検査モデルの外にある。有限診断は構成の区別を確認するもので、原文の唯一の読みや全文の意味一致を保証しない。',
            '原文の新しい文字範囲と意味確認済み区間は加算しない。残余条件は未充足であり、全ての内容を記述できる言語の完成とはしない。'])


def main():
    for name, body in (build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}).items():
        path = ROOT / name
        if path.exists(): assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(name, len(body))


if __name__ == '__main__': main()
