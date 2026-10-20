"""Bind forecast opportunities and dissemination to one contextual scenario."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_shared_public_scope import PROVIDERS
from scripts.compose_shared_future_period import CONDITION
from scripts.compose_existential_route_fields import SPECS, METADATA
from scripts.compose_described_dissemination import declaration
from scripts.compose_thinking_disseminators import call as k
from scripts.compose_existential_focus import FAMILY, PREDICATE

PARENT = 'examples/v016/kant-public-first-sentence.noema'
PARENT_BASIS = 'data/public-first-sentence-basis-v1.json'
FULL = 'examples/v016/kant-dissemination-opportunities.noema'
CORE = 'examples/v016/dissemination-opportunities-core.noema'
BASIS = 'data/dissemination-opportunities-basis-v1.json'
ANNOTATIONS = 'data/dissemination-opportunities-identifiers-v1.json'
REMAINING = [(n, t) for n, t in PROVIDERS if n not in ('reference', 'frame', 'anchor')]
REMAINING += [('opportunities', 'h[d] h[d] c')]
FORECAST = [(n, t) for n, t in SPECS['hzq5'] if n not in METADATA]
MEANINGS = {
    'r2lp': '同じ整合した履歴・順序・基準点について、明示した非空の評価機会全てが基準より後の履歴内にあり、各機会の後にも同じ履歴内の時点があることを要求する。その全機会で同じ応答を要求する。機会範囲は結果から逆算せず文脈で指定し、無効な機会を除いて成功させない。伝播の完了が機会より後である読みへの一般的な時間枠。',
    'r2lq': 'hzr7の将来の全時点へのrqtjを、明示した評価機会へのr2lpに替える。各機会での複数人、部分集団の一人、独立判断、共有する自己離脱、受け手ごとの存在する経路と取得は同じ本体を保つ。履歴の全時点と文脈上の評価機会を同一視しない。',
    'r2lr': '同じ公衆・参照文脈・期間と候補からr2lqの内容族を作る。構成員はrqu3、周囲の参照は同じ参照文脈、各人の伝播期間は同じ期間、出来事の評価文脈は同じ候補に固定する。評価機会は開始時点として渡し、候補の代わりに使わない。残る十供給関数は同じ候補を受け、部分集団の違いで取り替えない。',
    'r2ls': '既存rqtpの自由条件とr2lrの内容族を結び、同じ期間・公衆・参照文脈・候補を共有する。自由が満たされる候補の中で、各機会より後に同じ期間内で伝播の取得がある読み。自由条件を満たさない候補の不正な履歴も既存hzneが拒否する。',
    'r2lt': '第一文の同じ公衆・参照文脈からh222f/g/h/kで出所・期間・起点対応・候補を供給してr2lsへ接続する。第一文のほぼ必然と第二文の理由内容の同義性や、後者から前者への論理的含意を加えない。内容、性向、周囲、広がり、評価機会の十供給関数は原文に合わせて束縛する作業が残る。',
}
LIMITS = [
    'immerを、自由について述べた同じ仮定の中で、文脈上の各評価機会に該当する人がいる読みとする。期間の全ての時点、物理的な無限時間、永久に同じ人物という別の読みはこの構成で同時に主張しない。',
    '評価機会と、その後の伝播の取得時点を区別する。有限期間の最終時点を評価機会へ入れると後続取得がなく不成立になる。最終点を自動で捨てず、文脈が指定した機会を検査する。',
    '評価機会は、観察や議論の関心からあらかじめ決める入力である。自己思考者の存在や伝播の成功から選別しない。任意の成功点だけを選べば原文を記述できたとはしない。',
    '自由と予測に同じ期間・候補・起点を使う。伝播経路と自己離脱は既存の存在量化を保持する。自己離脱が基準点以前に起きた場合も、同じ期間内で順序を満たせば許す。',
    '伝播の完了を各評価機会より後に置くのは既存形を引き継ぐ明示した読み。文脈がすでに伝播を始めた人を含む場合も、取得の完了が後なら排除しない。全ての自然言語の時制をこの枠へ還元しない。',
    '一般的な時間関係と既存の伝播定義の接続を検査する。任意長の経路を全探索した証明、実際に予測が正しいという認定、第二文全体の意味判断ではない。',
    '第一文108非空白文字と既存十三単位の判断を保持する。第二文の残る内容入力、sogarの比較背景、任用・大衆、頚木の比喩の全接続、閉じた著者帰属を完成させてから第二文を通読する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def forecast_declaration():
    doc = deepcopy(parent().entries['hzr7']['declaration'])
    doc['name'] = 'r2lq'
    # Use the parsed public syntax for the function-sort representation.
    sample = parse('p:d z[opportunities h[d] c] c[e[v opportunities][v opportunities]].')
    opportunity = sample['declarations'][0]['parameters'][0]
    # The canonical va already belongs to the inherited parameters.
    opportunity['name'] = 'opportunities'
    doc['parameters'].append(opportunity)
    call = doc['body']['body']
    assert call['symbol'] == 'rqtj'
    call['symbol'] = 'r2lp'
    call['arguments'].insert(3, dict(kind='variable', name='opportunities'))
    return doc


def opportunity_definition():
    return '''
d r2lp[history h[d] c before h[d d] c base d opportunities h[d] c response h[d] c] c[
 w[k ta[v history v before]][w[c[v history][v base]][w[g point d[c[v opportunities][v point]]][
 f point d[y[c[v opportunities][v point]][
 w[c[v history][v point]][w[c[v before][v base v point]][
 w[k rqtb[v history v before v point]][c[v response][v point]]]]
 ]]
 ]]]
].
'''


def connections():
    supplied = {n: 'c[v ' + n + '][v branch]' for n, t in REMAINING}
    supplied.update(history=k('rqtw', 'v period', 'v branch'), before=k('rqtx', 'v branch'),
                    members=k('rqu3', 'v audience', 'v reference'),
                    reference='i[person a opportunity d][v reference]',
                    frame='i[person a opportunity d][v period]',
                    anchor='i[person a opportunity d][v branch]', subgroup='s[v subgroup]')
    text = declaration('r2lr', [('audience', 'a'), ('reference', 'd'), ('period', 'a')] + REMAINING,
                       FAMILY, 'i[subgroup ' + PREDICATE + ' branch d][' +
                       k('r2lq', *(supplied[n] for n, t in FORECAST), supplied['opportunities']) + ']')
    text += declaration('r2ls', CONDITION + REMAINING, 'h[' + PREDICATE + '] e',
                        k('rqtp', *('v ' + n for n, t in CONDITION),
                          k('r2lr', 'v permissionaudience', 'v permissionreference', 'v permissionframe',
                            *('v ' + n for n, t in REMAINING))))
    fixed = ['v audience', 'v reference', k('h222f', 'v audience', 'v reference'),
             k('h222g', 'v audience', 'v reference'),
             'i[branch d][' + k('h222h', 'v audience', 'v reference', 'v branch') + ']',
             'i[branch d][' + k('h222k', 'v audience', 'v reference', 'v branch') + ']']
    text += declaration('r2lt', [('audience', 'a'), ('reference', 'd')] + REMAINING,
                        'h[' + PREDICATE + '] e', k('r2ls', *fixed, *('v ' + n for n, t in REMAINING)))
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + opportunity_definition())
    doc['declarations'].append(forecast_declaration())
    doc = parse(format_graph(doc, 'compact') + connections())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2lt', 'hzpy']), statements=[])
    basis = dict(status='shared_scenario_with_explicit_prospective_opportunities_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 primitives={}, definitions=MEANINGS,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-first-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
