"""Quantify eligible enablers without replacing missing assessments by inability."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_topical_enablement import ENABLING, METHODS, CHECKED, POSSIBLE, COLLECTIVE, SOURCE

PARENT = 'examples/v014/kant-topical-enablement.noema'
ACTOR_CHECK = ENABLING + METHODS
SCOPE_CHECK = [(n, t) for n, t in ACTOR_CHECK if n != 'enabler'] + [('eligible', 'h[a a] c')]
SCOPE_POSSIBLE = SCOPE_CHECK + [('goals', 'h[a a] e')]
SCOPED_SOURCE = SOURCE + [('agents', 'h[a a d] c')] + [(n, t) for n, t in ENABLING if n not in ('enabler', 'person', 'context')]
GROUP_SOURCE = [(n, t) for n, t in COLLECTIVE if n not in ('assessed', 'capable', 'enableassessed', 'enableable')] + SCOPED_SOURCE
ROOTS = ['rlq', 'rlr', 'rls', 'rlp', 'rlm']


def definitions():
    offered = app(v('enabling'), v('enabler'), v('person'), v('plan'), v('context'))
    effect = app(v('effects'), v('enabler'), v('person'), v('plan'), v('context'), v('future'))
    assessed = k('rll', *args(CHECKED, context=v('future')))
    outcomes = quant('f', 'plan', 'a', op('y', offered,
        quant('f', 'future', 'd', op('y', effect, assessed))))
    text = definition('rlq', params(ACTOR_CHECK), both(k('rln', *args(ENABLING)), outcomes))
    member = app(v('eligible'), v('enabler'), v('person'))
    text += definition('rlr', params(SCOPE_CHECK), quant('f', 'enabler', 'a',
        op('y', member, k('rlq', *args(ACTOR_CHECK)))))
    text += definition('rls', params(SCOPE_POSSIBLE), quant('g', 'enabler', 'a',
        both(member, k('rlo', *args(POSSIBLE)))))
    return text


MEANINGS = {
    'rlq': '同じ実施者・本人・開始時点についてrlnが成立し、利用可能な各支援方法の全想定結果で、同じ本人・事柄の範囲の能力評価rllが整合する。将来の評価欠落と、評価した結果として能力がないことを分ける。',
    'rlr': '本人ごとに指定した実施者の範囲の全成員についてrlqが成立する。範囲は結果時点で変更しない。範囲が明示的に空なら全評価条件は成立するが、支援可能性の存在は導かない。',
    'rls': '指定した本人に対する実施者の範囲に、同じ本人を同じ事柄の能力状態へ置けるrloの実施者が少なくとも一つ存在する。別の実施者の失敗だけでこの存在を否定しない。全範囲の評価条件rlrとは別に保持する。',
    'hzev': '人aaについて、同じ本人・基準時点で固定した実施者範囲と、同じ主題・基準時点の事柄の範囲へrlrを接続する性質。',
    'hzew': '人aaについて、hzevと同じ実施者・事柄の範囲でrlsの支援可能性を述べる性質。自立的で理由に支えられた判断という目標はhzerと共通である。',
    'hzex': '同じ人々について、現在能力hzerと範囲内のいずれかによる支援可能性hzewの不足をrlpで比較する。支援結果での能力評価もhzevによって確認し、未評価の結果を不能として数えない。',
}
LIMITS = [
    '前版hzeuの固定実施者という制限を、本人ごとに指定できる実施者範囲への存在量化で拡張する。前版の定義は保持する。原文の受動態が許す実施者を現実に全て列挙した証明ではない。',
    '実施者の範囲は本人と基準時点で固定する。本人、他者、集団や装置を範囲へ明示的に含められるが、名前や型だけでその能力を与えない。空の範囲と範囲が未知であることは別で、未知は偽に置き換えない。',
    'rlrは可能な全支援結果における能力評価の整合を要求する。rlsは成功する実施者の存在であり、別の実施者の結果に評価欠落があっても成功する証人があれば真になり得る。人数による不足hzexは両者を分け、評価欠落のある対象を不能へ算入しない。',
    '各人にそれぞれ支援方法があることは、全員を同時に支援できる共通の方法や資源配分の存在ではない。共同実施や連鎖的な支援は対応する実施者と方法・結果を別途説明する必要がある。',
    '将来結果の評価整合は、指定された評価対象の非空性と結果への包含であり、根拠そのものの正しさや現実の因果関係を保証しない。実行器が未知の基本関係を要求した場合は評価を拒否する。',
    'u0014第二文の既存の部分注記を精密化する。宗教の内容、sicher und gutの全語義、人数に還元されない程度、時代の問答、進行と徴候、著者帰属、原文全体の意味確認は残る。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    relevant = 'i[person a matter a][' + app(v('topics'), v('person'), v('topic'), v('matter'), v('anchor')) + ']'
    eligible = 'i[enabler a person a][' + app(v('agents'), v('enabler'), v('person'), v('anchor')) + ']'
    goals = 'i[person a matter a][' + k('rlk', v('person'), v('matter'), *['p ' + n for n in ('ab', 'ac', 'fa', 'fb', 'fc', 'fd', 'ad')]) + ']'
    text = definitions()
    for name, target, fields in (('hzev', 'rlr', SCOPE_CHECK), ('hzew', 'rls', SCOPE_POSSIBLE)):
        body = k(target, *args(fields, relevant=relevant, eligible=eligible, goals=goals))
        text += definition(name, params(SCOPED_SOURCE), 'i[person a][b context[' + both(k('aa', v('person')), body) + ']]', 'h[a] e')
    functions = {field: k(symbol, *args(fields)) for field, symbol, fields in (
        ('assessed', 'hzeq', SOURCE), ('capable', 'hzer', SOURCE),
        ('enableassessed', 'hzev', SCOPED_SOURCE), ('enableable', 'hzew', SCOPED_SOURCE))}
    humans = quant('f', 'person', 'a', op('y', app(v('scope'), v('person')), k('aa', v('person'))))
    text += definition('hzex', params(GROUP_SOURCE), both(humans, k('rlp', *args(COLLECTIVE, **functions))))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-topical-enablement-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-scoped-enablers-basis-v1', document='examples/v014/kant-scoped-enablers.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'scoped-enablers')
def core_composed(): return projected(ROOTS + ['hzev', 'hzew', 'hzex'], 'scoped-enablers-core')
BUILDERS = ((generic_composed, 'scoped-enablers'), (source_composed, 'kant-scoped-enablers'), (core_composed, 'scoped-enablers-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored scoped enablers differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
