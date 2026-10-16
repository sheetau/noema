"""State rational existence and uniqueness without adding claims to the author."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.extraction import extract_document, extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_density_origins import ROOT, FULL, CORE
from scripts.compose_limits import call as k, op, both, quant, v
from scripts.check_real_products import assertion

DOCUMENT = 'examples/v014/density-existence.noema'
BASIS = 'data/density-existence-basis-v1.json'
REVIEW = 'data/density-formula-review-v12.json'
INPUTS = 'light speed beta density ux uy uz'.split()
OUTPUTS = 'newdensity vx vy vz'.split()
DIAGONALS = 'newexx neweyy newezz'.split()


def statements():
    square = k('ad', v('light'), v('light'))
    denominator = k('ab', square, k('ac', k('ad', v('speed'), v('ux'))))
    admissible = both(k('sra', v('light'), v('speed'), v('beta')), op('u', op('e', denominator, 'n p a b')))
    body = k('senr', *(v(n) for n in INPUTS+OUTPUTS+DIAGONALS))
    for n in reversed(OUTPUTS+['newexx']): body = quant('g', n, 'b', body)
    existence = assertion(' '.join(INPUTS+DIAGONALS[1:]), op('y', admissible, body))
    first = k('senr', *(v(n) for n in INPUTS+OUTPUTS+DIAGONALS))
    second = k('senr', *(v(n) for n in INPUTS), *(v('other'+n) for n in OUTPUTS+DIAGONALS))
    equal = both(*(op('e', v(n), v('other'+n)) for n in OUTPUTS))
    uniqueness = assertion(' '.join(INPUTS+OUTPUTS+DIAGONALS+['other'+n for n in OUTPUTS+DIAGONALS]),
        op('y', both(first, second), equal))
    return existence+uniqueness


def build():
    full = parse((ROOT/FULL).read_text(encoding='utf-8'))
    basis = json.loads((ROOT/'data/einstein-density-origins-basis-v1.json').read_text(encoding='utf-8'))
    selected = extract_document(full, roots=['senr'], statement_indices=[])
    doc = parse(format_graph(selected.document, 'compact')+statements())
    result = extract_basis(full, basis, selected, version='density-existence-basis-v1', document_path=DOCUMENT)
    result['unresolved'] += [
        '二つの主張は言語側で記述した有理数の存在・一意性の定理であり、原著者の本文への追記ではない。',
        '正の正規化betaを有理数の入力として与える。任意の有理数の速度に有理数のbetaが存在するとの主張ではない。',
        'Dが非零なら正負を問わず構成する。新密度と三速度は一意だが、電場の三対角微分値は和しか拘束しない。',
        '有理切断の算術、実数全域の演算との対応、物理的帰属、軌跡、密度の極限、微分値を実現する場の存在は、この有理数定理だけでは証明されない。',
    ]
    audit_basis(doc, result)
    review = json.loads((ROOT/'data/density-formula-review-v11.json').read_text(encoding='utf-8'))
    review.update(version='density-formula-review-v12', supersedes='data/density-formula-review-v11.json')
    review['checks'].insert(-1, dict(id='rational_output_existence', status='constructive_rational_certificate',
        evidence='For supplied rational positive normalized beta and nonzero D, explicit rational terms construct the unique density and three velocity outputs of senr. Any two diagonal entries may be chosen; the remaining one supplies the required divergence.',
        limit='This proves rational arithmetic existence only. It neither supplies a physical source case nor proves all real-cut operations, trajectories, density limits, electrical assignments or field derivatives.'))
    review['evidence_reports'].append('reports/density-existence-v1.json')
    review['derived_theorem_document'] = DOCUMENT
    return {DOCUMENT: format_graph(doc, 'compact')+'\n',
        BASIS: json.dumps(result, ensure_ascii=False, indent=2)+'\n',
        REVIEW: json.dumps(review, ensure_ascii=False, indent=2)+'\n'}


def main():
    for name, body in build().items():
        p = ROOT/name
        if p.exists(): assert p.read_text(encoding='utf-8') == body, name
        else:
            with p.open('x', encoding='utf-8', newline='\n') as f: f.write(body)
    print('Rational density existence and output uniqueness stated separately from the source')


if __name__ == '__main__': main()
