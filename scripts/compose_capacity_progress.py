"""Ground a candidate intervention score in assessed independent-use capacity."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_bounded_hindrance import generic_composed as hindrance
from scripts.compose_scoped_counts import definitions as scope_definitions, generic_composed as counts

PARENT = 'examples/v014/kant-bounded-hindrance.noema'
PARAMS = ('population j[a] scope h[a] c before d worlds h[h[a] c] d earlier h[d d] c '
    'variables j[a] equations h[a h[a] c] c factor a tolerance b')
ARGS = 'v population v scope v before v worlds v earlier v variables v equations v factor v tolerance'
TRUE = 'e[n p a b][n p a b]'


def definitions():
    return '''
d rei[population j[a] property h[a] e before d after d] b[
 k ha[k hf[v population i[person a][t[c[v property][v person]][v after]]]
  k hb[n u b b k hf[v population i[person a][t[c[v property][v person]][v before]]]]]
].
d rej[population j[a] scope h[a] c assessed h[a] e before d after d earlier h[d d] c] c[
 w[k rcm[v population v scope]][w[c[v earlier][v before v after]][f person a[
  y[c[v scope][v person]][w[t[c[v assessed][v person]][v before]][t[c[v assessed][v person]][v after]]]
 ]]]
].
d rel[population j[a] property h[a] e before d worlds h[h[a] c] d] h[h[a] c] b[
 i[state h[a] c][k rei[v population v property v before c[v worlds][v state]]]
].
d rek[population j[a] scope h[a] c assessed h[a] e property h[a] e before d worlds h[h[a] c] d earlier h[d d] c variables j[a] equations h[a h[a] c] c factor a tolerance b] c[
 w[k ree[v variables v equations v factor]][w[
  k rw[v variables v equations i[item a][e[v item][v factor]] i[item a][''' + TRUE + ''']
   i[state h[a] c][k rej[v population v scope v assessed v before c[v worlds][v state] v earlier]]]
 ][w[k rw[v variables v equations i[item a][e[v item][v factor]] i[item a][u[''' + TRUE + ''']]
   i[state h[a] c][k rej[v population v scope v assessed v before c[v worlds][v state] v earlier]]]
 ][k reh[v variables v equations v factor k rel[v population v property v before v worlds] v tolerance]]]]
].
'''


MEANINGS = {
    'rei': '同じ個体列について、指定性質を満たす後の人数から、共通の前の人数を引く。増減の生の数値であり、重複・全列挙・評価の正当性はrejで検査する。',
    'rej': '対象範囲が非空で全て重複なく列挙され、共通の始点が終点より先であり、全対象の指定評価条件が前後とも成立する。対象者を結果に応じて選び直さない。',
    'rel': '同じ個体列・性質・始点を固定し、介入の割当てに対応する終点でのreiを返す数値尺度。評価の妥当性はこの生の数値関数だけからは導かない。',
    'rek': '両介入の全解で同じ対象列と始点についてrejが成立し、relの人数増減尺度で許容値を超える低下が全組で存在しない。未評価の人を性質の不成立として比較しない。',
}
LIMITS = [
    '対象範囲と列は全介入で固定する。人数の増減は、個人ごとの変化や因果的な獲得過程、能力の程度、知識の内容、制度の変化を全て表す尺度ではない。',
    '共通の始点からの増減を比較する。始点の人数が共通なので、両介入の増減差は終点人数の差と一致するが、各介入における実際の増減は別に保持する。',
    '評価済み条件の実世界での妥当性と、時間順序・範囲・介入の対応の正当性は別に確認する。有限列の全列挙と順序の検査だけで、現実の全人や全時点を確認したとはしない。',
    '生の数値rei/relを、rej/rekの検査なしで確認済みの進歩尺度として使わない。評価が欠ける場合と、評価した結果として能力がない場合を区別する。',
]


def generic_composed():
    text, basis = hindrance()
    doc = parse(text + scope_definitions() + definitions())
    basis = deepcopy(basis)
    basis.update(version='capacity-progress-basis-v1', document='examples/v014/capacity-progress.noema')
    count_basis = counts()[1]
    basis['definitions'].update({key: count_basis['definitions'][key] for key in ('rcm', 'rcn', 'rco')})
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = definitions() + '''
d hzg[''' + PARAMS + '''] c[
 w[f person a[y[c[v scope][v person]][k aa[v person]]]][
  k rek[v population v scope p fo p h4l v before v worlds v earlier v variables v equations v factor v tolerance]
 ]
].
d hzh[population j[a] before d worlds h[h[a] c] d] h[h[a] c] b[k rel[v population p h4l v before v worlds]].
d hzi[policy e ''' + PARAMS + '''] e[
 b context[w[t[v policy][v context]][w[k hze[v policy v variables v equations v factor v worlds]][w[
  k hzg[''' + ARGS + ''']
 ][k rv[v variables v equations i[item a][e[v item][v factor]] i[item a][''' + TRUE + ''']
  i[state h[a] c][e[c[v worlds][v state]][v context]]
 ]]]]]
].
'''
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-bounded-hindrance-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-capacity-progress-basis-v1', document='examples/v014/kant-capacity-progress.noema')
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'hzg': '対象範囲が全て人で、同じ対象と共通始点について両介入の全終点でfoの評価が整合し、h4lの自立的使用の能力を持つ人数の増減で比較した低下が許容値を超えない。単なる未成熟の否定や、未評価の不成立を人数へ代用しない。',
        'hzh': '同じ対象列・共通始点について、各介入の終点でのh4l該当人数の純増を返す数値関数。正当な比較の条件はhzgで別に確認する。',
        'hzi': '同じ政策が指定文脈で成立し、政策と介入要因が対応し、自立的使用能力の人数尺度でhzgが成立し、その文脈が制限あり側の解に対応する終点であるという内容。これを閉じた記述としてhzaの許可対象にできる。',
    })
    basis['unresolved'] += LIMITS + [
        '啓蒙の進歩の比較尺度を、既存fo・up・h4lで定義する能力の人数増減へ接続した候補である。h4l自体の方法・結果の評価基準と、原文の啓蒙の全意味の妥当性は未完。',
        '人数の純増が同じでも、誰が獲得し誰が失ったかは異なり得る。特定の個人への悪影響や分配上の問題を、集団全体の純増だけで無害と認定しない。',
        '能力を獲得する原因・離脱過程・自分の精神への働きかけが生じたことは、この前後人数の差だけからは導かない。原文を人数へ還元した完成訳として採用しない。',
        'hziは単なる現在の政策成立に加え、評価する文脈を同じモデルの制限あり側の終点へ結ぶ強い候補。政策の許可から実際の成立や進歩を推論しない。本文の新たな主張は追加しない。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'capacity-progress'), (source_composed, 'kant-capacity-progress')):
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored capacity progress differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Fixed-population progress score connected to assessed independent-use capacity')


if __name__ == '__main__':
    main()
