"""Connect solemn appeals to the same undertaking acts without implying truth."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_situated_criticism import params, args
from scripts.compose_mutual_undertakings import ACT, FORM, SOURCE as FORM_SOURCE
from scripts.compose_purposive_undertakings import PURPOSIVE, SOURCE as PURPOSE_SOURCE

PARENT = 'examples/v014/kant-question-responses.noema'
POLICY = 'h[j[a]] e'
AUTHORITY = 'i[h[a] e]'
FORMULA = 'i[h[j[a]] f]'
INVOKES = 'h[a a ' + AUTHORITY + ' ' + FORMULA + ' j[a] d] c'
APPEAL = [('authority', AUTHORITY), ('formula', FORMULA), ('solemn', 'h[a a d] c'), ('invokes', INVOKES)]
SIGNED = [('target', POLICY), ('response', POLICY)]
ACTION = ACT + APPEAL
GROUP = FORM + APPEAL
PURPOSE = PURPOSIVE + APPEAL
SOURCE = FORM_SOURCE + APPEAL
SOURCE_PURPOSE = PURPOSE_SOURCE + APPEAL
ROOTS = ['rim', 'rin', 'rio', 'rip', 'riq']


def strengthened():
    fields = [('person', 'a'), ('act', 'a'), ('agreement', 'a'), ('terms', dict(FORM)['terms']), ('bindings', 'j[a]'), ('scene', 'd')]
    return 'i[' + params(fields) + '][' + both(
        app(v('declares'), *args(fields)),
        app(v('solemn'), v('person'), v('act'), v('scene')),
        app(v('invokes'), v('person'), v('act'), v('authority'), v('formula'), v('bindings'), v('scene'))) + ']'


def definitions():
    negative = op('u', op('t', app(v('target'), v('bindings')), v('scene')))
    consequence = op('t', app(v('response'), v('bindings')), v('scene'))
    text = definition('rim', params(SIGNED), 'i[bindings j[a]][b scene[' + op('y', negative, consequence) + ']]', POLICY)
    text += definition('rin', params(SIGNED), 'i[bindings j[a]][j m[' + app(k('rim', *args(SIGNED)), v('bindings')) + ']]', 'h[j[a]] f')
    text += definition('rio', params(ACTION), both(k('rhx', *args(ACT)),
        app(v('solemn'), v('person'), v('act'), v('scene')),
        app(v('invokes'), v('person'), v('act'), v('authority'), v('formula'), v('bindings'), v('scene'))))
    text += definition('rip', params(GROUP), k('rhz', *args(FORM, declares=strengthened())))
    text += definition('riq', params(PURPOSE), k('rh7', *args(PURPOSIVE, declares=strengthened())))
    return text


MEANINGS = {
    'rim': '同じ順序付き個体引数列と同じ状況について、対象内容が偽なら応答内容が成立するという条件内容の関数。応答は実際の出来事とも処罰とも自動認定しない。対象内部に期間全体の条件があれば、その条件全体の不成立が前件となる。',
    'rin': 'rimの条件内容を満たすよう求める発話を、同じ引数列に対応させる関数。呼びかけの内容であり、前件・応答・対象内容の真理を断言しない。',
    'rio': 'rhxの同じ本人・表明行為・状況で、厳粛な表明と、記述で指す権威への指定発話の呼びかけがある。同じ引数列を呼びかけへ渡す。権威の実在、受領、信頼性や応答の発生は含めない。',
    'rip': 'rhzの全当事者の各引受けの同じ行為・時点で、rioの厳粛な表明と呼びかけがある。別の人や別の行為で行った儀礼を流用しない。',
    'riq': 'rh7の目的付き相互引受けの同じ行為に、全当事者についてripの条件を接続する。目的の主体と当事者の範囲を同一視せず、目的主体の引受け・呼びかけ・目的志向も同じ行為へ結ぶ。',
}
LIMITS = [
    'solemnは、本人が指定行為を通常のやり取りと区別した厳粛な表明として行うという関係。invokesは、本人がその行為で、権威の記述へ、同じ引数列で指定する発話を呼びかける関係。慣習上の認定や厳粛さの基礎説明は残る。',
    '権威は個体の性質の閉じた記述で与え、該当個体を存在量化しない。虚構・宗教上の対象への呼びかけを記述しても、その対象が実在すると断言しない。記述された性質が神・最高権威・全知を意味するとは型だけで保証しない。',
    '条項と呼びかけの一般引数は独立である。具体的な検査例では同じ条項関数をrinへ渡した閉じた適用記述を作る。型だけでは無関係な条項・呼びかけの組合せを排除しない。',
    'rimの対象の不成立は、故意の違反・虚偽の発言・期限超過を一般に同定しない。応答を処罰と読むには、別途その応答内容を構成する必要がある。応答の主体・対象・期間の対応は渡す関数の意味規約で指定する。',
    'この構成は制裁を呼び求める宣誓への候補であり、非宗教的な宣誓や全文化の宣誓の必要十分条件ではない。慣用式の発話と実際の信念・誠実さ・履行・法的効力は区別する。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    before = 'i[first d second d][' + k('ic', v('first'), v('second'), v('context')) + ']'
    substitutions = dict(eligible='p aa', occurs='p dg', performs='p f3', before=before)
    text = definitions() + definition('hzcv', params(SOURCE), k('rip', *args(GROUP, **substitutions)))
    text += definition('hzcw', params(SOURCE_PURPOSE), k('riq', *args(PURPOSE, aims='p hzu', **substitutions)))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-question-responses-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-solemn-undertakings-basis-v1', document='examples/v014/kant-solemn-undertakings.noema')
    basis['definitions'].update(MEANINGS | {
        'hzcv': 'ripを既存の人aa、行為の生起dg、表明する側f3、同じ評価文脈の時間順序icへ接続する。厳粛さと権威への呼びかけは意味規約を明示した引数で受け取る。',
        'hzcw': 'hzcvの厳粛な引受けへ、同じ表明行為の目的志向hzuを接続する。全当事者に同じ目的を補わず、目的の達成を要求しない。'})
    basis['unresolved'] += LIMITS + [
        'u0013のeidlichへの部分的な解釈注記。後年のカントの宣誓論は構成候補を検討する補助資料であり、1784年の本文へその論説全体を補っていない。原文には具体的な宣誓文・呼びかけ先・制裁内容が明示されないため、検査用の記述を実際の発言として追加しない。',
        '契約の正当性や制度的な資格、神・宗教・教会の一般的な構成説明、反語・強調、全文の著者帰属と意味確認は未完。新しい原始概念・著者主張は追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'solemn-undertakings')
def core_composed(): return projected(ROOTS + ['hzcv', 'hzcw'], 'solemn-undertakings-core')
BUILDERS = ((generic_composed, 'solemn-undertakings'), (source_composed, 'kant-solemn-undertakings'), (core_composed, 'solemn-undertakings-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored solemn undertaking differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
