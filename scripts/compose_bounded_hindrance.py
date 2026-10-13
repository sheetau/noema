"""Compare intervention outcomes with an explicit tolerated loss."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, call, app, op, both, definition
from scripts.compose_proportions import generic_composed as proportions
from scripts.compose_scoped_interventions import generic_composed as scoped

PARENT = 'examples/v014/kant-closed-policies.noema'
LIBRARY = 'examples/v014/scoped-interventions.noema'
STATE = 'h[a] c'
EQUATIONS = 'h[a h[a] c] c'
SCORE = 'h[h[a] c] b'
PARAMS = 'variables j[a] equations ' + EQUATIONS + ' factor a score ' + SCORE + ' tolerance b'
TRUE = 'e[n p a b][n p a b]'


def definitions():
    def possible(sign, variable, body):
        return call('rv', v('variables'), v('equations'), 'i[item a][e[v item][v factor]]',
            'i[item a][' + sign + ']', 'i[' + variable + ' ' + STATE + '][' + body + ']')
    exists_pair = lambda body: possible(TRUE, 'on', possible(op('u', TRUE), 'off', body))
    factor_valid = call('rz', v('variables'), v('factor'))
    valid = op('u', call('hc', v('tolerance'), 'n p a b'))
    bounded = call('red', v('on'), v('off'), v('score'), v('tolerance'))
    text = definition('red', 'on ' + STATE + ' off ' + STATE + ' score ' + SCORE + ' tolerance b', both(valid,
        op('u', call('hc', call('ha', app(v('score'), v('on')), v('tolerance')), app(v('score'), v('off'))))))
    text += definition('ree', 'variables j[a] equations ' + EQUATIONS + ' factor a', both(factor_valid, exists_pair(TRUE)))
    text += definition('ref', PARAMS, both(factor_valid, exists_pair(bounded)))
    text += definition('reg', PARAMS, both(valid, factor_valid, exists_pair(op('u', bounded))))
    text += definition('reh', PARAMS, both(valid, call('ree', v('variables'), v('equations'), v('factor')),
        op('u', call('reg', v('variables'), v('equations'), v('factor'), v('score'), v('tolerance')))))
    return text


MEANINGS = {
    'red': '非負の許容損失について、制限あり側の尺度値にその許容値を足すと、制限なし側の値以上になる。同じ尺度での低下が許容値を超えない。改善や同値も許す。',
    'ree': '明示した重複のない変数列に同じ要因が含まれ、同じ方程式・背景で、その要因を真へ固定した解と偽へ固定した解が双方に存在する。',
    'ref': '両介入の解の組のうち、redで許容範囲内の低下となる組が少なくとも一つある。全解での保証とは別である。',
    'reg': '許容値が非負で、制限あり側が制限なし側より許容値を超えて低い解の組が少なくとも一つある。',
    'reh': '許容値が非負で、双方に解があり、許容値を超える低下となる解の組が一つもない。全ての両側の組を比較する強い保証条件。',
}
LIMITS = [
    '既存のrz〜rxを再利用し、指定した因果変数だけの全割当てを列挙する。人や役職を含む全個体を自動的に因果変数へ増やさない。列外は偽へ固定する規約であり、必要な背景条件は方程式で保持する。',
    '同じ構造方程式・背景・要因・数値尺度のもとで介入を比較する。観測の同時変化や、時間の前後だけを因果的な低下とは数えない。',
    '尺度は大きいほど進行が上位という有理数値を取る。差と許容値を同じ単位で解釈する。単なる順序尺度には差の比較を無条件に適用できない。正の尺度変換では許容値も同じ倍率で変える。',
    '許容値の境界と等しい低下は許す。許容値0は全く低下しないという強い条件であり、特に妨げないという原文を常に0へ固定しない。',
    '全解の全組での保証は一つの強い読みであり、確率的な傾向や対応する解だけの比較とは異なる。双方の解の存在を要求し、解なしを無害とはしない。',
    '妨害が小さいことから、実際に進歩すること、進歩が十分な大きさであること、制限が正当であることは導かない。方程式・尺度・許容値の現実的な妥当性は別の解釈上の課題。',
]


def generic_composed():
    text, basis = proportions()
    scoped_text, math = scoped()
    doc = parse(scoped_text + text.split(':', 1)[1] + definitions())
    basis = deepcopy(basis)
    basis.update(version='bounded-hindrance-basis-v1', document='examples/v014/bounded-hindrance.noema')
    basis['definitions'].update(math['definitions'])
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += math['unresolved'] + LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    declarations = {row['name']: row for row in doc['declarations']}
    if any(declarations.get(row['name']) != row for row in parse(scoped()[0])['declarations']):
        raise ValueError('Existing scoped intervention definitions differ')
    statements, doc['statements'] = doc['statements'], []
    extra = definitions() + '''
d hze[policy e variables j[a] equations ''' + EQUATIONS + ''' factor a worlds h[h[a] c] d] c[
 w[k ree[v variables v equations v factor]][w[
  k rw[v variables v equations i[item a][e[v item][v factor]] i[item a][''' + TRUE + ''']
   i[state h[a] c][z[t[v policy][c[v worlds][v state]]][c[v state][v factor]]]]
 ][k rw[v variables v equations i[item a][e[v item][v factor]] i[item a][u[''' + TRUE + ''']]
   i[state h[a] c][z[t[v policy][c[v worlds][v state]]][c[v state][v factor]]]]]]
].
d hzf[policy e variables j[a] equations ''' + EQUATIONS + ''' factor a worlds h[h[a] c] d score ''' + SCORE + ''' tolerance b] e[
 b context[w[t[v policy][v context]][w[k hze[v policy v variables v equations v factor v worlds]][k reh[v variables v equations v factor v score v tolerance]]]]
].
'''
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-closed-policies-basis-v1.json').read_text(encoding='utf-8')))
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'hze': '両側の介入に解があり、全ての介入解で、対応する状況における同じ政策内容の真偽が、介入要因の真偽と一致する。モデル変数が無関係な政策を指す場合を拒否する。世界対応の因果的妥当性そのものは保証しない。',
        'hzf': '指定文脈で同じ政策内容が成立し、hzeでその政策と介入要因が対応し、rehで全解にわたり許容値を超える低下がないという内容。h77の政策内容を渡し、この全体をhzaの許可対象として記述できる。',
    })
    basis.update(version='kant-bounded-hindrance-basis-v1', document='examples/v014/kant-bounded-hindrance.noema')
    basis['unresolved'] += LIMITS + [
        'hzfは制限状態と悪影響の上限を合わせた許可対象の候補である。条件付きで許可を与える規範、または単に二つの事実を並べた原文読解との同値は主張しない。',
        '政策内容にはh77の程度・頻度を含む状態を渡せるが、その具体的な尺度・値・期間を原文へ補わない。方程式中の変数選択と、啓蒙の進歩を測る尺度の先行定義への接続は未完。',
        'hzeは解の範囲で政策の真偽対応を検査する。指定した世界対応が現実の介入結果を正しく表すこと、政策の成立に十分な他の条件を保持することは別の仮定である。本文の新しい主張は追加しない。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'bounded-hindrance'), (source_composed, 'kant-bounded-hindrance')):
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored bounded hindrance differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Model-relative bounded hindrance composed without equating it with progress')


if __name__ == '__main__':
    main()
