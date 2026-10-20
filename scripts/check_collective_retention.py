"""Distinguish joint constraint from mere persistence or alleged causation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_collective_retention import (
    ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic

INDEX = 'data/semantic-review-index-v124.json'
AUDIT = 'data/collective-retention-reading-v1.json'
REPORT = 'reports/collective-retention-v1.json'
DOC = 'docs/collective-retention-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/public-reversal-reading-v1/page-484.jpg'
PRIOR = 'reports/public-second-sentence-v1.json'
SENTENCES = [('data/public-first-sentence-reading-v1.json', [55, 56]),
             ('data/public-second-sentence-reading-v1.json', [58])]
PEOPLE = ('group', 'act', 'p', 'q', 'r', 'target', 'other')
SCENES = ('first', 'middle', 'last')
EXTRA = '''
r zg[] a.r za[] a.r zt[] a.r zactors[] j[a].
r zh[d] c.r zb[d d] c.r zfirst[] d.r zlast[] d.r zanchor[] d.
r zstate[a] e.
'''
ARGS = 'k zg[] k za[] k zt[] k zactors[] r[p zh] r[p zb] r[k zfirst[]] r[k zlast[]]'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(source=False):
    doc = deepcopy(catalog().document)
    if source:
        d = next(d for d in doc['declarations'] if d['name'] == 'bf')
        d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
        d.pop('body')
    root = 'r2mn' if source else 'r2mm'
    doc.update(declarations=closure(doc, [root]), statements=[])
    args = ARGS + ('' if source else ' r[p zstate]') + ' k zanchor[]'
    return parse(format_graph(doc, 'compact') + EXTRA + 'q[k ' + root + '[' + args + ']].')


def model(doc, variant='baseline', flags=(True,) * 6, source=False):
    pressure, held, causal, joint, occurred, participation = flags
    actors = ('p', 'q')
    if variant == 'empty_actors':
        actors = ()
    if variant == 'duplicate_actors':
        actors = ('p', 'p')
    if variant == 'outside_actor':
        actors = ('p', 'other')
    if variant == 'nonhuman_actor':
        actors = ('p', 'act')
    state_name = 'bf' if source else 'zstate'

    def content(p):
        return Content(SCENES, tuple(held and p == 'target' and not (
            variant == 'intermediate_loss' and t == 'middle' or
            variant == 'only_late_acquisition' and t == 'first') for t in SCENES))

    def cause(act, factor, target, effect, anchor):
        f, e = json.loads(factor.syntax), json.loads(effect.syntax)
        assert f == dict(kind='apply', function=dict(kind='function_ref', symbol='r2mj'),
                         arguments=[dict(kind='call', symbol='zfirst', arguments=[])])
        assert e['function'] == dict(kind='function_ref', symbol='r2mk')
        assert [a['symbol'] for a in e['arguments']] == ['zh', 'zb', 'zfirst', 'zlast', state_name]
        return causal and (act, target, anchor) == (
            'other' if variant == 'wrong_causal_act' else 'act',
            'other' if variant == 'wrong_causal_target' else 'target', 'last')

    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(arithmetic())
    values.update(
        zg=lambda: 'group', za=lambda: 'act', zt=lambda: 'target', zactors=lambda: seq(actors),
        zh=lambda t: not (variant == 'missing_endpoint' and t == 'last'),
        zb=lambda a, b: SCENES.index(a) < SCENES.index(b) or
            variant == 'cyclic_history' and (a, b) == ('last', 'first'),
        zfirst=lambda: 'last' if variant == 'reversed_interval' else 'first',
        zlast=lambda: 'first' if variant == 'same_endpoint' else 'last',
        zanchor=lambda: 'middle' if variant == 'future_end' else 'last',
        aa=lambda p: p in ('p', 'q', 'r', 'target', 'other'),
        mp=lambda g: seq(('p', 'q', 'r')) if g == 'group' else seq(()),
        dg=lambda act, t: occurred and (act, t) == ('act', 'first'),
        df=lambda p, act, t: participation and (p, act, t) in {('p', 'act', 'first'), ('q', 'act', 'first')},
        h223o=lambda g, act, participants, t: joint and
            (g, act, participants.items, t) == ('group', 'other' if variant == 'wrong_joint_act' else 'act',
                                              actors, 'first'),
        h223n=lambda act, target, state, t: pressure and
            (act, target, symbol(state), t) == ('act', 'other' if variant == 'wrong_constraint_target' else 'target',
                                               'unrelated' if variant == 'wrong_constraint_state' else state_name, 'first'),
        hzie=cause, zstate=content,
    )
    if source:
        values['bf'] = content
    return values


@lru_cache(None)
def causal_checks():
    doc = fixture()
    count = 0
    for flags in product((False, True), repeat=6):
        actual = evaluate(doc, model(doc, flags=flags), PEOPLE, SCENES, True)
        assert actual == [all(flags)], (flags, actual)
        count += 1
    cases = {}
    for variant in ('baseline', 'empty_actors', 'duplicate_actors', 'outside_actor', 'nonhuman_actor',
                    'wrong_joint_act', 'wrong_constraint_target', 'wrong_constraint_state',
                    'wrong_causal_act', 'wrong_causal_target', 'intermediate_loss', 'only_late_acquisition',
                    'missing_endpoint', 'cyclic_history', 'future_end', 'same_endpoint', 'reversed_interval'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        cases[variant] = actual
    # A nonparticipating member r does not defeat a collective action by p and q.
    assert model(doc)['mp']('group').items == ('p', 'q', 'r')
    for name in ('h223n', 'h223o', 'hzie', 'df', 'dg', 'zstate', 'zb'):
        values = model(doc)
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(independent_condition_combinations=count, contrasts=cases,
                full_population_unanimity_not_required=True, same_act_target_state_interval=True,
                unknown_inputs_refused=7, whole_interval_not_endpoints_only=True)


@lru_cache(None)
def source_checks():
    doc = fixture(source=True)
    cases = {}
    for variant in ('baseline', 'wrong_constraint_state', 'intermediate_loss', 'wrong_causal_target'):
        actual = evaluate(doc, model(doc, variant, source=True), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline']
        cases[variant] = actual
    return dict(contrasts=cases, source_specialization_is_existing_bf=True,
                immaturity_content_is_explicit_boundary=True,
                source_pronouns_incitation_and_attribution_not_yet_closed=True)


@lru_cache(None)
def quote_checks():
    doc = fixture()
    declarations = {d['name']: d for d in doc['declarations']}
    # Reporting this content does not execute any constraint or causal facts.
    report = deepcopy(catalog().entries['hznreport']['declaration'])
    assert report['kind'] == 'primitive' and 'hznreport' not in declarations
    doc['declarations'].append(report)
    body = deepcopy(doc['statements'][0]['body'])
    doc['statements'] = [dict(kind='ask', body=dict(kind='call', symbol='hznreport', arguments=[
        dict(kind='call', symbol='zg', arguments=[]), dict(kind='call', symbol='za', arguments=[]),
        dict(kind='quote', rank=3, body=dict(kind='content', variable='zpoint', body=body)),
        dict(kind='call', symbol='zt', arguments=[]), dict(kind='call', symbol='zanchor', arguments=[])]))]
    doc = parse(format_graph(doc, 'compact'))
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(zg=lambda: 'group', za=lambda: 'act', zt=lambda: 'target', zanchor=lambda: 'last',
                  hznreport=lambda n, a, content, scope, ctx: content.rank == 3 and
                  (n, a, scope, ctx) == ('group', 'act', 'target', 'last'))
    assert evaluate(doc, values, PEOPLE, SCENES, True) == [True]
    return dict(all_world_inputs_unknown_without_execution=True, generic_report_only=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='third_sentence_collective_retention_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[548, 593],
                            text=unit['text'][548:593]),
                third_sentence=dict(range=[449, 845], text=unit['text'][449:845]),
                interpretation=LIMITS, whole_sentence_semantically_verified=False,
                newly_reviewed_sentence_characters=0, preserved_first_two_sentence_characters=382,
                facsimile=dict(artifact=IMAGE, page=484, visually_collated=True,
                               url='https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00524/full/full/0/default.jpg',
                               scope='前頁末のaufge-からwiegelt worden以下、偏見・生み手/先任者・第三文末までを継続して確認。'),
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, IMAGE, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 59
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
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
    for path in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    generic = parse((ROOT / LIBRARY).read_text(encoding='utf-8'))
    assert not {'bf', 'wa', 'hzp3', 'h223i'} & {d['name'] for d in generic['declarations']}
    return dict(new_definitions=len(MEANINGS), new_primitives=2, preserved_statements=59,
                preserved_reviews=len(reviews), preserved_sentence_characters=382,
                generic_library_has_no_kant_bindings=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('causal', causal_checks), ('source', source_checks),
                     ('quotation', quote_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, IMAGE, PRIOR, *[p for p, _ in SENTENCES],
        'scripts/compose_collective_retention.py', 'scripts/check_collective_retention.py',
        'tests/test_collective_retention.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='collective_retention_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_collective_constraint_and_retention'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
