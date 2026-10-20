"""Compose agentive cessation of unexamined-use dispositions, not skill acquisition."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_specialization import specialize_definition
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-depicted-referents.noema'
PARENT_BASIS = 'data/depicted-referents-basis-v1.json'
FULL = 'examples/v016/kant-abandoned-reliance.noema'
CORE = 'examples/v016/abandoned-reliance-core.noema'
LIBRARY = 'examples/v016/agentive-profile-change.noema'
BASIS = 'data/abandoned-reliance-basis-v1.json'
ANNOTATIONS = 'data/abandoned-reliance-identifiers-v1.json'
MEANINGS = {
    'r2gl': '指定した全比較場面が保持条件と外的機会を満たし、非空で有効な通常場面の全てで応答の真偽が指定極性と一致する。現在の実行は要求しない。負極性は肯定傾向の単なる否定ではなく、同じ有効な比較で応答がない傾向を積極的に要求する。',
    'r2gm': '同じ順序付き履歴の同じ過程について、対象への作用、本人の行為主体性、生起、同じ前後の性質を変える構成内容、同じ後性質への結果生成を結ぶ。前では前性質だけ、後では後性質だけが成立する。状態評価と変化・因果には同じ閉じた記述を渡す一般形。',
    'r2gn': '同じ対象を同じ本人が同じ活動で吟味せず使うr2epと、その活動の生起がある。誤用という評価、能力不足、未成熟、反復歴や成功はこの応答の成立条件に追加しない。',
    'r2go': '同じ提示文脈・対象・本人・基準について、保持条件と外的機会を全比較場面で確認し、その通常場面でr2gnの応答が指定極性となる傾向。現在使っていないだけでは負極性を満たさず、吟味して使う行為は吟味のない応答に数えない。',
    'r2gp': '提示文脈whと先行する種類r2fhを受けて選ぶ対象が非空で、その全てについて同じ本人に肯定のr2goがある。対象範囲を評価時点ごとに選び直さない。',
    'r2gq': 'r2gpと同じ固定された非空の指示対象範囲の全てについて、同じ本人に負極性のr2goがある。吟味した上での利用、自力で判断する能力の不足、後日の再依存の可能性を排除しない。',
    'r2gr': '一般的な行為主体による性質交替r2gmの前後記述を、r2gpとr2gqへ静的に固定した形。脱引用を除き、内容として引用できる。意味の同値を任意に推測して別記述へ置き換える特殊化ではない。',
    'r2gs': '同じ本人・過程・前後を、知的活動側の同じ仮定履歴と順序に置き、r2grの傾向の交替へ結ぶ。変化内容hzidと結果生成g3にも同じ前後記述を渡し、単に傾向が変わっただけでは本人による離脱としない。',
    'r2gt': 'この仮定の終点に至る同じ本人の過程があり、同じ固定対象群への吟味のない使用傾向を、通常場面でその応答がない傾向へ自ら変えるという第四文の前件候補。実際の離脱や後件の能力・不慣れを本文の事実として断定するものではない。',
}
PRIMITIVES = {
    'hzzzo': ('d a a d d', ['scope', 'object', 'person', 'anchor', 'candidate'],
        '同じ提示文脈・対象・本人・基準で、その対象を手段として用いるかが問題になる比較場面。応答の成否から場面を選ばない。本人側の基盤の保持と外的機会は別の入力で全候補について検査する。'),
    'hzzzp': ('d a a d d', ['scope', 'object', 'person', 'anchor', 'candidate'],
        'この対象への応答の比較で、基準の本人の関連する構成・理解・習慣・方針などの基盤を保つ。応答の真偽そのものや能力の同一性を保存条件にせず、新たな訓練で別の基盤へ交換しない。前後の基準をまたいで基盤が同一であるという意味ではない。'),
    'hzzzq': ('a a d', ['object', 'person', 'candidate'],
        'この対象を手段として扱う活動を本人が行える外的な局面がある。吟味の能力、実際の使用、適切さ、成功は要求しない。使用しなかった反例を機会がないことにして除かない。'),
    'hzzzr': ('d a a d d d', ['scope', 'object', 'person', 'anchor', 'preferred', 'other'],
        '同じ対象・本人・基準の比較場面について、妨害や背景条件から先の場面を通常とする厳密な優先関係。吟味のない使用をしたかどうかを優先根拠にしない。非反射性・推移性・極小候補への到達はrqt4で検査する。'),
    'hzzzs': ('a d d', ['person', 'case', 'point'],
        'この本人について、知的活動側の仮定の終点へ至る同じ履歴に属する状況。身体的な足枷の描写履歴h2rや、別の仮定の履歴を混ぜない。前後の履歴への所属と順序は別に検査する。'),
}
LIMITS = [
    '第四文のabwürfeの対象側を、規定・定型表現への吟味のない使用傾向を自らやめるという候補として構成する。自然言語の唯一の語義や、依存一般の必要十分条件を確定したものではない。',
    '肯定傾向も負極性の傾向も、有効な通常機会の全てで応答を検査する。混合した通常応答を、どちらかの確定した傾向へ丸めない。現実の一時点の不使用、空の比較、保持条件や機会の欠落は負極性の傾向ではない。',
    '使用を吟味しないことと、不適切な使用・経験による習慣形成・本人の過去の方針宣言は区別する。元から意識的に依存を選んだという歴史を補わない。',
    '選択した対象群を一つの過程の前後で扱う。複合過程の内部の各対象への離脱時点、部分的な離脱、離脱後の永久の保持はこの前件に含めない。前後の実際の応答の生起も要求しない。',
    '変化の構成内容・本人の行為主体性・結果生成は別々に要求する。過程と因果関係の認定は解釈入力であり、単なる前後の真偽差だけで本人の作用を認定しない。',
    '指示対象は同じ提示文脈で固定する。本文の第四文の二帰属や比喩はまだこの前件へ置き換えない。知的な課題の不確かな遂行、不慣れ、譲歩と限定を持つ後件との接続が必要である。',
    '前件が成立しても、自分の理解力を使う能力の獲得や未成熟の消滅を導かない。吟味して規定を使うことや、後に依存が戻る可能性も禁止しない。原文対応範囲・意味確認済み分量は増やさない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2gl[cases h[d] c preserved h[d] c opportunity h[d] c preferred h[d d] c response h[d] c positive c] c[
 w[f scene d[y[c[v cases][v scene]][w[c[v preserved][v scene]][c[v opportunity][v scene]]]]][
 k rqt4[v cases v preferred i[scene d][z[c[v response][v scene]][v positive]]]]
].
d r2gm[history h[d] c before h[d d] c person a process a start d end d
 old i[h[a] e] new i[h[a] e] changes h[a d d] c affected h[a a d d] c
 agent h[a a d] c occurs h[a d] c transition h[a a i[h[a] e] i[h[a] e] d d] c produces h[a a i[h[a] e] d] c] c[
 w[k tg[v history v before v process v start v end v changes]][
 w[c[v affected][v person v process v start v end]][w[c[v agent][v person v process v end]][
 w[c[v occurs][v process v end]][w[c[v transition][v person v process v old v new v start v end]][
 w[c[v produces][v process v person v new v end]][
 w[t[c[s[v old]][v person]][v start]][w[u[t[c[s[v new]][v person]][v start]]][
 w[u[t[c[s[v old]][v person]][v end]]][t[c[s[v new]][v person]][v end]]]]]]]]]]
].
d r2gn[object a person a point d] c[g act a[w[k r2ep[v person v object v act v point p hx2 p fa p fb p hz2]][k dg[v act v point]]]].
d r2go[object a person a anchor d positive c] c[k r2gl[
 i[scene d][k hzzzo[k wh[] v object v person v anchor v scene]]
 i[scene d][k hzzzp[k wh[] v object v person v anchor v scene]]
 i[scene d][k hzzzq[v object v person v scene]]
 i[first d last d][k hzzzr[k wh[] v object v person v anchor v first v last]]
 i[scene d][k r2gn[v object v person v scene]] v positive
]].
d r2gp[person a] e[b anchor[w[g object a[k hzzzm[k h2d[] k wa[] r b[p r2fh] v person v object k wh[]]]][
 f object a[y[k hzzzm[k h2d[] k wa[] r b[p r2fh] v person v object k wh[]]][k r2go[v object v person v anchor e[k wh[]][k wh[]]]]]
]]].
d r2gq[person a] e[b anchor[w[g object a[k hzzzm[k h2d[] k wa[] r b[p r2fh] v person v object k wh[]]]][
 f object a[y[k hzzzm[k h2d[] k wa[] r b[p r2fh] v person v object k wh[]]][k r2go[v object v person v anchor u[e[k wh[]][k wh[]]]]]]
]]].
'''


def extend(old):
    doc = deepcopy(old); statements = doc['statements']; doc['statements'] = []
    assert not (set(MEANINGS) | set(PRIMITIVES)) & {d['name'] for d in doc['declarations']}
    extra = ''.join('r ' + n + '[' + p + '] c.' for n, (p, _, _) in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + extra + definitions())
    quote = lambda n: dict(kind='quote', body=dict(kind='function_ref', symbol=n))
    trace = specialize_definition(doc, 'r2gm', 'r2gr', {6: quote('r2gp'), 7: quote('r2gq')})
    assert trace.disquotations_removed == 4
    doc = parse(format_graph(trace.document, 'compact') + '''
d r2gs[person a process a start d end d] c[k r2gr[
 i[point d][k hzzzs[v person v end v point]] i[first d last d][k ic[v first v last v end]]
 v person v process v start v end p ag p la p df p dg p hzid p g3
]].
d r2gt[person a] e[b end[g process a[g start d[k r2gs[v person v process v start v end]]]]].
''')
    doc['statements'] = statements
    return parse(format_graph(doc, 'compact')), trace


def build():
    old = parent(); doc, trace = extend(old.document)
    added = doc['declarations'][len(old.document['declarations']):]; assert len(added) == 14
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2gt']), statements=[])
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['r2gl', 'r2gm']), statements=[])
    decls = {d['name']: d for d in added}
    basis = dict(status='agentive_abandonment_antecedent_candidate', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
        primitives={n: dict(parameters=decls[n]['parameters'], result='truth', arguments=args, meaning_ja=meaning)
                    for n, (_, args, meaning) in PRIMITIVES.items()},
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS,
        specialization=dict(source='r2gm', target='r2gr', bound_positions=[6, 7], removed_disquotations=trace.disquotations_removed))
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/depicted-referents-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Abandonment antecedent composed; all 54 authored statements preserved', flush=True)
