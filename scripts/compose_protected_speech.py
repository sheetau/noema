"""Describe a ban and a distinct demand that the ban not obtain."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, call, both, op, definition

PARENT = 'examples/v014/kant-office-speech.noema'
PARAMS = 'assessor a regulator a office a target i[h[j[a]] e] context d'
TRUE = 'e[n p a b][n p a b]'


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-office-speech-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    execution = basis['role_linkage']['symbols']['roles']['dc']
    extra = ('d hzq[regulator a person a role a activity a] e[b context[k h7a['
             'v regulator v person v role v activity r[p ' + execution + '] u[' + TRUE + '] v context]]].\n')
    fields = [v(n) for n in ('assessor', 'regulator', 'office', 'target')]
    require = lambda sign: call('rea', *fields, sign, v('context'), 'p h7k', 'p h7l')
    negative = call('hzr', *fields, v('context'))
    extra += definition('hzr', PARAMS, require(op('u', TRUE)))
    extra += definition('hzs', PARAMS, both(negative, op('u', require(TRUE))))
    extra += definition('hzt', PARAMS, both(negative, call('hzc', v('target'), v('context'))))
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis.update(version='kant-protected-speech-basis-v1', document='examples/v014/kant-protected-speech.noema')
    basis['definitions'].update({
        'hzq': '指定した規制者が、同じ本人・立場・活動の実行を禁じるという規範状態を内容として返す。本人が実際に発言しないことや、発言への許可がないこととは異なる。',
        'hzr': '評価側の出所が、規制者にその立場で、閉じた対象記述の内容を不成立にするよう要求する。hzqに規制者・本人・立場・活動を渡した記述なら、その指定された禁止状態を成立させてはならないという上位の規範になる。',
        'hzs': 'hzrの不成立要求があり、同じ評価側の出所・名宛人・立場・対象記述・文脈からの成立要求はない。同じ出所内の衝突を除いた条件であり、出所の正当性や他の出所間の優先順位は判定しない。',
        'hzt': 'hzrの不成立要求があるにもかかわらず、同じ対象記述の内容が現に成立する。hzqの閉じた記述に適用した場合は、指定された禁止状態が上位の要求に反して存在する。',
    })
    basis['unresolved'] += [
        'hzr〜hztは任意の閉じた政策対象を受け取る。公的発言の保護へ用いる際はhzqの閉じた適用記述を作り、その本人・立場・活動を既存h6vの公的使用の同じ引数と対応させる。任意のtargetが自動で公的発言を指すわけではない。',
        '禁止を不成立にせよという規範、禁止が実際にないこと、本人への積極的な実行許可、本人の実際の実行、禁止する物理的能力がないことはそれぞれ別である。上位の要求に反して禁止が存在するモデルも許す。',
        '原文のbilligermaßenについて、指定された評価規範に反する禁止という部分的な読みを表す。評価側の規範が公正・正当である根拠、あらゆる規制者への一般化、権利の全条件を定義し終えたわけではない。',
        'hzqは現在の禁止状態を表す。禁止を発出・撤回する行為とその時間経過、過去に違反して今は解除された場合、補償や責任の判定は含まない。',
        '対象の引数は通常の引用と関数適用で固定し、同じ値や真偽となる別名の記述には規範を自動移転しない。外側の名宛人と内側の規制者を一致させる読みは作例の明示的な束縛であり、一般関数が強制する同一性ではない。',
        'hztは対象を脱引用して評価するので引用内では使えない。hzr/hzsは対象を実行評価せず、未知の禁止状態についても上位の要求を記述できる。既存の本文主張は保存する。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = source_composed()
    for name, body in ((basis['document'], text), ('data/kant-protected-speech-basis-v1.json',
            json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored protected speech differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Ban state and the demand against that state composed separately')


if __name__ == '__main__':
    main()
