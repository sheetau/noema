"""Check canonical contents, recipient-indexed rows and open comparison scope."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_demand_candidates import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, ALIGN_BASIS, ALIGN_LIBRARY,
    CASES, CONTENTS, CODE, MEANINGS, LIMITS, parent, aligned, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_command_alternatives as commands

INDEX = 'data/semantic-review-index-v153.json'
REPORT = 'reports/demand-candidates-v1.json'
DOC = 'docs/demand-candidates-v1.md'
LABELS = ('military', 'fiscal', 'clergy', 'royal')
RECIPIENTS = ('recipient', 'second')
PEOPLE = (*LABELS, *RECIPIENTS, 'extra', 'factor', 'outcome', 'public',
          'role-recipient', 'role-second',
          *(c + '-source' for c in LABELS), *(c + '-call' for c in LABELS),
          *(c + '-plan' for c in LABELS))
SCENES = ('reference', 'on', 'off', 'choice', 'otherpoint')


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    boundaries = {
        'anchors': ('r2uv',),
        'rows': ('r2ux',),
        'profile': ('r2uv', 'r2vr', 'r2vs', 'r2vt', 'r2vu'),
    }.get(kind, ())
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    roots = {
        'anchors': ['r2wa'], 'rows': ['r2wb', 'r2wc', *CONTENTS],
        'profile': ['r2wd', 'r2wf', 'r2wg', 'r2wh'], 'scope': ['r2we'],
        'contents': list(CONTENTS),
    }[kind]
    extra = ''
    if kind == 'contents':
        old = commands.fixture('combined')
        support = [d for d in old['declarations'] if d['name'].startswith('z')]
        teaching = next(d for d in old['declarations'] if d['name'] == 'h233b')
        replacement = parse('p:r zobey[a a d d] c.'
                            'd r2ud[source a person a reference d] e['
                            'b point[k zobey[v source v person v reference v point]]].')
        lookup = {d['name']: d for d in replacement['declarations']}
        lookup['h233b'] = teaching
        doc['declarations'] = support + [replacement['declarations'][0]] + [
            lookup.get(d['name'], d) for d in doc['declarations']]
        roots += [d['name'] for d in support]
        extra = ''.join('r zplan' + str(i + 2) + '[] a.' for i in range(4))
        queries = ''.join('q[t[k ' + name + '[k zp[] k zplan' + str(i + 2) +
                          '[]]][k zt[]]].' for i, name in enumerate(CONTENTS))
    elif kind == 'anchors':
        queries = ''.join('q[k r2wa[k ' + case + '[] r b[p ' + code + ']]].'
                          for case in CASES for code in CONTENTS)
    elif kind == 'rows':
        extra = 'r zon[] d.r zoff[] d.'
        queries = ''.join(
            'q[k r2wb[k ' + case + '[] r b[p ' + code + '] e[n p a b][n p a b] k zon[]]].'
            'q[k r2wb[k ' + case + '[] r b[p ' + code + '] u[e[n p a b][n p a b]] k zoff[]]].'
            'q[k r2wc[k ' + case + '[] r b[p ' + code + ']]].' for case, code in zip(CASES, CONTENTS))
    elif kind == 'profile':
        extra = '''r zvariables[] j[a].r zequation[a h[a] c] c.r zfactor[] a.
r zworld[h[a] c] d.r zpublic[] a.
r zevaluated[a d i b[h[a d] e] d] c.
r zatleast[a d i b[h[a d] e] d d] c.
'''
        tail = 'k zvariables[] p zequation k zfactor[] p zworld k zpublic[] p zevaluated p zatleast'
        queries = ''.join('q[k ' + fn + '[k ' + case + '[] r b[p ' + code + '] ' + tail + ']].'
                          for case, code in zip(CASES, CONTENTS) for fn in ('r2wd', 'r2wf', 'r2wg', 'r2wh'))
    else:
        extra = 'r zscope[a] c.'
        queries = 'q[k r2we[p zscope]].'
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra + queries)


def model(doc, variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update({n: (lambda value=value: value) for n, value in zip(CASES, LABELS)})
    v.update(h232v=lambda: 'reference', zon=lambda: 'on', zoff=lambda: 'off',
             h234l=lambda c, ref: c + '-source',
             h234m=lambda c, ref: c + '-call',
             h234q=lambda c: c + '-plan',
             h234r=lambda c, p, ref: 'role-second' if p == 'second' else 'role-recipient')

    def audience(call, ref, person):
        if variant == 'missing_second':
            return ref == 'reference' and person == 'recipient'
        return ref == 'reference' and person in RECIPIENTS and (
            call in {c + '-call' for c in LABELS[:3]} or call == 'royal-source')

    def demand(source, person, role, activity, content, sign, point):
        if activity not in {c + '-plan' for c in LABELS}:
            return False
        case = activity[:-5]
        code = CONTENTS[LABELS.index(case)]
        metadata = (source == ('extra' if variant == 'wrong_source' else case + '-source')
                    and person in RECIPIENTS and role == ('extra' if variant == 'wrong_role' else 'role-' + person)
                    and content.rank == 1 and symbol(content) == code and sign)
        active = point == 'on' and not (variant == 'partial_application' and person == 'second')
        active |= point == 'off' and variant == 'partial_withdrawal' and person == 'second'
        return metadata and active

    v.update(h232u=audience, h233p=audience, h234s=demand,
             h234n=lambda c, p, ref, base, point: variant != 'no_choice' and (
                 p, ref, base, point) == ('extra' if variant == 'outsider_choice' else 'recipient',
                                        'reference', 'reference', 'choice'),
             r2ux=lambda c, source, person, ref, point: variant == 'all_choices_comply' or
                 (person, source, ref, point) != ('recipient', c + '-source', 'reference', 'choice'),
             r2uv=lambda c, source, call, ref, point: (
                 source, call, symbol(ref), point) == (
                     'extra' if variant == 'wrong_anchor_source' else c + '-source',
                     'extra' if variant == 'wrong_anchor_call' else c + '-call',
                     'otherref' if variant == 'wrong_anchor_reference' else 'h232v', 'reference'))
    return v


@lru_cache(None)
def content_checks():
    doc = fixture('contents')
    plans = tuple(c + '-plan' for c in LABELS)
    people = (*commands.PEOPLE, *LABELS, *plans)
    rows = []
    for flags in product((False, True), repeat=5):
        v = commands.model(doc, flags=flags[:4])
        v.update({n: (lambda value=value: value) for n, value in zip(CASES, LABELS)})
        v.update({n: (lambda value=value: value) for n, value in zip(
            ('zplan2', 'zplan3', 'zplan4', 'zplan5'), plans)})
        v.update(h232v=lambda: 'reference', h234q=lambda c: c + '-plan', h234l=lambda c, ref: 'second',
                 zobey=lambda source, person, ref, point: flags[4] and (
                     source, person, ref, point) == ('second', 'first', 'reference', 'later'))
        actual = evaluate(doc, v, people, commands.SCENES, True)
        wanted = [not flags[0] and b for b in flags[1:4]] + [flags[4]]
        assert actual == wanted, (flags, actual)
        rows.append(dict(flags=flags, result=actual))
        if flags == (False, True, True, True, True):
            assert actual == [True] * 4
            v.update(zplan2=lambda: plans[1], zplan3=lambda: plans[2],
                     zplan4=lambda: plans[3], zplan5=lambda: plans[0])
            assert evaluate(doc, v, people, commands.SCENES, True) == [False] * 4
    return dict(matrix=rows, wrong_activity_types_rejected=True,
                ruler_permission_not_negated=True, same_person_and_source=True,
                semantic_boundaries=['r2ud is a native content wrapper around a checked source/person/reference predicate in this fixture; full-description coverage and its finite refusal remain in the prior free-choice-obedience report'])


@lru_cache(None)
def anchor_checks():
    doc = fixture('anchors')
    expected = [i == j for i in range(4) for j in range(4)]
    actual = evaluate(doc, model(doc), PEOPLE, SCENES, True)
    assert actual == expected, actual
    rows = {'baseline': actual}
    for variant in ('wrong_anchor_source', 'wrong_anchor_call', 'wrong_anchor_reference'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [False] * 16, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, same_prior_speaker_call_reference_and_canonical_code=True,
                normative_application_not_inferred=True,
                semantic_boundaries=['r2uv: previously checked four-way role and speech linkage'])


@lru_cache(None)
def row_checks():
    doc = fixture('rows')
    rows = {}
    cases = {'baseline': [True, True, True], 'partial_application': [False, True, True],
             'partial_withdrawal': [True, False, True], 'wrong_source': [False, True, True],
             'wrong_role': [False, True, True], 'no_choice': [True, True, False],
             'outsider_choice': [True, True, False], 'all_choices_comply': [True, True, False]}
    for variant, triple in cases.items():
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == triple * 4, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, every_fixed_recipient_has_one_whole_command_row=True,
                complete_application_and_withdrawal_kept=True, same_person_choice_required=True,
                semantic_boundaries=['r2ux: native selection and contents separately checked; r2ud limitation retained'])


@lru_cache(None)
def profile_checks():
    doc = fixture('profile')
    rows = {}
    for variant in ('baseline', 'wrong_anchor_source', 'wrong_anchor_call', 'wrong_anchor_reference'):
        v = model(doc, variant)
        v.update(zvariables=lambda: SequenceValue(('factor', 'outcome'), '"individual"'),
                 zfactor=lambda: 'factor', zequation=lambda variable, state: variable == 'outcome' and state('factor'),
                 zworld=lambda state: 'on' if state('factor') else 'off', zpublic=lambda: 'public',
                 zevaluated=unknown, zatleast=unknown)
        seen = []

        def inspect(*args, result):
            (records, sources, people, roles, activities, codes, signs, required, variables,
             equations, factor, worlds, choices, public, reference, evaluated, atleast) = args
            assert tuple(x for x in PEOPLE if records(x)) == RECIPIENTS
            case = activities('recipient')[:-5]
            assert case in LABELS
            for person in RECIPIENTS:
                assert (sources(person), people(person), roles(person), activities(person), codes(person).rank,
                        symbol(codes(person)), signs(person)) == (
                    case + '-source', person, 'role-' + person, case + '-plan', 1,
                    CONTENTS[LABELS.index(case)], True)
                assert required(sources(person), people(person), roles(person), activities(person),
                                codes(person), signs(person), 'on')
                assert choices(person, 'choice') == (person == 'recipient')
            assert variables.items == ('factor', 'outcome')
            assert (factor, public, reference) == ('factor', 'public', 'reference')
            seen.append(case)
            return result

        for name, result in zip(('r2vr', 'r2vs', 'r2vt', 'r2vu'), (True, False, True, True)):
            v[name] = lambda *args, result=result: inspect(*args, result=result)
        actual = evaluate(doc, v, PEOPLE, SCENES, True)
        assert actual == ([True, False, True, True] * 4 if variant == 'baseline' else [False] * 16)
        assert set(seen) == set(LABELS)
        rows[variant] = actual
    return dict(contrasts=rows, all_record_slots_and_fixed_reference_passed=True,
                semantic_boundaries=['r2vr/r2vs/r2vt/r2vu: native generic alignment and comparison checked in aligned-restriction-influence-v1; this check verifies the concrete bindings'])


@lru_cache(None)
def scope_checks():
    doc = fixture('scope')
    rows = {}
    for name, selected in [('four', set(LABELS)), ('plus_fifth', {*LABELS, 'extra'}),
                           ('missing_royal', set(LABELS[:3])), ('empty', set())]:
        v = model(doc)
        v.update(zscope=lambda item: item in selected, ha=lambda a, b: a + b,
                 hc=lambda a, b: a < b, hd=lambda truth: Fraction(int(truth)))
        actual = evaluate(doc, v, PEOPLE, SCENES, True)
        assert actual == [name in ('four', 'plus_fifth')], (name, actual)
        rows[name] = actual
    v['h233n'] = lambda: 'military'
    v['zscope'] = lambda item: item in LABELS
    assert evaluate(doc, v, PEOPLE, SCENES, True) == [False]
    return dict(contrasts=rows, all_four_required_but_more_candidates_allowed=True,
                duplicate_antecedent_nodes_refused=True)


@lru_cache(None)
def structure_checks():
    old, new, earlier = parent(), catalog(), aligned()
    assert old.document['statements'] == new.document['statements']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    for name in earlier.entries:
        for key in ('declaration', 'meaning_ja'):
            assert new.entries[name][key] == earlier.entries[name][key], (name, key)
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path in ('data/everywhere-restriction-reading-v1.json', 'data/single-ruler-reading-v1.json',
                 'data/role-commands-reading-v1.json', 'data/heard-prohibition-reading-v1.json'):
        record = json.loads((ROOT / path).read_text(encoding='utf-8'))
        assert record['selection'] == selection_binding(new, [s['index'] for s in record['selection']['statements']])
        validate_hashes(ROOT, record['source_sha256'])
    validate_hashes(ROOT, json.loads((ROOT / 'reports/aligned-restriction-influence-v1.json').read_text(encoding='utf-8'))['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_statements=70,
                preserved_reviewed_sentence_characters=496, added_statements=0,
                new_semantically_reviewed_characters=0, old_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    result = {}
    for name, fn in [('contents', content_checks), ('anchors', anchor_checks), ('rows', row_checks),
                     ('profiles', profile_checks), ('scope', scope_checks), ('structure', structure_checks)]:
        result[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, DOC, ALIGN_BASIS, ALIGN_LIBRARY, 'reports/aligned-restriction-influence-v1.json',
        'reports/everywhere-restriction-v1.json', 'reports/free-choice-obedience-v1.json',
        'scripts/compose_demand_candidates.py', 'scripts/check_demand_candidates.py',
        'tests/test_demand_candidates.py', 'scripts/check_command_alternatives.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'data/everywhere-restriction-reading-v1.json', 'data/single-ruler-reading-v1.json',
        'data/role-commands-reading-v1.json', 'data/heard-prohibition-reading-v1.json'}
    return dict(status='partial_demand_candidate_source_bindings_checked', document=FULL,
                **result, limitations=LIMITS, whole_sentence_semantically_verified=False,
                whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
