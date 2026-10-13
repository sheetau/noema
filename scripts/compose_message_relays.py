"""Compose finite, causally linked message routes without truth or adoption."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, call, definition
from scripts.compose_transitions import generic_composed as transitions

PARENT = 'examples/v014/kant-intragroup-change.noema'
MESSAGE = 'i[h[a] f]'
CONVEYS = 'h[a a a ' + MESSAGE + ' d] c'
RELAYS = 'h[a a a a ' + MESSAGE + ' d] c'
ROUTE = [('history', 'h[d] c'), ('before', 'h[d d] c'), ('eligible', 'h[a] c'),
    ('first', 'a'), ('rest', 'j[a]'), ('origin', 'a'), ('target', 'a'), ('subject', 'a'),
    ('description', MESSAGE), ('end', 'd'), ('sender', 'h[a] a'), ('recipient', 'h[a] a'),
    ('activity', 'h[a] a'), ('point', 'h[a] d'), ('occurs', 'h[a d] c'),
    ('presents', 'h[a a d] c'), ('conveys', CONVEYS), ('receives', CONVEYS), ('relays', RELAYS)]


def params(items):
    return ' '.join(name + ' ' + sort for name, sort in items)


def definitions():
    direct = [('actor', 'a'), ('target', 'a'), ('act', 'a'), ('subject', 'a'),
        ('description', MESSAGE), ('context', 'd'), ('occurs', 'h[a d] c'),
        ('presents', 'h[a a d] c'), ('conveys', CONVEYS)]
    invoke = lambda name, *names: app(v(name), *(v(n) for n in names))
    text = definition('rdb', params(direct), both(invoke('occurs', 'act', 'context'),
        invoke('presents', 'actor', 'act', 'context'),
        invoke('conveys', 'act', 'target', 'subject', 'description', 'context')))
    text += definition('rdc', params(direct + [('receives', CONVEYS)]), both(
        call('rdb', *(v(n) for n, _ in direct)),
        invoke('receives', 'act', 'target', 'subject', 'description', 'context')))
    field = lambda name, step: app(v(name), v(step))
    valid = lambda step: both(app(v('history'), field('point', step)),
        app(v('eligible'), field('sender', step)), app(v('eligible'), field('recipient', step)),
        op('u', op('e', field('sender', step), field('recipient', step))),
        call('rdc', field('sender', step), field('recipient', step), field('activity', step),
            v('subject'), v('description'), field('point', step),
            *(v(n) for n in ('occurs', 'presents', 'conveys', 'receives'))))
    initial = 'i[last a][' + both(op('e', v('last'), v('first')),
        op('e', field('sender', 'first'), v('origin')), valid('first')) + ']'
    predecessor = quant('g', 'previous', 'a', both(app(v('state'), v('previous')),
        op('e', field('recipient', 'previous'), field('sender', 'step')),
        app(v('before'), field('point', 'previous'), field('point', 'step')),
        app(v('relays'), field('activity', 'step'), field('activity', 'previous'),
            field('sender', 'step'), v('subject'), v('description'), field('point', 'step'))))
    update = 'i[state h[a] c step a][i[last a][' + both(
        op('e', v('last'), v('step')), valid('step'), predecessor) + ']]'
    folded = 'q[v rest][' + initial + '][' + update + ']'
    text += definition('rdd', params(ROUTE), both(call('ta', v('history'), v('before')),
        quant('g', 'last', 'a', both(app(folded, v('last')),
            op('e', field('recipient', 'last'), v('target')), op('e', field('point', 'last'), v('end'))))))
    collective = [('audience', 'h[a] c'), ('firsts', 'h[a] a'), ('tails', 'h[a] j[a]'),
        ('ends', 'h[a] d')] + [(n, t) for n, t in ROUTE if n not in ('first', 'rest', 'target', 'end')]
    replacements = {'first': invoke('firsts', 'target'), 'rest': invoke('tails', 'target'),
        'end': invoke('ends', 'target')}
    text += definition('rde', params(collective), both(quant('g', 'target', 'a', invoke('audience', 'target')),
        quant('f', 'target', 'a', op('y', invoke('audience', 'target'),
            call('rdd', *(replacements.get(n, v(n)) for n, _ in ROUTE))))))
    text += definition('rdf', params(ROUTE + [('understands', 'h[a a ' + MESSAGE + ' d] c')]),
        both(call('rdd', *(v(n) for n, _ in ROUTE)), invoke('understands', 'target', 'subject', 'description', 'end')))
    return text


MEANINGS = {
    'rdb': '同じ生起する提示行為で、指定当事者が、指定対象についての同じ発話記述を指定受け手へ示す。受領、理解、賛同、内容の真理を要求しない。',
    'rdc': 'rdbの提示と、その同じ行為・受け手・対象・記述・状況における受領を要求する。',
    'rdd': '最初の受領段階と有限の後続列から、指定発信者から指定受け手までの経路を作る。各段階は適格な異なる送受信者のrdcであり、全て同じ対象と記述を保つ。後続段階の送信者は直前の受け手で、時点は同じ履歴で厳密に後、伝達はその直前の受領に由来する。終端の受け手と時点も固定する。',
    'rde': '非空の指定受け手範囲の全員へ、同じ発信者・対象・記述からrddの経路がある。各受け手の経路と終点は異なってよい。',
    'rdf': 'rddの経路に加え、最終受け手が同じ対象と発話記述を終点で理解している。賛同・真理や、理解がこの伝達だけに起因することは要求しない。',
}
LIMITS = [
    '送信段階の時点は受領を含む粗い完了状況である。媒体の移動時間、送出時刻と受領時刻の分離、誤伝達の訂正は未記述。',
    'relaysは直前の受領に基づく再伝達という来歴を与える。同じ情報を偶然別々に知っただけの二活動と区別するが、因果機構の証明ではない。',
    '有限経路には最初の段階が必ずあり、後続列が空でも一回の伝達を表す。最初の発信者が内容を初めて発見したことは要求しない。',
    '同じ正規化した発話記述を保持する。言い換え間の同義性、内容の変更を伴う伝播、無限経路、全人類への到達は保証しない。',
    '理解していない人による再伝達や、同じ人物への後の再到達を許す。各段階での自己送信は除外する。受領・理解・賛同・行動変化は同一ではない。',
]


def generic_composed():
    parent_text, parent_basis = transitions()
    doc = parse(parent_text)
    doc['declarations'] = [row for row in doc['declarations'] if row['name'] == 'ta']
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    basis = {'version': 'message-relays-basis-v1', 'document': 'examples/v014/message-relays.noema',
        'primitives': [], 'definitions': {'ta': parent_basis['definitions']['ta'], **MEANINGS}, 'unresolved': LIMITS}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = 'r h6e[a a a ' + MESSAGE + ' d] c.r h6f[a a a a ' + MESSAGE + ' d] c.r h6g[a a ' + MESSAGE + ' d] c.\n'
    inputs = [('first', 'a'), ('rest', 'j[a]'), ('origin', 'a'), ('target', 'a'), ('subject', 'a'),
        ('description', MESSAGE), ('end', 'd'), ('anchor', 'd'), ('sender', 'h[a] a'),
        ('recipient', 'h[a] a'), ('activity', 'h[a] a'), ('point', 'h[a] d')]
    substitutions = {'history': 'i[scene d][k ia[v origin v anchor v scene]]',
        'before': 'i[earlier d later d][k ic[v earlier v later v anchor]]', 'eligible': 'p aa',
        'occurs': 'p dg', 'presents': 'p f3', 'conveys': 'p f2', 'receives': 'p h6e', 'relays': 'p h6f'}
    route = call('rdd', *(substitutions.get(n, v(n)) for n, _ in ROUTE))
    extra += definition('h6h', params(inputs), both(call('ia', v('origin'), v('anchor'), v('anchor')),
        op('x', op('e', v('end'), v('anchor')), call('ic', v('end'), v('anchor'), v('anchor'))), route))
    extra += definition('h6i', params(inputs), both(call('h6h', *(v(n) for n, _ in inputs)),
        call('h6g', v('target'), v('subject'), v('description'), v('end'))))
    group_inputs = [('group', 'a'), ('firsts', 'h[a] a'), ('tails', 'h[a] j[a]'), ('ends', 'h[a] d')] + [
        (n, t) for n, t in inputs if n not in ('first', 'rest', 'target', 'end')]
    member = call('hg', call('mp', v('group')), v('target'))
    replacements = {'first': app(v('firsts'), v('target')), 'rest': app(v('tails'), v('target')),
        'end': app(v('ends'), v('target'))}
    extra += definition('h6j', params(group_inputs), both(call('hi', call('mp', v('group')), 'p aa'),
        quant('g', 'target', 'a', member), quant('f', 'target', 'a', op('y', member,
            call('h6h', *(replacements.get(n, v(n)) for n, _ in inputs))))))
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-intragroup-change-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-message-relays-basis-v1', document='examples/v014/kant-message-relays.noema')
    decls = {row['name']: row for row in doc['declarations']}
    for name, args, meaning in (
        ('h6e', ['act', 'recipient', 'subject', 'message_description', 'context'], '同じ提示行為の指定対象に関する発話記述を、その受け手が受け取った。単に宛てられただけの場合と区別する。知覚・読解等の媒体上の取得であり、意味の理解や賛同は含まない。'),
        ('h6f', ['next_act', 'previous_act', 'relay_person', 'subject', 'message_description', 'context'], 'この当事者が前の提示行為から受け取った指定対象・発話記述に基づいて、後の行為で同じ内容を再伝達する。独立した取得や単なる同時生起と区別する。媒体・記憶・因果機構の構成説明は未完。'),
        ('h6g', ['recipient', 'subject', 'message_description', 'context'], 'この受け手が、指定対象について記述された発話の意味をこの状況で理解している。文の真理、同意、行為への採用は含まない。理解の評価基準と学習過程の構成説明は未完。')):
        declaration = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': declaration['parameters'], 'result': declaration['result'],
            'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h6h': '同じ発信者の基準文脈の実際の履歴で、人の間のrddの伝達経路を記述する。終端は基準時以前であり、記述された発話の内容は実行評価しない。',
        'h6i': 'h6hに加え、終点で受け手が同じ対象・発話記述を理解している。途中の人の理解や、受け手の賛同を補わない。',
        'h6j': '重複のない非空の人の集団mpの全員へ、それぞれh6hの経路がある。仲介者は集団外でもよく、同時に全員へ提示する必要もない。原文の周囲という範囲をこの全員へ無条件に同定しない。'})
    basis['unresolved'] += LIMITS + [
        'um sich verbreitenの伝達経路の部分構成である。理性的な自己価値の評価・各人の自己思考の使命・Geistという態度の伝播・未来の様相はこの記述へ未接続。発話の転送と態度の普及を同義とはしない。',
        '指定した受け手集団への到達と公衆の公開性は異なる。利用機会の開放、読者世界、到達と理解の程度、集団の自己啓蒙との因果的接続は未完。',
        '内容を原語の文字列へ格納しない。Noemaの発話定義を参照するが、今回の原文側の対象・内容はパラメーターとして残り、未記述の内容を表現済みと数えない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'message-relays'), (source_composed, 'kant-message-relays')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored message routes differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Finite receipt and relay routes composed without endorsement')


if __name__ == '__main__':
    main()
