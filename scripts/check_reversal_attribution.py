"""Check complete contextual domains, fixed case supply and nonfactive attribution."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_reversal_attribution import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, PROVIDERS, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic
from scripts import check_public_incitation as previous

INDEX = 'data/semantic-review-index-v128.json'
AUDIT = 'data/reversal-attribution-reading-v1.json'
REPORT = 'reports/reversal-attribution-v1.json'
DOC = 'docs/reversal-attribution-v1.md'
INVENTORY, PRIOR = previous.INVENTORY, previous.REPORT
PEOPLE = (*previous.PEOPLE, 'case', 'othercase')
SCENES = previous.SCENES
EXTRA = previous.EXTRA + 'r zcase[] a.r zreference[] d.'
DESCRIPTION_PROVIDERS = '''
d h224g[case a] i[h[d] c][r[p zhistory]].
d h224h[case a] i[h[d d] c][r[p zbefore]].
d h224i[case a] i[d][r[k zfirst[]]].
d h224j[case a] i[d][r[k zlast[]]].
d h224l[case a] i[a][r[k zname[]]].
'''


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(root):
    doc = deepcopy(catalog().document)
    extras = parse('p:' + EXTRA)
    # Description-valued providers are ordinary Noema definitions, not Python
    # objects purporting to capture a case variable inside quotation.
    providers = parse('p:' + EXTRA + DESCRIPTION_PROVIDERS)['declarations'][len(extras['declarations']):]
    replacements = {d['name']: d for d in providers}
    for index, declaration in enumerate(doc['declarations']):
        name = declaration['name']
        if name in ('bf', 'up') or root == 'r2nf' and name in ('r2ne', 'r2la'):
            declaration.update(kind='primitive', parameters=[p['sort'] for p in declaration['parameters']])
            declaration.pop('body')
        if name in replacements:
            doc['declarations'][index] = replacements[name]
    doc['declarations'] = extras['declarations'] + doc['declarations']
    # Keep question-only symbols as well as the transitive source closure.
    doc.update(declarations=closure(doc, [root, 'zpublic', 'zaffected', 'zreference', 'zcase', 'bf']),
               statements=[])
    bodies = {
        'r2la': 'k r2la[k zpublic[] k zreference[]]',
        'r2nc': 'k r2nc[k zpublic[] k zaffected[] r[p bf] k zreference[]]',
        'r2nd': 'k r2nd[k zpublic[] k zreference[]]',
        'r2ne': 'k r2ne[k zpublic[] k zreference[] k zcase[]]',
        'r2nf': 't[k r2nf[]][k zreference[]]',
        'r2ng': 'k r2ng[]',
    }
    return parse(format_graph(doc, 'compact') + 'q[' + bodies[root] + '].')


def model(doc, variant='baseline'):
    values = previous.model(doc, variant)
    values.update(zcase=lambda: 'case', zreference=lambda: 'last', zaffected=lambda: seq(('p',)),
                  h223v=lambda group, state, context:
                      seq(('p', 'q') if variant == 'omitted_affected_member' else ('p',))
                      if group == 'public' and symbol(state) == 'bf' else seq(()),
                  h222e=lambda group, reference:
                      (group, reference) == ('public', 'last') and variant != 'empty_public_scope',
                  h223w=lambda group, reference, case:
                      (group, reference) == ('public', 'last') and
                      (case == 'case' or variant == 'failing_second_case' and case == 'othercase')
                      and variant != 'empty_case_scope',
                  h6t=lambda group, person, reference:
                      group in ('public', 'other') and person in ('p', 'q') and reference == 'last',
                  ce=lambda group, point: (group, point) == ('other', 'last'),
                  ca=lambda person, act, point: (person, act, point) == ('p', 'inciteact', 'last'),
                  cb=lambda person, act, topic, point:
                      (person, act, topic, point) == ('p', 'inciteact', 'prioract', 'last'),
                  cd=lambda topic, point: (topic, point) == ('prioract', 'last'),
                  cc=lambda act, group, point: (act, point) == ('inciteact', 'last') and
                      group in ('public', 'other'))
    ordinary = {
        'guardians': 'zguardians', 'former': 'zformer', 'agitators': 'zagitators',
        'earlieract': 'zprioract', 'earlier': 'zearlier', 'incitingact': 'zinciteact',
        'incited': 'zincited', 'pressure': 'zpressure', 'participants': 'zparticipants',
        'anchor': 'zanchor',
    }
    for field, source in ordinary.items():
        values[PROVIDERS[field][0]] = lambda case, source=source: values[source]()
    if variant == 'failing_second_case':
        values['h224e'] = lambda case: 'other' if case == 'othercase' else 'pressure'
    if variant == 'different_prior_act':
        values['h224a'] = lambda case: 'other'
    if variant == 'different_prior_point':
        values['h224b'] = lambda case: 'incited'
    if variant == 'case_of_other_public':
        values['h223w'] = lambda public, reference, case: (public, reference, case) == ('other', 'last', 'case')
    if variant == 'roster_mismatch':
        old = values['mp']
        values['mp'] = lambda group: seq(('p',)) if group == 'public' else old(group)
    if variant == 'unclassified_public':
        values['ce'] = lambda *args: False
    return values


@lru_cache(None)
def scope_checks():
    doc = fixture('r2nc')
    rows = {}
    for variant in ('baseline', 'reordered', 'missing_member', 'extra_member', 'duplicates',
                    'empty', 'outside_scope', 'nonhuman_scope', 'wrong_state_scope'):
        chosen = {'baseline': ('p', 'q'), 'reordered': ('q', 'p'), 'missing_member': ('p',),
                  'extra_member': ('p', 'q', 'r'), 'duplicates': ('p', 'p', 'q'),
                  'empty': ()}.get(variant, ('p', 'q'))
        scope = {'outside_scope': ('p', 'other'), 'nonhuman_scope': ('p', 'pressure')}.get(
            variant, ('p', 'q'))
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(arithmetic())
        values.update(zpublic=lambda: 'public', zreference=lambda: 'last', zaffected=lambda: seq(chosen),
                      aa=lambda p: p in ('p', 'q', 'r', 'other'),
                      mp=lambda group: seq(('p', 'q', 'r')) if group == 'public' else seq(()),
                      h223v=lambda group, state, context:
                          seq(scope) if (group, symbol(state), context) == (
                              'public', 'up' if variant == 'wrong_state_scope' else 'bf', 'last') else seq(()))
        actual = evaluate(doc, values, (*PEOPLE, 'r'), SCENES, True)
        assert actual == [variant in ('baseline', 'reordered')], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, complete_contextual_scope_not_arbitrary_success_subset=True,
                list_order_not_semantic_membership=True)


@lru_cache(None)
def supply_checks():
    doc = fixture('r2ne')
    positives = ('baseline', 'overlapping_cohorts', 'no_appeal_without_pressure')
    negatives = ('no_pressure', 'only_one_former_pressured', 'omitted_affected_member',
                 'different_prior_act', 'different_prior_point', 'case_of_other_public', 'wrong_closed_action')
    rows = {}
    for variant in (*positives, *negatives):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant in positives], (variant, actual)
        rows[variant] = actual
    for name in ('h223v', 'h223w', 'h223x', 'h223y', 'h224a', 'h224b', 'h224e', 'h224f', 'h224k'):
        values = model(doc)
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, real_noema_closed_description_providers=True,
                native_incitation_incapacity_and_retention_executed=True, unknown_inputs_refused=9)


@lru_cache(None)
def quantified_checks():
    classification = fixture('r2la')
    classification_domain = ('public', 'other', 'p', 'q', 'inciteact', 'prioract')
    for variant in ('baseline', 'unclassified_public'):
        actual = evaluate(classification, model(classification, variant), classification_domain, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
    doc = fixture('r2nf')
    rows = {}
    for variant in ('baseline', 'empty_public_scope', 'empty_case_scope', 'failing_second_case',
                    'roster_mismatch', 'unclassified_public', 'omitted_affected_member',
                    'failing_second_public'):
        values = model(doc, variant)
        values['r2ne'] = lambda public, reference, case: (
            (public, reference) == ('public', 'last') and case == 'case'
            and variant != 'omitted_affected_member')
        values['r2la'] = lambda public, reference: (
            public in ('public', 'other') and reference == 'last' and variant != 'unclassified_public')
        if variant == 'failing_second_public':
            values['h222e'] = lambda public, reference: public in ('public', 'other') and reference == 'last'
            values['h223w'] = lambda public, reference, case: (
                public in ('public', 'other') and (reference, case) == ('last', 'case'))
            old_members = values['mp']
            values['mp'] = lambda group: seq(('p', 'q')) if group == 'other' else old_members(group)
        actual = evaluate(doc, values, PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_cases_of_all_selected_publics=True,
                public_classification_native_in_separate_small_model=True,
                roster_identity_native=True,
                public_classification_boundary_in_quantification=True,
                case_relation_boundary_checked_natively_in_supply=True,
                nonempty_domains_required=True)


@lru_cache(None)
def attribution_checks():
    doc = fixture('r2ng')
    rows = {}
    for accepted in (False, True):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(h224m=lambda: 'node', wa=lambda: 'author', hzp3=lambda: 'last',
                      hznreport=lambda node, author, content, scope, context:
                          accepted and (node, author, scope, context) == ('node', 'author', 'node', 'last')
                          and content.rank == 3 and json.loads(content.syntax) ==
                          dict(kind='call', symbol='r2nf', arguments=[]))
        actual = evaluate(doc, values, (*PEOPLE, 'node', 'author'), SCENES, True)
        assert actual == [accepted], actual
        rows[str(accepted)] = actual
    return dict(contrasts=rows, closed_rank_three_content=True,
                all_world_relations_unknown_without_execution=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='closed_reversal_relation_content_attributed_partial',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[449, 699], text=unit['text'][449:699]),
                selection=selection_binding(catalog(), [59]),
                interpretation=LIMITS, whole_sentence_semantically_verified=False,
                newly_reviewed_sentence_characters=0, preserved_first_two_sentence_characters=382,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:59] == old.document['statements']
    assert len(new.document['statements']) == 60
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    def walk(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)
    case_implications = [
        node for node in walk(new.entries['r2nf']['declaration']['body'])
        if node.get('kind') == 'implies' and
        node['arguments'][1].get('kind') == 'call' and node['arguments'][1]['symbol'] == 'r2ne'
    ]
    assert len(case_implications) == 1
    antecedent, consequent = case_implications[0]['arguments']
    assert antecedent['symbol'] == 'h223w' and antecedent['arguments'] == consequent['arguments']
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in previous.reversal.SENTENCES:
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
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES), new_attributed_statements=1,
                preserved_statements=59, preserved_reviews=len(reviews),
                same_case_arguments_in_scope_and_relation=True,
                preserved_sentence_characters=382, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('scope', scope_checks), ('supply', supply_checks), ('quantification', quantified_checks),
                     ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in previous.reversal.SENTENCES],
        'scripts/compose_reversal_attribution.py', 'scripts/check_reversal_attribution.py',
        'tests/test_reversal_attribution.py', 'scripts/check_public_incitation.py',
        'scripts/compose_public_incitation.py', 'scripts/check_public_reversal.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='reversal_attribution_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_closed_relation_content_with_contextual_scope'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
