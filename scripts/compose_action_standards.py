"""Assess a described action against explicit personal standards without enacting it."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT
from scripts.compose_self_reports import ROOTS as REPORT_ROOTS

PARENT = 'examples/v014/kant-self-reports.noema'
ROOTS = ['rne', 'rnf', 'rng']
ACTION = 'i[h[a a] e]'
STANDARD = 'h[a ' + ACTION + '] e'


def definitions():
    return """
d rne[person a action i[h[a a] e] standards j[h[a i[h[a a] e]] e]] e[b context[
 q[v standards][u[e[n p a b][n p a b]]][i[failed c standard h[a i[h[a a] e]] e][
 x[v failed][u[t[c[v standard][v person v action]][v context]]]]]
]].
d rnf[person a action i[h[a a] e] standards j[h[a i[h[a a] e]] e]] e[b context[
 w[u[e[d[v standards]][n p a b]]][u[t[k rne[v person v action v standards]][v context]]]
]].
d rng[action i[h[a a] e] standards j[h[a i[h[a a] e]] e]] h[j[a]] e[i[bindings j[a]][b context[
 w[k rdr[v bindings n p b b]][g seed a[t[
  c[q[v bindings][i[person a][k rnf[v person v action v standards]]][i[state h[a] e item a][i[person a][c[v state][v item]]]]][v seed]
 ][v context]]]
]]].
"""

MEANINGS = {
    'rne': '本人と同じ行為記述について、明示した基準列の少なくとも一つがその文脈で不成立であるという内容。空列では不足を認定しない。行為記述を渡すこと自体は行為の実行ではない。',
    'rnf': '非空の明示的な基準列について、本人の同じ行為記述にrneの不足がないという内容。空列を適合の証拠にしない。単なる禁止の不在や義務の成立とは区別する。',
    'rng': 'rnfをちょうど一人の順序付き引数列へ接続する内容関数。行為記述と基準列を固定したまま、同じ本人への評価を判断内容として埋め込める。',
}
LIMITS = [
    '品位に反しないことへの部分的な構成候補として、本人の行為記述が明示的な非空の基準列に不足しないことを使う。基準が品位を適切に説明すること、その文化的・制度的・道徳的根拠や網羅性は別途必要である。',
    '基準関数の引数は本人と行為記述であり、現在実行された行為個体ではない。記述だけを対象にする基準なら実行を仮定せず評価できる。任意の基準が内部で実行を調べないことまでは型で保証しない。',
    '同じ真理値を返す別の行為記述を同一視しない。基準列の順序や重複は充足判定を変えないが、基準列や判断内容の記述同一性とは別である。',
    'rnaにrngの閉じた記述を渡すと、本人が同じ行為について基準に反しないと判断する内容になる。現実の基準充足、実際の発言、発言内容の真偽、義務や政策をそこから導かない。',
    '基準が未知なら判定を拒否する。非空の判断候補全てで適合するという既存の判断モデルを使い、単に不適合だという判断を持たない状態とは区別する。',
    '原文のseiner nicht unwürdig findetへの部分注記であり、品位の一般的定義、程度・婉曲の語用、名称拒否・称賛と段落全体の意味確認は残る。原始記号と著者主張は追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions()); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-self-reports-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-action-standards-basis-v1', document='examples/v014/kant-action-standards.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS + REPORT_ROOTS + ['rm2','rm3','rm4','rm5','rm6','rm7'], 'action-standards')
def core_composed(): return projected(ROOTS + REPORT_ROOTS + ['hzfr','hzfs','hzft','hzfu','rm2','rm3','rm4','rm5','rm6','rm7','hzfn','hzfo','hzfp','hzfq'], 'action-standards-core')
BUILDERS = ((generic_composed, 'action-standards'), (source_composed, 'kant-action-standards'), (core_composed, 'action-standards-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored action standards differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
