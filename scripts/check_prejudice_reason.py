"""Verify harm/degree separation, same scopes, reason direction and quotation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_prejudice_reason import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_public_reversal import SENTENCES
from scripts import check_prejudice_claim as previous

INDEX = 'data/semantic-review-index-v133.json'
AUDIT = 'data/prejudice-reason-reading-v1.json'
REPORT = 'reports/prejudice-reason-v1.json'
DOC = 'docs/prejudice-reason-v1.md'
INVENTORY, PRIOR = previous.INVENTORY, previous.REPORT


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(root, boundaries=()):
    doc = deepcopy(catalog().document)
    extras = parse('p:' + previous.EXTRA)['declarations']
    replacements = {d['name']: d for d in parse('p:' + previous.EXTRA + previous.DESCRIPTIONS)[
        'declarations'][len(extras):]}
    for index, declaration in enumerate(doc['declarations']):
        if declaration['name'] in boundaries:
            declaration.update(kind='primitive', parameters=[p['sort'] for p in declaration['parameters']])
            declaration.pop('body')
        if declaration['name'] in replacements:
            doc['declarations'][index] = replacements[declaration['name']]
    doc['declarations'] = extras + doc['declarations']
    doc.update(declarations=closure(doc, [root, *[d['name'] for d in extras]]), statements=[])
    question = {
        'r2oq': 'q[k r2oq[k zcase[] k ztarget[]]].',
        'r2os': 'q[t[k r2os[k zroles[]]][k zreference[]]].',
        'r2ot': 'q[t[k r2ot[]][k zreference[]]].',
        'r2ox': 'q[k r2ox[]].',
    }[root]
    return parse(format_graph(doc, 'compact') + question)


@lru_cache(None)
def harm_checks():
    # Project the existing supplied r2og call onto its r2oe arguments.
    oldcall = parent().entries['r2oi']['declaration']['body']['arguments'][0]
    expected = dict(kind='call', symbol='r2oe', arguments=oldcall['arguments'][:9] + oldcall['arguments'][10:])
    assert catalog().entries['r2oq']['declaration']['body'] == expected
    doc = fixture('r2oq')
    rows = {}
    for variant in ('baseline', 'no_harm', 'no_generation', 'no_causal_contribution',
                    'other_harmed_person', 'wrong_closed_opinion', 'reversed_time',
                    'not_predecessor', 'not_terminal'):
        values = previous.model(doc, variant)
        scenes = previous.previous.SCENES
        if variant == 'not_predecessor':
            values.update(hzwn=lambda *args: False, h225a=lambda *args: False)
        if variant == 'not_terminal':
            scenes = ('earlier', 'later', 'after')
            values.update(zhistory=lambda point: point in scenes,
                          zbefore=lambda first, last: scenes.index(first) < scenes.index(last))
        actual = evaluate(doc, values, previous.PEOPLE, scenes, True)
        assert actual == [variant in ('baseline', 'not_predecessor', 'not_terminal')], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, exact_existing_causal_chain_projection=True,
                harm_does_not_require_reason_only_authorship_or_terminal_conditions=True)


@lru_cache(None)
def degree_checks():
    doc = fixture('r2ot', ('r2oq',))
    rows = {}
    for harm, high in product((False, True), repeat=2):
        values = previous.model(doc)
        values.update(r2oq=lambda case, target: harm and (case, target) == ('case', 'target'),
                      h225q=lambda prop, roles, ref:
                          high and prop.rank == 3 and symbol(prop) == 'r2os' and
                          roles.items == ('case',) and ref == 'later')
        actual = evaluate(doc, values, previous.PEOPLE, previous.previous.SCENES, True)
        assert actual == [harm and high], (harm, high, actual)
        rows[f'harm={harm},high={high}'] = actual
    for variant in ('empty_cases', 'empty_targets', 'second_target_fails', 'second_case_fails',
                    'wrong_degree_property', 'wrong_degree_case', 'unknown_degree'):
        values = previous.model(doc)
        values.update(h225b=lambda ref, case: ref == 'later' and variant != 'empty_cases' and
                          (case == 'case' or variant == 'second_case_fails' and case == 'othercase'),
                      h225c=lambda case: seq(() if variant == 'empty_targets' else
                          ('target', 'planter') if variant == 'second_target_fails' else ('target',)),
                      r2oq=lambda case, target: (case, target) == ('case', 'target'),
                      h225q=lambda prop, roles, ref: prop.rank == 3 and
                          symbol(prop) == ('r2on' if variant == 'wrong_degree_property' else 'r2os') and
                          roles.items == (('othercase',) if variant == 'wrong_degree_case' else ('case',))
                          and ref == 'later')
        if variant == 'unknown_degree':
            values['h225q'] = unknown
            try:
                evaluate(doc, values, previous.PEOPLE, previous.previous.SCENES, True)
            except ValueError:
                rows[variant] = 'rejected'
                continue
            raise AssertionError('Unknown degree was accepted')
        actual = evaluate(doc, values, previous.PEOPLE, previous.previous.SCENES, True)
        assert actual == [False], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, degree_never_replaces_actual_harm=True,
                same_case_property_and_context_for_degree=True, fixed_complete_domains_preserved=True)


@lru_cache(None)
def family_checks():
    doc = fixture('r2os', ('r2oq',))
    rows = {}
    for variant, roles in [('baseline', ('case',)), ('other', ('othercase',)),
                           ('empty', ()), ('extra', ('case', 'target'))]:
        values = previous.model(doc)
        values.update(zroles=lambda: seq(roles),
                      r2oq=lambda case, target: (case, target) == ('case', 'target'))
        actual = evaluate(doc, values, previous.PEOPLE, previous.previous.SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    # Both case-level target domains are exactly the prior reason domain.
    old = deepcopy(parent().entries['r2oj']['declaration'])
    new = catalog().entries['r2or']['declaration']
    old['name'] = 'r2or'
    old['body']['arguments'][1]['arguments'][1]['body']['arguments'][1]['symbol'] = 'r2oq'
    assert old == new
    return dict(contrasts=rows, same_target_quantification_as_reason=True,
                degree_applies_to_whole_case_not_each_person=True)


@lru_cache(None)
def discourse_checks():
    doc = fixture('r2ox', ('r2op',))
    people = ('prior', 'assessment', 'reason', 'author')
    rows = {}
    def content(desc, name):
        return desc.rank == 3 and json.loads(desc.syntax) == dict(kind='call', symbol=name, arguments=[])
    for variant in ('baseline', 'missing_previous', 'missing_assessment', 'missing_degree_reference',
                    'wrong_example', 'wrong_property', 'reason_reversed', 'missing_reason',
                    'text_order_reversed', 'same_clause'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(r2op=lambda: variant != 'missing_previous', h224m=lambda: 'prior',
                      h225s=lambda: 'assessment', h225o=lambda: 'assessment' if variant == 'same_clause' else 'reason',
                      wa=lambda: 'author', hzp3=lambda: 'context',
                      hznreport=lambda node, author, claim, scope, context:
                          (node, author, scope, context) == ('assessment', 'author', 'assessment', 'context')
                          and content(claim, 'r2ot') and variant != 'missing_assessment',
                      h225r=lambda node, author, claim, prop, example_node, example, context:
                          (node, author, example_node, context) == ('assessment', 'author', 'prior', 'context')
                          and content(claim, 'r2ot') and prop.rank == 3 and
                          symbol(prop) == ('r2on' if variant == 'wrong_property' else 'r2os') and
                          content(example, 'r2ok' if variant == 'wrong_example' else 'r2nf')
                          and variant != 'missing_degree_reference',
                      ud=lambda author, premises, conclusion, context:
                          (author, conclusion, context) ==
                          ('author', 'reason' if variant == 'reason_reversed' else 'assessment', 'context')
                          and {p for p in people if premises(p)} ==
                          ({'assessment'} if variant == 'reason_reversed' else {'reason'})
                          and variant != 'missing_reason',
                      ue=lambda first, last, context: context == 'context' and
                          (first, last) in ({('assessment', 'prior'), ('reason', 'assessment')}
                              if variant == 'text_order_reversed' else
                              {('prior', 'assessment'), ('assessment', 'reason')}))
        actual = evaluate(doc, values, people, ('context',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, reason_and_text_order_directions_preserved=True,
                conditional_prior_claim_quoted_unchanged=True, all_world_inputs_unknown_without_execution=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='harmfulness_degree_and_reason_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[701, 845], text=unit['text'][701:845], assessment_range=[701, 744]),
                references=[dict(url='https://korpora.org/Kant/aa08/036.html', role='primary_source_context')],
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
    for path, indices in SENTENCES:
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
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES), preserved_statements=59,
                integrated_statement_index=59, preserved_reviews=len(reviews),
                preserved_sentence_characters=382, inherited_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('harm', harm_checks), ('degree', degree_checks), ('family', family_checks),
                     ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in SENTENCES],
        'scripts/compose_prejudice_reason.py', 'scripts/check_prejudice_reason.py', 'tests/test_prejudice_reason.py',
        'scripts/compose_prejudice_claim.py', 'scripts/check_prejudice_claim.py', 'scripts/check_prejudice_effects.py',
        'scripts/check_public_reversal.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='prejudice_reason_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_harmfulness_demonstrative_degree_and_reason'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
