"""Check the same public-use content against all freedom forms without executing it."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_freedom_comparison import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, FAMILY, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v145.json'
REPORT = 'reports/freedom-comparison-v1.json'
AUDIT = 'data/freedom-comparison-reading-v1.json'
DOC = 'docs/freedom-comparison-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/public-topics-v1.json', 'reports/fourth-paragraph-v1.json']
PEOPLE = ('public', 'otherpublic', 'firstkind', 'secondkind', 'thirdkind', 'outside')
SCENES = ('reference', 'othercontext')
EXTRA = (f'r zpick[a d {FAMILY} {FAMILY} {FAMILY}] {FAMILY}.'
         'r zg[] a.r zr[] d.r zf[] a.')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind='all'):
    doc = deepcopy(catalog().document)
    extras = parse('p:' + EXTRA)['declarations']
    replacement = parse(format_graph(dict(doc, statements=[]), 'compact') + EXTRA +
                        f'd zprovider[form a reference d] {FAMILY}['
                        'k zpick[v form v reference r b[p r2sl] r b[p r2lm] r b[p r2ln]]'
                        '].')['declarations'][-1]
    replacement['name'] = 'h232c'
    doc['declarations'] = extras + [
        replacement if d['name'] == 'h232c' else d for d in doc['declarations']]
    doc.update(declarations=closure(doc, [*MEANINGS, *[d['name'] for d in extras]]), statements=[])
    questions = (
                 'q[k r2sm[k zg[] k zr[] k zf[]]].'
                 'q[k r2sn[k zg[] k zr[]]].')
    if kind == 'all':
        questions += 'q[t[k r2so[]][k zr[]]].'
    return parse(format_graph(doc, 'compact') + questions)


def model(doc, variant='baseline', seen=None):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    def scope(form, reference):
        if seen is not None:
            seen.append(('scope', reference))
        return reference == 'reference' and variant != 'empty_forms' and form in (
            ('secondkind', 'thirdkind') if variant == 'focal_outside_scope'
            else ('firstkind', 'secondkind', 'thirdkind'))
    def supply(form, reference, focal, second, third):
        if seen is not None:
            seen.append(('supply', reference))
        assert all(d.rank == 1 for d in (focal, second, third))
        assert tuple(symbol(d) for d in (focal, second, third)) == ('r2sl', 'r2lm', 'r2ln')
        return dict(firstkind=second if variant == 'wrong_focal_content' else focal,
                    secondkind=focal if variant == 'two_names_one_content' else second,
                    thirdkind=third).get(form, third)
    def leq(first, second, public, reference):
        if seen is not None:
            seen.append(('compare', public, reference, symbol(first), symbol(second)))
        expected_public = 'otherpublic' if variant == 'wrong_public' else public
        expected_reference = 'othercontext' if variant == 'wrong_context' else 'reference'
        if public != expected_public or reference != expected_reference:
            return False
        left, right = symbol(first), symbol(second)
        assert first.rank == second.rank == 1
        scores = dict(r2sl=1, r2lm=2, r2ln=3)
        if variant == 'tied_minimum':
            scores['r2lm'] = 1
        if variant == 'another_form_less_harmful' or variant == 'second_public_fails' and public == 'otherpublic':
            scores.update(r2sl=2, r2lm=1)
        if variant == 'nonreflexive' and left == right == 'r2lm':
            return False
        if variant == 'incomparable' and {left, right} == {'r2lm', 'r2ln'}:
            return False
        if variant == 'cyclic_comparison':
            return left == right or (left, right) in {('r2sl', 'r2lm'), ('r2lm', 'r2ln'), ('r2ln', 'r2sl')}
        return scores[left] <= scores[right]
    values.update(zg=lambda: 'public', zr=lambda: 'reference', zf=lambda: 'firstkind',
                  h232b=scope, zpick=supply, h232d=leq,
                  h222e=lambda public, reference: reference == 'reference' and variant != 'empty_publics'
                      and public in ('public', 'otherpublic'))
    return values


@lru_cache(None)
def minimum_checks():
    doc = fixture()
    rows = {}
    for variant in ('baseline', 'tied_minimum', 'another_form_less_harmful', 'empty_forms',
                    'focal_outside_scope', 'nonreflexive', 'incomparable', 'cyclic_comparison'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant in ('baseline', 'tied_minimum')] * 3, (variant, actual)
        rows[variant] = actual
    # Check direction independently: when another form is less harmful, it is
    # the native minimum, but it cannot supply the public-use content.
    values = model(doc, 'another_form_less_harmful')
    values['zf'] = lambda: 'secondkind'
    actual = evaluate(doc, values, PEOPLE, SCENES, True)
    assert actual == [True, False, False]
    rows['minimum_is_another_form'] = actual
    return dict(contrasts=rows, native_rce_rcd=True, ties_allowed=True,
                no_unique_or_zero_harm_assumption=True, incomplete_and_cyclic_comparisons_rejected=True)


@lru_cache(None)
def binding_checks():
    # Content construction evaluates all finite situations. Isolate the two
    # point-level calls when checking their fixed-reference argument trace.
    doc = fixture('binding')
    rows = {}
    for variant in ('baseline', 'wrong_focal_content', 'two_names_one_content',
                    'wrong_public', 'wrong_context'):
        seen = []
        actual = evaluate(doc, model(doc, variant, seen), PEOPLE, SCENES, True)
        expected = [True] * 2 if variant in ('baseline', 'two_names_one_content') else (
            [True, False] if variant == 'wrong_focal_content' else [False] * 2)
        assert actual == expected, (variant, actual)
        assert all(row[1] == 'reference' for row in seen if row[0] in ('scope', 'supply'))
        assert all(row[2] == 'reference' for row in seen if row[0] == 'compare')
        rows[variant] = actual
    # The quoted family remains the exact previously tested public-use content.
    assert catalog().entries['r2sl'] == parent().entries['r2sl']
    return dict(contrasts=rows, same_closed_public_use_family=True, fixed_reference=True,
                same_public_passed_to_both_comparison_sides=True,
                permission_execution_and_attainment_unknown_without_execution=True,
                semantic_boundaries=[], primitive_provider_supplied_native_quotes=True)


@lru_cache(None)
def scope_checks():
    doc = fixture()
    rows = {}
    for variant in ('baseline', 'empty_publics', 'second_public_fails'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [True, True, variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for missing in ('h232b', 'zpick', 'h232d', 'h222e'):
        values = model(doc)
        values[missing] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error), error
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, same_nonempty_public_scope=True, unknown_inputs_refused=4)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    start = unit['text'].index('die unschädlichste')
    return dict(status='freedom_content_minimum_harm_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[start, 214], text=unit['text'][start:214]),
                interpretation=LIMITS, definitions=list(MEANINGS),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                authored_statements_added=0,
                references=['https://korpora.org/Kant/aa08/036.html'],
                unresolved=['同じ啓蒙への照応', '自由以外の要件を求めない限定',
                            'aber/und zwar/nämlichの提示', '第一文全体の帰属と通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements']
    assert len(new.document['statements']) == 63
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), added_definitions=len(MEANINGS),
                added_basic_relations=len(PRIMITIVES), preserved_statements=63, added_statements=0,
                old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('minimum', minimum_checks), ('binding', binding_checks),
                     ('scope', scope_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, 'scripts/compose_freedom_comparison.py',
        'scripts/check_freedom_comparison.py', 'tests/test_freedom_comparison.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='freedom_content_minimum_harm_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_minimum_harm_of_public_use_freedom'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
