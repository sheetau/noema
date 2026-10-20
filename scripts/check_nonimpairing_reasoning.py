"""Exercise native causal comparison, method coverage, and scholarly binding."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue, FunctionValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_nonimpairing_reasoning import ROOT, LIBRARY, BASIS, MEANINGS, parents, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scholarly_self_ascription import writing_model, self_model, EXTRA as CIVIC_EXTRA, DOMAIN as CIVIC_DOMAIN

REPORT = 'reports/nonimpairing-reasoning-v1.json'
DOC = 'docs/nonimpairing-reasoning-v1.md'
PRIOR = ('reports/scholarly-self-ascription-v1.json', 'reports/qualitative-influence-v1.json', 'reports/office-obedience-v1.json')
STATES = tuple(product((False, True), repeat=2))
POINTS = ('off_a', 'off_b', 'on_a', 'on_b')
SCENES = ('reference', 'other', *POINTS)
DOMAIN = ('person', 'activity', 'work', 'method', 'othermethod', 'factor', 'result', 'other')
EXTRA = (CIVIC_EXTRA + 'r zmethod[] a.r zvariables[] j[a].r zequation[a h[a] c] c.r zfactor[] a.'
         'r zview[h[a] c] d.r zchecked[a d d] c.r zatleast[a d d d] c.'
         'r zavailable[a a d] c.r zoutcomes[a a d d] c.r zselected[a a d d] c.'
         'r zvariablesfor[a a d] j[a].r zequationsfor[a a d a h[a] c] c.'
         'r zfactorfor[a a d] a.r zviewfor[a a d h[a] c] d.')
MODEL = 'k zvariables[] p zequation k zfactor[] p zview'
SCALE = 'p zchecked p zatleast'
ABILITY = 'p zavailable p zoutcomes p zselected'
PROVIDERS = 'p zvariablesfor p zequationsfor p zfactorfor p zviewfor'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    target = {'causal': 'r3u', 'method': 'r3v', 'joint': 'r3w', 'scholarly': 'r3x'}[kind]
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, [target]), statements=[])
    args = {
        'causal': 'k zperson[] k zactivity[] k zwork[] k zref[] ' + MODEL + ' ' + SCALE,
        'method': 'k zperson[] k zactivity[] k zmethod[] k zref[] ' + MODEL + ' ' + ABILITY,
        'joint': 'k zperson[] k zactivity[] k zwork[] k zref[] ' + PROVIDERS + ' ' + SCALE + ' ' + ABILITY,
        'scholarly': ' '.join('k z' + n + '[]' for n in ('person', 'office', 'work', 'community', 'world', 'activity', 'scholar', 'writing', 'audience')) + ' k zref[] ' + PROVIDERS + ' ' + SCALE + ' ' + ABILITY,
    }[kind]
    return parse(format_graph(doc, 'compact') + EXTRA + 'q[k ' + target + '[' + args + ']].')


def key(state):
    return bool(state('factor')), bool(state('result'))


def model(doc, *, table=(False, False, False, False), grades=(2, 2, 2, 2), variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in ('person', 'community', 'world', 'office', 'work', 'activity', 'scholar', 'writing', 'audience', 'method', 'other'):
        v['z' + n] = lambda n=n: n
    v['zref'] = lambda: 'reference'
    solutions = [POINTS[i] for i, (f, out) in enumerate(STATES) if f and out == table[i]]
    selected = set(solutions)
    if variant == 'missing_result':
        selected.discard('on_b')
    elif variant == 'extra_result':
        selected.add('off_a')
    elif variant == 'empty_results':
        selected.clear()
    def equation(item, state):
        return table[STATES.index(key(state))] if item == 'result' else False
    def view(state):
        f, out = key(state)
        if variant == 'reversed_realization':
            f = not f
        return POINTS[STATES.index((f, out))]
    def checked(work, ref, point):
        return (work, ref) == ('other' if variant == 'other_assessed_work' else 'work',
                               'other' if variant == 'other_assessment_reference' else 'reference') and (
            point in POINTS and not (variant == 'missing_assessment' and point == 'on_a'))
    def atleast(work, ref, left, right):
        if (work, ref) != ('other' if variant == 'other_compared_work' else 'work', 'reference'):
            return False
        if variant == 'incomparable' and left != right:
            return False
        return left in POINTS and right in POINTS and grades[POINTS.index(left)] >= grades[POINTS.index(right)]
    def available(p, m, r):
        return variant != 'unavailable' and (p, m, r) == (
            'other' if variant == 'other_actor' else 'person',
            'othermethod' if variant == 'other_method_only' else 'method', 'reference')
    def outcomes(p, m, r, point):
        return variant != 'not_prospect' and (p, m, r) == ('person', 'method', 'reference') and point in selected
    def chosen(p, m, r, point):
        return (p, m, r) == ('person', 'method', 'other' if variant == 'other_result_reference' else 'reference') and point in selected
    v.update(zvariables=lambda: SequenceValue(('factor', 'result'), '"individual"'),
             zfactor=lambda: 'other' if variant == 'factor_outside' else 'factor',
             zequation=equation, zview=view, zchecked=checked, zatleast=atleast,
             zavailable=available, zoutcomes=outcomes, zselected=chosen,
             cg=lambda p, a, s: variant != 'no_execution' and (p, a) == (
                 'person', 'other' if variant == 'other_executed_activity' else 'activity') and s in ('on_a', 'on_b'))
    v.update(zvariablesfor=lambda p, m, r: v['zvariables'](),
             zfactorfor=lambda p, m, r: v['zfactor'](),
             zequationsfor=lambda p, m, r, item, state: equation(item, state),
             zviewfor=lambda p, m, r, state: view(state))
    return v


@lru_cache(None)
def causal_checks():
    doc, rows = fixture('causal'), {}
    for name, table, grades, expected in (
        ('same_performance', (False,) * 4, (2, 2, 2, 2), True),
        ('improved_performance', (False,) * 4, (1, 1, 2, 2), True),
        ('work_still_occurs_but_worse', (False,) * 4, (3, 3, 2, 2), False),
        ('mixed_safe_and_harmful_results', (False, True, False, True), (2, 2, 1, 3), False),
        ('safe_multistable_results', (False, True, False, True), (2, 2, 2, 3), True),
        ('no_off_solution', (True, False, False, False), (2,) * 4, False),
        ('no_on_solution', (False, False, True, False), (2,) * 4, False),
    ):
        actual = evaluate(doc, model(doc, table=table, grades=grades), DOMAIN, SCENES, True)
        assert actual == [expected], (name, actual)
        rows[name] = actual[0]
    for variant in ('other_executed_activity', 'no_execution', 'reversed_realization',
                    'other_assessed_work', 'other_assessment_reference', 'other_compared_work',
                    'missing_assessment', 'incomparable', 'factor_outside'):
        actual = evaluate(doc, model(doc, variant=variant), DOMAIN, SCENES, True)
        assert actual == [False], (variant, actual)
        rows[variant] = actual[0]
    return dict(contrasts=rows, native_intervention_and_qualitative_comparison=True,
                harm_not_reduced_to_total_failure=True)


@lru_cache(None)
def method_checks():
    doc, rows = fixture('method'), {}
    for variant in ('baseline', 'missing_result', 'extra_result', 'empty_results', 'unavailable',
                    'other_actor', 'other_method_only', 'not_prospect', 'other_result_reference', 'no_execution'):
        actual = evaluate(doc, model(doc, table=(False, True, False, True), variant=variant), DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    return dict(contrasts=rows, native_xd_evaluated=True, selected_equals_all_on_solutions=True)


@lru_cache(None)
def joint_checks():
    doc, rows = fixture('joint'), {}
    for variant in ('baseline', 'unavailable', 'other_actor', 'other_result_reference'):
        actual = evaluate(doc, model(doc, variant=variant), DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    # One available method harms the job; the other method is safe but unavailable.
    # Their on solutions are different, so the model cannot be silently shared.
    v = model(doc, grades=(2, 2, 1, 2))
    v['zequationsfor'] = lambda p, m, r, item, s: m == 'othermethod' and bool(s('factor')) if item == 'result' else False
    v['zselected'] = lambda p, m, r, s: (p, r) == ('person', 'reference') and s == ('on_b' if m == 'othermethod' else 'on_a')
    v['zoutcomes'] = v['zselected']
    actual = evaluate(doc, v, DOMAIN, SCENES, True)
    assert actual == [False], actual
    rows['safe_and_available_in_different_methods'] = actual[0]
    v['zavailable'] = lambda p, m, r: (p, r) == ('person', 'reference') and m in ('method', 'othermethod')
    actual = evaluate(doc, v, DOMAIN, SCENES, True)
    assert actual == [True], actual
    rows['safe_method_also_available'] = actual[0]
    # Provider arguments are inspected in real evaluation, not merely an AST fixture.
    calls = {n: set() for n in ('zvariablesfor', 'zequationsfor', 'zfactorfor', 'zviewfor')}
    for name in calls:
        original = v[name]
        def provider(*args, name=name, original=original):
            calls[name].add(args[:3])
            return original(*args)
        v[name] = provider
    assert evaluate(doc, v, DOMAIN, SCENES, True) == [True]
    for values in calls.values():
        assert values and all(p == 'person' and r == 'reference' for p, m, r in values)
        assert ('person', 'method', 'reference') in values
        assert ('person', 'othermethod', 'reference') in values
    return dict(contrasts=rows, provider_arguments_bound=True, one_method_for_ability_and_causality=True)


def scholarly_model(doc, variant):
    v = model(doc)
    written, ascribed = writing_model(doc), self_model(doc)
    for name in ('aa', 'ca', 'cb', 'cd', 'cc', 'ce', 'sc', 'hzwr', 'hzws', 'hzwt', 'h242g'):
        v[name] = written[name]
    for name in ('fa', 'h242h', 'h242d'):
        v[name] = ascribed[name]
    v.update(h237y=lambda w, r: (w, r) == ('work', 'reference'),
             h237h=lambda w, r: 'mechanism', h237i=lambda w, r: 'community',
             h237d=lambda m, w, r: FunctionValue(('individual',), 'truth', lambda p: p == 'person'),
             h237c=lambda p, c, r: (p, c, r) == ('person', 'community', 'reference'),
             h237e=lambda p, m, w, r: 'office',
             h237f=lambda p, role, m, w, r: (p, role, m, w, r) == ('person', 'office', 'mechanism', 'work', 'reference'),
             h232p=lambda a, r: variant != 'not_reasoned_discussion' and (a, r) == ('activity', 'reference'))
    if variant == 'other_public_actor':
        v['ca'] = lambda p, a, r: (p, a, r) == ('otherperson', 'activity', 'reference')
    elif variant == 'other_job_comparison':
        v['zchecked'] = lambda w, r, s: w == 'other'
    elif variant == 'harmful_method':
        v['zatleast'] = lambda w, r, l, q: (l not in ('on_a', 'on_b')) or q in ('on_a', 'on_b')
    return v


@lru_cache(None)
def scholarly_checks():
    doc, rows = fixture('scholarly'), {}
    domain = tuple(dict.fromkeys((*CIVIC_DOMAIN, *DOMAIN)))
    for variant in ('baseline', 'not_reasoned_discussion', 'other_public_actor', 'other_job_comparison', 'harmful_method'):
        actual = evaluate(doc, scholarly_model(doc, variant), domain, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    return dict(contrasts=rows, native_scholarly_office_binding=True, no_actual_source_claim_added=True)


@lru_cache(None)
def unknown_checks():
    rows = []
    for kind, names in [('causal', ('cg', 'zchecked', 'zatleast', 'zequation', 'zview')),
                        ('method', ('zavailable', 'zoutcomes', 'zselected'))]:
        doc = fixture(kind)
        for name in names:
            v = model(doc); v[name] = unknown
            try:
                evaluate(doc, v, DOMAIN, SCENES, True)
            except ValueError as error:
                assert 'Unknown' in str(error), str(error)
            else:
                raise AssertionError(name)
            rows.append(name)
    return dict(unknown_inputs_refused=rows)


@lru_cache(None)
def structure_checks():
    new = catalog()
    old = {n: e for c in parents() for n, e in c.entries.items()}
    assert not new.document['statements']
    for n, e in new.entries.items():
        if n not in MEANINGS:
            assert e['declaration'] == old[n]['declaration'], n
            assert e['meaning_ja'] == old[n]['meaning_ja'], n
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(new_definitions=4, new_primitives=0, unchanged_active_manuscript=True,
                new_semantic_reviews=0, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('causal', causal_checks), ('method', method_checks), ('joint', joint_checks),
                     ('scholarly', scholarly_checks), ('unknown', unknown_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set().union(*(set(c.source_sha256) for c in parents())) | {
        DOC, *PRIOR, 'scripts/compose_nonimpairing_reasoning.py', 'scripts/check_nonimpairing_reasoning.py',
        'tests/test_nonimpairing_reasoning.py', 'scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_scholarly_self_ascription.py'}
    return dict(status='practical_execution_with_same_work_causal_nondecrease_dependency', document=LIBRARY,
                **results, whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
