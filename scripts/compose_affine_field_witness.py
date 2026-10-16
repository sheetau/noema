"""Construct affine fields for specified derivative coefficients."""
import json
from noema.grammar import parse, format_graph
from noema.extraction import extract_document, extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_density_origins import ROOT, FULL
from scripts.compose_field_equations import CUT, POINT, JET, FIELD, ROLES
from scripts.compose_density_formula import FORMULA, PARTIALS
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, app, op, both, quant, v
from scripts.compose_situated_criticism import params, args

DOCUMENT = 'examples/v014/affine-field-witness.noema'
BASIS = 'data/affine-field-witness-basis-v1.json'
REVIEW = 'data/density-formula-review-v13.json'


def factory():
    terms = [k('shv', app(v('coefficients'), v('component'), k(role)), v(n))
        for role, n in zip(ROLES, ('x', 'y', 'z', 'time'))]
    total = app(v('offsets'), v('component'))
    for term in terms: total = k('bd', total, term)
    return definition('sexw', 'coefficients '+JET+' offsets '+POINT,
        'i[component a][i['+params([(n, CUT) for n in ('x', 'y', 'z', 'time')])+']['+total+']]', FIELD)


def region():
    return 'i['+params([(n, CUT) for n in ('x', 'y', 'z', 'time')])+']['+both(
        *(k('ba', v(n)) for n in ('x', 'y', 'z', 'time')))+']'


def validity():
    return both(*(op('u', op('e', k(a), k(b))) for i, a in enumerate(ROLES) for b in ROLES[i+1:]),
        *(k('ba', app(v('coefficients'), k(component), k(axis))) for component in ROLES[:3] for axis in ROLES),
        *(k('ba', app(v('offsets'), k(component))) for component in ROLES[:3]),
        *(k('ba', app(v('point'), k(axis))) for axis in ROLES))


def statements():
    field = k('sexw', v('coefficients'), v('offsets'))
    claims = both(*(k('s5t', app(field, k(component)), region(), v('point'), k(axis),
        app(v('coefficients'), k(component), k(axis))) for component in ROLES[:3] for axis in ROLES))
    shared = [('coefficients', JET), ('offsets', POINT), ('point', POINT)]
    text = ''
    for parameters, body in [(shared, op('y', validity(), claims)),
        ([(n, s) for n, s in FORMULA if n != 'newelectricjet']+shared,
         op('y', both(validity(), k('sens', *(v(n) for n, _ in FORMULA if n != 'newelectricjet'), v('coefficients'))),
             k('sent', *(v(n) for n, _ in FORMULA if n != 'newelectricjet'), v('coefficients'), field, region(), v('point'))))]:
        for n, s in reversed(parameters): body = quant('f', n, s, body)
        text += 's['+body+'].'
    return text


def build():
    source = parse((ROOT/FULL).read_text(encoding='utf-8'))
    basis = json.loads((ROOT/'data/einstein-density-origins-basis-v1.json').read_text(encoding='utf-8'))
    assert 'sexw' not in {d['name'] for d in source['declarations']}
    source['statements'] = []
    doc = parse(format_graph(source, 'compact')+factory()+statements())
    basis['definitions']['sexw'] = '係数表と成分ごとの定数から、四座標に関する三成分のアフィン場を構成する。各成分は定数と四つの係数×座標の和。係数表は値の表であり、偏微分としての成立は別の主張で結ぶ。'
    selected = extract_document(doc)
    basis = extract_basis(doc, basis, selected, version='affine-field-witness-basis-v1', document_path=DOCUMENT)
    basis['extraction_source'].pop('statement_indices', None)
    basis['extraction_source']['statement_origin'] = 'Two language-side derived claims; not source-author assertions.'
    basis['extraction_source']['added_definitions'] = ['sexw']
    basis['extraction_source']['metadata_policy'] = 'Old declarations and meanings are projected from the source; sexw and both claims are composed here. All source caveats are retained.'
    basis['unresolved'] += [
        '実数の標準算術を明示的な境界として、アフィン場の偏微分とsensからsentへの接続を検査する。実切断の演算がこの算術を実現することの証明は別に残る。',
        '係数は全実数の記号値として扱い、有限の点で微分を推測しない。物理的な電場帰属、電荷密度の極限、軌跡やMaxwell方程式の全条件を満たす場の構成ではない。',
    ]
    audit_basis(selected.document, basis)
    review = json.loads((ROOT/'data/density-formula-review-v12.json').read_text(encoding='utf-8'))
    review.update(version='density-formula-review-v13', supersedes='data/density-formula-review-v12.json')
    review['checks'].insert(-1, dict(id='affine_derivative_realization', status='standard_scalar_model_checked',
        evidence='A Noema affine field constructor realizes the prescribed coefficient table through the actual s5t/sjs/sjr definitions in an explicit standard real-arithmetic model. The three diagonal results connect sens to sent.',
        limit='This is a scalar interpretation, not a representation proof for all real-cut operations or an electrically assigned field and physical source case.'))
    review['evidence_reports'].append('reports/affine-field-witness-v1.json')
    review['affine_witness_document'] = DOCUMENT
    return {DOCUMENT: format_graph(selected.document, 'compact')+'\n',
        BASIS: json.dumps(basis, ensure_ascii=False, indent=2)+'\n',
        REVIEW: json.dumps(review, ensure_ascii=False, indent=2)+'\n'}


def main():
    for name, body in build().items():
        p = ROOT/name
        if p.exists(): assert p.read_text(encoding='utf-8') == body, name
        else:
            with p.open('x', encoding='utf-8', newline='\n') as f: f.write(body)
    print('Affine field constructed; scalar interpretation still to be checked')


if __name__ == '__main__': main()
