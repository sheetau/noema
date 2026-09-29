"""Check concrete tagged sums and exact scalar lemmas, not all real integrals."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.grammar import format_graph, number_word, parse
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import decode, encode
from scripts.compose_integrals import ROOT, composed
from scripts.compose_limits import v, call, app, op, both, quant, ZERO

REPORT = ROOT / 'reports/integrals-v1.json'
CLAIMS = ROOT / 'examples/v014/integral-scalar-claims.noema'
ARITHMETIC = {'aa': lambda a, b: a < b, 'ab': lambda a, b: a + b,
              'ac': lambda a: -a, 'ad': lambda a, b: a * b}
MEANINGS = {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'}
CELL = {'kind': 'function', 'parameters': ['number'], 'result': 'number'}


def cell_value(values):
    values = tuple(Fraction(value) for value in values)
    if len(values) != 3:
        raise ValueError('A tagged cell requires three fields')
    def field(index):
        if index not in (Fraction(0), Fraction(1), Fraction(2)):
            return Fraction(999)  # A total function; these other fields are immaterial.
        return values[int(index)]
    return FunctionValue(('number',), 'number', field)


def check_call(symbol, values, number=None):
    doc = parse(composed()[0])
    declaration = next(d for d in doc['declarations'] if d['name'] == symbol)
    model, arguments = dict(ARITHMETIC), []
    for index, (param, value) in enumerate(zip(declaration['parameters'], values, strict=True)):
        sort = param['sort']
        if isinstance(sort, dict) and sort['kind'] == 'sequence':
            value = SequenceValue(tuple(cell_value(cell) for cell in value), json.dumps(CELL, sort_keys=True, separators=(',', ':')))
        elif sort == CELL:
            value = (FunctionValue(('number',), 'number', value) if callable(value) else cell_value(value))
        else:
            value = Fraction(value)
        name = 'zz' + number_word(index)
        doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
        model[name] = lambda value=value: value
        arguments.append({'kind': 'call', 'symbol': name, 'arguments': []})
    body = {'kind': 'call', 'symbol': symbol, 'arguments': arguments}
    if number is not None:
        number = Fraction(number)
        body = {'kind': 'equal', 'arguments': [body, {'kind': 'number', 'numerator': number.numerator, 'denominator': number.denominator}]}
    doc['statements'] = [{'kind': 'ask', 'body': body}]
    return evaluate_document(doc, individuals=('one',), situations=('now',), primitives=model)[0]['value']


def partition_checks():
    results = {}
    def record(label, symbol, values, expected, number=None):
        actual = check_call(symbol, values, number)
        if actual != expected:
            raise ValueError('Tagged partition differs: ' + label)
        results[label] = {'expected': expected, 'actual': actual}
    for tag in (0, Fraction(1, 2), 1):
        record('tag_' + str(tag), 'ma', ((0, 1, tag),), True)
    for label, cell in [('outside_left', (0, 1, -1)), ('outside_right', (0, 1, 2)),
                        ('zero_width', (1, 1, 1)), ('negative_width', (1, 0, 0))]:
        record(label, 'ma', (cell,), False)
    halves = ((0, Fraction(1, 2), Fraction(1, 4)), (Fraction(1, 2), 1, Fraction(3, 4)))
    record('connected_partition', 'mb', (halves, 0, 1), True)
    record('gap', 'mb', (((0, Fraction(1, 4), 0), (Fraction(1, 2), 1, 1)), 0, 1), False)
    record('overlap', 'mb', (((0, Fraction(3, 4), 0), (Fraction(1, 2), 1, 1)), 0, 1), False)
    record('reversed_cells', 'mb', (tuple(reversed(halves)), 0, 1), False)
    record('duplicate_interval', 'mb', ((halves[0], halves[0], halves[1]), 0, 1), False)
    record('missing_end', 'mb', ((halves[0],), 0, 1), False)
    record('empty_is_not_positive_partition', 'mb', ((), 0, 1), False)
    record('wrong_lower_endpoint', 'mb', (halves, -1, 1), False)
    record('mesh_below_bound', 'mc', (halves, 1), True)
    record('mesh_equal_bound_is_not_strictly_below', 'mc', (halves, Fraction(1, 2)), False)
    record('negative_mesh_bound', 'mc', (halves, -1), False)
    record('empty_mesh_does_not_make_valid_partition', 'mc', ((), 1), True)
    record('empty_sum', 'md', ((), lambda x: x), True, 0)
    record('clock_rate_sum', 'md', (((0, 3, 2), (3, 10, 8)), lambda x: Fraction(4, 5)), True, 8)
    record('representative_point_changes_sum', 'md', (((0, 1, 0),), lambda x: x), False, 1)
    for size in (1, 2, 3, 4, 8, 12):
        for position, offset in (('left', Fraction(0)), ('middle', Fraction(1, 2)), ('right', Fraction(1))):
            cells = tuple((Fraction(i, size), Fraction(i + 1, size), (i + offset) / size) for i in range(size))
            record(f'{size}_{position}_partition', 'mb', (cells, 0, 1), True)
            record(f'{size}_{position}_constant', 'md', (cells, lambda x: Fraction(7)), True, 7)
            exact_sum = Fraction(1, 2) + (offset - Fraction(1, 2)) / size
            record(f'{size}_{position}_identity', 'md', (cells, lambda x: x), True, exact_sum)
            record(f'{size}_{position}_affine', 'md', (cells, lambda x: 2 * x + 3), True, 2 * exact_sum + 3)
    return results


def scalar_claims():
    add = lambda a, b: call('ab', a, b)
    neg = lambda a: call('ac', a)
    sub = lambda a, b: add(a, neg(b))
    mul = lambda a, b: call('ad', a, b)
    sq = lambda a: mul(a, a)
    lt = lambda a, b: call('aa', a, b)
    le = lambda a, b: op('u', lt(b, a))
    eq = lambda a, b: op('e', a, b)
    half = 'n p b c'
    a, b, c, tag, slope, intercept, delta = [v(n) for n in ('a', 'b', 'c', 'tag', 'slope', 'intercept', 'delta')]
    area = lambda left, right: add(mul(mul(half, slope), sub(sq(right), sq(left))), mul(intercept, sub(right, left)))
    error = sub(mul(sub(b, a), add(mul(slope, tag), intercept)), area(a, b))
    identity_error = sub(mul(sub(b, a), tag), mul(half, sub(sq(b), sq(a))))
    bound = mul(mul(half, delta), sub(b, a))
    specs = {
        'record_constructor_left_field': ('a b c', eq(app(call('mg', a, b, c), ZERO), a)),
        'record_constructor_right_field': ('a b c', eq(app(call('mg', a, b, c), 'n p b b'), b)),
        'record_constructor_tag_field': ('a b c', eq(app(call('mg', a, b, c), 'n p c b'), c)),
        'constant_sums_telescope': ('a b c intercept', eq(add(mul(intercept, sub(b, a)), mul(intercept, sub(c, b))), mul(intercept, sub(c, a)))),
        'affine_areas_telescope': ('a b c slope intercept', eq(add(area(a, b), area(b, c)), area(a, c))),
        'affine_cell_error_identity': ('a b tag slope intercept', eq(error, mul(mul(sub(b, a), slope), sub(tag, mul(half, add(a, b)))))),
        'identity_cell_error_bounded_by_mesh': ('a b tag delta', op('y', both(lt(a, b), le(a, tag), le(tag, b), lt(sub(b, a), delta)),
            both(le(neg(bound), identity_error), le(identity_error, bound)))),
        'error_bounds_add': ('left right firstbound lastbound', op('y', both(
            le(neg(v('firstbound')), v('left')), le(v('left'), v('firstbound')),
            le(neg(v('lastbound')), v('right')), le(v('right'), v('lastbound'))),
            both(le(neg(add(v('firstbound'), v('lastbound'))), add(v('left'), v('right'))),
                 le(add(v('left'), v('right')), add(v('firstbound'), v('lastbound')))))),
        'mesh_bound_scales_with_total_width': ('a b c delta', eq(add(mul(delta, sub(b, a)), mul(delta, sub(c, b))), mul(delta, sub(c, a)))),
        'affine_orientation_reverses_sign': ('a b slope intercept', eq(area(b, a), neg(area(a, b)))),
        'affine_zero_interval_has_zero_area': ('a slope intercept', eq(area(a, a), ZERO)),
    }
    rows = {}
    for name, (parameters, body) in specs.items():
        for parameter in reversed(parameters.split()):
            body = quant('f', parameter, 'b', body)
        rows[name] = 's[' + body + '].'
    return rows


def claim_document():
    doc = parse(composed()[0])
    doc['declarations'] = [d for d in doc['declarations'] if d['kind'] == 'primitive' or d['name'] == 'mg']
    text = format_graph(doc, 'compact') + '\n' + '\n'.join(scalar_claims().values())
    return format_graph(parse(text), 'compact') + '\n'


def proof_checks():
    rows = verify_universal(parse(claim_document()), MEANINGS, timeout_ms=15000)
    results = dict(zip(scalar_claims(), rows, strict=True))
    if any(row['status'] != 'valid' for row in rows):
        raise ValueError('Integral scalar proof failed: ' + str({name: row['status'] for name, row in results.items()}))
    return results


def refusal_checks():
    base = composed()[0]
    formulas = {
        'all_partitions': 's[f partition j[h[b] b][e[v partition][v partition]]].',
        'integral_is_not_a_finite_sum': 's[k me[n p a b n p b b i[x b][v x] n p b c]].',
    }
    results = {}
    for name, formula in formulas.items():
        try:
            evaluate_document(parse(base + formula), individuals=('one',), situations=('now',), primitives=ARITHMETIC)
        except ValueError as error:
            if ('unbounded sequence domain' if name == 'all_partitions' else 'rational number domain') not in str(error):
                raise
            results[name] = str(error)
        else:
            raise ValueError('An unbounded integral was accepted by finite sampling')
    return results


def example_document():
    doc = parse(composed()[0])
    doc['declarations'] = [d for d in doc['declarations'] if d['kind'] == 'primitive' or d['name'] in ('ma', 'mb', 'mc', 'md', 'mg')]
    return format_graph(parse(format_graph(doc, 'compact') + '\n' + '\n'.join([
        's[k mb[l[h[b] b][k mg[n p a b n p d b n p c b] k mg[n p d b n p k b n p i b]] n p a b n p k b]].',
        's[e[k md[l[h[b] b][k mg[n p a b n p d b n p c b] k mg[n p d b n p k b n p i b]] i[t b][n p e f]]][n p i b]].',
        's[e[k md[l[h[b] b][k mg[n p a b n p b b n p b c]] i[t b][v t]]][n p b c]].',
        's[e[k md[l[h[b] b][k mg[n p a b n p b b n p a b]] i[t b][v t]]][n p a b]].',
        's[e[k md[l[h[b] b][k mg[n p a b n p b b n p b b]] i[t b][v t]]][n p b b]].',
    ])), 'compact') + '\n'


def example_checks():
    text = example_document()
    if (ROOT / 'examples/v014/tagged-sums.noema').read_text(encoding='utf-8') != text:
        raise ValueError('Stored tagged sum example differs')
    rows = evaluate_document(parse(text), individuals=('one',), situations=('now',), primitives=ARITHMETIC)
    if not all(row['value'] for row in rows):
        raise ValueError('Noema record construction or sum failed')
    return len(rows)


def source_alignment():
    from scripts.check_limits import source_alignment as limits_alignment
    row = limits_alignment()
    row.update(definitions=['ne', 'ng', 'nh'], scope='conditional differentiable closed-curve rate and integral model')
    row['uncovered'] = ['physical acceleration law', 'clock observations and units', 'polygonal convergence theorem',
                        'full source smoothness interpretation', 'conditional authorial assertion', 'Earth clocks']
    return row


def build_report():
    import z3
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or CLAIMS.read_text(encoding='utf-8') != claim_document():
        raise ValueError('Stored integral document differs')
    doc = parse(text)
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Integral roundtrip differs')
    files = [basis['document'], 'data/integrals-basis-v1.json', CLAIMS.relative_to(ROOT).as_posix(),
             'scripts/compose_integrals.py', 'scripts/check_integrals.py', 'scripts/compose_limits.py',
             'scripts/check_limits.py', 'examples/v011/limits.noema', 'data/limits-basis-v1.json', 'examples/v014/tagged-sums.noema',
             'noema/discourse.py', 'noema/finite_semantics.py', 'noema/polynomial_proofs.py', 'noema/rational_proofs.py']
    return {'status': 'partial_tagged_integral_and_curve_rate_library', 'basis_audit': audit_basis(doc, basis),
            'roundtrips': True, 'partition_checks': partition_checks(), 'scalar_proofs': proof_checks(), 'noema_example_checks': example_checks(),
            'finite_refusals': refusal_checks(), 'z3_version': z3.get_version_string(), 'source_alignment': source_alignment(),
            'full_integral_theorems_machine_verified': False, 'real_cut_calculus_machine_verified': False,
            'physical_curve_clock_law_derived': False, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    cli.add_argument('--finite-only', action='store_true')
    args = cli.parse_args()
    if args.finite_only:
        print(f'{len(partition_checks())} finite partition checks; {example_checks()} Noema examples; {len(refusal_checks())} unbounded evaluations refused')
        return
    if not args.verify_only:
        for path, text in ((CLAIMS, claim_document()), (ROOT / 'examples/v014/tagged-sums.noema', example_document())):
            if path.exists():
                if path.read_text(encoding='utf-8') != text:
                    raise ValueError('Stored integral claims or examples differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(text)
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Integral report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Tagged sums and scalar lemmas checked; full integral and physical curve laws are not claimed proved')


if __name__ == '__main__':
    main()
