"""Check actual decoded bodies before finite point/binder diagnostics.

Point and coefficient-domain substitution is explicit. Finite diagnostics
do not constitute proofs over all real numbers or function spaces.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content, FunctionValue, DescriptionValue, SequenceValue, QuestionValue, evaluate_document
from noema.extraction import extract_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call, renamed
from scripts import check_einstein_tenth_observables_visible as check
from scripts.check_tau_differential import ConstructedCuts as HistoricalCuts
DIAGNOSTIC_ONLY = {'eu4', 'eu5'}
DIAGNOSTIC_ONLY_SEEN = set()
RECOVERED_DEFINITIONS_SEEN = set()
TRANSFORMED_DEFINITIONS_SEEN = set()

@lru_cache(None)
def diagnostic_controls():
    from pathlib import Path
    import hashlib
    root = Path(__file__).resolve().parents[1]
    controls = json.loads((root / 'data/tenth-observables-visible-diagnostic-controls-v1.json').read_text(encoding='utf-8'))
    assert controls['schema'] == 'noema-visible-diagnostic-controls-1'
    assert set(controls['controls']) == DIAGNOSTIC_ONLY
    assert all(not row['source_dependency'] for row in controls['controls'].values())
    for path, stamp in controls['source_sha256'].items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == stamp, path
    return controls

# These exact historical binder fixtures abstract sorts and a fixed real unit.
# They may be accepted only after checking the original typed body. Arbitrary
# edits to a recovered declaration still fail, including in these fixtures.
BINDING_TRANSFORMS = {
    **{root: ('jceunit', True) for root in ('ek7l', 'ek7m', 'ek7s', 'ek73')},
    **{root: ('jecunit', True) for root in ('ek6g', 'ek6p', 'ek6q', 'ek6u')},
    **{root: ('jerunit', True) for root in ('ek35', 'ek36')},
    **{root: ('jdynunit', True) for root in ('ele', 'elj', 'elk', 'ell')},
    'ek4q': ('jemunit', True), 'ek3x': ('jpdunit', True),
    'evj': ('jthone', False),
}
BINDING_TRANSFORMS.update({'elu':('jmrunits',True),'ema':('jfmunit',True),'emb':('jfmunit',True),'emn':('jdmunit',True),'emo':('jdmunit',True),'env':('jecczero',True)})

ENERGY_BINDING_ROOTS = {'eot', 'epu', 'epy'}

def energy_binding_transform(node, root):
    # Exact retained scalarize followed by collapse, confined to these roots.
    if node == 'number':return 'individual'
    if isinstance(node,list):return [energy_binding_transform(x,root) for x in node]
    if not isinstance(node,dict):return node
    if root == 'eot' and node.get('kind') in ('number','apply','function_ref'):
        return dict(kind='call',symbol='jkwzero',arguments=[])
    if node.get('kind') in ('sequence','function','question'):return 'individual'
    return {k:energy_binding_transform(v,root) for k,v in node.items()}

def boundary_single_speed_transform(declaration):
    """The retained setb fixture instantiates exactly one cut binder at 6."""
    literal = dict(kind='call', symbol='bb', arguments=[dict(kind='number', numerator=6, denominator=1)])
    cut = dict(kind='function', parameters=['number'], result='truth')
    found = []
    def substitute(node, name):
        if isinstance(node, list):return [substitute(x, name) for x in node]
        if not isinstance(node, dict):return node
        if node.get('kind') == 'variable' and node.get('name') == name:return deepcopy(literal)
        return {k:substitute(v, name) for k,v in node.items()}
    def visit(node):
        if isinstance(node, list):return [visit(x) for x in node]
        if not isinstance(node, dict):return node
        if node.get('kind') == 'forall' and node.get('sort') == cut:
            found.append(node['variable'])
            return substitute(node['body'], node['variable'])
        return {k:visit(v) for k,v in node.items()}
    result = deepcopy(declaration)
    result['body'] = visit(result['body'])
    assert len(found) == 1, 'Expected exactly one universal cut-speed binder'
    return result

def binding_transform(node, unit, scalar):
    if scalar and node == 'number':
        return 'individual'
    if isinstance(node, list):
        return [binding_transform(x, unit, scalar) for x in node]
    if not isinstance(node, dict):
        return node
    if node.get('kind') == 'call' and node.get('symbol') == 'bb':
        return dict(kind='call', symbol=unit, arguments=[])
    if scalar and node.get('kind') in ('function', 'sequence', 'question'):
        return 'individual'
    return {k: binding_transform(v, unit, scalar) for k, v in node.items()}

class Cuts:
    arithmetic = HistoricalCuts.arithmetic

    def __init__(self):
        self.table = {}

    def make(self, n):
        n = Q(n)
        f = FunctionValue(('number',), 'truth', lambda q: q < n)
        self.table[f.implementation] = n
        return f

    def read(self, f):
        while isinstance(f, FunctionValue):
            impl = f.implementation
            if impl in self.table:
                return self.table[impl]
            if isinstance(impl, FunctionValue):
                f = impl
                continue
            code = getattr(impl, '__code__', None)
            if code is None:
                break
            free = dict(zip(code.co_freevars, (c.cell_contents for c in getattr(impl, '__closure__', None) or ())))
            f = free.get('raw')
        raise ValueError('Unregistered finite cut')

@lru_cache(None)
def mapping():
    return check.names() | {old: check.vocabulary()._symbols[new] for old, new in check.RELATIONS.items()} | check.mapping()

def forbidden(*xs):
    raise ValueError('Unknown tenth-observables diagnostic input')

def value(x):
    if isinstance(x, SequenceValue):
        return tuple(value(item) for item in x.items)
    if isinstance(x, DescriptionValue):
        node = renamed(json.loads(x.syntax), {v: k for k, v in mapping().items()})
        if node.get('kind') in ('call', 'function_ref'):
            return node['symbol']
        raise ValueError('Unexpected quoted form')
    return x

def relation(rows):
    return lambda *xs: tuple((value(x) for x in xs)) in rows

def unknowns(test, model, names):
    for name in names:
        with pytest.raises(ValueError):
            test(model | {name: forbidden})

def perturb(test, model, rows, norm=lambda xs: tuple((value(x) for x in xs))):
    count = 1
    assert test(model)
    for name, rs in rows.items():
        for row in rs:
            assert not test(model | {name: lambda *xs, rs=rs - {row}: norm(xs) in rs})
            count += 1
            for slot in range(len(row)):
                bad = tuple(('wrong' if i == slot else x for i, x in enumerate(row)))
                assert not test(model | {name: lambda *xs, rs=rs - {row} | {bad}: norm(xs) in rs})
                count += 1
    unknowns(test, model, rows)
    return count

@lru_cache(None)
def checked_extract_json(serialized, roots, indices):
    extracted = extract_document(json.loads(serialized), roots=roots, statement_indices=list(indices))
    original = extracted.document
    mapped = normalize_document(renamed(original, mapping()))
    recovered = {d['name']: d for d in check.restored()['document']['declarations']}
    inverse = {v: k for k, v in mapping().items()}
    for i, (old, d) in enumerate(zip(original['declarations'], mapped['declarations'], strict=True)):
        if d['kind'] != 'definition':
            continue
        control = d['name'] not in recovered and old['name'] in DIAGNOSTIC_ONLY
        if control:
            entry = check.catalogs()['einstein-1905'].entries[old['name']]
            assert entry['declaration'] == diagnostic_controls()['controls'][old['name']]['declaration']
            actual = renamed(entry['declaration'], mapping())
        else:
            actual = deepcopy(recovered[d['name']])
        if actual != d:
            boundary = old['name'] == 'setb'
            assert boundary or (len(roots) == 1 and roots[0] in set(BINDING_TRANSFORMS)|ENERGY_BINDING_ROOTS), ('Unreviewed diagnostic transform', old['name'])
            assert old['name'] in RECOVERED_DEFINITIONS_SEEN | DIAGNOSTIC_ONLY_SEEN, ('Typed body was not checked first', old['name'])
            unmapped = renamed(actual, inverse)
            transformed = boundary_single_speed_transform(unmapped) if boundary else energy_binding_transform(unmapped, roots[0]) if roots[0] in ENERGY_BINDING_ROOTS else binding_transform(unmapped, *BINDING_TRANSFORMS[roots[0]])
            expected = renamed(transformed, mapping())
            assert expected == d, ('Diagnostic transform changed more than the declared abstraction', old['name'])
            TRANSFORMED_DEFINITIONS_SEEN.add(('single_speed_6' if boundary else roots[0], old['name']))
        else:
            (DIAGNOSTIC_ONLY_SEEN if control else RECOVERED_DEFINITIONS_SEEN).add(old['name'])
            original['declarations'][i] = renamed(actual, inverse)
    return extracted

def checked_extract(document, *, roots=(), statement_indices=()):
    return deepcopy(checked_extract_json(json.dumps(document, sort_keys=True), tuple(roots), tuple(statement_indices)))

def native_evaluate(document, *, primitives, **options):
    doc = normalize_document(renamed(document, mapping()))
    return evaluate_document(doc, primitives={mapping().get(n, n): fn for n, fn in primitives.items()}, **options)

def native_candidate(text, questions):
    # Historical candidate() does not extract: check the typed dependency
    # closure before the caller replaces analytical operations by primitives.
    # Keep its original return value, including unrelated declarations.
    from scripts.check_described_appraisals import candidate
    doc = candidate(text, questions)
    checked_extract(doc, statement_indices=range(len(doc['statements'])))
    return doc
GROUPS = {'experimental_list_opening': ['content_checks', 'enumeration_checks', 'presentation_checks'],
 'deflection_speed_determination': ['scalar_checks',
                                    'physical_checks',
                                    'quantity_checks',
                                    'measurement_checks',
                                    'possibility_checks',
                                    'binding_checks',
                                    'presentation_checks'],
 'direct_speed_experiment': ['quantity_checks',
                             'direct_checks',
                             'comparison_checks',
                             'oscillation_checks',
                             'possibility_checks',
                             'presentation_checks'],
 'traversed_potential': ['numeric_checks',
                         'unit_checks',
                         'path_checks',
                         'connection_checks',
                         'presentation_checks'],
 'local_magnetic_radius': ['numeric_checks',
                           'exclusive_checks',
                           'physical_checks',
                           'geometry_checks',
                           'connection_checks',
                           'presentation_checks'],
 'complete_motion_expression': ['equivalence_checks',
                                'physical_content_checks',
                                'binding_checks',
                                'specialization_checks',
                                'theory_scope_checks',
                                'presentation_checks']}
_NAMESPACES = {}
_MODULES = {}

def native_free(function):
    impl = function.implementation
    code = getattr(impl, '__code__', None)
    cells = dict(zip(code.co_freevars, (c.cell_contents for c in impl.__closure__ or ()))) if code else {}
    # The analytical fixture recognizes exact historical ASTs; map only symbol
    # spelling back. Captured values and binder identities are untouched.
    if 'node' in cells:
        cells['node'] = renamed(cells['node'], {v: k for k, v in mapping().items()})
    return cells

def native_unwrap(function):
    while isinstance(function, FunctionValue):
        if isinstance(function.implementation, FunctionValue):
            function = function.implementation
        elif 'raw' in native_free(function):
            function = native_free(function)['raw']
        else:
            break
    return function

def native_setup(module, namespace):
    import ast, inspect, textwrap
    tree = ast.parse(textwrap.dedent(inspect.getsource(module.setup)))
    candidates = []
    for node in ast.walk(tree):
        if isinstance(node, ast.While) and ast.unparse(node.test) == 'isinstance(x, FunctionValue)':
            if node.body and ast.unparse(node.body[0]) == 'f = x.implementation':
                candidates.append(node)
    assert len(candidates) == 1, module.__name__
    candidates[0].body[1:1] = ast.parse('if isinstance(f,FunctionValue):\n    x=f\n    continue').body
    exec(compile(ast.fix_missing_locations(tree), module.__file__, 'exec'), namespace)

def native_description_checks(module, namespace):
    """Normalize only the spelling read from the three quoted symbol probes."""
    import ast, inspect, textwrap
    for name, expected_count in (('selection_checks', 2), ('caution_checks', 1)):
        tree = ast.parse(textwrap.dedent(inspect.getsource(getattr(module, name))))
        changed = []
        class DescriptionSpelling(ast.NodeTransformer):
            def visit_Subscript(self, node):
                self.generic_visit(node)
                if (isinstance(node.slice, ast.Constant) and node.slice.value == 'symbol'
                        and isinstance(node.value, ast.Call)
                        and ast.unparse(node.value.func) == 'json.loads'
                        and len(node.value.args) == 1 and not node.value.keywords
                        and isinstance(node.value.args[0], ast.Attribute)
                        and node.value.args[0].attr == 'syntax'):
                    changed.append(ast.unparse(node))
                    return ast.copy_location(ast.Call(func=ast.Name(id='value', ctx=ast.Load()),
                        args=[node.value.args[0].value], keywords=[]), node)
                return node
        tree = DescriptionSpelling().visit(tree)
        assert len(changed) == expected_count, (name, changed)
        exec(compile(ast.fix_missing_locations(tree), module.__file__, 'exec'), namespace)

def diagnostic_import(name, globals=None, locals=None, fromlist=(), level=0):
    import builtins
    from types import SimpleNamespace
    if level == 0 and name.startswith('scripts.check_'):
        proxy = adapted_module(name)
        return proxy if fromlist else SimpleNamespace(**{name.split('.')[1]: proxy})
    if level == 0 and fromlist and (name == 'scripts'):
        module = builtins.__import__(name, globals, locals, fromlist, level)
        entries = dict(vars(module))
        for item in fromlist:
            if item.startswith('check_'):
                entries[item] = adapted_module('scripts.' + item)
        return SimpleNamespace(**entries)
    module = builtins.__import__(name, globals, locals, fromlist, level)
    if level == 0 and fromlist and (name == 'noema.finite_semantics'):
        return SimpleNamespace(**vars(module) | dict(Content=Content, FunctionValue=FunctionValue, DescriptionValue=DescriptionValue, SequenceValue=SequenceValue, QuestionValue=QuestionValue, evaluate_document=native_evaluate))
    return module

def adapted_module(module_name):
    import importlib, builtins, ast, inspect, textwrap
    from types import ModuleType
    if module_name in _MODULES:
        return _MODULES[module_name]
    module = importlib.import_module(module_name)
    proxy = ModuleType(module_name)
    ns = proxy.__dict__
    overrides = dict(Content=Content, FunctionValue=FunctionValue, DescriptionValue=DescriptionValue, SequenceValue=SequenceValue, QuestionValue=QuestionValue, ConstructedCuts=Cuts, value=value, relation=relation, perturb=perturb, unknowns=unknowns, extract_document=checked_extract, evaluate_document=native_evaluate)
    if module_name == 'scripts.check_described_appraisals':
        overrides['candidate'] = native_candidate
    ns.update(vars(module))
    ns.update(overrides)
    if module_name == 'scripts.check_material_acceleration':
        overrides.update(free=native_free, unwrap=native_unwrap)
        ns.update(overrides)
    ns['__builtins__'] = vars(builtins) | {'__import__': diagnostic_import}
    _MODULES[module_name] = proxy
    _NAMESPACES[module_name] = ns
    imported = []
    aliases = []
    classes = []
    for name, fn in vars(module).items():
        if name in overrides:
            continue
        if isinstance(fn, ModuleType) and fn.__name__.startswith('scripts.check_'):
            aliases.append((name, fn.__name__))
            continue
        if isinstance(fn, type) and fn.__module__ == module_name:
            classes.append(fn)
            continue
        if isinstance(fn, type) and fn.__module__.startswith('scripts.check_'):
            imported.append((name, fn.__module__, fn.__name__))
            continue
        raw = getattr(fn, '__wrapped__', fn)
        if not isinstance(raw, FunctionType):
            continue
        owner = raw.__module__
        if owner == module_name:
            copied = FunctionType(raw.__code__, ns, raw.__name__, raw.__defaults__, raw.__closure__)
            copied.__kwdefaults__ = raw.__kwdefaults__
            ns[name] = lru_cache(None)(copied) if hasattr(fn, 'cache_info') else copied
        elif owner.startswith('scripts.check_'):
            imported.append((name, owner, raw.__name__))
    for name, owner, original in imported:
        ns[name] = vars(adapted_module(owner))[original]
    for name, owner in aliases:
        ns[name] = adapted_module(owner)
    for cls in classes:
        # Resolve aliased bases first so inherited methods also use Native
        # globals. Recompile the unchanged class without modifying its owner.
        tree = ast.parse(textwrap.dedent(inspect.getsource(cls)))
        exec(compile(tree, module.__file__, 'exec'), ns)
    if module_name in ('scripts.check_attached_material_charge', 'scripts.check_convective_charge_setting', 'scripts.check_convective_transformed_quantities'):
        native_setup(module, ns)
    if module_name == 'scripts.check_calculation_discourse':
        ns['symbol'] = value
    if module_name == 'scripts.check_electron_convention_caution':
        native_description_checks(module, ns)
    return proxy

@pytest.mark.parametrize('group,name', [(group, name) for group, names in GROUPS.items() for name in names])
def test_native_physical_bodies_and_distinguishing_bindings(group, name):
    module = adapted_module('scripts.check_' + group)
    result = vars(module)[name]()
    assert isinstance(result, dict) and result.get('cases', 0) > 0, (group, name, result)
