"""Compose acquired affective attachment from response disposition and history."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-current-deprivation.noema'
PARENT_BASIS = 'data/current-deprivation-basis-v1.json'
FULL = 'examples/v016/kant-acquired-affection.noema'
CORE = 'examples/v016/acquired-affection-core.noema'
BASIS = 'data/acquired-affection-basis-v1.json'
ANNOTATIONS = 'data/acquired-affection-identifiers-v1.json'
PRIMITIVES = {
    'hzyw': (['actor', 'target', 'description', 'scene'], '本人が、記述により捉えた対象のあり方へ向けて、親しみを伴う肯定的な感情を抱く。合理的な賛同、道徳的評価、利益、一時的な気分の快さだけとは分ける。対象とその記述の組が感情の向かう先であり、記述された性質の真実性や本人の信念をこの関係から推論しない。'),
    'hzyx': (['actor', 'target', 'description', 'anchor', 'candidate'], '基準での本人の心理的基盤を保ち、同じ対象を同じ記述のもとで意識する比較状況。応答する感情の有無を選別基準にせず、別の性向を訓練で獲得する状況も含めない。比較範囲と心理的基盤の適切さは解釈入力として残す。'),
    'hzyy': (['actor', 'target', 'description', 'anchor', 'preferred', 'other'], '同じ本人・対象・記述・基準の比較状況における、刺激の受容や妨害などの背景による通常性の厳密な優先関係。感情が成立したかを優先の根拠にしない。非反射性・推移性・極小状況への到達条件をrqt4で検査する。'),
}
MEANINGS = {
    'r2ci': '本人・対象・記述・基準を固定し、引数の比較範囲と通常性で選ぶ非空の極小候補すべてに、引数の対象指向的な応答を要求する。既存rqt4を合成した一般的な応答傾向。現在の応答、対象の記述の真実性、過去の獲得は別に評価する。',
    'r2cj': '同じ本人自身の未成熟bfを対象とする、親しみを伴う肯定的感情hzywの応答傾向。本人が自分のその状態を意識する比較状況hzyxと通常性hzyyをr2ciへ渡す。好ましい受容idや基準での瞬間的な感情を必須条件にしない。',
    'r2ck': '同じ本人の現在の未成熟bfに加え、同じ本人・履歴の実際の過程で愛着の傾向r2cjを獲得し、その後端から現在まで保つ。既存rafの性質をr2cjへ置き換え、前端の比較範囲と通常性の有効性も要求する。空や不正な比較を以前の性向不在の証拠にしない。過去全体で一度も愛着がなかったこと、未来の永続、能力不足への因果は追加しない。',
}
LIMITS = [
    '第三段落のlieb gewonnenを、対象へ向かう愛着の傾向を獲得し現在まで保つ読みとして組み立てる。Adelungの語義は獲得する愛情・傾きを支持するが、この反事実的な応答モデル自体を辞書が証明するわけではない。',
    '親しみを伴う肯定的感情は一般的な経験の基本入力として追加する。愛着という語全体を未解釈な判定器にはしないが、感情の生理機構や愛の全種類を還元し終えてはいない。',
    '比較状況と通常性は感情の結果から独立に与える。形式検査で循環的な優先は拒否できるが、入力者が好都合な状況だけ選んだことや心理的な妥当性を自動検出できるとはしない。',
    '同じ対象の同じ性質を指す記述は引用の構文で保持する。任意の同義記述の同一化、誤認された対象、恋愛・慈愛などの細分類はここで完成させない。',
    '既存のrafの結果状態の持続という読解を継承する。途中に傾向が失われた履歴は拒否するが、感情を常時経験することは要求しない。履歴外・未来への持続や取得過程内の連続性は追加しない。',
    'sogar、第一文との人称と量化の接続、著者への帰属は未確定。三定義は部分的な内容式であり、51本文文と十二単位の既存判断を保つ。意味確認済み分量を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    basic = '''
r hzyw[a a i[h[a] e] d] c.
r hzyx[a a i[h[a] e] d d] c.
r hzyy[a a i[h[a] e] d d d] c.
d r2ci[actor a target a description i[h[a] e] anchor d
 response h[a a i[h[a] e] d] c cases h[a a i[h[a] e] d d] c preferred h[a a i[h[a] e] d d d] c] c[
 k rqt4[i[scene d][c[v cases][v actor v target v description v anchor v scene]]
 i[first d last d][c[v preferred][v actor v target v description v anchor v first v last]]
 i[scene d][c[v response][v actor v target v description v scene]]]
].
d r2cj[person a] e[b anchor[k r2ci[v person v person r[p bf] v anchor p hzyw p hzyx p hzyy]]].
'''
    valid = '''k r2ci[v person v person r[p bf] v earlier
 i[actor a target a description i[h[a] e] scene d][e[v actor][v actor]] p hzyx p hzyy]'''
    acquisition = '''k raf[i[point d][k ia[v person v anchor v point]]
 i[first d second d][k ic[v first v second v anchor]]
 v person p r2cj v process v earlier v later v anchor p ag p la]'''
    expression = 'w[' + valid + '][' + acquisition + ']'
    for name, sort in (('later', 'd'), ('earlier', 'd'), ('process', 'a')):
        expression = 'g ' + name + ' ' + sort + '[' + expression + ']'
    return basic + 'd r2ck[person a] e[b anchor[w[t[k bf[v person]][v anchor]][' + expression + ']]].'


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=[])
    added = doc['declarations'][size:]; by_name = {d['name']: d for d in added}
    assert len(added) == 6
    basis = dict(status='acquired_affective_disposition_composed', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
        primitives={n: dict(parameters=by_name[n]['parameters'], result=by_name[n]['result'], arguments=args, meaning_ja=meaning)
                    for n, (args, meaning) in PRIMITIVES.items()}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/current-deprivation-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print('Three composed definitions and three general inputs; 51 authored assertions preserved', flush=True)
