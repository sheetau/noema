"""Keep an attained condition distinct from ongoing development in one epoch."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args

PARENT = 'examples/v014/kant-clear-indications.noema'
FRAME = [('epoch', 'a'), ('context', 'd'), ('history', 'h[d] c'), ('before', 'h[d d] c'),
    ('periods', 'h[a d] c'), ('people', 'h[a] c'), ('present', 'h[a d] c')]
CHECKED = FRAME + [('assessed', 'h[a] e')]
ATTAINED = CHECKED + [('capable', 'h[a] e')]
PROGRESS = FRAME + [('progress', 'e')]
CONTRAST = ATTAINED + [('progress', 'e')]
QUESTION = [(n, t) for n, t in ATTAINED if n != 'context']
ANSWER = [(n, t) for n, t in CONTRAST if n != 'context']
SOURCE = [(n, t) for n, t in FRAME if n != 'context']
SOURCE_ANSWER = SOURCE + [('progress', 'e')]
ROOTS = ['rmh', 'rmi', 'rmj', 'rmk', 'rml', 'rmm', 'rmn']
TRUE = 'e[n p a b][n p a b]'


def definitions():
    selected = app(v('people'), v('person'))
    text = definition('rmh', params(FRAME), both(
        k('rjc', v('epoch'), v('history'), v('before'), v('periods')),
        app(v('periods'), v('epoch'), v('context')), quant('g', 'person', 'a', selected),
        quant('f', 'person', 'a', op('y', selected, app(v('present'), v('person'), v('context'))))))
    evaluated = quant('f', 'person', 'a', op('y', selected, op('t', app(v('assessed'), v('person')), v('context'))))
    attained = quant('f', 'person', 'a', op('y', selected, op('t', app(v('capable'), v('person')), v('context'))))
    text += definition('rmi', params(CHECKED), both(k('rmh', *args(FRAME)), evaluated))
    text += definition('rmj', params(ATTAINED), both(k('rmi', *args(CHECKED)), attained))
    text += definition('rmk', params(PROGRESS), both(k('rmh', *args(FRAME)), op('t', v('progress'), v('context'))))
    text += definition('rml', params(CONTRAST), both(k('rmi', *args(CHECKED)), op('u', k('rmj', *args(ATTAINED))), k('rmk', *args(PROGRESS))))
    text += definition('rmm', params(QUESTION), k('rij', 'b context[' + k('rmj', *args(ATTAINED)) + ']', TRUE), 'f')
    text += definition('rmn', params(ANSWER), k('rik', 'b context[' + k('rml', *args(CONTRAST)) + ']', TRUE), 'f')
    return text


MEANINGS = {
    'rmh': '同じ履歴と順序で時代の範囲が非空の区間をなし、評価文脈がその時代に属し、明示した非空の人々が全てその文脈で生存する。全人類やその時代の全人口であることは補わない。',
    'rmi': 'rmhの同じ人々について、同じ評価文脈で能力評価が全て整合している。',
    'rmj': 'rmiが成立し、同じ人々の全員が同じ文脈で指定された能力を持つ。現在の到達状態の強い候補であり、時代の全過去で成立したことは要求しない。',
    'rmk': 'rmhと同じ時代・人々・評価文脈で、指定した進行内容が成立する。現在全員が能力を持つことや、まだ持たないことをこの条件だけから導かない。',
    'rml': '同じ時代・人々の能力評価が済み、全員の到達状態rmjは成立せず、進行条件rmkは成立する。評価不足だけを到達の否定に使わない。',
    'rmm': '同じ時代・人々のrmjの内容を問う正極性の質問発話。質問を構成しただけで到達状態を主張せず、質問が実際に発せられたことも補わない。',
    'rmn': '同じ設定のrml、すなわち到達はしていないが進行条件はあるという内容を主張する発話。発話の構成と、内容の真理・著者による提示は別である。',
    'hzfb': 'rmjの評価をfo、能力をh4lへ接続する内容。同じ対象者全員が、評価済みで指導なしに自分の理解力を使えることを到達の候補にする。',
    'hzfc': 'rmlの同じ評価と能力をfo・h4lへ接続し、進行内容を別に受け取る。作例では同じ人々へのhzfaを渡し、到達と進行の対象者を一致させる。',
    'hzfd': 'hzfbと同じ到達内容を問う発話。現在時点での問いと、時代全体にわたる全称条件を混同しない。',
    'hzfe': 'hzfcと同じ内容を答えとして主張する発話。到達の否定と進行の肯定を同じ時代・人々・文脈へ結ぶ。',
}
LIMITS = [
    '時代を指定した履歴内の非空区間で表す。歴史的区分、主体となるwirの範囲、生存の一般理論、現実の人口の網羅性は入力の意味規約に依存する。',
    '現在の到達条件は、選んだ人々の全員が指定能力を持つという強い候補である。啓蒙の全ての側面、社会全体の程度、完全性の唯一の基準を確定したものではない。',
    '進行と到達は独立の性質であり、両方が真でも両方が偽でもよい。rmlはそのうち到達偽・進行真を述べる。評価が欠ける場合にはこの回答内容を確認済みとはしない。',
    '作例の進行はhzfaの自己作業の機会と障害の漸減を使う。機会が開かれつつある変化、実際の能力獲得、自己責任による未成熟からの離脱の全意味は依然未完。',
    '質問と回答は同じ閉じた設定から構成し、既存hzcuで問いの提示・回答の提示・本文順序・応答関係へ結べる。型だけで無関係な二記述を同じ問答と保証しない。',
    'u0014冒頭の問答への部分注記。原文の条件付きの問いかけWenn denn nun gefragt wirdを、現実に誰かが質問したという出来事へ変換しない。aber wohlの対比や強調、フリードリヒへの言及、著者帰属と段落全体の意味確認は残る。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, target, fields, parameters in (
        ('hzfb', 'rmj', ATTAINED, SOURCE), ('hzfc', 'rml', CONTRAST, SOURCE_ANSWER)):
        body = k(target, *args(fields, assessed='p fo', capable='p h4l'))
        text += definition(name, params(parameters), 'b context[' + body + ']', 'e')
    text += definition('hzfd', params(SOURCE), k('rij', k('hzfb', *args(SOURCE)), TRUE), 'f')
    text += definition('hzfe', params(SOURCE_ANSWER), k('rik', k('hzfc', *args(SOURCE_ANSWER)), TRUE), 'f')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-clear-indications-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-enlightening-epoch-basis-v1', document='examples/v014/kant-enlightening-epoch.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'enlightening-epoch')
def core_composed(): return projected(ROOTS + ['hzfb', 'hzfc', 'hzfd', 'hzfe', 'hzfa', 'hzey', 'hzez', 'hzcu', 'rmd', 'rme', 'rmf', 'rmg'], 'enlightening-epoch-core')
BUILDERS = ((generic_composed, 'enlightening-epoch'), (source_composed, 'kant-enlightening-epoch'), (core_composed, 'enlightening-epoch-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored enlightening epoch differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
