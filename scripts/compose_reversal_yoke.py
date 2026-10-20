"""Keep the same case roles while depicting immaturity as a yoke state."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_public_reversal import FIELDS
from scripts.compose_reversal_attribution import PROVIDERS

PARENT = 'examples/v016/kant-reversal-attribution.noema'
PARENT_BASIS = 'data/reversal-attribution-basis-v1.json'
FULL = 'examples/v016/kant-reversal-yoke.noema'
CORE = 'examples/v016/reversal-yoke-core.noema'
BASIS = 'data/reversal-yoke-basis-v1.json'
ANNOTATIONS = 'data/reversal-yoke-identifiers-v1.json'
PRIMITIVES = {
    'h224n': ('[a a i d[e] i d[h[j[a]] e] i d[h[j[a]] e] i d[h[j[a]] e] d] c',
              ['node', 'author', 'claim', 'scope', 'target', 'depiction', 'context'],
              '提示者が同じ主張の中で、指定した範囲に属する順序付き対象列と内容評価点に関する対象側の関係を、描写側の関係によって非字義的に提示する。範囲・対象・描写は同じ列の位置と評価点を共有し、別々の人物や時点を後から同じとみなさない。既存rbtと同種の非字義的な提示を、主張・範囲と段階3の関係記述に結ぶ。引用内容の真理、物理的な出来事の実在、両側の因果の同一性は含意しない。'),
    'h224o': ('[] a', [], '固定原文kant-1784:u0011第三文の[513,546)、先行してこの頚木の下へ置かれたという描写の箇所。装具そのものの固有名ではない。'),
    'h224p': ('[a a a i[h[a] e] i[h[a] e] d] c',
              ['node', 'antecedent', 'author', 'state', 'depiction', 'context'],
              '同じ著者・提示文脈で、現在の箇所が先行する非字義的な提示を受け、そこで対応づけられた状態の種類と身体的な描写の種類を、指定された二つの性質記述として再び指す。同じ状態・描写の種類への照応であり、描写上の個々の物体の同一性、状態や出来事の真理、担い手の同一性そのものは含意しない。'),
    'h224q': ('[] a', [], '固定原文kant-1784:u0011第三文の[574,593)、その下に留まるという描写の箇所。指す状態の種類を先行するこの頚木の描写へ結ぶ。'),
}
MEANINGS = {
    'r2nh': '同じ身体主体に、既存hzpkの首・頭側へ装着される牽引用の枠があるという内容。前文の除去描写が前状態に要求する同じ装具の種類を再利用する。人物間や全時点に物理的に一個の装具を要求せず、牽引の実行や未成熟の事実も含意しない。',
    'r2ni': '先行する集団作用r2mpの結果状態を閉じた性質記述として受け取る一般形。被作用者の全範囲・先行参加者・共同作用を保ち、同じ状態の実際の成立とその同じ行為による結果生成を要求する。',
    'r2nj': '作用の反転r2mrの先行作用をr2ni、後の保持をr2mmへ一般化し、両者の状態を同じ閉じた記述へ結ぶ。人物、時間順序、役割と扇動の条件、期間内保持と因果を変更しない。',
    'r2nk': '同じ原文事例の参照と先行対象範囲を保ち、r2njの状態だけを引数へ残す。後見役・取得不能・扇動は既存の同じ構成を使う。圧力行為名の一致も含意の外で要求し、比喩の描写へ移るときに別の人・行為・期間を供給しない。',
    'r2nl': '順序付き列を公衆・事例の二位置に固定し、内容評価点を参照文脈として、対象側の既存r2neを評価する。二位置以外の列はrbvにより成立しない。',
    'r2nm': '同じ公衆・事例の二位置と参照文脈について、先頭二文の公衆範囲h222eと、第三文の事例範囲h223wを共に要求する。対象と描写へ共通に適用する範囲の内容である。',
    'r2nn': 'r2nlと同じ二位置と参照文脈を保ち、r2nkの状態を身体的な頚木装着r2nhへ固定した描写。先行する装着状態の生成と、後の同じ種類の状態からの離脱制約・保持への因果を同じ事例の役割へ結ぶ。',
    'r2no': '同じ第三文前半の主張r2nf・範囲r2nmにおいて、関係内容r2nlを身体的描写r2nnによって非字義的に提示したと帰属する。三つの関係記述は閉じた段階3で渡し、実行しない。',
    'r2np': 'この頚木の箇所h224oを前文の除去描写hzpoへ、その下に留まる箇所h224qをh224oへ結ぶ。未成熟bfと装着状態r2nhの同じ種類の対応、および同じ提示文脈での二つの本文順序を要求する。物理的な一個の装具の再登場を要求しない。',
    'r2nq': '第三文前半の既存の関係内容の帰属r2ng、同じ役割に結ぶ非字義的な描写r2no、状態の種類の照応と本文順序r2npを統合する。Besonders/selbstと第三文後半はまだ含めない。',
}
LIMITS = [
    'dieses Jochとdarunterを、前文から続く知的未成熟と頚木装着という同じ種類の対応への照応として読む。前文の自己離脱者、先に拘束される公衆、後に留められる後見人を同一人物へ縮めず、装具の物理的同一性も追加しない。',
    '描写側の先行作用・後の保持には対象側と同じ役割と事例参照を渡す。状態の記述のみをbfからr2nhへ替える。前後の行為や時点を別の事例から選び直さず、扇動の条件や因果を省略しない。',
    '保持は同じ種類の装着状態が期間を通じて続く読みである。各時点の装具が常に同じ一個であることまでは要求しない。これは状態の種類を受ける読みであり、物体の同一性についての原文の追加主張を捏造しない。',
    '前文の対象側の離脱過程h4pはbfを前状態に持ち、描写側の除去hzpmはhzpkを前状態に持つ。今回のr2nhはhzpkの装具の存在を取る。同じ種類の照応をこの依存関係に結び、実際の知的・身体的な出来事の真理を比喩の帰属から導かない。',
    '60番目の未確認の前半帰属を、同じ内容帰属を含む統合形へ置き換える。先頭59文、十三の全単位判断、第四段落先頭二文382非空白文字は保持する。Besonders/selbst、後半の偏見の害と報復、第三文全体の統合・通読は残り、確認済み文字数は増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def early_definitions():
    return '''
d r2nh[person a] e[b point[g object a[t[k hzpk[v object v person]][v point]]]].
d r2ni[public a guardians a affected j[a] former j[a] act a point d state i[h[a] e]] c[
 w[k r2mo[v public v affected]][w[k r2ml[v guardians v act v former v point]][
 f person a[y[k hg[v affected v person]][
 w[t[c[s[v state]][v person]][v point]][k g3[v act v person v state v point]]
 ]]]]
].
'''


def generalized_reversal():
    original = deepcopy(parent().entries['r2mr']['declaration'])
    original['name'] = 'r2nj'
    state = dict(kind='variable', name='state')
    original['parameters'].append(dict(name='state', sort=dict(
        kind='description', result=dict(kind='function', parameters=['individual'], result='content'))))

    def replace(node):
        if isinstance(node, list):
            return [replace(item) for item in node]
        if not isinstance(node, dict):
            return node
        node = {key: replace(value) for key, value in node.items()}
        if node.get('kind') == 'call' and node['symbol'] == 'r2mp':
            node.update(symbol='r2ni', arguments=[*node['arguments'], deepcopy(state)])
        if node.get('kind') == 'call' and node['symbol'] == 'r2mn':
            node.update(symbol='r2mm', arguments=[*node['arguments'][:-1], deepcopy(state), node['arguments'][-1]])
        return node
    original['body'] = replace(original['body'])
    return original


def late_definitions():
    affected = 'k h223v[v public r[p bf] k h224b[v case]]'
    def value(name):
        if name == 'public':
            return 'v public'
        if name == 'affected':
            return affected
        if name == 'guardianrole':
            return 'p r2mu'
        if name == 'incapable':
            return 'p r2mt'
        if name == 'incites':
            return 'k r2na[k h224f[v case] k h224l[v case]]'
        return 'k ' + PROVIDERS[name][0] + '[v case]'
    args = ' '.join(value(n) for n, _ in FIELDS) + ' v state'
    return '''
d r2nk[public a reference d case a state i[h[a] e]] c[
 w[k h223w[v public v reference v case]][
 w[k r2nc[v public ''' + affected + ''' r[p bf] k h224b[v case]]][
 w[e[s[k h224l[v case]]][k h224e[v case]]][k r2nj[''' + args + ''']]]
 ]
].
d r2nl[roles j[a]] e[k rbv[i[public a case a][b reference[k r2ne[v public v reference v case]]] v roles]].
d r2nm[roles j[a]] e[k rbv[i[public a case a][b reference[
 w[k h222e[v public v reference]][k h223w[v public v reference v case]]
 ]] v roles]].
d r2nn[roles j[a]] e[k rbv[i[public a case a][b reference[k r2nk[v public v reference v case r[p r2nh]]]] v roles]].
d r2no[] c[k h224n[k h224m[] k wa[] r d[k r2nf[]]
 r d[p r2nm] r d[p r2nl] r d[p r2nn] k hzp3[]]].
d r2np[] c[
 w[k h224p[k h224o[] k hzpo[] k wa[] r[p bf] r[p r2nh] k hzp3[]]][
 w[k h224p[k h224q[] k h224o[] k wa[] r[p bf] r[p r2nh] k hzp3[]]][
 w[k ue[k hzpo[] k h224o[] k hzp3[]]][k ue[k h224o[] k h224q[] k hzp3[]]]]]
].
d r2nq[] c[w[k r2ng[]][w[k r2no[]][k r2np[]]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    text = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + text + early_definitions())
    doc['declarations'].append(generalized_reversal())
    doc = parse(format_graph(doc, 'compact') + late_definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    assert statements[-1] == dict(kind='assert', body=dict(kind='call', symbol='r2ng', arguments=[]))
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2nq', arguments=[]))
    doc['statements'] = statements[:-1] + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2nq']), statements=[statement])
    declarations = {d['name']: d for d in added}
    basis = dict(status='reversal_yoke_relation_and_anaphora_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2])
                             for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/reversal-attribution-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
