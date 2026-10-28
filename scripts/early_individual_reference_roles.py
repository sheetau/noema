"""Closed descriptions of the opening parameter, named Earth and hypothetical medium.

The roles explain candidates. Retrieval by a quoted role does not assert the
role, execute a propagation classification or establish physical existence.
"""
from scripts.shared_reference import definition
from scripts.shared_modality import call,v

CANDIDATES=('eisbo','eisbx','eisby')
ANCHORS=dict(eisbo='earlyfirstordertoken',eisbx='earlyearthtoken',eisby='earlymediumtoken')


def build_roles():
    x=v('candidate');s=v('context')
    propagation=dict(kind='quote',body=dict(kind='function_ref',symbol='radiationpropagation'))
    def both(*xs):
        result=xs[-1]
        for item in reversed(xs[:-1]):result=dict(kind='and',arguments=[item,result])
        return result
    def distinct(left,right):return dict(kind='not',arguments=[dict(kind='equal',arguments=[left,right])])
    bodies={
        'eisbo':both(call('signalvelocityratioparameter',x,propagation,s),
                    call('directionpreservingscalelimit',x,s),call('completeparameterdirections',x,s)),
        'eisbx':both(call('presentationholds',call('earlyearthtoken'),s),
                    call('nameapplies',call('earlyearthtoken'),call('earlyearthdesignation'),x,s),
                    distinct(call('earlyearthdesignation'),x)),
        'eisby':both(call('hypothesizedpropagationmedium',x,propagation,s),distinct(call('eisbx'),x))}
    return {n:definition('earlyrole'+n,[('candidate','individual'),('context','situation')],'truth',bodies[n])
            for n in CANDIDATES}


def dependency_graph():
    from noema.meaning_catalog import _references
    roles=build_roles();positions={n:i for i,n in enumerate(CANDIDATES)}
    graph={}
    for n,role in roles.items():
        dependencies=_references(role['body'])&set(CANDIDATES)
        if any(positions[d]>=positions[n] for d in dependencies):raise ValueError('Circular opening reference description')
        graph[n]=sorted(dependencies)
    return graph
