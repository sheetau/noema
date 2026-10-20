"""Separate a minimum task from the expectation background of its uncertain result."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_limits import v, call as k, app, op, both, quant
from scripts.compose_origin_clock import definition
from scripts.compose_scalar_backgrounds import PAIR

PARENT = 'examples/v016/kant-unfamiliar-judgment.noema'
PARENT_BASIS = 'data/unfamiliar-judgment-basis-v1.json'
FULL = 'examples/v016/kant-minimum-challenge.noema'
CORE = 'examples/v016/minimum-challenge-core.noema'
LIBRARY = 'examples/v016/bound-expectation.noema'
BASIS = 'data/minimum-challenge-basis-v1.json'
ANNOTATIONS = 'data/minimum-challenge-identifiers-v1.json'
PREDICATE = 'i[h[a a] e]'
ORDER = 'h[a ' + PREDICATE + ' a a a a d] c'
PRIMITIVES = {
    'h222a': (['person', 'scope', 'task'], '同じ人物・提示文脈で、困難の最小性を比較する課題の範囲。仮定内の成否に応じて範囲を選び直さない。全ての可能な課題の集合とは限らない。'),
    'h222b': (['person', 'first_task', 'second_task', 'case'], '同じ人物・仮定状況において、第一課題は第二課題より難しくないという順序比較。同順位を許す。物理的な幅、成功の確率、結果への期待、課題の実行とは別の意味入力。'),
    'h222c': (['observer', 'predicate', 'left_actor', 'left_task', 'right_actor', 'right_task', 'context'], '観点主体の同じ文脈での期待において、閉じた二引数内容述語を左の人物・課題へ適用する内容が、同じ述語を右の人物・課題へ適用する内容以上に見込まれる。述語を実行せず、実在・真偽・確率値を含意しない。両方向の成立は同順位、両方の不成立は既知の比較不能。未知は偽に補わない。hzptと関連する意味規約だが、二つの記述形式の比較値が自動的に等しいとは定めない。'),
}
MEANINGS = {
    'r2hn': '指定した同じ人物・課題について、前版r2haの不確かな判断活動があるという内容。課題を引数として開き、固定課題へ適用すればr2hbと一致する。因果理由や最小性は内容へ含めない。',
    'r2ho': '同じ観点主体・人物・閉じた内容述語・文脈について、課題範囲上の期待比較が反射的かつ推移的である。比較不能を許し、全順序や確率分布を要求しない。',
    'r2hp': '同じ人物・内容述語・文脈について、第一課題での内容が第二課題での内容より厳密に見込まれにくい。逆方向の弱比較が成立し、順方向は不成立。同順位と比較不能を区別する。',
    'r2hq': '固定した課題が同じ非空範囲で最小の困難であり、厳密に難しい代替課題が少なくとも一つある。焦点とその全代替上の期待順序を検査し、同じ人物・内容述語について焦点が全ての厳密に難しい代替より見込まれにくいという背景。同じ最小順位の課題は代替に加えず、その実行も要求しない。',
    'r2hr': '提示文脈whで本人について指定した同じ課題hzzzzが、同じ固定課題範囲h222aの困難順序h222bで最小である。仮定ごとに都合のよい課題へ変更せず、同順位の複数最小を許す。',
    'r2hs': '同じ人物・仮定状況について、著者の提示する期待比較で、最小課題での不確かな判断r2hnが、厳密に難しい全代替課題での同じ内容より見込まれにくいというr2hqの背景。各人物を束縛して比較し、集団全体の別の内容への比較に置換しない。',
    'r2ht': '同じ人物・仮定状況で最小課題r2hrと、前版の不慣れから不確かな判断への因果的帰結r2hjが成立する前景。最小性を因果関係の結果記述へ加えず、不慣れが課題の難しさを生むとはしない。',
    'r2hu': '同じ人物・仮定状況でr2hsの期待背景が成立するという内容。前景の実際の不確かな判断や原因を実行しない。',
    'r2hv': '提示文脈whで固定した同じ人物・仮定集合について、依存離脱r2gtなら最小課題での理由付き帰結r2htが成立し、離脱を満たす仮定もあるという非空の条件内容。',
    'r2hw': 'r2hvと同じ人物・仮定集合・離脱の前件に、期待背景r2huを結ぶ非空の条件内容。背景をその仮定内に置く読みであり、現実の全時点へ投射しない。',
    'r2hx': '第一文から継承する同じ非空の人物範囲の全員へr2hvを適用した前景内容。',
    'r2hy': 'r2hxと同じ人物範囲の各人へr2hwを適用した背景内容。比較対象の人物を取り替えない。',
    'r2hz': '閉じた前景r2hxと背景r2hyの引用を既存rstへ渡す対。前景の否定だけで背景を否定せず、引用だけでどちらの内容も実行しない。本文への著者帰属は未接続。',
}
LIMITS = [
    '原文のauch über den schmalesten Grabenの対象側を、最小の困難でも不確かな判断になるという尺度的な読みへ構成する。物理的な幅を知的な困難と同一視する証明ではなく、比喩の対応は別途必要。原文資料の綴りは変更しない。',
    '最小性と期待は別の入力。困難の大小だけから期待の大小を推論せず、期待から実行・不確かさ・因果寄与も導かない。焦点と厳密に難しい全代替を比較する読みであり、任意に都合のよい一つの代替だけを選ばない。',
    '比較は各人・閉じた述語・明示的な課題引数を保つ。実行時の自由変数を閉じた引用に隠さず、全員についての命題を各人の命題の代用品にしない。一般の束縛付き比較の意味規約であり、個別文の翻訳規則ではない。',
    '同順位の最小課題は複数でもよい。固定した一つの課題の判断を要求し、同順位の全課題での判断は要求しない。厳密に難しい課題がなければ最小性は成立しても今回の尺度背景は成立しない。',
    '背景は離脱を満たす仮定内で評価する候補。dennochの離脱と帰結の譲歩、nurの限定、身体描写との対応、種類照応、同じ参照対象と著者帰属を含む第四文全体の統合は未完。',
    '本文54文と既存の意味規約・十二全単位および先頭三文の判断を保持する。有限検査は原文との同義性の自動証明ではなく、新しい意味確認済み分量を加えない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def additions():
    text = 'r h222a[a d a] c.r h222b[a a a d] c.r h222c[a '+PREDICATE+' a a a a d] c.\n'
    text += 'd r2hn[person a topic a] e[b point[g judgment a[k r2ha[v person v judgment v topic v point]]]].\n'
    common = 'observer a actor a predicate '+PREDICATE+' '
    tail = 'point d ranking '+ORDER
    cmp = lambda a, b: app(v('ranking'), v('observer'), v('predicate'), v('actor'), v(a), v('actor'), v(b), v('point'))
    member = lambda a: app(v('scope'), v(a))
    reflexive = quant('f', 'first', 'a', op('y', member('first'), cmp('first', 'first')))
    transitive = quant('f', 'first', 'a', quant('f', 'second', 'a', quant('f', 'third', 'a', op('y',
        both(member('first'), member('second'), member('third'), cmp('first', 'second'), cmp('second', 'third')), cmp('first', 'third')))))
    text += definition('r2ho', common+'scope h[a] c '+tail, both(reflexive, transitive))
    text += definition('r2hp', common+'first a second a '+tail, both(cmp('second', 'first'), op('u', cmp('first', 'second'))))
    harder = lambda name: both(member(name), app(v('difficulty'), v('focus'), v(name)), op('u', app(v('difficulty'), v(name), v('focus'))))
    domain = 'i[item a]['+op('x', op('e', v('item'), v('focus')), harder('item'))+']'
    text += definition('r2hq', common+'focus a scope h[a] c difficulty h[a a] c '+tail,
        both(k('rce', v('focus'), v('scope'), v('difficulty')), quant('g', 'alternative', 'a', harder('alternative')),
        k('r2ho', v('observer'), v('actor'), v('predicate'), domain, v('point'), v('ranking')),
        quant('f', 'alternative', 'a', op('y', harder('alternative'),
            k('r2hp', v('observer'), v('actor'), v('predicate'), v('focus'), v('alternative'), v('point'), v('ranking'))))))
    task = 'k hzzzz[v person k wh[]]'
    scope = 'i[task a][k h222a[v person k wh[] v task]]'
    difficulty = 'i[first a second a][k h222b[v person v first v second v point]]'
    text += definition('r2hr', 'person a point d', k('rce', task, scope, difficulty))
    text += definition('r2hs', 'person a point d', k('r2hq', 'k wa[]', v('person'), 'r[p r2hn]', task, scope, difficulty, v('point'), 'p h222c'))
    text += 'd r2ht[person a] e[b point[w[k r2hr[v person v point]][t[k r2hj[v person]][v point]]]].\n'
    text += 'd r2hu[person a] e[b point[k r2hs[v person v point]]].\n'
    for name, consequence in [('r2hv', 'r2ht'), ('r2hw', 'r2hu')]:
        cases = 'i[scene d][k hzzzy[v person v anchor v scene]]'
        text += definition(name, 'person a', 'b anchor['+both(op('e', v('anchor'), 'k wh[]'),
            k('rc', v('person'), 'p r2gt', 'p '+consequence, cases), k('re', v('person'), 'p r2gt', cases))+']', 'e')
    text += 'd r2hx[] e[k r2ef[p r2hv]].d r2hy[] e[k r2ef[p r2hw]].\n'
    text += definition('r2hz', '', 'k rst[r c[k r2hx[]] r c[k r2hy[]]]', PAIR)
    return text


def build():
    old = parent(); doc = deepcopy(old.document); statements = doc['statements']; doc['statements'] = []
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + additions()); doc['statements'] = statements
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2hz', 'rsx', 'rsy', 'rsw']), statements=[])
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['r2ho', 'r2hp', 'r2hq']), statements=[])
    added = doc['declarations'][len(old.document['declarations']):]; assert len(added) == 16
    primitives = {d['name']: dict(parameters=d['parameters'], result=d['result'],
        arguments=PRIMITIVES[d['name']][0], meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['name'] in PRIMITIVES}
    basis = dict(status='unasserted_minimum_challenge_and_bound_expectation_candidate', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS, primitives=primitives,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/unfamiliar-judgment-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact')+'\n', LIBRARY: format_graph(lib, 'compact')+'\n',
        BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Minimum challenge and bound expectation composed; 54 statements preserved', flush=True)
