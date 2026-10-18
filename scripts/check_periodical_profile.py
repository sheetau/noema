"""Check numeric cadence, editorial bindings and nonfactive periodical naming."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import argparse
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts import check_current_footnote as prior
from scripts.check_gregorian_rules import SCALARS, sequence
from scripts.compose_periodical_profile import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, MEANINGS, LIMITS, build, parent, closure

REPORT = 'reports/periodical-profile-v1.json'
READING = 'data/periodical-profile-reading-v1.json'
DOMAIN = (*prior.DOMAIN, 'busching', 'busching_name')
SCENES = prior.SCENES


def unknown(*args):
    raise ValueError('Unknown periodical-profile interpretation')


@lru_cache(None)
def generic():
    text = (ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r zp[] a.r zs[] a.r zcal[] a.r zctx[] d.r zd[] j[b].r zn[] j[b].
r zcadence[a a b b d] c.r zeditor[a a d] c.
q[k rqw4[k zs[] k zcal[] k zd[] k zn[] k zctx[] p zcadence]].
q[k rqw5[k zp[] k zs[] k zcal[] k zd[] k zn[] k zctx[] p zcadence p zeditor]].
'''
    return parse(text)


def evaluate(doc, values):
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=SCENES,
        primitives={d['name']: values[d['name']] for d in doc['declarations'] if d['kind'] == 'primitive'},
        max_steps=3000000, memoize_definitions=False, memoize_expressions=False)]


def generic_model(days=(7,), issues=(1,), cadence=True, responsible=True):
    return dict(SCALARS, zp=lambda: 'busching', zs=lambda: 'weekly_series', zcal=lambda: 'calendar', zctx=lambda: 'note',
        zd=lambda: sequence(days), zn=lambda: sequence(issues), zcadence=lambda *args: cadence, zeditor=lambda *args: responsible)


def numeral_checks():
    values = [[], [0], [1], [7], [14], [1, 0], [0, 7], [-1], [32], [Fraction(1, 2)]]
    valid = lambda xs: bool(xs) and all(x.denominator == 1 and 0 <= x < 32 for x in map(Fraction, xs)) and any(xs)
    count = 0
    for days, issues in product(values, repeat=2):
        result = evaluate(generic(), generic_model(days, issues))
        assert result == [valid(days) and valid(issues)] * 2, (days, issues, result)
        count += 1
    rows = {}
    for cadence, responsible in product((False, True), repeat=2):
        result = evaluate(generic(), generic_model(cadence=cadence, responsible=responsible))
        assert result == [cadence, cadence and responsible]
        rows[str((cadence, responsible))] = result
    for name in ('zcadence', 'zeditor'):
        m = generic_model()
        m[name] = unknown
        try:
            evaluate(generic(), m)
        except ValueError as error:
            assert 'Unknown periodical-profile' in str(error)
        else:
            raise AssertionError(name)
    return dict(numeral_pairs=count, independent_relations=rows, unknown_inputs_refused=2,
        zero_negative_fractional_empty_and_out_of_range_digits_rejected=True)


@lru_cache(None)
def doc(mode='description'):
    d = parse((ROOT / FULL).read_text(encoding='utf-8'))
    indices = [41] if mode != 'joint' else [*prior.SELECTION, 41]
    d['statements'] = [d['statements'][i] for i in indices]
    d['declarations'] = closure(d, ['hzwg', 'hzwe', 'hzwf'] + (prior.SYMBOLS if mode == 'joint' else []))
    if mode == 'factual':
        d['declarations'].append({'kind': 'primitive', 'name': 'zpublished', 'parameters': [], 'result': 'truth'})
        d = parse(format_graph(d, 'compact') + 'q[t[k hzwe[k hzkd[]]][k hzjl[]]].q[k zpublished[]].')
    return d


def model(variant='baseline', cadence=None, responsible=None, published=False):
    d = doc('joint')
    m = {x['name']: unknown for x in d['declarations'] if x['kind'] == 'primitive'}
    inherited = variant if variant in prior.EXPECTED_FALSE else 'baseline'
    m.update(prior.model(inherited))
    m.update(hzwc=lambda: 'busching', hzwd=lambda: 'busching_name', zpublished=lambda: published)
    names = m['hzih']
    m['hzih'] = lambda use, name, person, ctx: names(use, name, person, ctx) or variant != 'missing_person_name' and (
        use, name, person, ctx) == ('naming', 'busching_name', 'other' if variant == 'other_named_person' else 'busching', 'note')

    def description(author, use, target, content, ctx):
        if variant == 'unknown_description':
            return unknown()
        return variant != 'missing_description' and (author, use, ctx) == (
            'other' if variant == 'other_author' else 'author', 'mention' if variant == 'other_use' else 'naming',
            'branch' if variant == 'other_description_context' else 'note') and json.loads(target.syntax) == {
                'kind': 'function_ref', 'symbol': 'hzmb' if variant == 'person_as_series' else 'hzwf'} and json.loads(content.syntax) == {
                'kind': 'function_ref', 'symbol': 'hzwf' if variant == 'bare_name_only' else 'hzwe'}

    m['hzwh'] = description
    if cadence is not None:
        m.update(SCALARS)
        expected = ['weekly_series', 'calendar', Fraction(7), Fraction(1), 'note']
        replacements = {'other_series': (0, 'monthly_series'), 'other_calendar': (1, 'other'),
            'fortnightly_pair': (2, Fraction(14)), 'twice_weekly': (3, Fraction(2)), 'other_profile_context': (4, 'branch')}
        if variant in replacements:
            i, value = replacements[variant]
            expected[i] = value
        if variant == 'fortnightly_pair':
            expected[3] = Fraction(2)
        m['hzwa'] = lambda *args: cadence and list(args) == expected
    if responsible is not None:
        m['hzwb'] = lambda person, series, ctx: responsible and (person, series, ctx) == (
            'other' if variant == 'other_editor' else 'busching',
            'monthly_series' if variant == 'other_editor_series' else 'weekly_series',
            'branch' if variant == 'other_editor_context' else 'note')
    return m


def description_checks():
    rows = {}
    variants = ('baseline', 'missing_person_name', 'other_named_person', 'missing_description', 'other_author',
        'other_use', 'other_description_context', 'person_as_series', 'bare_name_only')
    for variant in variants:
        result = evaluate(doc(), model(variant))
        assert result == [variant == 'baseline'], (variant, result)
        rows[variant] = result
    for name in ('hzwc', 'hzwd', 'hzih', 'hzwh'):
        m = model()
        m[name] = unknown
        try:
            evaluate(doc(), m)
        except ValueError as error:
            assert 'Unknown periodical-profile' in str(error)
        else:
            raise AssertionError(name)
    # Describing a nominal weekly policy neither evaluates nor certifies it.
    try:
        evaluate(doc('factual'), model())
    except ValueError as error:
        assert 'Unknown periodical-profile' in str(error)
    else:
        raise AssertionError('Actual unknown profile silently inferred from its title')
    truth_rows = []
    for cadence, responsible, published in product((False, True), repeat=3):
        result = evaluate(doc('factual'), model(cadence=cadence, responsible=responsible, published=published))
        assert result == [True, cadence and responsible, published]
        truth_rows.append(result)
    return dict(description_cases=rows, actual_profile_and_publication_combinations=truth_rows,
        unknown_bindings_refused=4, unknown_actual_profile_refused=True,
        conventional_cadence_distinct_from_actual_issuance=True)


def binding_checks():
    rows = {}
    for variant in ('baseline', 'other_series', 'other_calendar', 'fortnightly_pair', 'twice_weekly',
        'other_profile_context', 'other_editor', 'other_editor_series', 'other_editor_context'):
        result = evaluate(doc('factual'), model(variant, cadence=True, responsible=True))
        assert result == [True, variant == 'baseline', False], (variant, result)
        rows[variant] = result
    return dict(cases=rows, equal_average_frequency_not_same_cycle=True,
        calendar_series_person_context_and_both_quantities_preserved=True)


def joint_checks():
    rows = {}
    for variant in ('baseline', 'other_current_question', 'no_note_link', 'other_trial_question',
        'missing_person_name', 'missing_description'):
        false = prior.EXPECTED_FALSE.get(variant, ())
        want = [i not in false for i in range(11)] + [variant not in ('missing_person_name', 'missing_description')]
        result = evaluate(doc('joint'), model(variant))
        assert result == want, (variant, result)
        rows[variant] = result
    return dict(cases=rows, twelve_assertions_share_existing_references=True,
        descriptive_contents_remain_unevaluated=True, memoization=False)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    for name, body in build().items():
        assert (ROOT / name).read_text(encoding='utf-8') == body, name
    assert new.document['statements'][:-1] == old.document['statements'] and len(new.document['statements']) == 42
    assert new.document['declarations'][:-10] == old.document['declarations']
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    for name in (FULL, CORE, LIBRARY):
        d = parse((ROOT / name).read_text(encoding='utf-8'))
        for notation in ('full', 'compact'):
            text = format_graph(d, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    index = json.loads((ROOT / prior.INDEX).read_text(encoding='utf-8'))
    for name in index['works']['kant-1784']['reviews']:
        review = json.loads((ROOT / name).read_text(encoding='utf-8'))
        indices = [s['index'] for s in review['selection']['statements']]
        assert selection_binding(new, indices) == review['selection']
    ann = load_annotations(ROOT, BASIS, ANNOTATIONS).show()['entries']
    old_ann = load_annotations(ROOT, prior.BASIS, 'data/explanatory-question-identifiers-v1.json').show()['entries']
    assert ann[:-1] == old_ann and ann[-1]['symbol'] == 'hzwd'
    return dict(new_definitions=5, new_general_relations=3, new_local_references=2, preserved_statements=41,
        appended_statement=41, preserved_review_selections=10, roundtrips=True, names_kept_outside_meaning=True)


def reading():
    inv = json.loads((ROOT / prior.INVENTORY).read_text(encoding='utf-8'))
    unit = next(u for u in inv['units'] if u['id'] == 'kant-1784:u0020')
    paths = ['artifacts/weekly-publication-v1/canvas-299.jpg', 'artifacts/author-signature-facsimile-v1/page-494.jpg',
        'data/announced-answer-evidence-v1.json', prior.INVENTORY]
    return dict(status='periodical_profile_reading_from_source_and_primary_heading', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[3, 72], text=unit['text'][3:72]),
        images=[dict(path=paths[0], page=289, visually_inspected=True,
            url='https://api.digitale-sammlungen.de/iiif/image/v2/bsb10429071_00299/full/full/0/default.jpg'),
            dict(path=paths[1], page=494, visually_inspected=True)],
        observation='週報の表題にはAnton Friderich BüschingsとWöchentliche Nachrichtenがあり、日付と版元の表示は別の行にある。カントの呼び方は人物への帰属を含む短い系列名である。',
        decision='人物への編集上の帰属と、慣行としての暦上7日周期・通常1号という性質を、同じ系列の呼称内の記述として保持する。実際の全発行履歴を主張せず、欠刊・特別号・暦日の長さや周期の始点を補わない。',
        limits=LIMITS, whole_unit_semantically_verified=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    result = {}
    for name, fn in [('numerals', numeral_checks), ('description', description_checks), ('bindings', binding_checks),
        ('joint', joint_checks), ('structure', structure)]:
        result[name] = fn()
        print(name + ' checked', flush=True)
    note = reading()
    assert json.loads((ROOT / READING).read_text(encoding='utf-8')) == note
    previous = json.loads((ROOT / prior.REPORT).read_text(encoding='utf-8'))
    validate_hashes(ROOT, previous['source_sha256'])
    paths = set(build()) | set(parent().source_sha256) | set(note['source_sha256']) | {READING, prior.REPORT, prior.INDEX,
        'scripts/compose_periodical_profile.py', 'scripts/check_periodical_profile.py', 'tests/test_periodical_profile.py',
        'docs/periodical-profile-v1.md', 'scripts/check_current_footnote.py', 'scripts/check_gregorian_rules.py',
        'scripts/compose_gregorian_rules.py', 'scripts/compose_qualified_judgment.py', 'scripts/compose_falling_depiction.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py',
        'noema/semantic_reviews.py', 'noema/identifiers.py', 'noema/script.py'}
    source = note['source']
    return dict(status='partial_periodical_profile_with_explicit_nominal_cadence', document=FULL, **result,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'], source=source['text'],
            definitions=list(MEANINGS), status='explicit_interpretive_annotation', full_semantic_equivalence=False),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / READING, encoded(reading()))
    report = build_report()
    if args.verify_only:
        assert json.loads((ROOT / REPORT).read_text(encoding='utf-8')) == report
    else:
        write_exact(ROOT / REPORT, encoded(report))
    print('Periodical profile and twelve connected assertions checked', flush=True)


if __name__ == '__main__':
    main()
