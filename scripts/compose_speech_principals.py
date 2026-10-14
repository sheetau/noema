"""Keep speech attribution, role classification and reader reach separate."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_institutional_voice import CORE, PRESENTATION, RELATIONS, VOICE, SERVES

PARENT = 'examples/v014/kant-conscientious-office.noema'
OWN = [f for f in CORE if f[0] != 'principal']
ATTRIBUTED = PRESENTATION + [('voices', VOICE)]
PRIVATE = CORE + [('recipient', 'a'), ('voices', VOICE), ('serves', SERVES)]
PUBLIC = OWN + [('recipient', 'a'), ('channel', 'a'), ('voices', VOICE)]
SHARED = [('person', 'a'), ('context', 'd'), ('voices', VOICE), ('serves', SERVES)]


def paired(left, right):
    return SHARED + [('office' + n, t) for n, t in left if n not in dict(SHARED)] + [
        ('public' + n, t) for n, t in right if n not in dict(SHARED)]


def bound(fields, prefix):
    return [v(n if n in dict(SHARED) else prefix + n) for n, _ in fields]


PAIR = paired(PRIVATE, PUBLIC)
GENERIC_PAIR = paired(CORE, OWN) + [f for f in RELATIONS if f[0] not in dict(SHARED)]
ROOTS = ['rhe', 'rhf', 'rhg', 'rhh']
SOURCE_ROOTS = ['hzb3', 'hzb4', 'hzb5']


def definitions():
    # The input relation identifies a discourse principal. A self-attribution
    # is positive evidence, never the negation of somebody else's attribution.
    actual = k('rfo', *args(OWN[:2]), *args(OWN[3:]), *args(PRESENTATION))
    own = app(v('voices'), *map(v, ('person', 'activity', 'person', 'role', 'subject', 'message', 'context')))
    text = definition('rhe', params(OWN + ATTRIBUTED), both(actual, own))
    text += definition('rhf', params(CORE + RELATIONS), both(
        op('u', op('e', v('principal'), v('person'))), k('rgb', *args(CORE + RELATIONS))))
    left = k('rhf', *bound(CORE, 'office'), *args(RELATIONS))
    right = k('rhe', *bound(OWN, 'public'), *args(ATTRIBUTED))
    text += definition('rhg', params(GENERIC_PAIR), both(
        op('u', op('e', v('officeactivity'), v('publicactivity'))), left, right))
    text += definition('rhh', 'actual h[a] c intended h[a] c', both(
        quant('g', 'reader', 'a', app(v('actual'), v('reader'))),
        quant('f', 'reader', 'a', op('y', app(v('actual'), v('reader')), app(v('intended'), v('reader'))))))
    return text


MEANINGS = {
    'rhe': '同じ人・行為・役割・対象・発話記述について、非空の受け手群への実際の提示と、話者本人を語りの帰属先とする明示的な関係が共に成立する。他者への帰属がないことの言い換えではなく、信念・真理・独創性・許可・職務の不在も含まない。',
    'rhf': '同じ発話についてrgbの委任・役割・奉仕・提示の条件が成立し、その帰属先が本人と異なる。異なる帰属先の声として語ることと、内容への本人の同意を区別する。',
    'rhg': '同じ本人・文脈に、rhfを満たす行為とrheを満たす別の行為がある。行為ごとに役割・宛先範囲・対象・発話記述を保持し、他者の委任による発言と本人を帰属先とする発言を併記する。公的／私的という分類や許可はまだ加えない。',
    'rhh': '実際の受け手範囲は非空で、全員が指定した想定宛先範囲に含まれる。両範囲の一致や人数の閾値を要求しない。空の実際の受け手は不成立であり、公衆の分類ではない。',
}
LIMITS = [
    'voicesは明示的に渡す語りの帰属関係であり、今回の自己帰属では第三引数を同じ本人にする。従来の組織への帰属という使い方を保持しつつ、本人への帰属を別の構成で述べる。単一の帰属先を強制せず、引用・共同声明などの複数帰属を排除しない。',
    '自己帰属は他者への帰属の否定、内心の賛同、合理的自律の完成した定義ではない。関係が未解釈の場合に、本人の声として語ったと補わない。',
    '実際の受け手と想定宛先を分ける。部分集合条件は今回記述する提示の条件であり、想定外の読者への伝達一般を不可能とする言語上の公理ではない。',
    'どの構成にも人数の閾値を置かない。公衆、職務、学識者という分類の社会的な基礎は既存の未完の意味規約を引き継ぐ。有限モデルの人数変更は、全社会での公衆概念の完成証明ではない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-conscientious-office-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    intended = 'i[reader a][k h6t[v recipient v reader v context]]'
    fixed = dict(occurs='p dg', presents='p f3', conveys='p f2', positioned='p cb', entrusted='p cf')
    text += definition('hzb3', params(PRIVATE), both(
        k('rhf', *args(CORE + RELATIONS, **fixed)),
        k('zzp', *map(v, ('person', 'activity', 'role', 'context'))),
        k('cc', *map(v, ('activity', 'recipient', 'context'))),
        k('rhh', v('audience'), intended)))
    text += definition('hzb4', params(PUBLIC), both(
        k('rhe', *args(OWN + ATTRIBUTED, **fixed)),
        k('h6v', *map(v, ('person', 'activity', 'role', 'recipient', 'channel', 'subject', 'message', 'context'))),
        k('rhh', v('audience'), intended)))
    text += definition('hzb5', params(PAIR), both(
        op('u', op('e', v('officeactivity'), v('publicactivity'))),
        k('hzb3', *bound(PRIVATE, 'office')), k('hzb4', *bound(PUBLIC, 'public'))))
    doc = parse(format_graph(doc, 'compact') + text)
    doc['statements'] = statements
    basis.update(version='kant-speech-principals-basis-v1', document='examples/v014/kant-speech-principals.noema')
    basis['definitions'].update(MEANINGS | {
        'hzb3': 'rhfの他者の委任による実際の提示に、同じ人・行為・役職の私的使用の分類zzpと、同じ活動の指定宛先ccを結ぶ。実際の受け手はその想定宛先の非空部分集合である。人数が増えても、公的使用という分類を人数から導かない。',
        'hzb4': 'rheの本人を帰属先とする実際の提示に、同じ人・行為・役割・想定公衆・経路・対象・発話記述の公的使用h6vを結ぶ。実際の受け手は想定公衆の非空部分集合であり、全読者への到達や受領・理解・許可は要求しない。',
        'hzb5': '同じ本人・文脈でhzb3の職務上の行為とhzb4の別の公的行為を並べる。それぞれの役割・帰属先・想定宛先・実際の受け手・内容を保持する。人を恒常的に私的または公的へ二分せず、今回の二行為を異なるものとする。',
    })
    basis['unresolved'] += LIMITS + [
        'u0012の職務内の使用と、自分自身の立場から公衆へ語る使用の対比への部分接続。全会衆に届いたとも、読者世界の全員が読んだとも断言しない。実際の提示条件を記述しただけで、原文が特定の発話の実行を断言しているとは扱わない。',
        '家庭内の集まりというhäuslich、いかに大きくてもという譲歩の様相、Schriftenという媒体、自由の無制限性、他者の委任という理由付け、未成年と後見人の議論は未完。人数の非依存性をこれらの完成訳へ昇格させない。',
        '既存の宣言と15件の本文主張を保存する。新しい原始概念・著者主張を追加せず、私的と公的の分類を互いの単なる否定とも、全活動で排他的とも定めない。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed()
    doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    projected_basis = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', projected_basis


def generic_composed(): return projected(ROOTS, 'speech-principals')
def core_composed(): return projected(ROOTS + SOURCE_ROOTS, 'speech-principals-core')
BUILDERS = ((generic_composed, 'speech-principals'), (source_composed, 'kant-speech-principals'), (core_composed, 'speech-principals-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored speech principals differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
