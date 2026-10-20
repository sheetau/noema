"""Bind the content and contextual fields without inventing a source quotation."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_dissemination_opportunities import REMAINING, FORECAST
from scripts.compose_shared_future_period import CONDITION
from scripts.compose_existential_dissemination import EXISTENTIAL
from scripts.compose_qualitative_thinkers import QUALITATIVE
from scripts.compose_existential_route_fields import METADATA
from scripts.compose_described_dissemination import declaration
from scripts.compose_thinking_disseminators import call as k
from scripts.compose_existential_focus import PREDICATE

PARENT = 'examples/v016/kant-dissemination-opportunities.noema'
PARENT_BASIS = 'data/dissemination-opportunities-basis-v1.json'
FULL = 'examples/v016/kant-dissemination-content.noema'
CORE = 'examples/v016/dissemination-content-core.noema'
BASIS = 'data/dissemination-content-basis-v1.json'
ANNOTATIONS = 'data/dissemination-content-identifiers-v1.json'
BASE_FIELDS = [(n, t) for n, t in EXISTENTIAL + QUALITATIVE if n not in METADATA]
SPECS = {
    'hzr6': BASE_FIELDS,
    'r2lq': FORECAST + [('opportunities', 'h[d] c')],
    'r2lr': [('audience', 'a'), ('reference', 'd'), ('period', 'a')] + REMAINING,
    'r2ls': CONDITION + REMAINING,
    'r2lt': [('audience', 'a'), ('reference', 'd')] + REMAINING,
}
SUCCESSORS = dict(zip(SPECS, ('r2lu', 'r2lv', 'r2lw', 'r2lx', 'r2ly')))
CONTEXT = ['audience', 'reference']
CASES = CONTEXT + ['branch', 'person', 'anchor', 'scene']
PREFERRED = CONTEXT + ['branch', 'person', 'anchor', 'first', 'second']
PRIMITIVES = {
    'h222v': ('[a d] a', CONTEXT, '同じ公衆・参照文脈で、人としての自己の価値・長所を理由に基づいて評定する基準。金銭価格や有用性だけの基準へ固定せず、原文にない特定の高評点を補わない。実際の評定の存在・高さ・正しさはこの入力から導かない。'),
    'h222w': ('[a d] a', CONTEXT, '同じ公衆・参照文脈で、各人が自ら考える使命を論ずる事柄の参照。発信者ごとの具体的な伝達の話題とは区別する。規範内容そのものはhznqで全ての人への本人の思考要求として構成する。'),
    'h222x': ('[a d] a', CONTEXT, '同じ公衆・参照文脈で、理性を用いる人として各人の自己思考を課題とする規範の出所。神・国家・雇用者へ同定せず、人としての理性的な立場に帰属させるという採用解釈。出所の実際の権威・正当性や、規範の現実の採用は含意しない。'),
    'h222y': ('[a d] a', CONTEXT, '同じ公衆・参照文脈で、各人が人として理性を用いる立場。職業や任命された後見役の職務に限らない。hznqが全ての人の本人自身による思考要求をこの立場と規範源へ結ぶ。'),
    'h222z': ('[a d d a d d] c', CASES, '指定した仮定経過の本人・基準時に、自分の価値と人の自己思考への課題を判断する場面の範囲。本人の能力・利用できる理由・評価の機会を保った反事実的な場面を文脈から定める。成功する判断だけを選別せず、実際の一回の判断や受領の成否とは別に指定する。'),
    'h223a': ('[a d d a d d d] c', PREFERRED, 'h222zと同じ公衆・参照・仮定経過・本人・基準時について、第一の応答場面が第二より通常であるという厳密な比較。異常な妨害や注意をそらす要因など、応答の成功そのものとは別の事情に基づく。非反射性・推移性・極小場面の存在等はrqt4が検査し、数値確率を補わない。'),
    'h223b': ('[a d d a d d] c', CASES, '同じ公衆・参照・仮定経過の発信者について、基準機会に判断を求められ、理解力と理由を使い得る反事実的な場面の範囲。独立した判断への性向hzq3の入力であり、受け手の自己評価・使命承認の場面h222zと同一視しない。成功や他者の指導の欠如を見て範囲を絞らない。'),
    'h223c': ('[a d d a d d d] c', PREFERRED, 'h223bの同じ発信者・機会・仮定経過で、第一の場面を第二より通常とみなす厳密な比較。独立判断の成功から順位を逆算しない。比較の整合性と極小場面の存在はrqt4で検査する。受け手の性向の通常性と別の入力である。'),
    'h223d': ('[a d d a d d] a', CASES, 'h223bの同じ発信者・機会・仮定経過・場面で、その人が判断を求められる事柄。理由ある独立判断を同じ話題へ結ぶための入力。任意の別話題への成功で置き換えず、特定の学問分野を原文に補わない。'),
    'h223e': ('[a d d a a d] c', CONTEXT + ['branch', 'person', 'subject', 'scene'], '同じ仮定経過の発信者へ、この応答場面でこの事柄が判断の対象として提示されている。提示を判断の成功や同意と同一化せず、hzq3の話題とhzhgの判断対象を一致させる。'),
    'h223f': ('[a d d d] c', CONTEXT + ['branch', 'point'], '同じ公衆・参照文脈・仮定経過について、議論上の観察・評価機会としてあらかじめ指定した時点。自己思考者の存在や伝播の成功から選ばない。r2lpが非空・基準後・同じ期間内・後続時点ありを検査する。'),
    'h223g': ('[a] i[a]', ['individual'], '指定個体を引用内で指すために使う閉じた呼称の記述候補。外側の変数の値を引用へ暗黙に取り込む演算ではない。呼称が実際に元の個体を指すことは利用側で評価して一致を検査する。複数の呼称の同義性や任意の個体の命名可能性は保証しない。'),
    'h223h': ('[d] i[d]', ['situation'], '指定状況を引用内で指すために使う閉じた呼称の記述候補。状況の時刻名や文字列だけを意味へ置き換えず、利用側でその参照先と元の状況の一致を検査する。全状況の自動命名や任意の別表記の同義性は含意しない。'),
}
MEANINGS = {
    'r2lu': '同じ発信者・機会について、独立判断と自己離脱・伝播の既存hzr6を満たす話題と閉じた発話記述が存在する。発話の台詞を原文へ補わず、受領・理解・同じ性向の取得と因果を満たす存在を要求する。同じ発信者・機会では話題と抽象的発話内容を共用し、受け手ごとの経路と取得過程は別に存在してよい。',
    'r2lv': 'r2lqの各人・各評価機会の条件をr2luへ替え、話題・発話の供給関数を除く。他の人、別の機会の発話を流用せず、複数人と指定部分集団、非空の評価機会と将来の取得を保持する。',
    'r2lw': 'r2lrの同じ公衆・参照・期間・仮定経過を保ち、話題・発話を各人・機会の内部に存在量化したr2lvの内容族を作る。残る八供給関数を同じ候補へ渡す。',
    'r2lx': 'r2lsと同じ自由条件の枠へr2lwを接続する。発話の文面を外から固定せず、条件内の同じ発信者と機会で存在を述べる。',
    'r2ly': 'r2ltと同じ第一文の公衆・参照・出所・期間・起点・候補を共用し、r2lxへ接続する。第一文の主張内容と第二文の理由内容を同一視しない。',
    'r2lz': '同じ公衆・参照・仮定経過から、受け手本人の理由ある自己評価と全ての人の自己思考への課題を認めるhznuを応答とし、hzq6で数値なしの性向を構成する。基準・規範源・立場・通常性を固定し、応答と規範の現実の真理を区別する。',
    'r2m2': 'r2lzへ同じ公衆・参照・仮定経過の値を引用適用し、閉じた性向記述を構成する。同じ記述が受け手の状態評価・取得の原因・持続へ渡る。発信者の独立判断の性向とは区別する。',
    'r2m3': 'r2lyの八供給関数を全て充足する。受け手の性向はr2m2、社会的周囲はhzom、広がりはその範囲の異なる二人以上への取得rqsy、発信者の判断と評価機会は同じ公衆・参照・仮定経過の文脈入力へ結ぶ。部分集団だけを引数に残した条件付き内容の枠であり、任用された後見役の焦点・背景・著者帰属は別に接続する。',
    'r2m4': '閉じた性向記述へ渡す公衆と参照状況の呼称、および指定された全仮定候補の呼称を評価し、元の対象と等しいことを検査する。誤った呼称の候補を対象範囲から除いて成功させない。呼称の構文同一性は要求せず、指示対象の一致を要求する。',
}
LIMITS = [
    'Geistを、理由ある自己評価と全ての人の自己思考への課題を認める判断への持続的な性向として読む。実際の一回の判断、発信者の独立判断、規範自体の真理を同一化しない。',
    '自己評価の基準・規範源・人としての立場を意味規約に明記するが、価値の数値・高い自尊心・国家や神による命令は原文に補わない。規範の出所を人の理性的な立場として扱う明示的な読みである。',
    '性向の場面と通常性は、本人の能力・機会・理由・妨害の有無などの文脈入力である。成功結果から場面や順位を選ばない。rqt4は順序条件を検査するが、現実に適切な反事実場面を自動発見するものではない。',
    '具体的な話題と発話を存在で記述し、全員が原文にない同じ台詞を言うとはしない。同じ発信者・評価機会では一つの抽象的発話内容を共用する読みを採る。引用記述の同一性は表面上の文面の一致を意味しないが、意味が変わる伝播や任意の言い換えの同義性まで自動認定しない。',
    'um sichは、情報・援助の供給元として一方が他方を利用できる社会的な接点の範囲hzomとして読む。実際の利用・親密さ・地理的な近さは要求しない。中心本人はrqthで除外し、全公衆の読者範囲へ広げない。',
    'verbreitenは、その周囲の異なる二人以上に同じ性向の新しい取得が生じる読み。全員・過半数・同時の取得・中継者全員の同意を要求しない。語の全用法をこの人数条件へ還元するものではない。',
    '任意長の有限経路と記述の存在は文法で記述する。有限評価器で全ての発話・経路を探索し終える手続ではなく、指定した証人の成功と不存在の証明を区別する。',
    '引用に公衆・参照状況・仮定候補を入れるため、閉じた呼称の候補を使い、元の対象との一致をr2m4で要求する。呼称の内容が未知なら補完せず、指し先が違えば枠は不成立とする。この接続は必要な対象を呼称で指定できる解釈を対象とする。',
    '八供給関数を充足した条件付き枠までを接続する。任用・大衆、sogarの期待背景、頚木の比喩と自己離脱の同じ人物への対応、閉じた著者帰属、第二文全体の再読判断は残る。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def quantified_declarations():
    old = parent()
    removed = {n: {i for i, (p, t) in enumerate(fields) if p in ('subject', 'message')}
               for n, fields in SPECS.items()}

    def rewrite(node):
        if isinstance(node, list):
            return [rewrite(x) for x in node]
        if not isinstance(node, dict):
            return node
        if node.get('kind') == 'call' and node['symbol'] in SUCCESSORS:
            name = node['symbol']
            return dict(kind='call', symbol=SUCCESSORS[name],
                        arguments=[rewrite(x) for i, x in enumerate(node['arguments']) if i not in removed[name]])
        return {k: rewrite(v) for k, v in node.items()}

    declarations = []
    for name, fields in SPECS.items():
        doc = deepcopy(old.entries[name]['declaration'])
        assert len(doc['parameters']) == len(fields)
        bound = [p for i, p in enumerate(doc['parameters']) if i in removed[name]]
        assert len(bound) == 2
        doc['name'] = SUCCESSORS[name]
        doc['parameters'] = [p for i, p in enumerate(doc['parameters']) if i not in removed[name]]
        doc['body'] = rewrite(doc['body'])
        if name == 'hzr6':
            for p in reversed(bound):
                doc['body'] = dict(kind='exists', variable=p['name'], sort=p['sort'], body=doc['body'])
        declarations.append(doc)
    return declarations


def definitions():
    fixed = 'v audience v reference v branch'
    describe = lambda name: 'o a[r[p ' + name + ']][k h223g[v audience] k h223h[v reference]]'
    response = k('hznu', k('h222v', 'v audience', 'v reference'), k('h222w', 'v audience', 'v reference'),
                 describe('h222x'), describe('h222y'))
    text = declaration('r2lz', [('audience', 'a'), ('reference', 'd'), ('branch', 'd')], 'h[a] e',
                       k('hzq6', response,
                         'i[person a anchor d scene d][k h222z[' + fixed + ' v person v anchor v scene]]',
                         'i[person a anchor d first d last d][k h223a[' + fixed + ' v person v anchor v first v last]]'))
    text += declaration('r2m2', [('audience', 'a'), ('reference', 'd'), ('branch', 'd')], 'i[h[a] e]',
                        'o a[r[p r2lz]][k h223g[v audience] k h223h[v reference] k h223h[v branch]]')
    text += '''
d r2m4[audience a reference d] c[
 w[e[s[k h223g[v audience]]][v audience]][w[e[s[k h223h[v reference]]][v reference]][
 f branch d[y[k h222k[v audience v reference v branch]][e[s[k h223h[v branch]]][v branch]]]
 ]]
].
'''
    supplied = [
        'i[branch d][k r2m2[' + fixed + ']]',
        'i[branch d][p rqsy]', 'i[branch d][p hzom]',
        'i[branch d][i[person a anchor d scene d][k h223b[' + fixed + ' v person v anchor v scene]]]',
        'i[branch d][i[person a anchor d first d last d][k h223c[' + fixed + ' v person v anchor v first v last]]]',
        'i[branch d][i[person a anchor d scene d][k h223d[' + fixed + ' v person v anchor v scene]]]',
        'i[branch d][i[person a subject a scene d][k h223e[' + fixed + ' v person v subject v scene]]]',
        'i[branch d][i[point d][k h223f[' + fixed + ' v point]]]',
    ]
    text += declaration('r2m3', [('audience', 'a'), ('reference', 'd')], 'h[' + PREDICATE + '] e',
                        'i[subgroup ' + PREDICATE + '][b point[w[k r2m4[v audience v reference]][' +
                        't[c[' + k('r2ly', 'v audience', 'v reference', *supplied) +
                        '][v subgroup]][v point]]]]')
    return ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items()) + text


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    doc['declarations'].extend(quantified_declarations())
    doc = parse(format_graph(doc, 'compact') + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    declarations = {d['name']: d for d in added}
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2m3', 'hzpy']), statements=[])
    primitives = {n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                          arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()}
    basis = dict(status='dissemination_fields_bound_under_explicit_reading_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives=primitives,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/dissemination-opportunities-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
