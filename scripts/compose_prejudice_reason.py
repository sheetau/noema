"""Connect the harmfulness assessment, demonstrative degree and reason."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_prejudice_claim import supplied

PARENT = 'examples/v016/kant-prejudice-claim.noema'
PARENT_BASIS = 'data/prejudice-claim-basis-v1.json'
FULL = 'examples/v016/kant-prejudice-reason.noema'
CORE = 'examples/v016/prejudice-reason-core.noema'
BASIS = 'data/prejudice-reason-basis-v1.json'
ANNOTATIONS = 'data/prejudice-reason-identifiers-v1.json'
PRIMITIVES = {
    'h225q': ('[i d[h[j[a]] e] j[a] d] c', ['property', 'roles', 'reference'],
              '指定した閉じた内容関数と同じ順序付き引数について、その性質の程度をこの評価文脈で高いものとして扱う。既存hzxrと同じ評価関係を段階3の記述に適用する一般形。数値、最大性、各構成員が一律に高い程度を持つこと、基礎の性質の真理は含意せず、性質の成立は別に検査する。'),
    'h225r': ('[a a i d[e] i d[h[j[a]] e] a i d[e] d] c',
              ['node', 'author', 'claim', 'property', 'example_node', 'example', 'context'],
              '同じ著者・提示文脈の主張で、指定した性質の程度を、先行箇所の内容が示す程度として指示して取り立てる。例示側の条件・様相・留保は保持する。実際に先行の出来事が起きたこと、二内容の論理的含意、二事例の人物や時点の同一性、数値的な程度の等式は含意しない。'),
    'h225s': ('[] a', [], '固定原文kant-1784:u0011第三文の[701,744)、so schädlichから偏見を植えることまでの評価を述べる箇所。'),
}
MEANINGS = {
    'r2oq': '同じ事例・対象者のr2oiがr2ogへ渡す参照のうち、植え付けから後の不利益へのr2oeに必要な全引数を同じ順序で渡す。生み手または先任者という関係と経過の終点の条件は理由側に残し、結論側の害の関係に必要な因果・実際の要因と結果・前後順序は保つ。',
    'r2or': '同じ事例の非空で重複のない全対象者にr2oqが成立する。前の理由節と同じ全列h225cを使い、害の評価のために別の対象者列を選び直さない。',
    'r2os': '順序付き列の一位置を事例とし、その同じ事例のr2orを内容とする性質の族。程度評価はこの事例全体の害について行い、各対象者に別々の高程度を要求しない。一位置以外の列は成立しない。',
    'r2ot': '同じ非空の全関連事例h225bについて、r2orの害の成立と、同じ事例のr2osの高程度評価をともに要求する内容。程度の評価だけで実際の因果的な不利益を代用せず、数値尺度を補わない。',
    'r2ou': '評価箇所h225s・著者wa・段落文脈hzp3へ閉じた段階3の内容r2otを帰属する。世界の害や評価を帰属時に実行しない。',
    'r2ov': '同じ評価主張r2otの性質r2osの程度を、前半の箇所h224mの同じ条件付き内容r2nfが示す程度として指示する提示を帰属する。条件付きの反転を無条件の出来事へ強めず、前半と後半の事例の人物を機械的に同一視しない。',
    'r2ow': '既存udで理由節h225oを評価箇所h225sの根拠として同じ著者・段落文脈へ結び、ueで前半h224m・評価・理由節の本文順序を保つ。理由節と評価箇所の区別も要求する。論証の十分性や引用内容の真理は要求しない。',
    'r2ox': '前半と後半理由節の統合r2opへ、害と高程度の評価の帰属r2ou、先行内容を受ける程度指示r2ov、weilの理由提示と本文順r2owを接続する。植え付け・報復の非字義的描写と第三文全体の通読はまだ含めない。',
}
LIMITS = [
    'so schädlichを、前半の作用の反転を受けて、偏見を植え付けることがこれほど有害だと高い程度を取り立てる読みで採る。正確な損失額・確率・尺度値や最大性を補わない。程度を指示する提示と、性質の成立を別の条件とする。',
    '有害さは同じ植え付けから同じ受け手の偏見採用を経て対象者の不利益へ至る既存r2oeの関係で構成する。因果の推移律によって植え付け行為から不利益への新しい直接原因を導かない。元の二つの因果関係を保持する。',
    '高程度の評価は固定事例の全体について行う。各対象者の損害が個別に高い、全対象者が同時に害を受ける、という強い読みは追加しない。事例・対象者は理由節と同じ範囲を使う。',
    'soの先行内容への指示では前半の条件を保持する。前半の公衆の強制と後半の偏見の一般的反作用に、原文で決まっていない人物・行為・時点の一対一対応を足さない。',
    'weilは理由節の内容を有害さの評価の根拠として提示する既存udに結ぶ。理由の提示から高程度評価の数学的な証明や、原文の主張の現実の真理を自動認定しない。',
    '先頭59文と既存13区間・先頭二文382非空白文字を保持する。文番号59を今回の統合へ置き換える。植物の植え付け・報復の描写、第三文全体の統合の再読と意味判断が残り、今回も意味確認済み分量を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    fields = ('planter', 'act', 'recipient', 'opinion', 'name', 'earlier', 'earliername',
              'later', 'target', 'history', 'before')
    return '''
d r2oq[case a target a] c[k r2oe[''' + ' '.join(supplied(n) for n in fields) + ''']].
d r2or[case a] c[
 w[k hi[k h225c[v case] p aa]][w[g target a[k hg[k h225c[v case] v target]]][
 f target a[y[k hg[k h225c[v case] v target]][k r2oq[v case v target]]]
 ]]
].
d r2os[roles j[a]] e[b reference[g case a[
 w[e[v roles][l[a][v case]]][k r2or[v case]]
]]].
d r2ot[] e[b reference[
 w[g case a[k h225b[v reference v case]]][
 f case a[y[k h225b[v reference v case]][
 w[k r2or[v case]][k h225q[r d[p r2os] l[a][v case] v reference]]
 ]]]
]].
d r2ou[] c[k hznreport[k h225s[] k wa[] r d[k r2ot[]] k h225s[] k hzp3[]]].
d r2ov[] c[k h225r[k h225s[] k wa[] r d[k r2ot[]] r d[p r2os]
 k h224m[] r d[k r2nf[]] k hzp3[]]].
d r2ow[] c[
 w[u[e[k h225s[]][k h225o[]]]][
 w[k ud[k wa[] i[node a][e[v node][k h225o[]]] k h225s[] k hzp3[]]][
 w[k ue[k h224m[] k h225s[] k hzp3[]]][k ue[k h225s[] k h225o[] k hzp3[]]]]]
].
d r2ox[] c[w[k r2op[]][w[k r2ou[]][w[k r2ov[]][k r2ow[]]]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    assert statements[-1] == dict(kind='assert', body=dict(kind='call', symbol='r2op', arguments=[]))
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2ox', arguments=[]))
    doc['statements'] = statements[:-1] + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2ox']), statements=[statement])
    declarations = {d['name']: d for d in added}
    basis = dict(status='harmfulness_degree_and_reason_connected_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/prejudice-claim-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
