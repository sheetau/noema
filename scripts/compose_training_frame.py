"""Compose connected structural members and an intended training use."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_confinement import generic_composed as passage_composed


def definitions():
    return '''
d rah[device a members j[a] context d formed h[a d] c structural h[a a d] c connected h[a a d] c] c[
 w[c[v formed][v device v context]][w[
  g first a[g second a[w[k rac[v members v first]][w[k rac[v members v second]][u[e[v first][v second]]]]]]
 ][w[f part a[y[k rac[v members v part]][w[u[e[v part][v device]]][c[v structural][v device v part v context]]]]][
  f first a[f second a[y[w[k rac[v members v first]][k rac[v members v second]]][
   c[k rad[v members i[left a right a][x[c[v connected][v left v right v context]][c[v connected][v right v left v context]]]]][v first v second]
  ]]]
 ]]]
].
d rai[device a members j[a] users i[h[a] c] activity i[h[a] e] context d formed h[a d] c structural h[a a d] c connected h[a a d] c training h[a i[h[a] c] i[h[a] e] d] c bodily h[a a d] c movement h[a d] c] c[
 w[k rah[v device v members v context v formed v structural v connected]][w[
  c[v training][v device v users v activity v context]
 ][w[c[v movement][v device v context]][g part a[w[k rac[v members v part]][c[v bodily][v device v part v context]]]]]]
].
'''


def generic_composed():
    text, basis = passage_composed()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='training-frame-basis-v1', document='examples/v014/training-frame.noema')
    basis['definitions'].update({
        'rah': '意図的に形成された装置について、区別できる二つ以上の構造部分を選び、全てが同じ装置の真の構造部分で、選んだ部分の間の物理的な接続が連結している。自己を部分として数えず、列外の部分を経路に借用しない。',
        'rai': 'rahの構成を持つ装置が、記述された利用者群による活動の習得を目的とし、その構造部分に身体を支える配置を持ち、当該活動の身体運動を許す配置を持つ。利用者や活動の記述を実行して成功を要求しない。'})
    basis['unresolved'] += [
        '構造部分は材料を別々に製造した部品に限らず、一体成形した装置でも区別できる部分を選べる。対象となる構成の部分リストを記述者が与える。',
        '構造部分、接続、意図的形成、支持・運動の配置、学習用途は明示的な関係である。材料力学、設計行為や目的一般を説明し終えたとはしない。',
        '用途は利用者群と活動への記述を保持する。実際の利用者がその群に属すること、現在の使用、成功・有効性・安全性は要求しない。',
        'これは身体支持を伴う訓練用の構成であり、全ての道具や全種類の歩行補助具を網羅する定義ではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-confinement.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r zaa[a d] j[a].r zab[a a d] c.r zac[a a d] c.r zad[a d] c.
r zae[a i[h[a] c] i[h[a] e] d] c.r zaf[a a d] c.r zag[a d] c.
r zah[a] c.r zai[a a d] c.r zaj[a a d] c.r zap[] a.
d zal[person a] e[b context[g act a[w[k zai[v person v act v context]][u[k zaj[v person v act v context]]]]]].
d zam[device a] e[b context[
 k rai[v device k zaa[v device v context] r[p zah] r[p zal] v context p zad p zab p zac p zae p zaf p zag]
]].
d zan[being a] e[b context[w[t[k q4[v being]][v context]][t[k zam[k qs[v being v context]]][v context]]]].
d zao[] c[k qh[k zap[] k wa[] r[p q3] r[p zan] k wh[]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-confinement-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-training-frame-basis-v1', document='examples/v014/kant-training-frame.noema')
    general = generic_composed()[1]
    basis['definitions'].update({key: general['definitions'][key] for key in ('rah', 'rai')})
    decls = {d['name']: d for d in doc['declarations']}
    for name, args, meaning in (
        ('zaa', ['device', 'context'], 'この装置で枠の構成を記述するために選んだ構造部分の列。全装飾・全材料を列挙する条件ではない。'),
        ('zab', ['device', 'part', 'context'], 'その対象が同じ装置の形と荷重の保持に関わる構造部分である。単なる近接や所持とは区別する。'),
        ('zac', ['first_part', 'second_part', 'context'], '同じ構成の部分間に、力を伝え形を保つ物理的な接続がある。接続の意味は対称的に使い、因果の向きとは区別する。'),
        ('zad', ['device', 'context'], 'この対象は、材料の形や配置を意図的に整えて作られた物体である。偶然に似た形になった物を同一視しない。'),
        ('zae', ['device', 'users_description', 'activity_description', 'context'], 'この装置の設計上の用途は、記述された利用者群が記述された活動を習得することである。用途の帰属であり、有効性や習得済みという事実は含まない。'),
        ('zaf', ['device', 'part', 'context'], 'この装置のこの部分は、使用時に利用者の身体を支え、立った姿勢を保つための配置を持つ。現在の支持の実行とは区別する。'),
        ('zag', ['device', 'context'], 'この装置は、身体を支える位置から足を接地させ、脚を動かすための空間を持つ配置である。実際に歩くことや成功は要求しない。'),
        ('zah', ['person'], '通常の利用者として想定される、人間の身体発達の初期段階の子どもの分類。年齢の数値を固定せず、文化的・生物学的境界の説明は残る。'),
        ('zai', ['person', 'act', 'context'], '同じ身体が脚を動かし足で支持しながら位置を変える行為である。運動学の詳細や歩行と走行の境界はまだ未説明。'),
        ('zaj', ['person', 'act', 'context'], '同じ身体移動の行為で、他者や装置が足の接地とは別に身体を支える。地面からの通常の支持まで外部の歩行補助とはしない。'),
        ('zap', [], '身体支持と歩行学習の用途を持つ枠を、閉じ込めの描写に接続した部分注記の箇所。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
                                    'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'zal': '足による身体移動があり、同じ行為に他者や装置による身体支持がない。独りでの身体移動という用途の目標。知的な自立bbとは同一視しない。',
        'zam': '子どもによるzalの習得を用途とし、身体支持と脚の動作の空間を持つ構造を構成する。車輪数、材質、現在の使用者や成果を固定しない。',
        'zan': '同じ対象についての家畜・閉じ込めの描写q4に、対応する同じ装置qsがzamの構成と用途を持つことを加える。',
        'zao': '対象側q3と、装置の構成・用途を加えた描写側zanを、内容を実行せず比喩の注記として参照する。'})
    basis['unresolved'] += general['unresolved'][-4:] + [
        'Gängelwagenの構造・用途を部分的に合成した。歴史的な器具の形状の範囲、歩行の運動学、子どもの分類、設計と学習目的の一般説明は未完。',
        '元の対象者が子どもであることや、器具で実際に学習が促進されることは主張しない。閉じ込めの描写q4と、通常の学習用途zamを別に保持する。',
        '閉じ込めの開始・時間関係、穏順さ、許可・機会・勇気、比喩の評価的効果、全文の意味確認は引き続き残る。本文の既存9主張は変更しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/training-frame-basis-v1.json'),
                              (source_composed, 'data/kant-training-frame-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored training frame differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Connected structure and intended training purpose composed')


if __name__ == '__main__':
    main()
