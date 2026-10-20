"""Check complete domains, same-case supply, terminal point and nonfactivity."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_prejudice_claim import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, PROVIDERS, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic
from scripts import check_prejudice_effects as previous

INDEX = 'data/semantic-review-index-v132.json'
AUDIT = 'data/prejudice-claim-reading-v1.json'
REPORT = 'reports/prejudice-claim-v1.json'
DOC = 'docs/prejudice-claim-v1.md'
INVENTORY, PRIOR = previous.INVENTORY, previous.REPORT
PEOPLE = (*previous.PEOPLE, 'case', 'othercase')
EXTRA = previous.EXTRA + 'r zcase[] a.r zroles[] j[a].r zreference[] d.'
DESCRIPTIONS = '''
d h224y[opinion a] i[h[a] e][r[p zclaim]].
d h225h[case a] i[a][r[k zname]].
d h225j[case a] i[d][r[k zearly]].
d h225m[case a target a] i[h[d] c][r[p zhistory]].
d h225n[case a target a] i[h[d d] c][r[p zbefore]].
'''.replace('k zname]', 'k zname[]]').replace('k zearly]', 'k zearly[]]')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(root, boundaries=()):
    doc = deepcopy(catalog().document)
    extras = parse('p:' + EXTRA)['declarations']
    replacements = {d['name']: d for d in parse('p:' + EXTRA + DESCRIPTIONS)['declarations'][len(extras):]}
    for index, declaration in enumerate(doc['declarations']):
        if declaration['name'] in boundaries:
            declaration.update(kind='primitive', parameters=[p['sort'] for p in declaration['parameters']])
            declaration.pop('body')
        if declaration['name'] in replacements:
            doc['declarations'][index] = replacements[declaration['name']]
    doc['declarations'] = extras + doc['declarations']
    roots = ['r2om', 'r2on'] if root == 'families' else [root]
    doc.update(declarations=closure(doc, [*roots, *[d['name'] for d in extras]]), statements=[])
    question = {
        'r2oh': 'q[k r2oh[p zhistory p zbefore k zlate[]]].',
        'r2oi': 'q[k r2oi[k zcase[] k ztarget[]]].',
        'r2ok': 'q[t[k r2ok[]][k zreference[]]].',
        'families': 'q[t[k r2om[k zroles[]]][k zreference[]]].q[t[k r2on[k zroles[]]][k zreference[]]].',
        'r2op': 'q[k r2op[]].',
    }[root]
    return parse(format_graph(doc, 'compact') + question)


def model(doc, variant='baseline'):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(previous.model(variant))
    values.update(arithmetic())
    values.update(zcase=lambda: 'case', zreference=lambda: 'later',
                  h225b=lambda reference, case: reference == 'later' and case == 'case',
                  h225c=lambda case: seq(('target',)),
                  hzwn=lambda person, role, point:
                      (person, role, point) in {('planter', 'other', 'earlier'), ('target', 'other', 'later')},
                  h225a=lambda role, prior, successor, earlier, later:
                      (role, prior, successor, earlier, later) == ('other', 'planter', 'target', 'earlier', 'later'))
    sources = dict(planter='zplanter', act='zact', recipient='zrecipient', opinion='zopinion',
                   earlier='zearly', later='zlate', role='zrole')
    for field, source in sources.items():
        values[PROVIDERS[field][0]] = lambda *args, source=source: values[source]()
    return values


@lru_cache(None)
def terminal_checks():
    doc = fixture('r2oh')
    points = ('earlier', 'later', 'after')
    rows = {}
    for variant in ('baseline', 'unrelated_later_world_point', 'not_terminal', 'missing_endpoint',
                    'reverse_order', 'cycle'):
        values = model(doc)
        members = ('earlier', 'later', 'after') if variant == 'not_terminal' else ('earlier', 'later')
        values.update(zlate=lambda: 'later',
                      zhistory=lambda point: point in members and
                          not (variant == 'missing_endpoint' and point == 'later'),
                      zbefore=lambda first, last:
                          (first != last if variant == 'cycle' else points.index(first) > points.index(last)
                           if variant == 'reverse_order' else points.index(first) < points.index(last)))
        actual = evaluate(doc, values, PEOPLE, points, True)
        assert actual == [variant in ('baseline', 'unrelated_later_world_point')], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_contextual_maximum_not_world_end=True,
                chronology_and_scope_both_required=True)


@lru_cache(None)
def case_checks():
    doc = fixture('r2oi')
    rows = {}
    for variant in ('baseline', 'wrong_closed_opinion', 'other_judge', 'other_generating_act',
                    'no_generation', 'no_harm', 'other_harmed_person', 'no_causal_contribution',
                    'reversed_time', 'wrong_case_opinion', 'wrong_case_earlier', 'wrong_target_role',
                    'wrong_target_later', 'nonterminal_result'):
        values = model(doc, variant)
        scenes = previous.SCENES
        if variant == 'wrong_case_opinion':
            values['h225g'] = lambda case: 'other'
        if variant == 'wrong_case_earlier':
            values['h225i'] = lambda case: 'later'
        if variant == 'wrong_target_role':
            values['h225l'] = lambda case, target: 'topic'
        if variant == 'wrong_target_later':
            values['h225k'] = lambda case, target: 'earlier'
        if variant == 'nonterminal_result':
            scenes = ('earlier', 'later', 'after')
            values.update(zhistory=lambda point: point in scenes,
                          zbefore=lambda first, last: scenes.index(first) < scenes.index(last))
        actual = evaluate(doc, values, PEOPLE, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_case_relations_evaluated_natively=True,
                same_opinion_and_time_names_checked=True)


@lru_cache(None)
def scope_checks():
    doc = fixture('r2ok', ('r2oi',))
    rows = {}
    for variant in ('baseline', 'empty_cases', 'empty_targets', 'duplicate_targets',
                    'nonhuman_target', 'failing_second_target', 'failing_second_case', 'unknown_case'):
        values = model(doc)
        values.update(h225b=lambda ref, case:
                          ref == 'later' and variant != 'empty_cases' and
                          (case == 'case' or variant == 'failing_second_case' and case == 'othercase'),
                      h225c=lambda case: seq(
                          () if variant == 'empty_targets' else
                          ('target', 'target') if variant == 'duplicate_targets' else
                          ('opinion',) if variant == 'nonhuman_target' else
                          ('target', 'planter') if variant == 'failing_second_target' else ('target',)),
                      r2oi=lambda case, target: (case, target) == ('case', 'target'))
        if variant == 'unknown_case':
            values['r2oi'] = unknown
            try:
                evaluate(doc, values, PEOPLE, previous.SCENES, True)
            except ValueError:
                rows[variant] = 'rejected'
                continue
            raise AssertionError('Unknown case was accepted')
        actual = evaluate(doc, values, PEOPLE, previous.SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    # Check the syntactic binding across each quantifier boundary independently.
    casebody = catalog().entries['r2oj']['declaration']['body']
    targetquant = casebody['arguments'][1]['arguments'][1]
    membership, relation = targetquant['body']['arguments']
    assert membership['arguments'][1] == relation['arguments'][1]
    assert membership['arguments'][0]['arguments'][0] == relation['arguments'][0]
    globalbody = catalog().entries['r2ok']['declaration']['body']['body']
    casequant = globalbody['arguments'][1]
    antecedent, consequent = casequant['body']['arguments']
    assert antecedent['arguments'][1] == consequent['arguments'][0]
    return dict(contrasts=rows, all_cases_and_all_targets_required=True,
                relation_boundary_tested_natively_separately=True, quantifier_arguments_match=True)


@lru_cache(None)
def focus_checks():
    doc = fixture('families', ('r2oi',))
    rows = {}
    for variant, roles, expected in [
        ('baseline', ('case', 'opinion', 'target'), [True, True]),
        ('own', ('case', 'opinion', 'planter'), [True, True]),
        ('harm_false', ('case', 'opinion', 'target'), [True, False]),
        ('wrong_opinion', ('case', 'other', 'target'), [False, False]),
        ('wrong_bearer', ('case', 'opinion', 'other'), [False, False]),
        ('wrong_case', ('othercase', 'opinion', 'target'), [False, False]),
        ('missing_role', ('case', 'target'), [False, False]),
        ('extra_role', ('case', 'opinion', 'target', 'other'), [False, False]),
    ]:
        values = model(doc)
        values.update(zroles=lambda: seq(roles), h225c=lambda case: seq(
                          ('planter',) if variant == 'own' else ('target',)) if case == 'case' else seq(()),
                      r2oi=lambda case, target: case == 'case' and
                          target == ('planter' if variant == 'own' else 'target') and variant != 'harm_false')
        actual = evaluate(doc, values, PEOPLE, previous.SCENES, True)
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, scope_does_not_select_by_harm=True,
                emphatic_self_includes_both_originator_and_successor=True)


@lru_cache(None)
def attribution_checks():
    doc = fixture('r2op', ('r2ny',))
    rows = {}
    for variant in ('baseline', 'missing_first_half', 'missing_reason_claim', 'wrong_reason_node',
                    'missing_focus', 'wrong_focus_family'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        def claim_ok(claim):
            return claim.rank == 3 and json.loads(claim.syntax) == dict(kind='call', symbol='r2ok', arguments=[])
        values.update(r2ny=lambda: variant != 'missing_first_half',
                      h225o=lambda: 'reason', h225p=lambda: 'self', wa=lambda: 'author', hzp3=lambda: 'context',
                      hznreport=lambda node, author, claim, scope, context:
                          (node, author, scope, context) ==
                          ('self' if variant == 'wrong_reason_node' else 'reason', 'author', 'reason', 'context')
                          and claim_ok(claim) and variant != 'missing_reason_claim',
                      h224s=lambda node, author, claim, scope, feature, context:
                          (node, author, context) == ('self', 'author', 'context') and claim_ok(claim) and
                          scope.rank == feature.rank == 3 and
                          (symbol(scope), symbol(feature)) ==
                          (('r2on', 'r2om') if variant == 'wrong_focus_family' else ('r2om', 'r2on')) and
                          variant != 'missing_focus')
        actual = evaluate(doc, values, ('reason', 'self', 'author'), ('context',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, world_inputs_unknown_without_execution=True,
                first_half_preserved_as_previously_tested_boundary=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='prejudice_reason_clause_explicit_reading_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[746, 845], text=unit['text'][746:845], self_range=[771, 783]),
                references=[
                    dict(url='https://korpora.org/Kant/aa08/036.html', role='primary_source_context'),
                    dict(url='https://www.duden.de/rechtschreibung/zuletzt',
                         role='modern_auxiliary_terminal_reading_not_last_occurrence')],
                interpretation=LIMITS, selection=selection_binding(catalog(), [59]),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_two_sentence_characters=382,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:59] == old.document['statements'][:59]
    assert len(new.document['statements']) == len(old.document['statements']) == 60
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in previous.previous.previous.previous.previous.reversal.SENTENCES:
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES),
                preserved_statements=59, integrated_statement_index=59, preserved_reviews=len(reviews),
                preserved_sentence_characters=382, inherited_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('terminal', terminal_checks), ('cases', case_checks), ('scope', scope_checks),
                     ('focus', focus_checks), ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR,
        *[p for p, _ in previous.previous.previous.previous.previous.reversal.SENTENCES],
        'scripts/compose_prejudice_claim.py', 'scripts/check_prejudice_claim.py', 'tests/test_prejudice_claim.py',
        'scripts/compose_prejudice_effects.py', 'scripts/check_prejudice_effects.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='prejudice_claim_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_all_cases_terminal_return_and_emphatic_self'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
