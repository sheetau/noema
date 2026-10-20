"""Close all relevant cases and targets of the eventual adverse return."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-prejudice-effects.noema'
PARENT_BASIS = 'data/prejudice-effects-basis-v1.json'
FULL = 'examples/v016/kant-prejudice-claim.noema'
CORE = 'examples/v016/prejudice-claim-core.noema'
BASIS = 'data/prejudice-claim-basis-v1.json'
ANNOTATIONS = 'data/prejudice-claim-identifiers-v1.json'
PROVIDERS = {
    'planter': ('h225d', '[a] a', '当該の偏見採用を生じさせる人'),
    'act': ('h225e', '[a] a', '植え付けの行為'),
    'recipient': ('h225f', '[a] a', '偏見採用を生じさせられる受け手'),
    'opinion': ('h225g', '[a] a', '同じ意見の個体'),
    'name': ('h225h', '[a] i[a]', '同じ意見の閉じた個体記述'),
    'earlier': ('h225i', '[a] d', '植え付けの先行点'),
    'earliername': ('h225j', '[a] i[d]', '同じ先行点の閉じた記述'),
    'later': ('h225k', '[a a] d', 'この対象者について経過の帰結を評価する点'),
    'role': ('h225l', '[a a] a', '生み手とこの対象者の継承を評価する同じ実践の役割'),
    'history': ('h225m', '[a a] i[h[d] c]', 'この対象者に関して問題にする全経過の閉じた範囲記述'),
    'before': ('h225n', '[a a] i[h[d d] c]', '同じ全経過の先行関係の閉じた記述'),
}
PRIMITIVES = {
    'h225b': ('[d a] c', ['reference', 'case'],
              '同じ提示の参照文脈で、偏見の植え付けと生み手側への反作用について述べる関連事例の全範囲。実際または仮定の経過を識別する。害の成否や帰属の真理を見て事例を選ばず、不都合な事例を省かない。各関係の成立は合成内容で検査する。'),
    'h225c': ('[a] j[a]', ['case'],
              '同じ固定事例で、当該の偏見を生んだ本人またはその先任者を通じて関係づけられる対象者の全列。結果の害が成立した者だけを選ばない。実際の生み手・先任者関係、人数・人の分類・重複の不在は合成内容で検査する。'),
    'h225o': ('[] a', [], '固定原文kant-1784:u0011第三文の[746,845)、weilから生み手の過去の関係までの理由節の文章箇所。関係内容はr2okで構成する。weilによる前の結論への理由関係はこの箇所参照だけでは表さない。'),
    'h225p': ('[] a', [], '固定原文kant-1784:u0011第三文の[771,783)、denen selbstの本人への取り立ての箇所。'),
}
for field, (name, signature, meaning) in PROVIDERS.items():
    params = ['case', 'target'] if signature.startswith('[a a]') else ['case']
    extra = (' 範囲は反作用の成否を見て切り詰めず、同じ因果的な展開として扱う関連局面を全て含める。'
             if field == 'history' else '')
    PRIMITIVES[name] = (signature, params, '同じ固定事例の' + meaning +
                       'を指す局所参照。参照だけで結果の真理や時間の最終性は保証しない。' + extra)
MEANINGS = {
    'r2oh': '非空の厳密な線形順序を持つ同じ履歴に終点が属し、その全点が終点と等しいか終点より前にある。文脈上の全経過の終点を検査する一般形で、世界の時間全体の終端や、その結果が初めて生じた点とはしない。',
    'r2oi': '同じ固定事例・対象者からr2ogの人物、植え付け、意見、前後点、役割、閉じた履歴と順序を供給する。同じ後の点が同じ全経過の終点であることをr2ohで要求する。意見名・先行点名の一致はr2ogの内部構成が検査する。',
    'r2oj': '同じ事例の全対象者列h225cが非空で重複のない人々の列であり、その全員にr2oiが成立する。一人への反作用だけで他の対象者を省略しない。',
    'r2ok': '参照文脈の非空の関連事例範囲h225bの全事例にr2ojが成立する内容。各事例の植え付け・当該受け手・同じ偏見・生み手または先任者・経過の終点での害を結ぶ。前半の条件付き強制を無条件の現実の出来事へ変更しない。',
    'r2ol': '同じ理由節h225o・著者wa・段落提示文脈hzp3へ、閉じた段階3の関係内容r2okをhznreportで帰属する。帰属から世界の植え付けや害を断言せず、so/weilの論述上の関係と描写は別途接続する。',
    'r2om': '順序付き列[事例,意見,本人]と参照文脈について、固定した関連事例に属し、意見が同じ事例の参照と一致し、本人が同じ全対象者列に属するという焦点範囲。害の成否から対象を選ばない。',
    'r2on': '同じ三位置の意見を同じ事例へ固定し、その同じ本人にr2oiが成立するという焦点の内容。別の意見や別の被害者へ本人の取り立てを付け替えない。',
    'r2oo': '同じ関係内容r2ok・著者・文脈で、denen selbstを固定範囲r2omの最終位置の本人の反作用r2onへ結ぶ。閉じた段階3の引用であり、強調によって対象を生み手本人だけに縮めず、先任者を持つ本人も含む。',
    'r2op': '第三文前半の統合r2nyと、後半理由節の関係内容帰属r2ol・本人の取り立てr2ooを接続した途中段階。頚木の比喩と前半の条件を保持する。so/weil、植え付けと報復の描写、文全体の通読はまだ含めない。',
}
LIMITS = [
    '後半の一般的な述定を、文脈で固定した非空の全関連事例と各事例の全対象者について読む。成功者だけを量化する例示へ縮めず、時代・社会を問わない全人類の全履歴へも勝手に広げない。範囲が原文の文脈に十分かは意味判断で別途確認する。',
    '同じ事例の受け手・意見・行為・生み手を固定する。対象者ごとの役割・経過・帰結点は同じ対象者へ結び、全被害者が同じ一瞬に害を受けるとは要求しない。',
    'zuletztは、述べている因果的な展開の終わりにという読み。関連局面を全て含む事前固定の経過を使い、単なる任意の後続点では代用しない。その後世界で何も起きないことや、同じ害がそれ以前には一度もなかったことは加えない。',
    '後半の関係内容を理由節へ帰属するが、so schädlichの程度と前半の事例との結びつき、weilの理由関係はまだ未接続である。後半の因果的な一般化から、前半の扇動条件の現実の成立や無条件の強制を導かない。',
    'denen selbstは、固定された全対象者の本人への取り立てとする。生み手本人または先任者を持つ本人という既存r2ogの選言を保持し、本人の枝だけへ焦点を縮めない。',
    '文番号59を前半と理由節の統合へ置き換え、先頭59文と既存13区間・先頭二文382非空白文字を保持する。植物の植え付け・報復の描写、so/weil、第三文全体の統合・通読が残り、意味確認済み分量は増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def supplied(name):
    if name == 'target':
        return 'v target'
    symbol, signature, _ = PROVIDERS[name]
    args = 'v case v target' if signature.startswith('[a a]') else 'v case'
    result = 'k ' + symbol + '[' + args + ']'
    return 's[' + result + ']' if name in ('history', 'before') else result


def triple(name, body):
    return ('d ' + name + '[roles j[a]] e[b reference[g case a[g opinion a[g target a['
            'w[e[v roles][l[a][v case v opinion v target]]][' + body + ']]]]]].')


def definitions():
    fields = ('planter', 'act', 'recipient', 'opinion', 'name', 'earlier', 'earliername',
              'later', 'target', 'role', 'history', 'before')
    return '''
d r2oh[history h[d] c before h[d d] c endpoint d] c[
 w[k ta[v history v before]][w[c[v history][v endpoint]][
 f point d[y[c[v history][v point]][x[e[v point][v endpoint]][c[v before][v point v endpoint]]]]
 ]]
].
d r2oi[case a target a] c[
 w[k r2og[''' + ' '.join(supplied(n) for n in fields) + ''']][
 k r2oh[''' + ' '.join(supplied(n) for n in ('history', 'before', 'later')) + ''']]
].
d r2oj[case a] c[
 w[k hi[k h225c[v case] p aa]][w[g target a[k hg[k h225c[v case] v target]]][
 f target a[y[k hg[k h225c[v case] v target]][k r2oi[v case v target]]]
 ]]
].
d r2ok[] e[b reference[
 w[g case a[k h225b[v reference v case]]][
 f case a[y[k h225b[v reference v case]][k r2oj[v case]]]]
]].
d r2ol[] c[k hznreport[k h225o[] k wa[] r d[k r2ok[]] k h225o[] k hzp3[]]].
''' + triple('r2om', '''
w[k h225b[v reference v case]][
w[e[v opinion][k h225g[v case]]][k hg[k h225c[v case] v target]]]
''') + triple('r2on', '''
w[e[v opinion][k h225g[v case]]][k r2oi[v case v target]]
''') + '''
d r2oo[] c[k h224s[k h225p[] k wa[] r d[k r2ok[]] r d[p r2om] r d[p r2on] k hzp3[]]].
d r2op[] c[w[k r2ny[]][w[k r2ol[]][k r2oo[]]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    text = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + text + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    assert statements[-1] == dict(kind='assert', body=dict(kind='call', symbol='r2ny', arguments=[]))
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2op', arguments=[]))
    doc['statements'] = statements[:-1] + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2op']), statements=[statement])
    declarations = {d['name']: d for d in added}
    basis = dict(status='prejudice_all_cases_terminal_return_and_self_focus_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/prejudice-effects-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
