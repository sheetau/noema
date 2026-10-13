"""Keep a scoped negative history separate from evidence, action and ability."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-caused-conditions.noema'


def definitions():
    return '''
d rab[history h[d] c before h[d d] c anchor d] h[d] c[i[point d][
 w[c[v history][v point]][c[v before][v point v anchor]]
]].
d rac[scope h[d] c occurrence h[d] c] c[f point d[y[c[v scope][v point]][u[c[v occurrence][v point]]]]].
d rad[scope h[d] c positive h[d] c negative h[d] c] c[f point d[y[c[v scope][v point]][w[
 x[c[v positive][v point]][c[v negative][v point]]
][u[w[c[v positive][v point]][c[v negative][v point]]]]]]].
d rae[scope h[d] c positive h[d] c negative h[d] c] c[
 w[k rad[v scope v positive v negative]][k rac[v scope v positive]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'attempt-history-basis-v1', 'document': 'examples/v014/attempt-history.noema',
        'primitives': [], 'definitions': {
            'rab': '指定した履歴に属し、固定した基準状況より先行する状況の範囲。別履歴・同時点・将来を含めない。順序の妥当性は呼出側で検査する。',
            'rac': '指定範囲のどの状況でも対象の関係が成立しない。範囲が空なら真であり、未記録という意味ではない。',
            'rad': '指定範囲の各状況で肯定・否定の証拠分類がちょうど一つ成立する。未評価と矛盾した分類を拒否する。証拠の信頼性や範囲の網羅性をこの式だけでは証明しない。',
            'rae': 'radの分類が完全かつ矛盾せず、範囲内の全てが否定側である。肯定記録がないだけでは成立しない。racの意味論上の否定と、入力された証拠分類の確認を分ける。'},
        'unresolved': [
            '範囲・履歴・時間順序は引数で指定する。観測点を世界の全時点と同一視しない。',
            'radとraeは与えた分類の整合条件であり、証拠の正しさや現実の全履歴を調査済みだという認識論的保証ではない。',
            '対象の関係の否定だけから、禁止、実際の未実行、能力不足、未来にも成立しないことは導かない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r g7[a a i[h[a] e] d] c.
d h2[person a context d] c[w[k ia[v person v context v context]][
 k ta[i[point d][k ia[v person v context v point]] i[earlier d later d][k ic[v earlier v later v context]]]
]].
d h3[person a] e[b context[w[k h2[v person v context]][k rac[
 k rab[i[point d][k ia[v person v context v point]] i[earlier d later d][k ic[v earlier v later v context]] v context]
 i[point d][g agent a[k g7[v agent v person r[p bm] v point]]]
]]]].
d h4[person a] e[b context[w[k aa[v person]][k xg[v person k bm[v person] v context p ae p af p ap]]]].
d h5[person a] e[b context[w[t[k h3[v person]][v context]][w[
 t[k h4[v person]][v context]
][k ea[v person r[p h3] v person r[p h4] v context]]]]].
d h6[person a] e[b context[w[k h2[v person v context]][k rac[
 k rab[i[point d][k ia[v person v context v point]] i[earlier d later d][k ic[v earlier v later v context]] v context]
 i[point d][k ei[v person r[p bm] v point]]
]]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-caused-conditions-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-attempt-history-basis-v1', document='examples/v014/kant-attempt-history.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    decl = next(d for d in doc['declarations'] if d['name'] == 'g7')
    basis['primitives'].append({'symbol': 'g7', 'parameters': decl['parameters'], 'result': decl['result'],
        'arguments': ['agent', 'person', 'activity_description', 'context'],
        'meaning_ja': '第一の行為者が、本人による記述された活動の試みをこの状況で許容する。法的許可・命令だけに限定せず、試みをさせておく社会的関係として部分的に読む。実際の試み・成功・能力・物理的機会とは別条件。社会的許容の基礎説明は未完。'})
    basis['definitions'].update({
        'h2': '本人と固定した文脈の履歴が基準状況を含み、その履歴内の先行関係が厳密な全順序を満たす。現実の全時点の調査完了という意味ではない。',
        'h3': 'h2の履歴内の基準状況より前では、本人が自分の理解力を使うbmを試みることを許容した行為者がいない。manを特定の後見人へ固定せず、行為者ごとに許容の不在を保つ。',
        'h4': '本人は人であり、現在の整合した能力評価で、自分の理解力を使うbmを達成する方法がない。指導排除を含むbbや、理解の十分さakの否定とは区別する。未来全体の能力を否定しない。',
        'h5': '同じ本人のh3と現在のh4がともに成立し、そのh3の記述をh4の原因として説明に採用する。許容の不在から能力不足を論理的に導出したことにはしない。',
        'h6': '比較用定義。同じ過去範囲でbmを実際に試みたことがない。許容がなかったh3と同一視しない。原文の代わりにこの経験不在を断言しない。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        '第三段落の能力とweil節だけの部分解釈。vor der Handは評価状況への限定で保持し、具体的期間、将来の回復や永続的不能を補わない。wirklichの強調は未完。',
        'den Versuch davonの対象を直前の自分の理解力の使用bmへ結ぶ。他者の指導なしbbの条件を追加しない。lassenの社会的許容と実効的な機会の全容は未完。',
        '原文にh3からh4への普遍的な能力法則があるとはしない。説明への採用ea、内容の成立、現実の因果機構を区別する。',
        '第三段落の一般化の範囲、自然となった状態・愛着・規則と公式・足枷・跳躍の比喩・慣れ・少数者の成功は未記述。新しい無条件の本文主張は追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, name in ((generic_composed, 'attempt-history'), (source_composed, 'kant-attempt-history')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text),
                (ROOT / ('data/' + name + '-basis-v1.json'), json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored attempt history differs: ' + str(path))
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Scoped permission history, actual attempts and present ability composed')


if __name__ == '__main__':
    main()
