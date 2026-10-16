"""Construct exact rational outputs of the actual saved density relation."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import json
import subprocess
import sys
import z3
from noema.grammar import parse, format_graph
from noema.extraction import extract_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.rational_witnesses import verify_witnesses
from noema.script import transcribe
from scripts.compose_density_existence import ROOT, FULL, CORE, DOCUMENT, BASIS, REVIEW, INPUTS, OUTPUTS, DIAGONALS, build
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k

REPORT = ROOT/'reports/density-existence-v1.json'


def document(): return parse((ROOT/DOCUMENT).read_text(encoding='utf-8'))


def one_statement(index):
    doc = document(); doc['statements'] = [doc['statements'][index]]; return doc


def certificate(doc):
    node = doc['statements'][0]['body']; inputs = []
    while node['kind'] == 'forall': inputs.append(node['variable']); node = node['body']
    assert len(inputs) == len(INPUTS)+2 and node['kind'] == 'implies'
    node = node['arguments'][1]; outputs = []
    while node['kind'] == 'exists': outputs.append(node['variable']); node = node['body']
    assert len(outputs) == 5 and node['kind'] == 'call' and node['symbol'] == 'senr'
    v = {n: ['variable', actual] for n, actual in zip(INPUTS+DIAGONALS[1:], inputs, strict=True)}
    mul = lambda a, b: ['multiply', a, b]
    sub = lambda a, b: ['add', a, ['negate', b]]
    div = lambda a, b: ['divide', a, b]
    square = mul(v['light'], v['light']); D = sub(square, mul(v['speed'], v['ux']))
    rho = div(mul(mul(v['beta'], D), v['density']), square)
    terms = [rho, div(mul(square, sub(v['ux'], v['speed'])), D),
        div(mul(square, v['uy']), mul(v['beta'], D)),
        div(mul(square, v['uz']), mul(v['beta'], D)), sub(sub(rho, v['neweyy']), v['newezz'])]
    return dict(zip(outputs, terms, strict=True))


@lru_cache(None)
def proofs():
    doc = one_statement(0); terms = certificate(doc)
    existence = verify_witnesses(doc, MEANINGS, terms, timeout_ms=20000)
    assert existence['status'] == 'valid', existence
    uniqueness = verify_universal(one_statement(1), MEANINGS, timeout_ms=20000)[0]
    assert uniqueness['status'] == 'valid', uniqueness
    # Mutating the actual saved premise must invalidate this certificate:
    # without nonzero D, the proposed division witnesses need not be defined.
    weak = deepcopy(doc); node = weak['statements'][0]['body']
    while node['kind'] == 'forall': node = node['body']
    assert node['arguments'][0]['kind'] == 'and'
    node['arguments'][0] = node['arguments'][0]['arguments'][0]
    missing_denominator = verify_witnesses(weak, MEANINGS, terms, timeout_ms=20000)
    assert missing_denominator['status'] == 'uncertified', missing_denominator
    wrong = deepcopy(terms); name = list(wrong)[1]; wrong[name] = ['negate', wrong[name]]
    wrong_sign = verify_witnesses(doc, MEANINGS, wrong, timeout_ms=20000)
    assert wrong_sign['status'] == 'uncertified', wrong_sign
    return dict(existence=existence, uniqueness=uniqueness, witnesses=terms,
        missing_denominator_condition=missing_denominator, wrong_velocity_sign=wrong_sign,
        real_cut_existence_proved=False, physical_source_applicability_proved=False)


def rational_outputs(inputs, yy=0, zz=0):
    V, speed, beta, rho, ux, uy, uz = map(F, inputs)
    assert V > 0 and speed*speed < V*V and beta > 0 and beta*beta*(V*V-speed*speed) == V*V
    D = V*V-speed*ux
    if D == 0: raise ValueError('Undefined velocity denominator')
    newrho = beta*D*rho/(V*V)
    return [newrho, V*V*(ux-speed)/D, V*V*uy/(beta*D), V*V*uz/(beta*D), newrho-F(yy)-F(zz), F(yy), F(zz)]


@lru_cache(None)
def concrete_cases():
    doc = document(); doc['statements'] = []; base = format_graph(doc, 'compact')
    cases = {
        'positive_density': ((5, 3, F(5,4), 4, 1, -2, 3), 0, 0),
        'negative_density': ((5, 3, F(5,4), -4, 1, -2, 3), 2, -3),
        'zero_density_nonzero_velocity': ((5, 3, F(5,4), 0, 1, -2, 3), 2, -3),
        'negative_denominator': ((5, 3, F(5,4), 4, 10, 2, -1), 1, 2),
        'opposite_boost': ((5, -3, F(5,4), 4, 1, -2, 3), -1, 4),
        'zero_boost': ((1, 0, 1, 2, 0, 0, 0), 0, 0),
        'different_diagonal_split': ((5, 3, F(5,4), 4, 1, -2, 3), 7, -2),
    }; rows = {}
    for name, (inputs, yy, zz) in cases.items():
        outputs = rational_outputs(inputs, yy, zz)
        claim = assertion('', k('senr', *(literal(n) for n in (*inputs, *outputs))))
        result = verify_universal(parse(base+claim), MEANINGS)[0]
        assert result['status'] == 'valid', (name, result)
        rows[name] = dict(inputs=list(map(str, inputs)), outputs=list(map(str, outputs)), actual_senr_satisfied=True)
    assert rows['positive_density']['outputs'][:4] == rows['different_diagonal_split']['outputs'][:4]
    assert rows['positive_density']['outputs'][4:] != rows['different_diagonal_split']['outputs'][4:]
    assert rows['zero_density_nonzero_velocity']['outputs'][0] == '0'
    assert rows['zero_density_nonzero_velocity']['outputs'][1] != '0'
    try: rational_outputs((5, 3, F(5,4), 4, F(25,3), 0, 0))
    except ValueError: pass
    else: raise AssertionError('Singular input silently filled')
    return dict(cases=rows, singular_denominator_refused=True, diagonal_tuple_not_unique=True,
        explicit_rational_normalizations_only=True, premise_examples_not_physical_source_cases=True)


def build_report():
    files = build()
    for p, body in files.items(): assert (ROOT/p).read_text(encoding='utf-8') == body, p
    doc = document(); full = parse((ROOT/FULL).read_text(encoding='utf-8'))
    extracted = extract_document(full, roots=['senr'], statement_indices=[]).document
    assert doc['declarations'] == extracted['declarations']
    audit = audit_basis(doc, json.loads(files[BASIS])); audit.pop('definition_dependencies')
    for notation in ('full', 'compact'):
        formatted = format_graph(doc, notation)
        assert parse(formatted) == parse(transcribe(formatted, alphabet='v2')) == doc
    result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'noema', 'parse', '-i', str(ROOT/DOCUMENT)],
        check=True, capture_output=True, encoding='utf-8')
    assert json.loads(result.stdout) == doc
    inventory = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit = next(u for u in inventory['units'] if u['id'] == 'einstein-1905:u0236')
    math = next(m for m in inventory['math'] if m['id'] == 'M0390')
    paths = set(files) | {FULL, CORE, 'data/einstein-density-origins-basis-v1.json', 'data/density-formula-review-v11.json',
        'artifacts/written-units-v1/einstein-1905.json', 'docs/density-existence-v1.md',
        'scripts/check_density_existence.py', 'scripts/compose_density_existence.py', 'scripts/compose_density_origins.py',
        'scripts/compose_limits.py', 'scripts/check_real_products.py', 'scripts/check_moving_light_trip.py',
        'tests/test_density_existence.py', 'tests/test_rational_witnesses.py'}
    paths.update('noema/'+n+'.py' for n in ('rational_witnesses', 'polynomial_proofs', 'rational_proofs', 'grammar',
        'language', 'discourse', 'semantics', 'meaning_basis', 'extraction', 'script'))
    return dict(status='rational_density_output_existence_and_uniqueness_certified', document=DOCUMENT,
        source_document=FULL, audit=audit, proof=proofs(), examples=concrete_cases(),
        existing_declarations_extracted_unchanged=True, new_primitives=0, new_definitions=0,
        derived_statements=2, new_author_statements=0, roundtrips=True, cli_parse=True,
        solver_version=z3.get_version_string(), verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        alignment=dict(segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'], math_id='M0390', math_sha256=math['sha256'],
            status='partial_rational_existence_certificate', definitions=['senr', 'semp'])]),
        source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli = argparse.ArgumentParser(); cli.add_argument('--verify-only', action='store_true'); options = cli.parse_args()
    report = build_report()
    if options.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('Rational density outputs constructed uniquely; derivative splits remain nonunique')


if __name__ == '__main__': main()
