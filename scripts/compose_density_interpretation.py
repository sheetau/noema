"""Connect the authored formula to an explicit, reviewable density interpretation.

This is a revised reading, not an equivalence-preserving rewrite of the old
opaque assignment. Only one quoted content changes; attribution is preserved.
"""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT
from scripts.compose_additive_charge import SOURCE

PARENT = 'examples/v014/einstein-additive-charge.noema'
PARENT_BASIS = 'data/einstein-additive-charge-basis-v1.json'
FULL = 'examples/v014/einstein-density-interpretation.noema'
CORE = 'examples/v014/density-interpretation-manuscript.noema'
REVIEW = 'data/density-formula-review-v3.json'
INDEX = 174
FIXED = {'light': 'tc', 'electricassigned': 'zqe', 'frames': 'zqf'}
LOCAL = dict(zip((n for n, _ in SOURCE if n not in FIXED),
                 ('zqg', 'zqh', 'zqi', 'zqj', 'zqk', 'zql', 'zqm', 'zqn', 'zqo', 'zqp', 'zqq'), strict=True))
BINDINGS = FIXED | LOCAL
MEANINGS = {
    'distribution': 'この部分解釈で追跡する電荷分布への固定参照。同じ分布を新旧二系で用い、追跡する一点そのものの総電荷とは区別する。',
    'pi': '円周率の固定値。seonのsedi条件と、球体積・4pi規格化の全箇所で同じ値を用いる。任意の正数で代用しない。',
    'lengthunit': '新旧二系の座標と球の大きさに共通して用いる長さ単位への参照。単位の実現は未説明部分として残る。',
    'timeunit': '新旧二系の座標時間と出来事の時刻に共通して用いる時間単位への参照。固有時の単位指定を座標時間へ無断で流用しない。',
    'chargeunit': '選んだ分布の符号付き総電荷と密度に用いる電荷単位への参照。',
    'measured': '分布・系・出来事・空間領域・長さ単位・電荷単位・総量・文脈を結ぶ元の電気量の帰属関係。加法的な任意の量を電荷と同一視しないために保持する。測定済みの事実を意味するとは限らず、仮定上の帰属も文脈で区別する。電気的作用と校正の説明は未完。',
    'chartunits': '指定した系の座標に長さ単位と時間単位を割り当てる関係。新旧二系の各座標と同じ文脈で照合する。',
    'member': '追跡する物質点が選んだ電荷分布に属することを文脈へ結ぶ関係。点の電荷と、その周囲の分布の総量は別である。',
    'clock': '系・出来事・時間単位・文脈から、その出来事の座標時刻を指定する関数。球と総量の同時刻の切断に用いる。',
    'domains': '系・出来事・長さ単位・時間単位・電荷単位・文脈ごとに、総電荷の定義域となる空間領域族を指定する関数。全ての領域の有限総量は要求しない。',
    'totals': 'domainsと同じ六参照ごとに、空間領域へ符号付き総電荷を与える関数を指定する。seouが有限加法性・定義域・元の電気量帰属との一致を検査する。',
}
LIMITS = [
    'この版は、本文の175番目の文の引用内容をsenx(tc,zqd,zqe,zqf)からseovの明示した説明へ改訂する部分解釈である。旧版との無条件の同義性、著者自身がこの数学的説明を選んだことは主張しない。著者・範囲・文脈・先行箇所の帰属は同じ構造で保持する。',
    'seovから、同時刻の符号付き加法的総量、球平均の局所密度、規格化、物質点の座標時間微分が本文の引用内容へ接続される。微分や局所密度の存在が失われると、senxの前提に当てはまる事例自体が減り得る。',
    '旧版と同じ内容と判断する十分条件は、円周率条件と、同じ物質・系・出来事・密度・三速度・文脈について旧帰属zqdと新しく構成した帰属が双方向に一致することである。この一致は定義だけでは証明されず、原文の対象範囲と仮定の確認が残る。',
    '新しい固定参照は自由な推定値ではない。分布・単位・電気量・座標・所属・領域族を指定する意味規約として版管理する。電気的作用と単位の実現、一般の密度や流れとこの読みの一致は未完。',
    '引用内容の意味を改訂するため引用の構文も変える。同じ真理値や内容の外延的一致だけから、旧引用に対する著者の態度を新引用へ移せるとはしない。原文に対応させる改訂読解として別文書に保存する。',
]


def source_composed():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = deepcopy(parent)
    statements, doc['statements'] = doc['statements'], []
    additions = ''.join('r ' + LOCAL[n] + '[] ' + sort + '.' for n, sort in SOURCE if n in LOCAL)
    doc = parse(format_graph(doc, 'compact') + additions)
    previous = statements[INDEX]['body']['arguments'][-1]
    if previous != {'kind': 'quote', 'body': {'kind': 'call', 'symbol': 'senx',
            'arguments': [{'kind': 'call', 'symbol': s, 'arguments': []} for s in ('tc', 'zqd', 'zqe', 'zqf')]}}:
        raise ValueError('Expected historical source quote')
    statements[INDEX]['body']['arguments'][-1] = {'kind': 'quote', 'body': {
        'kind': 'call', 'symbol': 'seov', 'arguments': [
            {'kind': 'call', 'symbol': BINDINGS[n], 'arguments': []} for n, _ in SOURCE]}}
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '\n'
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / PARENT_BASIS).read_text(encoding='utf-8')))
    basis.update(version='einstein-density-interpretation-basis-v1', document=FULL)
    ds = {d['name']: d for d in doc['declarations']}
    for name, symbol in LOCAL.items():
        d = ds[symbol]
        basis['primitives'].append(dict(symbol=symbol, parameters=d['parameters'], result=d['result'],
            arguments=[], meaning_ja=MEANINGS[name]))
    basis['unresolved'] += LIMITS
    basis['interpretation_revision'] = dict(parent=PARENT, statement_index=INDEX,
        old_quote=previous, new_quote=statements[INDEX]['body']['arguments'][-1],
        fixed_bindings=BINDINGS, equivalence_to_parent_proven=False)
    audit_basis(doc, basis)
    return text, basis


def core_composed():
    text, basis = source_composed()
    doc = parse(text)
    selected = extract_document(doc, statement_indices=[INDEX])
    basis = extract_basis(doc, basis, selected, version='density-interpretation-manuscript-basis-v1', document_path=CORE)
    return format_graph(selected.document, 'compact') + '\n', basis


BUILDERS = ((source_composed, 'einstein-density-interpretation'), (core_composed, 'density-interpretation-manuscript'))


def review_packet():
    old = json.loads((ROOT / 'data/density-formula-review-v2.json').read_text(encoding='utf-8'))
    result = deepcopy(old)
    for name in ('statement_sha256', 'quoted_content_sha256', 'dependency_paths'):
        result.pop(name)
    result.update(version='density-formula-review-v3', supersedes='data/density-formula-review-v2.json',
        document=CORE, source_document=FULL, source_statement_index=INDEX,
        original_assignment='zqd', revised_content='seov', fixed_bindings=BINDINGS,
        equivalence_to_previous_reading_proven=False,
        integrated_symbols=['seny', 'seov', 'seou', 'seon', 'seom', 'seof', 'seoe', 'seoc', 'senx', 'senv', 'sent', 'sens'],
        available_not_in_source_statement=[])
    updates = {
        'source_context_bindings': ('structurally_connected_in_revised_reading',
            'The same light, electric assignment, ordered frames, source author, scope, context and earlier node are retained. Eleven fixed interpretation inputs now bind the density/velocity explanation.',
            'The physical meaning of the remaining assignment and unit conventions is incomplete.'),
        'discourse_role': ('structurally_connected_in_revised_reading',
            'The seny attribution has the same five discourse arguments and a revised seov quotation.',
            'This is a separately versioned source reading, not an inference of attitude substitution from extensional equivalence.'),
        'meaning_expansion_in_statement': ('connected_in_revised_reading',
            'The actual authored statement now refers through seov to additive charge, local density and material coordinate velocity.',
            'Connection does not prove that the strengthened interpretation covers exactly the source cases.'),
        'concept_grounding': ('open',
            'Velocity, density and signed totals are now compositional parts of the quoted content. Distribution, electrical attribution, chart units and frame conventions are fixed explicitly.',
            'Electrical action, units and the relationship of the chosen point/distribution model to the source remain incomplete.'),
        'whole_unit_decision': ('open',
            'Meaning explanations are used in a revised manuscript, but added conditions, source-case coverage and remaining basic meanings still need review.',
            'No semantic-completion count is authorized.')}
    for check in result['checks']:
        if check['id'] in updates:
            check['status'], check['evidence'], check['limit'] = updates[check['id']]
    result['checks'].insert(-1, dict(id='interpretation_conservativity', status='open',
        evidence='Sufficient conditions: the chosen pi satisfies sedi, and old/new assignment truth agrees in both directions for every shared tuple. These conditions are not assumed automatically.',
        limit='Missing derivative/density cases may make a conditional law vacuously true; an invalid pi may make the new content false.'))
    result['evidence_reports'].append('reports/density-interpretation-v1.json')
    return result


def main():
    outputs = {}
    for builder, stem in BUILDERS:
        text, basis = builder()
        outputs[basis['document']] = text
        outputs['data/' + stem + '-basis-v1.json'] = json.dumps(basis, ensure_ascii=False, indent=2) + '\n'
    outputs[REVIEW] = json.dumps(review_packet(), ensure_ascii=False, indent=2) + '\n'
    for name, body in outputs.items():
        path = ROOT / name
        if path.exists() and path.read_text(encoding='utf-8') != body:
            raise ValueError('Stored interpretation differs: ' + name)
    for name, body in outputs.items():
        path = ROOT / name
        if not path.exists():
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('One source quotation revised; explanations connected; equivalence remains under review')


if __name__ == '__main__':
    main()
