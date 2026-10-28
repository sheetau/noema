"""Check typed Native roles, then diagnose one witness binding at a time.

The diagnostic erases numeric/function sorts to distinguishing individuals,
fixes other witnesses, and pins the varied witness with an explicit guard.
It is a binding diagnostic, not a model or proof over real/function domains.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import renamed
from scripts import check_einstein_tenth_motion_visible as check

ROLES=('eisxh','eisxt','eisxv','eisxy','eisxz','eisx2','eisx3','eisxg','eisyn')
COUNTS={}
def var(n):return dict(kind='variable',name=n)
def call(n,*xs):return dict(kind='call',symbol=n,arguments=list(xs))
def both(a,b):return dict(kind='and',arguments=[a,b])
def number(n):return dict(kind='number',numerator=n,denominator=1)
def forbidden(*args):raise ValueError('Unspecified binding diagnostic input')


@lru_cache(None)
def expected_roles():
    # Reconstruct from original predicates and their public argument positions,
    # independently of the connector's ROLE_DEFINITIONS.
    source={d['name']:d for d in check.catalogs()['einstein-1905'].document['declarations']}
    base=source['ek34']['parameters']
    assert [p['name'] for p in base]==['v'+c for c in 'abcdefghijklmnopqrstuvwxyz234567']+['vba']
    peers=('eisxy','eisxz','eisx2','eisx3');result={}
    for old in ROLES:
        fixed={'vd':var('context')};extra=[]
        if old=='eisxh':fixed.update(va=call('ra'),vn=var('candidate'))
        if old=='eisxv':fixed.update(va=call('ra'),vo=var('candidate'))
        args=[fixed.get(p['name'],var(p['name'])) for p in base]
        witnesses=[p for p in base if p['name'] not in fixed]
        if old=='eisxh':body=both(call('ek3v',*args),call('ek4m',args[15],args[16]))
        elif old=='eisxt':body=both(call('ek34',*args),both(call('ek4m',args[15],args[16]),call('ek4o',*args[17:21],var('candidate'))))
        elif old=='eisxv':body=call('ek56',*args)
        elif old in peers:
            values=[]
            for index,peer in enumerate(peers):
                name='peer'+'abcd'[index]
                values.append(var('candidate') if peer==old else var(name))
                if peer!=old:extra.append(dict(name=name,sort=source[peer]['result']))
            body=both(call('ek6f',*args),call('ek5w',*args,values[0],call('tc'),*values[1:]))
        elif old=='eisxg':
            witnesses=[]
            body=both(call('eisdv',call('eisxm'),var('candidate'),call('eispb'),call('eirf'),number(2),number(10),var('context')),
                dict(kind='not',arguments=[dict(kind='equal',arguments=[var('candidate'),call('eispb')])]))
        else:
            witnesses=[];body=call('ele',var('candidate'),var('context'))
        for p in reversed(witnesses+extra):body=dict(kind='exists',variable=p['name'],sort=p['sort'],body=body)
        role=dict(kind='definition',name='bindingrole',parameters=[dict(name='candidate',sort=source[old]['result']),dict(name='context',sort='situation')],result='truth',body=body)
        dependencies=[]
        for n in sorted(_references(body)):
            d=source[n]
            dependencies.append(dict(kind='primitive',name=n,
                parameters=[p['sort'] for p in d['parameters']] if d['kind']=='definition' else d['parameters'],result=d['result']))
        mapping=check.names()|{n:check.vocabulary()._symbols[p] for n,p in check.RELATIONS.items()}|check.mapping()
        mapping['bindingrole']=check.reference_roles()[old]
        normalized=normalize_document(renamed(dict(schema_version='0.16',lexicon_version='0.16',declarations=dependencies+[role],statements=[]),mapping))
        result[old]=normalized
    return result


def replace_variables(node,values):
    if isinstance(node,list):return [replace_variables(x,values) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name'] in values:return deepcopy(values[node['name']])
    return {k:replace_variables(x,values) for k,x in node.items()}


@pytest.mark.parametrize('old',ROLES)
def test_each_role_witness_and_relation_argument_binding(old):
    recovered={d['name']:d for d in check.restored()['document']['declarations']}
    expected=deepcopy(expected_roles()[old]);role=expected['declarations'][-1]
    actual=deepcopy(recovered[check.reference_roles()[old]])
    # Preserve and compare the complete real types and the native body first.
    assert actual==role,('Typed Native role differs from source predicate projection',old)
    binders=[];leaf=actual['body']
    while leaf['kind']=='exists':
        binders.append((leaf['variable'],leaf['sort']));leaf=leaf['body']
    assert len(binders)=={'eisxh':30,'eisxt':32,'eisxv':30,'eisxy':35,'eisxz':35,'eisx2':35,'eisx3':35,'eisxg':0,'eisyn':0}[old]
    constants={d['name']:d for d in expected['declarations'][:-1] if not d['parameters']}
    predicates={d['name']:d for d in expected['declarations'][:-1] if d['parameters']}
    constant_values={n:'constant'+str(i) for i,n in enumerate(constants)}
    individuals=('fixed','chosen','candidate','wrong',*constant_values.values())
    assert len(individuals)<=8
    cases=0;tested_slots=set()
    # One existential remains; all other witnesses are explicitly instantiated.
    for selected,_ in binders or [(None,None)]:
        env={p['name']:value for p,value in zip(role['parameters'],('candidate','context'),strict=True)}
        env.update({n:'chosen' if n==selected else 'fixed' for n,_ in binders})
        rows={}
        def ground(x):
            if x['kind']=='variable':return env[x['name']]
            if x['kind']=='number':return Q(x['numerator'],x['denominator'])
            assert x['kind']=='call' and not x['arguments']
            return constant_values[x['symbol']]
        def collect(x):
            if x['kind']=='call' and x['arguments']:
                rows.setdefault(x['symbol'],set()).add(tuple(ground(a) for a in x['arguments']))
            for a in x.get('arguments',[]):collect(a)
        # Expected rows come from the independently reconstructed specification.
        expected_leaf=role['body']
        while expected_leaf['kind']=='exists':expected_leaf=expected_leaf['body']
        collect(expected_leaf)
        substitutions={n:call('bindingfixed') for n,_ in binders if n!=selected}
        diagnostic_body=replace_variables(leaf,substitutions)
        if selected is not None:
            diagnostic_body=dict(kind='exists',variable=selected,sort='individual',body=both(
                dict(kind='equal',arguments=[var(selected),call('bindingchosen')]),diagnostic_body))
        diagnostic=deepcopy(actual);diagnostic['body']=diagnostic_body
        diagnostic['parameters'][0]['sort']='individual'
        declarations=[]
        for d in expected['declarations'][:-1]:
            d=deepcopy(d)
            # Projection roles only pass witnesses to predicates. Erase their
            # opaque sorts for binding checks; section literal numbers stay typed.
            d['parameters']=[s if s in ('situation','number') and old=='eisxg' or s=='situation' else 'individual' for s in d['parameters']]
            if not d['parameters']:d['result']='individual'
            declarations.append(d)
        declarations += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in
            [('bindingfixed','individual'),('bindingchosen','individual'),('bindingcandidate','individual'),('bindingcontext','situation')]]
        declarations.append(diagnostic)
        doc=dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,
            statements=[dict(kind='ask',body=call(actual['name'],call('bindingcandidate'),call('bindingcontext')))])
        model={n:(lambda value=value:value) for n,value in constant_values.items()}
        model.update(bindingfixed=lambda:'fixed',bindingchosen=lambda:'chosen',bindingcandidate=lambda:'candidate',bindingcontext=lambda:'context')
        def evaluate(table):
            handlers=model|{n:(lambda *xs,allowed=allowed:xs in allowed) for n,allowed in table.items()}
            return evaluate_document(doc,individuals=individuals,situations=('context','wrongcontext'),primitives=handlers,
                memoize_definitions=True,memoize_expressions=True)[0]['value']
        assert evaluate(rows),(old,selected,'positive');cases+=1
        for n,allowed in rows.items():
            for row in allowed:
                assert not evaluate(rows|{n:allowed-{row}}),(old,selected,n,'missing');cases+=1
                for slot,value in enumerate(row):
                    wrong=Q(99) if isinstance(value,Q) else ('wrongcontext' if value=='context' else 'wrong')
                    changed=row[:slot]+(wrong,)+row[slot+1:]
                    assert not evaluate(rows|{n:(allowed-{row})|{changed}}),(old,selected,n,slot)
                    tested_slots.add((selected,n,slot));cases+=1
        if selected is not None:assert any('chosen' in row for allowed in rows.values() for row in allowed)
    COUNTS[old]=dict(witnesses=len(binders),distinct_argument_slots=len(tested_slots),cases=cases,
        original_typed_body_compared=True,diagnostic_sort_erasure=True,other_witnesses_instantiated=True,
        one_guarded_witness_at_a_time=True,full_real_domain_proof=False)
