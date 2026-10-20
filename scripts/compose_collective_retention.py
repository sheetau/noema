"""Compose collective constraint, continuous retention and actual causal contribution."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-public-second-sentence.noema'
PARENT_BASIS = 'data/public-second-sentence-basis-v1.json'
FULL = 'examples/v016/kant-collective-retention.noema'
CORE = 'examples/v016/collective-retention-core.noema'
LIBRARY = 'examples/v016/collective-retention.noema'
BASIS = 'data/collective-retention-basis-v1.json'
ANNOTATIONS = 'data/collective-retention-identifiers-v1.json'
FIELDS = [('group', 'a'), ('act', 'a'), ('target', 'a'), ('actors', 'j[a]'),
          ('history', 'i[h[d] c]'), ('before', 'i[h[d d] c]'),
          ('first', 'i[d]'), ('last', 'i[d]'), ('state', 'i[h[a] e]'), ('anchor', 'd')]
PRIMITIVES = {
    'h223n': ('[a a i[h[a] e] d] c', ['act', 'target', 'state', 'point'],
              'この同じ行為は、この本人が記述された状態から離れる選択肢を、身体的な阻止または拒否に伴う不利益の威嚇などの圧力によって制約する。情報や理由を提示するだけの説得、助言、無関係な活動への制約とは区別する。制約の適用を表す関係であり、実際の状態保持・成功・因果的寄与・当人の抵抗の実行は別条件。法的な命令や身体暴力に限定しない。'),
    'h223o': ('[a a j[a] d] c', ['group', 'act', 'actors', 'point'],
              'この状況の同じ参加者群が担う同じ行為を、指定集団の共同的な働きとして帰属できる。構成員が偶然別々に行ったことや、集団に反して行う私的行為だけでは満たさない。制度的な代表権、全員一致、全構成員の参加は要求しない。参加者の集団所属・行為参加・生起は合成定義で別に検査する。共同作用への帰属の基本関係であり、国家や公衆に限定しない。'),
}
MEANINGS = {
    'r2mj': '指定した先行時点で同じ行為が生起したという性質記述を作る。後の評価時点に行為の再発を要求せず、圧力行為の生起を因果要因として引用する。',
    'r2mk': '同じ本人・性質について、非空の厳密な順序付き履歴の異なる始点と終点の間で、両端を含む全時点に性質が成立する。評価時点は終点以後の履歴内である。取得や新しい変化は要求せず、途中の喪失や未来の未完了を保持と数えない。',
    'r2ml': '非空で重複のない人の参加者列が、同じ人の集団の構成員であり、全員が一つの生起行為へ参加し、その同じ行為が集団の共同的な働きに帰属する。集団全員の参加や、各人が単独で十分な原因になることは加えない。',
    'r2mm': '同じ集団のr2mlの行為が、同じ本人による指定状態からの離脱をh223nで制約し、その生起r2mjが同じ本人の期間全体の保持r2mkへ因果的に寄与する。要因・保持の真理と寄与は既存rqqu/hzieで全て要求する。圧力だけ、保持だけ、因果説明への採用だけでは成立しない。',
    'r2mn': 'r2mmの保持状態を既存の知的未成熟bfに固定する。集団・行為・本人・参加者・履歴・始終点・評価時点は引数に残す。公衆が後見人をその状態に留める部分に使う候補であり、先行する逆向きの作用や扇動条件はまだ付加しない。',
}
LIMITS = [
    'zwingt darunter zu bleibenの対象側を、離脱への圧力と実際の状態保持への因果的寄与として読む。制約しただけの未遂、説得、偶然の保持と区別する。制約が唯一・必要・十分な原因であるという反事実条件は加えない。',
    '同じ本人が期間を通して未成熟である読みを使い、保持を新たな取得として扱わない。期間は文脈上固定し、都合のよい時点だけを列挙しない。未来の永久的な保持や、全ての候補経過での成功を主張しない。',
    '集団の共同作用は非空の参加者群が担える。公衆全員の一斉行為、法人格、制度的代表権を追加せず、単に同じ集団の構成員だから私的行為を公衆の行為とみなすことも避ける。',
    '履歴・順序・始終点は閉じた記述として受け、同じ内容を保持の評価と因果結果へ渡す。元の原文事例の公衆・時点との照合は後続の事例結合で必要。引数を任意に与えた試験を原文の完成記述とはしない。',
    '第四段落第三文[548,593)の強制・保持の部分候補。公衆と後見人の照応、先行する逆向きの作用、扇動と啓蒙不能、頚木の指示、偏見と害・報復、閉じた帰属と文全体の再読は残る。既存59文と先頭二文382非空白文字の判断を保持する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    fields = ' '.join(n + ' ' + t for n, t in FIELDS)
    source_fields = ' '.join(n + ' ' + t for n, t in FIELDS if n != 'state')
    args = ' '.join('r[p bf]' if n == 'state' else 'v ' + n for n, _ in FIELDS)
    return '''
d r2mj[first d] h[a] e[i[act a][b anchor[k dg[v act v first]]]].
d r2mk[history h[d] c before h[d d] c first d last d state h[a] e] h[a] e[
 i[person a][b anchor[
 w[k ta[v history v before]][w[c[v history][v first]][w[c[v history][v last]][
 w[c[v history][v anchor]][w[c[v before][v first v last]][
 w[x[e[v last][v anchor]][c[v before][v last v anchor]]][
 f point d[y[w[c[v history][v point]][w[x[e[v first][v point]][c[v before][v first v point]]][
 x[e[v point][v last]][c[v before][v point v last]]]]][t[c[v state][v person]][v point]]]
 ]]]]]]
 ]]
].
d r2ml[group a act a actors j[a] point d] c[
 w[k hi[k mp[v group] p aa]][w[k hi[v actors p aa]][
 w[g person a[k hg[v actors v person]]][w[k dg[v act v point]][
 w[k h223o[v group v act v actors v point]][
 f person a[y[k hg[v actors v person]][w[k hg[k mp[v group] v person]][k df[v person v act v point]]]]
 ]]]]]
].
d r2mm[''' + fields + '''] c[
 w[k aa[v target]][w[k r2ml[v group v act v actors s[v first]]][
 w[k h223n[v act v target v state s[v first]]][
 k rqqu[v act o a[r[p r2mj]][v first] v target
 o a[r[p r2mk]][v history v before v first v last v state] v anchor]
 ]]]
].
d r2mn[''' + source_fields + '''] c[k r2mm[''' + args + ''']].
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
    core.update(declarations=closure(doc, ['r2mn']), statements=[])
    library = deepcopy(core)
    library['declarations'] = closure(doc, ['r2mm'])
    declarations = {d['name']: d for d in added}
    primitives = {n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                          arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()}
    basis = dict(status='collective_constraint_and_causal_retention_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives=primitives,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-second-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            LIBRARY: format_graph(library, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
