"""Describe model-relative diagnostic evidence without making it factive."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_declining_hindrances import SOURCE as DECLINE

PARENT = 'examples/v014/kant-declining-hindrances.noema'
SCORING = [('points', 'j[d]'), ('scope', 'h[d] c'), ('classified', 'h[d] c'), ('weight', 'h[d] b'), ('threshold', 'b')]
DIAGNOSTIC = [('evidence', 'e'), ('hypothesis', 'e')] + SCORING
EVIDENCE = [('observer', 'a'), ('item', 'a'), ('target', 'i[e]'), ('context', 'd')] + [
    (n, t) for n, t in SCORING if n != 'classified'] + [('classifications', 'h[a d] c'), ('contents', 'h[a] e'),
    ('linked', 'h[a i[e] d] c'), ('accessible', 'h[a a d] c')]
INDICATIONS = [(n, t) for n, t in EVIDENCE if n != 'item']
RECOGNIZED = INDICATIONS + [('recognized', 'h[a i[e] d] c')]
SOURCE = [(n, t) for n, t in DECLINE if n != 'end'] + [
    ('authority', 'a'), ('roles', 'h[a] a'), ('execution', 'i[h[a a] e]')]
ROOTS = ['rmb', 'rmc', 'rmd', 'rme', 'rmf', 'rmg']


def definitions():
    truth = op('t', v('hypothesis'), v('point')); observed = op('t', v('evidence'), v('point'))
    def mass(predicate): return k('rd4', v('points'), 'i[point d][' + predicate + ']', v('weight'))
    positive, negative = mass(truth), mass(op('u', truth))
    positive_signal, negative_signal = mass(both(truth, observed)), mass(both(op('u', truth), observed))
    # P(E|H) > threshold * P(E|not H), cross-multiplied without division.
    contrast = k('hc', k('hb', v('threshold'), k('hb', negative_signal, positive)), k('hb', positive_signal, negative))
    text = definition('rmb', params(DIAGNOSTIC), both(k('rd5', *args(SCORING[:-1])),
        k('hc', 'n p b b', v('threshold')), k('hc', 'n p a b', positive), k('hc', 'n p a b', negative), contrast))
    evidence = app(v('contents'), v('item'))
    diagnostic = k('rmb', *args(DIAGNOSTIC, evidence=evidence, hypothesis='s[v target]',
        classified='i[point d][' + app(v('classifications'), v('item'), v('point')) + ']'))
    text += definition('rmc', params(EVIDENCE), both(app(v('accessible'), v('observer'), v('item'), v('context')),
        app(v('linked'), v('item'), v('target'), v('context')), op('t', evidence, v('context')), diagnostic))
    text += definition('rmd', params(INDICATIONS), quant('g', 'item', 'a', k('rmc', *args(EVIDENCE))))
    pair = both(op('u', op('e', v('first'), v('second'))), k('rmc', *args(EVIDENCE, item=v('first'))),
        k('rmc', *args(EVIDENCE, item=v('second'))))
    text += definition('rme', params(INDICATIONS), quant('g', 'first', 'a', quant('g', 'second', 'a', pair)))
    text += definition('rmf', params(RECOGNIZED), both(k('rme', *args(INDICATIONS)),
        app(v('recognized'), v('observer'), v('target'), v('context'))))
    text += definition('rmg', params(INDICATIONS), both(k('rme', *args(INDICATIONS)), op('t', 's[v target]', v('context'))))
    return text


MEANINGS = {
    'rmb': '同じ非空の比較状況を重複なく完全に列挙し、全分類と正の重みを確認する。仮説が真・偽の両側に正の重みがあり、真の場合の徴候の重み比率が偽の場合の比率に指定した1超の係数を掛けた値より厳密に大きい。除算せず交差積で比較する。',
    'rmc': '同じ観察主体がこの項目を利用でき、項目が同じ対象記述へ結ばれ、その徴候内容が現在成立し、同じ比較範囲でrmbの識別条件を満たす。対象内容が現在真であることや本人の肯定判断は要求しない。',
    'rmd': '同じ主体・対象記述・現在・比較範囲・重み・基準についてrmcを満たす項目が少なくとも一つある。',
    'rme': '同じ設定について異なる二項目がそれぞれrmcを満たす。複数の徴候であり、独立性や情報量の加算は主張しない。',
    'rmf': 'rmeの複数の徴候があり、同じ主体が同じ対象記述を認識している。肯定判断や対象の真理を追加しない。',
    'rmg': 'rmeに加え、対象内容が現在実際に真であることも要求する。徴候があるだけのrmeとの比較用の強い条件。',
    'hzfa': '同じ人々について、本人の役割に応じた自由な自己作業の機会hze4と、同じ人々の能力を尺度にした障害の漸減hze7を同じ評価文脈で結ぶ内容。漸減の終点をその文脈に固定し、徴候の対象として引用できるよう既知の実行記述を静的に特殊化して使う。',
}
LIMITS = [
    '重み付きの比較モデルに相対的な識別力の候補であり、原文が確率や数値の基準を指定したとはしない。実世界の頻度、事後確率、確信度、証拠の信頼性、明瞭さの全語義を定義し終えたわけではない。',
    '比較範囲・重み・基準は仮説の真偽の両側で固定する。両側に正の重みを要求し、最初から真の候補だけにして強い徴候と認定しない。重みの一様な正の倍率変更では比率の比較を保つ。',
    '対象が偽の候補でも徴候が現れてよい。識別力が強いことから、現在の対象内容の真理、本人の肯定判断、原因の存在を推論しない。現在の状況が比較範囲に含まれることも自動で補わない。',
    '項目の利用可能性、対象記述への対応、観察内容の分類の根拠は入力で指定する。項目の別名や相関した徴候を二つ数えても、証拠が独立だとか信頼性が倍になるとはしない。未知の内容・対応・分類は偽で補わず拒否する。',
    'hzfaの機会は不実行も許される強い候補であり、開かれつつある変化そのものは未構成。障害の漸減も固定した件数尺度の強い候補である。これらの既存の意味上の限界を徴候への接続で解消したとはしない。',
    'u0014のdavonを機会と障害の漸減の連言へ結ぶ部分的な読み。wirの主体は明示した観察主体であり、人類全員の認識や全成員の同意を補わない。明瞭さの選定理由、著者帰属、段落全体の意味確認は残る。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    opportunity = k('hze4', v('authority'), v('people'), v('roles'), v('execution'), v('context'))
    decline = k('hze7', *args(DECLINE, end=v('context')))
    text = definitions() + definition('hzfa', params(SOURCE), 'b context[' + both(opportunity, decline) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-declining-hindrances-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-clear-indications-basis-v1', document='examples/v014/kant-clear-indications.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'clear-indications')
def core_composed(): return projected(ROOTS + ['hzfa', 'hzey', 'hzez'], 'clear-indications-core')
BUILDERS = ((generic_composed, 'clear-indications'), (source_composed, 'kant-clear-indications'), (core_composed, 'clear-indications-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored clear indications differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
