"""Bind protective comparisons to the same situation's complete observed state."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_community_protection import STATE, LINK, THREAT_LINK, SETTINGS, SOURCE as POLICY_SOURCE, FALSE

PARENT = 'examples/v014/kant-community-protection.noema'
OBSERVATION = [(n, t) for n, t in LINK if n != 'worlds'] + [('context', 'd'), ('observed', STATE)]
THREAT_OBSERVATION = OBSERVATION + [('threatfactor', 'a'), ('threat', 'e')]
OBSERVED_LINK = LINK + [('records', 'h[d] ' + STATE)]
THREAT_OBSERVED_LINK = THREAT_LINK + [('records', 'h[d] ' + STATE)]
POLICY = SETTINGS + [('observations', 'h[a d] ' + STATE)]
SOURCE = POLICY_SOURCE + [('observations', 'h[a d] ' + STATE)]
ROOTS = ['rkz', 'rk2', 'rk3', 'rk4', 'rk5', 'rk6']


def definitions():
    none = 'i[item a][' + FALSE + ']'
    fit = both(k('rz', v('variables'), v('factor')),
        k('ru', v('variables'), v('equations'), none, none, v('observed')),
        op('z', op('t', v('policy'), v('context')), app(v('observed'), v('factor'))),
        op('z', op('t', v('activity'), v('context')), app(v('goal'), v('observed'))))
    text = definition('rkz', params(OBSERVATION), fit)
    text += definition('rk2', params(THREAT_OBSERVATION), both(k('rkz', *args(OBSERVATION)),
        k('rz', v('variables'), v('threatfactor')), op('u', op('e', v('factor'), v('threatfactor'))),
        op('z', op('t', v('threat'), v('context')), app(v('observed'), v('threatfactor')))))
    for name, prior, fields, linked, observation in (
        ('rk3', 'rkw', THREAT_OBSERVED_LINK, THREAT_LINK, THREAT_OBSERVATION),
        ('rk4', 'rkx', OBSERVED_LINK, LINK, OBSERVATION)):
        text += definition(name, params(fields), 'b context[' + both(
            op('t', k(prior, *args(linked)), v('context')),
            k('rk2' if name == 'rk3' else 'rkz', *args(observation, observed=app(v('records'), v('context'))))) + ']', 'e')
    applied = {name: app(v(plural), v('community')) for name, plural in (
        ('variables', 'catalog'), ('equations', 'laws'), ('factor', 'factors'), ('threatfactor', 'threatfactors'),
        ('goal', 'goals'), ('worlds', 'worldmaps'), ('activity', 'activities'), ('threat', 'threats'))}
    applied['records'] = 'i[point d][' + app(v('observations'), v('community'), v('point')) + ']'
    conditions = [op('t', v('policy'), v('context'))]
    for selection, target, fields in (('reform', 'rk3', THREAT_OBSERVED_LINK), ('retained', 'rk4', OBSERVED_LINK)):
        conditions.append(quant('f', 'community', 'a', op('y', app(v(selection), v('community'), v('anchor')),
            op('t', k(target, *args(fields, **applied)), v('context')))))
    text += definition('rk5', params(POLICY), 'b context[' + both(*conditions) + ']', 'e')
    text += definition('rk6', params(THREAT_OBSERVED_LINK), 'b context[' + both(
        op('t', k('rk3', *args(THREAT_OBSERVED_LINK)), v('context')), op('t', v('threat'), v('context'))) + ']', 'e')
    return text


MEANINGS = {
    'rkz': '同じ評価状況の観測割当てが介入で上書きする前の方程式の解であり、同じ政策内容と活動内容の真偽が、その割当ての政策要因と活動目標に一致する。指定変数外を真にした記録や重複変数は既存ruで拒否する。',
    'rk2': 'rkzに加え、政策と異なる脅威要因がモデルの変数に含まれ、同じ評価状況の脅威内容が同じ観測割当ての脅威要因に一致する。別時点の脅威や別の記録を継ぎ合わせない。',
    'rk3': '前版rkwの政策実施・保護効果・内容対応に、同じ状況の記録を使うrk2の観測整合性を加える。実際に脅威がある場合だけに限定せず、予防的な保護も残す。',
    'rk4': '前版rkxの政策実施・不干渉比較・内容対応に、同じ状況の記録を使うrkzを加える。もともと活動不能なら、観測に適合する不干渉でも活動の実現は導かない。',
    'rk5': '基準時点で選んだ各共同体の保護または不干渉を、同じ共同体・同じ評価状況の観測記録で検査する。別の共同体の整合する記録を流用しない。',
    'rk6': 'rk3の保護と観測整合性に加え、同じ時点で脅威内容も実際に成立する場合。脅威のない予防的なrk3とは区別する。',
    'hzek': '前版hzejと同じ共同体範囲・変更条件・維持条件を使い、rk5の観測整合性付きの政策内容を返す。これを提案の内容として引用しても、提案したことからその政策や観測内容の成立を導かない。',
}
LIMITS = [
    '観測記録は同じ共同体・時点からモデルの全変数への割当てとして与える。測定手続や観測の信頼性を推定する処理ではなく、未知の値は偽で埋めず評価を拒否する。',
    '実際の記録が満たすのは介入による上書き前の方程式である。政策が実施された背景条件をこの方程式にも与える。仮想介入の側だけで成立する記録を、実際の整合した記録として採用しない。',
    '比較状況と実際の状況の同一性は要求しない。モデルに選んだ変数と同じ政策・活動・脅威の内容を照合する。モデル外の全事情や、現実の因果機構の正当性を観測適合だけで証明したとはしない。',
    'rk3では保護効果と整合する記録から選択された活動の成立を検査できるが、rk4は活動を生じさせることを要求しない。保護の全語義、法的地位・救済・補償などの未記述範囲は前版から引き継ぐ。',
    '共同体の選択は引き続き変更条件と維持条件の肯定内容に基づく。制度への合意・希望・宗教制度の具体的な定義、君主の制度的位置、著者帰属と全文の意味確認は残る。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    selections = {name: 'i[community a point d][' + both(app(v('communities'), v('community')),
        op('t', app(v(condition), v('community')), v('point'))) + ']' for name, condition in (
            ('reform', 'changeconditions'), ('retained', 'stayconditions'))}
    text = definitions() + definition('hzek', params(SOURCE), k('rk5', *args(POLICY, **selections)), 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-community-protection-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-observed-protection-basis-v1', document='examples/v014/kant-observed-protection.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS + ['rky'], 'observed-protection')
def core_composed(): return projected(ROOTS + ['hzej', 'hzek', 'hzef'], 'observed-protection-core')
BUILDERS = ((generic_composed, 'observed-protection'), (source_composed, 'kant-observed-protection'), (core_composed, 'observed-protection-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored observed protection differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
