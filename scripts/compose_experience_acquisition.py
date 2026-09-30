"""Describe ordered experiences contributing to an assessed capacity change."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, definition

TRUE = 'e[n p a b][n p a b]'
FALSE = 'u[' + TRUE + ']'


def definitions():
    when = app(v('when'), v('event'))
    before = lambda a, b: app(v('before'), a, b)
    base = 'i[limit d][' + op('x', op('e', v('start'), v('limit')), before(v('start'), v('limit'))) + ']'
    step = 'i[prefix h[d] c event a][i[limit d][' + both(
        app(v('prefix'), when), op('u', before(when, when)),
        before(when, v('limit'))) + ']]'
    scan = op('q', v('events'), base, step)
    text = definition('r4', 'events j[a] when h[a] d before h[d d] c start d end d', both(
        op('u', op('e', 'd[v events]', 'n p a b')),
        op('u', op('e', v('start'), v('end'))),
        op('u', before(v('start'), v('start'))), op('u', before(v('end'), v('end'))),
        before(v('start'), v('end')), app(scan, v('end'))))
    common = 'person a process a events j[a] when h[a] d before h[d d] c start d end d'
    text += definition('r5', common + ' assessed h[a d] c capable h[a d] c transitions h[a d d] c affected h[a a d d] c experience h[a a d] c contributes h[a a a d d] c', both(
        'k r4[v events v when v before v start v end]',
        app(v('transitions'), v('process'), v('start'), v('end')),
        app(v('affected'), v('person'), v('process'), v('start'), v('end')),
        app(v('assessed'), v('person'), v('start')), app(v('assessed'), v('person'), v('end')),
        op('u', app(v('capable'), v('person'), v('start'))), app(v('capable'), v('person'), v('end')),
        op('q', v('events'), TRUE, 'i[valid c event a][' + both(v('valid'),
            app(v('experience'), v('person'), v('event'), when),
            app(v('contributes'), v('event'), v('person'), v('process'), v('start'), v('end'))) + ']')))
    return text


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'experience-acquisition-basis-v1',
        'document': 'examples/v014/experience-acquisition.noema', 'primitives': [],
        'definitions': {
            'r4': '非空の経験列の時点が、開始以上・終了未満にあり、列の順に厳密に先行する。各経験時点と両端で自己への先行を拒否し、同じ経験の重複も拒否する。',
            'r5': '同じ本人について、整合した評価で能力がない前状態から能力がある後状態へ、本人を対象とする同じ過程が結ぶ。r4の各経験を本人に結び、その各経験が同じ能力変化の過程に寄与することを要求する。'},
        'unresolved': [
            '時間順序・能力の評価基準・経験と過程の寄与関係は引数で与える。順序だけから因果的寄与を導かず、認知機構や経験一般の理論を確定しない。',
            'before引数は厳密な時間順序という意味規約を持つ。r4は隣接比較を一回ずつ合成し、引数全域の推移性・非循環性の検査器ではない。',
            '列は選んだ経験の列であり、全経験の網羅性や、各経験だけで能力変化を引き起こす十分性・必要性を要求しない。',
            '同じ時点の複数経験や、もともとある能力の程度的改善はこの取得条件に含まない。能力を得たことから現在の行為実行は導かない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-directed-presentations.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r f5[a a i[h[a] e] d] c.r f6[a d] c.r f7[a] d.r fh[a] j[a].r fi[a] d.
r fk[a a a d d] c.r fl[a d d] c.r fm[b d] c.r fu[] a.r fv[] a.
d fg[person a event a point d] c[w[k f5[v person v event r[p bb] v point]][
 w[g outcome d[k f6[v event v outcome]]][f outcome d[y[k f6[v event v outcome]][u[t[k bb[v person]][v outcome]]]]]
]].
d fo[person a] e[b point[w[k aa[v person]][k xe[v person v point p ae p af p ap]]]].
d fp[person a process a end d context d] c[w[k fm[d[k fh[v process]] v context]][
 k r5[v person v process k fh[v process] p f7 p dd k fi[v process] v end
  i[subject a point d][t[k fo[v subject]][v point]] i[subject a point d][t[k up[v subject]][v point]]
  p ag p la p fg p fk]
]].
d fq[person a context d] e[b end[g process a[k fp[v person v process v end v context]]]].
d fr[person a] e[b context[k ri[k fq[v person v context] v context i[end d][k fl[v person v context v end]] p tx]]].
d fs[] e[b context[w[g person a[k dj[v person v context]]][f person a[y[k dj[v person v context]][t[k fr[v person]][v context]]]]]].
d ft[] c[w[k uc[k fu[] k wa[] r[k e4[]] k wh[]]][w[
 k uc[k fv[] k wa[] r[k fs[]] k wh[]]
][w[k ud[k wa[] i[node a][e[v node][k fv[]]] k fu[] k wh[]]][k ue[k fu[] k fv[] k wh[]]]]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-directed-presentations-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-experience-acquisition-basis-v1', document='examples/v014/kant-experience-acquisition.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    declarations = {d['name']: d for d in doc['declarations']}
    for name, args, meaning in (
        ('f5', ['person', 'event', 'task_description', 'point'], 'この人がこの行為で、記述された活動をこの状況で試みる。試みたという経験を行為個体に結び、成功や能力を前提としない。'),
        ('f6', ['event', 'outcome'], 'この経験行為において生じた結果状況。行為一般の可能な結果候補ではなく、評価する履歴内の結果である。'),
        ('f7', ['event'], '経験行為の評価時点。列内では時点の異なる経験を用いる。具体的な日時を固定しない。'),
        ('fh', ['process'], 'この能力変化の過程で寄与を調べる経験行為の有限列。全人生の経験の網羅ではない。'),
        ('fi', ['process'], 'この過程の前状態を評価する状況。能力の評価条件と経験の時点は別途検査する。'),
        ('fk', ['event', 'person', 'process', 'start', 'end'], 'この人のこの前後状態を結ぶ能力変化の過程へ、この経験が因果的に寄与する。単なる前後・同時発生からは導かず、認知的な機構や唯一の原因までは指定しない。'),
        ('fl', ['person', 'context', 'candidate'], 'この人が経験によって能力を得ると著者が仮定的に見込む候補状況。würden ... wohlの部分的な読み。実現済みの履歴や全可能性ではなく、確率値も固定しない。'),
        ('fm', ['count', 'context'], 'この文脈で、経験回数がeinigemahlの少数回という基準を満たす。具体的な上限値を語義へ固定しない。非空性はr4が別に要求する。'),
        ('fu', [], '危険がそれほど大きくないという部分解釈の談話箇所。'),
        ('fv', [], '経験による能力取得の見込みを、その理由として示す談話箇所。')):
        declaration = declarations[name]
        basis['primitives'].append({'symbol': name, 'parameters': declaration['parameters'], 'result': declaration['result'],
            'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'fg': '同じ人による自立的な理解力の使用bbの試みで、生じた結果が非空、かつその全てでbbが成立しない。試みの不在、結果未記録、別人の不達成とは区別する。',
        'fo': '本人が人であり、能力評価対象の選択が実行可能な全方法で整合している。未評価の方法を不能とみなさない。',
        'fp': '同じ人・同じ過程について、少数回の不成功経験が時間順にあり、それらの寄与によって、整合した評価で自立的な活動の能力がない状態からある状態へ移る。',
        'fq': '指定した本人と回数基準の文脈に対し、fpを満たす過程が終わる状況の内容。取得過程は候補ごと・人ごとに異なってよい。',
        'fr': '非空の将来の見込み候補の全てでfqが成立する。過程や失敗が現実に生じたとは断定せず、回数基準は元の文脈に固定する。',
        'fs': '現在の対象範囲djが非空で、その同じ人々の全員についてfrを見込む内容。将来状況で対象範囲を選び直さない。',
        'ft': '著者によるe4とfsの主張の帰属を、fsを根拠側、e4を結論側とする談話関係と本文順へ結ぶ。両内容の真理や論証の十分性は評価しない。本文へ無条件に実行する主張とは別の、明示した解釈候補。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        'Fallenとgehen lernenを、自立した理解力の使用における不成功経験と能力取得へ対応させる対象側の部分解釈である。文字通りの転倒・歩行の身体的描写、比喩の両側の対応はまだ完成していない。',
        '能力の不在から取得への変化を読む。熟達度の連続的改善、経験による機構の一般説明、würden・wohlの語用論的効果は未完。',
        'dennの理由付けはftで保持するが、学習できるという見込みだけから危険が小さいという論理的含意を追加しない。譲歩・焦点、後続の萎縮・断念、原刊照合と全文の意味確認は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/experience-acquisition-basis-v1.json'),
                              (source_composed, 'data/kant-experience-acquisition-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored experience acquisition differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Experience, assessed acquisition and prospective explanation composed')


if __name__ == '__main__':
    main()
