"""Bind a joint plan to a protective mechanism with the same member activity."""
import json
from copy import deepcopy

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_joint_readiness import ROOT, BASE, PLAN, av
from scripts.compose_origin_clock import definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import TRUE
from scripts.compose_community_protection import THREAT, THREAT_LINK
from scripts.compose_observed_protection import THREAT_OBSERVATION, STATE

JOINT = 'examples/v016/joint-readiness.noema'
PROTECTION = 'examples/v014/observed-protection.noema'
LIBRARY = 'examples/v016/collective-protection.noema'
EXAMPLE = 'examples/v016/collective-protection-example.noema'
BASIS = 'data/collective-protection-basis-v1.json'
MEMBERS = BASE[:6] + [('plan', 'a')]
MECHANISM = [(('modelgoal' if n == 'goal' else n), t) for n, t in THREAT_LINK if n != 'policy']
FIXED = PLAN + MECHANISM
POSSIBLE = BASE + MECHANISM
OBSERVED = FIXED + [('records', 'h[d] ' + STATE)]
OBSERVED_POSSIBLE = POSSIBLE + [('records', 'h[d] ' + STATE)]


def definitions():
    scope = 'i[person a][' + app(v('membersof'), v('group'), v('person'), v('anchor')) + ']'
    membergoal = app(v('goals'), v('planner'), v('group'), v('person'), v('plan'), v('anchor'))
    fulfilled = 'q[v members][' + TRUE + '][i[valid c person a][' + both(v('valid'), op('t', membergoal, v('point'))) + ']]'
    text = definition('ruv', params(MEMBERS), 'b point[' + both(k('rcm', v('members'), scope), fulfilled) + ']', 'e')
    replacements = {'goal': v('modelgoal'), 'policy': k('ruv', *av(MEMBERS))}
    def invoke(name, fields):
        return k(name, *[replacements.get(n, v(n)) for n, _ in fields])
    # The very same activity content is the joint goal and the causal target.
    text += definition('ruw', params(FIXED), both(k('rur', *av(PLAN), v('activity')),
        invoke('rks', THREAT), invoke('rku', THREAT_LINK)))
    text += definition('rux', params(POSSIBLE), quant('g', 'plan', 'a', k('ruw', *av(FIXED))))
    replacements.update(context=v('point'), observed=app(v('records'), v('point')))
    selected = app(v('selected'), v('planner'), v('group'), v('plan'), v('anchor'), v('point'))
    text += definition('ruy', params(OBSERVED), both(k('ruw', *av(FIXED)),
        quant('f', 'point', 'd', op('y', selected, invoke('rk2', THREAT_OBSERVATION)))))
    text += definition('ruz', params(OBSERVED_POSSIBLE), quant('g', 'plan', 'a', k('ruy', *av(OBSERVED))))
    return text


def build():
    doc = parse((ROOT / JOINT).read_text(encoding='utf-8'))
    old = parse((ROOT / PROTECTION).read_text(encoding='utf-8'))
    lookup = {d['name']: d for d in old['declarations']}
    keep, pending = set(), {'rks', 'rku', 'rk2'}
    while pending:
        name = pending.pop()
        if name in keep: continue
        keep.add(name); pending.update(_references(lookup[name]) - keep)
    assert not keep.intersection(d['name'] for d in doc['declarations'])
    doc['declarations'] += [deepcopy(d) for d in old['declarations'] if d['name'] in keep]
    library = parse(format_graph(doc, 'compact') + definitions())
    text = format_graph(library, 'compact')
    refs = {}
    for name, sort in OBSERVED:
        if name == 'goals': continue
        symbol = 'jg' + name
        if sort.startswith('h['):
            depth = 1
            for pos in range(2, len(sort)):
                depth += (sort[pos] == '[') - (sort[pos] == ']')
                if not depth: break
            text += 'r ' + symbol + '[' + sort[2:pos] + '] ' + sort[pos+1:].strip() + '.'
            refs[name] = 'p ' + symbol
        else:
            text += 'r ' + symbol + '[] ' + sort + '.'
            refs[name] = k(symbol)
    text += 'r jgexecuted[a a a a d d] c.'
    text += definition('jggoals', 'planner a group a person a plan a anchor d',
        'b point[k jgexecuted[v planner v group v person v plan v anchor v point]]', 'e')
    refs['goals'] = 'p jggoals'
    def invoke(name, fields): return k(name, *[refs[n] for n, _ in fields])
    text += 'q[t[' + invoke('ruv', MEMBERS) + '][k jganchor[]]].'
    text += 'q[' + invoke('rur', PLAN + [('activity', 'e')]) + '].'
    text += 'q[' + invoke('ruw', FIXED) + '].'
    text += 'q[' + invoke('rux', POSSIBLE) + '].'
    text += 'q[' + invoke('ruy', OBSERVED) + '].'
    text += 'q[' + invoke('ruz', OBSERVED_POSSIBLE) + '].'
    quoted = 'r b[' + invoke('ruy', OBSERVED) + ']'
    text += 'q[e[' + quoted + '][' + quoted + ']].'
    return {LIBRARY: format_graph(library, 'compact') + '\n', EXAMPLE: format_graph(parse(text), 'compact') + '\n'}


def basis():
    return dict(status='joint_activity_bound_to_a_specified_protective_mechanism', definitions={
        'ruv': '基準文脈の全構成員を過不足なく列挙し、同じ計画者・集団・計画の全構成員の目標が評価状況で成立する内容。利用可能性や結果の選択はこの内容へ混ぜない。',
        'ruw': '同じ計画で全員の目標と共通活動が成立するrurに、既存rksの保護比較とrkuの内容対応を加える。保護要因はruvそのものへ、モデル目標はrurと同じ活動内容へ結ぶ。',
        'rux': '固定した集団・基準文脈・保護機構のもとでruwを満たす計画が存在する。計画ごとに別の機構を選び直す意味ではない。',
        'ruy': 'ruwに加え、同じ計画の全評価結果における記録が介入前の方程式を満たし、同じ構成員の共同活動・共通活動・脅威の内容と対応することを既存rk2で確認する。',
        'ruz': '評価結果の記録が整合するruyの計画が存在する。計画・結果ごとに都合のよい機構へ変更しない。'}, limitations=[
        '原文の保証を検討するための強い保護の一解釈。脅威なし・集団活動なしで目的が成立し、脅威あり・集団活動なしで不成立、集団活動ありでは脅威の有無によらず成立することを各非空の全解へ要求する。',
        '方程式、脅威、比較状況、活動の内容は明示的な引数である。現実の因果機構や全脅威への対応を、真偽の一致だけで実証しない。',
        'ruvは構成員の指定目標の共同成立であり、軍隊の制度・訓練・指揮権・命令の正当性を定義しない。目標を実行した意図も追加しない。',
        '能力の評価対象と介入の比較状況は同一集合にしない。同じ内容を両方で使うが、全比較状況が利用可能な計画の実際の結果だとは要求しない。',
        'ruy/ruzの記録適合は評価対象の各結果に要求する。基準時点で集団活動や脅威が実際に成立することは要求せず、予測・仮想結果を現在の事実へ変えない。記録の取得方法や信頼性は別途必要。',
        '公的平穏、軍隊、啓蒙、恐れ、発話可能性と原文上位主張への接続は未完。新たな原文対応範囲は追加しない。'])


def main():
    for name, body in (build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}).items():
        path = ROOT / name
        if path.exists(): assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(name, len(body))


if __name__ == '__main__': main()
