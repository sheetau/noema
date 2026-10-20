"""Join the answer's contents, contrast, concessive qualification and self-presentation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import ARGS, both
from scripts.compose_aligned_influence import FIELDS
from scripts.compose_private_choice_frequency import MARGS
from scripts.compose_qualified_private_influence import BOUND, PARGS
from scripts.compose_private_policy_permission import bound_args

PARENT = 'examples/v016/kant-private-policy-permission.noema'
PARENT_BASIS = 'data/private-policy-permission-basis-v1.json'
FULL = 'examples/v016/kant-answer-discourse.noema'
CORE = 'examples/v016/answer-discourse-core.noema'
BASIS = 'data/answer-discourse-basis-v1.json'
ANNOTATIONS = 'data/answer-discourse-identifiers-v1.json'
FAMILY = 'i c[h[a a a a] e]'
PRIMITIVES = {
    'h236k': ('[a a a i d[e] a i d[e] i[h[a] e] d] c',
              ['node', 'presenter', 'first_node', 'first_content', 'second_node', 'second_content', 'dimension', 'context'],
              '提示者が同じ箇所・文脈で、二箇所に対応する閉じた段階3の内容を、指定の共通観点についてこの順で対照的に提示する。h222qと同じ対照を高い記述段階で扱い、条件・様相・留保を保持する。前者の撤回、二内容の矛盾、実際の真理、単なる本文順序を対照の意味へ代えない。'),
    'h236l': ('[a a i d[e] i[h[a a a a] c] ' + FAMILY + ' ' + FAMILY + ' ' + FAMILY + ' d] c',
              ['node', 'presenter', 'outer_content', 'domain', 'premise', 'retained', 'qualified', 'context'],
              '提示者が指定箇所・文脈の外側内容の中で、同じ範囲・同じ順の四個体引数に適用する第一内容を認めても、それによって第二内容を退ける帰結にはならないとして、第二を保った第三の合成内容を提示する。第一を契機とする反対の見通しを退ける譲歩的な留保であり、第一の否定ではない。外側の許可・条件等の作用域を保ち、第一や第二を現実の真理として実行しない。因果の具体的な意味、第一と第二を含む第三の構成、範囲の参照は渡す記述で別に示す。伝記的な内心、数値確率、読者全員の実際の期待は補わない。'),
    'h236m': ('[a a a a i d[e] d] c',
              ['intro_node', 'presenter', 'question_node', 'response_node', 'response_content', 'context'],
              '提示者が導入箇所で自分を現在の回答者として明示し、指定した問いへの自分の回答として、指定箇所と閉じた段階3の内容を提示する。単に他者が回答者を帰属することや、仮定例の一人称とは区別する。回答の真理・十分性、実在する対話相手、歴史的な口頭発話を含意しない。'),
    'h236n': ('[] a', [], '固定原文kant-1784:u0012の[690,704)、Ich antworte:という自己回答の導入箇所。回答全体h235pに含まれ、公的使用側の最初の節h235sへ続く。'),
}
MEANINGS = {
    'r2z7': 'r2yyと同じ全引数から、同じ本人・職務・要求表・選択肢による強い制限の頻度r2ysだけを内容として取り出す。程度や頻度の基準、候補から取り出す各時点の値を替えない。',
    'r2za': 'r2yyと同じ全引数から、期間枠の一致、方針の適用と全解除の介入対応r2yv、同じ啓蒙への許容低下r2yuを内容として取り出す。第一の制限から生じる効果を比較する同じモデル・全対応組を保ち、無関係な悪化の不在で代用しない。r2z7との連言は元のr2yyと同じ条件である。',
    'r2zb': '私的使用の節と同じr2yzの全参照をr2z7へ渡し、談話上取り上げる強い制限の頻度の内容族とする。公衆・本人・職務・案の順を保持する。',
    'r2zc': '同じr2yzの全参照をr2zaへ渡し、同じ制限が同じ啓蒙を特に妨げないという留保の内容族とする。別の案や文脈の効果を借りず、許可の外側へ現実の無害性を取り出さない。',
    'r2zd': '第五段落の固定基準で、対象公衆h222e、全本人職務h236h、結果から選別しない案h235vの同じ四引数範囲。方針の良否や実施で案を除かない。実際の適合案の存在はこの範囲関係だけから導かない。',
    'r2ze': '公的使用の自由要求r2yhと唯一の実現経路r2ymを同じ評価点の連言にし、回答前半の内容として保持する。undを理由や条件へ変えず、実際の自由や啓蒙達成へ強めない。',
    'r2zf': '回答前半r2zeと私的使用の許可r2z5の同じ評価点の連言。全回答の閉じた段階3の内容として用い、許可対象の存在量化や程度・頻度・許容低下の作用域を変えない。',
    'r2zg': '同じ固定基準で本人が人であり本人の理性を使う活動caがあるという性質。公的使用と私的使用の規範上の扱いを、本人の理性使用という共通観点で対照するための内容記述であり、実際の使用実行を要求しない。',
    'r2zh': '同じ著者wa・第五段落の提示h232o・回答箇所h235pに全内容r2zfを帰属する。二問の同じ回答としての自己提示とhzcsを保ち、公的自由の要求と私的使用への許可を共通観点で対照する。私的使用側は同じ四引数・同じr2yzの中で強い制限r2zbと因果的留保r2zcを結ぶ。回答内の三節と導入の異なる箇所と順序を保持する。',
}
LIMITS = [
    'Ich antworteを著者自身による現在の論述上の回答の自己提示と読む。先行二問に同じ全回答を結び、口頭対話の史実や回答の十分性を補わない。直前のダッシュは問いから回答への区切りとして保持する。',
    '公的使用の自由は全関連時機への規範的要求、der allein kannは公的使用の生産的な関与を欠く啓蒙実現経路がないという先行の読みを継承する。公的使用一つだけで十分、全人類が既に啓蒙、私的使用は理性使用ではない、とはしない。',
    'aberは本人の理性使用の扱いについて、公的自由の要求と、私的制限を含む方針への許可を対照する。前半の要求を撤回せず、論理的矛盾とも扱わない。undは前半の二内容の連言として保持し、原文にない理由関係へ強めない。',
    'ohne doch darumは、同じ強い私的制限から同じ啓蒙への著しい阻害を帰結させないという譲歩的留保として読む。darumの因果的な参照をr2yv/r2yuの同じ方針の適用対全解除に結び、単なる時点の共存に置換しない。dochを読者の実際の信念や数値的な期待差へ変換しない。',
    '私的使用の程度・頻度・許容低下、固定された候補・全要求表・期間・選択と機会の重み、全対応組による比較は先行定義を継承する。有限の正の有理数重みと一過程の能力変化の広がりによる操作的な読みであり、無限の連続測度、速度、質的深さも同時に記述したとはしない。',
    '制限方針の存在と因果的留保を許可対象の内側に置く先行の作用域を保つ。著者が許可を述べたことから実際の許可や方針の実施を、許可から内容の真理を導かない。引用時の全記述域の有限評価拒否も弱めない。',
    '固定原文の回答文[690,980)の250非空白文字を、原刊484〜485頁とAA8/37で照合し、明示した解釈の下で通読する。これはアシスタントの意味判断であり独立査読や自動同義性証明ではない。第五段落全体・二作品全文の完成とは区別する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    policy = ('b branch[k r2ys[' + MARGS + ' v frame i[point d][c[v degrees][v branch v point]] '
              'v degreecriterion c[v points][v branch] i[point d][c[v timeweight][v branch v point]] '
              'c[v frequencies][v branch] v frequencycriterion v branch]]')
    released = 'k r2yx[' + FIELDS + ' v required v frame]'
    text = 'd r2z7[' + BOUND + '] e[' + policy + '].\n'
    text += 'd r2za[' + BOUND + '] e[b evaluation[' + both(
        'e[v frame][k h222g[v public v reference]]',
        'k r2yv[' + policy + ' ' + released + ' ' + ARGS + ' v worlds]',
        'k r2yu[' + PARGS + ']') + ']].\n'
    for name, target in (('r2zb', 'r2z7'), ('r2zc', 'r2za')):
        text += 'd ' + name + '[public a person a role a case a] e[k ' + target + '[' + bound_args() + ']].\n'
    text += 'd r2zd[public a person a role a case a] c[' + both(
        'k h222e[v public k h232v[]]', 'k h236h[v public k h232v[] v person v role]',
        'k h235v[v public v person v role k h232v[] v case]') + '].\n'
    text += '''
d r2ze[] e[b evaluation[w[t[k r2yh[]][v evaluation]][t[k r2ym[]][v evaluation]]]].
d r2zf[] e[b evaluation[w[t[k r2ze[]][v evaluation]][t[k r2z5[]][v evaluation]]]].
d r2zg[person a] e[b evaluation[w[k aa[v person]][g activity a[k ca[v person v activity k h232v[]]]]]].
'''
    ctx, author = 'k h232o[]', 'k wa[]'
    answer, intro, first, middle, last = ('k ' + n + '[]' for n in ('h235p', 'h236n', 'h235s', 'h235t', 'h236j'))
    parts = [
        'k h236i[' + answer + ' ' + author + ' r d[k r2zf[]] ' + ctx + ']',
        'k h236k[' + answer + ' ' + author + ' ' + first + ' r d[k r2yh[]] ' + last +
        ' r d[k r2z5[]] r[p r2zg] ' + ctx + ']',
        'k h236l[' + last + ' ' + author + ' r d[k r2z5[]] r[p r2zd] r c[p r2zb] r c[p r2zc] r c[p r2yz] ' + ctx + ']',
        'u[e[' + intro + '][' + answer + ']]',
        'k ue[' + intro + ' ' + first + ' ' + ctx + ']',
        'k ue[' + first + ' ' + middle + ' ' + ctx + ']',
        'k ue[' + middle + ' ' + last + ' ' + ctx + ']',
    ]
    for question in ('h235n', 'h235o'):
        node = 'k ' + question + '[]'
        parts += ['k h236m[' + intro + ' ' + author + ' ' + node + ' ' + answer + ' r d[k r2zf[]] ' + ctx + ']',
                  'k hzcs[' + author + ' ' + node + ' ' + answer + ' ' + ctx + ']',
                  'k ue[' + node + ' ' + intro + ' ' + ctx + ']']
    nodes = (intro, first, middle, last, answer)
    parts += ['u[e[' + left + '][' + right + ']]'
              for i, left in enumerate(nodes) for right in nodes[i + 1:]]
    text += 'd r2zh[] c[' + both(*parts) + '].\n'
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r2zh', arguments=[]))
    doc['statements'] = statements + [new]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=[new])
    decls = {d['name']: d for d in added}
    basis = dict(status='answer_sentence_under_explicit_reading', document=FULL,
                 parent=PARENT, inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/private-policy-permission-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
