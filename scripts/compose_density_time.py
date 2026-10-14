"""Tie density's spatial ball and charge content to the same event time."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_local_density import FIXED, POINT, ROLES
from scripts.compose_material_velocity import DENSITY
from scripts.compose_additive_charge import SOURCE, CLOCK
from scripts.compose_density_interpretation import BINDINGS, INDEX

PARENT = 'examples/v014/einstein-density-interpretation.noema'
PARENT_BASIS = 'data/einstein-density-interpretation-basis-v1.json'
FULL = 'examples/v014/einstein-density-time.noema'
CORE = 'examples/v014/density-time-manuscript.noema'
REVIEW = 'data/density-formula-review-v4.json'
TIME = [('matter', 'a'), ('frame', 'a'), ('event', 'a'), ('timeunit', 'a'), ('context', 'd'), ('clock', CLOCK)]
LOCAL = [('matter', 'a'), ('frame', 'a'), ('event', 'a'), ('normalized', 'h[b] c'), ('context', 'd')]


def definitions():
    time = app(v('clock'), v('frame'), v('event'), v('timeunit'), v('context'))
    valid = both(*(k('ba', app(v('point'), k(axis))) for axis in ROLES))
    observed = k('zpb', v('matter'), v('frame'), v('event'), v('point'), v('context'))
    agreement = quant('f', 'point', POINT, op('y', both(valid, observed), k('seot', v('point'), time)))
    text = definition('seox', params(TIME), both(k('ba', time), agreement))
    existing = app(k('seom', *args(FIXED)), *args(LOCAL))
    text += definition('seoy', params(FIXED + [('clock', CLOCK)]),
        'i[' + params(LOCAL) + '][' + both(existing, k('seox', *args(TIME))) + ']', DENSITY)
    adapted = k('seou', v('distribution'), v('timeunit'), v('measured'), v('clock'), v('domains'), v('totals'))
    fixed = [adapted if name == 'measured' else v(name) for name, _ in FIXED]
    density = k('seoy', *fixed, v('clock'))
    content = k('seof', v('light'), density, v('electricassigned'), v('frames'))
    text += definition('seoz', params(SOURCE),
        'b context[' + both(k('sedi', v('pi')), op('t', content, v('context'))) + ']', 'e')
    return text


MEANINGS = {
    'seox': '指定した物質点・系・出来事・文脈に属する全ての有効な四座標について、その座標時刻が同じ系・出来事・時間単位・文脈のclockの値と一致する。clock自体の有効性も要求する。座標記録の存在はこの条件単独では主張しない。',
    'seoy': '既存の球平均による規格化密度seomに、同じ物質・系・出来事・時間単位・文脈の時刻整合条件seoxを結ぶ。密度の中心点と別の時刻の総量を、値が零だからという理由で混同しない。',
    'seoz': 'seouの総量の帰属とseoyの密度を同じclockへ結び、座標時間微分の速度seofと本文の式へ渡す。円周率条件と元の電気量帰属、単位、分布、系の配置を保持する。',
}
LIMITS = [
    '旧版seovでは、球の中心点が持つ時刻と総量の対象範囲を切るclockの値が式の上で直接照合されていなかった。seozで同じ出来事の全有効座標に一致を要求し、総量零の場合も時刻の取り違えを拒否する。過去のseouは指定範囲との共通部分を評価する一般構成として変更しない。',
    'seoxは全POINT域の条件である。有限に選んだ地点を全部確認しても、この全域条件の証明にはしない。一つの有効な同じ出来事の反例は不一致の証人になる。',
    'seox単独では座標の存在を要求しないが、seoyのseom側には有効な同じ物質・系・出来事の中心点の存在が含まれる。別の物質・系・出来事・文脈の記録にまで同時刻を要求しない。',
    'この修正は時刻の接続を明示するもので、旧zqdと新しい密度・速度の帰属の双方向一致、電気量や単位の基礎説明、原文単位全体の意味確認を完了させない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions())
    quote = statements[INDEX]['body']['arguments'][-1]['body']
    if quote['symbol'] != 'seov':
        raise ValueError('Expected previous density interpretation')
    quote['symbol'] = 'seoz'
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '\n'
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / PARENT_BASIS).read_text(encoding='utf-8')))
    basis.update(version='einstein-density-time-basis-v1', document=FULL)
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += LIMITS
    basis['interpretation_revision'] = dict(parent=PARENT, statement_index=INDEX,
        previous_content='seov', revised_content='seoz', fixed_bindings=BINDINGS,
        correction='density center coordinate time agrees with the charge-content slice time',
        equivalence_to_parent_proven=False)
    audit_basis(doc, basis)
    return text, basis


def core_composed():
    text, basis = source_composed()
    doc = parse(text)
    selected = extract_document(doc, statement_indices=[INDEX])
    basis = extract_basis(doc, basis, selected, version='density-time-manuscript-basis-v1', document_path=CORE)
    return format_graph(selected.document, 'compact') + '\n', basis


BUILDERS = ((source_composed, 'einstein-density-time'), (core_composed, 'density-time-manuscript'))


def review_packet():
    result = deepcopy(json.loads((ROOT / 'data/density-formula-review-v3.json').read_text(encoding='utf-8')))
    result.update(version='density-formula-review-v4', supersedes='data/density-formula-review-v3.json',
        source_document=FULL, document=CORE, revised_content='seoz',
        integrated_symbols=['seny', 'seoz', 'seoy', 'seox', 'seou', 'seom', 'seof', 'seoe', 'seoc', 'senx', 'senv', 'sent', 'sens'])
    for check in result['checks']:
        if check['id'] in ('discourse_role', 'meaning_expansion_in_statement'):
            check['evidence'] = check['evidence'].replace('seov', 'seoz')
        if check['id'] == 'interpretation_conservativity':
            check['evidence'] = ('Sufficient conditions still require the pi condition and bidirectional assignment agreement. '
                'The revised assignment additionally checks same-event coordinate time against the charge-content clock; this corrects a previously unenforced meaning convention.')
    result['checks'].insert(-1, dict(id='density_charge_time_connection', status='structurally_connected_with_counterexample_check',
        evidence='seoy requires seox on the same density tuple; seoz supplies the same clock to seoy and seou. The original source attribution changes only its quoted content symbol.',
        limit='Instantiated coordinate probes and a zero-total adapter example are not a proof over the full spatial domain or of source equivalence.'))
    result['evidence_reports'].append('reports/density-time-v1.json')
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
            raise ValueError('Stored density time differs: ' + name)
    for name, body in outputs.items():
        path = ROOT / name
        if not path.exists():
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Density center time connected to charge-content clock in the authored reading')


if __name__ == '__main__':
    main()
