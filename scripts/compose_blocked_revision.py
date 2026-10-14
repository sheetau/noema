"""Bind revision goals to the same holder, starting stage and outcome relation."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_epistemic_revision import CHANGE

PARENT = 'examples/v014/kant-epistemic-revision.noema'
OPTIONS = [('available', 'h[a a d] c'), ('outcomes', 'h[a a d d] c')]
CHOICE = [('actor', 'a'), ('start', 'd')] + OPTIONS
BLOCK = [('actor', 'a'), ('goal', 'e'), ('start', 'd')] + OPTIONS
SOURCE = [(n, t) for n, t in CHANGE if n not in ('before', 'after')] + OPTIONS
ROOTS = ['rja', 'rjb', 'xb', 'xc']
SOURCE_ROOTS = ['hzda', 'hzdb', 'hzdc', 'hzdd', 'hzcq']


def definitions():
    enabled = app(v('available'), v('actor'), v('plan'), v('start'))
    outcome = app(v('outcomes'), v('actor'), v('plan'), v('start'), v('end'))
    text = definition('rja', params(CHOICE), quant('f', 'plan', 'a', op('y', enabled, quant('g', 'end', 'd', outcome))))
    text += definition('rjb', params(BLOCK), both(k('rja', *args(CHOICE)), op('u', k('xb', *args(BLOCK)))))
    return text


MEANINGS = {
    'rja': '同じ行為主体・開始状況の全ての利用可能な方法について、想定結果が少なくとも一つある。方法がなければ成立する。列挙の網羅性そのものは証明しない。',
    'rjb': 'rjaで空の想定結果を持つ利用可能な方法がないことを確認し、同じ主体・目的・開始状況について成功可能性xbがない。成功保証xcの否定とは異なる。',
    'hzda': '同じ知識主体と評価状況を保持し、開始段階から各想定結果段階へのri5の情報拡大を目的として、rjbの成功可能性の不在を述べる内容。実際に情報が増えていないことだけでは成立しない。',
    'hzdb': 'hzdaと同じ設定で、ri6の誤りの減少を達成する方法の成功可能性がないという内容。誤りが元からない場合も減少の目的は達成できず、そのことだけで害とはしない。',
    'hzdc': '同じ設定で、ri7の範囲内の誤りの全除去を達成する方法の成功可能性がないという内容。部分除去もできないhzdbとは分ける。',
    'hzdd': '同じ主体・範囲・評価状況・開始段階・方法と結果について、hzdaとhzdbがともに成立する。両目的を同じ方法で同時に達成できないという弱い条件へ置換しない。',
}
LIMITS = [
    'availableとoutcomesは、主体・方法・開始状況を固定した利用可能性と想定結果の関係。実際に方法を選んだか、許可されたか、成功が保証されるかとは別である。未知は空集合として与えない。',
    'rjaは各利用可能方法の結果が空でないという整合性だけを調べる。方法と結果の網羅性・現実への適合性は明示した解釈の前提であり、有限モデルから現実の不可能性を証明しない。',
    'SOURCEのassessmentは真偽の評価状況で、内容を評価するstartと別。改善の比較ではbefore=start、after=想定結果の状況とし、現在と結果の真理を混同しない。',
    'holderは一人でも集団でもよいが、集団の知識・方法への帰属は解釈の前提である。全構成員が同じことを知る、同じ方法を使えるとはしない。世代の同定や継承の一般定義は未完。',
    'ri5・ri6・ri7の支持、比較範囲、意味内容による情報増加の限界を引き継ぐ。恒真命題の理解の進歩や、知識一般の十分条件へ広げない。',
    '閉じたhzdd等の結果を既存hzcqへ渡すと、同じ記述の因果関係と結果の成立を結べる。因果関係は引数で明示し、単なる同時成立・目的・契約の成立から推定しない。',
    'u0013の状態へ置くことと不可能性への部分候補。前後世代の同定、時代の順序、契約・宣誓への目的接続、mussの必然性、将来性、規範的否認、啓蒙全体の進展は未完。実際に妨害したとの著者主張を追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, target in (('hzda', 'ri5'), ('hzdb', 'ri6'), ('hzdc', 'ri7')):
        goal = 'b end[' + k(target, *args(CHANGE, before=v('start'), after=v('end'))) + ']'
        body = k('rjb', *args(BLOCK, actor=v('holder'), goal=goal))
        text += definition(name, params(SOURCE), 'b start[' + body + ']', 'e')
    text += definition('hzdd', params(SOURCE), 'b start[' + both(*(op('t', k(n, *args(SOURCE)), v('start')) for n in ('hzda', 'hzdb'))) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-epistemic-revision-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-blocked-revision-basis-v1', document='examples/v014/kant-blocked-revision.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'blocked-revision')
def core_composed(): return projected(ROOTS + SOURCE_ROOTS, 'blocked-revision-core')
BUILDERS = ((generic_composed, 'blocked-revision'), (source_composed, 'kant-blocked-revision'), (core_composed, 'blocked-revision-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored blocked revision differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
