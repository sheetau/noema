"""Check native goal/ratio agreement, progress order and comparison callbacks."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_enlightenment_extent import (
    ROOT, LIBRARY, BASIS, PARENT_BASIS, PAIRED_BASIS, MEANINGS, LIMITS, build, parent, paired, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic
from scripts import check_aligned_influence as aligned

DOC = 'docs/enlightenment-extent-v1.md'
REPORT = 'reports/enlightenment-extent-v1.json'
PEOPLE = ('public', 'one', 'two', 'process')
SCENES = ('reference', 'left', 'right')
MEMBERS = ('one', 'two')
EXTRA = 'r zpublic[] a.r zreference[] d.r zleft[] d.r zright[] d.r zexpected[] b.'


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    roots = {'extent': ['r2xc', 'r2xe', 'r2ln', 'r2wz'],
             'order': ['r2xd'], 'guards': ['r2wz'],
             'combined': ['r2xh', 'r2xi', 'r2xj', 'r2xk'],
             'callbacks': ['r2xf', 'r2xg']}[kind]
    boundaries = {'extent': ('hzmx', 'r2la'), 'order': ('r2xc', 'r2la'),
                  'guards': ('r2la',), 'combined': ('r2wz', 'r2xd'),
                  'callbacks': ('r2wz', 'r2xd')}[kind]
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    prefix = 'k zpublic[] k zreference[]'
    extra = EXTRA
    if kind == 'extent':
        query = 'q[e[k r2xc[' + prefix + ' k zleft[] k zpublic[] k zreference[] k zleft[]]][k zexpected[]]].'
        query += ''.join(
            'q[k r2wz[' + prefix + ' k z' + side + '[]]].'
            'q[t[k r2ln[' + prefix + ']][k z' + side + '[]]].'
            'q[k r2xe[' + prefix + ' k z' + side + '[]]].' for side in ('left', 'right'))
    elif kind == 'order':
        query = ''.join('q[k r2xd[' + prefix + ' k z' + a + '[] k z' + b + '[]]].'
                        for a, b in (('left', 'left'), ('right', 'right'), ('left', 'right'), ('right', 'left')))
    elif kind == 'guards':
        query = 'q[k r2wz[' + prefix + ' k zleft[]]].'
    elif kind == 'combined':
        extra = aligned.EXTRA + 'r zmatch[h[a] c h[a] c] c.'
        args = aligned.FIELDS + ' p zrequired ' + aligned.MODEL + ' p zchoices p zmatch k zpublic[] k zreference[]'
        query = ''.join('q[k ' + n + '[' + args + ']].' for n in roots)
    else:
        extra += 'd zother[public a reference d] e[b point[e[v point][v point]]].'
        query = ''.join('q[k r2xf[' + prefix + ' r b[p ' + goal + '] k zleft[]]].'
                        'q[k r2xg[' + prefix + ' r b[p ' + goal + '] k zleft[] k zright[]]].'
                        for goal in ('r2ln', 'zother'))
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra + query)


def model(doc, changes=None, variant='baseline', ratios=None):
    changes = changes or {}
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(arithmetic())
    population = () if variant == 'empty' else ('one',) if variant == 'missing_reader' else (
        ('one', 'two', 'two') if variant == 'duplicate_reader' else MEMBERS)
    v.update(zpublic=lambda: 'public', zreference=lambda: 'reference',
             zleft=lambda: 'left', zright=lambda: 'right',
             zexpected=lambda: Fraction(len(changes.get(('left', 'public'), set()) & set(MEMBERS)), 2),
             pa=lambda n, d: n / d if d else Fraction(0),
             aa=lambda person: person in MEMBERS and not (variant == 'nonhuman' and person == 'two'),
             h6t=lambda group, person, reference: (group, reference) == (
                 'process' if variant == 'wrong_public' else 'public', 'reference') and person in MEMBERS,
             h222i=lambda public, reference: SequenceValue(tuple(population), '"individual"'),
             h222j=lambda public, reference: Fraction(1) if variant == 'bad_threshold' else Fraction(1, 2),
             h222g=lambda public, reference: 'public',
             h222h=lambda public, reference, branch: branch if variant == 'no_future' else 'reference',
             h7q=lambda frame, branch, point: frame == 'public' and (
                 point in ('reference', branch) if branch in ('left', 'right') else point == 'reference'),
             ic=lambda before, after, branch: (before, after) == ('reference', branch) and branch != 'reference',
             r2la=lambda public, reference: variant != 'not_public' and (public, reference) == ('public', 'reference'))

    def changed(group, actor, person, process, part, before, after, branch, scope):
        if (group, actor, part, before, after) != ('public', 'one', 'process', 'reference', branch):
            return False
        assert {p for p in PEOPLE if scope('public', p, branch)} == set(MEMBERS)
        return person in changes.get((branch, process), set())

    v['hzmx'] = changed
    if ratios is not None:
        v['r2xc'] = lambda public, reference, branch, process, before, after: ratios.get(
            (branch, process), Fraction(0))
    return v


@lru_cache(None)
def extent_checks():
    doc = fixture('extent')
    sets = [set(), {'one'}, {'two'}, {'one', 'two'}]
    rows = []
    for left, right in product(sets, repeat=2):
        changes = {('left', 'public'): left, ('right', 'public'): right}
        actual = evaluate(doc, model(doc, changes), PEOPLE, SCENES, True)
        expected = [True, True, len(left) > 1, len(left) > 1, True, len(right) > 1, len(right) > 1]
        assert actual == expected, (changes, actual)
        rows.append(dict(left=sorted(left), right=sorted(right), result=actual))
    # A single joint process is required by the old goal. Separate changes must
    # not be merged into a fictitious process that reaches the audience threshold.
    separate = {('left', 'public'): {'one'}, ('left', 'process'): {'two'},
                ('right', 'public'): {'one', 'two'}}
    actual = evaluate(doc, model(doc, separate), PEOPLE, SCENES, True)
    assert actual == [True, True, False, False, True, True, True]
    outsider = {('left', 'public'): {'one', 'public'}, ('right', 'public'): set()}
    assert evaluate(doc, model(doc, outsider), PEOPLE, SCENES, True) == [True, True, False, False, True, False, False]
    return dict(native_goal_and_reconstructed_threshold=rows, separate_processes_not_merged=actual,
                external_successes_excluded=True, threshold_equality_is_not_attainment=True,
                semantic_boundaries=['hzmx: existing native audience-change-v1 evidence; this check varies its checked person/process/time witnesses',
                                     'r2la: public classification is separately checked in public-comparison-claim-v1'])


@lru_cache(None)
def order_checks():
    doc = fixture('order')
    rows = []
    for left, right in product((Fraction(0), Fraction(1, 2), Fraction(1)), repeat=2):
        ratios = {('left', 'public'): left, ('right', 'public'): right}
        actual = evaluate(doc, model(doc, ratios=ratios), PEOPLE, SCENES, True)
        assert actual == [True, True, left >= right, right >= left], (left, right, actual)
        rows.append(dict(left=str(left), right=str(right), result=actual))
    ratios = {('left', 'public'): Fraction(1, 2), ('left', 'process'): Fraction(1, 2),
              ('right', 'public'): Fraction(1)}
    actual = evaluate(doc, model(doc, ratios=ratios), PEOPLE, SCENES, True)
    assert actual == [True, True, False, True]
    return dict(ordered_extent_cases=rows, separate_processes_do_not_add=actual,
                below_threshold_progress_distinguished=True, zero_progress_is_comparable=True,
                semantic_boundaries=['r2xc: native same-audience ratio checked separately; order evaluates all process/time witnesses'])


@lru_cache(None)
def guard_checks():
    doc = fixture('guards')
    rows = {}
    for variant in ('baseline', 'empty', 'missing_reader', 'duplicate_reader', 'nonhuman',
                    'wrong_public', 'bad_threshold', 'no_future', 'not_public'):
        actual = evaluate(doc, model(doc, variant=variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    v = model(doc)
    v['h222i'] = unknown
    try:
        evaluate(doc, v, PEOPLE, SCENES, True)
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown audience became a zero extent')
    return dict(contrasts=rows, invalid_population_or_period_refused=True, unknown_audience_refused=True)


@lru_cache(None)
def callback_checks():
    doc = fixture('callbacks')
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(zpublic=lambda: 'public', zreference=lambda: 'reference', zleft=lambda: 'left',
             zright=lambda: 'right', zexpected=lambda: Fraction(0),
             r2wz=lambda public, reference, branch: (public, reference, branch) == ('public', 'reference', 'left'),
             r2xd=lambda public, reference, left, right: (public, reference, left, right) ==
                 ('public', 'reference', 'left', 'right'))
    actual = evaluate(doc, v, PEOPLE, SCENES, True)
    assert actual == [True, True, False, False]
    return dict(results=actual, same_closed_r2ln_required=True, different_goal_cannot_use_scale=True)


@lru_cache(None)
def integration_checks():
    doc = fixture('combined')
    rows = {}
    for direction in ('gain', 'equal', 'loss'):
        v = aligned.model(doc)
        grades = {'on': 2 if direction == 'gain' else 0 if direction == 'loss' else 1,
                  'off': 1, 'partial': 1, 'reference': 1, 'choice': 1}
        v.update(zmatch=lambda on, off: on('factor') and not off('factor'),
                 r2wz=lambda public, reference, branch: (public, reference) == ('public', 'reference') and branch in ('on', 'off'),
                 r2xd=lambda public, reference, left, right: (public, reference) == ('public', 'reference') and
                     grades[left] >= grades[right])
        actual = evaluate(doc, v, aligned.PEOPLE, aligned.SCENES, True)
        expected = {'gain': [True, False, True, True], 'equal': [True, False, True, False],
                    'loss': [True, True, False, False]}[direction]
        assert actual == expected, (direction, actual)
        rows[direction] = actual
    v['r2wz'] = lambda *args: False
    assert evaluate(doc, v, aligned.PEOPLE, aligned.SCENES, True) == [False] * 4
    for name in ('r2wz', 'r2xd'):
        bad = dict(v)
        bad[name] = unknown
        try:
            evaluate(doc, bad, aligned.PEOPLE, aligned.SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, invalid_scale_is_not_nonhindrance=True, unknown_scale_refused=True,
                native_demands_matches_and_goal_callbacks=True,
                semantic_boundaries=['r2wz/r2xd: domain and quantified extent order checked separately in this report'])


@lru_cache(None)
def native_profile_checks():
    doc = deepcopy(catalog().document)
    # Retain the actual scale, temporal checks and paired classifier together.
    # Only the already tested individual-change/public-classification relations
    # are boundaries; no numeric grade or comparison predicate is supplied.
    for d in doc['declarations']:
        if d['name'] in ('hzmx', 'r2la'):
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    roots = ['r2wm', 'r2wn', 'r2wo', 'r2xf', 'r2xg']
    doc.update(declarations=closure(doc, roots), statements=[])
    extra = EXTRA + '''r zvariables[] j[a].r zequation[a h[a] c] c.r zfactor[] a.
r zworld[h[a] c] d.r zmatch[h[a] c h[a] c] c.'''
    assessed = 'i[state h[a] c][k r2xf[k zpublic[] k zreference[] r b[p r2ln] k zworld[v state]]]'
    comparison = ('i[first h[a] c second h[a] c][k r2xg[k zpublic[] k zreference[] r b[p r2ln] '
                  'k zworld[v first] k zworld[v second]]]')
    args = 'k zvariables[] p zequation k zfactor[] p zmatch ' + assessed + ' ' + comparison
    doc = parse(format_graph(doc, 'compact') + extra + ''.join(
        'q[k ' + name + '[' + args + ']].' for name in ('r2wm', 'r2wn', 'r2wo')))
    domain = (*PEOPLE, 'factor', 'outcome')
    rows = {}
    for label, on, off, expected in (
        ('below_threshold_gain', {'one'}, set(), [False, True, True]),
        ('same_extent_different_people', {'one'}, {'two'}, [False, True, False]),
        ('lost_extent', set(), {'one'}, [True, False, False]),
    ):
        v = model(doc, {('left', 'public'): on, ('right', 'public'): off})
        v.update(zvariables=lambda: SequenceValue(('factor', 'outcome'), '"individual"'),
                 zequation=lambda variable, state: variable == 'outcome' and state('factor'),
                 zfactor=lambda: 'factor', zworld=lambda state: 'left' if state('factor') else 'right',
                 zmatch=lambda on, off: on('factor') and not off('factor'))
        actual = evaluate(doc, v, domain, SCENES, True)
        assert actual == expected, (label, actual)
        rows[label] = actual
    return dict(contrasts=rows, native_scale_and_paired_profiles_together=True,
                progress_does_not_require_goal_attainment=True,
                semantic_boundaries=['hzmx/r2la only; same-person change and public meaning remain pinned to prior evidence'])


@lru_cache(None)
def structure_checks():
    old, prior, new = parent(), paired(), catalog()
    for source in (old, prior):
        for n, e in source.entries.items():
            if n in new.entries and n not in MEANINGS:
                for key in ('declaration', 'meaning_ja'):
                    assert new.entries[n][key] == e[key], (n, key)
    for name in ('reports/audience-change-v1.json', 'reports/public-comparison-claim-v1.json',
                 'reports/paired-restriction-influence-v1.json'):
        validate_hashes(ROOT, json.loads((ROOT / name).read_text(encoding='utf-8'))['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    assert not new.document['statements']
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(added_definitions=len(MEANINGS), added_primitives=0, added_author_statements=0,
                new_semantically_reviewed_characters=0, unchanged_dependencies=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('extent', extent_checks), ('order', order_checks), ('guards', guard_checks),
                     ('callbacks', callback_checks), ('integration', integration_checks),
                     ('native_profile', native_profile_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(parent().source_sha256) | set(paired().source_sha256) | {DOC,
        'scripts/compose_enlightenment_extent.py', 'scripts/check_enlightenment_extent.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/compose_aligned_influence.py', 'scripts/compose_paired_influence.py',
        'scripts/check_aligned_influence.py', 'scripts/check_scoped_counts.py',
        'scripts/check_motive_causes.py', 'scripts/check_pastoral_roles.py',
        'tests/test_enlightenment_extent.py', 'reports/audience-change-v1.json',
        'reports/public-comparison-claim-v1.json', 'reports/paired-restriction-influence-v1.json'}
    return dict(status='partial_same_enlightenment_extent_scale_checked', document=LIBRARY, **results,
                limitations=LIMITS, whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
