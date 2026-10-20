"""Check correspondence coverage, native effects and concrete source bindings."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import FunctionValue, SequenceValue
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import digest, validate_hashes
from scripts.compose_paired_influence import (
    ROOT, LIBRARY, BASIS, PARENT_BASIS, MEANINGS, LIMITS, build, parent, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_qualitative_influence as prior
from scripts import check_aligned_influence as aligned
from scripts import check_demand_candidates as concrete

REPORT = 'reports/paired-restriction-influence-v1.json'
DOC = 'docs/paired-restriction-influence-v1.md'
STATES = prior.STATES
PAIRS = tuple(product((2, 3), (0, 1)))
PROFILES = ('r2wj', 'r2wk', 'r2wl', 'r2wm', 'r2wn', 'r2wo')


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    if kind == 'profile':
        roots = PROFILES
        extra = '''r zvariables[] j[a].r zequation[a h[a] c] c.r zfactor[] a.
r zassessed[h[a] c] c.r zatleast[h[a] c h[a] c] c.r zmatch[h[a] c h[a] c] c.'''
        base = 'k zvariables[] p zequation k zfactor[] p zmatch'
        query = ''.join('q[k ' + n + '[' + base +
                        (' p zatleast' if n in ('r2wk', 'r2wl') else ' p zassessed p zatleast') + ']].'
                        for n in PROFILES)
    elif kind == 'combined':
        roots = ['r2wq', 'r2wr', 'r2ws', 'r2wt']
        extra = aligned.EXTRA + 'r zmatch[h[a] c h[a] c] c.'
        args = aligned.FIELDS + ' p zrequired ' + aligned.MODEL + ' p zchoices p zmatch ' + aligned.TARGET
        query = ''.join('q[k ' + n + '[' + args + ']].' for n in roots)
    else:
        roots = ['r2wu', 'r2wv', 'r2ww', 'r2wx']
        for d in doc['declarations']:
            if d['name'] in ('r2wa', 'r2wq', 'r2wr', 'r2ws', 'r2wt'):
                d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
                d.pop('body')
        # Keep native closed contents even though r2wa is a checked boundary.
        roots += list(concrete.CONTENTS)
        extra = '''r zvariables[] j[a].r zequation[a h[a] c] c.r zfactor[] a.
r zworld[h[a] c] d.r zpublic[] a.r zmatch[h[a] c h[a] c] c.
r zevaluated[a d i b[h[a d] e] d] c.
r zatleast[a d i b[h[a d] e] d d] c.'''
        tail = 'k zvariables[] p zequation k zfactor[] p zworld p zmatch k zpublic[] p zevaluated p zatleast'
        query = ''.join('q[k ' + n + '[k ' + case + '[] r b[p ' + code + '] ' + tail + ']].'
                        for case, code in zip(concrete.CASES, concrete.CONTENTS)
                        for n in ('r2wu', 'r2wv', 'r2ww', 'r2wx'))
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra + query)


def values(table, grades, pairs, **kwargs):
    v = prior.model(table, grades, **kwargs)
    v['zmatch'] = lambda on, off: (STATES.index(prior.state_key(on)),
                                 STATES.index(prior.state_key(off))) in pairs
    return v


def reference(table, grades, pairs):
    on = [i for i in (2, 3) if table[i] == STATES[i][1]]
    off = [i for i in (0, 1) if table[i] == STATES[i][1]]
    chosen = [(a, b) for a in on for b in off if (a, b) in pairs]
    complete = bool(on and off) and all(any(a == i for a, b in chosen) for i in on)
    complete = complete and all(any(b == j for a, b in chosen) for j in off)
    loss = any(grades[a] < grades[b] for a, b in chosen)
    gain = any(grades[a] > grades[b] for a, b in chosen)
    return [complete, loss, gain, complete and loss, complete and not loss,
            complete and not loss and gain]


@lru_cache(None)
def neutral_regression():
    table, grades = (False, True, False, True), (0, 1, 0, 1)
    old = evaluate(prior.fixture(), prior.model(table, grades), prior.PEOPLE, ('reference',), True)
    matched = evaluate(fixture('profile'), values(table, grades, {(2, 0), (3, 1)}),
                       prior.PEOPLE, ('reference',), True)
    crossed = evaluate(fixture('profile'), values(table, grades, set(PAIRS)),
                       prior.PEOPLE, ('reference',), True)
    assert old == crossed == [True, True, True, True, False, False]
    assert matched == [True, False, False, False, True, False]
    return dict(outcome_mechanism='result = result, independent of factor',
                grades=grades, old_cross_product=old, all_pairs_reproduces_old=crossed,
                same_branch_only=matched, neutral_branch_variation_not_counted_as_effect=True,
                interpretation='matches preserves the independently chosen outcome branch in this diagnostic model')


@lru_cache(None)
def matrix_checks():
    doc = fixture('profile')
    count = 0
    patterns = set()
    table = (False, True, False, True)
    for mask in product((False, True), repeat=4):
        pairs = {pair for pair, active in zip(PAIRS, mask) if active}
        for grades in ((0, 1, 0, 1), (0, 1, 1, 2), (1, 2, 0, 1), (0, 2, 1, 1)):
            actual = evaluate(doc, values(table, grades, pairs), prior.PEOPLE, ('reference',), True)
            assert actual == reference(table, grades, pairs), (mask, grades, actual)
            patterns.add(tuple(actual))
            count += 1
    for table in product((False, True), repeat=4):
        for pairs in (set(PAIRS), {(2, 0), (3, 1)}):
            grades = (0, 1, 1, 2)
            actual = evaluate(doc, values(table, grades, pairs), prior.PEOPLE, ('reference',), True)
            assert actual == reference(table, grades, pairs), (table, pairs, actual)
            count += 1
    return dict(checked_combinations=count, distinct_profiles=len(patterns),
                every_solution_on_both_sides_requires_a_match=True,
                many_to_many_matches_allowed=True,
                columns=['valid', 'raw_loss', 'raw_gain', 'loss', 'nonloss', 'nonloss_with_gain'])


@lru_cache(None)
def guard_checks():
    doc = fixture('profile')
    table, grades, pairs = (False, True, False, True), (0, 1, 0, 1), {(2, 0), (3, 1)}
    branches = {(a, b) for a in STATES for b in STATES if a[1] == b[1]}
    rows = {}
    result = evaluate(doc, values(table, grades, pairs, relation=branches), prior.PEOPLE, ('reference',), True)
    assert result == [True, False, False, False, True, False]
    rows['unmatched_branches_need_not_be_comparable'] = result
    cyclic = {(s, s) for s in STATES} | {(STATES[0], STATES[1]), (STATES[1], STATES[2]),
        (STATES[2], STATES[0]), (STATES[3], STATES[0]), (STATES[3], STATES[1]), (STATES[3], STATES[2])}
    cases = {
        'missing_assessment': dict(assessed=set(STATES) - {STATES[3]}),
        'missing_reflexivity': dict(relation=branches - {(STATES[2], STATES[2])}),
        'matched_pair_incomparable': dict(relation={(s, s) for s in STATES}),
        'nontransitive': dict(relation=cyclic),
        'duplicate_variables': dict(variables=('factor', 'result', 'result')),
        'factor_outside': dict(factor='outside'),
    }
    for name, kwargs in cases.items():
        result = evaluate(doc, values(table, grades, pairs, **kwargs), prior.PEOPLE, ('reference',), True)
        assert not any(result[i] for i in (0, 3, 4, 5)), (name, result)
        rows[name] = result
    v = values(table, grades, pairs)
    v['zmatch'] = unknown
    try:
        evaluate(doc, v, prior.PEOPLE, ('reference',), True)
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown correspondence became a negative answer')
    return dict(contrasts=rows, unknown_correspondence_refused=True)


@lru_cache(None)
def alignment_checks():
    doc = fixture('combined')
    rows = {}
    for direction, expected in [('gain', [True, False, True, True]),
                                ('equal', [True, False, True, False]), ('loss', [True, True, False, False])]:
        v = aligned.model(doc, direction=direction)
        v['zmatch'] = lambda on, off: on('factor') and not off('factor')
        actual = evaluate(doc, v, aligned.PEOPLE, aligned.SCENES, True)
        assert actual == expected, (direction, actual)
        rows[direction] = actual
    for variant in ('partly_withdrawn', 'partly_applied', 'other_public', 'other_reference',
                    'other_goal', 'all_choices_comply', 'wrong_code', 'unassessed_on', 'no_match'):
        v = aligned.model(doc, variant)
        v['zmatch'] = lambda on, off: variant != 'no_match' and on('factor') and not off('factor')
        actual = evaluate(doc, v, aligned.PEOPLE, aligned.SCENES, True)
        assert actual == [False] * 4, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_demands_and_matched_comparison=True,
                fixed_public_reference_and_r2ln_goal=True)


@lru_cache(None)
def concrete_checks():
    doc = fixture('concrete')
    v = concrete.model(doc)
    v.update(zvariables=lambda: SequenceValue(('factor', 'outcome'), '"individual"'),
             zequation=lambda variable, state: variable == 'outcome' and state('factor'),
             zfactor=lambda: 'factor', zworld=lambda state: 'on' if state('factor') else 'off',
             zpublic=lambda: 'public', zmatch=lambda on, off: on('factor') and not off('factor'),
             zevaluated=unknown, zatleast=unknown,
             r2wa=lambda case, code: case in concrete.LABELS and symbol(code) ==
                 concrete.CONTENTS[concrete.LABELS.index(case)] and code.rank == 1)
    seen = []

    def inspect(*args, result):
        (records, sources, people, roles, activities, codes, signs, required, variables,
         equations, factor, worlds, choices, matches, public, reference, evaluated, atleast) = args
        assert tuple(x for x in concrete.PEOPLE if records(x)) == concrete.RECIPIENTS
        case = activities('recipient')[:-5]
        for person in concrete.RECIPIENTS:
            assert (sources(person), people(person), roles(person), activities(person), codes(person).rank,
                    symbol(codes(person)), signs(person)) == (
                case + '-source', person, 'role-' + person, case + '-plan', 1,
                concrete.CONTENTS[concrete.LABELS.index(case)], True)
            assert required(sources(person), people(person), roles(person), activities(person),
                            codes(person), signs(person), 'on')
            assert choices(person, 'choice') == (person == 'recipient')
        on = FunctionValue(('individual',), 'truth', lambda item: item == 'factor')
        off = FunctionValue(('individual',), 'truth', lambda item: False)
        assert matches(on, off) and not matches(off, on)
        assert (worlds(on), worlds(off), public, reference, factor) == ('on', 'off', 'public', 'reference', 'factor')
        assert variables.items == ('factor', 'outcome')
        assert equations('outcome', on) and not equations('outcome', off)
        seen.append(case)
        return result

    for name, result in zip(('r2wq', 'r2wr', 'r2ws', 'r2wt'), (True, False, True, True)):
        v[name] = lambda *args, result=result: inspect(*args, result=result)
    actual = evaluate(doc, v, concrete.PEOPLE, concrete.SCENES, True)
    assert actual == [True, False, True, True] * 4
    v['r2wa'] = lambda case, code: False
    assert evaluate(doc, v, concrete.PEOPLE, concrete.SCENES, True) == [False] * 16
    assert set(seen) == set(concrete.LABELS)
    return dict(same_all_recipient_rows_and_ordered_matches=True, prior_anchor_required=True,
                semantic_boundaries=['r2wa and concrete command contents: demand-candidates-v1',
                                     'r2wq/r2wr/r2ws/r2wt: native generic evaluation in this report',
                                     'r2ud: prior full-description finite-evaluation refusal retained'])


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    record = json.loads((ROOT / BASIS).read_text(encoding='utf-8'))
    for name in record['imported_symbols']:
        for key in ('kind', 'declaration', 'meaning_ja'):
            assert new.entries[name][key] == old.entries[name][key], (name, key)
    assert not new.document['statements']
    validate_hashes(ROOT, record['import_source_sha256'])
    for path in ('reports/demand-candidates-v1.json', 'reports/aligned-restriction-influence-v1.json'):
        validate_hashes(ROOT, json.loads((ROOT / path).read_text(encoding='utf-8'))['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(unchanged_imports=len(record['imported_symbols']), added_definitions=len(MEANINGS),
                added_primitives=0, added_author_statements=0, new_semantically_reviewed_characters=0,
                roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('neutral_regression', neutral_regression), ('matrix', matrix_checks), ('guards', guard_checks),
                     ('alignment', alignment_checks), ('concrete', concrete_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | set(parent().source_sha256) | set(prior.catalog().source_sha256) | {DOC, PARENT_BASIS,
        'scripts/compose_paired_influence.py', 'scripts/check_paired_influence.py',
        'scripts/compose_grounded_step.py',
        'scripts/compose_demand_candidates.py', 'scripts/compose_aligned_influence.py',
        'scripts/compose_qualitative_influence.py', 'scripts/check_qualitative_influence.py',
        'scripts/check_aligned_influence.py', 'scripts/check_demand_candidates.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'tests/test_paired_influence.py', 'reports/demand-candidates-v1.json',
        'reports/aligned-restriction-influence-v1.json'}
    return dict(status='partial_matched_restriction_influence_checked', document=LIBRARY, **results,
                limitations=LIMITS, whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
