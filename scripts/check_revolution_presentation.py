"""Check extracted modalities and the complete fifth-sentence presentation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_revolution_presentation import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_public_comparison_claim import seq
from scripts.check_public_third_sentence import normalized, quoted
from scripts.check_public_revolution import contains_symbol
from scripts import check_political_withdrawal as withdrawal

INDEX = 'data/semantic-review-index-v143.json'
REPORT = 'reports/revolution-presentation-v1.json'
AUDIT = 'data/revolution-presentation-reading-v1.json'
DOC = 'docs/revolution-presentation-v1.md'
INVENTORY = withdrawal.INVENTORY
PRIOR = ['reports/' + n + '-v1.json' for n in
         ('public-revolution', 'prejudice-forecast', 'leading-band')]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, declarations, questions, boundaries=(), providers=False):
    doc = deepcopy(catalog().document)
    extra = parse('p:' + declarations)['declarations'] if declarations.strip() else []
    replacements = {}
    if providers:
        replacements = {d['name']: d for d in parse('p:' + declarations + '''
            d h227b[public a] i[a][r[k zname[]]].
            d h227c[reference d] i[d][r[k zrname[]]].
        ''')['declarations'][len(extra):]}
    for index, d in enumerate(doc['declarations']):
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
        if d['name'] in replacements:
            doc['declarations'][index] = replacements[d['name']]
    doc['declarations'] = extra + doc['declarations']
    doc.update(declarations=closure(doc, roots + [d['name'] for d in extra]), statements=[])
    return parse(format_graph(doc, 'compact') + questions)


def base(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


@lru_cache(None)
def modality_checks():
    doc = fixture(['r2qy', 'r2rz', 'r2sa', 'r2sd'],
                  'r zg[] a.r zr[] d.r zname[] a.r zrname[] d.r zcase[] d.',
                  ''.join('q[k ' + n + '[k zg[] k zr[]]].' for n in ('r2qy', 'r2rz', 'r2sa')) +
                  'q[t[k r2sd[k zg[] k zr[]]][k zcase[]]].',
                  ('r2qx', 'r2qr', 'hzne'), True)
    people, scenes = ('public', 'event', 'other'), ('reference', 'candidate', 'alternative')
    def model(variant):
        v = base(doc)
        v.update(zg=lambda: 'public', zr=lambda: 'reference', zcase=lambda: 'candidate',
                 zname=lambda: 'other' if variant == 'wrong_public_name' else 'public',
                 zrname=lambda: 'alternative' if variant == 'wrong_reference_name' else 'reference',
                 h222g=lambda public, reference: 'public',
                 h222h=lambda public, reference, candidate: 'reference',
                 h222k=lambda public, reference, candidate:
                     candidate in ('candidate', 'alternative') and variant != 'empty',
                 hzne=lambda frame, origin, candidate:
                     not (variant == 'invalid_unused_frame' and candidate == 'alternative'),
                 r2qx=lambda public, reference, act, candidate:
                     (public, reference) == ('public', 'reference') and variant not in ('empty', 'no_revolution')
                     and (act, candidate) in (('event', 'candidate'), ('other', 'alternative')))
        def result(public, reference, act, candidate, desc):
            if (public, reference) != ('public', 'reference'):
                return False
            if contains_symbol(desc, 'r2qv'):
                return (act, candidate) == ('event', 'candidate') and variant != 'no_withdrawal'
            assert contains_symbol(desc, 'r2qw')
            return variant == 'other_revolution_reforms' and (act, candidate) == ('other', 'alternative')
        v['r2qr'] = result
        return v
    rows = {}
    for variant in ('baseline', 'no_withdrawal', 'other_revolution_reforms', 'empty', 'no_revolution',
                    'wrong_public_name', 'wrong_reference_name', 'invalid_unused_frame'):
        actual = evaluate(doc, model(variant), people, scenes, True)
        bad_context = variant in ('wrong_public_name', 'wrong_reference_name', 'invalid_unused_frame')
        possibility = not bad_context and variant not in ('empty', 'no_revolution', 'no_withdrawal')
        negative = not bad_context and variant != 'other_revolution_reforms'
        candidate_result = variant not in ('empty', 'no_revolution', 'no_withdrawal')
        assert actual == [possibility and negative, possibility, negative, candidate_result], (variant, actual)
        rows[variant] = actual
    for missing in ('r2qx', 'r2qr', 'h222k'):
        v = model('baseline'); v[missing] = unknown
        try:
            evaluate(doc, v, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, extracted_conjunction_matches_original=True,
                other_revolution_not_filtered_by_withdrawal=True,
                unqualified_candidate_result_distinct_from_qualified_possibility=True,
                boundaries=['r2qx', 'r2qr', 'hzne'], unknown_inputs_refused=3)


@lru_cache(None)
def scope_checks():
    doc = fixture(['r2qz', 'r2sb', 'r2sc'], 'r zr[] d.',
                  ''.join('q[t[k ' + n + '[]][k zr[]]].' for n in ('r2qz', 'r2sb', 'r2sc')),
                  ('r2qy', 'r2rz', 'r2sa', 'r2la', 'r2nd'))
    rows = {}
    for variant in ('baseline', 'second_no_possibility', 'second_reforms', 'empty', 'bad_public', 'bad_members'):
        v = base(doc)
        positive = lambda public, reference: not (variant == 'second_no_possibility' and public == 'second')
        negative = lambda public, reference: not (variant == 'second_reforms' and public == 'second')
        v.update(zr=lambda: 'reference', h222e=lambda public, reference: variant != 'empty',
                 r2la=lambda public, reference: variant != 'bad_public',
                 r2nd=lambda public, reference: variant != 'bad_members',
                 r2rz=positive, r2sa=negative,
                 r2qy=lambda public, reference: positive(public, reference) and negative(public, reference))
        actual = evaluate(doc, v, ('first', 'second'), ('reference',), True)
        valid = variant not in ('empty', 'bad_public', 'bad_members')
        expected = [variant == 'baseline', valid and variant != 'second_no_possibility',
                    valid and variant != 'second_reforms']
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, same_nonempty_public_scope_and_all_members=True,
                boundaries=['r2qy', 'r2rz', 'r2sa', 'r2la', 'r2nd'])


def expectations():
    q = quoted
    p = lambda n, rank=3: quoted(n, rank, 'function_ref')
    a, c = 'wa', 'hzp3'
    return [
        ('hznreport', ('h227h', a, q('r2qz'), 'h227h', c)),
        ('hznreport', ('h227n', a, q('r2rn'), 'h227n', c)),
        ('h223l', ('h227o', a, p('h222e', 1), p('h223i', 1), c)),
        ('h224n', ('h227n', a, q('r2rn'), p('r2ru'), p('r2rv'), p('r2rw'), c)),
        ('h227t', ('h227x', a, q('r2qz'), p('h222e'), p('r2sd'), p('r2rz'), c)),
        ('h222q', ('h227h', a, 'h227x', q('r2sb', 1), 'h227y', q('r2sc', 1), p('r2se', 0), c)),
        ('h227u', ('h227h', a, 'h227x', q('r2sb', 1), 'h227y', q('r2sc', 1), p('r2se', 0), c)),
        ('h227v', ('h227w', a, 'h227y', q('r2sc', 1), 'h227n', q('r2rn', 1), p('r2se', 0), c)),
        *[('ue', (first, last, c)) for first, last in
          [('h226h', 'h227h'), ('h227h', 'h227n'), ('h227x', 'h227y'), ('h227y', 'h227n')]],
    ]


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2si'], '', 'q[k r2si[]].')
    constants = ('wa', 'h226h', 'h227h', 'h227n', 'h227o', 'h227w', 'h227x', 'h227y')
    people, scenes = (*constants, 'other'), ('hzp3', 'other')
    expected = expectations()
    def model(omitted=None, wrong=None):
        values = base(doc)
        values.update({n: (lambda n=n: 'other' if n == wrong else n) for n in (*constants, 'hzp3')})
        seen = set()
        def checker(name):
            def check(*args):
                row = (name, tuple(normalized(a) for a in args))
                if row not in expected:
                    return False
                position = expected.index(row)
                seen.add(position)
                return position != omitted
            return check
        values.update({n: checker(n) for n, _ in expected})
        return values, seen
    values, seen = model()
    assert evaluate(doc, values, people, scenes, True) == [True]
    assert seen == set(range(len(expected)))
    for index in range(len(expected)):
        values, _ = model(omitted=index)
        assert evaluate(doc, values, people, scenes, True) == [False], expected[index]
    for name in (*constants, 'hzp3'):
        values, _ = model(wrong=name)
        assert evaluate(doc, values, people, scenes, True) == [False], name
    for name in sorted({n for n, _ in expected}):
        values, _ = model(); values[name] = unknown
        try:
            evaluate(doc, values, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(native_integrated_root='r2si', replaced_definitions=[],
                required_relations=len(expected), omitted_relations_refused=len(expected),
                wrong_source_references_refused=len(constants) + 1,
                unknown_attribution_relations_refused=len({n for n, _ in expected}),
                world_inputs_unknown_and_unexecuted=True,
                uncertainty_denial_and_replacement_have_distinct_scopes=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='revolution_presentation_integrated', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[907, 1216], text=unit['text'][907:1216]),
                interpretation=LIMITS, selection=selection_binding(catalog(), [61, 62]),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_four_sentence_characters=771,
                references=['https://korpora.org/Kant/aa08/036.html',
                            'https://www.duden.de/rechtschreibung/vielleicht_eventuell_circa',
                            'https://www.duden.de/rechtschreibung/wohl_gut_besser_durchaus',
                            'https://www.duden.de/rechtschreibung/sondern_jedoch_hingegen'],
                unresolved=['第五文と段落全体の通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:-1] == old.document['statements'][:-1]
    assert len(new.document['statements']) == len(old.document['statements']) == 63
    assert new.document['statements'][-1]['body']['symbol'] == 'r2si'
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in withdrawal.REVIEWS:
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
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
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_sentence_characters=771,
                added_definitions=len(MEANINGS), added_basic_relations=len(PRIMITIVES),
                preserved_statements=62, integrated_statement_index=62,
                old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('modality', modality_checks), ('scope', scope_checks),
                     ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, *[p for p, _ in withdrawal.REVIEWS],
        'scripts/compose_revolution_presentation.py', 'scripts/check_revolution_presentation.py',
        'scripts/compose_public_first_sentence.py', 'tests/test_revolution_presentation.py',
        'scripts/check_political_withdrawal.py', 'scripts/check_public_revolution.py',
        'scripts/check_public_third_sentence.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_public_comparison_claim.py'}
    return dict(status='revolution_presentation_integrated', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_revolution_presentation_integrated_not_reviewed'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
