"""Separate prior experience, retained acquired response and its attributed reason."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, definition, call, lam
from scripts.compose_persistence import generic_composed as persistence
from scripts.compose_conditional_release import content_definition

PARENT = 'examples/v014/kant-conditional-release.noema'
COMMON = 'person a task i[h[a] e] now d history h[d] c before h[d d] c experience h[a a i[h[a] e] d] c'
ORIGIN = COMMON + ' contributes h[a a i[h[a] e] d d] c'
LEARNED = ORIGIN + ' settled h[a i[h[a] e] d] c'


def definitions():
    past = both(app(v('history'), v('earlier')), app(v('before'), v('earlier'), v('now')),
        app(v('experience'), v('person'), v('event'), v('task'), v('earlier')))
    origin = quant('g', 'event', 'a', quant('g', 'earlier', 'd', both(past,
        app(v('contributes'), v('event'), v('person'), v('task'), v('earlier'), v('now')))))
    valid = both(call('ta', v('history'), v('before')), app(v('history'), v('now')))
    args = [v(n) for n in ('person', 'task', 'now', 'history', 'before', 'experience', 'contributes')]
    text = definition('rcg', ORIGIN, both(valid, origin))
    text += definition('rch', LEARNED, both(call('rcg', *args), app(v('settled'), v('person'), v('task'), v('now'))))
    text += definition('rci', LEARNED, both(valid, op('u', call('rch', *args, v('settled')))))
    text += definition('rcj', COMMON, both(valid, quant('g', 'event', 'a', quant('g', 'earlier', 'd', past))))
    return text


def generic_composed():
    text, basis = persistence()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='learned-familiarity-basis-v1', document='examples/v014/learned-familiarity.noema')
    basis['definitions'].update({
        'rcg': '同じ順序付き履歴の現在より前に、本人が指定された活動を経験した出来事があり、その同じ経験が現在の同じ活動への反応傾向に寄与する。履歴と現在への所属を要求し、時系列だけから寄与を導かない。',
        'rch': 'rcgによる過去の経験の寄与と、現在も定着している反応傾向の両方を要求する。経験に由来する慣れの一つの構成であり、成功、適切さ、能力一般、今の実行を含意しない。',
        'rci': '正当な同じ履歴に現在が属し、rchの経験に由来する定着が成立しない。未確認や不正な履歴を不慣れと判定する演算ではない。',
        'rcj': '正当な同じ履歴の現在より前に、本人が指定された活動を経験した出来事がある。現在の定着や、その経験の現在への寄与は要求しない。'})
    basis['unresolved'] += [
        '経験、現在の反応の定着、経験から現在への寄与は引数の意味規約で与える。神経機構、定着の程度や頻度の閾値を確定せず、回数だけで慣れを認定しない。',
        '経験の全領域と関係の真偽を与える意味論である。未収集の経験を不存在、未測定の定着を不成立として入力してはいけない。未知の入力から否定を推定する仕組みではない。',
        '慣れの全語義、単なる刺激への馴化、生得的な反応、技能の適切さや成功保証との関係は別途記述する。過去に慣れていても現在失われた場合を許す。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''r h3e[a a i[h[a] e] d] c.r h3f[a i[h[a] e] d] c.
r h3g[a a i[h[a] e] d d] c.r h3h[a a d] c.r h3s[] a.
'''
    blocked = quant('g', 'object', 'a', quant('g', 'limb', 'a', both(
        call('h2f', v('limb'), v('person'), v('case')),
        call('h2h', v('object'), v('limb'), v('person'), v('movement'), v('case')))))
    movement = quant('g', 'movement', 'a', both(call('h3h', v('person'), v('movement'), v('case')), op('u', blocked)))
    extra += content_definition('h3j', 'person a', 'case', movement)
    history = lam('point', 'd', call('h2r', v('person'), v('case'), v('point')))
    before = 'i[first d last d][' + call('ic', v('first'), v('last'), v('case')) + ']'
    args = [v('person'), 'r[p h3j]', v('case'), history, before, 'p h3e']
    for name, operation in (('h3k', 'rch'), ('h3l', 'rci'), ('h3m', 'rcj')):
        extra += content_definition(name, 'person a', 'case', call(operation, *args,
            *([] if operation == 'rcj' else ['p h3g', 'p h3f'])))
    extra += 'd h3n[person a] e[k h2w[v person k wh[]]].\n'
    extra += 'd h3o[person a] e[k h2x[v person k wh[]]].\n'
    extra += content_definition('h3p', 'person a', 'case', both(
        op('t', call('h3l', v('person')), v('case')),
        op('t', call('h3o', v('person')), v('case')),
        call('ea', v('person'), 'r[p h3l]', v('person'), 'r[p h3o]', v('case'))))
    cases = lam('case', 'd', call('h2t', v('person'), call('wh'), v('case')))
    extra += content_definition('h3q', 'person a', 'anchor', both(op('e', v('anchor'), call('wh')),
        call('rc', v('person'), 'p h3n', 'p h3p', cases), call('re', v('person'), 'p h3n', cases)))
    selected = quant('g', 'object', 'a', call('h2s', v('object'), v('person'), call('wh')))
    extra += content_definition('h3r', '', 'anchor', both(op('e', v('anchor'), call('wh')),
        quant('f', 'person', 'a', op('y', both(call('aa', v('person')), selected),
            op('t', call('h3q', v('person')), v('anchor'))))))
    extra += definition('h3t', '', both(call('uc', call('h3s'), call('wa'), 'r[k h3r[]]', call('wh')),
        call('ue', call('h3a'), call('h3s'), call('wh'))))
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements + [{'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'h3t', 'arguments': []}}]
    basis = deepcopy(json.loads((ROOT / 'data/kant-conditional-release-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-learned-familiarity-basis-v1', document='examples/v014/kant-learned-familiarity.noema')
    generic = generic_composed()[1]
    basis['definitions'].update({name: generic['definitions'][name] for name in ('rcg', 'rch', 'rci', 'rcj')})
    decls = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('h3e', ['person', 'event', 'activity_description', 'point'], '本人が、この出来事で、記述された活動を行う経験をこの時点に持つ。経験の対象を構文として保持し、現在の実行や習熟、成功は含意しない。'),
        ('h3f', ['person', 'activity_description', 'case'], '本人に、記述された活動への反応の仕方が現在定着しており、毎回初めてとして対処の仕方を作り直す必要がない。反応の正しさ、成功保証、生得か経験由来かは別条件。定着の程度・安定性の基礎説明は未完。'),
        ('h3g', ['event', 'person', 'activity_description', 'earlier', 'case'], 'この本人のこの時点の経験が、現在のこの活動への反応の形成に因果的に寄与する。別の活動や人への寄与、単なる前後関係からは導かない。現在まで影響が残るが、定着の基準を満たすとは限らず、唯一・十分・必要な原因とは主張しない。'),
        ('h3h', ['person', 'movement', 'case'], '本人がこの身体運動によって自分の身体を空間内で移動させるという描写。誰かに運ばれるだけの移送と分ける。具体的な軌道、速度、全運動学は未定義。'),
        ('h3s', [], '足枷の除去を仮定する条件文に、不慣れという理由節を接続して提示する談話箇所。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update({
        'h3j': '本人の身体移動があり、その同じ運動について本人の足側に物体による物理的な阻害がない。運動における身体的自由の部分構成であり、法的許可・知的自立・あらゆる障害の不存在ではない。',
        'h3k': '同じ仮定内の順序付き履歴で、本人のh3jへの過去の経験が現在の反応の定着へ寄与し、その定着が現在もある。h3jの記述を経験・定着・寄与で共有する。',
        'h3l': '同じ仮定の正当な履歴に現在が属し、h3kの慣れが成立しない。経験が一度もないことや、活動が不可能であることまでは含意しない。',
        'h3m': '同じ仮定の履歴で、本人にh3jの過去の経験がある。h3kと比較するための定義であり、原文の経験回数は補わない。',
        'h3n': 'この文書の固定した基準文脈whで指定する対象を除去する、既存h2wの内容。',
        'h3o': 'この文書の同じ基準文脈whで指定する最小対象への不確かな跳躍h2x。引用内に開いた変数を置かず、元の指示対象を維持する。',
        'h3p': '同じ仮定状況で同じ人に不慣れh3lと不確かな跳躍h3oが成立し、説明では前者の記述を後者の原因として採用する。採用を逆向きにせず、一般的な因果法則や唯一の原因とはしない。',
        'h3q': '固定した文書文脈whについて、非空の同じ仮定集合で除去h3nなら理由付きの跳躍h3pが成立し、除去を満たす仮定もある。現在や別の文脈にそのまま移さない。',
        'h3r': '基準文脈whで除去対象が指定される同じ人々にh3qを提示する内容。理由の不慣れを除去が起きる仮定内に置く部分的な読み。',
        'h3t': '著者に理由付き条件文h3rを帰属させ、先行する条件文の箇所の後に置く。内容を実行せず、現実の出来事・不慣れ・原因を断言しない。'})
    basis['unresolved'] += generic['unresolved'][-3:] + [
        'weil er zu dergleichen freier Bewegung nicht gewöhnt istの部分的な読み。dergleichenの運動の種類への照応全体、自由の全条件、gewöhntの全語義、現在形と反事実条件の関係は未確定。',
        '身体的自由は足側の物理的阻害の不在までの構成であり、全身の制約・法的許可・知的活動への比喩を同義に扱わない。h3jへの慣れを、不確かな跳躍に関する技能や成功と同一化しない。',
        '理由節を、除去を満たす仮定内の不慣れとその説明への採用として接続した。現実の基準時にも不慣れが成立するという投射は別途検討する。理由の十分性、譲歩・限定、後続の少数者への推論は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'learned-familiarity'), (source_composed, 'kant-learned-familiarity')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored learned familiarity differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Past experience, acquired familiarity and hypothetical reasons composed')


if __name__ == '__main__':
    main()
