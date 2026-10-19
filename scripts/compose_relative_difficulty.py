"""Bind task difficulty to the actor's reserve and the same achieving methods."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_graded_change import parameters
from scripts.compose_limits import v, call as k, app, op, both, quant, definition

PARENT = 'examples/v016/kant-unselected-continuation.noema'
PARENT_BASIS = 'data/unselected-continuation-basis-v1.json'
FULL = 'examples/v016/kant-relative-difficulty.noema'
CORE = 'examples/v016/relative-difficulty-core.noema'
BASIS = 'data/relative-difficulty-basis-v1.json'
ANNOTATIONS = 'data/relative-difficulty-identifiers-v1.json'
ORDER = [('scale', 'h[a] c'), ('less', 'h[a a] c'), ('low', 'a'), ('high', 'a'), ('band', 'h[a] c')]
METHOD = [('actor', 'a'), ('plan', 'a'), ('start', 'd'), ('limit', 'a'), ('scale', 'h[a] c'), ('less', 'h[a a] c'),
          ('required', 'h[a a d d a] c'), ('available', 'h[a a d] c'), ('outcomes', 'h[a a d d] c'),
          ('selected', 'h[a a d d] c'), ('success', 'h[a a d d] c')]
TASK = [('actor', 'a'), ('start', 'd')] + ORDER + [('capacity', 'h[a d a] c')] + METHOD[6:]
PRIMITIVES = {
    'hzzh': (['effort_agent', 'beneficiary', 'dimension', 'method', 'start', 'end', 'degree'], '同じ受益者のための同じ方法・開始・結果への経路について、指定実施者に必要な力の投入を、指定した種類と尺度の程度として評価する。数量的な仕事量や主観的な煩わしさとは限らない。実際の実行や成功は含めず、別の人の努力・別の結果を流用しない。尺度・種類・測定の妥当性は文脈で与える。'),
    'hzzi': (['actor', 'dimension', 'start', 'degree'], '本人が指定された種類の力を、この開始時点の基盤から当該活動のために投入し得る範囲の上限を、同じ尺度の程度として評価する。現在の意欲や実際の投入量、個別方法での成功、未来に訓練した別の能力とは分ける。評価欠落を最低値とみなさない。'),
}
MEANINGS = {
    'r2db': '尺度上の本人の上限に対し、追加投入不要の下端を超え上限以下の帯を取り、上限まで上方閉包であることを検査する。上限が下端より上なら帯は非空で上限を含み、上限が下端なら帯は空とする。余力が少ない帯の実質的な境界は文脈で与え、順序だけから自動発見しない。',
    'r2dc': '同じ本人・方法・開始・結果の必要量が尺度内で一意であり、本人の上限以下である。欠落や多値を低負担へ補わず、上限を超える経路を資源面で実行できる経路として数えない。',
    'r2dd': '利用可能な全方法で結果評価xaが整い、その評価結果すべてで達成する方法については全経路の必要量も一意に評価されている。明らかに達成しない方法の必要量まで要求せず、未評価の達成方法を容易な方法の不在へ変換しない。',
    'r2de': '同じ利用可能な方法の非空な評価結果すべてで、指定された達成関係と本人の上限内の必要量r2dcが成立する。別方法の成功と余力を混ぜない。現在その方法を実行したことは要求しない。',
    'r2df': 'r2deの同じ達成方法の全評価経路で、必要量が余力の少ない帯の外にある。全評価結果に余裕を確保できる方法であり、一つの安い結果だけを方法全体の容易さとしない。',
    'r2dg': '有効な同じ尺度・本人の一意な上限・上限に沿った帯の下で、余裕を確保できる同じ達成方法r2dfがある。有効な一方法があれば、他方法の必要量の評価欠落だけではこの肯定を取り消さない。',
    'r2dh': '同じ尺度と本人の上限・帯が有効で、方法評価r2ddが整い、上限内で達成する方法r2deが少なくとも一つあるが、全結果に余裕を確保できる方法r2dfはない。達成方法ごとに少なくとも一つは帯に入る経路がある。到達不能や単なる煩わしさとは分けた、達成可能だが余力の少ない困難さの構成である。',
    'r2di': '現在未成熟bfにある本人について、同じ本人の自己作業によるbfからh4lへの移行h4pを達成関係に使い、r2dhの余力の少ない困難さを組み立てる。本人を努力実施者と受益者にそろえ、同じ評価種類を必要量と上限へ渡す。結果ごとの仮定内で過程を評価し、現在の実行や完了を断言しない。',
}
LIMITS = [
    'schwerを、本人の力に対して必要な投入が大きく、余裕を確保できる達成方法がないという読みから構成する。Kant AA VII147の容易さと煩わしさの区別を参照するが、1784年の語義を一意に確定する証明ではない。',
    'r2dhは少なくとも一つの資源面で実行可能な達成方法を要求する。方法がない、未評価、資源の上限を超えることを、同じ困難さへまとめない。到達不能を含み得るschwerの他の読みと、全個人への範囲は別途検討する。',
    '結果の採用基準は文脈入力であり、全評価結果に余裕を確保できる方法があるかを調べる。失敗・高負担の結果を都合よく除いてよい規則ではない。数値確率、割合、実際の成功保証を原文へ補わない。',
    '力の種類、尺度、上限、必要量、余力の少ない帯の校正は意味上の入力である。下端は当該種類について追加投入を要しない基準として指定する。普遍的な物理単位や数値ゼロを算出したとはせず、未知と下端を分ける。上限が下端でも追加投入不要の達成方法を扱える。',
    '自己作業の一方法を一つの変化過程に対応させる既存h4pの粒度を採る。各想定結果内の履歴と過程を評価し、現在の世界ですべての代替過程が実行済みとはしない。本人の作業は必要だが他者の援助を一律には除かない。',
    '本性に近づいた性向との統合、習慣の抑制の具体的な機構、jeden einzelnen Menschen、also、人称と著者帰属は未完。既存51本文文と十二単位の判断を保持し、句全体・第一文・段落を意味確認済みとして計上しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def refs(fields):
    return [v(n) for n, _ in fields]


def definitions():
    use = lambda name, *names: app(v(name), *(v(n) for n in names))
    le = lambda a, b: op('x', op('e', v(a), v(b)), use('less', a, b))
    selected = use('selected', 'actor', 'plan', 'start', 'end')
    all_selected = lambda body: quant('f', 'end', 'd', op('y', selected, body))
    need = 'i[point d value a][c[v required][v actor v plan v start v point v value]]'
    unique = lambda amount: k('r2cl', need, v('scale'), v('end'), v(amount))
    bounded = both(use('scale', 'limit'),
        op('z', op('u', op('e', v('limit'), v('low'))), quant('g', 'amount', 'a', use('band', 'amount'))),
        quant('f', 'amount', 'a', op('y', use('band', 'amount'), both(use('scale', 'amount'), use('less', 'low', 'amount'), le('amount', 'limit')))),
        quant('f', 'amount', 'a', quant('f', 'higher', 'a', op('y',
            both(use('band', 'amount'), use('scale', 'higher'), use('less', 'amount', 'higher'), le('higher', 'limit')), use('band', 'higher')))))
    text = 'r hzzh[a a a a d d a] c.r hzzi[a a d a] c.'
    text += definition('r2db', 'scale h[a] c less h[a a] c low a limit a band h[a] c', bounded)
    path = quant('g', 'amount', 'a', both(unique('amount'), le('amount', 'limit')))
    text += definition('r2dc', 'actor a plan a start d end d limit a scale h[a] c less h[a a] c required h[a a d d a] c', path)
    valid = k('xa', v('actor'), v('plan'), v('start'), v('outcomes'), v('selected'))
    succeeds = all_selected(use('success', 'actor', 'plan', 'start', 'end'))
    assessed = both(valid, op('y', succeeds, all_selected(quant('g', 'amount', 'a', unique('amount')))))
    assessment_fields = [('actor', 'a'), ('start', 'd'), ('scale', 'h[a] c')] + METHOD[6:]
    text += definition('r2dd', parameters(assessment_fields), quant('f', 'plan', 'a', op('y',
        use('available', 'actor', 'plan', 'start'), assessed)))
    feasible = k('r2dc', *(v(n) for n in ('actor', 'plan', 'start', 'end', 'limit', 'scale', 'less', 'required')))
    text += definition('r2de', parameters(METHOD), both(use('available', 'actor', 'plan', 'start'), valid,
        all_selected(both(use('success', 'actor', 'plan', 'start', 'end'), feasible))))
    text += definition('r2df', parameters(METHOD) + ' band h[a] c', both(k('r2de', *refs(METHOD)),
        all_selected(quant('g', 'amount', 'a', both(unique('amount'), op('u', use('band', 'amount')))))))
    ceiling = 'i[point d value a][c[v capacity][v actor v point v value]]'
    setting = both(k('rqsq', *(v(n) for n in ('scale', 'less', 'low', 'high'))),
        k('r2cl', ceiling, v('scale'), v('start'), v('limit')),
        k('r2db', *(v(n) for n in ('scale', 'less', 'low', 'limit', 'band'))))
    easy = quant('g', 'plan', 'a', k('r2df', *refs(METHOD), v('band')))
    possible = quant('g', 'plan', 'a', k('r2de', *refs(METHOD)))
    text += definition('r2dg', parameters(TASK), quant('g', 'limit', 'a', both(setting, easy)))
    text += definition('r2dh', parameters(TASK), quant('g', 'limit', 'a', both(setting,
        k('r2dd', *refs(assessment_fields)), possible, op('u', easy))))
    fields = [('person', 'a'), ('dimension', 'a')] + ORDER
    bindings = dict(actor=v('person'), start=v('start'), **{n: v(n) for n, _ in ORDER},
        capacity='i[actor a point d degree a][k hzzi[v actor v dimension v point v degree]]',
        required='i[actor a plan a first d last d degree a][k hzzh[v actor v actor v dimension v plan v first v last v degree]]',
        available='p ae', outcomes='p af', selected='p ap',
        success='i[actor a plan a first d last d][k h4p[v actor v plan v first v last v last]]')
    body = both(op('t', k('bf', v('person')), v('start')), k('r2dh', *(bindings[n] for n, _ in TASK)))
    return text + 'd r2di[' + parameters(fields) + '] e[b start[' + body + ']].'


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=[])
    added = doc['declarations'][size:]; by_name = {d['name']: d for d in added}
    assert len(added) == 10
    basis = dict(status='actor_relative_difficulty_with_same_achieving_methods', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
        primitives={n: dict(parameters=by_name[n]['parameters'], result=by_name[n]['result'], arguments=args, meaning_ja=meaning)
                    for n, (args, meaning) in PRIMITIVES.items()}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/unselected-continuation-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print('Eight definitions and two general inputs composed; no new authored assertions', flush=True)
