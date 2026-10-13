"""Use ordinary closed descriptions to bind mixed typed policy arguments."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, call, definition
from scripts.compose_policy_norms import DESCRIPTION, RULE, TRUE, generic_composed as policies

PARENT = 'examples/v014/kant-restriction-frequency.noema'
PARAMS = 'source a person a role a description ' + DESCRIPTION + ' polarity c context d required ' + RULE + ' allowed ' + RULE


def definitions():
    args = [v(n) for n in ('source', 'person', 'role', 'description')]
    args += ['l[a][]', v('polarity'), v('context'), 'i[bindings j[a]][k rdr[v bindings n p a b]]', v('required'), v('allowed')]
    return ''.join(definition(name, PARAMS, call(target, *args)) for name, target in (
        ('rea', 'rds'), ('reb', 'rdt'), ('rec', 'rdu')))


MEANINGS = {
    'rea': '同じ出所・名宛人・立場・対象記述・極性・文脈について、空の個体引数列で適用する政策内容への要求がある。対象の型付き引数は記述内の閉じた式として保持する。',
    'reb': '同じ指定対象を空の引数列で適用した内容の指定極性を積極的に許可する。対象を実行評価しない。',
    'rec': 'rebの許可があり、同じ記述・空の引数列・文脈について反対極性の要求がない。許可内容の実現は含まない。',
}
LIMITS = [
    '既存の記述生成補助により、内容を返す関数の記述と、それに渡す任意の型の閉じた式記述から、通常のNoema引用を組み立てる。実行時の値を個体IDへ変換せず、新しい構文も追加しない。',
    '空の個体引数列を使うのは、対象の型付き引数が記述の内部で全て束縛されているためである。記述の外側の自由変数は捕捉しない。個体・数値・列・関数の型と引数順は通常の型検査で保持する。',
    '生成補助は通常の引用と関数適用を出力する。言語利用者は同じ式を直接記述でき、Pythonや補助関数が意味の外部定義を担うわけではない。',
    '記述は式の構造を保持し、同じ値となる別名や別の式を自動同一視しない。関数適用の記述は、展開や簡約された同値式とは異なる記述である。',
    '閉じた式の参照先は、意味規約で解釈する定数や関数を含み得る。閉じていることは、値が既知・不変・現実に正当であることを意味しない。未知の内容でも許可を記述できる。',
]


def generic_composed():
    text, basis = policies()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='closed-policies-basis-v1', document='examples/v014/closed-policies.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = definitions() + '''
d h77[source a person a role a frame a populations h[d] j[a] degrees h[d] b degreecriterion h[b] c points j[d] weight h[d] b frequency b frequencycriterion h[b] c] e[
 b anchor[k h76[v source v person v role v frame v populations v degrees v degreecriterion v points v weight v frequency v frequencycriterion v anchor]]
].
'''
    params = 'assessor a regulator a office a target ' + DESCRIPTION + ' context d'
    args = [v(n) for n in ('assessor', 'regulator', 'office', 'target')] + [TRUE, v('context'), 'p h7k', 'p h7l']
    extra += definition('hza', params, call('reb', *args))
    extra += definition('hzb', params, call('rec', *args))
    extra += '''d hzc[target ''' + DESCRIPTION + ''' context d] c[t[c[s[v target]][l[a][]]][v context]].
d hzd[''' + params + '''] c[w[k hza[v assessor v regulator v office v target v context]][u[k hzc[v target v context]]]].
'''
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-restriction-frequency-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-closed-policies-basis-v1', document='examples/v014/kant-closed-policies.noema')
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h77': '既存h76の全引数を同じ型・順序で受け取り、評価状況ごとの制限の程度と頻度の状態を内容として返す。各時点の活動列・割合・二つの評価基準・期間列・重みを記述の引数へ渡せる。',
        'hza': '評価側の出所が、規制者にその立場で、型付きの対象記述を空の個体引数列で適用した内容を積極的に許可する。h77の閉じた適用記述を渡すことで、程度と頻度を含む制限状態を許可の対象にできる。',
        'hzb': 'hzaの許可があり、同じ対象への反対要求がない。衝突のない許可であり、実際の制限状態ではない。',
        'hzc': '同じ対象記述を空の引数列で評価した内容が、その評価状況で実際に成立する。許可を要求しない。',
        'hzd': 'hzaの許可はあるが、その同じ対象記述の内容は現在の評価状況で成立していない。許可の未行使を義務違反とはしない。',
    })
    basis['unresolved'] += LIMITS + [
        'hzaは閉じた政策記述一般を受け取る。カントの程度・頻度への接続は、h77の引用と型付き引数から生成した対象を渡した場合に限る。無関係な対象を渡した呼出まで同じ意味とは扱わない。',
        '原文のdarfに対する、頻度・程度の状態全体を許可する読みを表せるようにした。各機会で許可があるという別の作用範囲との同値や、唯一の読みの確定は含まない。',
        'h77の比率と頻度は明示した正確な値であり、原文がその数値を指定したとはしない。数値・範囲・重みの候補全体を量化した原文の許可、進歩を特に妨げないという留保、全文の意味一致は未完。',
        'hzcとhzdは脱引用を含み、その記述をさらに引用できないという現行制約を維持する。許可だけを述べるhza/hzbは対象を実行評価しない。本文の新たな事実主張は追加しない。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'closed-policies'), (source_composed, 'kant-closed-policies')):
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored closed policy differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Typed closed policy descriptions connected to existing normative relations')


if __name__ == '__main__':
    main()
