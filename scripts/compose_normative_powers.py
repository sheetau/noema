"""Separate permission from a controlled, constitutively recognized norm change."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_policy_norms import DESCRIPTION, RULE, TRUE

PARENT = 'examples/v014/kant-office-associations.noema'
CONTROL = 'h[a ' + DESCRIPTION + ' j[a] d] c'
EDGE = 'h[a a a ' + DESCRIPTION + ' j[a] d d] c'
EFFECT = [('source', 'a'), ('person', 'a'), ('role', 'a'), ('target', DESCRIPTION), ('bindings', 'j[a]'),
    ('polarity', 'c'), ('start', 'd'), ('end', 'd'), ('status', 'c'), ('valid', 'h[j[a]] c'), ('relation', RULE)]
HOLDER = [('framework', 'a'), ('actor', 'a'), ('capacity', 'a'), ('exercise', DESCRIPTION),
    ('exercisebindings', 'j[a]'), ('exercisevalid', 'h[j[a]] c')]
TRANSITION = HOLDER + EFFECT + [('controlled', CONTROL), ('recognizes', EDGE)]
POWER = [(n, t) for n, t in TRANSITION if n != 'end']
ACTUAL = TRANSITION + [('performed', CONTROL), ('realized', 'h[d d] c')]
SOURCE = [(n, t) for n, t in POWER if n not in ('start', 'relation')]
PERMITTED = SOURCE + [('assessor', 'a')]
ROOTS = ['riv', 'riw', 'rix', 'riy']


def definitions():
    fields = [v(n) for n in ('source', 'person', 'role', 'target', 'bindings', 'polarity')]
    before = app(v('relation'), *fields, v('start'))
    after = app(v('relation'), *fields, v('end'))
    text = definition('riv', params(EFFECT), both(op('u', op('e', v('start'), v('end'))),
        app(v('valid'), v('bindings')), op('z', before, op('u', v('status'))), op('z', after, v('status'))))
    recognized = app(v('recognizes'), *[v(n) for n in ('framework', 'actor', 'capacity', 'exercise', 'exercisebindings', 'start', 'end')])
    control = app(v('controlled'), v('actor'), v('exercise'), v('exercisebindings'), v('start'))
    text += definition('riw', params(TRANSITION), both('a[v exercisebindings][n p a b][v actor]',
        app(v('exercisevalid'), v('exercisebindings')), control, recognized, k('riv', *args(EFFECT))))
    text += definition('rix', params(POWER), quant('g', 'end', 'd', k('riw', *args(TRANSITION))))
    text += definition('riy', params(ACTUAL), both(k('riw', *args(TRANSITION)),
        app(v('performed'), v('actor'), v('exercise'), v('exercisebindings'), v('start')),
        app(v('realized'), v('start'), v('end'))))
    return text


MEANINGS = {
    'riv': '同じ規範の出所・名宛人・立場・対象記述・引数列・内容の極性について、異なる二状況の間で規範関係が指定の有無へ変わる。statusが真なら不在から成立へ、偽なら成立から不在へ変わる。内容の否定と規範の廃止は別である。',
    'riw': '同じ主体が自らの意思によって選ぶ行使を、その枠組みが同じ前後状況の制度上の移行として認め、その同じ移行にrivの指定規範の変化がある。行使引数列の先頭が主体であり、列の適合条件を満たす。',
    'rix': '指定した基準状況からriwを満たす結果状況が存在する。特定の規範の成立・廃止を生じさせる権能への操作的な候補。行使の実行、許可、現実の結果は要求しない。',
    'riy': 'riwの同じ行使を本人が実行し、その同じ二状況の移行が現実に生起した。実行と現実の移行を独立に要求し、単なる権能の保有を既行使と扱わない。',
}
LIMITS = [
    'controlledは同じ主体が指定の行使を自らの意思によって選ぶ側にある関係。物理的な実行可能性や成功の保証、行使の許可は含めない。選択の統制や共同主体の意思の一般的な構成説明は残る。',
    'recognizesは、指定した制度的枠組みがその主体のその立場での同じ行使を、指定した前状況から後状況を生じる制度上の移行として扱う関係。単なる時間的先行や二状況の同時観測ではなく、その行使による構成的な効果を指定する。制度の成立・承認・正当性の基礎説明は残る。',
    'performedは同じ記述・引数列の行使を実際に行った関係、realizedは指定した前後状況への実際の移行の関係。制度上の効果と物理的な因果機構を同一視しない。',
    'statusは規範関係の有無、polarityは規範が対象にする内容の肯否である。肯定内容への要求の廃止は、否定内容への要求の生成とは異なる。要求と積極的許可も別のrelationとして扱う。',
    '既にある同じ規範を確認するだけの行使はrivの変更条件を満たさない。それを無効な行為とする定義ではなく、特定の変更を生じる権能に範囲を限定している。',
    '指定した一つの規範対象についての変更であり、他の規範が不変であること、全ての制度効果の列挙、権能・免責そのものの変更を網羅しない。状態解釈とrecognizesは同じ枠組みに対応させる必要があり、その現実への対応を有限検査だけでは保証しない。',
    '対象政策・行使記述は脱引用して実行しない。型の一致だけで意味的な適合を保証せず、validとexercisevalidにそれぞれの引数規約を明示する。未知の関係を偽として補わない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, relation in (('hzc2', 'h7k'), ('hzc3', 'h7l')):
        text += definition(name, params(SOURCE), 'b start[' + k('rix', *args(POWER, relation='p ' + relation)) + ']', 'e')
    permission = k('rdu', v('assessor'), v('actor'), v('capacity'), v('exercise'), v('exercisebindings'), TRUE,
        v('start'), v('exercisevalid'), 'p h7k', 'p h7l')
    power = op('t', k('hzc2', *args(SOURCE)), v('start'))
    text += definition('hzc4', params(PERMITTED), 'b start[' + both(permission, power) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-office-associations-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-normative-powers-basis-v1', document='examples/v014/kant-normative-powers.noema')
    basis['definitions'].update(MEANINGS | {
        'hzc2': '指定した要求h7kを成立・廃止させるrixの権能について、基準状況を受け取る内容を作る。契約をsourceにできるが、契約が実際に形成されたことや効力を生じたことは付けない。',
        'hzc3': 'hzc2と同じ構成で、積極的許可h7lの成立・廃止を扱う。要求を変更する権能から許可を変更する権能を推定しない。',
        'hzc4': '同じ行使に対する指定評価側の反対要求と衝突しない積極的許可rduと、指定要求を変更する権能hzc2を併記した内容。許可のみ・権能のみの読みとは区別する。'})
    basis['unresolved'] += LIMITS + [
        'u0013のberechtigt seinの再検討用の候補。以前のhzctの許可の読みを保持し、制度的効果を生む権能hzc2/hzc3と、許可を併記するhzc4を追加する。原文の一意の語義として採用したものではない。',
        'Hohfeldの権能と自由の区別は設計の参考であり、カントへ後世の法理論をそのまま帰属させない。ここでの積極的許可rduは、反対義務の不在のみを表すHohfeldのprivilegeと同一ではない。',
        '具体的な契約・将来世代・全啓蒙を制約する内容、制度の承認条件、権能の正当性、団体による行使や代表権、問い・否定回答の原文全体への帰属は未完。新しい著者主張・原始記号は追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'normative-powers')
def core_composed(): return projected(ROOTS + ['hzc2', 'hzc3', 'hzc4', 'rii', 'rij', 'hzcu'], 'normative-powers-core')
BUILDERS = ((generic_composed, 'normative-powers'), (source_composed, 'kant-normative-powers'), (core_composed, 'normative-powers-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored normative power differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
