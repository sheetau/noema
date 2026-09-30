"""Bind a produced condition to a joint act, its agents and its recipient."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
d raa[agents h[a] c person a result e description i[h[a] e] context d occurs h[a d] c participates h[a a d] c produces h[a a i[h[a] e] d] c] c[
 w[t[v result][v context]][w[g agent a[c[v agents][v agent]]][g act a[
  w[c[v occurs][v act v context]][w[
   f agent a[y[c[v agents][v agent]][c[v participates][v agent v act v context]]]
  ][c[v produces][v act v person v description v context]]]
 ]]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'caused-conditions-basis-v1', 'document': 'examples/v014/caused-conditions.noema',
        'primitives': [], 'definitions': {
            'raa': '指定した結果が本人について成立し、非空の行為者群が同じ生起する行為へ関与し、その行為が同じ本人に記述された結果を生じさせる。記述と内容の対応は呼出側で固定する。'},
        'unresolved': [
            '結果を生じさせる関係は、単なる先行、同時成立、原因説明への採用と別の意味規約として引数で与える。現実の因果機構を発見・立証する処理ではない。',
            '前状態の否定、能力の低下量、継続期間、行為者の意図、各行為者単独での十分性は含めない。必要なら別の条件として記述する。',
            '行為者群は同じ行為へ参加する。部分行為を持つ共同の行為を許すが、無関係な別々の行為を一つの因果的行為として集計しない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-example-deterrence.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r g3[a a i[h[a] e] d] c.
d g4[group a person a context d] c[w[k aa[v person]][w[k hi[k mp[v group] p aa]][
 k raa[i[agent a][k hg[k mp[v group] v agent]] v person k bj[v person] r[p bj] v context p dg p df p g3]
]]].
d g5[group a anchor d earlier d middle d] c[w[g person a[k dj[v person v anchor]]][w[
 k dd[v earlier v middle]
][f person a[y[k dj[v person v anchor]][w[k g4[v group v person v earlier]][t[k er[v group v person]][v middle]]]]]]].
d g6[group a] e[b anchor[w[t[k ew[v group]][v anchor]][g earlier d[g middle d[w[
 k dd[v middle v anchor]
][k g5[v group v anchor v earlier v middle]]]]]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-example-deterrence-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-caused-conditions-basis-v1', document='examples/v014/kant-caused-conditions.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    d = next(d for d in doc['declarations'] if d['name'] == 'g3')
    basis['primitives'].append({'symbol': 'g3', 'parameters': d['parameters'], 'result': d['result'],
        'arguments': ['act', 'person', 'condition_description', 'context'],
        'meaning_ja': 'この行為が同じ人について記述された状態を、この文脈で結果として生じさせる。単なる状態の共存、時間的先行、原因だと誰かが説明することとは区別する。因果機構の一般的な基礎説明は未完。'})
    basis['definitions'].update({
        'g4': '同じ後見人の非空の人間集団が関与する同じ行為が生起し、同じ対象者について理解の十分さakがないという既存bjの状態を生じさせる。未成熟bf、決意不足、勇気不足とは同一化しない。',
        'g5': '提示時点anchorで選ぶ対象者が非空で、その同じ対象者全員について、先にg4、その後に既存のモデル相対的妨害erが成立する。過去の時点で対象者を選び直さない。',
        'g6': '後見人の危険提示ewの前に、同じ対象者についてg4、erがこの順で成立する二状況がある。これまでのexへ先行する状態を生じさせる行為を追加した部分解釈である。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        'dumm gemachtを、この文脈での理解の不足bjを生じさせる行為として読む。dummの語義全体、侮蔑的評価、個人の一般的知性・価値の判定を表すものではない。数値の知能尺度や能力の減少量は補わない。',
        '理解の十分さakは既存の基礎関係であり、判断能力bkの否定や自立的使用能力の不在bfへ機械的に置き換えていない。akの基礎説明は依然として未完。',
        '先行する状態を生じさせる行為、妨害、危険提示の順を明示したが、家畜としての描写・所有、穏順さ、歩行器、転倒と歩行の比喩、慎重さ・焦点・譲歩、原刊照合と全文の意味確認は残る。',
        'g3を基本関係として与えただけで現実の因果を立証したとは扱わない。先行草案のerも明示的な介入モデルに相対的な読みのままである。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/caused-conditions-basis-v1.json'),
                              (source_composed, 'data/kant-caused-conditions-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored caused condition differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Causative result and fixed-recipient temporal chain composed')


if __name__ == '__main__':
    main()
