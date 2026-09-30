"""Compose finite passage reachability and an explicitly scoped enclosure reading."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
d rac[nodes j[a] item a] c[q[v nodes][u[e[n p a b][n p a b]]][i[found c node a][x[v found][e[v node][v item]]]]].
d rad[nodes j[a] edges h[a a] c] h[a a] c[
 q[v nodes][i[from a to a][w[k rac[v nodes v from]][w[k rac[v nodes v to]][x[e[v from][v to]][c[v edges][v from v to]]]]]][
  i[reachable h[a a] c via a][i[from a to a][x[c[v reachable][v from v to]][
   w[c[v reachable][v from v via]][c[v reachable][v via v to]]
  ]]]
 ]
].
d rae[nodes j[a] inside h[a] c outside h[a] c] c[
 f place a[y[k rac[v nodes v place]][u[w[c[v inside][v place]][c[v outside][v place]]]]]
].
d raf[nodes j[a] edges h[a a] c start a outside h[a] c] c[
 g end a[w[k rac[v nodes v end]][w[c[v outside][v end]][c[k rad[v nodes v edges]][v start v end]]]]
].
d rag[nodes j[a] inside h[a] c outside h[a] c edges h[a a] c removed h[a a] c start a] c[
 w[k rae[v nodes v inside v outside]][w[k rac[v nodes v start]][w[c[v inside][v start]][w[
  k raf[v nodes v edges v start v outside]
 ][u[k raf[v nodes i[from a to a][w[c[v edges][v from v to]][u[c[v removed][v from v to]]]] v start v outside]]]]]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'confinement-basis-v1', 'document': 'examples/v014/confinement.noema', 'primitives': [],
        'definitions': {
            'rac': '場所が明示した有限列に含まれる。重複は到達関係を変えない。',
            'rad': '指定した場所だけを端点・中間点とする、移動辺の反射的推移閉包。各場所を順に中間点へ加え、経路を構成する。列外へは到達したとしない。',
            'rae': '指定した場所について内部と外部の分類が重ならない。境界など、両方でない場所を許す。',
            'raf': '出発場所から、指定した外部の場所へ有限回の移動で到達できる。方向を保持し、同じ場所にいる零回の経路も扱う。',
            'rag': '本人の場所が内部にあり、同じ移動辺では外部へ到達できるが、指定した辺を取り除くと到達できなくなる。内部・外部は重ならず、出発点も指定範囲内である。'},
        'unresolved': [
            '有限の場所・移動辺が可能な移動を尽くすという規約に相対的な定義である。省いた出口を不可能とする根拠はこの定義から導かない。',
            '場所は通行可能性についての状態を表せる。連続空間、時間で変わる障害、身体の姿勢や道具の変化は必要に応じて状態・辺へ明示する。',
            '削除比較だけで現実の因果を証明しない。制限前から移動できない場合や、制限以外の背景も同時に変わる場合は、この強い条件では閉じ込めを認定しない。',
            '実際の脱出、脱出する意思、脱出の許可、恐れによる不実行、内部へ移した行為とは区別する。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-husbandry-depiction.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r qs[a d] a.r qt[a d] j[a].r qu[a a d] c.r qv[a a d] c.r qw[a d] a.
r qx[a a a a a d] c.r qy[a a a a a d] c.r qz[a a a a d] c.r q5[] a.r q7[a a a d] c.
d q2[being a carrier a] e[b context[
 g restriction a[w[k q7[v restriction v being v carrier v context]][w[
  k rag[k qt[v carrier v context] i[place a][k qu[v carrier v place v context]]
   i[place a][k qv[v carrier v place v context]]
   i[from a to a][k qx[v restriction v being v carrier v from v to v context]]
   i[from a to a][k qy[v restriction v being v carrier v from v to v context]] k qw[v being v context]]
 ][g act a[w[k dg[v act v context]][w[k qz[v act v restriction v being v carrier v context]][
  g keeper a[w[k hg[k mp[k db[]] v keeper]][w[k aa[v keeper]][k df[v keeper v act v context]]]]
 ]]]]]]
]].
d q3[being a] e[b context[w[t[k qj[v being]][v context]][t[k er[k db[] v being]][v context]]]].
d q4[being a] e[b context[w[t[k qk[v being]][v context]][t[k q2[v being k qs[v being v context]]][v context]]]].
d q6[] c[k qh[k q5[] k wa[] r[p q3] r[p q4] k wh[]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-husbandry-depiction-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-confinement-basis-v1', document='examples/v014/kant-confinement.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    decls = {d['name']: d for d in doc['declarations']}
    for name, args, meaning in (
        ('qs', ['being', 'context'], '描写中、その対象が入れられている装置。歩行器の構造や用途はこの識別関数から導かず、未説明とする。'),
        ('qt', ['carrier', 'context'], '同じ装置・文脈の移動可能性を検討する有限の場所の列。外部と中間の場所も含む。'),
        ('qu', ['carrier', 'place', 'context'], '同じ装置に対してその場所が内部にある。装置と場所は別の対象である。'),
        ('qv', ['carrier', 'place', 'context'], '同じ装置に対してその場所が外部にある。内部でないだけでは外部とせず、境界を残す。'),
        ('qw', ['being', 'context'], '同じ対象がこの描写の時点で占める場所。'),
        ('qx', ['restriction', 'being', 'carrier', 'from', 'to', 'context'], 'この制限を取り除き他の背景を固定した場合、この対象が装置周辺で一段階に移動できる方向付きの関係。目的や許可ではない。'),
        ('qy', ['restriction', 'being', 'carrier', 'from', 'to', 'context'], '同じ制限が同じ対象・装置・文脈で、その移動辺を通れなくする。辺を削除するモデルを明示した読み。'),
        ('qz', ['act', 'restriction', 'being', 'carrier', 'context'], 'この実際の行為が、同じ対象・装置へその制限を適用している。行為者と生起はdf・dgへ別に結ぶ。'),
        ('q5', [], '家畜の描写に閉じ込めの関係を加えた比喩の部分的な注記箇所。'),
        ('q7', ['restriction', 'being', 'carrier', 'context'], 'この制限・対象・装置・文脈について、qtの場所とqxの移動辺が検討すべき移動の可能性を尽くすという明示的な前提。現実の完全性の自動認定ではない。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
                                    'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'q2': '明示した完全性の前提とragの閉じ込め条件に加え、同じ制限を同じ対象・装置へ適用する実際の行為に、後見人集団内の人が参加する。全構成員が直接参加したとは補わない。',
        'q3': '同じ人の監督対象としての性質qjと、活動の試みを制約する既存の部分的な読みerを結ぶ対象側の記述。',
        'q4': '家畜の描写qkに、同じ対象が対応する装置内で移動を制限されるq2を結ぶ。装置を歩行器として定義し終えたという条件ではない。',
        'q6': '対象側q3と身体的な描写側q4を、内容を実行せず比喩の提示として参照する部分注記。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        '歩行器の物理的な構成と学習補助の用途、穏順さ、原文の許可・機会・勇気、閉じ込めの開始行為と時間順序は未接続である。',
        'これは移動辺の削除として明示した強い読みである。身体的描写の全意味や、規範的・心理的な制約の全場合を包含しない。',
        '本文の既存9主張は変更しない。q6を著者の独立した新しい主張としては追加せず、原文の相対節に対応する部分注記として保持する。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/confinement-basis-v1.json'),
                              (source_composed, 'data/kant-confinement-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored confinement differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Finite passage closure and scoped confinement composed')


if __name__ == '__main__':
    main()
