"""Check expanded first-order individual/situation/Boolean assertions.

Individual and situation domains are nonempty, separate, and not finite samples.
Higher-order definitions may expand to first-order formulas; quantification over
functions, function equality, arithmetic, descriptions and content are rejected.
General quantified logic is undecidable, so unknown remains inconclusive.
"""
from .discourse import normalize_document
from .semantics import require


def verify(document, *, timeout_ms=10000, max_expansion=100000):
    import z3
    require(type(timeout_ms) is int and timeout_ms>0, 'Invalid first-order proof timeout')
    require(type(max_expansion) is int and max_expansion>0, 'Invalid first-order expansion budget')
    doc=normalize_document(document)
    declarations={d['name']:d for d in doc['declarations']}
    individual=z3.DeclareSort('NoemaIndividual')
    situation=z3.DeclareSort('NoemaSituation')
    uses_situations=False
    def scalar_sort(value):
        nonlocal uses_situations
        require(isinstance(value,str) and value in ('individual','situation','truth'),
            'First-order proof supports individual, situation and truth sorts only')
        if value=='situation':uses_situations=True
        return {'individual':individual,'situation':situation,'truth':z3.BoolSort()}[value]
    primitives={}
    for name,d in declarations.items():
        if d['kind']=='primitive':
            signature=[scalar_sort(s) for s in [*d['parameters'],d['result']]]
            primitives[name]=z3.Function('p_'+name,*signature)
    steps=0;bound_counter=0
    def named(name,args):
        d=declarations[name]
        if d['kind']=='definition':
            return expression(d['body'],{p['name']:a for p,a in zip(d['parameters'],args,strict=True)})
        require(all(z3.is_expr(a) for a in args),'First-order primitive received a function')
        return primitives[name](*args)
    def expression(node,env):
        nonlocal steps,bound_counter
        steps+=1
        require(steps<=max_expansion,'First-order expansion budget exceeded')
        kind=node['kind']
        if kind=='variable':return env[node['name']]
        if kind=='call':return named(node['symbol'],[expression(a,env) for a in node['arguments']])
        if kind=='function_ref':return lambda *args:named(node['symbol'],args)
        if kind=='lambda':
            captured=dict(env)
            return lambda *args:expression(node['body'],{**captured,**{p['name']:a for p,a in zip(node['parameters'],args,strict=True)}})
        if kind=='apply':
            function=expression(node['function'],env)
            require(callable(function),'Expected expanded first-order function')
            return function(*(expression(a,env) for a in node['arguments']))
        if kind in ('forall','exists'):
            sort=scalar_sort(node['sort']);bound_counter+=1
            variable=z3.Const('q_'+str(bound_counter),sort)
            body=expression(node['body'],{**env,node['variable']:variable})
            require(z3.is_bool(body),'Expected quantified Boolean body')
            return (z3.ForAll if kind=='forall' else z3.Exists)([variable],body)
        require(kind in ('not','and','or','implies','iff','equal'),
            'Unsupported first-order expression: '+kind)
        args=[expression(a,env) for a in node['arguments']]
        if kind=='equal':
            require(all(z3.is_expr(a) for a in args),'First-order function equality is unsupported')
            require(args[0].sort()==args[1].sort(),'First-order equality sorts differ')
            return args[0]==args[1]
        require(all(z3.is_bool(a) for a in args),'Expected first-order Boolean operands')
        return {'not':lambda:z3.Not(args[0]),'and':lambda:z3.And(*args),'or':lambda:z3.Or(*args),
            'implies':lambda:z3.Implies(*args),'iff':lambda:args[0]==args[1]}[kind]()
    results=[]
    for statement in doc['statements']:
        require(statement['kind']=='assert','First-order proof requires assertions')
        formula=expression(statement['body'],{})
        require(z3.is_bool(formula),'Expected first-order assertion')
        solver=z3.Solver();solver.set(timeout=timeout_ms);solver.add(z3.Not(formula));status=solver.check()
        row={'status':'unknown','reason':None,'countermodel':None,'formula':formula.sexpr()}
        if status==z3.unsat:
            domains='individual and situation' if uses_situations else 'individual'
            row.update(status='valid',reason=f'Negation is unsatisfiable over arbitrary nonempty {domains} domains')
        elif status==z3.sat:
            row.update(status='invalid',reason='A first-order countermodel exists',countermodel=solver.model().sexpr())
        else:row['reason']=solver.reason_unknown()
        results.append(row)
    return results
