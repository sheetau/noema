"""Certify supplied rational witnesses, never infer Q existence from R existence.

The admitted shape is forall rational inputs: premise => exists rational outputs:
matrix. Witnesses contain rational constants, input variables and field operations.
All division denominators and the substituted matrix are checked under the actual
premise. Closure of Q then supplies witnesses for every rational input satisfying
that premise. A failed certificate is not a disproof of the existential theorem.
"""
from .discourse import normalize_document
from .rational_proofs import SIGNATURES
from .semantics import require


def verify_witnesses(document, interpretations, witnesses, *, timeout_ms=10000, max_expansion=100000):
    import z3
    require(type(timeout_ms) is int and timeout_ms > 0, 'Invalid proof timeout')
    require(type(max_expansion) is int and max_expansion > 0, 'Invalid expansion budget')
    doc = normalize_document(document)
    require(len(doc['statements']) == 1 and doc['statements'][0]['kind'] == 'assert', 'Expected one asserted existence claim')
    declarations = {d['name']: d for d in doc['declarations']}
    primitives = {n: d for n, d in declarations.items() if d['kind'] == 'primitive'}
    require(isinstance(interpretations, dict) and set(interpretations) == set(primitives), 'Interpret every primitive explicitly')
    for name, meaning in interpretations.items():
        require(isinstance(meaning, str) and meaning in SIGNATURES, 'Unsupported arithmetic interpretation')
        require((primitives[name]['parameters'], primitives[name]['result']) == SIGNATURES[meaning], 'Arithmetic signature mismatch')
    node = doc['statements'][0]['body']; inputs = {}
    while node['kind'] == 'forall':
        require(node['sort'] == 'number' and node['variable'] not in inputs, 'Expected distinct rational inputs')
        inputs[node['variable']] = z3.Real(node['variable']); node = node['body']
    require(node['kind'] == 'implies', 'Expected premise and existential conclusion')
    premise, node = node['arguments']; outputs = []
    while node['kind'] == 'exists':
        require(node['sort'] == 'number' and node['variable'] not in inputs and node['variable'] not in outputs,
                'Expected distinct rational outputs')
        outputs.append(node['variable']); node = node['body']
    require(outputs and isinstance(witnesses, dict) and set(witnesses) == set(outputs), 'Supply exactly the existential witnesses')
    steps = 0; denominators = []

    def tick():
        nonlocal steps
        steps += 1
        require(steps <= max_expansion, 'Witness expansion budget exceeded')

    def certificate(term):
        tick()
        require(isinstance(term, list) and term and isinstance(term[0], str), 'Malformed rational witness term')
        kind = term[0]
        if kind == 'variable':
            require(len(term) == 2 and isinstance(term[1], str) and term[1] in inputs, 'Witness may reference only universal inputs')
            return inputs[term[1]]
        if kind == 'number':
            require(len(term) == 3 and type(term[1]) is int and type(term[2]) is int and term[2] > 0, 'Expected exact rational constant')
            return z3.RealVal(str(term[1])+'/'+str(term[2]))
        arities = {'add': 2, 'negate': 1, 'multiply': 2, 'divide': 2}
        require(kind in arities and len(term) == arities[kind]+1, 'Unsupported rational witness operation')
        args = [certificate(t) for t in term[1:]]
        if kind == 'divide': denominators.append(args[1])
        return {'add': lambda: args[0]+args[1], 'negate': lambda: -args[0],
                'multiply': lambda: args[0]*args[1], 'divide': lambda: args[0]/args[1]}[kind]()

    def expr(node, env):
        tick(); kind = node['kind']
        if kind == 'variable': return env[node['name']]
        if kind == 'number': return z3.RealVal(str(node['numerator'])+'/'+str(node['denominator']))
        if kind == 'call':
            args = [expr(a, env) for a in node['arguments']]; decl = declarations[node['symbol']]
            if decl['kind'] == 'definition':
                return expr(decl['body'], {p['name']: a for p, a in zip(decl['parameters'], args, strict=True)})
            require(all(z3.is_arith(a) for a in args), 'Expected arithmetic arguments')
            return {'less': lambda: args[0] < args[1], 'add': lambda: args[0]+args[1],
                    'negate': lambda: -args[0], 'multiply': lambda: args[0]*args[1]}[interpretations[node['symbol']]]()
        require(kind in ('not', 'and', 'or', 'implies', 'iff', 'equal'), 'Expected quantifier-free polynomial premise and matrix')
        args = [expr(a, env) for a in node['arguments']]
        if kind == 'equal' and all(z3.is_arith(a) for a in args): return args[0] == args[1]
        require(all(z3.is_bool(a) for a in args), 'Expected Boolean formula')
        return {'not': lambda: z3.Not(args[0]), 'and': lambda: z3.And(*args), 'or': lambda: z3.Or(*args),
                'implies': lambda: z3.Implies(*args), 'iff': lambda: args[0] == args[1], 'equal': lambda: args[0] == args[1]}[kind]()

    hypothesis = expr(premise, inputs)
    substitutions = {n: certificate(witnesses[n]) for n in outputs}
    matrix = expr(node, inputs | substitutions)
    require(z3.is_bool(hypothesis) and z3.is_bool(matrix), 'Expected a Boolean premise and matrix')
    solver = z3.SolverFor('QF_NRA'); solver.set(timeout=timeout_ms)
    solver.add(hypothesis, z3.Not(z3.And(*(d != 0 for d in denominators), matrix)))
    status = solver.check()
    result = dict(status='uncertified', universal_inputs=list(inputs), existential_outputs=outputs,
        denominator_obligations=len(denominators), rational_closure_checked=True,
        premise_satisfiability_proved=False, theorem_disproved=False)
    if status == z3.unsat:
        result.update(status='valid', reason='All supplied rational terms are defined and satisfy the actual matrix under the premise')
    elif status == z3.unknown:
        result.update(status='unknown', reason=solver.reason_unknown())
    else:
        result['reason'] = 'Supplied terms are not certified on the real extension; no verdict against rational existence'
    return result
