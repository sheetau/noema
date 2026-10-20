"""Check source field bindings, local message witnesses and quote referents."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content, FunctionValue
from noema.existential_witnesses import verify_witnesses
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_dissemination_content import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS,
    BASE_FIELDS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v121.json'
REPORT = 'reports/dissemination-content-v1.json'
AUDIT = 'data/dissemination-content-reading-v1.json'
DOC = 'docs/dissemination-content-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
READING = 'data/public-first-sentence-reading-v1.json'
PRIOR = ['reports/dissemination-opportunities-v1.json', 'reports/qualitative-receipt-v1.json',
         'reports/reasoned-self-appraisal-v1.json', 'reports/existential-route-fields-v1.json',
         'reports/relative-dissemination-v1.json']
PEOPLE = ('group', 'wrong', 'p', 'q', 'r', 'criterion', 'subject')
SCENES = ('reference', 'branch', 'other', 'normal', 'exception')
NAMES = '''
r zagroup[] a.r zareference[] d.r zabranch[] d.r zaother[] d.
r zselect[d i[d] i[d] i[d]] i[d].
d h223g[person a] i[a][r[k zagroup[]]].
d h223h[scene d] i[d][k zselect[v scene r[k zareference[]] r[k zabranch[]] r[k zaother[]]]].
'''


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, extra, boundaries=(), named=False):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    if named:
        doc['declarations'] = parse('p:' + NAMES)['declarations'] + [
            d for d in doc['declarations'] if d['name'] not in ('h223g', 'h223h')]
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


def names(variant='baseline'):
    return dict(zagroup=lambda: 'wrong' if variant == 'wrong_public_name' else 'group',
                zareference=lambda: 'other' if variant == 'wrong_reference_name' else 'reference',
                zabranch=lambda: 'other' if variant == 'wrong_branch_name' else 'branch',
                zaother=lambda: 'other',
                zselect=lambda point, reference, branch, other:
                reference if point == 'reference' else branch if point == 'branch' else other)


def call_syntax(name):
    return dict(kind='call', symbol=name, arguments=[])


def applied_syntax(name, arguments):
    return dict(kind='apply', function=dict(kind='function_ref', symbol=name),
                arguments=[call_syntax(a) for a in arguments])


@lru_cache(None)
def state_checks():
    doc = fixture(['r2m2'], 'r zg[] a.r zr[] d.r zb[] d.r zp[] a.'
                  'q[t[c[s[k r2m2[k zg[] k zr[] k zb[]]]][k zp[]]][k zr[]]].',
                  ('hznu',), named=True)
    seen = set()

    def model(normal=True, exception=False, ranked=True):
        values = unknowns(doc)
        values.update(names(), zg=lambda: 'group', zr=lambda: 'reference', zb=lambda: 'branch', zp=lambda: 'p')

        def field(g, r, b, p, a, *args):
            assert (g, r, b) == ('group', 'reference', 'branch')
            seen.add((p, a))

        def response(criterion, subject, source, role):
            assert (criterion, subject) == ('criterion', 'subject')
            assert json.loads(source.syntax) == applied_syntax('h222x', ['zagroup', 'zareference'])
            assert json.loads(role.syntax) == applied_syntax('h222y', ['zagroup', 'zareference'])
            return FunctionValue(('individual',), 'content', lambda person: Content(
                SCENES, tuple(person == 'p' and ((s == 'normal' and normal) or
                                               (s == 'exception' and exception)) for s in SCENES)))

        values.update(h222v=lambda g, r: 'criterion' if (g, r) == ('group', 'reference') else 'wrong',
                      h222w=lambda g, r: 'subject' if (g, r) == ('group', 'reference') else 'wrong',
                      hznu=response,
                      h222z=lambda g, r, b, p, a, s: field(g, r, b, p, a, s) is None and s in ('normal', 'exception'),
                      h223a=lambda g, r, b, p, a, x, y: field(g, r, b, p, a, x, y) is None and
                      ranked and (x, y) == ('normal', 'exception'))
        return values

    for normal, exception, ranked in product((False, True), repeat=3):
        actual = evaluate(doc, model(normal, exception, ranked), PEOPLE, SCENES, True)
        assert actual == [normal and (ranked or exception)]
    assert ('p', 'reference') in seen
    for name in ('h222z', 'h223a', 'h222v'):
        values = model()
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(response_and_normality_combinations=8, native_qualitative_disposition=True,
                contextual_referents_preserved_in_norm_description=True,
                appraisal_and_assent_are_explicit_test_boundary=True, unknown_inputs_refused=3)


@lru_cache(None)
def binding_checks():
    doc = fixture(['r2m3'], 'r zg[] a.r zr[] d.r zsubgroup[a d] c.'
                  'q[t[c[k r2m3[k zg[] k zr[]]][r[p zsubgroup]]][k zr[]]].',
                  ('r2ly',), named=True)
    seen = set()
    subgroup_sort = next(d for d in doc['declarations'] if d['name'] == 'r2m3')['result']['parameters'][0]
    predicate = lambda members: FunctionValue(('individual',), 'truth', lambda p: p in members)

    def model(variant='baseline'):
        values = unknowns(doc)
        values.update(names(variant), zg=lambda: 'group', zr=lambda: 'reference',
                      h222k=lambda g, r, b: (g, r) == ('group', 'reference') and b == 'branch',
                      aa=lambda p: p in ('p', 'q', 'r'),
                      sa=lambda p, q, r: r == 'reference' and (p, q) in {('p', 'q'), ('r', 'p')})

        def record(kind, g, r, b, *args):
            assert (g, r, b) == ('group', 'reference', 'branch')
            seen.add(kind)
            return True

        values.update(
            h223b=lambda *a: record('cases', *a),
            h223c=lambda *a: record('preferred', *a),
            h223d=lambda *a: 'subject' if record('topics', *a) else 'wrong',
            h223e=lambda *a: record('presented', *a),
            h223f=lambda *a: record('opportunities', *a) and a[-1] == 'normal',
        )

        def frame(group, reference, state, extent, scope, cases, preferred, topics, presented, opportunities):
            assert (group, reference) == ('group', 'reference')
            description = state('branch')
            assert description.rank == 0
            assert json.loads(description.syntax) == applied_syntax('r2lz', ['zagroup', 'zareference', 'zabranch'])
            spread = extent('branch')
            assert spread(predicate({'p', 'q', 'r'}), predicate({'p', 'q'}))
            assert not spread(predicate({'p', 'q', 'r'}), predicate({'p'}))
            assert not spread(predicate({'p', 'q'}), predicate({'p', 'r'}))
            surrounding = scope('branch')
            assert surrounding('p', 'q', reference) and surrounding('p', 'r', reference)
            assert not surrounding('p', 'q', 'other')
            assert not surrounding('p', 'group', reference)
            assert cases('branch')('p', 'reference', 'normal')
            assert preferred('branch')('p', 'reference', 'normal', 'exception')
            assert topics('branch')('p', 'reference', 'normal') == 'subject'
            assert presented('branch')('p', 'subject', 'normal')
            assert opportunities('branch')('normal') and not opportunities('branch')('exception')
            return FunctionValue((subgroup_sort,), 'content', lambda subgroup: Content(
                SCENES, tuple(symbol(subgroup) == 'zsubgroup' for s in SCENES)))

        values['r2ly'] = frame
        return values

    rows = {}
    for variant in ('baseline', 'wrong_public_name', 'wrong_reference_name', 'wrong_branch_name'):
        actual = evaluate(doc, model(variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    assert seen == {'cases', 'preferred', 'topics', 'presented', 'opportunities'}
    for name in ('h223f', 'zselect', 'sa'):
        values = model()
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(all_eight_providers_bound=True, designation_contrasts=rows,
                native_social_scope_and_plural_extent=True,
                wrong_quoted_referents_refused=True, unknown_inputs_refused=3,
                conditional_forecast_is_explicit_test_boundary=True)


@lru_cache(None)
def witness_checks():
    fields = [(n, t) for n, t in BASE_FIELDS if n not in ('subject', 'message')]
    helpers = ''.join('r z' + n + '[] ' + t + '.' for n, t in fields if n != 'state')
    helpers += 'r zstate[a] e.r zmessage[a] f.r zothermessage[a] f.r zsubject[] a.'
    args = ['r[p zstate]' if n == 'state' else 'k z' + n + '[]' for n, t in fields]
    doc = fixture(['r2lu'], helpers + 'q[k r2lu[' + ' '.join(args) + ']].', ('hzq3', 'hzr5'))
    query = parse('p:r zsubject[] a.r zmessage[a] f.q[e[k zsubject[]][k zsubject[]]].'
                  'q[e[r[p zmessage]][r[p zmessage]]].')
    witnesses = [s['body']['arguments'][0] for s in query['statements']]
    values = unknowns(doc)
    values.update(zreference=lambda: 'reference', zorigin=lambda: 'p', zframe=lambda: 'group',
                  zinitial=lambda: 'normal', zanchor=lambda: 'branch', zsubject=lambda: 'subject')
    declarations = {d['name']: d for d in doc['declarations']}
    for name in ('extent', 'scope', 'thinkcases', 'thinkpreferred', 'thinktopics', 'thinkpresented'):
        sort = declarations['z' + name]['result']
        values['z' + name] = lambda sort=sort: FunctionValue(
            tuple(sort['parameters']), sort['result'], unknown)
    observed = []

    def qualifies(person, initial, *args):
        observed.append(('thinking', person, initial))
        return (person, initial) == ('p', 'normal')

    def disseminates(reference, person, subject, message, state, frame, initial, anchor, extent, scope):
        observed.append(('dissemination', person, initial))
        return (reference, person, subject, frame, initial, anchor) == (
            'reference', 'p', 'subject', 'group', 'normal', 'branch') and symbol(message) == 'zmessage' \
            and symbol(state) == 'zstate'

    values.update(hzq3=qualifies, hzr5=disseminates)
    options = dict(individuals=PEOPLE, situations=SCENES,
                   primitives={d['name']: values[d['name']] for d in doc['declarations'] if d['kind'] == 'primitive'},
                   max_steps=1000000, memoize_definitions=True, memoize_expressions=True)
    good = verify_witnesses(doc, witnesses, **options)
    assert good['status'] == 'valid' and good['witnesses_checked'] == 2
    bad = deepcopy(witnesses)
    bad[1]['body']['symbol'] = 'zothermessage'
    failed = verify_witnesses(doc, bad, **options)
    assert failed['status'] == 'uncertified' and not failed['theorem_disproved']
    assert {row[1:] for row in observed} == {('p', 'normal')}
    try:
        evaluate(doc, values, PEOPLE, SCENES, True)
    except ValueError as error:
        assert 'Cannot finitely quantify the description domain' in str(error)
    else:
        raise AssertionError('Description domain silently enumerated')
    return dict(topic_and_message_witnesses=2, same_person_and_opportunity=True,
                failed_witness_does_not_disprove_existence=True, unlimited_description_domain_not_enumerated=True,
                thinking_and_transmission_are_explicit_test_boundaries=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='dissemination_fields_bound_sentence_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[129, 448], text=unit['text'][129:448]),
                interpretation=LIMITS,
                remaining=['同じ公衆について、任用された後見役・大衆とsogarの主張／比較背景を接続する。',
                           '頚木の比喩と自己離脱を、予測内の同じ人物・前後関係へ対応させる。',
                           '閉じた著者帰属と第一文への理由提示を完成させ、第二文全体を再読する。'],
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                preserved_first_sentence_characters=108, newly_reviewed_sentence_characters=0,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted({FULL, BASIS, DOC, INVENTORY, *PRIOR})})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert new.document['statements'] == old.document['statements']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    local = deepcopy(new.entries['r2lu']['declaration'])
    bound = []
    while local['body']['kind'] == 'exists':
        body = local['body']
        bound.append(dict(name=body['variable'], sort=body['sort']))
        local['body'] = body['body']
    assert len(bound) == 2
    local['name'] = 'hzr6'
    local['parameters'][2:2] = bound
    context = deepcopy(old.document)
    position = next(i for i, d in enumerate(context['declarations']) if d['name'] == 'hzr6')
    context['declarations'][position] = local
    assert parse(format_graph(context, 'compact')) == old.document
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    assert read(READING)['selection'] == selection_binding(new, [55, 56])
    validate_hashes(ROOT, read(READING)['source_sha256'])
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
    return dict(new_definitions=len(MEANINGS), new_context_inputs=len(PRIMITIVES), statements_preserved=57,
                remaining_provider_arguments=0, remaining_audience_reference_and_focus_arguments=True,
                preserved_whole_unit_reviews=len(reviews), preserved_first_sentence_characters=108, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('state', state_checks), ('binding', binding_checks), ('witnesses', witness_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, READING, *PRIOR, 'scripts/compose_dissemination_content.py',
        'scripts/check_dissemination_content.py', 'tests/test_dissemination_content.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/compose_dissemination_opportunities.py', 'scripts/compose_shared_future_period.py',
        'scripts/compose_existential_dissemination.py', 'scripts/compose_qualitative_thinkers.py',
        'scripts/compose_existential_route_fields.py', 'scripts/compose_described_dissemination.py',
        'scripts/compose_thinking_disseminators.py', 'scripts/compose_existential_focus.py',
        'noema/existential_witnesses.py',
    }
    source = read(AUDIT)['source']
    phrase = 'den Geist einer vernünftigen Schätzung des eigenen Werths und des Berufs jedes Menschen selbst zu denken um sich verbreiten'
    start = source['range'][0] + source['text'].index(phrase)
    return dict(status='second_sentence_content_bindings_partial', document=FULL, **results,
                alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'],
                               range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS),
                               status='partial_content_and_surroundings_binding'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
