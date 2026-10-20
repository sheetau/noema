"""Bind open restriction candidates to one context and two individual questions."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import STATE, TRUE, both
from scripts.compose_aligned_influence import CODE
from scripts.compose_enlightenment_extent import BASIS as SCALE_BASIS

PARENT = 'examples/v016/kant-demand-candidates.noema'
PARENT_BASIS = 'data/demand-candidates-basis-v1.json'
FULL = 'examples/v016/kant-restriction-questions.noema'
CORE = 'examples/v016/restriction-questions-core.noema'
BASIS = 'data/restriction-questions-basis-v1.json'
ANNOTATIONS = 'data/restriction-questions-identifiers-v1.json'
PRIMITIVES = {
    'h234t': ('[d] a', ['context'],
              '同じ比較の提示文脈で啓蒙の進行を比べる対象公衆。候補・要求の適用・結果の良否で対象公衆を変更しない。読者全体・期間・起点・広がり基準は同じ公衆と評価基準から既存定義で取り出す。参照だけで公衆分類や実際の啓蒙を肯定しない。'),
    'h234u': ('[d a] c', ['context', 'candidate'],
              '同じ比較文脈で、自由の選択肢を要求によって制限する政策・指示の事例として検討する候補の範囲。結果の良否を見て選び直さず、四つの先行事例を尽くす範囲に限定しない。候補の要求内容と比較の有効性は別に構成する。'),
    'h234v': ('[d a a] c', ['context', 'candidate', 'record'],
              '同じ文脈で指定候補を構成する全要求表の行の範囲。要求の出所・宛先・役割・行為型・内容・極性を一つの行へ保持する。効果や履行を見て行を削らず、この候補の全要求を表す。先行四事例は各固定宛先一行に照合し、他の候補では別の索引と複数行を許す。'),
    'h234w': ('[d a a] a', ['context', 'candidate', 'record'], '指定された同じ候補・要求行の出所。比較する候補世界ごとに替えない。命令の正当性や履行を意味しない。'),
    'h234x': ('[d a a] a', ['context', 'candidate', 'record'], '指定された同じ候補・要求行の宛先本人。自由選択と内容の評価もこの本人へ結ぶ。行の索引と本人は一般には異なってよい。'),
    'h234y': ('[d a a] a', ['context', 'candidate', 'record'], '指定された同じ候補・要求行で受け手が要求を受ける立場。出所の役職へ取り替えず、比較中に替えない。'),
    'h234z': ('[d a a] a', ['context', 'candidate', 'record'], '指定された同じ候補・要求行の行為型。内容記述の第二引数と同じもので、文章箇所や実行済みの出来事へ無断で置換しない。'),
    'h235a': ('[d a a] ' + CODE, ['context', 'candidate', 'record'],
              '指定された同じ候補・要求行の、本人と行為型を受ける閉じた段階1内容記述。比較中に内容を変更しない。返す記述の意味は既存または追加の合成定義で説明し、原語の文の名前だけを内容として返さない。'),
    'h235b': ('[d a a] c', ['context', 'candidate', 'record'],
              '指定された同じ候補・要求行の極性。真は内容を満たす要求、偽は内容を満たさない要求。全命令を否定と肯定の連言で表した先行四事例の正極性と、追加候補の否定形の要求を混同しない。'),
    'h235c': ('[d a a d] c', ['context', 'candidate', 'record', 'alternative'],
              '同じ文脈の指定要求行の宛先本人について、要求への適合で選別する前の自由選択候補。出所・本人・役割・行為型・内容・極性、他者と関連背景を固定し、本人の選択を変える。単に他人が違反する状況や内容自体を変更した状況ではない。先行四事例では同じh234nへ照合する。'),
    'h235d': ('[d a] j[a]', ['context', 'candidate'], '同じ比較文脈の候補に対応する介入モデルの全変数列。重複や要因の範囲は既存のモデル検査で確認する。結果に応じた変数の取り替えは行わない。'),
    'h235e': ('[d a a ' + STATE + '] c', ['context', 'candidate', 'variable', 'assignment'],
              '同じ比較文脈・候補の構造式がこの変数へ与える真偽。候補の要因を有効／無効にする介入の間で、他の式・外生条件・介入前の背景を保持する。異なる候補も同じ文脈で定めた共通背景について検討する。'),
    'h235f': ('[d a] a', ['context', 'candidate'], '同じ候補の全要求の有効／無効に対応させるモデル変数。要求の履行の真偽ではなく全要求の存在を切り替え、その対応はr2vpで検査する。'),
    'h235g': ('[d a ' + STATE + '] d', ['context', 'candidate', 'assignment'],
              '同じ文脈・候補の割当てに対応する評価経過。要求の適用と啓蒙の進行を同じ経過で評価する。公衆・期間・起点・広がり基準を効果の良否で変更しない。'),
    'h235h': ('[d a ' + STATE + ' ' + STATE + '] c', ['context', 'candidate', 'on', 'off'],
              '同じ文脈・候補で、共通の外生条件・介入前の背景・非決定的な選択枝を保って要因だけを変更した、あり側・なし側の順の対応。意味上適切な対応を全て含め、結果の良否から事後選別しない。全解に対応先があることはr2wiで検査する。'),
}
MEANINGS = {
    'r2xp': '先行四事例の候補では、要求行の範囲が既存の全宛先と一致し、各行の出所・本人・立場・行為型・閉じた内容・正極性、全状況の自由選択が同じ先行事例に一致することを検査する。四事例以外ではこの特定形式を強制せず、一般の全要求表へ渡す。',
    'r2xq': '同じ提示文脈の候補範囲が、異なる先行四事例を全て含むことをr2weで確認する。第五の候補を除外せず、効果の良否や答えの存在をこの範囲条件に含めない。',
    'r2xr': '同じ候補の要求表と先行事例の照合r2xpを、共通文脈のモデル・対応・対象公衆・h232vの基準によるr2xhへ結ぶ。追加候補も同じ全要求・自由選択・啓蒙尺度を使う。',
    'r2xs': '同じ文脈と候補の全接続を保ち、r2xiによる潜在的な阻害を分類する。別の候補や別文脈の結果を借りない。',
    'r2xt': '同じ全接続を保ち、r2xjによる非阻害を分類する。未評価や不完全な要求表から害がないとはしない。',
    'r2xu': '同じ全接続を保ち、r2xkによる非阻害かつ潜在的な促進を分類する。非阻害だけの候補を促進へ強めない。',
    'r2xv': '同じ提示文脈の範囲条件r2xqの下で、その範囲に属して阻害分類r2xsを満たす候補を問う個体回答型の質問。候補の存在・唯一性・著者の答えへの賛同を主張しない。',
    'r2xw': '同じ文脈・公衆・基準・候補範囲で、非阻害かつ促進r2xuを満たす候補を問う個体回答型の質問。第一問とは同じ比較の別分類であり、候補や目標を替えない。wohl/garの提示上の留保と強調は別途必要。',
}
LIMITS = [
    '二問の答え条件と共通入力を構成する段階。著者による問いの提示、aber/sondern、wohl/gar、後続回答への談話接続はまだ追加していない。旧70主張・意味判断を保持し、二問を意味確認済みとは数えない。',
    '新しい基本関係は比較文脈と全要求表・モデルの汎用的な入力欄である。原文の文を判定する一文専用演算子ではない。内容は段階1の合成されたNoema記述、影響は既存の要求と介入・尺度から構成する。',
    '四事例は既存の文章箇所を索引として各命令を指し、追加候補は別の政策・指示の索引でよい。候補を人物そのものや四種類だけへ限定しない。入力の行が候補の全要求を尽くすことと背景の適合は公開する意味規約であり、架空の検査表を原文の全候補列挙とはしない。',
    '同じ提示文脈を全ての入力欄へ渡し、対象公衆を候補間で共用、基準を先行文のh232vへ固定する。候補ごとにモデルの変数や要求行が異なることを許すが、公衆や期間の取り替え、対応の事後選別は許さない。',
    '阻害・非阻害・促進は、同じ背景の対応組と、同じ期間内の集団変化の広がりによる潜在性の読み。追加候補も全要求の有無と本人の自由選択を満たす必要があり、空表や不完全な解除を無害としない。',
    '四事例の照合は引用内容を実行する義務を追加せず、統治者の全記述域の有限評価拒否を保持する。未知の入力を偽として隠さない。質問の答え条件を構成しても、現実の候補が存在することや因果の実証は含意しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def scale():
    return load_catalog(ROOT, SCALE_BASIS)


def field(name, row='record'):
    return 'k ' + name + '[v context v case v ' + row + ']'


def supplied():
    return ' '.join('i[record a][' + field(n) + ']' for n in
                    ('h234v', 'h234w', 'h234x', 'h234y', 'h234z', 'h235a', 'h235b'))


def definitions():
    source = 'k h234l[v case k h232v[]]'
    audience = 'k r2uw[v case ' + source + ' k h234m[v case k h232v[]] k h232v[] v record]'
    row = both('e[' + field('h234w') + '][' + source + ']',
               'e[' + field('h234x') + '][v record]',
               'e[' + field('h234y') + '][k h234r[v case v record k h232v[]]]',
               'e[' + field('h234z') + '][k h234q[v case]]',
               'k r2wa[v case ' + field('h235a') + ']', field('h235b'),
               'f point d[z[k h235c[v context v case v record v point]]'
               '[k h234n[v case v record k h232v[] k h232v[] v point]]]')
    text = 'd r2xp[context d case a] c[y[k r2ut[v case]][' + both(
        'f record a[z[' + field('h234v') + '][' + audience + ']]',
        'f record a[y[' + field('h234v') + '][' + row + ']]') + ']].\n'
    text += 'd r2xq[context d] c[k r2we[i[case a][k h234u[v context v case]]]].\n'
    args = (supplied() + ' p h234s k h235d[v context v case] '
            'i[variable a state ' + STATE + '][k h235e[v context v case v variable v state]] '
            'k h235f[v context v case] i[state ' + STATE + '][k h235g[v context v case v state]] '
            'i[record a point d][k h235c[v context v case v record v point]] '
            'i[on ' + STATE + ' off ' + STATE + '][k h235h[v context v case v on v off]] '
            'k h234t[v context] k h232v[]')
    for name, target in zip(('r2xr', 'r2xs', 'r2xt', 'r2xu'), ('r2xh', 'r2xi', 'r2xj', 'r2xk')):
        text += 'd ' + name + '[context d case a] c[' + both(
            'k r2xp[v context v case]', 'k ' + target + '[' + args + ']') + '].\n'
    for name, classification in (('r2xv', 'r2xs'), ('r2xw', 'r2xu')):
        text += 'd ' + name + '[context d] g[a][j v[i[case a][' + both(
            'k r2xq[v context]', 'k h234u[v context v case]',
            'k ' + classification + '[v context v case]') + ']]].\n'
    return text


def build():
    old, prior = parent(), scale()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    imported = {}
    for d in prior.document['declarations']:
        n = d['name']
        if n in old.entries:
            assert old.entries[n]['declaration'] == d
            assert old.entries[n]['meaning_ja'] == prior.entries[n]['meaning_ja']
        else:
            doc['declarations'].append(deepcopy(d))
            imported[n] = prior.entries[n]['meaning_ja']
    assert not (set(PRIMITIVES) | set(MEANINGS)) & (set(old.entries) | set(imported))
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + data[0] + '.' for n, data in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=[])
    decls = {d['name']: d for d in added}
    basis = dict(status='partial_open_restriction_questions_same_context', document=FULL,
                 parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=data[1], meaning_ja=data[2]) for n, data in PRIMITIVES.items()},
                 definitions=imported | MEANINGS,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 imported_scale=SCALE_BASIS,
                 import_source_sha256=dict(prior.source_sha256), limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/demand-candidates-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda data: json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
