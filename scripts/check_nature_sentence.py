"""Check acquisition without a prescribed origin and review the first sentence."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_nature_sentence import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, MAPPING, parent, build, closure, revised_nature
from scripts.compose_courageous_undertaking import replace_symbols
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_unselected_continuation as prior

INDEX = 'data/semantic-review-index-v95.json'
AUDIT = 'data/nature-sentence-reading-v1.json'
REPORT = 'reports/nature-sentence-v1.json'
DOC = 'docs/nature-sentence-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
COMPONENTS = {
    'graded-change': ['r2cl', 'r2cm', 'r2cn', 'r2co', 'r2cp'],
    'internalized-state': ['r2ct'],
    'unselected-continuation': ['r2cw', 'r2cz'],
    'assessed-difficulty': ['r2dr', 'r2ds', 'r2du', 'r2dx', 'h4p'],
    'individual-departure': ['r2dj', 'r2dp', 'r2dq', 'r2dn'],
}
IMAGES = ['artifacts/first-cause-reading-v1/page-482.jpg', 'artifacts/future-dissemination-reading-v1/page-483.jpg']


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, suffix):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots.split()), statements=[])
    return parse(format_graph(doc, 'compact') + suffix)


def source_values(doc, variant='baseline'):
    values = prior.source_values(doc, variant)
    if variant == 'no_guided_activity': values['ad'] = lambda *args: False
    if variant == 'no_prior_experience': values['h3e'] = lambda *args: False
    if variant == 'no_formation_cause': values['hzzc'] = lambda *args: False
    if variant == 'no_process': values['ag'] = lambda *args: False
    if variant == 'other_pattern_owner':
        values['hzyz'] = lambda pattern, person, point: (pattern, person) == ('process', 'person')
    if variant == 'other_causal_pattern':
        values['hzie'] = lambda factor, prop, target, result, point: (factor, symbol(prop), target, symbol(result)) == (
            'process', 'r2cr', 'person', 'bf') and point in ('after', 'now')
    if variant == 'prior_deliberated_contribution':
        original = values['hzzd']
        values['hzzd'] = lambda pattern, person, desc, anchor, point, candidate: (
            (pattern, person, symbol(desc), anchor) == ('reference', 'person', 'bf', 'now') and candidate in ('before', 'after')
            if point == 'before' else original(pattern, person, desc, anchor, point, candidate))
        values['hzzf'] = lambda judgment, target, desc, polarity, point: (
            judgment, target, symbol(desc), polarity, point) == ('process', 'reference', 'r2cr', True, 'after')
    return values


@lru_cache(None)
def source_checks():
    doc = fixture('r2da r2ea', prior.SOURCE_DECLS + ''.join(
        'q[t[k ' + name + '[' + prior.SOURCE_ARGS + ']][k zanchor[]]].' for name in ('r2da', 'r2ea')))
    expected = dict(baseline=[True, True], no_guided_activity=[False, True], no_prior_experience=[False, True],
        no_formation_cause=[False, True], prior_deliberated_contribution=[False, True],
        currently_selected=[True, True], currently_opposed=[True, True])
    for name in ('no_process', 'missing_prior', 'ambiguous_prior', 'no_increase', 'no_internal_cause',
                 'other_pattern_owner', 'other_causal_pattern', 'selected_successes', 'all_selected', 'empty_selection_comparison'):
        expected[name] = [False, False]
    rows = {}
    for name, wanted in expected.items():
        actual = evaluate(doc, source_values(doc, name), prior.SOURCE_PEOPLE, prior.SOURCE_SCENES, True)
        assert actual == wanted, (name, actual, wanted)
        rows[name] = actual
        print('nature contrast ' + name, flush=True)
    new_only = deepcopy(doc); new_only['statements'] = [doc['statements'][1]]
    for name in ('h3e', 'hzzc'):
        values = source_values(new_only); values[name] = unknown
        assert evaluate(new_only, values, prior.SOURCE_PEOPLE, prior.SOURCE_SCENES, True) == [True]
    for name in ('zmeasured', 'ag', 'hzie', 'hzzf', 'hzzg'):
        values = source_values(new_only); values[name] = unknown
        try: evaluate(new_only, values, prior.SOURCE_PEOPLE, prior.SOURCE_SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    deps = {d['name'] for d in closure(catalog().document, ['r2ea'])}
    assert not deps & {'h3e', 'hzzc', 'r2cs', 'r2cq'}
    return dict(contrasts=rows, irrelevant_origin_unknowns_allowed=2, required_unknown_inputs_refused=5,
        new_content_tested_independently_with_unknowns=True, native_acquisition_and_current_cause_executed=True,
        independent_choice_and_withdrawal_profiles_not_forced_to_share_lower_endpoint=True)


@lru_cache(None)
def discourse_checks():
    doc = fixture('r2ed wh', 'q[t[k r2ed[]][k wh[]]].')
    nodes = ('mw', 'uo', 's3', 't4', 'hzsq', 'g2'); people = nodes + ('claim', 'author', 'other')
    def model(bits=(True,) * 8, variant='baseline'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update({n: (lambda n=n: n) for n in nodes})
        expected = dict(kind='call', symbol='r2dy' if variant == 'old_content' else 'r2ec', arguments=[])
        values.update(hzzq=lambda: 'claim', wa=lambda: 'author', wh=lambda: 'now',
            uc=lambda node, author, content, point: bits[0] and (node, author, point) == (
                'other' if variant == 'other_node' else 'claim', 'other' if variant == 'other_author' else 'author',
                'elsewhere' if variant == 'other_context' else 'now') and json.loads(content.syntax) == expected,
            ud=lambda author, premises, node, point: bits[1] and (author, node, point) == ('author', 'claim', 'now')
                and {p for p in people if premises(p)} == set(nodes[:-1] if variant == 'wrong_premises' else nodes),
            ue=lambda first, last, point: first in nodes and bits[2 + nodes.index(first)] and (
                last, point) == ('claim', 'now') and variant != 'reversed_order')
        return values
    for bits in product((False, True), repeat=8):
        assert evaluate(doc, model(bits), people, ('now', 'elsewhere'), True) == [all(bits)], bits
    rows = {}
    for name in ('baseline', 'old_content', 'other_author', 'other_node', 'other_context', 'wrong_premises', 'reversed_order'):
        actual = evaluate(doc, model(variant=name), people, ('now', 'elsewhere'), True)
        assert actual == [name == 'baseline'], (name, actual)
        rows[name] = actual
    for name in ('uc', 'ud', 'ue'):
        values = model(); values[name] = unknown
        try: evaluate(doc, values, people, ('now', 'elsewhere'), True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=256, contrasts=rows, unknown_inputs_refused=3, world_contents_unknown=True,
        quote_uses_revised_content=True, same_premises_author_context_order_preserved=True)


@lru_cache(None)
def reused_checks():
    current = catalog(); rows = {}
    for name, roots in COMPONENTS.items():
        path = 'reports/' + name + '-v1.json'; report = read(path)
        validate_hashes(ROOT, report['source_sha256'])
        old = parse((ROOT / report['document']).read_text(encoding='utf-8'))
        assert closure(old, roots) == closure(current.document, roots)
        dependencies = {d['name'] for d in closure(current.document, roots)}
        for name in dependencies:
            basis = current.entries[name]['meaning_basis']
            assert report['source_sha256'][basis] == current.source_sha256[basis], (path, name)
        rows[path] = dict(roots=roots, dependency_count=len(dependencies), declarations_and_meaning_sources_unchanged=True)
    return dict(reports=rows, finite_evidence_reused_without_claiming_new_execution=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    specs = [
        (0, 12, ['r2ed', 'r2dn', 'uc', 'ud', 'ue'], '先行六箇所からの帰結として著者がこの内容を提示する。推論の妥当性の保証ではない。'),
        (12, 41, ['r2ec', 'hzzn', 'aa'], '同じ文脈の非空の人の範囲に属する各人について述べる。対象を結果から選別せず、各人を別々に束縛する。'),
        (41, 49, ['r2dx', 'r2dw', 'r2du', 'r2ds'], '本人の力と評価された選択肢に照らし、余裕を持って達成を確保する方法がない。成功経路の存在も不存在もここでは追加しない。'),
        (49, 62, ['bf', 'h4p'], '同じ本人の現在の未成熟から、その本人が精神の作業を行って離脱する。援助者一般の不在は要求しない。'),
        (62, 108, ['r2ea', 'r2eb', 'r2ct', 'r2cp', 'r2cz'], '未成熟に寄与する本人の内的構成が、更新と選び直しを要さず働く程度を実際に増し、現在も完全な上端より手前の近接域にある。形容的背景の具体化として読む。'),
        (108, 125, ['h4p', 'h4o', 'h4l'], '自分の精神を働かせる過程を通じ、同じ本人が独立して理解を用いる能力へ至ることを目標とする。')]
    clauses = [dict(range=[start, end], text=unit['text'][start:end], definitions=roots, interpretation=explanation)
               for start, end, roots, explanation in specs]
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, *IMAGES}
    paths.update('reports/' + name + '-v1.json' for name in COMPONENTS)
    return dict(status='whole_first_sentence_reviewed_under_explicit_reading', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[0, 125], text=unit['text'][:125], nonblank_characters=108),
        selection=selection_binding(catalog(), [51]), clauses=clauses,
        decision='equivalent_under_stated_reading_for_this_sentence',
        interpretation='各人が自分の未成熟から精神の作業で離脱することの非容易性を、内的な定着という背景とともに述べる。この肯定の単独文を、以下の明示した文脈・尺度・比喩の読みで確認する。',
        references=[
            dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant, Aufklärung AA VIII036', accessed='2026-10-20', use='第一文と、当面の不能・成功者の少なさ・公衆の可能性の対照。画像482末尾から483冒頭も照合した。'),
            dict(url='https://korpora.org/Kant/aa07/149.html', title='Kant, Anthropologie AA VII149', accessed='2026-10-20', use='習慣の内的強制と別の本性という後年の記述を比較。全条件を1784年の比喩へ移さない。'),
            dict(url='https://lexika.digitale-sammlungen.de/adelung//lemma/bsb00009133_2_0_600', title='Adelung, Natur', accessed='2026-10-20', use='内的に組織された作用・変化の力と、習慣が別の本性になる用法を参照。生来という別義を必須にしない。')],
        interpretation_limits=LIMITS, revised_statement_index=51, whole_sentence_semantically_verified=True,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=108,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-4] == old.document['declarations']
    assert len(new.document['statements']) == len(old.document['statements']) == 52
    assert new.document['statements'][:-1] == old.document['statements'][:-1]
    assert new.document['statements'][-1] == replace_symbols(old.document['statements'][-1], MAPPING)
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS)
    assert new.entries['r2ea']['declaration'] == revised_nature(old)
    for before in ('r2dk', 'r2dy', 'r2dz'):
        expected = replace_symbols(deepcopy(old.entries[before]['declaration']), MAPPING)
        expected['name'] = MAPPING[before]
        assert new.entries[MAPPING[before]]['declaration'] == expected
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
    record = reading(); assert record == read(AUDIT); validate_hashes(ROOT, record['source_sha256'])
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == record['source']['unit'])
    assert digest(unit['text'].encode('utf-8')) == record['source']['unit_sha256']
    assert ''.join(c['text'] for c in record['clauses']) == unit['text'][:125]
    assert [i for c in record['clauses'] for i in range(*c['range'])] == list(range(125))
    assert sum(not ch.isspace() for ch in unit['text'][:125]) == 108
    assert all(set(c['definitions']) <= set(record['selection']['dependencies']) for c in record['clauses'])
    return dict(new_definitions=4, new_primitives=0, preserved_statements=51, revised_statement_index=51,
        authored_statements=52, preserved_review_selections=12, reviewed_nonblank_characters=2212,
        clause_partition=6, reviewed_sentence_characters=108, nonblank_source_partition_complete=True,
        scope_and_attribution_exactly_rebound=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('source', source_checks), ('discourse', discourse_checks), ('reused', reused_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_nature_sentence.py', 'scripts/check_nature_sentence.py', 'scripts/register_nature_sentence.py',
        'tests/test_nature_sentence.py', 'scripts/check_unselected_continuation.py', 'scripts/check_internalized_state.py',
        'scripts/check_graded_change.py', 'scripts/compose_courageous_undertaking.py', 'scripts/compose_grounded_step.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    for name in COMPONENTS: paths.update(read('reports/' + name + '-v1.json')['source_sha256'])
    return dict(status='whole_nature_sentence_reviewed_under_explicit_reading', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        review_decision=record['decision'], reviewer='assistant_review', whole_sentence_semantically_verified=True,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=108, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
