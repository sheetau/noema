"""Conjoin kind-level generalizations without pooling away either kind."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

SOURCE = 'examples/v016/kant-conditioned-persistence.noema'
SOURCE_BASIS = 'data/conditioned-persistence-basis-v1.json'
LIBRARY = 'examples/v016/conjoined-kinds.noema'
BASIS = 'data/conjoined-kinds-basis-v1.json'
MEANINGS = {
    'r2fa': '二つの種類の事例範囲について、同じ通常性関係を各範囲の内部へ制限して既存r2bgを別々に適用し、両方の一般化が成立することを要求する。一方の種類の事例が他方の全事例を劣後させても、後者を無視しない。範囲の重なりを許し、割合や現在の実例数へ換算しない。',
    'r2fb': '同じ事例から取り出した対象・本人・基準について、候補選択と継続点の選択にもその三者を固定して既存r2eyの条件付き作用を評価する。別事例の対象・本人・基準から候補や結果を借りない。',
    'r2fc': '指定した事例から、同じ事例の対象と基準について規定hd2に属するもの、定型表現h22に属するものを別々に取り出す。各種類の通常事例で同じr2fbの作用を要求する。第三文の二種類を分配的に読む場合の比較構成であり、著者の主張にはまだ採用しない。',
}
LIMITS = [
    '二つの種類について別々に同じ性質を一般化する読みを扱う。二種類の共同作用や全用例での成立、裸の複数名詞の全用法を定義したものではない。',
    '各種類に通常事例が少なくとも一つ必要だが、事例は仮定の場合でもよく、現在の実例の存在を要求する意味ではない。どの仮定を認めるかは解釈入力である。',
    '通常性は各種類の内部で評価する。種類をまたぐ優先辺は両方の範囲に属する端点を持たない限り使わず、種類間の順位の理論は作らない。範囲内の循環や比較不能な通常反例を無視しない。',
    '候補・分類・通常性を結論に合わせて選定することは正当化しない。未登録の分類や原因は偽で埋めない。個別の状況が通常であると別に分からなければ、一般化からその状況の結果を確定できない。',
    '原文側は既存hd2とh22の部分分類、r2eyの条件付き作用をそのまま使う。規定の拘束性、任意の型の定型表現、持続の強さ、通常性の根拠、theseに相当する指示と比喩の全体接続は未完。',
    '二種類をまとめた一回の通常性評価では一方の種類が消える反例を示す。だからといってこの方式を第三文の唯一の読みとはせず、現行54文・登録簿・既存判断・原文対応範囲は変更しない。',
]


@lru_cache(None)
def catalog(): return load_catalog(ROOT, SOURCE_BASIS)


def definitions():
    return '''
d r2fa[first h[a] c second h[a] c preferred h[a a] c response h[a] c] c[
 w[k r2bg[v first v preferred v response]][k r2bg[v second v preferred v response]]
].
d r2fb[item a objects h[a] a persons h[a] a anchors h[a] d branches h[a a d d] c futures h[a a d d d] c] c[
 k r2ey[c[v objects][v item] c[v persons][v item] c[v anchors][v item]
 i[anchor d branch d][c[v branches][c[v objects][v item] c[v persons][v item] v anchor v branch]]
 i[anchor d branch d point d][c[v futures][c[v objects][v item] c[v persons][v item] v anchor v branch v point]]]
].
d r2fc[items h[a] c objects h[a] a persons h[a] a anchors h[a] d preferred h[a a] c branches h[a a d d] c futures h[a a d d d] c] c[
 k r2fa[i[item a][w[c[v items][v item]][t[k hd2[c[v objects][v item]]][c[v anchors][v item]]]]
 i[item a][w[c[v items][v item]][t[k h22[c[v objects][v item]]][c[v anchors][v item]]]]
 v preferred i[item a][k r2fb[v item v objects v persons v anchors v branches v futures]]]
].
'''


def build():
    old = catalog(); assert not set(MEANINGS) & set(old.entries)
    doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['r2bg', 'r2ey', 'hd2', 'h22']), statements=[])
    doc = parse(format_graph(doc, 'compact') + definitions())
    primitives, meanings = [], {}
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'definition': meanings[n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
        else:
            e = old.entries[n]
            primitives.append(dict(symbol=n, parameters=d['parameters'], result=d['result'], arguments=e['arguments'], meaning_ja=e['meaning_ja']))
    basis = dict(status='conjoined_kind_generalizations_not_source_replacement', document=LIBRARY,
        primitives=primitives, definitions=meanings, limitations=LIMITS,
        origin_sha256={SOURCE: digest((ROOT / SOURCE).read_bytes()), SOURCE_BASIS: digest((ROOT / SOURCE_BASIS).read_bytes())})
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Three definitions; manuscript and review registry unchanged', flush=True)
