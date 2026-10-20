"""Verify state-only generalization, yoke depiction and nonliteral reference."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_reversal_yoke import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts import check_reversal_attribution as previous

INDEX = 'data/semantic-review-index-v129.json'
AUDIT = 'data/reversal-yoke-reading-v1.json'
REPORT = 'reports/reversal-yoke-v1.json'
DOC = 'docs/reversal-yoke-v1.md'
INVENTORY, PRIOR = previous.INVENTORY, previous.REPORT


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, question, boundaries=()):
    doc = deepcopy(catalog().document)
    extras = parse('p:' + previous.EXTRA + 'r zroles[] j[a].r zperson[] a.r zpoint[] d.')
    providers = parse('p:' + previous.EXTRA + previous.DESCRIPTION_PROVIDERS)['declarations'][
        len(parse('p:' + previous.EXTRA)['declarations']):]
    replacements = {d['name']: d for d in providers}
    for index, declaration in enumerate(doc['declarations']):
        if declaration['name'] in boundaries:
            declaration.update(kind='primitive', parameters=[p['sort'] for p in declaration['parameters']])
            declaration.pop('body')
        if declaration['name'] in replacements:
            doc['declarations'][index] = replacements[declaration['name']]
    doc['declarations'] = extras['declarations'] + doc['declarations']
    doc.update(declarations=closure(doc, [*roots, 'zpublic', 'zcase', 'zreference', 'zroles', 'zperson', 'zpoint']),
               statements=[])
    return parse(format_graph(doc, 'compact') + question)


@lru_cache(None)
def depiction_checks():
    doc = fixture(['r2nh'], 'q[t[k r2nh[k zperson[]]][k zpoint[]]].')
    people, scenes = ('person', 'object', 'part', 'load', 'other'), ('point',)
    rows = {}
    for variant in ('baseline', 'wrong_body', 'no_frame', 'no_attachment', 'no_link', 'self_load', 'foot'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(zperson=lambda: 'person', zpoint=lambda: 'point',
                      hzph=lambda obj, point: obj == 'object' and variant != 'no_frame',
                      hzpg=lambda part, bearer, point:
                          (part, bearer) == ('part', 'other' if variant == 'wrong_body' else 'person')
                          and variant != 'foot',
                      h2e=lambda obj, part, bearer, point:
                          (obj, part, bearer) == ('object', 'part', 'person') and variant != 'no_attachment',
                      hzpi=lambda obj, part, bearer, load, point:
                          (obj, part, bearer, load) == (
                              'object', 'part', 'person', 'object' if variant == 'self_load' else 'load')
                          and variant != 'no_link')
        actual = evaluate(doc, values, people, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_neck_frame_attachment_and_traction_relation=True)


@lru_cache(None)
def generalized_checks():
    # Undo ONLY the new state arguments and verify the entire original temporal
    # and conditional body survives alpha-normalization unchanged.
    old = deepcopy(parent().document)
    old.update(declarations=closure(old, ['r2mr']), statements=[])
    restored = deepcopy(catalog().entries['r2nj']['declaration'])
    restored['name'] = 'r2mr'
    restored['parameters'].pop()

    def restore(node):
        if isinstance(node, list):
            return [restore(x) for x in node]
        if not isinstance(node, dict):
            return node
        result = {k: restore(v) for k, v in node.items()}
        if result.get('kind') == 'call' and result['symbol'] == 'r2ni':
            result.update(symbol='r2mp', arguments=result['arguments'][:-1])
        if result.get('kind') == 'call' and result['symbol'] == 'r2mm':
            result.update(symbol='r2mn', arguments=[*result['arguments'][:-2], result['arguments'][-1]])
        return result
    restored['body'] = restore(restored['body'])
    projected = deepcopy(old)
    projected['declarations'] = [restored if d['name'] == 'r2mr' else d for d in projected['declarations']]
    assert parse(format_graph(projected, 'compact')) == parse(format_graph(old, 'compact'))

    doc = fixture(['r2nk', 'bf', 'r2nh'],
                  'q[k r2nk[k zpublic[] k zreference[] k zcase[] r[p bf]]].'
                  'q[k r2nk[k zpublic[] k zreference[] k zcase[] r[p r2nh]]].',
                  ('bf', 'up', 'r2nh'))
    rows = {}
    for variant in ('baseline', 'physical_state_lost', 'no_physical_prior_cause',
                    'no_physical_pressure', 'no_physical_retention_cause', 'wrong_closed_action'):
        values = previous.model(doc, variant)
        old_g3, old_constraint, old_cause = values['g3'], values['h223n'], values['hzie']
        values['r2nh'] = lambda p: Content(previous.SCENES, tuple(
            held and not (variant == 'physical_state_lost' and p == 'h' and point == 'middle')
            for point, held in zip(previous.SCENES, values['bf'](p).values)))
        # Syntax is parsed for checking, never fabricated as an interpreter value.
        def generated(act, person, state, point):
            if json.loads(state.syntax) == dict(kind='function_ref', symbol='r2nh'):
                return (act, person, point) == ('prioract', 'p', 'earlier') and variant != 'no_physical_prior_cause'
            return old_g3(act, person, state, point)
        def constraint(act, person, state, point):
            if symbol(state) == 'r2nh':
                return (act, point) == ('pressure', 'first') and person in ('g', 'h') and variant != 'no_physical_pressure'
            return old_constraint(act, person, state, point)
        def cause(act, factor, person, effect, point):
            expression = json.loads(effect.syntax)
            if expression['arguments'][-1]['symbol'] == 'r2nh':
                assert expression['function'] == dict(kind='function_ref', symbol='r2mk')
                assert [arg['symbol'] for arg in expression['arguments']] == [
                    'zhistory', 'zbefore', 'zfirst', 'zlast', 'r2nh']
                assert json.loads(factor.syntax) == dict(kind='apply',
                    function=dict(kind='function_ref', symbol='r2mj'),
                    arguments=[dict(kind='call', symbol='zfirst', arguments=[])])
                return (act, point) == ('pressure', 'last') and person in ('g', 'h') and variant != 'no_physical_retention_cause'
            return old_cause(act, factor, person, effect, point)
        values.update(g3=generated, h223n=constraint, hzie=cause)
        actual = evaluate(doc, values, previous.PEOPLE, previous.SCENES, True)
        expected = [False, False] if variant == 'wrong_closed_action' else [True, variant == 'baseline']
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, original_temporal_and_conditional_body_exactly_preserved=True,
                only_state_replaced_in_same_case=True, bf_up_and_yoke_state_explicit_boundaries=True)


@lru_cache(None)
def family_checks():
    doc = fixture(['r2nl', 'r2nm', 'r2nn'],
                  ''.join('q[t[k ' + name + '[k zroles[]]][k zreference[]]].'
                          for name in ('r2nl', 'r2nm', 'r2nn')), ('r2ne', 'r2nk'))
    rows = {}
    for variant, roles in [('baseline', ('public', 'case')), ('reversed', ('case', 'public')),
                           ('one_role', ('public',)), ('extra_role', ('public', 'case', 'other')),
                           ('other_case', ('public', 'other'))]:
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(zroles=lambda: seq(roles), zreference=lambda: 'reference',
                      h222e=lambda p, ref: (p, ref) == ('public', 'reference'),
                      h223w=lambda p, ref, case: (p, ref, case) == ('public', 'reference', 'case'),
                      r2ne=lambda p, ref, case: (p, ref, case) == ('public', 'reference', 'case'),
                      r2nk=lambda p, ref, case, state:
                          (p, ref, case, symbol(state)) == ('public', 'reference', 'case', 'r2nh'))
        actual = evaluate(doc, values, ('public', 'case', 'other'), ('reference',), True)
        assert actual == [variant == 'baseline'] * 3, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, same_public_case_and_reference_in_all_families=True,
                case_relations_tested_separately_as_explicit_boundaries=True)


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2nq'], 'q[k r2nq[]].')
    people = ('node', 'yoke', 'remain', 'prior', 'author')
    rows = {}
    for variant in ('baseline', 'missing_depiction', 'wrong_antecedent', 'wrong_state',
                    'reversed_order', 'missing_claim'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(h224m=lambda: 'node', h224o=lambda: 'yoke', h224q=lambda: 'remain',
                      hzpo=lambda: 'prior', wa=lambda: 'author', hzp3=lambda: 'context',
                      hznreport=lambda node, author, claim, scope, context:
                          (node, author, scope, context) == ('node', 'author', 'node', 'context')
                          and claim.rank == 3 and json.loads(claim.syntax) ==
                          dict(kind='call', symbol='r2nf', arguments=[]) and variant != 'missing_claim',
                      h224n=lambda node, author, claim, scope, target, depiction, context:
                          (node, author, context) == ('node', 'author', 'context') and
                          all(x.rank == 3 for x in (claim, scope, target, depiction)) and
                          json.loads(claim.syntax) == dict(kind='call', symbol='r2nf', arguments=[]) and
                          [symbol(x) for x in (scope, target, depiction)] == ['r2nm', 'r2nl', 'r2nn'] and
                          variant != 'missing_depiction',
                      h224p=lambda node, prior, author, state, depiction, context:
                          (node, prior) in ({('yoke', 'remain'), ('remain', 'yoke')}
                                           if variant == 'wrong_antecedent' else {('yoke', 'prior'), ('remain', 'yoke')})
                          and (author, symbol(state), symbol(depiction), context) ==
                          ('author', 'up' if variant == 'wrong_state' else 'bf', 'r2nh', 'context'),
                      ue=lambda first, last, context:
                          (first, last) in ({('yoke', 'prior'), ('remain', 'yoke')}
                                           if variant == 'reversed_order' else {('prior', 'yoke'), ('yoke', 'remain')})
                          and context == 'context')
        actual = evaluate(doc, values, people, ('context',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_world_inputs_unknown_without_execution=True,
                same_state_kinds_not_one_physical_object=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='reversal_yoke_and_kind_anaphora_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[513, 593], text=unit['text'][513:593]),
                selection=selection_binding(catalog(), [59]), interpretation=LIMITS,
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_two_sentence_characters=382,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:59] == old.document['statements'][:59]
    assert len(new.document['statements']) == len(old.document['statements']) == 60
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    # The preceding release descriptions use precisely these two prior states.
    def symbols(node):
        if isinstance(node, dict):
            return ({node['symbol']} if 'symbol' in node else set()) | set().union(
                *(symbols(v) for v in node.values()))
        if isinstance(node, list):
            return set().union(*(symbols(v) for v in node))
        return set()
    assert 'bf' in symbols(new.entries['h4p']['declaration'])
    assert 'hzpk' in symbols(new.entries['hzpm']['declaration'])
    assert 'hzpk' in symbols(new.entries['r2nh']['declaration'])
    assert symbols(new.entries['r2nq']['declaration']) == {'r2ng', 'r2no', 'r2np'}
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in previous.previous.reversal.SENTENCES:
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
                preserved_sentence_characters=382, prior_yoke_state_dependencies_checked=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('depiction', depiction_checks), ('generalization', generalized_checks),
                     ('families', family_checks), ('attribution', attribution_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in previous.previous.reversal.SENTENCES],
        'scripts/compose_reversal_yoke.py', 'scripts/check_reversal_yoke.py', 'tests/test_reversal_yoke.py',
        'scripts/compose_public_reversal.py', 'scripts/compose_reversal_attribution.py',
        'scripts/check_reversal_attribution.py', 'scripts/check_public_incitation.py',
        'scripts/check_public_reversal.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='reversal_yoke_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_same_case_yoke_depiction_and_kind_anaphora'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
