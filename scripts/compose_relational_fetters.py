"""Preserve participant positions across a relational figurative presentation."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-described-routines.noema'
DESCRIPTION = 'i[h[j[a]] e]'


def definitions():
    return f'''
r rbt[a a {DESCRIPTION} {DESCRIPTION} d] c.
d rbu[node a author a target {DESCRIPTION} depiction {DESCRIPTION} context d] c[
 w[u[e[v target][v depiction]]][k rbt[v node v author v target v depiction v context]]
].
d rbv[relation h[a a] e participants j[a]] e[b context[w[e[d[v participants]][n p c b]][
 g first a[g second a[w[a[v participants][n p a b][v first]][w[
  a[v participants][n p b b][v second]
 ][t[c[v relation][v first v second]][v context]]]]]
]]].
d rbx[object a person a context d fastens h[a a a d] c lower h[a a d] c possible h[a a d] c blocked h[a a a a d] c] c[
 g limb a[w[c[v lower][v limb v person v context]][w[c[v fastens][v object v limb v person v context]][
  g movement a[w[c[v possible][v person v movement v context]][c[v blocked][v object v limb v person v movement v context]]]
 ]]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    primitive = doc['declarations'][0]
    basis = {'version': 'relational-fetters-basis-v1', 'document': 'examples/v014/relational-fetters.noema',
        'primitives': [{'symbol': 'rbt', 'parameters': primitive['parameters'], 'result': primitive['result'],
            'arguments': ['node', 'author', 'target_description', 'depiction_description', 'context'],
            'meaning_ja': '著者がこの談話箇所・文脈で、対象側の関係記述を描写側の関係記述による非字義的な提示として採る。引数は個体の順序付き列で、対応する位置は両側で同じ対象を指す。現実の描写の成立や両内容の真偽の一致は要求しない。'}],
        'definitions': {
            'rbu': '異なる二つの列引数の関係記述について、位置対応を保持した非字義的な提示がある。参加者数と各位置の役割は各記述の定義で定める。',
            'rbv': '個体二つを取る内容を、長さが厳密に二つの個体列を取る内容へ変換する。0番目を第一、1番目を第二の役割へ渡す。余分な参加者や欠けた参加者は偽とし、同じ個体が両役割に入ることは型だけでは禁止しない。',
            'rbx': '同じ人の足または足首側の部位に同じ物体が固定され、その同じ部位への固定によって、制限がなければ可能な同じ人の身体運動の少なくとも一つが妨げられる。全ての移動不能や実際の移動の試みは要求しない。'},
        'unresolved': [
            'rbtは非字義的な提示の意味規約であり、比喩を自動的に発見・解釈する処理ではない。列の対応だけで比喩の評価や含意を尽くさない。',
            '列を受け取る記述は任意の有限個の個体の役割に使える。rbvは二項関係への接続例であり、異なる型の引数や全ての比喩を一つの固定の二項構造へ還元しない。',
            '固定、身体部位への帰属、制限なしの場合の運動可能性、固定による制限は明示した関係を引数で与える。比較時に他の背景を変えず、許可や恐怖による不実行と混同しない。',
            'rbxは足側に装着する身体拘束の部分的な構成であり、歴史的な足枷の全形態、材質や施錠、設計目的、身体運動の物理的な基礎を定義し終えたものではない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''
r h2d[] a.r h2e[a a a d] c.r h2f[a a d] c.r h2g[a a d] c.r h2h[a a a a d] c.
d h26[person a] e[b context[w[k ib[v person v context v context]][w[
 k tb[i[point d][k ia[v person v context v point]] i[point d][k ib[v person v context v point]] i[first d second d][k ic[v first v second v context]]]
][w[k tc[i[point d][k ib[v person v context v point]] k bf[v person]]][
 f point d[y[k ib[v person v context v point]][x[e[v point][v context]][k ic[v context v point v context]]]]
]]]]].
d h27[object a] e[b context[x[t[k hd2[v object]][v context]][t[k h22[v object]][v context]]]].
d h2i[object a person a] e[b context[w[t[k h27[v object]][v context]][
 k raa[i[agent a][e[v agent][v person]] v person k h26[v person] r[p h26] v context p dg
 i[agent a act a point d][k hx2[v agent v object v act v point]] p g3]
]]].
d h2j[object a person a] e[b context[k rbx[v object v person v context p h2e p h2f p h2g p h2h]]].
d h2a[participants j[a]] e[k rbv[p h2i v participants]].
d h2b[participants j[a]] e[k rbv[p h2j v participants]].
d h2c[] c[k rbu[k h2d[] k wa[] r[p h2a] r[p h2b] k wh[]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    # This asserts the attribution of a partial relational depiction, not
    # physical restraints or the actuality of either quoted relation.
    doc['statements'].append({'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'h2c', 'arguments': []}})
    basis = deepcopy(json.loads((ROOT / 'data/kant-described-routines-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-relational-fetters-basis-v1', document='examples/v014/kant-relational-fetters.noema')
    generic = generic_composed()[1]
    basis['primitives'] += generic['primitives']
    basis['definitions'].update(generic['definitions'])
    declarations = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('h2d', [], '第三段落で規定・定型表現を足枷として描く談話箇所。実際の物理的な足枷の個体とは別にする。'),
        ('h2e', ['object', 'limb', 'person', 'context'], '同じ人の同じ身体部位へ、その物体が留められている。単なる近接や、別の人の部位への装着とは区別する。'),
        ('h2f', ['limb', 'person', 'context'], 'その部位が、その同じ人の足または足首側の身体部位である。腕や首の拘束と区別するための帰属・部位条件で、解剖学の全体系は未定義。'),
        ('h2g', ['person', 'movement', 'context'], '同じ背景で対象の身体拘束がなければ、その人に可能な身体運動である。心理的な試みや規範的な許可とは区別する。'),
        ('h2h', ['object', 'limb', 'person', 'movement', 'context'], '同じ物体が同じ人の同じ部位へ固定されることにより、この身体運動が物理的に制限される。制限のない場合と他の背景を固定して比べる関係。')):
        declaration = declarations[name]
        basis['primitives'].append({'symbol': name, 'parameters': declaration['parameters'], 'result': declaration['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update({
        'h26': '本人について文脈で採る残る生涯の評価範囲が履歴内の非空の区間で、その範囲に基準時を含み、全点が基準時以降で、範囲全体で既存の未成熟bfが成立する。使用以前の状態までその使用の結果とせず、範囲外や無期限の持続も主張しない。',
        'h27': '規定hd2または固定した表現の型h22に該当するもの。双方への該当を許し、二種類の全体への分配や列挙の談話効果はまだ加えない。',
        'h2i': '同じ規定または定型表現を同じ本人が用いる生起する活動があり、その活動が同じ本人についてh26の持続する依存状態を生じさせ、その状態も成立するという対象側の部分的な関係。',
        'h2j': '同じ物体が同じ人の足側の部位へ留められ、その部位への固定で本人の身体運動を制限するという描写側の関係。',
        'h2a': '二つの位置を規定・定型表現、その利用者の順でh2iへ渡す。',
        'h2b': '同じ二つの位置を足側を拘束する物体、その被拘束者の順でh2jへ渡す。',
        'h2c': '著者がh2aの対象側の関係をh2bの身体的描写で提示するという部分的な比喩帰属。二つの位置の対象は保持し、引用内容は実行しない。'})
    basis['unresolved'] += generic['unresolved'] + [
        'h2iは道具の使用が依存状態の持続に関わるという明示した読みであり、単なる同時成立を因果に変えずg3を別条件にする。因果機構や原文の唯一の解釈を証明したものではない。',
        'immerwährendenの強さは未確定である。h26は指定範囲内の持続を与えるが、有限の観測区間から永久の持続を結論しない。この副詞相当の修飾部は今回の原文対応範囲へ含めない。',
        '規定と定型表現の全体への量化、これらという指示、身体拘束の文化的・評価的意味、後続の取り外しと跳躍の反事実的描写への接続は残る。',
        'h27を実行するには式記述への量化があり、有限評価器では評価できない。今回の本文主張は比喩の帰属であり、h2iやh2jの現実の成立を主張しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'relational-fetters'), (source_composed, 'kant-relational-fetters')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored relational fetters differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Relational metaphor keeps object and affected person positions')


if __name__ == '__main__':
    main()
