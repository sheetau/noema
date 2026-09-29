"""Reproduce exact linear-arithmetic checks and source-equation alignment."""
import argparse
import hashlib
import json
from pathlib import Path

import z3

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.rational_proofs import verify
from noema.script import encode, decode

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/real-cuts-v1.json'
MEANINGS = {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'}
LAWS = {
    'rational_embedding_is_a_cut': 's[f r b[k ba[k bb[v r]]]].',
    'negation_preserves_embedding': 's[f r b[f q b[z[c[k be[k bb[v r]]][v q]][k aa[v q k ac[v r]]]]]].',
    'addition_preserves_embedding': 's[f a b[f b b[f q b[z[c[k bd[k bb[v a] k bb[v b]]][v q]][k aa[v q k ab[v a v b]]]]]]].',
    'subtraction_preserves_embedding': 's[f a b[f b b[f q b[z[c[k bf[k bb[v a] k bb[v b]]][v q]][k aa[v q k ab[v a k ac[v b]]]]]]]].',
    'strict_order_preserves_embedding': 's[f a b[f b b[z[k bg[k bb[v a] k bb[v b]]][k aa[v a v b]]]]].',
    'clock_equation_preserves_rational_readings': 's[f a b[f b b[f c b[z[k bi[k bb[v a] k bb[v b] k bb[v c]]][e[k ab[v b k ac[v a]]][k ab[v c k ac[v b]]]]]]]].',
}
COUNTERCLAIMS = {
    'empty_is_a_cut': 's[k ba[i[q b][u[e[v q][v q]]]]].',
    'whole_domain_is_a_cut': 's[k ba[i[q b][e[v q][v q]]]].',
    'closed_boundary_is_a_cut': 's[k ba[i[q b][u[k aa[n p a b v q]]]]].',
    'subtraction_can_reverse_arguments': 's[f a b[f b b[f q b[z[c[k bf[k bb[v a] k bb[v b]]][v q]][k aa[v q k ab[v b k ac[v a]]]]]]]].',
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build_report():
    path = 'examples/v011/real-cuts.noema'
    text = (ROOT / path).read_text(encoding='utf-8')
    doc = parse(text)
    basis = json.loads((ROOT / 'data/real-cuts-basis-v1.json').read_text(encoding='utf-8'))
    audit = audit_basis(doc, basis)
    results = {}
    for name, claim in {**LAWS, **COUNTERCLAIMS}.items():
        result = verify(parse(text + claim), MEANINGS)[0]
        if result['status'] != ('valid' if name in LAWS else 'invalid'):
            raise ValueError('Unexpected proof result: ' + name)
        results[name] = result
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Real definition round trip differs')
    alignment = json.loads((ROOT / 'data/einstein-clock-equation-v1.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    source_path = 'artifacts/written-units-v1/einstein-1905.json'
    if sha(source_path) != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source unit artifact changed')
    source = json.loads((ROOT / source_path).read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == alignment['source_unit'])
    math = next(m for m in source['math'] if m['id'] == alignment['math_id'])
    if unit['math_ids'] != [math['id']] or hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest() != alignment['math_sha256']:
        raise ValueError('Equation source differs')
    if alignment['document'] != path or alignment['definition'] not in basis['definitions'] or alignment['status'] != 'partial':
        raise ValueError('Invalid equation alignment')
    files = [path, 'data/real-cuts-basis-v1.json', 'data/einstein-clock-equation-v1.json',
             'noema/rational_proofs.py', 'noema/discourse.py', 'noema/grammar.py', 'noema/meaning_basis.py',
             'noema/script.py', 'scripts/check_real_cuts.py', 'reports/written-units-v1.json', 'pyproject.toml']
    return {'status': 'partial_mathematical_foundation', 'z3_version': z3.get_version_string(),
            'basis_audit': audit, 'linear_rational_results': results, 'roundtrip': True,
            'source_alignment': alignment, 'verified_full_units': 0,
            'general_real_field_laws_machine_verified': False,
            'source_sha256': {p: sha(p) for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Real cut verification differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Real cuts: six linear rational laws valid, four counterclaims invalid; full source coverage incomplete')


if __name__ == '__main__':
    main()
