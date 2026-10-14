"""Describe protective effects and non-interference before proposing the policy."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_policy_norms import TRUE

PARENT = 'examples/v014/kant-public-deliberation.noema'
FALSE = op('u', TRUE)
STATE = 'h[a] c'
EQUATIONS = 'h[a ' + STATE + '] c'
GOAL = 'h[' + STATE + '] c'
WORLDS = 'h[' + STATE + '] d'
MODEL = [('variables', 'j[a]'), ('equations', EQUATIONS), ('factor', 'a'), ('goal', GOAL)]
THREAT = MODEL + [('threatfactor', 'a')]
LINK = MODEL + [('worlds', WORLDS), ('policy', 'e'), ('activity', 'e')]
THREAT_LINK = THREAT + [('worlds', WORLDS), ('policy', 'e'), ('activity', 'e'), ('threat', 'e')]
SETTINGS = [('policy', 'e'), ('anchor', 'd'), ('reform', 'h[a d] c'), ('retained', 'h[a d] c'),
    ('catalog', 'h[a] j[a]'), ('laws', 'h[a] ' + EQUATIONS), ('factors', 'h[a] a'), ('threatfactors', 'h[a] a'),
    ('goals', 'h[a] ' + GOAL), ('worldmaps', 'h[a] ' + WORLDS), ('activities', 'h[a] e'), ('threats', 'h[a] e')]
SOURCE = [(n, t) for n, t in SETTINGS if n not in ('reform', 'retained')] + [
    ('communities', 'h[a] c'), ('changeconditions', 'h[a] e'), ('stayconditions', 'h[a] e')]
ROOTS = ['rks', 'rkt', 'rku', 'rkv', 'rkw', 'rkx', 'rky']


def intervention(target, sign, goal, threatsign=None):
    factor = op('e', v('item'), v('factor'))
    mask = factor if threatsign is None else op('x', factor, op('e', v('item'), v('threatfactor')))
    fixed = sign if threatsign is None else op('x', both(factor, sign), both(op('e', v('item'), v('threatfactor')), threatsign))
    return k(target, v('variables'), v('equations'), 'i[item a][' + mask + ']', 'i[item a][' + fixed + ']', goal)


def definitions():
    valid = both(k('rz', v('variables'), v('factor')), k('rz', v('variables'), v('threatfactor')),
        op('u', op('e', v('factor'), v('threatfactor'))))
    # Off/no threat succeeds; off/threat fails; protection preserves success in
    # both threat settings. Every guarantee includes a nonempty solution set.
    text = definition('rks', params(THREAT), both(valid,
        intervention('rw', FALSE, v('goal'), FALSE),
        intervention('rw', FALSE, 'i[state ' + STATE + '][' + op('u', app(v('goal'), v('state'))) + ']', TRUE),
        intervention('rw', TRUE, v('goal'), FALSE), intervention('rw', TRUE, v('goal'), TRUE)))
    exists = 'i[state ' + STATE + '][' + TRUE + ']'
    text += definition('rkt', params(MODEL), both(k('rz', v('variables'), v('factor')),
        intervention('rv', FALSE, exists), intervention('rv', TRUE, exists),
        op('y', intervention('rv', FALSE, v('goal')), intervention('rw', TRUE, v('goal')))))
    match = both(op('z', op('t', v('policy'), app(v('worlds'), v('state'))), app(v('state'), v('factor'))),
        op('z', op('t', v('activity'), app(v('worlds'), v('state'))), app(v('goal'), v('state'))))
    linked = 'i[state ' + STATE + '][' + match + ']'
    triple = 'i[state ' + STATE + '][' + both(match,
        op('z', op('t', v('threat'), app(v('worlds'), v('state'))), app(v('state'), v('threatfactor')))) + ']'
    text += definition('rku', params(THREAT_LINK), both(valid, *[
        intervention('rw', sign, triple, danger) for sign in (FALSE, TRUE) for danger in (FALSE, TRUE)]))
    text += definition('rkv', params(LINK), both(k('rz', v('variables'), v('factor')),
        intervention('rw', FALSE, linked), intervention('rw', TRUE, linked)))
    text += definition('rkw', params(THREAT_LINK), 'b context[' + both(op('t', v('policy'), v('context')),
        k('rks', *args(THREAT)), k('rku', *args(THREAT_LINK))) + ']', 'e')
    text += definition('rkx', params(LINK), 'b context[' + both(op('t', v('policy'), v('context')),
        k('rkt', *args(MODEL)), k('rkv', *args(LINK))) + ']', 'e')
    applied = {name: app(v(plural), v('community')) for name, plural in (
        ('variables', 'catalog'), ('equations', 'laws'), ('factor', 'factors'), ('threatfactor', 'threatfactors'),
        ('goal', 'goals'), ('worlds', 'worldmaps'), ('activity', 'activities'), ('threat', 'threats'))}
    obligations = []
    for selection, target, fields in (('reform', 'rkw', THREAT_LINK), ('retained', 'rkx', LINK)):
        obligations.append(quant('f', 'community', 'a', op('y', app(v(selection), v('community'), v('anchor')),
            op('t', k(target, *args(fields, **applied)), v('context')))))
    text += definition('rky', params(SETTINGS), 'b context[' + both(op('t', v('policy'), v('context')), *obligations) + ']', 'e')
    return text


MEANINGS = {
    'rks': '同じ方程式・活動目標で政策と脅威の二要因を別々に介入する。政策なし・脅威なしでは活動が成立し、政策なし・脅威ありでは不成立、政策ありでは脅威の有無のどちらでも成立することを、各場合の非空の全解で要求する。',
    'rkt': '同じ政策要因の有無の両側に解があり、政策なしで活動を満たす解が一つでもあるなら、政策ありでは全解で活動が成立する。単に強い妨害を否定するより強い、活動を失わせない比較条件。',
    'rku': '政策・脅威を別々に切り替えた四条件の全解で、対応する状況の同じ政策内容・脅威内容・活動内容が、それぞれモデルの政策要因・脅威要因・活動目標の真偽と一致する。四条件全てに解を要求する。',
    'rkv': '政策有無の両側の非空の全解で、対応状況の同じ政策内容と活動内容が、モデルの政策要因と目標の真偽に一致する。無関係な目標の保存を、その活動の不干渉としない。',
    'rkw': '同じ政策が評価状況で成立し、rksの保護効果とrkuの内容対応があるという内容。モデルの選択された脅威を防いで活動を保つ、一つの強い保護の読み。',
    'rkx': '同じ政策が評価状況で成立し、rktの損失を生じさせない比較とrkvの内容対応があるという内容。活動がもともと不可能な場合もあり、政策による害の不在だけで実際の活動を認定しない。',
    'rky': '固定した基準時点で改革側に当たる全共同体にはrkw、維持側に当たる全共同体にはrkxが、同じ実施政策について成立する内容。共同体ごとのモデル・活動・脅威を保持し、結果時点に対象群を選び直さない。',
    'hzej': 'rkyの対象群を、共同体であり、同じ基準時点で明示された変更条件または維持条件の内容を満たすものへ接続する。変更側でないというだけで維持側へ分類せず、両条件を独立に保つ。',
}
LIMITS = [
    '保護はここでは明示された脅威による活動喪失を政策が防ぐ強い介入比較である。予防・法的地位・救済・補償・確率的な危険低減など、保護の全用法の必要十分条件ではない。脅威が実際に発生したという条件は加えない。',
    'rktは政策なし側で成功が可能なら政策あり側で成功を保証する強い読みである。全解の全組に損失がないことを要求し、平均効果や部分的な妨害の不存在と同一視しない。両側に解を要求し、無解を無害としない。',
    '方程式・背景・変数・目標・世界対応を同じ比較の間で固定する。内容対応は選択された介入解での真偽を検査するもので、現実の因果機構への適合や未知の脅威の網羅性を証明しない。',
    '改革側と維持側は基準時点の二つの肯定条件で選ぶ。互いの否定として定義せず、空の対象群や両側に当たる共同体も構文上排除しない。存在や分類の完全性が必要なら別の条件として加える。',
    '同じ共同体の同じ活動内容をモデルの目標へ接続する。変更した制度への合意、よりよい理解についての当事者の判断、旧制度を望むこと、宗教制度・共同体の具体的な定義は選択条件と活動内容を埋める次の課題である。',
    'hzejの閉じた適用記述を共同提案の内容として渡せる。提案すること・提案可能性は、政策が実施されたことや保護・不干渉が実現したことを含意しない。君主の制度的位置、目的の因果、著者帰属と全文の意味確認は残る。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    selections = {name: 'i[community a point d][' + both(app(v('communities'), v('community')),
        op('t', app(v(condition), v('community')), v('point'))) + ']' for name, condition in (
            ('reform', 'changeconditions'), ('retained', 'stayconditions'))}
    text = definitions() + definition('hzej', params(SOURCE), k('rky', *args(SETTINGS, **selections)), 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-public-deliberation-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-community-protection-basis-v1', document='examples/v014/kant-community-protection.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'community-protection')
def core_composed(): return projected(ROOTS + ['hzej', 'rko', 'rkp', 'rkq', 'hzef'], 'community-protection-core')
BUILDERS = ((generic_composed, 'community-protection'), (source_composed, 'kant-community-protection'), (core_composed, 'community-protection-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored community protection differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
