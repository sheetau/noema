"""Connect contextual minima and agent-bound release within hypothetical cases."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, call, app, op, both, quant, lam, definition
from scripts.compose_persistence import generic_composed as persistence
from scripts.compose_transitions import definitions as transitions, generic_composed as transition_basis

PARENT = 'examples/v014/kant-unending-persistence.noema'


def definitions():
    member = lambda name: app(v('scope'), v(name))
    leq = lambda a, b: app(v('leq'), v(a), v(b))
    ordered = both(quant('g', 'x', 'a', member('x')),
        quant('f', 'x', 'a', op('y', member('x'), leq('x', 'x'))),
        quant('f', 'x', 'a', quant('f', 'y', 'a', op('y', both(member('x'), member('y')), op('x', leq('x', 'y'), leq('y', 'x'))))),
        quant('f', 'x', 'a', quant('f', 'y', 'a', quant('f', 'z', 'a', op('y',
            both(member('x'), member('y'), member('z'), leq('x', 'y'), leq('y', 'z')), leq('x', 'z'))))))
    text = definition('rcd', 'scope h[a] c leq h[a a] c', ordered)
    text += definition('rce', 'item a scope h[a] c leq h[a a] c', both(call('rcd', v('scope'), v('leq')),
        member('item'), quant('f', 'other', 'a', op('y', member('other'), leq('item', 'other')))))
    params = ('history h[d] c before h[d d] c process a object a person a earlier d later d state h[a a] e '
        'changes h[a d d] c affected h[a a d d] c agent h[a a d] c terminates h[a a a d d] c')
    state = app(v('state'), v('object'), v('person'))
    text += definition('rcf', params, both(
        call('tg', v('history'), v('before'), v('process'), v('earlier'), v('later'), v('changes')),
        app(v('affected'), v('person'), v('process'), v('earlier'), v('later')),
        app(v('agent'), v('person'), v('process'), v('later')),
        app(v('terminates'), v('process'), v('object'), v('person'), v('earlier'), v('later')),
        op('t', state, v('earlier')), op('u', op('t', state, v('later')))))
    return text


def generic_composed():
    text, basis = persistence()
    doc = parse(text + transitions() + definitions())
    basis = deepcopy(basis)
    basis.update(version='conditional-release-basis-v1', document='examples/v014/conditional-release.noema')
    prior = transition_basis()[1]
    basis['definitions'].update({name: prior['definitions'][name] for name in ('tg', 'th')})
    basis['definitions'].update({
        'rcd': '指定した非空の対象範囲について、比較関係が反射的・推移的・全比較可能である。両方向の比較が成り立つ同順位を許し、比較できないことを同順位とみなさない。',
        'rce': 'rcdを満たす同じ範囲にその対象が属し、範囲内の全対象に対してその対象が以下である。複数の最小対象を許す。無限の範囲に最小対象が必ずあるとは主張しない。',
        'rcf': '同じ順序付き履歴の前後で、同じ本人が行う同じ過程が同じ対象との状態関係を終わらせる。本人への作用と終結関係を別に要求し、状態は前に成立し後に不成立となる。単なる不在、別の人による除去、無関係な変化や偶然の消失とは区別する。'})
    basis['unresolved'] += [
        '比較範囲と尺度の意味は引数で与える。数値を固定せず比較を表せるが、未知の比較を真偽で勝手に埋めたり、実際の幾何的な幅をこの論理だけで測定したりはしない。',
        '状態の終結は終結関係の意味規約で与える。前後の真偽の差だけで因果を認定しない。過程の内部、本人の意図、他の拘束の有無、技能の獲得や後続の動作は含めない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def content_definition(name, parameters, variable, body):
    return f'd {name}[{parameters}] e[b {variable}[{body}]].\n'


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''r h2n[a d] c.r h2o[a a d] c.r h2p[a a d] c.r h2q[a a a d d] c.
r h2r[a d d] c.r h2s[a a d] c.r h2t[a d d] c.r h2u[a a a d] c.r h2v[a d] c.r h3a[] a.r h3d[a d] a.
'''
    selected = lambda name: call('h2s', v(name), v('person'), v('anchor'))
    release = call('rcf', lam('point', 'd', call('h2r', v('person'), v('case'), v('point'))),
        'i[first d second d][' + call('ic', v('first'), v('second'), v('case')) + ']',
        v('process'), v('object'), v('person'), v('earlier'), v('case'), 'p h2j', 'p ag', 'p la', 'p df', 'p h2q')
    premise = both(quant('g', 'object', 'a', selected('object')),
        quant('f', 'object', 'a', op('y', selected('object'), quant('g', 'process', 'a', quant('g', 'earlier', 'd', release)))))
    extra += content_definition('h2w', 'person a anchor d', 'case', premise)
    scope = lam('item', 'a', both(call('h2p', v('person'), v('item'), v('anchor')), call('h2n', v('item'), v('case'))))
    comparison = 'i[first a second a][' + call('h2o', v('first'), v('second'), v('case')) + ']'
    extra += definition('h3c', 'person a anchor d case d ditch a', call('rce', v('ditch'), scope, comparison))
    ditch = call('h3d', v('person'), v('anchor'))
    minimum = call('h3c', v('person'), v('anchor'), v('case'), ditch)
    jump = quant('g', 'act', 'a', both(call('dg', v('act'), v('case')),
        call('h2u', v('person'), ditch, v('act'), v('case')), call('h2v', v('act'), v('case'))))
    extra += content_definition('h2x', 'person a anchor d', 'case', both(minimum, jump))
    antecedent = lam('subject', 'a', call('h2w', v('subject'), v('anchor')))
    consequence = lam('subject', 'a', call('h2x', v('subject'), v('anchor')))
    cases = lam('case', 'd', call('h2t', v('person'), v('anchor'), v('case')))
    extra += content_definition('h2y', 'person a', 'anchor', both(
        call('rc', v('person'), antecedent, consequence, cases), call('re', v('person'), antecedent, cases)))
    people = both(call('aa', v('person')), quant('g', 'object', 'a', selected('object')))
    extra += content_definition('h2z', '', 'anchor', quant('f', 'person', 'a',
        op('y', people, op('t', call('h2y', v('person')), v('anchor')))))
    extra += definition('h3b', '', call('uc', call('h3a'), call('wa'), 'r[k h2z[]]', call('wh')))
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements + [{'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'h3b', 'arguments': []}}]
    basis = deepcopy(json.loads((ROOT / 'data/kant-unending-persistence-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-conditional-release-basis-v1', document='examples/v014/kant-conditional-release.noema')
    generic = generic_composed()[1]
    basis['definitions'].update({name: generic['definitions'][name] for name in ('rcd', 'rce', 'rcf')})
    decls = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('h2n', ['ditch', 'case'], '描写中の地面にある、両側より低く細長く延びる溝状の地形。ここでは横断する対象として扱う。人工・自然の由来や全地形学は未定義。'),
        ('h2o', ['first_ditch', 'second_ditch', 'case'], '同じ描写状況で横断に関わる幅について、第一の溝が第二以下である。等幅を含み、深さ・長さ・危険度で置き換えない。'),
        ('h2p', ['person', 'ditch', 'anchor'], 'この基準文脈の同じ人物について、最も狭いという比較に採る溝の候補。仮定状況ごとに都合のよい別の候補群を選び直さない。'),
        ('h2q', ['process', 'object', 'person', 'earlier', 'later'], 'この同じ過程が、同じ物体による同じ人の足側の拘束状態を終わらせる。前後の状態差だけではなく終結への関与を要求する。'),
        ('h2r', ['person', 'case', 'point'], 'その人について、その仮定状況に至る描写内の同じ履歴に属する状況。現実の履歴iaと混ぜず、仮定ごとの過程を検討する。'),
        ('h2s', ['object', 'person', 'anchor'], 'この基準文脈の描写で、この人について先行する足枷を受けて指す除去対象。仮定内の後状態だけを見て対象を入れ替えない。規定と定型句の全てへの対応の確定は残る。'),
        ('h2t', ['person', 'anchor', 'case'], 'この人物・基準文脈の条件文を評価するために採る仮定状況。現実に起きた事実の列ではない。どの状況が比較として適切か、反事実条件の一般的な選択理論は未完。'),
        ('h2u', ['person', 'ditch', 'act', 'case'], 'この同じ人が、同じ活動で、足で跳び出し身体を一時的に支持から離して、その溝の一方から他方へ跳ぶという描写。技能の安定、反復可能性や実際の転倒を含意しない。'),
        ('h2v', ['act', 'case'], 'この同じ跳躍が、その動作・着地を確かなものとして遂行できない不安定な跳躍として描かれる。確率値、実際の失敗・転倒・傷害を補わない。不確かさの基礎尺度と全語義は未完。'),
        ('h3a', [], '足枷を取り払った場合の不確かな跳躍を提示する条件文の談話箇所。後続の不慣れによる説明は含めない。'),
        ('h3d', ['person', 'anchor'], 'この人物について、この基準文脈で最も狭い溝として指している一つの比較対象。幅の最小性はh3cで別に要求する。仮定状況ごとに指す対象を変えず、同幅の他の溝への跳躍を追加しない。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update({
        'h2w': '基準文脈で指定した除去対象が非空で、その全てについて、同じ本人が行い本人に作用する過程によって足側の拘束状態が真から偽へ移り、仮定状況で終結する。各対象の過程は同一である必要はない。',
        'h3c': '基準文脈で同じ人物について選んだ候補のうち、仮定状況で溝に該当する範囲に対する幅の最小対象。同幅の複数の対象を許す。',
        'h2x': '基準文脈で指している同じ対象h3dがh3cの最小対象であり、その溝について同じ本人の生起する跳躍があり、その跳躍が不確かである。同幅の全ての溝で別々に跳ぶこと、単に小さい溝、別人の跳躍、候補範囲の不在と区別する。',
        'h2y': '選んだ非空の仮定状況で、h2wならh2xという条件が成立し、h2wを満たす仮定状況も少なくとも一つある。既存rcとreを使い、実際の除去や跳躍、技能獲得を主張しない。',
        'h2z': '描写の基準文脈で除去対象が指定される人の全てについてh2yを提示する内容。人物と除去対象・比較候補を仮定の前後で保持する。',
        'h3b': '著者がこの箇所でh2zの条件付きの描写を主張するという帰属。内容を実行せず、現実の身体拘束や除去・跳躍の出来事を断言しない。'})
    basis['unresolved'] += generic['unresolved'][-2:] + [
        'Wer sie auch abwürfeからSprung thunまでの部分的な条件付き描写である。auch・dennochの譲歩や尺度的な効果、nurの限定、動詞法の全含意、後続のweil節はまだ記述していない。',
        '最小対象が同幅で複数あることを許し、文脈が指す一つの対象へ跳躍を結ぶ読みを置く。現実の全ての溝の最小値や唯一の最小対象を仮定せず、比較範囲と指示対象は明示的な文脈の前提である。',
        '足枷と跳躍の条件付き描写を接続したが、規定・定型句から離れた人の知的な活動への比喩対応全体は未完。本人に技能がない理由、自由な運動への不慣れ、後続の少数者の結論は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'conditional-release'), (source_composed, 'kant-conditional-release')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored conditional release differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Contextual minima and the same person releasing fixed restraints composed')


if __name__ == '__main__':
    main()
