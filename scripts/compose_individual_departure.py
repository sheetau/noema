"""Compose a scoped, attributed first-sentence candidate from existing contents."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_limits import v, call as k, app, op, both, quant, definition

PARENT = 'examples/v016/kant-relative-difficulty.noema'
PARENT_BASIS = 'data/relative-difficulty-basis-v1.json'
FULL = 'examples/v016/kant-individual-departure.noema'
CORE = 'examples/v016/individual-departure-core.noema'
BASIS = 'data/individual-departure-basis-v1.json'
ANNOTATIONS = 'data/individual-departure-identifiers-v1.json'
PRIMITIVES = {
    'hzzj': (['dimension', 'context'], '指定した評価種類と基準文脈で用いる質的程度の有限列。低い順に並べる。単位間の等間隔、数値確率、観測頻度は含まない。重複・順序・両端は利用側で検査し、評価する内容の真偽に合わせて列を選び直さない。'),
    'hzzk': (['dimension', 'degree', 'context'], 'この評価種類と基準文脈で、上端の手前の近接域に指定程度が入る。尺度や値の実測は含まない。近接域の順序条件はrqssで別に検査し、対象を近いものにするため閾値を変更しない。'),
    'hzzl': (['dimension', 'person', 'description', 'reference', 'anchor', 'point', 'degree'], '指定種類・本人・性質記述・比較対象・基準を固定した履歴点での程度評価。生の評価入力であり、欠落と複数値を保持する。値の一意性と比較事例の両端条件は利用側で検査する。'),
    'hzzm': (['dimension', 'person', 'degree', 'context'], 'この種類・本人・開始文脈で、指定程度の投入が本人の上限に近く余力の少ない帯に入る。上限と帯の順序整合はr2dbで別に検査する。達成方法を見て帯を変更したり、他人の帯を流用しない。'),
    'hzzn': (['node', 'person', 'context'], '同じ談話箇所と基準文脈で、人物への一般的主張が対象とする範囲。述べる性質を満たす人だけに事後的に絞らない。人であること、範囲の非空性、全員についての内容は利用側で別に要求する。'),
    'hzzo': ([], '経験で形成された内的構成が、外的な維持の更新やその都度の選び直しなしに未成熟へ寄与することを比べる評価種類。出自が生得的かどうかの尺度ではない。'),
    'hzzp': ([], '自分の理解力を独立に使う状態への自己作業に必要な力と、本人が投入できる力を同じ基準で比べる評価種類。本人の性向の定着度とは別の尺度である。'),
    'hzzq': ([], '第三段落の、個々人による未成熟からの離脱の困難さを述べる第一文の談話箇所。主張の真理や内容そのものを表す記号ではない。'),
}
MEANINGS = {
    'r2dj': '有限列を左から畳み込み、第一対象を既に見た後で第二対象が現れることを検査する。同じ位置は前後関係を満たさない。重複列では自己先行が生じ得るため、尺度としては別のrtで重複を拒む。',
    'r2dp': '非空の有限列の先頭個体を返す。空列なら明示した代替個体を返す全域的な列操作であり、尺度の有効性や欠測値の補完ではない。尺度として使う側は所属と有界順序を検査する。',
    'r2dq': '非空の有限列の末尾個体を返す。空列なら明示した代替個体を返す。尺度が空のときも未知の程度を捏造せず、利用側の所属検査を通らない値として扱う。',
    'r2dk': '固定した性向尺度の列から所属と順序を構成し、同じ本人に属するある内的構成についてr2daを評価する。近接域と生の測定は同じ評価種類・基準へ結ぶ。両端はr2da内のrqsqで拘束し、値を任意に選んで近いことを作らない。',
    'r2dl': '同じ基準の力の尺度から所属と順序を構成し、同じ本人に対するr2diを評価する。帯は同じ種類・本人・基準へ結ぶ。性向尺度と力の尺度を混ぜず、現在の未成熟から自己作業で達成可能だが余力の少ない読みを採る。',
    'r2dm': '当該箇所・基準の対象範囲が非空で全員が人であることを要求し、各本人にr2dkとr2dlの両方を結ぶ。別人の性向と別人の困難さを合成しない。対象は各人であり集団の同時達成ではなく、他者の援助の一律禁止も補わない。',
    'r2dn': 'alsoの根拠側として採用する先行する原因説明、便宜さ、代行例、支払い、後見人の働きかけ、例による萎縮の六談話箇所の集合。直前の学習見込みだけを根拠とする読みには固定しない。',
    'r2do': '第一文の同じ内容r2dmを同じ著者waと談話箇所へucで帰属し、先行する根拠箇所からの帰結としてudで提示し、全根拠箇所が先行するueを結ぶ。引用された世界内容は評価せず、論理的含意や著者の正しさを断言しない。',
}
LIMITS = [
    '第三段落第一文の通した記述候補を本文へ一文追加する。機械検査だけでドイツ語との意味一致を認定しない。十二単位の既存レビューを保ち、この一文も段落全体も意味確認済みに加算しない。',
    'jeden einzelnen Menschenは文脈上の対象者それぞれへの分配的全称として読む。全時代の全人類への無制限な全称や、援助を完全に排した孤立条件とはしない。対象範囲は結論から選ばず、先行文のdjや段落末の成功者計数範囲h4iへ同一視しない。',
    'alsoは先行する未成熟の維持の説明全体を受けるという読みを採る。六箇所の選択は談話解釈であり、著者が明示的に列挙した前提や論理的な演繹の証明ではない。',
    '性向を本人に結ぶ現在の内的寄与と形成を副詞的・形容的説明の内容として併記する。前提性や情報構造を完全には分析していない。後続Er/sieの照応は今回の一文へ含めない。',
    'schwerは達成可能だが余力が少ない既存r2diを採る。到達不能を含む読みとの比較、および全称主張の下で全員の到達可能性まで含めることの妥当性は、通し読解で解消すべき具体的な未決事項である。',
    '本性に近いことは、経験から形成された内的寄与が、外的更新や毎回の決定なしに保たれるr2daで具体化する。強制性・停止能力の欠如を含めるかと程度校正の根拠は未決であり、原語の全語義を尽くしたとはしない。',
    '尺度列・近接域・帯・測定は意味の文脈入力である。世界の実測値を本文から生成する機能ではない。未知なら内容評価を保留し、引用による著者帰属とは区別する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = '''r hzzj[a d] j[a].r hzzk[a a d] c.r hzzl[a a i[h[a] e] a d d a] c.
r hzzm[a a a d] c.r hzzn[a a d] c.r hzzo[] a.r hzzp[] a.r hzzq[] a.'''
    yes = 'e[n p a b][n p a b]'; no = 'u[' + yes + ']'
    seen = 'a[v state][n p a b][' + yes + ']'
    ordered = 'a[v state][n p b b][' + yes + ']'
    step = 'i[state j[c] item a][l[c][' + op('x', seen, op('e', v('item'), v('first'))) + ' ' + op('x', ordered, both(seen, op('e', v('item'), v('last')))) + ']]'
    fold = 'q[v levels][l[c][' + no + ' ' + no + ']][' + step + ']'
    text += definition('r2dj', 'levels j[a] first a last a', 'a[' + fold + '][n p b b][' + yes + ']')
    text += 'd r2dp[levels j[a] fallback a] a[c[q[v levels][i[value a][v value]][i[previous h[a] a item a][i[value a][c[v previous][v item]]]]][v fallback]].'
    text += 'd r2dq[levels j[a] fallback a] a[q[v levels][v fallback][i[previous a item a][v item]]].'
    for name, dimension, nature in [('r2dk', 'hzzo', True), ('r2dl', 'hzzp', False)]:
        levels = k('hzzj', k(dimension), v('anchor'))
        scale = 'i[value a][' + k('hg', levels, v('value')) + ']'
        less = 'i[first a last a][' + k('r2dj', levels, v('first'), v('last')) + ']'
        if nature:
            near = 'i[value a][' + k('hzzk', k(dimension), v('value'), v('anchor')) + ']'
            measured = 'i[actor a description i[h[a] e] reference a basis d point d degree a][' + k('hzzl', k(dimension), *(v(n) for n in ('actor', 'description', 'reference', 'basis', 'point', 'degree'))) + ']'
            body = k('r2da', v('person'), v('pattern'), scale, less, near, k('r2dp', levels, k(dimension)), k('r2dq', levels, k(dimension)), measured)
        else:
            band = 'i[value a][' + k('hzzm', k(dimension), v('person'), v('value'), v('anchor')) + ']'
            body = k('r2di', v('person'), k(dimension), scale, less, k('r2dp', levels, k(dimension)), k('r2dq', levels, k(dimension)), band)
        body = op('t', body, v('anchor'))
        if nature: body = quant('g', 'pattern', 'a', body)
        body = both(k('rt', levels), body)
        text += 'd ' + name + '[person a] e[b anchor[' + body + ']].'
    scope = k('hzzn', k('hzzq'), v('person'), v('anchor'))
    body = both(quant('g', 'person', 'a', scope), quant('f', 'person', 'a', op('y', scope, both(
        k('aa', v('person')), op('t', k('r2dk', v('person')), v('anchor')), op('t', k('r2dl', v('person')), v('anchor'))))))
    text += 'd r2dm[] e[b anchor[' + body + ']].'
    premises = 'l[a][' + ' '.join(k(n) for n in ('mw', 'uo', 's3', 't4', 'hzsq', 'g2')) + ']'
    text += definition('r2dn', 'node a', k('hg', premises, v('node')))
    body = both(k('uc', k('hzzq'), k('wa'), 'r[k r2dm[]]', v('anchor')),
        k('ud', k('wa'), 'p r2dn', k('hzzq'), v('anchor')),
        quant('f', 'node', 'a', op('y', k('r2dn', v('node')), k('ue', v('node'), k('hzzq'), v('anchor')))))
    return text + 'd r2do[] e[b anchor[' + body + ']].'


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions() + 's[t[k r2do[]][k wh[]]].')
    doc['statements'] = statements + doc['statements']; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS) + ['wh']), statements=[doc['statements'][-1]])
    added = doc['declarations'][size:]; by_name = {d['name']: d for d in added}
    assert len(added) == 16 and len(doc['statements']) == 52
    basis = dict(status='scoped_attributed_first_sentence_candidate', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={n: dict(parameters=by_name[n]['parameters'], result=by_name[n]['result'], arguments=args, meaning_ja=meaning)
                    for n, (args, meaning) in PRIMITIVES.items()}, definitions=MEANINGS,
        new_signatures={d['name']: {key: d[key] for key in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/relative-difficulty-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Eight definitions, eight context inputs and one attributed sentence candidate composed', flush=True)
