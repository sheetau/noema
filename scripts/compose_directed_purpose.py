"""Describe goal-bearing participation and directed coverage without unanimity."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-benevolent-framing.noema'
PARENT_BASIS = 'data/benevolent-framing-basis-v1.json'
FULL = 'examples/v016/kant-directed-purpose.noema'
CORE = 'examples/v016/directed-purpose-core.noema'
LIBRARY = 'examples/v016/directed-purpose.noema'
BASIS = 'data/directed-purpose-basis-v1.json'
GUIDES = 'h[a a a i[e] d] c'
MEANINGS = {
    'rqys': '指定した非空の行為者群の全員が、同じ状況で実際に生じる同じ行為へ能動的に参加する。目的や結果はこの条件に含めない。',
    'rqyt': '指定群に属し、同じ行為・閉じた目標記述・状況について目的関係を満たす人だけを選ぶ。群の外の意図を足さず、目標の真理は実行評価しない。',
    'rqyu': 'rqysの実際の参加者全員について、本人が同じ目標を目指すか、その目標を目指す同じ参加者から同じ行為・目標・状況に関する方向付けを受けている。少なくとも一人がその目標を目指す。方向付けは、供給者のその目標に向けた計画・働きかけが受け手の当該参加を実際に導く関係として渡す。単なる同席、肩書、無視された命令、偶然一致では満たさない。これは目的を担う参加者による直接の被覆条件であり、共同意図の全理論や必要十分条件とはしない。',
    'rqyv': '重複のない人間としての後見人群について、rqyuを同じ母集団mvの危険判断分布rqydへ適用する比較候補。方向付け関係は引数で明示し、本文が特定の指揮者や分担を述べたとはしない。',
    'rqyw': '現在のdoと同じ監督・負担・判断・因果条件に、全員共通の目的rqygの代わりにrqyvの方向付けを結ぶ比較内容。同じ生起行為が同じ危険判断分布へ寄与することを要求する。原文の確定訳として採用せず、方向付けの根拠と原文への適合は別に検証する。',
}
LIMITS = [
    '全員が同じ目的を持つ場合と、一部がその目的を担い他の参加者を実際に方向付ける場合を区別する。後者を一人が目指すだけの条件へ弱めない。',
    '直接の方向付けを引数として渡す。推移閉包、指揮権の正当性、相互承認、共通知識、全構成員の同意は補わない。中間担当者の連鎖はこの定義だけでは扱わない。',
    '全員が目指す場合には方向付けを要求しないため、共通目的の一致だけから共同意図を認定する定義ではない。全員共通の目的と共同意図は別問題である。',
    'どの人も目標を明示的に持たない制度的な集団目的や、複数の異なる行為の合成は対象外。既存のhzuを集団対象へ無断で拡張しない。',
    '方向付けの具体的な説明と原文による根拠は未確定。既存45文と現行の意味確認登録を変更せず、比較可能な記述を追加する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d rqys[agents h[a] c act a scene d occurs h[a d] c performs h[a a d] c] c[
 w[c[v occurs][v act v scene]][w[g actor a[c[v agents][v actor]]][
 f actor a[y[c[v agents][v actor]][c[v performs][v actor v act v scene]]]]]
].
d rqyt[agents h[a] c act a goal i[e] scene d aims h[a a i[e] d] c] h[a] c[
 i[actor a][w[c[v agents][v actor]][c[v aims][v actor v act v goal v scene]]]
].
d rqyu[agents h[a] c act a goal i[e] scene d occurs h[a d] c performs h[a a d] c aims h[a a i[e] d] c guides h[a a a i[e] d] c] c[
 w[k rqys[v agents v act v scene v occurs v performs]][w[
 g director a[c[k rqyt[v agents v act v goal v scene v aims]][v director]]
 ][f actor a[y[c[v agents][v actor]][g director a[w[
 c[k rqyt[v agents v act v goal v scene v aims]][v director]
 ][x[e[v actor][v director]][c[v guides][v director v actor v act v goal v scene]]]]]]]]
].
d rqyv[group a act a scene d guides h[a a a i[e] d] c] c[w[k hi[k mp[v group] p aa]][
 k rqyu[i[actor a][k hg[k mp[v group] v actor]] v act r[k rqyd[k mv[]]] v scene p dg p df p hzu v guides]
]].
d rqyw[group a guides h[a a a i[e] d] c] e[b scene[w[t[k dk[v group]][v scene]][w[t[k dn[k mv[]]][v scene]][
 w[t[k rqyd[k mv[]]][v scene]][g act a[w[k rqyv[v group v act v scene v guides]][
 k hzie[v act r[p rqye] k mv[] r[p rqyd] v scene]
 ]]]]]]].
'''


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not set(MEANINGS) & set(old.entries)
    statements = doc['statements']; doc['statements'] = []
    size = len(doc['declarations'])
    doc = parse(format_graph(doc, 'compact') + definitions()); doc['statements'] = statements
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqyu']), statements=[])
    core = deepcopy(doc); core.update(declarations=closure(doc, ['rqyw', 'do']), statements=[])
    basis = dict(status='directed_purpose_comparison_not_adopted_claim', document=FULL, library=LIBRARY,
        inherited_meaning_basis=PARENT_BASIS, parent=PARENT, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in doc['declarations'][size:]},
        limitations=LIMITS)
    return {FULL: format_graph(doc, 'compact')+'\n', CORE: format_graph(core, 'compact')+'\n',
        LIBRARY: format_graph(lib, 'compact')+'\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2)+'\n'}


def main():
    from scripts.audit_opening_scope import write_exact
    for path, content in build().items():
        write_exact(ROOT/path, content)
    print('Directed goal coverage composed without changing the active manuscript', flush=True)


if __name__ == '__main__':
    main()
