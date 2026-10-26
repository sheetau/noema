"""Expose a source definition's contextual inputs without asserting a reading.

This produces a conditional template, not a resolved manuscript instance.
Quoted contextual names and dependencies needing implicit context are rejected.
"""
from copy import deepcopy
from noema.constructed_discourse import normalize_document, function_sort
from noema.meaning_catalog import _references
from scripts.shared_modality import renamed
from scripts.visible_lexical_script import require


def abstract(document, target, names, roles):
    source = normalize_document(document)
    declarations = {d['name']: d for d in source['declarations']}
    selected = declarations[target]
    require(selected['kind'] == 'definition' and not selected['parameters'],
            'Select a closed contextual definition')
    refs = _references(selected['body'])
    inputs = {n for n in refs if declarations[n]['kind'] == 'primitive'}
    require(inputs == set(roles), 'Context interface must cover exactly the direct primitive inputs')
    require(all(isinstance(v, str) and v.strip() for v in roles.values()), 'Missing context role')
    retained = set()

    def retain(name):
        d = declarations[name]
        require(d['kind'] == 'definition', 'Dependency needs its own explicit context: ' + name)
        if name in retained:
            return
        retained.add(name)
        for dependency in _references(d['body']):
            retain(dependency)

    for name in refs - inputs:
        retain(name)
    require(set(names) == retained | {target} and len(set(names.values())) == len(names),
            'Retained names must be injective and complete')
    # Internal binder names have no lexical meaning. Avoid every existing string
    # before normalization, including variables under lambdas and quantifiers.
    def strings(value):
        if isinstance(value, str):
            return {value}
        if isinstance(value, dict):
            return set().union(set(value), *(strings(v) for v in value.values()))
        if isinstance(value, list):
            return set().union(*(strings(v) for v in value))
        return set()
    used = strings(source); binders = {}; interface = []
    for n in sorted(inputs):
        label = 'contextvalue'
        while label in used:
            label += 'a'
        used.add(label); binders[n] = label; d = declarations[n]
        sort = function_sort(d['parameters'], d['result']) if d['parameters'] else d['result']
        interface.append(dict(source_symbol=n, role=roles[n], sort=deepcopy(sort), parameter=label))

    def transform(value):
        if isinstance(value, list):
            return [transform(v) for v in value]
        if not isinstance(value, dict):
            return value
        kind = value.get('kind')
        if kind == 'quote':
            require(not (_references(value) & inputs), 'Quoted contextual identity cannot be abstracted')
        if kind == 'apply' and value['function'].get('kind') == 'function_ref':
            require(value['function']['symbol'] not in inputs,
                    'Explicit primitive application requires a separate preservation rule')
        if kind in ('call', 'function_ref') and value['symbol'] in inputs:
            name = value['symbol']; variable = dict(kind='variable', name=binders[name])
            if kind == 'function_ref':
                require(declarations[name]['parameters'], 'Nullary function reference is distinct from its value')
                return variable
            if not declarations[name]['parameters']:
                return variable
            return dict(kind='apply', function=variable, arguments=transform(value['arguments']))
        return {k: transform(v) for k, v in value.items()}

    result = deepcopy(selected)
    result['parameters'] = [dict(name=r['parameter'], sort=r['sort']) for r in interface]
    result['body'] = transform(selected['body'])
    ds = [deepcopy(d) for d in source['declarations'] if d['name'] in retained] + [result]
    output = normalize_document(renamed(dict(schema_version='0.16', lexicon_version='0.16',
        declarations=ds, statements=[]), names))
    for record, parameter in zip(interface, output['declarations'][-1]['parameters'], strict=True):
        record['parameter'] = parameter['name']
    return output, interface


def instantiate(template, interface, original, target, names):
    """Proof-side reconstruction with the original context; not a decoder.

    No existence, universal quantification or real-world identity is inferred.
    The caller must compare the reconstructed closed slice with the original.
    """
    source = normalize_document(original)
    ds = {d['name']: d for d in source['declarations']}
    records = {r['parameter']: r for r in interface}
    require(len(records) == len(interface) == len({r['source_symbol'] for r in interface}),
            'Repeated context binding')
    restored = renamed(deepcopy(template), {v: k for k, v in names.items()})
    selected = next(d for d in restored['declarations'] if d['name'] == target)
    require({p['name'] for p in selected['parameters']} == set(records), 'Context parameter inventory differs')
    for parameter in selected['parameters']:
        r = records[parameter['name']]; d = ds[r['source_symbol']]
        expected = function_sort(d['parameters'], d['result']) if d['parameters'] else d['result']
        require(parameter['sort'] == r['sort'] == expected, 'Context parameter type differs')

    def replace(value, bound=frozenset()):
        if isinstance(value, list):
            return [replace(v, bound) for v in value]
        if not isinstance(value, dict):
            return value
        if value.get('kind') == 'apply' and value['function'].get('kind') == 'variable':
            record = records.get(value['function']['name']) if value['function']['name'] not in bound else None
            if record and ds[record['source_symbol']]['parameters']:
                return dict(kind='call', symbol=record['source_symbol'], arguments=replace(value['arguments'], bound))
        if value.get('kind') == 'variable' and value['name'] in records and value['name'] not in bound:
            name = records[value['name']]['source_symbol']
            return (dict(kind='function_ref', symbol=name) if ds[name]['parameters'] else
                    dict(kind='call', symbol=name, arguments=[]))
        inner = bound
        if value.get('kind') in ('forall', 'exists', 'content'):
            inner = bound | {value['variable']}
        elif value.get('kind') == 'lambda':
            inner = bound | {p['name'] for p in value['parameters']}
        return {k: replace(v, inner if k == 'body' else bound) for k, v in value.items()}

    selected['body'] = replace(selected['body']); selected['parameters'] = []
    by_name = {d['name']: d for d in restored['declarations']}
    for r in interface:
        by_name[r['source_symbol']] = deepcopy(ds[r['source_symbol']])
    restored['declarations'] = [by_name[d['name']] for d in source['declarations'] if d['name'] in by_name]
    return normalize_document(restored)
