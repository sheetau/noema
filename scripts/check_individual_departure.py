"""Check sequence scales, native adapters, distributed scope and attribution."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_individual_departure import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v93.json'
AUDIT = 'data/individual-departure-reading-v1.json'
REPORT = 'reports/individual-departure-v1.json'
DOC = 'docs/individual-departure-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, suffix):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots.split()), statements=[])
    return parse(format_graph(doc, 'compact') + suffix)


def seq(items): return SequenceValue(tuple(items), '"individual"')


@lru_cache(None)
def order_checks():
    doc = fixture('r2dj rt r2dp r2dq', '''r zlevels[] j[a].r zfirst[] a.r zlast[] a.
q[k r2dj[k zlevels[] k zfirst[] k zlast[]]].
q[k rt[k zlevels[]]].
q[e[k r2dp[k zlevels[] k zfirst[]]][k zhead[]]].
q[e[k r2dq[k zlevels[] k zlast[]]][k ztail[]]].'''.replace('q[k r2dj', 'r zhead[] a.r ztail[] a.q[k r2dj', 1))
    rows = []
    for length in range(4):
        for levels in product(('a', 'b'), repeat=length):
            for first, last in product(('a', 'b', 'absent'), repeat=2):
                values = dict(zlevels=lambda: seq(levels), zfirst=lambda: first, zlast=lambda: last,
                    zhead=lambda: levels[0] if levels else first, ztail=lambda: levels[-1] if levels else last)
                actual = evaluate(doc, values, ('a', 'b', 'absent'), ('now',), True)
                expected = [any(x == first and y == last for i, x in enumerate(levels) for y in levels[i+1:]), len(set(levels)) == len(levels), True, True]
                assert actual == expected, (levels, first, last, actual, expected)
                rows.append(dict(levels=levels, first=first, last=last, values=actual))
    return dict(cases=len(rows), order_and_duplicate_oracle_agree=True, endpoints_match_direct_indexing=True,
                empty_and_absent_and_same_position_tested=True)


@lru_cache(None)
def adapter_checks():
    from scripts import check_unselected_continuation as nature
    from scripts import check_relative_difficulty as effort
    results = {}
    for label, name, source, people, scenes, levels in [
        ('nature', 'r2dk', nature, nature.SOURCE_PEOPLE, nature.SOURCE_SCENES, nature.VALUES),
        ('effort', 'r2dl', effort, effort.SOURCE_PEOPLE, effort.SOURCE_SCENES, effort.VALUES)]:
        suffix = 'r zperson[] a.r zpoint[] d.q[t[k ' + name + '[k zperson[]]][k zpoint[]]].'
        doc = fixture(name, suffix)
        def model(variant='baseline'):
            original = source.source_values(doc)
            values = dict(original)
            point = 'now' if label == 'nature' else 'start'
            dimension = 'reference' if label == 'nature' else 'dimension'
            values.update(zperson=lambda: 'person', zpoint=lambda: point,
                hzzo=lambda: dimension, hzzp=lambda: dimension,
                hzzj=lambda kind, anchor: seq(levels if variant != 'duplicate_scale' else (*levels, levels[0]))
                    if (kind, anchor) == (dimension, point) else seq(()))
            if label == 'nature':
                values['hzzk'] = lambda kind, degree, anchor: (kind, anchor) == (dimension, point) and original['znear'](degree)
                values['hzzl'] = lambda kind, *args: kind == dimension and original['zmeasured'](*args)
                if variant == 'other_dimension': values['hzzo'] = lambda: 'method'
                if variant == 'no_origin': values['hzzc'] = lambda *args: False
                if variant == 'missing_measure': values['hzzl'] = lambda *args: False
                if variant == 'near_is_top': values['hzzk'] = lambda kind, degree, anchor: degree == levels[-1]
                if variant == 'unknown': values['hzzl'] = unknown
            else:
                values['hzzm'] = lambda kind, person, degree, anchor: (kind, person, anchor) == (dimension, 'person', point) and original['zband'](degree)
                if variant == 'other_dimension': values['hzzp'] = lambda: 'method'
                if variant == 'other_person_band': values['hzzm'] = lambda kind, person, degree, anchor: person == 'other' and original['zband'](degree)
                if variant == 'no_self_work': values['h4n'] = lambda *args: False
                if variant == 'unknown': values['hzzm'] = unknown
            return values
        variants = ('baseline', 'duplicate_scale', 'other_dimension') + (
            ('no_origin', 'missing_measure', 'near_is_top') if label == 'nature' else ('other_person_band', 'no_self_work'))
        rows = {}
        for variant in variants:
            print(label + ': ' + variant, flush=True)
            actual = evaluate(doc, model(variant), people, scenes, True)
            assert actual == [variant == 'baseline'], (label, variant, actual)
            rows[variant] = actual
        try: evaluate(doc, model('unknown'), people, scenes, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError((label, 'unknown'))
        results[label] = dict(contrasts=rows, unknown_refused=True, native_component_executed=True)
    return results


@lru_cache(None)
def scope_checks():
    # A deliberately isolated boundary test. Native component execution is
    # checked above; this fixture checks quantifier and identity wiring only.
    original = fixture('r2dm', 'r zpoint[] d.q[t[k r2dm[]][k zpoint[]]].')
    doc = deepcopy(original)
    probes = parse('p:r zhabit[a d] c.r zdifficult[a d] c.d zfirst[person a] e[b point[k zhabit[v person v point]]].d zsecond[person a] e[b point[k zdifficult[v person v point]]].')
    mapping = {'r2dk': probes['declarations'][2]['body'], 'r2dl': probes['declarations'][3]['body']}
    for declaration in doc['declarations']:
        if declaration['name'] in mapping: declaration['body'] = deepcopy(mapping[declaration['name']])
    doc['declarations'] = probes['declarations'][:2] + doc['declarations']
    doc = parse(format_graph(doc, 'compact'))
    people = ('first', 'second', 'outsider', 'node')
    def model(scope, habit, difficult, human=('first', 'second', 'outsider')):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(zpoint=lambda: 'now', hzzq=lambda: 'node', aa=lambda p: p in human,
            hzzn=lambda node, p, point: node == 'node' and point == 'now' and p in scope,
            zhabit=lambda p, point: p in habit and point == 'now', zdifficult=lambda p, point: p in difficult and point == 'now')
        return values
    rows = []
    for bits in product((False, True), repeat=4):
        habit = {p for p, flag in zip(people[:2], bits[:2]) if flag}
        difficult = {p for p, flag in zip(people[:2], bits[2:]) if flag}
        actual = evaluate(doc, model(people[:2], habit, difficult), people, ('now',), True)
        assert actual == [all(bits)], (bits, actual)
        rows.append(dict(bits=bits, values=actual))
    contrasts = {}
    for name, scope, habit, difficult, human, expected in [
        ('empty_scope', (), (), (), people, False),
        ('nonhuman_scope_member', ('first', 'node'), people, people, people[:3], False),
        ('unqualified_outsider_not_quantified', ('first',), ('first',), ('first',), people[:3], True),
        ('split_people', people[:2], ('first',), ('second',), people[:3], False),
        ('one_failing_member', people[:2], people[:2], ('first',), people[:3], False)]:
        actual = evaluate(doc, model(scope, habit, difficult, human), people, ('now',), True)
        assert actual == [expected], (name, actual)
        contrasts[name] = actual
    values = model(people[:2], people[:2], people[:2]); values['hzzn'] = unknown
    try: evaluate(doc, values, people, ('now',), True)
    except ValueError as error: assert 'Unknown' in str(error)
    else: raise AssertionError('scope unknown')
    return dict(combinations=rows, contrasts=contrasts, unknown_refused=True,
                component_boundary_isolated=True, not_a_native_full_sentence_world_test=True)


@lru_cache(None)
def discourse_checks():
    doc = fixture('r2do wh', 'q[t[k r2do[]][k wh[]]].')
    nodes = ('mw', 'uo', 's3', 't4', 'hzsq', 'g2')
    people = nodes + ('claim', 'author', 'other')
    expected_content = {'kind': 'call', 'symbol': 'r2dm', 'arguments': []}
    rows = {}
    variants = ('baseline', 'no_attribution', 'other_author', 'other_claim', 'other_context', 'obsolete_content',
                'no_consequence', 'wrong_premise_set', 'reverse_order', 'one_missing_predecessor')
    for variant in variants:
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update({n: (lambda n=n: n) for n in nodes})
        wanted = dict(expected_content, symbol='hb2') if variant == 'obsolete_content' else expected_content
        values.update(hzzq=lambda: 'claim', wa=lambda: 'author', wh=lambda: 'now',
            uc=lambda node, author, content, point: variant != 'no_attribution' and (node, author, point) == (
                'other' if variant == 'other_claim' else 'claim', 'other' if variant == 'other_author' else 'author',
                'elsewhere' if variant == 'other_context' else 'now') and json.loads(content.syntax) == wanted,
            ud=lambda author, premises, node, point: variant != 'no_consequence' and (author, node, point) == ('author', 'claim', 'now') and
                {p for p in people if premises(p)} == set(nodes[:-1] if variant == 'wrong_premise_set' else nodes),
            ue=lambda first, last, point: (first in nodes and last == 'claim' if variant != 'reverse_order' else first == 'claim' and last in nodes)
                and point == 'now' and not (variant == 'one_missing_predecessor' and first == 't4'))
        actual = evaluate(doc, values, people, ('now', 'elsewhere'), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for name in ('uc', 'ud', 'ue'):
        # Rebuild the baseline callbacks, without borrowing a failing variant.
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update({n: (lambda n=n: n) for n in nodes})
        values.update(hzzq=lambda: 'claim', wa=lambda: 'author', wh=lambda: 'now', uc=lambda *args: True,
                      ud=lambda *args: True, ue=lambda *args: True)
        values[name] = unknown
        try: evaluate(doc, values, people, ('now',), True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(contrasts=rows, unknown_inputs_refused=3, world_contents_unknown=True,
                manuscript_assertion_quotes_closed_content=True, implication_not_asserted=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS,
             'reports/unselected-continuation-v1.json', 'reports/relative-difficulty-v1.json',
             'artifacts/first-cause-reading-v1/page-482.jpg', 'artifacts/future-dissemination-reading-v1/page-483.jpg'}
    return dict(status='first_sentence_composed_with_explicit_unresolved_readings', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            range=[0, 125], text=unit['text'][:125]), definitions=list(MEANINGS),
        decision='同じ人物への性向と困難さ、範囲を固定した各人への全称、著者帰属と先行説明からの帰結を一文に接続する。全文候補は記述できるが、到達可能性の含意と本性の読解は未決のため意味確認を保留する。',
        image_evidence='原版482末から483冒頭へ第一文が続く。直前は別段落、後続はEr hat sie...。画像は境界・接続の根拠であり、文脈範囲や語義を一意に確定しない。',
        interpretation_limits=LIMITS, authored_statement_index=51, whole_sentence_semantically_verified=False,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-16] == old.document['declarations']
    assert new.document['statements'][:-1] == old.document['statements'] and len(new.document['statements']) == 52
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS) | set(PRIMITIVES)
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        review = read(path); validate_hashes(ROOT, review['source_sha256'])
        ids = [s['index'] for s in review['selection']['statements']]
        assert review['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    assert len(read(INDEX)['works']['kant-1784']['reviews']) == 12
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    core = parse((ROOT / CORE).read_text(encoding='utf-8'))
    assert core['statements'] == [new.document['statements'][-1]]
    assert core['declarations'] == closure(new.document, list(MEANINGS) + ['wh'])
    assert reading() == read(AUDIT); validate_hashes(ROOT, read(AUDIT)['source_sha256'])
    return dict(new_definitions=8, new_primitives=8, preserved_statements=51, new_authored_assertions=1,
        preserved_review_selections=12, reviewed_nonblank_characters=2212, roundtrips=True,
        first_sentence_candidate_composed=True, lexical_equivalence_not_claimed=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('order', order_checks), ('adapters', adapter_checks), ('scope', scope_checks),
                     ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_individual_departure.py', 'scripts/check_individual_departure.py',
        'scripts/register_individual_departure.py', 'tests/test_individual_departure.py',
        'scripts/check_unselected_continuation.py', 'scripts/check_internalized_state.py', 'scripts/check_graded_change.py',
        'scripts/check_relative_difficulty.py', 'scripts/compose_graded_change.py', 'scripts/compose_limits.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/compose_grounded_step.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    unit = record['source']['text']
    return dict(status='scoped_attributed_first_sentence_candidate_checked', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, new_verified_sentence_characters=0,
        new_covered_characters=sum(not c.isspace() for c in unit[:41] + unit[124:125]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
