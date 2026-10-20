"""Verify demand-based degree and temporal frequency with fixed private choices."""
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
from scripts.compose_private_choice_frequency import ROOT, LIBRARY, BASIS, MEANINGS, LIMITS, parent, build, RULE
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_scoped_counts import arithmetic

REPORT = 'reports/private-choice-frequency-v1.json'
DOC = 'docs/private-choice-frequency-v1.md'
PRIOR = ('reports/public-enlightenment-route-v1.json', 'reports/aligned-restriction-influence-v1.json',
         'reports/restriction-frequency-v1.json')
PEOPLE = ('source', 'person', 'role', 'acta', 'actb', 'ra', 'rb', 'frame')
CHOICES = ('c00', 'c01', 'c10', 'c11')
TIMES = ('first', 'middle', 'last')
SCENES = ('reference', *CHOICES, *TIMES)
FIELDS = 'p zrecords p zsources p zpeople p zroles p zactivities p zcodes p zsigns'
ARGS = ('k zsource[] k zperson[] k zrole[] k zreference[] ' + FIELDS +
        ' p zrequired k zchoices[] p zscope p zchoiceweight')
FARGS = (ARGS + ' k zframe[] p zdegrees p zdegreecriterion k zpoints[] p ztimeweight '
         'k zfrequency[] p zfrequencycriterion k zanchor[]')
EXTRA = '''
r zsource[] a.r zperson[] a.r zrole[] a.r zreference[] d.r zframe[] a.r zanchor[] d.
r zrecords[a] c.r zsources[a] a.r zpeople[a] a.r zroles[a] a.r zactivities[a] a.r zsigns[a] c.
r ztruth[a a d] c.
d zperform[person a act a] e[b choice[k ztruth[v person v act v choice]]].
d zcodes[record a] i b[h[a a] e][r b[p zperform]].
r zchoices[] j[d].r zscope[d] c.r zchoiceweight[d] b.r zratio[] b.r zpoint[] d.
r zdegrees[d] b.r zdegreecriterion[b] c.r zpoints[] j[d].r ztimeweight[d] b.
r zfrequency[] b.r zfrequencycriterion[b] c.
''' + 'r zrequired' + RULE[1:] + '.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    doc['statements'] = []
    if kind == 'degree':
        query = ('q[k r2yq[' + ARGS + ' k zratio[] k zpoint[]]].'
                 'q[k r2yr[' + ARGS + ' k zratio[] p zdegreecriterion k zpoint[]]].')
    elif kind == 'frequency':
        query = 'q[k r2ys[' + FARGS + ']].'
    else:
        query = ('d zpolicy[] e[b point[k r2ys[' + FARGS + ']]].'
                 'd zquote[] i c[e][r c[k zpolicy[]]].')
    return parse(format_graph(doc, 'compact') + EXTRA + query)


def model(doc, masks=(3, 1, 0), variant='baseline', threshold=Fraction(3, 4), weighted=False):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    def degree(mask):
        return (Fraction(0), Fraction(1, 2), Fraction(1, 2), Fraction(3, 4))[mask]
    def norm(source, person, role, act, code, sign, point):
        if (source, person, role, symbol(code), code.rank) != ('source', 'person', 'role', 'zperform', 1) or point not in TIMES:
            return False
        mask = masks[TIMES.index(point)]
        return (mask & 1 and (act, sign) == ('acta', True)) or bool(
            mask & 2 and (act, sign) == ('acta' if variant == 'contradictory' else 'actb', False))
    weights = (2, 1, 1) if weighted else (1, 1, 1)
    freq = Fraction(sum(w for w, m in zip(weights, masks) if degree(m) >= threshold and degree(m) > 0), sum(weights))
    v.update(arithmetic())
    v.update(zsource=lambda: 'source', zperson=lambda: 'person', zrole=lambda: 'role',
             zreference=lambda: 'reference', zframe=lambda: 'frame', zanchor=lambda: 'last',
             zrecords=lambda record: variant != 'empty_records' and record in ('ra', 'rb'),
             zsources=lambda record: 'role' if variant == 'other_source' and record == 'rb' else 'source',
             zpeople=lambda record: 'role' if variant == 'other_person' and record == 'rb' else 'person',
             zroles=lambda record: 'source' if variant == 'other_role' and record == 'rb' else 'role',
             zactivities=lambda record: 'acta' if record == 'ra' or variant == 'contradictory' else 'actb',
             zsigns=lambda record: record == 'ra', zrequired=norm,
             ztruth=lambda person, act, choice: person == 'person' and choice in CHOICES and (
                 choice[1] == '1' if act == 'acta' else choice[2] == '1' if act == 'actb' else False),
             zchoices=lambda: SequenceValue(
                 CHOICES[:-1] if variant == 'omitted_choice' else (*CHOICES, 'c00') if variant == 'duplicate_choice' else CHOICES,
                 '"situation"'),
             zscope=lambda choice: choice in CHOICES,
             zchoiceweight=lambda choice: Fraction(0 if variant == 'zero_choice_weight' and choice == 'c11' else 1),
             zratio=lambda: Fraction(1) if variant == 'contradictory' else Fraction(0) if variant == 'wrong_degree' else degree(masks[0]),
             zpoint=lambda: 'first',
             zdegrees=lambda point: (Fraction(1) if variant == 'contradictory' and point == 'first' else
                 Fraction(0) if variant == 'wrong_middle_degree' and point == 'middle' else
                 degree(masks[TIMES.index(point)]) if point in TIMES else Fraction(0)),
             zdegreecriterion=lambda ratio: ratio >= threshold,
             zpoints=lambda: SequenceValue(('first', 'last') if variant == 'omitted_point' else TIMES, '"situation"'),
             ztimeweight=lambda point: Fraction(weights[TIMES.index(point)] if point in TIMES else 1),
             zfrequency=lambda: Fraction(0) if variant == 'wrong_frequency' else freq,
             zfrequencycriterion=lambda ratio: ratio >= Fraction(1, 2),
             aa=lambda person: person == 'person',
             ca=lambda person, act, reference: person == 'person' and act in ('acta', 'actb') and reference == (
                 'first' if variant == 'moving_activity_scope' else 'reference'),
             cb=lambda person, act, role, reference: (person, role, reference) == ('person', 'role', 'reference') and act in ('acta', 'actb'),
             cf=lambda person, role, reference: (person, role, reference) == ('person', 'role', 'reference') and variant != 'not_private',
             h7q=lambda frame, anchor, point: frame == 'frame' and point in TIMES,
             h7r=lambda frame, anchor, point: frame == 'frame' and variant != 'empty_period' and point in (
                 ('first', 'last') if variant == 'gap' else TIMES),
             ic=lambda before, after, anchor: SCENES.index(before) < SCENES.index(after))
    return v


@lru_cache(None)
def degree_checks():
    doc = fixture('degree')
    rows = {}
    for mask in range(4):
        actual = evaluate(doc, model(doc, (mask, 0, 0)), PEOPLE, SCENES, True)
        assert actual == [True, mask == 3], (mask, actual)
        rows[str(mask)] = actual
    contrasts = {}
    for variant in ('contradictory', 'empty_records', 'other_source', 'other_person', 'other_role',
                    'omitted_choice', 'duplicate_choice', 'zero_choice_weight', 'wrong_degree',
                    'moving_activity_scope', 'not_private'):
        actual = evaluate(doc, model(doc, variant=variant), PEOPLE, SCENES, True)
        assert actual == [False, False], (variant, actual)
        contrasts[variant] = actual
    for name in ('zrequired', 'ztruth', 'cf', 'zscope'):
        v = model(doc)
        v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(positive_negative_and_combined=rows, contrasts=contrasts,
                unknown_inputs_refused=4, compatible_choice_required=True, semantic_boundaries=[])


@lru_cache(None)
def frequency_checks():
    doc = fixture('frequency')
    count = 0
    for masks in product(range(4), repeat=3):
        actual = evaluate(doc, model(doc, masks), PEOPLE, SCENES, True)[0]
        assert actual == (sum(m == 3 for m in masks) >= 2), (masks, actual)
        count += 1
    rows = {}
    for label, options, wanted in (
        ('one_of_three', {}, False),
        ('weighted_half', {'weighted': True}, True),
        ('less_strict_degree', {'threshold': Fraction(1, 2)}, True),
        ('zero_not_strong_even_with_zero_threshold', {'masks': (0, 0, 0), 'threshold': Fraction(0)}, False),
        *((v, {'variant': v, 'weighted': True}, False) for v in
          ('wrong_middle_degree', 'wrong_frequency', 'omitted_point', 'empty_period', 'gap', 'contradictory')),
    ):
        actual = evaluate(doc, model(doc, **options), PEOPLE, SCENES, True)[0]
        assert actual == wanted, (label, actual)
        rows[label] = actual
    return dict(three_time_demand_combinations=count, contrasts=rows,
                fixed_choices_and_separate_degree_frequency=True, semantic_boundaries=[])


@lru_cache(None)
def quotation_checks():
    doc = fixture('quote')
    # Keep the actual closed target, including ranked demand evaluation.
    text = format_graph(doc, 'compact')
    try:
        parse(text.replace('d zquote[] i c[e][r c[k zpolicy[]]]', 'd zquote[] i b[e][r b[k zpolicy[]]]'))
    except ValueError as error:
        assert 'strictly lower ranks' in str(error)
    else:
        raise AssertionError('Lower policy quotation rank accepted')
    return dict(rank_two_policy_accepted=True, rank_one_refused=True)


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    basis = read(BASIS)
    validate_hashes(ROOT, basis['import_source_sha256'])
    for n in basis['imported_symbols']:
        assert new.entries[n]['declaration'] == old.entries[n]['declaration']
        assert new.entries[n]['meaning_ja'] == old.entries[n]['meaning_ja']
    for p in PRIOR:
        validate_hashes(ROOT, read(p)['source_sha256'])
    for p, body in build().items():
        assert (ROOT / p).read_text(encoding='utf-8') == body
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(added_definitions=5, added_primitives=0, added_statements=0,
                imported_meanings_unchanged=True, active_manuscript_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p, body in build().items():
        write_exact(ROOT / p, body)


def build_report():
    results = {}
    for name, fn in [('degree', degree_checks), ('frequency', frequency_checks),
                     ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(read(BASIS)['import_source_sha256']) | {
        DOC, *PRIOR, 'scripts/compose_private_choice_frequency.py', 'scripts/check_private_choice_frequency.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_aligned_influence.py',
        'scripts/compose_qualitative_influence.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_scoped_counts.py', 'tests/test_private_choice_frequency.py'}
    return dict(status='private_choice_degree_and_frequency_dependency', document=LIBRARY, **results,
                interpretation=LIMITS, new_reviewed_sentence_characters=0,
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
