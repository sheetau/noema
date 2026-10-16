"""Connect the existing common-zero convention to the density frame condition."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.extraction import extract_document, extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, quant as q
from scripts.compose_positive_axis_calibration import FULL as PARENT, INDEX, FIELDS, BINDINGS as PREVIOUS_BINDINGS, CUT, FRAMES

FULL = 'examples/v014/einstein-density-origins.noema'
CORE = 'examples/v014/density-origins-manuscript.noema'
REVIEW = 'data/density-formula-review-v11.json'
BINDINGS = {**PREVIOUS_BINDINGS, 'frames': 'sexv'}
MEANINGS = {
    'sexu': '同じ出来事・文脈について、両系の有効な四成分記録と、既存の共通零条件smkを要求する。静止系の実際の原点割当と、その原点に出来事があることも明示する。動く系での原点割当・配置はsmkが要求する。二つの原点物の同一性や全出来事での座標一致ではない。',
    'sexv': '先行する二系・速度・配置・方向記録・所有系での正方向の条件sextを保持し、同じ文脈にsexuを満たす一つの出来事がある標準原点配置へ限定する。原点をずらした一般の配置まで含む関係とはしない。',
}
LIMITS = [
    '密度式の既存の零定数の座標変換に合わせ、両系の共通零出来事を配置条件へ接続した。原点や時刻原点を自由にずらす場合は、既存の独立加算定数の表現が別に必要である。',
    '共通零は一つの出来事の空間座標・座標時刻に関する条件であり、全出来事での同時性や時計指示の一致、二つの原点物の同一性を含意しない。',
    'shdによる出来事と座標の実際の割当、原点割当、位置関係の物理的充足は別の意味境界として残る。有限検査で測定・校正・慣性系や全適用事例を証明したとはしない。',
    '配置条件を強めたため旧版との無条件の意味同値は主張しない。実際の原文事例での前提の充足、電気的帰属、物質軸全体と全文の意味確認は未完である。',
]


def definitions():
    event, context = v('event'), v('context')
    record = lambda frame: k('zdz', event, k(frame), context)
    origin = k('zbn', k('ra'), context)
    text = definition('sexu', 'event a context d', both(
        k('zc4', event),
        k('sha', record('ra'), 'p ba'), k('sha', record('zbm'), 'p ba'),
        k('smk', event, context), k('zbv', k('ra'), origin, context),
        k('cb', event, origin, k('ra'))))
    text += definition('sexv', '', 'i[first a second a value '+CUT+' context d]['+both(
        app(k('sext'), v('first'), v('second'), v('value'), context),
        q('g', 'event', 'a', k('sexu', event, context)))+']', FRAMES)
    return text


def build():
    old = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    doc = deepcopy(old); doc['statements'] = []
    assert not set(MEANINGS) & {d['name'] for d in doc['declarations']}
    doc = parse(format_graph(doc, 'compact')+definitions())
    doc['statements'] = deepcopy(old['statements'])
    expression = doc['statements'][INDEX]['body']['arguments'][-1]['body']
    assert expression == dict(kind='call', symbol='seoz', arguments=[dict(kind='call', symbol=PREVIOUS_BINDINGS[n], arguments=[]) for n, _ in FIELDS])
    expression['arguments'] = [dict(kind='call', symbol=BINDINGS[n], arguments=[]) for n, _ in FIELDS]
    basis = json.loads((ROOT/'data/einstein-positive-axis-calibration-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-density-origins-basis-v1', document=FULL)
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    basis['interpretation_revision'] = dict(parent=PARENT, statement_index=INDEX, changed_arguments=['frames'],
        previous_bindings=PREVIOUS_BINDINGS, fixed_bindings=BINDINGS, equivalence_to_parent_proven=False,
        new_primitives=0, configuration_relation_retained='zqf', common_zero_condition_reused='smk')
    audit_basis(doc, basis)
    review = json.loads((ROOT/'data/density-formula-review-v10.json').read_text(encoding='utf-8'))
    review.update(version='density-formula-review-v11', supersedes='data/density-formula-review-v10.json',
        source_document=FULL, document=CORE, fixed_bindings=BINDINGS)
    for row in review['checks']:
        if row['id'] == 'source_context_bindings':
            row['evidence'] = 'sexv retains sext and requires one common-zero event in the supplied context through sexu and the existing smk condition.'
            row['limit'] = 'This restricts the adopted zero-offset reading. Physical assignment, metrology, inertia and full source-case coverage remain open; it does not cover arbitrary translated origins.'
    review['checks'].insert(-1, dict(id='common_zero_event', status='connected_in_revised_reading',
        evidence='The same event has valid four-component records assigned in both source frames, vanishing coordinates and coordinate times, and lies at the assigned origin of each frame.',
        limit='One common event does not equate distinct events, origin objects, all coordinates or physical clock readings. Assignment and placement retain their explicit semantic boundaries.'))
    review['integrated_symbols'] += list(MEANINGS)
    review['evidence_reports'].append('reports/density-origins-v1.json'); review['semantic_completion'] = False
    selected = extract_document(doc, roots=[], statement_indices=[INDEX])
    files = {FULL: format_graph(doc, 'compact')+'\n', 'data/einstein-density-origins-basis-v1.json': basis,
        CORE: format_graph(selected.document, 'compact')+'\n', REVIEW: review,
        'data/density-origins-manuscript-basis-v1.json': extract_basis(doc, basis, selected,
            version='density-origins-manuscript-basis-v1', document_path=CORE)}
    return {p: x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, indent=2)+'\n' for p, x in files.items()}


def main():
    for p, body in build().items():
        path = ROOT/p
        if path.exists(): assert path.read_text(encoding='utf-8') == body, p
        else:
            with path.open('x', encoding='utf-8', newline='\n') as f: f.write(body)
    print('Common-zero event connected to the density frame condition', flush=True)


if __name__ == '__main__': main()
