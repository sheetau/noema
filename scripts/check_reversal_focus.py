"""Check focus attachment, unchanged conditional scope and nonfactivity."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_reversal_focus import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic
from scripts import check_reversal_yoke as previous

INDEX = 'data/semantic-review-index-v130.json'
AUDIT = 'data/reversal-focus-reading-v1.json'
REPORT = 'reports/reversal-focus-v1.json'
DOC = 'docs/reversal-focus-v1.md'
INVENTORY, PRIOR = previous.INVENTORY, previous.REPORT


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def nodes(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from nodes(item)


def fixture(roots, question, boundaries=()):
    doc = deepcopy(catalog().document)
    extras = parse('p:' + previous.previous.EXTRA + 'r zroles[] j[a].')
    providers = parse('p:' + previous.previous.EXTRA + previous.previous.DESCRIPTION_PROVIDERS)[
        'declarations'][len(parse('p:' + previous.previous.EXTRA)['declarations']):]
    replacements = {d['name']: d for d in providers}
    for index, declaration in enumerate(doc['declarations']):
        if declaration['name'] in boundaries:
            declaration.update(kind='primitive', parameters=[p['sort'] for p in declaration['parameters']])
            declaration.pop('body')
        if declaration['name'] in replacements:
            doc['declarations'][index] = replacements[declaration['name']]
    doc['declarations'] = extras['declarations'] + doc['declarations']
    doc.update(declarations=closure(doc, [*roots, 'zpublic', 'zcase', 'zreference', 'zroles']),
               statements=[])
    return parse(format_graph(doc, 'compact') + question)


@lru_cache(None)
def attachment_checks():
    # Expand only the three supply wrappers, not the semantic relation bodies.
    # The extraction starts at the old claim's case relation, independently of
    # the builder's handwritten projection.
    def substitute(value, bindings):
        if isinstance(value, dict):
            if value.get('kind') == 'variable' and value['name'] in bindings:
                return deepcopy(bindings[value['name']])
            return {key: substitute(item, bindings) for key, item in value.items()}
        if isinstance(value, list):
            return [substitute(item, bindings) for item in value]
        return value

    def expand(value):
        if isinstance(value, dict):
            if value.get('kind') == 'call' and value['symbol'] in ('r2nb', 'r2mv', 'r2mr'):
                declaration = parent().entries[value['symbol']]['declaration']
                bound = dict(zip((p['name'] for p in declaration['parameters']), value['arguments']))
                return expand(substitute(declaration['body'], bound))
            return {key: expand(item) for key, item in value.items()}
        if isinstance(value, list):
            return [expand(item) for item in value]
        return value

    case = parent().entries['r2ne']['declaration']
    projected = catalog().entries['r2nr']['declaration']
    publicvar, casevar = [dict(kind='variable', name=p['name']) for p in projected['parameters']]
    source = substitute(case['body'], {case['parameters'][0]['name']: publicvar,
                                       case['parameters'][2]['name']: casevar})
    candidates = [n for n in nodes(expand(source)) if n.get('kind') == 'implies' and
                  n['arguments'][0].get('symbol') == 'r2mq']
    assert len(candidates) == 1
    doc = deepcopy(catalog().document)
    for declaration in doc['declarations']:
        if declaration['name'] == 'r2nr':
            declaration['body'] = candidates[0]
    normalized = parse(format_graph(doc, 'compact'))
    assert next(d for d in normalized['declarations'] if d['name'] == 'r2nr') == projected

    # The incapable function and its two arguments occur inside the original
    # antecedent's member quantifier, not as an unconditional extra assertion.
    antecedent = projected['body']['arguments'][0]
    assert antecedent['arguments'][6] == dict(kind='function_ref', symbol='r2mt')
    mq = parent().entries['r2mq']['declaration']
    incapname, pointname = [mq['parameters'][i]['name'] for i in (6, 4)]
    applications = [n for n in nodes(mq['body']) if n.get('kind') == 'apply' and
                    n['function'] == dict(kind='variable', name=incapname)]
    assert len(applications) == 1
    assert applications[0]['arguments'][1] == dict(kind='variable', name=pointname)
    focus = catalog().entries['r2nv']['declaration']
    call = next(n for n in nodes(focus['body']) if n.get('symbol') == 'r2mt')
    member = next(n for n in nodes(focus['body']) if n.get('symbol') == 'hg')
    assert call['arguments'][0] == member['arguments'][1]
    assert call['arguments'][1]['symbol'] == 'h224d'
    assert member['arguments'][0]['symbol'] == 'h223z'
    assert call['arguments'][1]['arguments'] == member['arguments'][0]['arguments']
    return dict(conditional_projection_exact_after_supply_and_alpha_normalization=True,
                incapacity_is_the_same_antecedent_member_property=True)


@lru_cache(None)
def conditional_checks():
    doc = fixture(['r2nr'], 'q[k r2nr[k zpublic[] k zcase[]]].', ('r2mq', 'r2mn'))
    rows = {}
    for incited, retained in product((False, True), repeat=2):
        values = previous.previous.model(doc)
        values.update(zpublic=lambda: 'public', zcase=lambda: 'case',
                      h223y=lambda case: seq(('g', 'h')),
                      r2mq=lambda public, agents, act, pressure, point, role, incapable, incites:
                          incited if (public, act, pressure, point) ==
                          ('public', 'inciteact', 'pressure', 'incited') else False,
                      r2mn=lambda public, pressure, person, actors, history, before, first, last, anchor:
                          (public, pressure, anchor) == ('public', 'pressure', 'last') and
                          (person == 'g' or retained and person == 'h'))
        actual = evaluate(doc, values, previous.previous.PEOPLE, previous.previous.SCENES, True)
        assert actual == [not incited or retained], (incited, retained, actual)
        rows[f'incited={incited},all_retained={retained}'] = actual
    return dict(contrasts=rows, no_unconditional_coercion=True, every_former_actor_required=True,
                antecedent_and_retention_relations_are_separately_tested_boundaries=True)


@lru_cache(None)
def family_checks():
    names = ('r2ns', 'r2nt', 'r2nu', 'r2nv')
    doc = fixture(names, ''.join('q[t[k ' + n + '[k zroles[]]][k zreference[]]].' for n in names),
                  ('r2nr', 'r2mt'))
    cases = [
        ('public', ('public', 'case', 'public'), True, True, [True, True, False, False]),
        ('agitator', ('public', 'case', 'agent'), True, True, [False, False, True, True]),
        ('incapacity_false', ('public', 'case', 'agent'), True, False, [False, False, True, False]),
        ('conditional_false', ('public', 'case', 'public'), False, True, [True, False, False, False]),
        ('wrong_bearer', ('public', 'case', 'other'), True, True, [False] * 4),
        ('wrong_case', ('public', 'other', 'agent'), True, True, [False] * 4),
        ('two_roles', ('public', 'case'), True, True, [False] * 4),
        ('four_roles', ('public', 'case', 'agent', 'other'), True, True, [False] * 4),
    ]
    rows = {}
    for variant, roles, condition, incapable, expected in cases:
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(arithmetic())
        values.update(zroles=lambda: seq(roles), zreference=lambda: 'reference',
                      h222e=lambda public, ref: (public, ref) == ('public', 'reference'),
                      h223w=lambda public, ref, case:
                          (public, ref, case) == ('public', 'reference', 'case'),
                      h223z=lambda case: seq(('agent',)) if case == 'case' else seq(()),
                      h224d=lambda case: 'reference',
                      r2nr=lambda public, case: condition and (public, case) == ('public', 'case'),
                      r2mt=lambda person, point: incapable and (person, point) == ('agent', 'reference'))
        actual = evaluate(doc, values, ('public', 'case', 'agent', 'other'), ('reference',), True)
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, three_ordered_roles_and_same_evaluation_point=True,
                scopes_not_filtered_by_success=True)


@lru_cache(None)
def attribution_checks():
    # The already checked r2nq is a boundary here; its preserved dependency
    # binding and hash-pinned native tests are checked by structure_checks.
    doc = fixture(['r2ny'], 'q[k r2ny[]].', ('r2nq',))
    rows = {}
    for variant in ('baseline', 'no_prior_claim', 'no_peculiarity', 'no_public_focus', 'no_agent_focus',
                    'wrong_discussion', 'swapped_families'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        def claim_ok(claim):
            return claim.rank == 3 and json.loads(claim.syntax) == dict(kind='call', symbol='r2nf', arguments=[])
        def self_focus(node, author, claim, scope, feature, context):
            expected = {'publicself': ('r2ns', 'r2nt'), 'agentself': ('r2nu', 'r2nv')}
            pair = expected[node]
            if variant == 'swapped_families':
                pair = expected['agentself' if node == 'publicself' else 'publicself']
            return (author, context) == ('author', 'context') and claim_ok(claim) and (
                scope.rank == feature.rank == 3 and (symbol(scope), symbol(feature)) == pair
                and not (variant == 'no_public_focus' and node == 'publicself')
                and not (variant == 'no_agent_focus' and node == 'agentself'))
        values.update(r2nq=lambda: variant != 'no_prior_claim',
                      h224t=lambda: 'note', h224u=lambda: 'publicself', h224v=lambda: 'agentself',
                      wa=lambda: 'author', hzp3=lambda: 'context', hzp4=lambda: 'first',
                      hzp5=lambda: 'other' if variant == 'wrong_discussion' else 'second',
                      h224r=lambda node, author, claim, focus, discussion, context:
                          (node, author, context) == ('note', 'author', 'context') and
                          claim_ok(claim) and claim_ok(focus) and
                          discussion.items == ('first', 'second') and
                          variant != 'no_peculiarity',
                      h224s=self_focus)
        actual = evaluate(doc, values, ('note', 'publicself', 'agentself', 'author', 'first', 'second', 'other'),
                          ('context',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_world_inputs_unknown_without_execution=True,
                original_attribution_is_a_preserved_tested_boundary=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='reversal_focus_explicit_reading_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[449, 699], text=unit['text'][449:699],
                            focus_ranges=[[449, 469], [560, 566], [637, 643]]),
                references=[
                    dict(url='https://korpora.org/Kant/aa08/036.html', role='primary_source_context'),
                    dict(url='https://www.duden.de/rechtschreibung/selbst_selber',
                         role='modern_auxiliary_emphatic_self_distinct_from_scalar_even'),
                    dict(url='https://www.duden.de/rechtschreibung/besonders',
                         role='modern_auxiliary_multiple_senses_not_unique_historical_resolution')],
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
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in previous.previous.previous.reversal.SENTENCES:
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
    for name, fn in [('attachment', attachment_checks), ('conditional', conditional_checks),
                     ('families', family_checks), ('attribution', attribution_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR,
        *[p for p, _ in previous.previous.previous.reversal.SENTENCES],
        'scripts/compose_reversal_focus.py', 'scripts/check_reversal_focus.py', 'tests/test_reversal_focus.py',
        'scripts/compose_reversal_yoke.py', 'scripts/check_reversal_yoke.py',
        'scripts/compose_reversal_attribution.py', 'scripts/check_reversal_attribution.py',
        'scripts/check_public_incitation.py', 'scripts/check_public_reversal.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='reversal_focus_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_noteworthy_presentation_and_emphatic_bearers'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
