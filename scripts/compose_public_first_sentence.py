"""Preserve contrast, strengthening and qualified sufficiency in the first sentence."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-public-comparison-claim.noema'
PARENT_BASIS = 'data/public-comparison-claim-basis-v1.json'
FULL = 'examples/v016/kant-public-first-sentence.noema'
CORE = 'examples/v016/public-first-sentence-core.noema'
BASIS = 'data/public-first-sentence-basis-v1.json'
ANNOTATIONS = 'data/public-first-sentence-identifiers-v1.json'
PAIR_SIGNATURE = '[a a a i b[e] a i b[e] i[h[a] e] d] c'
PAIR_ARGUMENTS = ['node', 'presenter', 'first_node', 'first_content', 'second_node',
                  'second_content', 'common_dimension', 'context']
PRIMITIVES = {
    'h222q': (PAIR_SIGNATURE, PAIR_ARGUMENTS,
              '提示者が同じ箇所・文脈で、指定された二箇所の内容を、明示した共通観点に関して対照的に提示する。第一から第二への向きを保持するが、前者の否定、論理的矛盾、内容の真理、通常予想への違反をそれだけで要求しない。観点は性質記述であり、対象の語形や単なる文の前後だけで対比を代用しない。'),
    'h222r': (PAIR_SIGNATURE, PAIR_ARGUMENTS,
              '提示者が同じ箇所・文脈と共通観点で、第一の内容を受け、第二の内容を一段強い言い方として追加提示する。第二に明示された条件・様相・留保をそのまま保持する。論理的含意、二内容の真理、無条件と条件付きの数値確率の大小、第一の撤回を要求しない。強い言い方としての論述上の扱いを表す基本関係で、特定の接続語専用ではない。'),
    'h222s': ('[a a i[h[a d] c] i b[h[a d] e] i b[h[a d] e] i b[h[a d] c] d] c',
              ['node', 'presenter', 'subject_scope', 'condition_family', 'goal_family', 'qualification_family', 'context'],
              '提示者が指定箇所・文脈で、対象範囲の同じ個体・参照状況へ適用した条件を、同じ目標について指定の限定付き判断を述べるために足りるものとして取り立て、さらに供給すべき要件を付加しないと提示する。条件と目標は候補で評価する内容の族、限定は同じ二つを結ぶ様相等の判断である。限定を落として無条件の成功へ強めず、背景を消さず、条件の必要性・唯一原因性・現実の真理を含意しない。hzxlに関連する一般化だが人物専用の型を変更しない。'),
    'h222t': ('[] a', [], '固定原文kant-1784:u0011第一文のセミコロン前、公衆の自己啓蒙がより可能だと述べる主節の箇所。原文への範囲参照であり、その内容自体はr2ljで構成する。'),
    'h222u': ('[] a', [], '固定原文kant-1784:u0011第一文のjaから文末まで、自由を残す条件下でほぼ避けがたいと述べる箇所。原文への範囲参照であり、その内容自体はr2llで構成する。'),
}
MEANINGS = {
    'r2lh': '既存r2ldの同じ全入力を保ち、r2kwの比較と条件付き判断の連言から、r2kvの比較側だけを取り出す。公衆と個人の同じ候補・期間・起点・尺度を維持する。',
    'r2li': '既存r2leと同じ非空の公衆範囲・個人範囲・公衆分類を保持し、各組についてr2lhの比較だけを述べる。比較対象を取り替えたり空範囲を許したりしない。',
    'r2lj': 'r2liを参照状況で評価する閉じた内容。第一文前半の比較的な可能性の内容で、自由の条件付き判断とは別に提示できる。',
    'r2lk': '同じ公衆と参照状況について、r2ldがr2kwへ渡していた出所・期間・起点・広がり・候補・尺度・近さ・条件付き程度を、そのままhznhへ接続する。比較個人の引数を外し、全個人に共通だった同じ条件付き判断だけを取り出す。',
    'r2ll': '非空の同じ公衆範囲の全てがr2laの分類を満たし、各公衆でr2lkの条件付きのほぼ必然が成立する内容。比較個人の範囲を条件付き判断自体へ余計に含めない。r2ljとの連言では旧r2lfと同じ非空性と主張を保つ。',
    'r2lm': '同じ公衆・参照状況で固定した出所・期間・起点対応による自由維持hznfを、候補ごとの内容として取り出す。公衆の範囲・活動の分類と、候補内の規範評価を混同しない。',
    'r2ln': '同じ公衆・参照状況で固定した期間・起点・比率基準による将来の能力変化hzngを、候補ごとの内容として取り出す。r2lmとr2lkに結ばれる同じ目標である。',
    'r2lo': '前半r2ljと後半r2llをそれぞれの本文箇所へ同じ著者・文脈で帰属する。個人の離脱の難しさr2ecと前半をh4lの自立的使用を共通観点として対比し、前半から後半への強め方を記述する。後半では同じ自由維持r2lmと変化r2lnを、ほぼ必然r2lkという限定を保ったまま足りる条件として提示する。内容の真理は実行せず、旧中核主張r2lgを保持する。',
}
LIMITS = [
    'aberは第三段落冒頭の個人の離脱の難しさと、公衆の比較的な可能性との対比として読む。先行主張の否定や、全ての通常予想の反転を余計に付けない。',
    'jaは同じ自己啓蒙の見通しについて、比較的可能という言い方から、自由の条件付きでほぼ避けがたいという言い方へ進む強め方として読む。条件付き程度が無条件の程度を数値的に上回ること、後半が前半を論理的に含意することは加えない。',
    'nurは自由を与えておけば足りるという条件の取り立てとして読む。ただし帰結はほぼ避けがたいという限定付きであり、自由があれば例外なく達成するという十分条件や、自由だけが唯一の原因という主張へ強めない。背景の文脈と別の達成経路は保持する。',
    '自由は後続の公的理性使用の説明を受けた規範的な許可として読む。同じ公的活動を許し不実行を要求しない政策を、選択した経過で維持する。現実に許可があること、権利の正当性、身体的な機会や妨害の全てまで同じ語で記述する読みではない。',
    '公衆は公的議論の宛先、一般化は指定した公衆と先行段落の個人への文脈的全称、集団の変化は固定した全読者の比率が文脈基準を超える読みを継承する。無限の公衆や例外を許す総称という別読解を同時に主張しない。',
    '本文の知的自立の達成は自己または内部の人の活動・因果と前後変化へ接続する。身体の光を照らす出来事をaufkläreに追加せず、この論説が冒頭で説明した理解力の自立という概念を用いる。',
    '三つの新しい提示関係は共通の発話行為の意味規約を持つ基本関係であり、内容や原語の文字列を返す一文専用演算子ではない。対比・強め方・限定付きの条件提示の全心理的な機構を定義展開したという結果ではない。',
    '第一文128文字・108非空白文字についてのアシスタントの意味判断であり、自動同義性証明や独立査読ではない。第四段落全体、後続の理由の内容、二作品全文の完成は別に確認する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def replace_calls(node, mapping):
    if isinstance(node, list):
        return [replace_calls(n, mapping) for n in node]
    if not isinstance(node, dict):
        return node
    result = {k: replace_calls(v, mapping) for k, v in node.items()}
    if result.get('kind') in ('call', 'function_ref') and result.get('symbol') in mapping:
        result['symbol'] = mapping[result['symbol']]
    return result


def extracted():
    old = parent()
    first = replace_calls(deepcopy(old.entries['r2ld']['declaration']), {'r2kw': 'r2kv'})
    first['name'] = 'r2lh'
    quantified = replace_calls(deepcopy(old.entries['r2le']['declaration']), {'r2ld': 'r2lh'})
    quantified['name'] = 'r2li'
    second = deepcopy(old.entries['r2ld']['declaration'])
    second['name'] = 'r2lk'
    second['parameters'] = [second['parameters'][i] for i in (0, 2)]
    combined = second['body']['arguments'][1]
    assert combined['kind'] == 'call' and combined['symbol'] == 'r2kw'
    combined.update(symbol='hznh', arguments=[combined['arguments'][i] for i in
                                            (1, 0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15)])
    return [first, quantified, second]


def definitions():
    return '''
d r2lj[] e[b reference[k r2li[v reference]]].
d r2ll[] e[b reference[w[g audience a[k h222e[v audience v reference]]][
 f audience a[y[k h222e[v audience v reference]][w[k r2la[v audience v reference]][k r2lk[v audience v reference]]]]
 ]]].
d r2lm[audience a reference d] e[b branch[
 k hznf[v audience v reference k h222f[v audience v reference] k h222g[v audience v reference]
 k h222h[v audience v reference v branch] v branch]
]].
d r2ln[audience a reference d] e[b branch[
 k hzng[v audience v reference k h222g[v audience v reference]
 k h222h[v audience v reference v branch]
 i[members h[a] c changed h[a] c][k r2lc[v audience v reference v members v changed]] v branch]
]].
d r2lo[] c[
 w[u[e[k h222t[]][k h222u[]]]][
 w[k hzon[k h222t[] k wa[] r b[k r2lj[]] k hzp3[]]][
 w[k hzon[k h222u[] k wa[] r b[k r2ll[]] k hzp3[]]][
 w[k h222q[k hzp4[] k wa[] k hzzq[] r b[k r2ec[]] k h222t[] r b[k r2lj[]] r[p h4l] k hzp3[]]][
 w[k h222r[k hzp4[] k wa[] k h222t[] r b[k r2lj[]] k h222u[] r b[k r2ll[]] r[p h4l] k hzp3[]]][
 w[k h222s[k h222u[] k wa[] r[p h222e] r b[p r2lm] r b[p r2ln] r b[p r2lk] k hzp3[]]][
 k ue[k h222t[] k h222u[] k hzp3[]]
 ]]]]]]
].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    doc['declarations'].extend(extracted())
    extra = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + extra + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2lo', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2lg', 'r2lo']), statements=[statements[55], statement])
    declarations = {d['name']: d for d in added}
    primitives = {n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                          arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()}
    basis = dict(status='public_first_sentence_under_explicit_reading',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives=primitives,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-comparison-claim-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
