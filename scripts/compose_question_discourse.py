"""Attribute the two restriction questions with contrast, conjecture and focus."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both

PARENT = 'examples/v016/kant-restriction-questions.noema'
PARENT_BASIS = 'data/restriction-questions-basis-v1.json'
FULL = 'examples/v016/kant-question-discourse.noema'
CORE = 'examples/v016/question-discourse-core.noema'
BASIS = 'data/question-discourse-basis-v1.json'
ANNOTATIONS = 'data/question-discourse-identifiers-v1.json'
QUESTION = 'i c[g[a]]'
PROPERTY = 'i c[h[a] e]'
PRIMITIVES = {
    'h235i': ('[a a ' + QUESTION + ' d] c', ['node', 'author', 'question', 'context'],
              '著者が指定箇所・文脈に、段階2の閉じた記述で指定された個体回答型の問いを提示する。修辞的な問いや自ら後で答える問いも含み、現実の聞き手への要求、回答の存在・唯一性、答えへの賛同や真理を含意しない。hzibの帰属と関連するが、質問の回答型と記述段階を保持して別型とする。引用時に質問を実行しない。'),
    'h235j': ('[a a a i b[e] ' + QUESTION + ' d] c',
              ['node', 'author', 'antecedent_node', 'antecedent_content', 'question', 'context'],
              '著者が同じ文脈で先行箇所の叙述内容を受けながら、この箇所ではその事例について区別すべき点を指定の問いとして対照的に提出する。先行内容を撤回・否定せず、単なる話題の順接とも区別する。先行内容の真理や問いの答えは実行・肯定しない。'),
    'h235k': ('[a a ' + PROPERTY + ' ' + PROPERTY + ' ' + QUESTION + ' d] c',
              ['node', 'author', 'rejected_property', 'replacement_property', 'question', 'context'],
              '同じ問いで求める対象について、指定された第一の性質を否定側に置き、第二の性質をそれに代わる肯定側として対照的に提示する。二つの性質は同じ未知の回答対象にかかり、別の対象の性質を混ぜない。問いの中の訂正・対置であって、第一問自体の撤回や第二の性質の実際の成立は含意しない。'),
    'h235l': ('[a a ' + PROPERTY + ' ' + QUESTION + ' d] c',
              ['node', 'author', 'focus_property', 'question', 'context'],
              '著者が同じ問いの求める対象に指定の焦点性質が当てはまる見込みを、推量を伴う暫定的な提案として提示する。問いの内容を確定した答えとして断言せず、数値確率・客観的な証拠水準・伝記的な内心は付加しない。焦点以外の内容全体を不確定にしたことにもせず、回答対象の存在を主張しない。'),
    'h235m': ('[a a ' + PROPERTY + ' ' + PROPERTY + ' ' + QUESTION + ' d] c',
              ['node', 'author', 'baseline_property', 'focus_property', 'question', 'context'],
              '著者が同じ問いの中で、第二の焦点性質を第一の性質にとどまることを越えたものとして取り立て、強調する。共通対象と問いを保ち、第一の否定や撤回、数値的な程度差、焦点がより高い確率を持つことは要求しない。推量等の別に記述した留保を消さず、実際の成立も断言しない。'),
    'h235n': ('[] a', [], '第五段落u0012の第一問[582,638)の箇所。どの制限が啓蒙を妨げるかを問う内容はr2yaで構成する。'),
    'h235o': ('[] a', [], '同第二問[639,687)の箇所。省略された制限・啓蒙・述語を先行問と共有し、非阻害と促進を問う内容はr2ybで構成する。'),
    'h235p': ('[] a', [], '同じ第五段落でIch antworteから始まる次の回答文[690,980)の箇所。ここでは二問への回答としての談話上の参照先であり、この回答文の全内容を確認済みとする記号ではない。'),
}
MEANINGS = {
    'r2xx': '第五段落の提示文脈h232oで固定した、同じ候補の阻害分類r2xsを内容化する。質問中の性質記述に使い、任意の評価点へ移して公衆・基準・モデルを取り替えない。',
    'r2xy': '同じ文脈の同じ候補の非阻害r2xtを内容化する。既知の無効・未評価と、悪化がないことを混同しない。',
    'r2xz': '同じ文脈の同じ候補の非阻害かつ促進r2xuを内容化する。第二問の肯定側と推量・強調の焦点を同じ性質に結ぶ。',
    'r2ya': '第一問r2xvを第五段落の同じ提示文脈h232oへ適用した閉じた質問。本文のどの制限という範囲と、同じ啓蒙の目標・公衆・基準を保持する。',
    'r2yb': '第二問r2xwを同じh232oへ適用した閉じた質問。省略された制限と阻害、ihrが指す啓蒙を第一問と同じ入力から構成し、答えの存在は主張しない。',
    'r2yc': '第一問を著者waへ段階2の記述で帰属し、直前の至るところ制限があるという叙述r2uzから、どの制限が妨げるかの区別へ対照的に移る。先行文からの順序と、後続の同じ回答文への関係を保つ。叙述の撤回や質問内容の実行を加えない。',
    'r2yd': '第二問を同じ著者・文脈へ帰属する。同じ対象の阻害を否定側、非阻害かつ促進を肯定側へ置き、促進側に推量の留保と、単なる非阻害を越える強調を付ける。第一問、第二問、後続回答の異なる箇所と順序を保ち、両問を同じ回答文へつなぐ。',
}
LIMITS = [
    '二問[582,638)・[639,687)を、直前の四事例を含む開いた制限候補範囲について、同じ啓蒙への効果を問うものとして読む。原文は答えの存在・唯一性や全ての制限の阻害を断言しない。',
    '阻害は同じ背景の対応組で進行が悪くなりうること、非阻害は全対応組で悪化なし、促進はそれに加えて改善しうることという先行の潜在性の読み。進行は同じ有限の全読者・期間・能力変化を用いる集団変化の広がり。平均効果・期間内の速度・個人の質的深さという別読解は同時に主張しない。',
    'aberは制限の存在を受けつつその効果を問い分ける対照、sondernは同じ回答対象の阻害を否定側、促進を肯定側へ置く対置として読む。先行叙述や第一問の撤回ではない。',
    'wohlは促進の見込みを問いの中で推量的に提出する留保、garは単なる非阻害を越える促進を取り立てる強調として読む。辞書は可能な用法を支えるが、この箇所の解釈を一意に証明するものではない。問いの内容に数値確率や確定した答えを補わない。',
    '質問の答え条件は同じ候補の非阻害と促進を問う。wohl/garはその促進側の提示態度として別に保持するので、現実の促進を著者の断言へ強めず、非阻害の内容を削除もしない。',
    '段階2の質問記述は引用時に実行しない。統治者の要求内容r2udの全記述域に対する有限評価拒否は保持し、有限の局所例を全域の自動同義性証明とはしない。',
    '後続の回答文への本文順序とhzcsの回答関係を構成する。回答文の公的使用・私的使用の全内容は次の作業であり、今回の二問の判断にその文章の文字数を加算しない。',
    '二問92非空白文字について明示した解釈の下で行うアシスタントの通読判断であり、独立査読ではない。第五段落全体と二作品全文の完成は別に確認する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = ''
    for name, classification in (('r2xx', 'r2xs'), ('r2xy', 'r2xt'), ('r2xz', 'r2xu')):
        text += 'd ' + name + '[case a] e[b point[k ' + classification + '[k h232o[] v case]]].\n'
    text += 'd r2ya[] g[a][k r2xv[k h232o[]]].\nd r2yb[] g[a][k r2xw[k h232o[]]].\n'
    ctx, author = 'k h232o[]', 'k wa[]'
    first, second, response, previous = ('k ' + n + '[]' for n in ('h235n', 'h235o', 'h235p', 'h234o'))
    qa, qb = 'r c[k r2ya[]]', 'r c[k r2yb[]]'
    loss, nonloss, gain = ('r c[p ' + n + ']' for n in ('r2xx', 'r2xy', 'r2xz'))
    text += 'd r2yc[] c[' + both(
        'u[e[' + first + '][' + previous + ']]',
        'k h235i[' + first + ' ' + author + ' ' + qa + ' ' + ctx + ']',
        'k h235j[' + first + ' ' + author + ' ' + previous + ' r b[k r2uz[]] ' + qa + ' ' + ctx + ']',
        'k ue[' + previous + ' ' + first + ' ' + ctx + ']',
        'k hzcs[' + author + ' ' + first + ' ' + response + ' ' + ctx + ']') + '].\n'
    text += 'd r2yd[] c[' + both(
        'u[e[' + first + '][' + second + ']]', 'u[e[' + first + '][' + response + ']]',
        'u[e[' + second + '][' + response + ']]',
        'k h235i[' + second + ' ' + author + ' ' + qb + ' ' + ctx + ']',
        'k h235k[' + second + ' ' + author + ' ' + loss + ' ' + gain + ' ' + qb + ' ' + ctx + ']',
        'k h235l[' + second + ' ' + author + ' ' + gain + ' ' + qb + ' ' + ctx + ']',
        'k h235m[' + second + ' ' + author + ' ' + nonloss + ' ' + gain + ' ' + qb + ' ' + ctx + ']',
        'k ue[' + first + ' ' + second + ' ' + ctx + ']',
        'k ue[' + second + ' ' + response + ' ' + ctx + ']',
        'k hzcs[' + author + ' ' + second + ' ' + response + ' ' + ctx + ']') + '].\n'
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = [dict(kind='assert', body=dict(kind='call', symbol=n, arguments=[])) for n in ('r2yc', 'r2yd')]
    doc['statements'] = statements + new
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2yc', 'r2yd']), statements=new)
    decls = {d['name']: d for d in added}
    basis = dict(status='restriction_question_pair_under_explicit_reading', document=FULL,
                 parent=PARENT, inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/restriction-questions-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
