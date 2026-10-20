"""Check bounded same-goal comparisons, correspondence, and policy withdrawal."""
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
from scripts.compose_qualified_private_influence import ROOT, LIBRARY, BASIS, MEANINGS, LIMITS, parent, choices, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_enlightenment_extent as extent
from scripts import check_paired_influence as paired
from scripts import check_private_choice_frequency as private

REPORT = 'reports/qualified-private-influence-v1.json'
DOC = 'docs/qualified-private-influence-v1.md'
PRIOR = ('reports/private-choice-frequency-v1.json', 'reports/enlightenment-extent-v1.json',
         'reports/paired-restriction-influence-v1.json')
MODEL_EXTRA = '''r zvariables[] j[a].r zequation[a h[a] c] c.r zfactor[] a.
r zworld[h[a] c] d.r zmatch[h[a] c h[a] c] c.r zpublic[] a.r zreference[] d.r ztolerance[] b.'''
MARGS = 'k zvariables[] p zequation k zfactor[] p zworld p zmatch k zpublic[] k zreference[] k ztolerance[]'
BOUND_ARGS = (private.ARGS + ' k zframe[] p zbranchdegrees p zdegreecriterion p zbranchpoints '
              'p zbranchweight p zbranchfrequency p zfrequencycriterion '
              'k zvariables[] p zequation k zfactor[] p zworld p zmatch k zpublic[] k ztolerance[]')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    if kind == 'extent':
        doc['declarations'].append(deepcopy(parent().entries['r2xd']['declaration']))
    roots = {'extent': ['r2yt', 'r2xd'], 'matched': ['r2yu'], 'native': ['r2yu'],
             'bound': ['r2yy'], 'quote': ['r2yy']}[kind]
    boundaries = {'extent': ('hzmx', 'r2la'), 'matched': ('r2wz', 'r2yt'),
                  'native': ('hzmx', 'r2la'), 'bound': ('r2ys', 'r2yu'), 'quote': ()}[kind]
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    if kind == 'extent':
        extra = extent.EXTRA + 'r ztolerance[] b.'
        fields = 'k zpublic[] k zreference[] k zleft[] k zright[]'
        query = 'q[k r2yt[' + fields + ' k ztolerance[]]].q[k r2xd[' + fields + ']].'
    elif kind in ('matched', 'native'):
        extra, query = MODEL_EXTRA, 'q[k r2yu[' + MARGS + ']].'
    else:
        # private.EXTRA already supplies zreference, so omit its duplicate.
        extra = private.EXTRA + MODEL_EXTRA.replace('r zreference[] d.', '') + '''
r zbranchdegrees[d d] b.r zbranchpoints[d] j[d].r zbranchweight[d d] b.r zbranchfrequency[d] b.
r zbranch[] d.'''
        query = 'q[t[k r2yy[' + BOUND_ARGS + ']][k zbranch[]]].'
        if kind == 'quote':
            query = 'd zclosed[] e[k r2yy[' + BOUND_ARGS + ']].d zquote[] i c[e][r c[k zclosed[]]].'
    return parse(format_graph(doc, 'compact') + extra + query)


@lru_cache(None)
def extent_checks():
    doc = fixture('extent')
    sets = (set(), {'one'}, {'one', 'two'})
    rows = []
    for left, right, tolerance in product(sets, sets, (Fraction(0), Fraction(1, 4), Fraction(1, 2))):
        v = extent.model(doc, {('left', 'public'): left, ('right', 'public'): right})
        v['ztolerance'] = lambda: tolerance
        actual = evaluate(doc, v, extent.PEOPLE, extent.SCENES, True)
        wanted = [Fraction(len(left), 2) + tolerance >= Fraction(len(right), 2), len(left) >= len(right)]
        assert actual == wanted, (left, right, tolerance, actual)
        rows.append(dict(on=len(left), off=len(right), tolerance=str(tolerance), bounded_and_old=actual))
    contrasts = {}
    for variant in ('empty', 'missing_reader', 'bad_threshold', 'no_future', 'not_public'):
        v = extent.model(doc, variant=variant)
        v['ztolerance'] = lambda: Fraction(1, 2)
        actual = evaluate(doc, v, extent.PEOPLE, extent.SCENES, True)
        assert actual == [False, False]
        contrasts[variant] = actual
    v = extent.model(doc)
    v['ztolerance'] = lambda: Fraction(-1, 4)
    assert evaluate(doc, v, extent.PEOPLE, extent.SCENES, True) == [False, True]
    for name in ('hzmx', 'ztolerance'):
        v = extent.model(doc); v['ztolerance'] = lambda: Fraction(0); v[name] = unknown
        try:
            evaluate(doc, v, extent.PEOPLE, extent.SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(cases=rows, invalid_inputs=contrasts, zero_tolerance_matches_old_order=True,
                boundary_equality_allowed=True, negative_tolerance_refused=True,
                semantic_boundaries=['hzmx/r2la, as in enlightenment-extent-v1; native ratio/period/order composition'])


@lru_cache(None)
def matched_checks():
    doc = fixture('matched')
    people = (*paired.prior.PEOPLE, 'public')
    scenes = ('reference', 's0', 's1', 's2', 's3')
    table = (False, True, False, True)
    count = 0
    for mask in product((False, True), repeat=4):
        pairs = {p for p, active in zip(paired.PAIRS, mask) if active}
        for grades in ((0, 1, 0, 1), (0, 1, 1, 2), (1, 2, 0, 1)):
            for tolerance in (Fraction(0), Fraction(1, 2), Fraction(1)):
                v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
                v.update(paired.values(table, grades, pairs))
                v.update(extent.arithmetic())
                v.update(zpublic=lambda: 'public', zreference=lambda: 'reference',
                         ztolerance=lambda: tolerance,
                         zworld=lambda state: 's' + str(paired.STATES.index(paired.prior.state_key(state))),
                         r2wz=lambda public, reference, branch: (public, reference) == ('public', 'reference') and branch in scenes[1:],
                         r2yt=lambda public, reference, on, off, slack:
                             (public, reference) == ('public', 'reference') and slack >= 0
                             and grades[int(on[1:])] + slack >= grades[int(off[1:])])
                actual = evaluate(doc, v, people, scenes, True)[0]
                complete = paired.reference(table, grades, pairs)[0]
                expected = complete and all(grades[a] + tolerance >= grades[b] for a, b in pairs)
                assert actual == expected, (pairs, grades, tolerance, actual)
                count += 1
    # Same-branch pairs are neutral; crossed branches manufacture a loss.
    neutral = (0, 1, 0, 1)
    results = []
    for pairs in ({(2, 0), (3, 1)}, set(paired.PAIRS)):
        v.update(paired.values(table, neutral, pairs))
        v.update(ztolerance=lambda: Fraction(0),
                 r2yt=lambda public, reference, on, off, slack: neutral[int(on[1:])] + slack >= neutral[int(off[1:])])
        results.append(evaluate(doc, v, people, scenes, True)[0])
    assert results == [True, False]
    v['zmatch'] = unknown
    try:
        evaluate(doc, v, people, scenes, True)
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown match accepted')
    return dict(combinations=count, matched_and_crossed_neutral=results,
                complete_correspondence_required=True, unknown_match_refused=True,
                semantic_boundaries=['r2wz/r2yt isolate correspondence; native scale tested separately and together below'])


@lru_cache(None)
def native_checks():
    doc = fixture('native')
    people = (*extent.PEOPLE, 'factor', 'outcome')
    rows = {}
    for label, on, off, tolerance, expected in (
        ('small_loss_at_boundary', {'one'}, {'one', 'two'}, Fraction(1, 2), True),
        ('loss_exceeds_bound', {'one'}, {'one', 'two'}, Fraction(1, 4), False),
        ('no_progress_either_side', set(), set(), Fraction(0), True),
        ('below_attainment_threshold', set(), {'one'}, Fraction(1, 2), True),
    ):
        v = extent.model(doc, {('left', 'public'): on, ('right', 'public'): off})
        v.update(zvariables=lambda: SequenceValue(('factor', 'outcome'), '"individual"'),
                 zequation=lambda variable, state: variable == 'outcome' and state('factor'),
                 zfactor=lambda: 'factor', zworld=lambda state: 'left' if state('factor') else 'right',
                 zmatch=lambda on, off: on('factor') and not off('factor'),
                 ztolerance=lambda: tolerance)
        actual = evaluate(doc, v, people, extent.SCENES, True)[0]
        assert actual == expected, (label, actual)
        rows[label] = actual
    return dict(contrasts=rows, native_interventions_matches_extent_and_bound=True,
                small_hindrance_does_not_imply_actual_enlightenment=True,
                semantic_boundaries=['hzmx/r2la only'])


@lru_cache(None)
def policy_checks():
    doc = fixture('bound')
    people = (*private.PEOPLE, 'factor', 'outcome', 'public')
    scenes = (*private.SCENES, 'on', 'off', 'offlater')
    results = {}
    for variant in ('baseline', 'partial_row_release', 'partial_time_release', 'other_frame',
                    'wrong_policy_state', 'excessive_loss', 'actual_policy_absent'):
        v = private.model(doc)
        present = v['zrequired']
        def required(source, person, role, act, code, sign, point):
            if point in ('off', 'offlater'):
                return (variant == 'partial_row_release' and act == 'acta' and sign
                        or variant == 'partial_time_release' and point == 'offlater')
            return bool(present(source, person, role, act, code, sign, point))
        seen = []
        def inspect(*args):
            (source, person, role, reference, records, sources, recipients, roles, activities, codes, signs,
             rule, candidates, scope, weight, frame, degrees, criterion, points, timeweight,
             frequency, frequencycriterion, branch) = args
            assert (source, person, role, reference, frame) == ('source', 'person', 'role', 'reference', 'frame')
            assert tuple(r for r in people if records(r)) == ('ra', 'rb')
            for record, act, sign in (('ra', 'acta', True), ('rb', 'actb', False)):
                assert (sources(record), recipients(record), roles(record), activities(record),
                        symbol(codes(record)), codes(record).rank, signs(record)) == (
                            source, person, role, act, 'zperform', 1, sign)
                assert rule(source, person, role, act, codes(record), sign, 'first') == (
                    present(source, person, role, act, codes(record), sign, 'first'))
            assert candidates.items == private.CHOICES
            assert all(scope(c) and weight(c) == 1 for c in private.CHOICES)
            assert points.items == (private.TIMES if branch == 'on' else ('off', 'offlater'))
            assert degrees('first') == (Fraction(3, 4) if branch == 'on' else Fraction(0))
            assert timeweight('first') == (2 if branch == 'on' else 1)
            assert frequency == (Fraction(1, 2) if branch == 'on' else Fraction(0))
            assert criterion(Fraction(3, 4)) and frequencycriterion(Fraction(1, 2))
            seen.append(branch)
            return branch == ('off' if variant == 'wrong_policy_state' else 'on')
        v.update(zvariables=lambda: SequenceValue(('factor', 'outcome'), '"individual"'),
                 zequation=lambda variable, state: variable == 'outcome' and state('factor'),
                 zfactor=lambda: 'factor', zworld=lambda state: 'on' if state('factor') else 'off',
                 zmatch=lambda on, off: on('factor') and not off('factor'),
                 zpublic=lambda: 'public', ztolerance=lambda: Fraction(1, 4),
                 zbranch=lambda: 'off' if variant == 'actual_policy_absent' else 'on',
                 zbranchdegrees=lambda branch, point: Fraction(3, 4) if branch == 'on' else Fraction(0),
                 zbranchpoints=lambda branch: SequenceValue(private.TIMES if branch == 'on' else ('off', 'offlater'), '"situation"'),
                 zbranchweight=lambda branch, point: Fraction(2 if branch == 'on' else 1),
                 zbranchfrequency=lambda branch: Fraction(1, 2) if branch == 'on' else Fraction(0),
                 h222g=lambda public, reference: 'role' if variant == 'other_frame' else 'frame',
                 h7q=lambda frame, branch, point: frame == 'frame' and point in (
                     private.TIMES if branch == 'on' else ('off', 'offlater')),
                 h7r=lambda frame, branch, point: frame == 'frame' and point in (
                     private.TIMES if branch == 'on' else ('off', 'offlater')),
                 ic=lambda first, last, branch: scenes.index(first) < scenes.index(last),
                 zrequired=required, r2ys=inspect,
                 r2yu=lambda variables, equations, factor, worlds, matches, public, reference, tolerance:
                     variant != 'excessive_loss' and (public, reference, tolerance) == ('public', 'reference', Fraction(1, 4)))
        actual = evaluate(doc, v, people, scenes, True)[0]
        assert actual == (variant == 'baseline'), (variant, actual)
        assert {'on', 'off'} <= set(seen)
        results[variant] = actual
    quoted = fixture('quote')
    text = format_graph(quoted, 'compact')
    try:
        parse(text.replace('d zquote[] i c[e][r c[k zclosed[]]]', 'd zquote[] i b[e][r b[k zclosed[]]]'))
    except ValueError as error:
        assert 'strictly lower ranks' in str(error)
    else:
        raise AssertionError('Lower quotation rank accepted')
    return dict(contrasts=results, full_same_table_and_period_release_required=True,
                target_rank_two_accepted_and_rank_one_refused=True,
                semantic_boundaries=['r2ys inspects every bound argument and candidate projection; its actual degree/frequency checked in private-choice-frequency-v1',
                                     'r2yu is the checked matched bound; hze/r2yx and final content execute natively'])


@lru_cache(None)
def structure_checks():
    old, prior, new = parent(), choices(), catalog()
    record = read(BASIS)
    validate_hashes(ROOT, record['import_source_sha256'])
    for name in record['imported_symbols']:
        entry = old.entries.get(name) or prior.entries[name]
        assert new.entries[name]['declaration'] == entry['declaration']
        assert new.entries[name]['meaning_ja'] == entry['meaning_ja']
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(added_definitions=len(MEANINGS), added_primitives=0, added_statements=0,
                active_manuscript_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p, body in build().items():
        write_exact(ROOT / p, body)


def build_report():
    results = {}
    for name, fn in [('extent', extent_checks), ('matched', matched_checks), ('native', native_checks),
                     ('policy', policy_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(read(BASIS)['import_source_sha256']) | {
        DOC, *PRIOR, 'scripts/compose_qualified_private_influence.py', 'scripts/check_qualified_private_influence.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_private_choice_frequency.py',
        'scripts/compose_aligned_influence.py', 'scripts/compose_paired_influence.py',
        'scripts/compose_qualitative_influence.py', 'scripts/check_private_choice_frequency.py',
        'scripts/check_enlightenment_extent.py', 'scripts/check_paired_influence.py',
        'scripts/check_qualitative_influence.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'tests/test_qualified_private_influence.py'}
    return dict(status='qualified_private_policy_and_matched_extent_bound', document=LIBRARY, **results,
                interpretation=LIMITS, new_reviewed_sentence_characters=0,
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
