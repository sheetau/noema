"""Check recognized examples with native failed-experience and bodily-fall meanings."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_recognized_example import (
    ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS,
    MEANINGS, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_falling_depiction import physical_model

INDEX = 'data/semantic-review-index-v81.json'
REPORT = 'reports/recognized-example-v1.json'
AUDIT = 'data/recognized-example-reading-v1.json'
DOC = 'docs/recognized-example-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PEOPLE = ('person', 'other', 'experience', 'otherexperience', 'case')
SCENES = ('start', 'end', 'now')


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, suffix):
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, roots.split()), statements=[])
    return parse(format_graph(d, 'compact') + suffix)


@lru_cache(None)
def generic_checks():
    d = parse((ROOT/LIBRARY).read_text(encoding='utf-8') + '''
r zo[] a.r ze[] a.r zn[] d.r zp[a] c.r zr[a a d] c.r zt[a] d.r zb[d d] c.r zx[a a d] c.
q[k r2ba[k zo[] k ze[] k zn[] p zp p zr p zt p zb p zx]].
''')
    def model(bits=(True, True, True, True), variant='baseline'):
        recognized, earlier, eligible, experienced = bits
        observer = 'person' if variant == 'self' else 'other'
        return dict(zo=lambda: observer, ze=lambda: 'experience', zn=lambda: 'now',
            zp=lambda p: eligible and p == 'person',
            zr=lambda p, e, s: recognized and (p, e, s) == (
                'person' if variant == 'wrong_observer' else observer,
                'otherexperience' if variant == 'wrong_example' else 'experience',
                'end' if variant == 'wrong_recognition_time' else 'now'),
            zt=lambda e: 'start',
            zb=lambda a, b: earlier and (a, b) == ('start', 'now'),
            zx=lambda p, e, s: experienced and (p, e, s) == (
                'other' if variant == 'ineligible_experiencer' else 'person',
                'otherexperience' if variant == 'foreign_experience' else 'experience',
                'end' if variant == 'wrong_experience_time' else 'start'))
    for bits in product((False, True), repeat=4):
        assert evaluate(d, model(bits), PEOPLE, SCENES) == [all(bits)], bits
    rows = {}
    for name in ('baseline', 'self', 'wrong_observer', 'wrong_example', 'wrong_recognition_time',
            'ineligible_experiencer', 'foreign_experience', 'wrong_experience_time'):
        value = evaluate(d, model(variant=name), PEOPLE, SCENES)
        assert value == [name in ('baseline', 'self')], (name, value)
        rows[name] = value
    for name in ('zp', 'zr', 'zt', 'zb', 'zx'):
        v = model(); v[name] = unknown
        try:
            evaluate(d, v, PEOPLE, SCENES)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(combinations=16, contrasts=rows, unknown_inputs_refused=5, ordinary_evaluation=True)


NATIVE = '''
r zcase[] a.r zanchor[] d.
q[t[k gr[k zcase[]]][k zanchor[]]].
q[k r2ba[k gd[k zcase[]] k ge[k zcase[]] k zanchor[] p aa p gg p f7 p dd p fg]].
q[t[k r2bb[k zcase[]]][k zanchor[]]].
'''


def native_model(d, variant='baseline', mind=True, body=True):
    v = physical_model(d, variant)
    observer = 'person' if variant == 'self' else 'other'
    def trial(p, e, g, s):
        return (p, e, s) == ('person', 'experience', 'start') and (
            mind and symbol(g) == 'bb' or body and symbol(g) == 'zal')
    v.update(zcase=lambda: 'case', zanchor=lambda: 'now', gd=lambda case: observer,
        ge=lambda case: 'otherexperience' if variant == 'different_selected_example' else 'experience',
        gg=lambda p, e, s: variant != 'unrecognized' and (p, e, s) == (
            'person' if variant == 'different_recognizer' else observer, 'experience', 'now'),
        f7=lambda e: 'end' if variant == 'different_experience_time' else 'start',
        dd=lambda a, b: SCENES.index(a) < SCENES.index(b) and not (
            variant == 'not_prior' and (a, b) == ('start', 'now')),
        aa=lambda p: variant != 'ineligible_experiencer' and p == 'person',
        f5=trial, ab=lambda *args: False, ac=lambda *args: False, ad=lambda *args: False)
    return v


@lru_cache(None)
def native_checks():
    d = fixture('gr r2ba r2bb', NATIVE); rows = []
    for mind, body in product((False, True), repeat=2):
        actual = evaluate(d, native_model(d, mind=mind, body=body), PEOPLE, SCENES, True)
        assert actual == [mind, mind, body], (mind, body, actual)
        rows.append(dict(intellectual=mind, bodily=body, values=actual))
    contrasts = {}
    shared = {'different_selected_example', 'unrecognized', 'different_recognizer',
        'different_experience_time', 'not_prior', 'ineligible_experiencer', 'missing_result', 'foreign_result'}
    for name in ('baseline', 'self', *sorted(shared), 'other_falling_person', 'other_falling_experience',
            'no_occurrence', 'no_transition', 'still_standing', 'no_lower_contact', 'no_descent', 'controlled_lowering'):
        actual = evaluate(d, native_model(d, name), PEOPLE, SCENES, True)
        expected = [name not in shared]*2 + [name in ('baseline', 'self')]
        assert actual == expected, (name, actual, expected)
        contrasts[name] = actual
    for name in ('gg', 'f7', 'f5', 'f6', 'hzul'):
        v = native_model(d); v[name] = unknown
        try:
            evaluate(d, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(independent_contents=rows, contrasts=contrasts, unknown_inputs_refused=5,
        columns=['existing_gr', 'general_recognized_experience_with_fg', 'recognized_bodily_fall'],
        current_failure_and_fall_definitions_executed=True, observer_may_differ_from_experiencer=True,
        pure_memoization=True)


@lru_cache(None)
def attribution_checks():
    d = parse((ROOT/CORE).read_text(encoding='utf-8')); rows = {}
    for name in ('baseline', 'other_author', 'learning_clause_only', 'other_context',
            'reversed', 'learning_prospect_only', 'bare_fall_only'):
        v = {x['name']: unknown for x in d['declarations'] if x['kind'] == 'primitive'}
        v.update(g2=lambda: 'deterrence', wa=lambda: 'author', wh=lambda: 'context',
            qa=lambda n, a, t, b, s: (n, a, symbol(t), symbol(b), s) == (
                'learning' if name == 'learning_clause_only' else 'deterrence',
                'other' if name == 'other_author' else 'author',
                'r2bb' if name == 'reversed' else 'fr' if name == 'learning_prospect_only' else 'gr',
                'gr' if name == 'reversed' else 'hzum' if name == 'bare_fall_only' else 'r2bb',
                'elsewhere' if name == 'other_context' else 'context'))
        actual = evaluate(d, v, ('deterrence', 'learning', 'author', 'other'), ('context', 'elsewhere'))
        assert actual == [name == 'baseline'], (name, actual)
        rows[name] = actual
    v['qa'] = unknown
    try:
        evaluate(d, v, ('deterrence', 'author'), ('context',))
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown depiction accepted')
    return dict(contrasts=rows, all_world_contents_unknown=True, unknown_inputs_refused=1)


def reading():
    unit = next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units']
        if u['id'] == 'kant-1784:u0009')
    text = 'ein Beispiel von der Art'; start = unit['text'].index(text)
    paths = (INDEX, INVENTORY, PARENT, PARENT_BASIS, FULL, BASIS,
        'data/walking-acquisition-reading-v1.json', 'reports/walking-acquisition-v1.json',
        'reports/falling-depiction-v1.json', 'artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='recognized_prior_fall_depiction_connected', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start+len(text)], text=text),
        references=['https://korpora.org/Kant/aa08/036.html'],
        decision='そのような一例を、先行する転倒経験の種類を受ける例として、後続する萎縮節の同じ事例へ接続する。',
        selection=selection_binding(catalog(), [51]), interpretation_limits=LIMITS,
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def structure():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-3] == old.document['declarations']
    assert new.document['statements'][:-1] == old.document['statements']
    assert len(new.document['statements']) == 52
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert set(new.entries)-set(old.entries) == set(MEANINGS)
    index = json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review = json.loads((ROOT/path).read_text(encoding='utf-8'))
        ids = [s['index'] for s in review['selection']['statements']]
        assert review['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    preceding = json.loads((ROOT/'reports/guarded-walking-reading-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT, preceding['source_sha256'])
    bindings = [r['current_selection'] for r in preceding['preceding']['reviews'].values()]
    bindings.append(json.loads((ROOT/'data/guarded-walking-reading-v1.json').read_text(encoding='utf-8'))['selection'])
    for binding in bindings:
        assert binding == selection_binding(new, [s['index'] for s in binding['statements']])
    for path, body in build().items():
        assert (ROOT/path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE, LIBRARY):
        d = parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(d, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    r = reading(); assert r == json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))
    validate_hashes(ROOT, r['source_sha256'])
    return dict(new_definitions=3, new_primitives=0, preserved_statements=51, total_statements=52,
        preserved_review_selections=11, preserved_reviewed_sentence_characters=1021, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT/AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('native', native_checks),
            ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn(); print(name+' checked', flush=True)
    r = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(r['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_recognized_example.py', 'scripts/check_recognized_example.py',
        'scripts/register_recognized_example.py', 'tests/test_recognized_example.py',
        'scripts/check_falling_depiction.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py', 'noema/constructed.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='recognized_prior_example_with_native_failure_and_fall_evidence', document=FULL, **results,
        alignment=dict(**r['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, new_verified_sentence_characters=0, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT/REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
