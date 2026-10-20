"""Check population selection and the fixed first-sentence core claim."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue, FunctionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_comparison_claim import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS,
    PRIMITIVES, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

INDEX = 'data/semantic-review-index-v118.json'
REPORT = 'reports/public-comparison-claim-v1.json'
AUDIT = 'data/public-comparison-claim-reading-v1.json'
DOC = 'docs/public-comparison-claim-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/prospective-comparison-v1.json', 'reports/prospective-liberty-v1.json',
         'reports/collective-change-v1.json', 'reports/public-use-link-v1.json']


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, extra, boundaries=()):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


def seq(items):
    return SequenceValue(tuple(items), '"individual"')


def predicate(members):
    return FunctionValue(('individual',), 'truth', lambda p: p in members)


@lru_cache(None)
def public_checks():
    doc = fixture(['r2la'], 'r zg[] a.r zr[] d.q[k r2la[k zg[] k zr[]]].')
    domain = ('p', 'q', 'outside', 'group', 'world', 'act', 'role', 'object')

    def model(variant):
        members = set() if variant == 'empty' else {'p'} if variant == 'single' else {'p', 'q'}
        if variant == 'nonhuman':
            members.add('object')
        readers = {'p'} if variant == 'outside_world' else {'p', 'q', 'outside'}
        values = unknowns(doc)
        values.update(
            zg=lambda: 'world' if variant == 'whole_world' else 'group', zr=lambda: 'reference',
            aa=lambda p: p in ('p', 'q', 'outside'),
            h6t=lambda group, p, ref: ref == 'reference' and p in (members if group == 'group' else readers if group == 'world' else set()),
            ce=lambda group, ref: variant != 'no_public_world' and (group, ref) == ('world', 'reference'),
            ca=lambda who, act, ref: variant != 'not_reason_use' and (who, act, ref) == ('p', 'act', 'reference'),
            cb=lambda who, act, role, ref: (who, act, role, ref) == ('p', 'act', 'role', 'other' if variant == 'wrong_reference' else 'reference'),
            cd=lambda role, ref: variant != 'private_role' and (role, ref) == ('role', 'reference'),
            cc=lambda act, audience, ref: (act, ref) == ('act', 'reference') and
                audience in ({'group'} if variant == 'private_address_only' else {'world'} if variant == 'no_local_address' else {'group', 'world'}),
        )
        return values

    rows = {}
    for variant in ('baseline', 'whole_world', 'empty', 'single', 'nonhuman', 'outside_world',
                    'no_public_world', 'not_reason_use', 'private_role', 'private_address_only',
                    'no_local_address', 'wrong_reference'):
        actual = evaluate(doc, model(variant), domain, ('reference', 'other'), True)
        assert actual == [variant in ('baseline', 'whole_world')], (variant, actual)
        rows[variant] = actual
    for name in ('h6t', 'ce', 'cd'):
        values = model('baseline')
        values[name] = unknown
        try:
            evaluate(doc, values, domain, ('reference', 'other'), True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    assert not {'h6e', 'h6g', 'h7a', 'h7b', 'dg'} & {d['name'] for d in doc['declarations']}
    return dict(cases=rows, intended_public_address_not_actual_receipt_or_permission=True,
                proper_subpublic_and_whole_world_allowed=True, unknown_inputs_refused=3)


@lru_cache(None)
def extent_checks():
    doc = fixture(['r2lb'], 'r zp[] j[a].r zt[] b.r zm[a] c.r zc[a] c.r ze[a] c.'
                  'q[k r2lb[k zp[] k zt[] p zm p zc p ze]].')
    domain = ('p', 'q', 'outside')

    def model(population, members, changed, threshold, eligible=domain):
        values = unknowns(doc)
        values.update(arithmetic())
        values.update(pa=lambda n, d: n / d if d else Fraction(0), zp=lambda: seq(population),
                      zt=lambda: Fraction(threshold), zm=lambda p: p in members,
                      zc=lambda p: p in changed, ze=lambda p: p in eligible)
        return values

    cases = 0
    for bits in product((False, True), repeat=6):
        members = {p for p, b in zip(domain, bits[:3]) if b}
        changed = {p for p, b in zip(domain, bits[3:]) if b}
        population = [p for p in domain if p in members]
        for threshold in (Fraction(-1), Fraction(0), Fraction(1, 3), Fraction(1, 2), Fraction(1)):
            actual = evaluate(doc, model(population, members, changed, threshold), domain, ('now',), True)
            wanted = bool(members) and 0 < threshold < 1 and Fraction(len(members & changed), len(members)) > threshold
            assert actual == [wanted], (members, changed, threshold, actual)
            cases += 1
    rows = {}
    for name, population, members, changed, threshold, eligible, wanted in (
        ('threshold_equality', ('p', 'q'), {'p', 'q'}, {'p'}, Fraction(1, 2), domain, False),
        ('one_new_member_can_suffice', ('p', 'q'), {'p', 'q'}, {'p'}, Fraction(1, 3), domain, True),
        ('success_only_sample', ('p',), {'p', 'q'}, {'p'}, Fraction(1, 3), domain, False),
        ('duplicate', ('p', 'p', 'q'), {'p', 'q'}, {'p', 'q'}, Fraction(1, 3), domain, False),
        ('extra_person', domain, {'p', 'q'}, {'p', 'q'}, Fraction(1, 3), domain, False),
        ('outside_success_only', ('p', 'q'), {'p', 'q'}, {'outside'}, Fraction(1, 3), domain, False),
        ('nonhuman_member', ('p', 'q'), {'p', 'q'}, {'p', 'q'}, Fraction(1, 3), {'p'}, False),
    ):
        actual = evaluate(doc, model(population, members, changed, threshold, eligible), domain, ('now',), True)
        assert actual == [wanted], (name, actual)
        rows[name] = actual
    for name in ('zp', 'zt', 'zc'):
        values = model(('p', 'q'), {'p', 'q'}, {'p'}, Fraction(1, 3))
        values[name] = unknown
        try:
            evaluate(doc, values, domain, ('now',), True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(membership_change_threshold_combinations=cases, cases=rows,
                complete_population_and_exact_ratio_executed=True, unknown_inputs_refused=3)


@lru_cache(None)
def binding_checks():
    doc = fixture(['r2ld'], 'r zg[] a.r zp[] a.r zr[] d.q[k r2ld[k zg[] k zp[] k zr[]]].', ('r2kw',))
    domain = ('group', 'p', 'q', 'source', 'frame', 'low', 'mid', 'high')
    scenes = ('reference', 'branch', 'start')
    seen = set()

    def track(name, args, result):
        seen.add((name, *args))
        return result

    values = unknowns(doc)
    values.update(arithmetic())
    values.update(pa=lambda n, d: n / d if d else Fraction(0),
                  zg=lambda: 'group', zp=lambda: 'p', zr=lambda: 'reference',
                  aa=lambda p: p in ('p', 'q'))
    for name, result in [('h222f', 'source'), ('h222g', 'frame'), ('h222i', seq(('p', 'q'))),
                         ('h222j', Fraction(1, 3)), ('h222l', seq(('low', 'mid', 'high'))),
                         ('h222n', 'mid'), ('h222p', 'mid')]:
        values[name] = lambda *args, name=name, result=result: track(name, args, result)
    values.update(
        h222h=lambda g, r, b: track('h222h', (g, r, b), 'start'),
        h222k=lambda g, r, b: track('h222k', (g, r, b), b == 'branch'),
        h222m=lambda g, r, value: track('h222m', (g, r, value), value == 'mid'),
        h222o=lambda g, p, r: track('h222o', (g, p, r), 'low'),
    )

    def modal(reference, audience, person, source, frame, origins, extent, cases,
              scale, less, near, low, high, public, individual, conditioned):
        assert (reference, audience, person, source, frame) == ('reference', 'group', 'p', 'source', 'frame')
        assert origins('branch') == 'start'
        assert [s for s in scenes if cases(s)] == ['branch']
        assert [p for p in domain if scale(p)] == ['low', 'mid', 'high']
        assert less('low', 'mid') and less('mid', 'high') and not less('mid', 'low')
        assert near('mid') and not near('high')
        assert (low, high, public, individual, conditioned) == ('low', 'high', 'mid', 'low', 'mid')
        # Execute the real new source extent, including exact population checks.
        assert extent(predicate({'p', 'q'}), predicate({'p'}))
        assert not extent(predicate({'p'}), predicate({'p'}))
        assert not extent(predicate({'p', 'q'}), predicate({'source'}))
        return True

    values['r2kw'] = modal
    assert evaluate(doc, values, domain, scenes, True) == [True]
    assert all(row[1] == 'group' for row in seen)
    assert all(row[3] == 'reference' if row[0] == 'h222o' else row[2] == 'reference' for row in seen)
    assert ('h222o', 'group', 'p', 'reference') in seen
    invalid = dict(values, h222l=lambda *args: seq(('low', 'mid', 'mid', 'high')), r2kw=lambda *args: True)
    assert evaluate(doc, invalid, domain, scenes, True) == [False]
    return dict(all_fifteen_parameters_bound=True, population_and_threshold_fixed_at_reference=True,
                real_source_extent_executed_through_modal_callback=True,
                duplicate_scale_refused_before_accepting_modal_result=True,
                previous_modal_body_is_explicit_boundary=True)


@lru_cache(None)
def quantifier_checks():
    doc = fixture(['r2le'], 'r zr[] d.q[k r2le[k zr[]]].', ('r2la', 'r2ld'))
    domain = ('g', 'h', 'p', 'q', 'node', 'object')
    pairs = tuple(product(('g', 'h'), ('p', 'q')))

    def model(groups, people, true_pairs):
        values = unknowns(doc)
        values.update(
            zr=lambda: 'now', wh=lambda: 'earlier', hzzq=lambda: 'node',
            h222e=lambda g, r: g in groups and r == 'now',
            hzzn=lambda n, p, r: (n, r) == ('node', 'earlier') and p in people,
            aa=lambda p: p in ('p', 'q'),
            r2la=lambda g, r: g in ('g', 'h') and r == 'now',
            r2ld=lambda g, p, r: (g, p) in true_pairs and r == 'now',
        )
        return values

    cases = 0
    for bits in product((False, True), repeat=8):
        groups = {p for p, b in zip(('g', 'h'), bits[:2]) if b}
        people = {p for p, b in zip(('p', 'q'), bits[2:4]) if b}
        true_pairs = {p for p, b in zip(pairs, bits[4:]) if b}
        wanted = bool(groups and people) and set(product(groups, people)) <= true_pairs
        assert evaluate(doc, model(groups, people, true_pairs), domain, ('now', 'earlier'), True) == [wanted]
        cases += 1
    for name, values in (
        ('nonpublic_selected_group', model({'g', 'object'}, {'p'}, {('g', 'p'), ('object', 'p')})),
        ('nonhuman_comparison_person', model({'g'}, {'p', 'object'}, {('g', 'p'), ('g', 'object')})),
    ):
        assert evaluate(doc, values, domain, ('now', 'earlier'), True) == [False], name
    for name in ('h222e', 'hzzn', 'r2ld'):
        values = model({'g'}, {'p'}, {('g', 'p')})
        values[name] = unknown
        try:
            evaluate(doc, values, domain, ('now', 'earlier'), True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(scope_and_pair_combinations=cases, all_prior_individuals_compared=True,
                selected_ineligible_objects_not_silently_removed=True,
                empty_scopes_refused=True, unknown_inputs_refused=3)


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2lg'], 'q[k r2lg[]].')
    expected = dict(kind='call', symbol='r2lf', arguments=[])

    def report(node, author, content, context):
        assert content.rank == 1
        return (node, author, context) == ('conclusion', 'author', 'text') and json.loads(content.syntax) == expected

    values = unknowns(doc)
    values.update(hzp4=lambda: 'conclusion', wa=lambda: 'author', hzp3=lambda: 'text', h5t=lambda: 'prior',
                  hzon=report, ue=lambda first, last, ctx: (first, last, ctx) == ('prior', 'conclusion', 'text'))
    domain, scenes = ('conclusion', 'author', 'prior', 'other'), ('text', 'other')
    assert evaluate(doc, values, domain, scenes, True) == [True]
    for name in ('hzp4', 'wa', 'hzp3', 'h5t'):
        modified = dict(values)
        modified[name] = lambda: 'other'
        assert evaluate(doc, modified, domain, scenes, True) == [False]
    return dict(source_assertion_closed=True, all_context_inputs_and_world_facts_unexecuted=True,
                attribution_and_textual_order_not_world_truth=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    paths = {FULL, BASIS, DOC, INVENTORY, *PRIOR}
    return dict(status='first_sentence_core_claim_under_contextual_public_reading_partial',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[0, 128], text=unit['text'][:128]),
                selection=selection_binding(catalog(), [55]),
                interpretation=LIMITS,
                unresolved=['aberの対比、jaの強め方、nurが自由を足りる条件として取り立てる作用を接続する。',
                            '自由の規範的な読みを後続段落の限定と照合し、第一文全体を再読して判断する。'],
                references=[dict(url='https://korpora.org/Kant/aa08/036.html', accessed='2026-10-20',
                                 use='公衆と個人の比較、後続する理由と自由の限定。'),
                            dict(url='https://korpora.org/Kant/aa08/037.html', accessed='2026-10-20',
                                 use='公的な理性使用と読者世界全体への宛先、職務内の私的使用との区別。')],
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert new.document['statements'][:-1] == old.document['statements']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']
    for row in reviews['kant-1784']:
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
    return dict(added_definitions=len(MEANINGS), added_context_inputs=len(PRIMITIVES),
                authored_statements=56, added_statement_index=55,
                preserved_whole_unit_reviews=len(reviews['kant-1784']), roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('public', public_checks), ('extent', extent_checks), ('binding', binding_checks),
                     ('quantifiers', quantifier_checks), ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, 'scripts/compose_public_comparison_claim.py',
        'scripts/check_public_comparison_claim.py', 'tests/test_public_comparison_claim.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/check_scoped_counts.py',
    }
    source = read(AUDIT)['source']
    phrase = 'ein Publikum sich selbst aufkläre'
    start = source['text'].index(phrase)
    return dict(status='public_comparison_core_claim_connected_first_sentence_partial', document=FULL, **results,
                alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'],
                               range=[start, start + len(phrase)], text=phrase,
                               definitions=list(MEANINGS), status='explicit_partial_contextual_public_claim'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
