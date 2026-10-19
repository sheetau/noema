"""Check evaluated non-ease, path impossibility and the revised manuscript claim."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_assessed_difficulty import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, MAPPING, parent, build, closure
from scripts.compose_courageous_undertaking import replace_symbols
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts import check_relative_difficulty as prior
from scripts.compose_relative_difficulty import TASK

INDEX = 'data/semantic-review-index-v94.json'
AUDIT = 'data/assessed-difficulty-reading-v1.json'
REPORT = 'reports/assessed-difficulty-v1.json'
DOC = 'docs/assessed-difficulty-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, suffix):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots.split()), statements=[])
    return parse(format_graph(doc, 'compact') + suffix)


def data(first='heavy', second='full', first_success=True, second_success=True, variant='baseline'):
    d = prior.data(first, second, first_success, second_success, variant)
    if variant.startswith('mixed_'):
        d['success'] = {'first': {'one'}, 'second': set()}
        d['required']['first'] = {'one': {'light'}, 'two': {'heavy'}}
    if variant == 'mixed_missing_success_cost': d['required']['first']['one'] = set()
    if variant == 'mixed_ambiguous_success_cost': d['required']['first']['one'] = {'light', 'heavy'}
    if variant == 'mixed_outside_success_cost': d['required']['first']['one'] = {'other'}
    if variant == 'mixed_unaffordable_success':
        d.update(capacity={'light'}, band={'light'}); d['required']['first']['one'] = {'heavy'}
    if variant == 'mixed_missing_failed_cost': d['required']['first']['two'] = set()
    if variant == 'demanding_route_and_unassessed_mixed_alternative':
        d['success']['second'] = {'one'}; d['required']['second']['one'] = set()
    return d


def oracle(d):
    # Set/position calculation independent of the Noema quantifier construction.
    scale, order, low, high = (d[k] for k in ('scale', 'less', 'low', 'high'))
    ordered = low in scale and high in scale and low != high and all((x, x) not in order for x in scale) and all(
        a == b or ((a, b) in order) != ((b, a) in order) for a in scale for b in scale) and all(
        (a, c) in order for a in scale for b in scale for c in scale if (a, b) in order and (b, c) in order) and all(
        (x == low or (low, x) in order) and (x == high or (x, high) in order) for x in scale)
    def unique(values): return next(iter(values)) if len(values) == 1 and values <= scale else None
    limit = unique(d['capacity']); band = d['band']
    setting = ordered and limit is not None and bool(band) == (limit != low) and all(
        x in scale and (low, x) in order and (x == limit or (x, limit) in order) for x in band) and all(
        y in band for x in band for y in scale if (x, y) in order and (y == limit or (y, limit) in order))
    assessed = True; easy = []; paths = []
    for plan in d['available']:
        selected = d['selected'][plan]; valid = bool(selected) and selected <= d['outcomes'][plan]
        successful = selected & d['success'][plan]
        costs = {end: unique(d['required'][plan].get(end, set())) for end in selected}
        assessed &= valid and all(costs[end] is not None for end in successful)
        affordable = {end for end in successful if costs[end] is not None and limit is not None and (
            costs[end] == limit or (costs[end], limit) in order)}
        paths.append(valid and bool(affordable))
        easy.append(valid and affordable == selected and all(costs[end] not in band for end in selected))
    return [prior.oracle(d)[1], bool(setting and assessed and not any(easy)),
            bool(setting and assessed and not any(paths)), bool(assessed)]


CONTRASTS = ('missing_success_cost', 'ambiguous_success_cost', 'outside_success_cost', 'missing_failed_cost',
    'cheap_failed_route', 'cheap_success_route', 'easy_witness_unassessed_alternative', 'one_easy_path',
    'partial_success_only', 'only_failed_routes', 'no_methods', 'empty_selection', 'outside_selection',
    'missing_capacity', 'ambiguous_capacity', 'outside_capacity', 'unaffordable', 'same_effort_smaller_capacity',
    'same_effort_more_reserve', 'no_additional_resource', 'empty_band', 'band_hole', 'band_includes_low',
    'band_above_capacity', 'cyclic_scale', 'wrong_cost_actor', 'wrong_cost_start', 'mixed_cheap_success',
    'mixed_missing_success_cost', 'mixed_ambiguous_success_cost', 'mixed_outside_success_cost',
    'mixed_unaffordable_success', 'mixed_missing_failed_cost', 'demanding_route_and_unassessed_mixed_alternative')


@lru_cache(None)
def generic_checks():
    suffix = prior.DECLS + ''.join('q[k ' + name + '[' + prior.ARGS + ']].' for name in ('r2dh', 'r2du', 'r2dv'))
    suffix += 'q[k r2ds[k zactor[] k zstart[] p zscale p zrequired p zavailable p zoutcomes p zselected p zsuccess]].'
    doc = fixture('r2dh r2du r2dv r2ds', suffix); rows = []
    for first, second, first_success, second_success in product(prior.VALUES, prior.VALUES, (False, True), (False, True)):
        d = data(first, second, first_success, second_success)
        actual = evaluate(doc, prior.model(d), prior.PEOPLE, prior.SCENES, True)
        assert actual == oracle(d), (first, second, first_success, second_success, actual, oracle(d))
        rows.append(dict(first=first, second=second, first_success=first_success, second_success=second_success, values=actual))
    contrasts = {}
    for name in CONTRASTS:
        d = data(variant=name)
        actual = evaluate(doc, prior.model(d, name), prior.PEOPLE, prior.SCENES, True)
        assert actual == oracle(d), (name, actual, oracle(d))
        contrasts[name] = actual
    assert contrasts['no_methods'] == contrasts['only_failed_routes'] == [False, True, True, True]
    assert contrasts['mixed_cheap_success'] == contrasts['mixed_missing_failed_cost'] == [False, True, False, True]
    assert contrasts['mixed_missing_success_cost'] == [False, False, False, False]
    assert contrasts['demanding_route_and_unassessed_mixed_alternative'] == [True, False, False, False]
    for statement in doc['statements'][1:3]:
        probe = deepcopy(doc); probe['statements'] = [statement]
        for name in ('zscale', 'zless', 'zband', 'zcapacity', 'zrequired', 'zavailable', 'zoutcomes', 'zselected', 'zsuccess'):
            values = prior.model(data()); values[name] = unknown
            try: evaluate(probe, values, prior.PEOPLE, prior.SCENES, True)
            except ValueError as error: assert 'Unknown' in str(error)
            else: raise AssertionError((statement['body']['symbol'], name))
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=18,
                both_new_classifiers_tested_independently_with_unknown_inputs=True,
                successful_path_not_confused_with_guaranteed_strategy=True,
                missing_mixed_success_cost_not_counted_as_impossibility=True,
                known_empty_choices_distinct_from_unknown_choices=True)


@lru_cache(None)
def source_checks():
    # Exercise the original self-work, capacity, transition and cause definitions.
    doc = fixture('r2di r2dw r2dv r2dx r2dl', prior.SOURCE_DECLS + '''
q[t[k r2di[''' + prior.SOURCE_ARGS + ']][k zstart[]]].q[t[k r2dw[' + prior.SOURCE_ARGS + ''']][k zstart[]]].
q[t[k r2dl[k zperson[]]][k zstart[]]].q[t[k r2dx[k zperson[]]][k zstart[]]].''')
    rows = {}
    variants = ('baseline', 'no_self_work', 'no_future_capacity', 'cheap_failed_route', 'cheap_success_route',
                'other_effort_agent', 'other_beneficiary', 'other_dimension', 'more_reserve')
    from noema.constructed_semantics import SequenceValue
    for variant in variants:
        values = prior.source_values(doc, variant)
        values.update(hzzp=lambda: 'dimension', hzzj=lambda kind, point: SequenceValue(prior.VALUES, '"individual"'),
            hzzm=lambda kind, person, degree, point: (kind, person) == ('dimension', 'person') and values['zband'](degree))
        actual = evaluate(doc, values, prior.SOURCE_PEOPLE, prior.SOURCE_SCENES, True)
        old = variant in ('baseline', 'cheap_failed_route')
        new = variant in ('baseline', 'cheap_failed_route', 'no_self_work', 'no_future_capacity')
        assert actual == [old, new, old, new], (variant, actual)
        rows[variant] = actual
    for position in (1, 3):
        probe = deepcopy(doc); probe['statements'] = [doc['statements'][position]]
        for name in ('hzzh', 'hzzi', 'h4n'):
            values = prior.source_values(doc)
            values.update(hzzp=lambda: 'dimension', hzzj=lambda *args: SequenceValue(prior.VALUES, '"individual"'),
                          hzzm=lambda kind, person, degree, point: degree in ('heavy', 'full'))
            values[name] = unknown
            try: evaluate(probe, values, prior.SOURCE_PEOPLE, prior.SOURCE_SCENES, True)
            except ValueError as error: assert 'Unknown' in str(error)
            else: raise AssertionError((position, name))
    return dict(contrasts=rows, unknown_inputs_refused=6, native_self_work_and_capacity_executed=True,
                both_new_contents_tested_independently_with_unknown_inputs=True,
                old_and_new_closed_scale_adapters_executed=True, no_achievement_presupposed=True)


@lru_cache(None)
def discourse_checks():
    doc = fixture('r2dz wh', 'q[t[k r2dz[]][k wh[]]].')
    nodes = ('mw', 'uo', 's3', 't4', 'hzsq', 'g2'); people = nodes + ('claim', 'author', 'other')
    rows = {}
    for variant in ('baseline', 'old_content', 'other_author', 'other_node', 'other_context', 'no_consequence', 'reversed_order'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update({n: (lambda n=n: n) for n in nodes})
        expected = dict(kind='call', symbol='r2dm' if variant == 'old_content' else 'r2dy', arguments=[])
        values.update(hzzq=lambda: 'claim', wa=lambda: 'author', wh=lambda: 'now',
            uc=lambda node, author, content, point: (node, author, point) == (
                'other' if variant == 'other_node' else 'claim', 'other' if variant == 'other_author' else 'author',
                'elsewhere' if variant == 'other_context' else 'now') and json.loads(content.syntax) == expected,
            ud=lambda author, premises, node, point: variant != 'no_consequence' and (author, node, point) == ('author', 'claim', 'now')
                and {p for p in people if premises(p)} == set(nodes),
            ue=lambda first, last, point: variant != 'reversed_order' and first in nodes and (last, point) == ('claim', 'now'))
        actual = evaluate(doc, values, people, ('now', 'elsewhere'), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, world_contents_unknown=True, quote_uses_revised_content=True,
                same_premises_author_context_order_preserved=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, 'reports/individual-departure-v1.json', 'reports/relative-difficulty-v1.json'}
    return dict(status='non_ease_reading_without_universal_attainability', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[0, 125], text=unit['text'][:125]), definitions=list(MEANINGS),
        decision='第一文の困難さを、評価された選択肢の中に余裕を持って達成を確保できる方法がないという読みへ改訂する。達成経路の有無は別定義で検査できるが本文では断定しない。混合結果の成功経路の評価欠落も拒み、旧第52文の引用内容だけを更新する。',
        references=[
            dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant, Aufklärung AA VIII036', accessed='2026-10-20',
                 use='各個人の困難さ、当面の不能、成功者の少なさと、公衆が自己啓蒙する可能性の対照を読む。全員の到達可能性を追加しないという今回の解釈判断の文脈であり、それ自体の論理的証明ではない。'),
            dict(url='https://korpora.org/Kant/aa07/146.html', title='Kant, Anthropologie AA VII146', accessed='2026-10-20',
                 use='容易・困難を身体的性質との類比から能力の議論へ導入する箇所を、147頁へ続けて確認した。'),
            dict(url='https://korpora.org/Kant/aa07/147.html', title='Kant, Anthropologie AA VII147', accessed='2026-10-20',
                 use='容易さを本人の力の余裕と結び、困難・相対的な実行不能・煩わしさを区別する後年の記述を参照した。結果の採用と経路評価は本実装の明示的な形式化である。')],
        interpretation_limits=LIMITS, revised_statement_index=51, whole_sentence_semantically_verified=False,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=0, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-9] == old.document['declarations']
    assert len(new.document['statements']) == len(old.document['statements']) == 52
    assert new.document['statements'][:-1] == old.document['statements'][:-1]
    assert new.document['statements'][-1] == replace_symbols(old.document['statements'][-1], MAPPING)
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS)
    for before, after in MAPPING.items():
        expected = replace_symbols(deepcopy(old.entries[before]['declaration']), dict(MAPPING, r2dh='r2du'))
        expected['name'] = after
        assert new.entries[after]['declaration'] == expected
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        review = read(path); validate_hashes(ROOT, review['source_sha256'])
        ids = [s['index'] for s in review['selection']['statements']]
        assert 51 not in ids and review['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    assert len(read(INDEX)['works']['kant-1784']['reviews']) == 12
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert reading() == read(AUDIT); validate_hashes(ROOT, read(AUDIT)['source_sha256'])
    return dict(new_definitions=9, new_primitives=0, preserved_statements=51, revised_statement_index=51,
                authored_statements=52, preserved_review_selections=12, reviewed_nonblank_characters=2212,
                scope_and_attribution_exactly_rebound=True, roundtrips=True, lexical_equivalence_not_claimed=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('source', source_checks), ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_assessed_difficulty.py', 'scripts/check_assessed_difficulty.py', 'scripts/register_assessed_difficulty.py',
        'tests/test_assessed_difficulty.py', 'scripts/check_relative_difficulty.py', 'scripts/compose_relative_difficulty.py',
        'scripts/compose_graded_change.py', 'scripts/compose_courageous_undertaking.py', 'scripts/compose_limits.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/compose_grounded_step.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='assessed_non_ease_and_path_absence_separated', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, new_verified_sentence_characters=0, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
