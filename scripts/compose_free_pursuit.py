"""Separate permission, opportunities for self-development, and achieved ability."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_described_norms import DESCRIPTION as EXECUTION, RULE, TRUE
from scripts.compose_policy_norms import DESCRIPTION as GOAL
from scripts.compose_parameterized_goals import AIMS
from scripts.compose_topical_enablement import SOURCE as CAPACITY

PARENT = 'examples/v014/kant-scoped-enablers.noema'
WORK = [('goal', GOAL), ('aims', AIMS), ('occurs', 'h[a d] c'), ('participates', 'h[a a d] c'), ('work', 'h[a a d] c')]
OPPORTUNITY = [('source', 'a'), ('person', 'a'), ('role', 'a'), ('activity', 'a'), ('description', EXECUTION),
    ('context', 'd'), ('available', 'h[a a d] c'), ('outcomes', 'h[a a d d] c'), ('required', RULE), ('allowed', RULE)]
SOURCE = OPPORTUNITY[:6]
GROUP = [('source', 'a'), ('scope', 'h[a] c'), ('roles', 'h[a] a'), ('description', EXECUTION), ('context', 'd')]
ROOTS = ['rlt', 'rlu', 'rlv', 'rlw', 'rlx']


def definitions():
    actual = both(app(v('occurs'), v('activity'), v('point')),
        app(v('participates'), v('person'), v('activity'), v('point')),
        app(v('work'), v('person'), v('activity'), v('point')),
        app(v('aims'), v('person'), v('activity'), v('goal'), 'l[a][v person]', v('point')))
    text = definition('rlt', params(WORK), 'i[person a activity a][b point[' + actual + ']]', 'h[a a] e')
    value = quant('g', 'person', 'a', both('a[v bindings][n p a b][v person]',
        op('t', app(v('goals'), v('person')), v('point'))))
    text += definition('rlu', 'goals h[a] e', 'i[bindings j[a]][b point[' + both(
        k('rdr', v('bindings'), 'n p b b'), value) + ']]', 'h[j[a]] e')
    normargs = [v(n) for n in ('source', 'person', 'role', 'activity', 'description')]
    def permitted(sign): return k('rdm', *normargs, sign, v('context'), v('required'), v('allowed'))
    execution = app('s[v description]', v('person'), v('activity'))
    result = quant('g', 'future', 'd', both(
        app(v('outcomes'), v('person'), v('activity'), v('context'), v('future')), op('t', execution, v('future'))))
    text += definition('rlv', params(OPPORTUNITY), both(permitted(TRUE),
        app(v('available'), v('person'), v('activity'), v('context')), result))
    text += definition('rlw', params(OPPORTUNITY), both(k('rlv', *args(OPPORTUNITY)), permitted(op('u', TRUE))))
    member = app(v('scope'), v('person'))
    text += definition('rlx', 'scope h[a] c opportunities h[a] e context d', both(quant('g', 'person', 'a', member),
        quant('f', 'person', 'a', op('y', member, op('t', app(v('opportunities'), v('person')), v('context'))))))
    return text


MEANINGS = {
    'rlt': '同じ人が同じ活動に能動的に参加し、その活動が実際に起き、指定された自己作業であり、同じ時点で本人だけを引数にした目標記述を目指す内容。目標の達成・実現可能性を評価しない。',
    'rlu': '人から内容への関数を、ちょうど一人を含む個体列から内容への関数へ接続する。余分な引数や空列を切り捨てず、目標の本人を保持する。',
    'rlv': '同じ出所・本人・役割・活動・実行記述に衝突のない実行許可があり、その本人がその活動を実行でき、想定結果の一つで同じ実行記述が成立する。現在の実行や、実行内容の目標の達成を要求しない。',
    'rlw': 'rlvに加え、同じ活動・実行記述の不実行にも衝突のない積極的許可がある。取り組むことを強制されない規範的選択を加えた強い候補であり、物理的な不実行の可能性までは主張しない。',
    'rlx': '空でない指定範囲の各人について、同じ文脈で指定された機会内容が成立する。各人に別の活動があってよく、全員を同時に実行させる共通計画を導かない。',
    'hzey': '同じ主題・事柄・基準時点・方法を使う自立的判断能力hzerをrluで一人用の目標関数へ接続する。目標の記述として引用するだけなら能力を評価しない。',
    'hzez': 'rltの実際の活動と本人の参加をdg・df、自己の精神的営みを吟味し組み直す作業をh4oへ接続する。同じ本人の目標記述への志向を保ち、能力の達成や成功の因果関係は補わない。',
    'hze2': '人aaについて、rlvの実行許可を既存h7a・h7b、方法の利用可能性と結果をae・afへ接続する。ここでは活動を方法として選択する同じ個体で表す。',
    'hze3': 'hze2と同じ本人・活動・規範源・役割・実行記述に、rlwの不実行の許可も要求する。自由な取り組みの一つの強い操作的候補。',
    'hze4': '同じ規範源・実行記述・文脈で、非空の人々の各人に、本人の役割に応じたhze3の活動が存在する。実行記述をhzezの能力獲得を目指す作業へ固定して原文へ接続する。',
}
LIMITS = [
    '前版の能力を目標にするが、取り組みの機会があることから現在能力、実際の努力、能力の獲得を推定しない。目標記述が未知でも許可や目標志向を表せる。',
    'hzezの目標には、hzeyの同じ本人に関する閉じた関数記述を渡す。hze2からhze4の実行記述には、その同じ目標を持つhzezの閉じた記述を渡す。一般の同じ型の引数が自動でこの接続を満たすわけではない。',
    '規範的な許可、実行できる方法、想定結果での本人の作業を同じ活動に結ぶ。可能な結果と現実の結果、同時に起きただけの他者の作業、別人の目標を区別する。',
    'rlvは取り組む許可と機会であり、rlwは不実行も積極的に許される強い選択条件。原文のfreiの唯一の意味とはせず、身体的な不実行の可能性、全規範源からの自由、権利の正当性は残す。',
    '同じ活動を方法として選択する粒度を採用する。複数段階の計画、その部分活動への対応、反復や努力量、精神的な営みの構造、学習や能力獲得の因果機構は未完。',
    'u0014の自由な自己形成のための機会への部分的な解釈注記である。開かれつつあるという進行・変化、一般的啓蒙の障害の漸減、明瞭な徴候、著者帰属、段落全体の意味確認は未接続。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    text += definition('hzey', params(CAPACITY), k('rlu', k('hzer', *args(CAPACITY))), 'h[j[a]] e')
    text += definition('hzez', params(WORK[:2]), k('rlt', v('goal'), v('aims'), 'p dg', 'p df', 'p h4o'), 'h[a a] e')
    for name, target in (('hze2', 'rlv'), ('hze3', 'rlw')):
        text += definition(name, params(SOURCE), both(k('aa', v('person')), k(target, *args(OPPORTUNITY,
            available='p ae', outcomes='p af', required='p h7a', allowed='p h7b'))))
    possible = quant('g', 'activity', 'a', k('hze3', *args(SOURCE, role=app(v('roles'), v('person')))))
    opportunities = 'i[person a][b context[' + possible + ']]'
    text += definition('hze4', params(GROUP), k('rlx', v('scope'), opportunities, v('context')))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-scoped-enablers-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-free-pursuit-basis-v1', document='examples/v014/kant-free-pursuit.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'free-pursuit')
def core_composed(): return projected(ROOTS + ['hzey', 'hzez', 'hze2', 'hze3', 'hze4'], 'free-pursuit-core')
BUILDERS = ((generic_composed, 'free-pursuit'), (source_composed, 'kant-free-pursuit'), (core_composed, 'free-pursuit-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored free pursuit differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
