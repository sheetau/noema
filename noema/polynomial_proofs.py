"""A sufficient real-domain check for universal rational polynomial claims.

Only a leading universal rational prefix and a quantifier-free expanded matrix
are admitted. UNSAT over R proves validity over Q. SAT is a Q counterexample
only after every witness is rational and exact substitution falsifies the matrix.
No mixed-quantifier nonlinear formula is silently reinterpreted over the reals.
"""
from fractions import Fraction

from .discourse import normalize_document
from .rational_proofs import SIGNATURES
from .semantics import require


def verify_universal(document, interpretations, *, timeout_ms=10000, max_expansion=100000):
    import z3
    require(type(timeout_ms) is int and timeout_ms > 0, 'Invalid proof timeout')
    require(type(max_expansion) is int and max_expansion > 0, 'Invalid expansion budget')
    doc = normalize_document(document)
    declarations = {d['name']: d for d in doc['declarations']}
    primitives = {n: d for n, d in declarations.items() if d['kind'] == 'primitive'}
    require(isinstance(interpretations, dict) and set(interpretations) == set(primitives), 'Interpret every primitive explicitly')
    for name, meaning in interpretations.items():
        require(isinstance(meaning, str) and meaning in SIGNATURES, 'Unsupported polynomial interpretation')
        require((primitives[name]['parameters'], primitives[name]['result']) == SIGNATURES[meaning], 'Arithmetic signature mismatch')
    steps = 0

    def named(name, args):
        declaration = declarations[name]
        if declaration['kind'] == 'definition':
            return expr(declaration['body'], {p['name']: a for p, a in zip(declaration['parameters'], args, strict=True)})
        require(all(z3.is_arith(a) for a in args), 'Expected polynomial arguments')
        return {'less': lambda: args[0] < args[1], 'add': lambda: args[0] + args[1],
                'negate': lambda: -args[0], 'multiply': lambda: args[0] * args[1]}[interpretations[name]]()

    def expr(node, env):
        nonlocal steps
        steps += 1
        require(steps <= max_expansion, 'Polynomial expansion budget exceeded')
        kind = node['kind']
        if kind == 'variable':
            return env[node['name']]
        if kind == 'number':
            return z3.RealVal(f"{node['numerator']}/{node['denominator']}")
        if kind == 'call':
            return named(node['symbol'], [expr(a, env) for a in node['arguments']])
        if kind == 'function_ref':
            return lambda *args: named(node['symbol'], args)
        if kind == 'lambda':
            captured = dict(env)
            return lambda *args: expr(node['body'], {**captured, **{p['name']: a for p, a in zip(node['parameters'], args, strict=True)}})
        if kind == 'apply':
            function = expr(node['function'], env)
            require(callable(function), 'Expected expanded function')
            return function(*(expr(a, env) for a in node['arguments']))
        require(kind in ('not', 'and', 'or', 'implies', 'iff', 'equal'),
                'Expanded polynomial matrix must be quantifier-free')
        args = [expr(a, env) for a in node['arguments']]
        if kind == 'equal' and all(z3.is_arith(a) for a in args):
            return args[0] == args[1]
        require(all(z3.is_bool(a) for a in args), 'Expected Boolean polynomial formula; function equality is unsupported')
        return {'not': lambda: z3.Not(args[0]), 'and': lambda: z3.And(*args), 'or': lambda: z3.Or(*args),
                'implies': lambda: z3.Implies(*args), 'iff': lambda: args[0] == args[1], 'equal': lambda: args[0] == args[1]}[kind]()

    results = []
    for statement in doc['statements']:
        require(statement['kind'] == 'assert', 'Polynomial proof requires assertions')
        node, variables = statement['body'], {}
        while node['kind'] == 'forall':
            require(node['sort'] == 'number', 'Polynomial prefix quantifies rational numbers only')
            variables[node['variable']] = z3.Real(node['variable'])
            node = node['body']
        formula = expr(node, variables)
        require(z3.is_bool(formula), 'Expected polynomial assertion')
        solver = z3.SolverFor('QF_NRA')
        solver.set(timeout=timeout_ms)
        solver.add(z3.Not(formula))
        status = solver.check()
        result = {'status': 'unknown', 'reason': None, 'counterexample': None, 'matrix': formula.sexpr()}
        if status == z3.unsat:
            result['status'] = 'valid'
            result['reason'] = 'No real counterexample; therefore no rational counterexample'
        elif status == z3.unknown:
            result['reason'] = solver.reason_unknown()
        else:
            model = solver.model()
            values = {n: model.eval(v, model_completion=True) for n, v in variables.items()}
            if all(z3.is_rational_value(v) for v in values.values()):
                ground = z3.simplify(z3.substitute(formula, *[(variables[n], v) for n, v in values.items()]))
                if z3.is_false(ground):
                    result['status'] = 'invalid'
                    result['reason'] = 'Exact rational counterexample'
                    result['counterexample'] = {n: str(Fraction(v.numerator_as_long(), v.denominator_as_long())) for n, v in values.items()}
                else:
                    result['reason'] = 'Rational model did not certify a false matrix'
            else:
                result['reason'] = 'Real counterexample is not certified rational; no Q verdict'
        results.append(result)
    return results
