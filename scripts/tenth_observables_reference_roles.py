"""Closed candidate descriptions for the three observational arguments.

These projections preserve the original typed settings. Separate reference
lookups do not establish existence, uniqueness or a common set of witnesses.
"""
from copy import deepcopy

POTENTIAL = frozenset('eis4'+c for c in 'ghijklmnop')
MAGNETIC = frozenset('eis5'+c for c in 'abcdefghijklmnopqrs')

def _var(name):return dict(kind='variable', name=name)
def _call(name,*args):return dict(kind='call',symbol=name,arguments=list(args))


def build_roles(document):
    source={d['name']:d for d in document['declarations']}
    roles={}
    for content,predicate,peers in [('esb','er7',POTENTIAL),('esw','esp',MAGNETIC)]:
        node=source[content]['body']
        if node['kind']!='content' or node['body']['kind']!='call' or node['body']['symbol']!=predicate:
            raise ValueError('Observational setting content changed: '+content)
        arguments=node['body']['arguments'];parameters=source[predicate]['parameters']
        calls=[a['symbol'] for a in arguments if a['kind']=='call']
        if len(arguments)!=len(parameters) or any(calls.count(n)!=1 for n in peers):
            raise ValueError('Observational setting tuple changed')
        for arg,param in zip(arguments,parameters,strict=True):
            if arg['kind']=='call':
                if arg['arguments'] or source[arg['symbol']]['result']!=param['sort']:
                    raise ValueError('Observational setting argument type changed')
            elif arg!=_var(node['variable']) or param['sort']!='situation':
                raise ValueError('Unexpected observational context argument')
        for candidate in sorted(peers):
            witnesses=[name for name in calls if name in peers and name!=candidate]
            variables={name:'observedpeer'+chr(97+i) for i,name in enumerate(witnesses)}
            actual=[]
            for arg in arguments:
                if arg['kind']=='variable':actual.append(_var('observedcontext'))
                elif arg['symbol']==candidate:actual.append(_var('observedcandidate'))
                elif arg['symbol'] in variables:actual.append(_var(variables[arg['symbol']]))
                else:actual.append(deepcopy(arg))
            body=_call(predicate,*actual)
            for name in reversed(witnesses):
                body=dict(kind='exists',variable=variables[name],sort=deepcopy(source[name]['result']),body=body)
            roles[candidate]=dict(kind='definition',name='observedrole'+candidate,
                parameters=[dict(name='observedcandidate',sort=deepcopy(source[candidate]['result'])),
                            dict(name='observedcontext',sort='situation')],result='truth',body=body)

    charge=source['eq6']
    if [p['sort'] for p in charge['parameters']]!=['number','situation'] or charge['result']!='truth':
        raise ValueError('Charge background signature changed')
    variables={charge['parameters'][0]['name']:'observedscale',charge['parameters'][1]['name']:'observedcontext'}
    replaced=[]
    def replace(node):
        if isinstance(node,list):return [replace(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='variable':
            if node['name'] not in variables:raise ValueError('Unexpected charge background variable')
            return _var(variables[node['name']])
        if node.get('kind')=='call' and node['symbol']=='eis35':
            if node['arguments']:raise ValueError('Charge reference is no longer closed')
            replaced.append(node)
            return _var('observedcandidate')
        return {k:replace(v) for k,v in node.items()}
    body=replace(charge['body'])
    if len(replaced)!=1:raise ValueError('Charge record occurrence changed')
    roles['eis35']=dict(kind='definition',name='observedroleeis35',parameters=[
        dict(name='observedcandidate',sort='individual'),dict(name='observedcontext',sort='situation')],
        result='truth',body=dict(kind='exists',variable='observedscale',sort='number',body=body))
    return roles


def build_report():
    import hashlib,json
    from pathlib import Path
    from noema.constructed_discourse import normalize_document
    from noema.extraction import extract_document
    from noema.meaning_catalog import _references
    from scripts.check_manuscript_context import catalogs
    root=Path(__file__).resolve().parents[1];catalog=catalogs()['einstein-1905']
    source={d['name']:d for d in catalog.document['declarations']}
    roles=build_roles(catalog.document);graph={};dependencies=set()
    for name,role in roles.items():
        seen=set();pending=list(_references(role['body']))
        while pending:
            symbol=pending.pop()
            if symbol in seen:continue
            seen.add(symbol);pending.extend(_references(source[symbol].get('body'))-seen)
        if name in seen:raise ValueError('Self-referential observational role: '+name)
        graph[name]=sorted(seen&set(roles));dependencies.update(seen)
    if graph['eis35'] or any(graph[n] for n in POTENTIAL) or any(set(graph[n])!={'eis4m'} for n in MAGNETIC):
        raise ValueError('Unexpected observational role dependency')
    document=extract_document(catalog.document,roots=sorted(dependencies),statement_indices=[]).document
    document['declarations']+=list(roles.values());normalize_document(document)
    paths=set(catalog.source_sha256)|{catalog.document_path,'data/work-state.json',
        'scripts/tenth_observables_reference_roles.py','tests/test_tenth_observables_reference_roles.py',
        'noema/constructed_discourse.py','noema/constructed_semantics.py','noema/extraction.py',
        'noema/meaning_catalog.py','scripts/check_manuscript_context.py'}
    return dict(schema='noema-tenth-observables-reference-roles-1',
        status='closed_typed_roles_checked_against_full_source_dependencies',roles=30,
        potential_roles=10,magnetic_roles=19,charge_record_roles=1,
        role_dependency_graph=graph,normalized_source_closure=True,
        definition_sha256={n:hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest() for n,d in sorted(roles.items())},
        actual_svg_decoding_performed=False,document_integration_credit=0,
        limitations=['Candidate descriptions do not prove existence, uniqueness or joint consistency.',
            'Finite binding diagnostics do not prove laws over real or function domains.',
            'The full source argument still needs Native connection and actual SVG decoding.'],
        source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sorted(paths)})
