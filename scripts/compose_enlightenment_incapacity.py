"""Distinguish inability to attain independence from inability to exercise it."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_public_reversal import FIELDS as PRIOR_FIELDS

PARENT = 'examples/v016/kant-public-reversal.noema'
PARENT_BASIS = 'data/public-reversal-basis-v1.json'
FULL = 'examples/v016/kant-enlightenment-incapacity.noema'
CORE = 'examples/v016/enlightenment-incapacity-core.noema'
BASIS = 'data/enlightenment-incapacity-basis-v1.json'
ANNOTATIONS = 'data/enlightenment-incapacity-identifiers-v1.json'
FIELDS = [(n, t) for n, t in PRIOR_FIELDS if n not in ('guardianrole', 'incapable')]
PRIMITIVES = {
    'h223p': ('[a i[h[a] e] d d] c', ['person', 'goal', 'reference', 'start'],
              '同じ本人が記述された状態を取得する能力を、基準時点から評価するための開始機会の範囲。実際の履歴だけに限定せず、状態を得られる結果から逆算して機会を選ばない。行使活動の成功だけでなく、学習や援助を含む取得方法を評価する文脈を指定する。候補自体の非空性・基準保持・外的条件は別に検査する。'),
    'h223q': ('[a i[h[a] e] d d] c', ['person', 'goal', 'reference', 'start'],
              '指定状態の取得を評価するために採る本人側の理解・習慣・身体・方針などの基盤が、同じ基準から候補の開始点へ保たれる。取得可能性の結論そのものを保持条件にせず、既に訓練した別の本人側状態で開始しない。開始後の方法に含まれる学習・変化を禁止する関係ではない。'),
    'h223r': ('[a i[h[a] e] d] c', ['person', 'goal', 'start'],
              '同じ本人が、指定状態の取得へ向かう方法を試せる外的な機会を、この開始点が備える。学習・助言などの利用機会を含み得るが、本人の取得能力、方法の実行、成功、社会的な許可を含意しない。指定状態が既に成立することとも区別する。'),
}
MEANINGS = {
    'r2ms': '同じ本人・目標・基準に対する非空の機会候補の全てで、基準からの本人側の状態保持と外的機会を要求し、利用可能な全方法の評価範囲が整合し、目標を達成する方法xdがないことを要求する。通常機会の一部で失敗するだけでは足りない。方法分類による除外は行わず、学習や他者の援助を伴う方法も利用可能なら評価する。候補の網羅性と結果評価基準は解釈入力の責任として残る。',
    'r2mt': '同じ本人が自立的な理解力使用の能力upに至ることを目標として、r2msの全候補での不能を評価する。取得の機会候補・基準保持・外的機会は、同じ閉じた目標記述r[p up]へ結び付けたh223p/h223q/h223rを使う。現在の未成熟bfやbbの行使不能だけから取得不能とはしない。本人側の基盤を保つのは各候補の開始時点であり、方法の途中の学習を禁止しない。',
    'r2mu': '本人が人であり、重複のない人の完全な構成員列を持つ同じ公衆の、少なくとも一人の他の構成員に対して総括的な指導・監督の立場dcを持つ。既存r2m5を実際の役割関係として評価する。制度的な任命履歴、合法性、指導の成功、本人の啓蒙能力は追加しない。',
    'r2mv': '公衆と先行後見人・扇動者を結ぶr2mrの後見役をr2mu、啓蒙不能をr2mtへ充足する。先行の後見人の役割と、扇動条件内の各扇動者の役割・不能を同じ人と各時点で評価する。扇動関係だけは引数に残り、ここでは第三文全体や閉じた著者帰属を完成させない。',
}
LIMITS = [
    'aller Aufklärung unfähigを、指定した取得機会のどこにも自立的な理解力使用の能力へ至る達成方法がないという強い読みで構成する。単に一つの普通の場面で行使できないこととは区別する。無限の将来や全ての物理的可能世界の不可能性、部分的な知識が一切増えないことまでは主張しない。',
    '自己思考の能力upを取得目標に採る。現在のupの不成立や未成熟bfから、将来の取得不能を推論しない。利用可能な学習・援助の方法を分類で除かず、基準の本人側状態は各候補の開始にのみ保持する。',
    'h223pの機会範囲とae/af/apの方法・結果は文脈入力である。機会範囲が空、基準保持や外的条件に違反、ある方法の結果が空・不整合であれば不能の肯定に使えない。未知の入力を偽として穴埋めしない。解釈範囲そのものの網羅性は有限モデルの通過だけでは証明できない。取得の三つの基本関係は任意の状態記述を取り、啓蒙不能を一語で代用するものではない。',
    '後見役を公衆の構成員への実際の監督的な立場として読む。第二文のeingesetztに対応する制度的任命を、第三文のseiner Vormünderへ無条件に追加しない。集団への述定として指示範囲が十分かの確認は、閉じた参照供給とともに残る。',
    '扇動の意味構成、被作用者の範囲、閉じた参照、頚木の照応、Besonders/selbst、偏見の害と報復、第三文全体の著者帰属・通読は未完。既存59文、十三の全単位判断、先頭二文382非空白文字を保持し、今回確認済み文字数は増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    fields = ' '.join(n + ' ' + t for n, t in FIELDS)
    args = ' '.join('p r2mu' if n == 'guardianrole' else 'p r2mt' if n == 'incapable'
                    else 'v ' + n for n, _ in PRIOR_FIELDS)
    return '''
d r2ms[person a goal e reference d candidate h[a d d] c
 stable h[a d d] c opportunity h[a d] c available h[a a d] c
 possible h[a a d d] c selected h[a a d d] c] c[
 w[k aa[v person]][w[g scene d[c[v candidate][v person v reference v scene]]][
 w[k rqu7[v person v reference v candidate v stable v opportunity]][
 f scene d[y[c[v candidate][v person v reference v scene]][
 w[k xe[v person v scene v available v possible v selected]][
 u[k xd[v person v goal v scene v available v possible v selected]]]
 ]]
 ]]]
].
d r2mt[person a reference d] c[
 k r2ms[v person k up[v person] v reference
 i[who a base d scene d][k h223p[v who r[p up] v base v scene]]
 i[who a base d scene d][k h223q[v who r[p up] v base v scene]]
 i[who a scene d][k h223r[v who r[p up] v scene]]
 p ae p af p ap]
].
d r2mu[person a public a point d] c[
 w[k aa[v person]][w[k hi[k mp[v public] p aa]][t[k r2m5[v person v public]][v point]]]
].
d r2mv[''' + fields + '''] c[k r2mr[''' + args + ''']].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    text = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + text + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2mv']), statements=[])
    basis = dict(status='attainment_incapacity_and_guardian_role_composed_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives={
                     n: dict(parameters=next(d for d in added if d['name'] == n)['parameters'],
                             result='truth', arguments=spec[1], meaning_ja=spec[2])
                     for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-reversal-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
