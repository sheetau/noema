"""Optional, bounded Z3 verification of the linear rational arithmetic fragment.

Definitions/lambdas are unfolded from the checked Noema document. Only rational
affine terms and Boolean connectives/quantifiers over rationals are admitted.
No uninterpreted predicates, finite sampling or nonlinear Real-for-Q shortcut.
"""
from dataclasses import dataclass
from fractions import Fraction

from .discourse import normalize_document
from .semantics import require


@dataclass(frozen=True)
class Affine:
    constant: Fraction
    coefficients: dict

    def scaled(self, value):
        return Affine(self.constant * value, {n: a * value for n, a in self.coefficients.items() if a * value})

    def plus(self, other):
        names = self.coefficients.keys() | other.coefficients.keys()
        coefficients = {n: self.coefficients.get(n, 0) + other.coefficients.get(n, 0) for n in sorted(names)}
        return Affine(self.constant + other.constant, {n: a for n, a in coefficients.items() if a})


SIGNATURES = {'less': (['number', 'number'], 'truth'), 'add': (['number', 'number'], 'number'),
              'negate': (['number'], 'number'), 'multiply': (['number', 'number'], 'number')}


def verify(document, interpretations, *, timeout_ms=10000, max_expansion=100000):
    """Return valid/invalid/unknown for each unconditionally asserted formula.

    `interpretations` assigns declared primitives to explicit arithmetic meanings.
    Validity is checked by unsatisfiability of the negation, with a timeout.
    """
    import z3
    require(type(timeout_ms) is int and timeout_ms > 0, 'Invalid proof timeout')
    require(type(max_expansion) is int and max_expansion > 0, 'Invalid expansion budget')
    doc = normalize_document(document)
    declarations = {d['name']: d for d in doc['declarations']}
    primitives = {d['name']: d for d in doc['declarations'] if d['kind'] == 'primitive'}
    require(isinstance(interpretations, dict) and set(interpretations) == set(primitives), 'Interpret every primitive explicitly')
    for name, meaning in interpretations.items():
        require(isinstance(meaning, str) and meaning in SIGNATURES, 'Unsupported arithmetic interpretation')
        require((primitives[name]['parameters'], primitives[name]['result']) == SIGNATURES[meaning], 'Arithmetic signature mismatch')
    steps, serial = 0, 0
    variables = {}

    def rational(value):
        return z3.RealVal(f'{value.numerator}/{value.denominator}')

    def arithmetic(term):
        require(isinstance(term, Affine), 'Expected affine rational term')
        return rational(term.constant) + sum((rational(a) * variables[n] for n, a in sorted(term.coefficients.items())), z3.RealVal(0))

    def named(name, args):
        declaration = declarations[name]
        if declaration['kind'] == 'definition':
            return expr(declaration['body'], {p['name']: a for p, a in zip(declaration['parameters'], args, strict=True)})
        meaning = interpretations[name]
        require(all(isinstance(a, Affine) for a in args), 'Arithmetic argument must be affine')
        if meaning == 'less':
            return arithmetic(args[0]) < arithmetic(args[1])
        if meaning == 'add':
            return args[0].plus(args[1])
        if meaning == 'negate':
            return args[0].scaled(Fraction(-1))
        require(not args[0].coefficients or not args[1].coefficients, 'Nonlinear rational arithmetic is not supported')
        return args[1].scaled(args[0].constant) if not args[0].coefficients else args[0].scaled(args[1].constant)

    def expr(node, env):
        nonlocal steps, serial
        steps += 1
        require(steps <= max_expansion, 'Arithmetic expansion budget exceeded')
        kind = node['kind']
        if kind == 'variable':
            return env[node['name']]
        if kind == 'number':
            return Affine(Fraction(node['numerator'], node['denominator']), {})
        if kind == 'function_ref':
            return lambda *args: named(node['symbol'], args)
        if kind == 'lambda':
            captured = dict(env)
            return lambda *args: expr(node['body'], {**captured, **{p['name']: a for p, a in zip(node['parameters'], args, strict=True)}})
        if kind == 'apply':
            function = expr(node['function'], env)
            require(callable(function), 'Expected expanded function')
            return function(*(expr(a, env) for a in node['arguments']))
        if kind == 'call':
            return named(node['symbol'], [expr(a, env) for a in node['arguments']])
        if kind in ('forall', 'exists'):
            require(node['sort'] == 'number', 'Only rational quantification is supported')
            symbol = 'r' + str(serial)
            serial += 1
            variable = variables[symbol] = z3.Real(symbol)
            body = expr(node['body'], {**env, node['variable']: Affine(Fraction(0), {symbol: Fraction(1)})})
            require(z3.is_bool(body), 'Expected a formula')
            return z3.ForAll([variable], body) if kind == 'forall' else z3.Exists([variable], body)
        require(kind in ('not', 'and', 'or', 'implies', 'iff', 'equal'), 'Expression is outside rational proof fragment')
        args = [expr(a, env) for a in node['arguments']]
        if kind == 'equal' and isinstance(args[0], Affine):
            return arithmetic(args[0]) == arithmetic(args[1])
        require(all(z3.is_bool(a) for a in args), 'Only arithmetic or truth equality is supported; functions need pointwise comparison')
        return {'not': lambda: z3.Not(args[0]), 'and': lambda: z3.And(*args), 'or': lambda: z3.Or(*args),
                'implies': lambda: z3.Implies(*args), 'iff': lambda: args[0] == args[1],
                'equal': lambda: args[0] == args[1]}[kind]()

    results = []
    for statement in doc['statements']:
        require(statement['kind'] == 'assert', 'Proof input requires explicit assertions, without assumption blocks')
        formula = expr(statement['body'], {})
        require(z3.is_bool(formula), 'Expected an assertion formula')
        solver = z3.Solver()
        solver.set(timeout=timeout_ms)
        solver.add(z3.Not(formula))
        result = solver.check()
        results.append({'status': 'valid' if result == z3.unsat else 'invalid' if result == z3.sat else 'unknown',
                        'reason': solver.reason_unknown() if result == z3.unknown else None,
                        'formula': formula.sexpr()})
    return results
