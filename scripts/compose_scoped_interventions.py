"""Enumerate causal assignments over declared variables, not every individual."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

TRUE = 'e[n p a b][n p a b]'
FALSE = 'u[' + TRUE + ']'


def definitions():
    return '''
d rz[variables j[a] variable a] c[q[v variables][FALSE][i[found c item a][x[v found][e[v item][v variable]]]]].
d rs[variables j[a]] j[h[a] c][
 q[v variables][l[h[a] c][i[variable a][FALSE]]][i[states j[h[a] c] item a][
  q[v states][l[h[a] c][]][i[result j[h[a] c] state h[a] c][
   m[v result][l[h[a] c][
    i[variable a][x[e[v variable][v item]][c[v state][v variable]]]
    i[variable a][w[u[e[v variable][v item]]][c[v state][v variable]]]
   ]]
  ]]
 ]]
].
d rt[variables j[a]] c[
 f item a[c[
  q[v variables][i[seen c][TRUE]][i[continuation h[c] c current a][i[seen c][
   w[u[w[v seen][e[v current][v item]]]][c[v continuation][x[v seen][e[v current][v item]]]]
  ]]]
 ][FALSE]]
].
d ru[variables j[a] equations h[a h[a] c] c mask h[a] c fixed h[a] c state h[a] c] c[
 w[k rt[v variables]][w[
  f variable a[y[u[k rz[v variables v variable]]][u[c[v state][v variable]]]]
 ][q[v variables][TRUE][i[valid c variable a][w[v valid][w[
  y[c[v mask][v variable]][z[c[v state][v variable]][c[v fixed][v variable]]]
 ][y[u[c[v mask][v variable]]][z[c[v state][v variable]][c[v equations][v variable v state]]]]]]]]]
].
d rv[variables j[a] equations h[a h[a] c] c mask h[a] c fixed h[a] c goal h[h[a] c] c] c[
 q[k rs[v variables]][FALSE][i[found c state h[a] c][x[v found][
  w[k ru[v variables v equations v mask v fixed v state]][c[v goal][v state]]
 ]]]
].
d rw[variables j[a] equations h[a h[a] c] c mask h[a] c fixed h[a] c goal h[h[a] c] c] c[
 w[k rv[v variables v equations v mask v fixed i[state h[a] c][TRUE]]][
  q[k rs[v variables]][TRUE][i[valid c state h[a] c][w[v valid][
   y[k ru[v variables v equations v mask v fixed v state]][c[v goal][v state]]
  ]]]
 ]
].
d rx[variables j[a] equations h[a h[a] c] c factor a goal h[h[a] c] c] c[
 w[k rz[v variables v factor]][w[
  k rv[v variables v equations i[variable a][e[v variable][v factor]] i[variable a][FALSE] v goal]
 ][k rw[v variables v equations i[variable a][e[v variable][v factor]] i[variable a][TRUE]
  i[state h[a] c][u[c[v goal][v state]]]]]]
].
'''.replace('FALSE', FALSE).replace('TRUE', TRUE)


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'scoped-interventions-basis-v1',
        'document': 'examples/v014/scoped-interventions.noema', 'primitives': [],
        'definitions': {
            'rz': '変数の識別子が指定列に現れる。識別子は個体型だが、個体領域の全対象を変数として扱うわけではない。',
            'rs': '指定変数への全ての二値割当てを有限列として構成する。列外の識別子は偽に固定する。変数がn個なら2のn乗個を生成し、空列には一つの空割当てがある。',
            'rt': '変数の識別子が重複しない。真偽の状態を渡す関数の合成を有限列で畳み込み、同じ識別子を二回見た場合を拒否する。',
            'ru': '変数列が重複せず、列外は偽で、指定した変数では介入で固定した値、それ以外の変数では元の方程式と割当てが一致する。',
            'rv': '生成した割当てのうち、介入後の方程式を満たし目標も満たすものが存在する。',
            'rw': '介入後に少なくとも一つの解があり、その全てが目標を満たす。無解を保証として扱わない。',
            'rx': '要因が変数列に含まれ、それを偽にした側では目標を満たす解があり、真にした側では解が存在して全解で目標が不成立になる。同じ方程式と背景の下での、強い妨害の比較。'},
        'unresolved': [
            '変数と方程式、目標、背景条件の選定は記述者の仮定である。現実の因果機構を発見したり妥当性を認定したりするものではない。',
            '列外の識別子の値は偽に固定した全域関数として扱う。外部の変数が自由に変動するモデルではなく、必要な背景は方程式に明示する。',
            '個体領域の大きさによる全関数の列挙を避けるが、変数数については指数的な列挙である。大きいモデルの効率的な解法、確率的な傾向、部分的な妨害の全語義は含まない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-scoped-groups.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r ee[] a.r ef[] a.r eh[a a d] h[a h[a] c] c.r ei[a i[h[a] e] d] c.r ep[a a d] c.
d eg[] j[a][l[a][k ee[] k ef[]]].
d ej[person a] e[b context[k ei[v person r[p bb] v context]]].
d ek[group a person a context d] c[
 k rx[k eg[] k eh[v group v person v context] k ee[] i[state h[a] c][c[v state][k ef[]]]]
].
d eq[group a person a] e[b context[w[k hi[k mp[v group] p aa]][
 k rr[i[actor a][k hg[k mp[v group] v actor]] v context
  i[act a scene d][w[k dg[v act v scene]][k ep[v act v person v scene]]] p df]
]]].
d er[group a person a] e[b context[
 w[k ek[v group v person v context]][w[t[k eq[v group v person]][v context]][
  w[u[t[k ej[v person]][v context]]][
   k ru[k eg[] k eh[v group v person v context] i[variable a][FALSE] i[variable a][FALSE]
    i[variable a][x[w[e[v variable][k ee[]]][t[k eq[v group v person]][v context]]][
     w[e[v variable][k ef[]]][t[k ej[v person]][v context]]
    ]]
   ]
  ]
 ]]
]].
d es[group a] e[b context[w[g person a[k dj[v person v context]]][
 f person a[y[k dj[v person v context]][t[k er[v group v person]][v context]]]
]]].
'''.replace('FALSE', FALSE)
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-scoped-groups-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-scoped-interventions-basis-v1',
                 document='examples/v014/kant-scoped-interventions.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    decls = {d['name']: d for d in doc['declarations']}
    for name, args, meaning in (
        ('ee', [], 'このモデルで後見人群の対象への制約行為が適用されているかを表す二値変数の識別子。行為者自身を変数と同一視しない。'),
        ('ef', [], 'このモデルで本人が自分の理解力を他者の指導なしで使おうと試みるかを表す二値変数の識別子。試みと成功は区別する。'),
        ('eh', ['group', 'person', 'context'], 'この後見人群・本人・文脈の二変数に対して仮定する構造方程式。制約の適用を変える比較では、本人と背景を固定する。現実の心理機構へ適合するという証明ではない。'),
        ('ei', ['person', 'activity_description', 'context'], '本人がこの状況で記述された活動を試みる。活動の成功、許可、勇気が十分あることは別条件。'),
        ('ep', ['act', 'person', 'context'], 'この文脈で当該行為が、本人の活動を制約する条件を適用している。適用しただけで実際に試みが失われたとはしない。その結果は方程式による比較と実際の試みで別に検査する。')):
        declaration = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': declaration['parameters'],
            'result': declaration['result'], 'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'eg': 'この比較に使う二つの変数の列。全ての人や出来事を二値変数として列挙しない。',
        'ej': '自分の理解力を指導なしに使う既存内容bbを、活動の試みの対象として参照する。試みただけでbbが成立するとはしない。',
        'ek': '同じ後見人群・本人・文脈のモデルで、制約がない側では自立した試みが可能で、ある側では全ての解で試みがない。',
        'eq': '同じ後見人群の非空で重複のない人々が参加する一つの行為が実際に生じ、その行為が同じ本人へ制約条件を適用する。別人や別行為の制約を借用しない。',
        'er': 'ekの比較が成立し、実際にeqの制約があり、本人は試みておらず、この二つの観測から作った割当てが元の方程式の解でもある。モデルに合わない観測を妨害の成立として採用しない。',
        'es': '先行文で対象となった人々djが非空で、その全員について同じ後見人群によるerが成立する。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        'これはverhüteten以下を、自立した活動の試みを制約によって失わせると読む場合の、明示的なモデル内の強い解釈である。原文と同義な完成訳として採用したものではない。',
        'wagen durftenに含まれる許可・機会・勇気、慎重さと強調、家畜と歩行器の描写、その前の認知的な変化と後の危険提示は未接続。この断片だけを新しい著者の独立断言として追加しない。',
        'ehの変数選択と方程式の根拠、epによる制約条件の機構を、後続の具体的な説明へ接続する必要がある。結果がないだけでは制約による妨害としない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/scoped-interventions-basis-v1.json'),
                              (source_composed, 'data/kant-scoped-interventions-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored scoped intervention differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Explicit-variable interventions and an actual-observation prevention fragment composed')


if __name__ == '__main__':
    main()
