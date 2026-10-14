"""Connect variable cohorts to modal revision results and undertaking policies."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_parameterized_goals import CASE, SOURCE as UNDERTAKING
from scripts.compose_necessary_futures import SOURCE as FUTURE

PARENT = 'examples/v014/kant-parameterized-goals.noema'
FIVE = 'h[a a a a a] e'
POLICY = 'h[j[a]] e'
MODAL = [(n, t) for n, t in FUTURE if n not in ('holder', 'later', 'condition')] + [('conditions', FIVE)]
# Only these fields varied by agreement lacked an agreement argument previously.
PER_AGREEMENT = {'terms', 'parties', 'arguments', 'proponents', 'authority', 'formula'}
CONFIG = [(n, 'h[a] ' + t if n in PER_AGREEMENT else t)
    for n, t in UNDERTAKING if n not in dict(CASE) and n != 'context']
ROOTS = ['rj3', 'hzdu', 'hzdv', 'hzdw', 'hzdx', 'hzdr', 'hzds', 'hzdt', 'rin']


def definitions():
    slots = [('one', 'a'), ('two', 'a'), ('three', 'a'), ('four', 'a'), ('five', 'a')]
    # After k <= 5 updates, state(a1,...,a5) = target(x1,...,xk,a1,...,a(5-k)).
    shifted = 'i[' + params(slots) + '][' + app(v('state'), v('item'), *args(slots[:4])) + ']'
    step = 'i[state ' + FIVE + ' item a][' + shifted + ']'
    folded = 'q[v bindings][v target][' + step + ']'
    result = op('t', app(folded, *([v('seed')] * 5)), v('context'))
    body = both(k('rdr', v('bindings'), 'n p f b'), quant('g', 'seed', 'a', result))
    text = definition('rj3', 'target ' + FIVE, 'i[bindings j[a]][b context[' + body + ']]', POLICY)
    for name, target in (('hzdu', 'hzdh'), ('hzdv', 'hzdi'), ('hzdw', 'hzdj')):
        content = k(target, *args(FUTURE, holder=v('nextgroup'), later=v('later'),
            condition=app(v('conditions'), *args(CASE))))
        text += definition(name, params(MODAL), k('rj3', 'i[' + params(CASE) + '][' + content + ']'), POLICY)
    replacements = {n: app(v(n), v('agreement')) for n in PER_AGREEMENT}
    content = 'b context[' + k('hzdq', *args(UNDERTAKING, **replacements)) + ']'
    text += definition('hzdx', params(CONFIG), k('rj3', 'i[' + params(CASE) + '][' + content + ']'), POLICY)
    return text


MEANINGS = {
    'rj3': '五個体から内容への関数を、同順の五個体列から内容への関数にする。既存の順次集計で関数の先頭引数を順に固定し、長さ五だけを受理する。重複を消さず、先頭と末尾を逆転させない。五回固定後の残りの仮引数は結果に影響しない。',
    'hzdu': '五個体列の後続集団をhzdhの知識主体、後続時代をその将来範囲へ接続する。前件も同じ五個体で指定する。指定候補の非空性と前件の適用例を持つ、各候補での将来的な情報拡大不能・誤り減少不能の内容。',
    'hzdv': 'hzduと同じ対象束縛で、hzdiの各候補の選択将来全体での改善不能を返す。一度の成立と選択将来全体での成立を分ける。',
    'hzdw': 'hzduと同じ対象束縛で、hzdjの前件の適用例を要求しない条件付き内容を返す。適用例の不存在を存在へ補わない。',
    'hzdx': '五個体列を同じ時代区分・集団・契約のhzdqへ接続する政策。条項・当事者・個人別引数・目的主体・権威・呼びかけは同じ契約から選ぶ。目的の関数記述は共有し、hzdqで目的の五対象を同じ列に固定する。',
}
LIMITS = [
    'rj3は五引数という今回必要な型の変換であり、新しい構文や値の引用演算ではない。長さ五の列は個体を含むため、末端の存在量化で新しい対象の実在を追加しない。型の異なる値や任意個数の異種引数への自動変換は含まない。',
    '順次集計を五回適用した関数は残余引数に依存しない。有限検査は順序・重複・長さ・状況を確認するが、任意の高階関数に対する機械的な一般証明ではない。',
    'hzdu・hzdv・hzdwの知識範囲、支持、方法、結果、候補・継続の解釈上の限界は親定義から引き継ぐ。先行集団・先行時代・契約は前件の関数へ渡し、その条件をどの制度や過程が満たすかを自動確定しない。',
    'hzdxは同じ契約で六つの設定を選ぶ。型だけでは設定関数と契約への割当・目的・呼びかけの意味の整合性を全て保証しない。実際の引受け成立は政策を評価する場合にのみ要求する。',
    '閉じたmodal設定を結果の関数記述にし、既存hzdrを静的に特殊化してから、同じ契約の当事者を行為者とする目的の関数記述を構成する。目的・因果結果・規範対象の各層に同じ五個体列を渡す。未知の設定を生成したり、別の対象を実行時の引用へ補わない。',
    '普遍的な禁止と積極的許可の欠如には同じhzdx政策を渡せるが、原文の唯一の否認の読み、規範の出所と適用条件の網羅性、集団の代表資格、権利・人間本性からの理由、著者帰属は未完。啓蒙全体の進展や括弧内の強調も今回完成したとはしない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions()); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-parameterized-goals-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-bound-revision-basis-v1', document='examples/v014/kant-bound-revision.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def core_composed():
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=ROOTS, statement_indices=[])
    result = extract_basis(doc, basis, selected, version='bound-revision-core-basis-v1', document_path='examples/v014/bound-revision-core.noema')
    return format_graph(selected.document, 'compact') + '\n', result


BUILDERS = ((source_composed, 'kant-bound-revision'), (core_composed, 'bound-revision-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored bound revision differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
