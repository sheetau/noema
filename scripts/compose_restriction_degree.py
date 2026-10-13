"""Compose explicit normative classification and a finite restriction measure."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, call, definition
from scripts.compose_described_norms import PARAMS, TRUE, definitions as norms, MEANINGS as NORM_MEANINGS, LIMITS
from scripts.compose_scoped_counts import generic_composed as counts

PARENT = 'examples/v014/kant-temporal-norms.noema'


def definitions():
    fields = [v(n) for n in ('source', 'person', 'role', 'activity', 'description')]
    rule = lambda name, sign: app(v(name), *fields, sign, v('context'))
    sign = v('polarity')
    positive, opposed = rule('required', sign), rule('required', op('u', sign))
    permitted, other_allowed = rule('allowed', sign), rule('allowed', op('u', sign))
    args = [v(n) for n in ('source', 'person', 'role', 'activity', 'description', 'polarity', 'context', 'required', 'allowed')]
    return ''.join(definition(name, PARAMS, body) for name, body in (
        ('rdx', op('x', both(positive, opposed), op('x', both(permitted, opposed), both(other_allowed, positive)))),
        ('rdy', both(opposed, op('u', positive), op('u', permitted))),
        ('rdz', both(op('u', call('rdx', *args)), op('x', call('rdm', *args), call('rdy', *args)))))) + '''
d rd2[population j[a] scope h[a] c classified h[a] c restricted h[a] c ratio b criterion h[b] c] c[
 w[k rcm[v population v scope]][w[f item a[y[c[v scope][v item]][c[v classified][v item]]]][
  w[k hj[v population v restricted v ratio]][c[v criterion][v ratio]]
 ]]
].
'''


MEANINGS = {
    'rdx': '同じ出所・人・立場・行為・記述・文脈について、両極性の要求、またはいずれかの許可と反対極性の要求が併存する。両極性の許可だけは衝突としない。',
    'rdy': '指定極性の反対が明示的に要求され、指定極性への要求も許可もない。その極性の実行に対する、衝突のない禁止。許可の不在だけでは成立しない。',
    'rdz': 'rdxの衝突がなく、指定極性が積極的に許可されるかrdyで禁止される。全規範が評価できても、この二分類のどちらにも決まらない場合がある。',
    'rd2': '非空の対象範囲を重複なく全列挙し、全対象が指定の分類済み条件を満たし、制限対象の正確な比率が指定の評価基準を満たす。分類済み条件の内容は引数で与える。',
}
EXTRA_LIMITS = [
    '規範の有無を評価できない場合と、規範を全て調べた上で許可にも禁止にも分類できない場合を分ける。前者を偽として補わない。衝突の解決や要求から許可を導く規則は追加しない。',
    '有限個の活動を等しく数える操作的な尺度である。活動の分割や統合に対して不変ではなく、数え方・独立した対象範囲・評価基準を固定しない比較は認めない。時間の頻度、行為の重要性や強度、連続的な選択範囲の測度は表さない。',
    '対象列が範囲を全列挙することと、その範囲が原文の全活動を正しく表すことは別である。有限検査は現実の無限の選択肢の網羅を証明しない。',
    '非常に狭く制限することの候補尺度であり、禁止割合に普遍的な数値閾値を与えない。原文の程度の全意味との一致は未確定である。',
]


def generic_composed():
    text, basis = counts()
    doc = parse(text + norms() + definitions())
    basis = deepcopy(basis)
    basis.update(version='restriction-degree-basis-v1', document='examples/v014/restriction-degree.noema')
    basis['definitions'].update(NORM_MEANINGS)
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += LIMITS + EXTRA_LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    basis = deepcopy(json.loads((ROOT / 'data/kant-temporal-norms-basis-v1.json').read_text(encoding='utf-8')))
    mapping = basis['role_linkage']['symbols']['roles']
    args = [v(n) for n in ('source', 'person', 'role', 'activity')] + ['r[p ' + mapping['dc'] + ']', TRUE, v('context'), 'p h7a', 'p h7b']
    params = 'source a person a role a activity a context d'
    extra = definitions()
    extra += definition('h7y', params, both(call('rdm', *args), op('u', call('rdx', *args))))
    for name, target in (('h7z', 'rdy'), ('h72', 'rdx'), ('h73', 'rdz')):
        extra += definition(name, params, call(target, *args))
    extra += '''d h74[source a person a role a population j[a] ratio b criterion h[b] c context d] c[
 k rd2[v population i[activity a][k ''' + mapping['db'] + '''[v person v activity v role v context]]
  i[activity a][k h73[v source v person v role v activity v context]]
  i[activity a][k h7z[v source v person v role v activity v context]] v ratio v criterion]
].
'''
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis.update(version='kant-restriction-degree-basis-v1', document='examples/v014/kant-restriction-degree.noema')
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h7y': '同じ活動・実行記述に積極的な実行許可があり、両極性の要求・許可のいずれの衝突もない。',
        'h7z': '同じ活動・実行記述に、不実行の要求があり、実行要求も実行許可もない。衝突のない明示的な禁止。',
        'h72': '同じ活動・実行記述についてrdxの規範上の衝突がある。',
        'h73': '同じ活動・実行記述が、衝突なく明示的に許可または禁止される。',
        'h74': '指定した人・職務・文脈の私的活動を過不足なく全列挙し、全活動がh73で分類済みで、そのうちh7zの明示的な禁止割合が、指定した値と基準を満たす。時間の頻度や、制限することへの著者側の許可とは別の条件。',
    })
    basis['unresolved'] += EXTRA_LIMITS + [
        '既存の公的／私的使用の分類を再利用する。有限の活動種類の全列挙という読みの適切さは未確定であり、実際の出来事だけを数えて選択の自由を測ったとはしない。',
        'h74は規範内容の実際の評価であり、著者が制限を許すこと、しばしば、啓蒙の進歩を特に妨げないという留保への接続は残る。本文の新たな主張を追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'restriction-degree'), (source_composed, 'kant-restriction-degree')):
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored restriction degree differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Explicit permissions, prohibitions and conflicts composed with a finite scoped degree')


if __name__ == '__main__':
    main()
