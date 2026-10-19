"""Check conditional rule contributions against the existing norm machinery."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_prescription_effects import ROOT, SOURCE, SOURCE_BASIS, LIBRARY, BASIS, MEANINGS, LIMITS, catalog, build

REPORT = 'reports/prescription-effects-v1.json'
DOC = 'docs/prescription-effects-v1.md'
INDEX = 'data/semantic-review-index-v101.json'
PEOPLE = ('rule', 'issuer', 'person', 'role', 'other')
SCENES = ('now', 'before', 'after', 'elsewhere')
TRUE = 'e[n p a b][n p a b]'
FALSE = 'u[' + TRUE + ']'
EXTRA = '''
r zrule[] a.r zissuer[] a.r zperson[] a.r zrole[] a.r zother[] a.r zpoint[] d.r zsign[] c.
r zconditionvalue[a d] c.r zgoalvalue[a d] c.r zholding[a a d] c.
r zallowed[a a a i[h[j[a]] e] j[a] c d] c.
d zcondition[person a] e[b point[k zconditionvalue[v person v point]]].
d zobjective[person a] e[b point[k zgoalvalue[v person v point]]].
d zalias[person a] e[k zobjective[v person]].
d zconditionalias[person a] e[k zcondition[v person]].
d ztarget[] i[h[j[a]] e][k r2fn[r[p zobjective]]].
d zarguments[] j[a][l[a][k zperson[]]].
d zrequired[source a person a role a description i[h[j[a]] e] bindings j[a] polarity c point d] c[
 k r2fp[k zrule[] k zissuer[] k zrole[] r[p zcondition] r[p zobjective] k zsign[] p zholding
 v source v person v role v description v bindings v polarity v point]].
'''
PRESCRIPTION = 'k zrule[] k zissuer[] k zperson[] k zrole[] r[p zcondition] r[p zobjective] k zsign[] k zpoint[] p zholding'
TARGET = 'k zrule[] k zperson[] k zrole[] k ztarget[] k zarguments[] k zsign[] k zpoint[]'
NORMS = TARGET + ' p r2fo p zrequired p zallowed'
QUERIES = ''.join('q[k ' + n + '[' + PRESCRIPTION + ']].' for n in ('rbb', 'rbc', 'rbd')) + ''.join(
    'q[k ' + n + '[' + NORMS + ']].' for n in ('rds', 'rdt', 'rdw'))


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def library(): return parse((ROOT / LIBRARY).read_text(encoding='utf-8'))


def fixture(queries=QUERIES, extra=''):
    return parse(format_graph(library(), 'compact') + EXTRA + extra + queries)


def unknown(*args): raise ValueError('Unknown prescription-effect interpretation')


def symbol(value): return json.loads(value.syntax).get('symbol')


def model(doc, adopted=True, holding=True, condition=True, goal=True, positive=True, allowed=False, variant='baseline'):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    expected = ['rule', 'issuer', 'role', 'zcondition', 'zobjective', positive, 'now']
    positions = dict(rule=0, issuer=1, role=2, condition=3, goal=4, polarity=5, context=6)
    alternatives = dict(condition='zconditionalias', goal='zalias', context='elsewhere', polarity=not positive)
    if variant in positions: expected[positions[variant]] = alternatives.get(variant, 'other')
    values.update(zrule=lambda: 'rule', zissuer=lambda: 'issuer', zperson=lambda: 'person', zrole=lambda: 'role',
        zother=lambda: 'other', zpoint=lambda: 'now', zsign=lambda: positive,
        zconditionvalue=lambda p, s: condition and (p, s) == ('person', 'now'),
        zgoalvalue=lambda p, s: goal and (p, s) == ('person', 'now'),
        zholding=lambda p, r, s: holding and (p, r, s) == (
            'other' if variant == 'holder' else 'person', 'other' if variant == 'held_role' else 'role', 'now'),
        rba=lambda r, issuer, role, cond, target, sign, s: adopted and [r, issuer, role, symbol(cond), symbol(target), sign, s] == expected,
        zallowed=lambda *args: allowed)
    return values


def evaluate(doc, values):
    return [r['value'] for r in evaluate_document(doc, individuals=PEOPLE, situations=SCENES,
        primitives=values, max_steps=2_000_000, memoize_definitions=True, memoize_expressions=True)]


@lru_cache(None)
def truth_checks():
    doc = fixture(); rows = []
    for adopted, holding, condition, goal, positive, allowed in product((False, True), repeat=6):
        actual = evaluate(doc, model(doc, adopted, holding, condition, goal, positive, allowed))
        active = adopted and holding and condition
        assert actual == [active, active and goal == positive, active and goal != positive,
                          active, allowed, active and goal != positive], actual
        rows.append(dict(inputs=[adopted, holding, condition, goal, positive, allowed], results=actual))
    return dict(combinations=64, cases=rows, existing_applicability_and_violation_executed=True,
                permission_independent_of_prescription=True)


@lru_cache(None)
def binding_checks():
    baseline = 'q[k rds[' + NORMS + ']].'; rows = {}
    for name in ('baseline', 'rule', 'issuer', 'role', 'condition', 'goal', 'polarity', 'context', 'holder', 'held_role'):
        doc = fixture(baseline); actual = evaluate(doc, model(doc, variant=name))
        assert actual == [name == 'baseline'], (name, actual)
        rows['adoption_' + name] = actual
    targets = {
        'source_is_issuer': TARGET.replace('k zrule[]', 'k zissuer[]', 1),
        'other_person': TARGET.replace('k zperson[]', 'k zother[]', 1),
        'other_role': TARGET.replace('k zrole[]', 'k zother[]', 1),
        'same_denotation_alias': TARGET.replace('k ztarget[]', 'k r2fn[r[p zalias]]'),
        'empty_bindings': TARGET.replace('k zarguments[]', 'l[a][]'),
        'extra_binding': TARGET.replace('k zarguments[]', 'l[a][k zperson[] k zother[]]'),
        'other_binding': TARGET.replace('k zarguments[]', 'l[a][k zother[]]'),
        'other_polarity': TARGET.replace('k zsign[]', 'u[k zsign[]]'),
    }
    for name, target in targets.items():
        doc = fixture('q[k rds[' + target + ' p r2fo p zrequired p zallowed]].')
        actual = evaluate(doc, model(doc)); assert actual == [False], (name, actual); rows[name] = actual
    doc = fixture(baseline); values = model(doc); values['zgoalvalue'] = unknown; values['zallowed'] = unknown
    assert evaluate(doc, values) == [True]
    for name in ('rba', 'zholding', 'zconditionvalue'):
        values = model(doc); values[name] = unknown
        try: evaluate(doc, values)
        except ValueError as error: assert 'Unknown prescription-effect' in str(error)
        else: raise AssertionError(name)
    violation = fixture('q[k rdw[' + NORMS + ']].'); values = model(violation); values['zgoalvalue'] = unknown
    try: evaluate(violation, values)
    except ValueError as error: assert 'Unknown prescription-effect' in str(error)
    else: raise AssertionError('Unknown goal treated as failure')
    all_rules = fixture('q[k r2fq[' + TARGET + ' p zholding]].')
    try: evaluate(all_rules, model(all_rules))
    except ValueError as error: assert 'Cannot finitely quantify' in str(error) and 'description' in str(error)
    else: raise AssertionError('All rule descriptions replaced by finite witnesses')
    return dict(cases=rows, unknown_inputs_refused=4, target_not_executed_for_requirement=True,
                unbounded_description_quantification_refused=True, issuer_distinct_from_rule_source=True)


@lru_cache(None)
def adapter_checks():
    queries = 'q[e[k ztarget[]][k r2fn[r[p zalias]]]].'
    shapes = ('l[a][]', 'l[a][k zperson[]]', 'l[a][k zother[]]', 'l[a][k zperson[] k zother[]]')
    for shape in shapes: queries += 'q[t[c[s[k ztarget[]]][' + shape + ']][k zpoint[]]].'
    doc = fixture(queries); rows = []
    for goal in (False, True):
        actual = evaluate(doc, model(doc, goal=goal))
        assert actual == [False, False, goal, False, False], actual
        rows.append(dict(goal=goal, results=actual))
    doc = fixture('q[e[k ztarget[]][k ztarget[]]].'); values = model(doc)
    values['zgoalvalue'] = values['zconditionvalue'] = values['rba'] = unknown
    assert evaluate(doc, values) == [True]
    return dict(cases=rows, exact_one_person_shape=True, quoted_constructor_does_not_evaluate_contents=True,
                distinct_goal_descriptions_remain_distinct=True)


@lru_cache(None)
def conflict_checks():
    extra = '''
d zopposed[source a person a role a description i[h[j[a]] e] bindings j[a] polarity c point d] c[
 k r2fp[k zrule[] k zissuer[] k zrole[] r[p zcondition] r[p zobjective] u[k zsign[]] p zholding
 v source v person v role v description v bindings v polarity v point]].
d zcombined[source a person a role a description i[h[j[a]] e] bindings j[a] polarity c point d] c[
 x[k zrequired[v source v person v role v description v bindings v polarity v point]][
 k zopposed[v source v person v role v description v bindings v polarity v point]]].
'''
    args = NORMS.replace('p zrequired', 'p zcombined')
    doc = fixture('q[k rdv[' + args + ']].q[k rdw[' + args + ']].q[k rdw[' +
                  args.replace('k zsign[]', 'u[k zsign[]]') + ']].', extra)
    rows = []
    for first, second, goal in product((False, True), repeat=3):
        values = model(doc, goal=goal)
        values['rba'] = lambda r, issuer, role, cond, target, sign, s: (
            (first if sign else second) and [r, issuer, role, symbol(cond), symbol(target), s] ==
            ['rule', 'issuer', 'role', 'zcondition', 'zobjective', 'now'])
        actual = evaluate(doc, values)
        assert actual == [first and second, first and not goal, second and goal], actual
        rows.append(dict(positive=first, negative=second, goal=goal, results=actual))
    doc['statements'] = doc['statements'][:1]; values = model(doc)
    values['rba'] = lambda *args: True; values['zgoalvalue'] = unknown
    assert evaluate(doc, values) == [True]
    return dict(cases=rows, conflict_does_not_assert_both_goal_truths=True, nonfulfillment_not_negated_requirement=True)


@lru_cache(None)
def transition_checks():
    extra = 'r zstart[] d.r zend[] d.'
    fields = 'k zrule[] k zperson[] k zrole[] k ztarget[] k zarguments[] k zsign[] k zstart[] k zend[] '
    queries = ''.join('q[k riv[' + fields + sign + ' p r2fo p zrequired]].' for sign in (TRUE, FALSE))
    doc = fixture(queries, extra); rows = []
    for adopted_before, adopted_after, condition_before, condition_after in product((False, True), repeat=4):
        values = model(doc); values.update(zstart=lambda: 'before', zend=lambda: 'after', zgoalvalue=unknown)
        adopted = dict(before=adopted_before, after=adopted_after)
        conditions = dict(before=condition_before, after=condition_after)
        values['rba'] = lambda r, issuer, role, cond, target, sign, s: adopted.get(s, False) and (
            [r, issuer, role, symbol(cond), symbol(target), sign] == ['rule', 'issuer', 'role', 'zcondition', 'zobjective', True])
        values['zconditionvalue'] = lambda p, s: p == 'person' and conditions.get(s, False)
        values['zholding'] = lambda p, r, s: (p, r) == ('person', 'role') and s in ('before', 'after')
        before, after = adopted_before and condition_before, adopted_after and condition_after
        actual = evaluate(doc, values); assert actual == [not before and after, before and not after], actual
        rows.append(dict(adopted=[adopted_before, adopted_after], condition=[condition_before, condition_after], results=actual))
    return dict(cases=rows, existing_norm_change_executed=True, adoption_change_distinct_from_condition_change=True,
                no_legislative_act_inferred_from_requirement_change=True)


@lru_cache(None)
def structure_checks():
    old, new = catalog(), load_catalog(ROOT, BASIS)
    assert not new.document['statements'] and set(new.entries) - set(old.entries) == set(MEANINGS)
    for n in set(new.entries) & set(old.entries):
        assert new.entries[n]['declaration'] == old.entries[n]['declaration']
        assert new.entries[n]['meaning_ja'] == old.entries[n]['meaning_ja']
        assert new.entries[n].get('arguments') == old.entries[n].get('arguments')
    assert all(new.entries[n]['kind'] == 'definition' for n in MEANINGS)
    assert len(old.document['statements']) == 54
    index = read(INDEX); assert index['works']['kant-1784']['document'] == SOURCE
    for path in index['works']['kant-1784']['reviews']:
        r = read(path)
        assert r['selection'] == selection_binding(old, [s['index'] for s in r['selection']['statements']])
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body
    for style in ('compact', 'full'):
        text = format_graph(new.document, style)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(new_definitions=4, new_primitives=0, inherited_declarations_and_meanings=len(new.entries)-4,
                manuscript_statements_preserved=54, registered_reviews_preserved=12, active_registry_unchanged=True,
                roundtrips=True, source_equivalence_not_claimed=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('truth', truth_checks), ('bindings', binding_checks), ('adapter', adapter_checks),
                     ('conflicts', conflict_checks), ('transitions', transition_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(catalog().source_sha256) | set(build()) | {INDEX, DOC, 'scripts/compose_prescription_effects.py',
        'scripts/check_prescription_effects.py', 'tests/test_prescription_effects.py', 'noema/constructed.py',
        'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py',
        'noema/semantic_reviews.py', 'noema/script.py', 'scripts/compose_grounded_step.py',
        'scripts/audit_opening_scope.py'}
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    pins = {p: digest((ROOT / p).read_bytes()) for p in sorted(paths)}
    validate_hashes(ROOT, pins)
    return dict(status='prescription_effects_checked_not_source_replacement', document=LIBRARY, **results,
        alignment=[], whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_covered_characters=0, new_verified_sentence_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, limitations=LIMITS, source_sha256=pins)


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
