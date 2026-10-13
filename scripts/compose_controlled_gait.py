"""Require positive control throughout a completed locomotion episode."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, call, definition
from scripts.compose_persistence import generic_composed as persistence

PARENT = 'examples/v014/kant-self-achievement.noema'


def definitions():
    phase = lambda name: app(v('scope'), v(name))
    earlier = lambda first, last: app(v('before'), v(first), v(last))
    params = ('history h[d] c before h[d d] c scope h[d] c person a act a last d '
        'occurs h[a d] c locomotion h[a a d] c balance h[a a d] c placement h[a a d] c')
    return definition('rcq', params, both(call('tb', v('history'), v('scope'), v('before')),
        phase('last'), quant('g', 'first', 'd', both(phase('first'), earlier('first', 'last'))),
        app(v('occurs'), v('act'), v('last')), app(v('locomotion'), v('person'), v('act'), v('last')),
        quant('f', 'point', 'd', op('y', phase('point'), both(
            op('x', op('e', v('point'), v('last')), earlier('point', 'last')),
            app(v('balance'), v('person'), v('act'), v('point')),
            app(v('placement'), v('person'), v('act'), v('point')))))))


def generic_composed():
    text, basis = persistence()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='controlled-gait-basis-v1', document='examples/v014/controlled-gait.noema')
    basis['definitions']['rcq'] = '同じ順序付き履歴の空でない区間に、指定した完了点とそれより前の点があり、全点が完了点以前である。同じ本人・活動が身体移動として生起し、区間全体で本人の同じ活動の身体の均衡と足の配置の制御が成立する。端点だけの安定や転倒の不在だけでは認定しない。'
    basis['unresolved'] += [
        'scopeは同じ活動の評価対象の全過程を表す。履歴が現実の連続した時間を尽くすことは、有限の点による検査からは得られない。都合のよい安定した区間だけを選ぶ正当化でもない。',
        '均衡・配置の制御と身体移動は引数の意味規約であり、力学的な方程式や知覚運動機構を説明し終えたものではない。尺度・許容差・外乱への応答は別途必要である。',
        '一つの完了した活動を記述する。あらゆる外乱への頑健性、将来の無事故、他の活動の制御、補助者や装置の不在は要求しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''r h4v[a a d] c.r h4w[a a d] c.r h4x[a d d] c.
d h4y[person a act a last d anchor d] c[
 w[k ia[v person v anchor v anchor]][w[x[e[v last][v anchor]][k ic[v last v anchor v anchor]]][
  k rcq[i[point d][k ia[v person v anchor v point]] i[first d final d][k ic[v first v final v anchor]]
   i[point d][k h4x[v act v last v point]] v person v act v last p dg p zai p h4v p h4w]
 ]]
].
d h4z[person a] e[b anchor[g act a[g last d[k h4y[v person v act v last v anchor]]]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-self-achievement-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-controlled-gait-basis-v1', document='examples/v014/kant-controlled-gait.noema')
    generic = generic_composed()[1]
    basis['definitions']['rcq'] = generic['definitions']['rcq']
    decls = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('h4v', ['person', 'act', 'point'], 'この同じ脚による移動中、本人の身体の姿勢・支持への荷重の移し方が制御され、均衡を保っている。単に転倒していないことや偶然支えられた結果だけとは区別する。具体的な力学条件・許容差・制御機構は未説明。'),
        ('h4w', ['person', 'act', 'point'], 'この同じ移動中、本人の足の置き方や接地の更新が、行おうとする移動の方向・支持に沿って制御されている。毎瞬間足を動かしていることではなく、現在の配置や次の配置への移行を制御している。機構と誤差の尺度は未説明。'),
        ('h4x', ['act', 'last', 'point'], 'この完了点で記述する同じ身体移動の全過程の範囲に入る状況。安定していた部分だけを切り出す範囲ではない。非空性・完了点・時間順序・間の欠落はrcqで別に検査する。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update({
        'h4y': '同じ本人の同じ基準文脈の履歴で、基準時までに完了した、脚による身体移動zaiにrcqの全過程の制御がある。既存dg・ia・icへ接続し、zalの外部補助の不在は追加しない。',
        'h4z': '同じ本人について、基準時までにh4yを満たす身体移動があるという描写側の内容。自立の達成h4qや、知的活動の安定を直接には含意しない。'})
    basis['unresolved'] += generic['unresolved'][-3:] + [
        'einen sicheren Gang zu thunの身体的描写側の部分構成である。sicherの確信・安全性・技能の持続などの全語義、歩行と走行の境界、運動機構は未完。',
        '自立を達成した人h4qに身体移動h4zをそのまま論理積で課すと、原文の知的活動の比喩を現実の身体能力の条件へ変えてしまう。対象側の安定した知的活動との対応を作るまで、少数者の本文主張へ接続しない。',
        '同じ活動の身体制御は追加したが、dennochの譲歩、Daherの推論、成功者の数量への最終的な接続、原文との意味一致確認は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'controlled-gait'), (source_composed, 'kant-controlled-gait')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored controlled gait differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Completed foot locomotion with positive control over its whole episode composed')


if __name__ == '__main__':
    main()
