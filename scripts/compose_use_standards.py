"""Compose use assessments from explicit standards and signed evidence."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-reformulations.noema'
BASE_PARAMS = ('standard a person a resource a act a context d adopted h[a d] c '
    'member h[a a d] c applicable h[a a a a d] c use h[a a a d] c')
BASE_ARGS = 'v standard v person v resource v act v context v adopted v member v applicable v use'
PARAMS = BASE_PARAMS + ' evidence h[a a a a c d] c'
ARGS = BASE_ARGS + ' v evidence'
ACTIVE = 'w[c[v member][v standard v criterion v context]][c[v applicable][v criterion v person v resource v act v context]]'
YES = 'c[v evidence][v criterion v person v resource v act e[v act][v act] v context]'
NO = 'c[v evidence][v criterion v person v resource v act u[e[v act][v act]] v context]'
TARGETS = {'rbi': 'hp2', 'rbj': 'hq2', 'rbk': 'hr2', 'rbl': 'hs2', 'rbm': 'ht2'}


def definitions():
    both = f'w[{YES}][{NO}]'
    neither = f'u[x[{YES}][{NO}]]'
    return f'''
d rbh[{BASE_PARAMS}] c[w[c[v adopted][v standard v context]][w[
 c[v use][v person v resource v act v context]
][g criterion a[{ACTIVE}]]]].
d rbi[{PARAMS}] c[w[k rbh[{BASE_ARGS}]][f criterion a[y[{ACTIVE}][u[z[{YES}][{NO}]]]]]].
d rbj[{PARAMS}] c[w[k rbi[{ARGS}]][f criterion a[y[{ACTIVE}][{YES}]]]].
d rbl[{PARAMS}] c[w[k rbh[{BASE_ARGS}]][g criterion a[w[{ACTIVE}][{both}]]]].
d rbk[{PARAMS}] c[w[k rbh[{BASE_ARGS}]][w[u[k rbl[{ARGS}]]][g criterion a[w[{ACTIVE}][{NO}]]]]].
d rbm[{PARAMS}] c[w[k rbh[{BASE_ARGS}]][w[u[k rbl[{ARGS}]]][g criterion a[w[{ACTIVE}][{neither}]]]]].
d rbn[person a resource a act a goal i[h[a] e] context d use h[a a a d] c purpose h[a a a i[h[a] e] d] c produces h[a a i[h[a] e] d] c] c[
 w[c[v use][v person v resource v act v context]][w[
  c[v purpose][v person v resource v act v goal v context]
 ][w[c[v produces][v act v person v goal v context]][t[c[s[v goal]][v person]][v context]]]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'use-standards-basis-v1', 'document': 'examples/v014/use-standards.noema',
        'primitives': [], 'definitions': {
            'rbh': '同じ文脈で採用された評価基準に属する適用項目が少なくとも一つあり、同じ人・資源・行為の使用が実際にある。空の基準や適用項目の不在を評価の成功としない。',
            'rbi': 'rbhが成立し、全適用項目について、充足を支持する証拠と違反を支持する証拠のちょうど一方がある。評価資料の充足性であり、証拠の信頼性の証明ではない。',
            'rbj': 'rbiの全適用項目で充足を支持する証拠がある。採用した基準に照らした適合であり、絶対的な合理性や道徳的正当性ではない。',
            'rbl': 'rbhが成立し、少なくとも一つの適用項目で充足と違反の証拠が共存する。異なる項目の肯定と否定だけでは衝突としない。',
            'rbk': 'rbhが成立し、全適用項目に証拠の衝突がなく、少なくとも一つで違反の証拠がある。他項目が未確認でも違反の根拠を表せる。',
            'rbm': 'rbhが成立し、全適用項目に証拠の衝突がなく、少なくとも一つは充足・違反の証拠がどちらもない。他項目の違反と両立する。',
            'rbn': '同じ人・資源・行為の使用があり、その使用に記述された本人についての目的が結び付き、同じ行為が同じ人にその結果を生じさせ、結果も成立する。目的の達成を使用の適切さと同一視しない。'},
        'unresolved': [
            '採用、基準への所属、適用条件、実際の使用、符号付きの証拠は型付き関係を引数として与える。基準の正当性や証拠の信頼性・収集方法までこの構造からは導かない。',
            'memberは採用した基準の全項目の範囲を表す。既知の好都合な項目だけを切り出して網羅したとすることはできず、範囲の完全さは呼出側の意味規約である。',
            '証拠関係の真偽は証拠の存在を表す。否定の証拠がないことを項目の充足とせず、肯定の証拠がないことを違反としない。衝突時には適合と違反の確定を保留する。',
            '目的への帰属、結果を生じさせる関係は別の引数である。単なる共存から因果関係を推測せず、効率・反復可能性・手段の合理性・責任も補わない。',
            'rbnは目的記述を評価するため現行の引用制限を受ける。rbhからrbmは評価する引用を含まない。有限の検査を全ての基準や現実の証拠の妥当性の証明とはしない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    params = PARAMS.replace(' use h[a a a d] c', '')
    args = ARGS.replace('v use', 'p hi2')
    extra = ''.join(f'd {target}[{params}] c[k {source}[{args}]].' for source, target in TARGETS.items())
    # This is an explicit bridge condition, not an assertion that Kant adopted
    # a particular standard or that standards alone exhaust rationality.
    bridge_args = args.replace(' p hi2', '')
    extra += f'''d hu2[{params}] c[w[
 z[k hj2[v act e[v act][v act] v context]][k hq2[{bridge_args}]]
][z[k hj2[v act u[e[v act][v act]] v context]][k hr2[{bridge_args}]]]].
d hv2[person a resource a act a goal i[h[a] e] context d purpose h[a a a i[h[a] e] d] c] c[
 k rbn[v person v resource v act v goal v context p hi2 v purpose p g3]
].'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-reformulations-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-use-standards-basis-v1', document='examples/v014/kant-use-standards.noema')
    generic = generic_composed()[1]
    basis['definitions'].update(generic['definitions'])
    for source, target in TARGETS.items():
        basis['definitions'][target] = f'{source}の使用関係を既存hi2へ固定し、同じ本人・能力・使用行為について評価する。採用基準・項目・適用・証拠は明示的な引数として残す。'
    basis['definitions'].update({
        'hu2': 'この人物・能力・行為・文脈について既存hj2の肯定評価がhq2、誤用評価がhr2と一致するという橋渡し条件。これを主張せず、評価基準をカントへ補うこともしない。',
        'hv2': '既存hi2の同じ能力使用とg3の同じ結果生成を結び、記述された目的が同じ本人について成立する。使用評価hj2とは独立で、目的を達成したことだけでは適切な使用や合理性を断言しない。'})
    basis['unresolved'] += generic['unresolved'] + [
        '使用の評価根拠を合成するための候補であり、カント本文がこの基準・証拠制度を採ったという翻訳ではない。新しい原文範囲や本文の主張は追加しない。',
        'hj2を削除・再定義せず、hu2で明示した条件が成り立つ場合に限って候補と結ぶ。合理性・適切な用途・自然的資質の基礎説明と後続の道具・足枷の接続は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'use-standards'), (source_composed, 'kant-use-standards')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored use standards differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Use standards, evidence gaps, conflicts and purpose attainment composed')


if __name__ == '__main__':
    main()
