"""Separate a bounded change into confinement from its persisting condition."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_persistence import generic_composed as persistence
from scripts.compose_transitions import definitions as transition_definitions, generic_composed as transitions


def definitions():
    return '''
d raj[history h[d] c before h[d d] c process a subject a carrier a restriction a earlier d later d valid h[a a a d] c state h[a a a] e changes h[a d d] c affected h[a a d d] c applies h[a a a a d] c occurs h[a d] c] c[
 w[c[v valid][v subject v carrier v restriction v earlier]][w[c[v valid][v subject v carrier v restriction v later]][w[
  k th[v history v before v process v earlier v later v changes c[v state][v subject v carrier v restriction]]
 ][w[c[v affected][v subject v process v earlier v later]][w[c[v occurs][v process v later]][
  c[v applies][v process v restriction v subject v carrier v later]
 ]]]]]
].
'''


def generic_composed():
    text, basis = persistence()
    doc = parse(text + transition_definitions() + definitions())
    basis = deepcopy(basis)
    basis.update(version='confinement-onset-basis-v1', document='examples/v014/confinement-onset.noema')
    prior = transitions()[1]
    basis['definitions'].update({key: prior['definitions'][key] for key in ('tg', 'th')})
    basis['definitions']['raj'] = '同じ対象・装置・制限について評価が整った前後で、制限状態が不成立から成立へ移る。同じ実際の変化過程が対象に作用し、後端で同じ制限を同じ対象と装置へ適用する行為として生起する。'
    basis['unresolved'] += [
        '前状態の不成立を、情報不足による不成立と混ぜないため、両端で評価の妥当性を別に要求する。妥当性の意味規約は呼出側が定める。',
        '同じ制限についての成立開始であり、それ以前に他の制限が一切なかったことや、対象が装置の外にいたことは要求しない。',
        '変化過程と適用行為を同じ対象として結ぶ読みである。過程内部、唯一の開始時刻、身体移動の経路、意図と機構の説明は別に要する。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-training-frame.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r zba[a a a d d] c.r zbh[] a.
d zbb[being a carrier a restriction a] e[b context[
 w[k q7[v restriction v being v carrier v context]][
  k rag[k qt[v carrier v context] i[place a][k qu[v carrier v place v context]]
   i[place a][k qv[v carrier v place v context]]
   i[from a to a][k qx[v restriction v being v carrier v from v to v context]]
   i[from a to a][k qy[v restriction v being v carrier v from v to v context]] k qw[v being v context]]
 ]
]].
d zbc[being a carrier a restriction a context d] c[
 w[k q7[v restriction v being v carrier v context]][w[k rac[k qt[v carrier v context] k qw[v being v context]]][
  k rae[k qt[v carrier v context] i[place a][k qu[v carrier v place v context]] i[place a][k qv[v carrier v place v context]]]
 ]]
].
d zbd[being a carrier a restriction a process a earlier d later d anchor d] c[
 w[k raj[i[point d][k zba[v restriction v being v carrier v anchor v point]] p dd v process v being v carrier v restriction
  v earlier v later p zbc p zbb p ag p la p qz p dg]][
  g keeper a[w[k hg[k mp[k db[]] v keeper]][w[k aa[v keeper]][k df[v keeper v process v later]]]]
 ]
].
d zbe[being a carrier a restriction a anchor d] c[
 w[k zba[v restriction v being v carrier v anchor v anchor]][g process a[g earlier d[g later d[w[
  k zbd[v being v carrier v restriction v process v earlier v later v anchor]
 ][w[x[e[v later][v anchor]][k dd[v later v anchor]]][
  f point d[y[w[k zba[v restriction v being v carrier v anchor v point]][w[
   x[e[v later][v point]][k dd[v later v point]]
  ][x[e[v point][v anchor]][k dd[v point v anchor]]]]][w[
   k zbc[v being v carrier v restriction v point]
  ][t[k zbb[v being v carrier v restriction]][v point]]]]
 ]]]]]]
].
d zbf[being a] e[b anchor[w[t[k qk[v being]][v anchor]][w[t[k zam[k qs[v being v anchor]]][v anchor]][
 g restriction a[k zbe[v being k qs[v being v anchor] v restriction v anchor]]
]]]].
d zbg[] c[k qh[k zbh[] k wa[] r[p q3] r[p zbf] k wh[]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-training-frame-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-confinement-onset-basis-v1', document='examples/v014/kant-confinement-onset.noema')
    basis['definitions']['raj'] = generic_composed()[1]['definitions']['raj']
    decls = {d['name']: d for d in doc['declarations']}
    for name, args, meaning in (
        ('zba', ['restriction', 'being', 'carrier', 'anchor', 'point'], 'この対象・装置・制限を基準文脈で振り返るときの同じ時間履歴。端点だけでなく、成立後から基準時までの評価範囲を指定する。'),
        ('zbh', [], '閉じ込めの成立過程と継続を、歩行器と家畜の描写へ加えた部分注記箇所。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
                                    'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'zbb': '同じ対象・装置・制限に対する移動制限の状態。実際の適用行為が現在も生起していることを状態の条件には含めない。',
        'zbc': '移動範囲の完全性、実際の位置の列への所属、内部と外部の非重複を確認する。評価が欠けた前状態を、閉じ込めていなかったという証拠にしない。',
        'zbd': '同じ過程を、当該対象に作用する変化ag・laと、当該制限を当該対象・装置へ適用する行為dg・qzへ結び、後見人集団内の人が同じ行為に参加する。状態変化は同じzbb、両端の評価はzbcで保持する。',
        'zbe': '基準時までに同じ制限の成立過程があり、その後から基準時までの同じ履歴内の全時点で評価が整い、制限状態が続く。後の別の制限への置換を混ぜない。',
        'zbf': '家畜として描かれる同じ対象について、対応する同じ歩行訓練用の装置に、基準時まで持続する閉じ込めの成立過程がある。現在も閉じる行為が行われるとは要求しない。',
        'zbg': '対象側q3と成立過程を加えた描写側zbfを、両内容を実行せず参照する比喩の部分注記。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'][-3:] + [
        '閉じ込める行為に続いて同じ制限が持続すると読む時間的な候補である。原文の全時制・談話順序を確定したものではない。',
        '履歴は記述者が与える。有限検査では履歴外の連続時間や記載漏れを自動で補完しない。q7・zbaの現実への適合と、因果機構の説明は残る。',
        '既存の現在の適用行為を含むq2は保存し、成立過程と持続状態を分けたzbfを追加した。本文の既存9主張は変えない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/confinement-onset-basis-v1.json'),
                              (source_composed, 'data/kant-confinement-onset-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2)+'\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored confinement onset differs: '+name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Confinement onset and ongoing state separated')


if __name__ == '__main__':
    main()
