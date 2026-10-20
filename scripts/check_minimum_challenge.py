"""Check contextual minima and binding-aware expectation independently of truth."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, canonical_digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_minimum_challenge import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, PRIMITIVES, LIMITS, PREDICATE, ORDER, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_uncertain_judgment import source_values as judgment_values, PEOPLE as JUDGMENT_PEOPLE, SCENES as JUDGMENT_SCENES

INDEX = 'data/semantic-review-index-v109.json'
REPORT = 'reports/minimum-challenge-v1.json'
AUDIT = 'data/minimum-challenge-reading-v1.json'
DOC = 'docs/minimum-challenge-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/unfamiliar-judgment-v1.json', 'reports/uncertain-judgment-v1.json', 'reports/abandoned-reliance-v1.json', 'reports/depicted-referents-v1.json', 'reports/fetters-sentence-v1.json']
SENTENCES = [('data/nature-sentence-reading-v1.json', [51]), ('data/confirmed-incapacity-reading-v1.json', [11, 12]), ('data/fetters-sentence-reading-v1.json', [10, 52])]
TASKS = ('topic', 'harder', 'hardest')
PEOPLE = ('person', 'second', 'author', 'node') + TASKS
SCENES = ('anchor', 'one', 'two')


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))
@lru_cache(None)
def document(): return parse((ROOT / FULL).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def fixture(roots, extra):
    doc = deepcopy(document()); doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc): return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


def refuse(doc, values, names, people=PEOPLE, scenes=SCENES):
    for name in names:
        changed = dict(values); changed[name] = unknown
        try: evaluate(doc, changed, people, scenes, True)
        except ValueError as error: assert 'Unknown' in str(error), (name, str(error))
        else: raise AssertionError(name)


def task_values(doc, tasks=TASKS, levels=(0, 1, 2), variant='baseline'):
    values = unknowns(doc)
    values.update(zperson=lambda: 'person', zanchor=lambda: 'anchor', wh=lambda: 'anchor', wa=lambda: 'author',
        hzzzz=lambda p, sc: 'topic' if (p, sc) == ('person', 'anchor') else 'harder',
        h222a=lambda p, sc, t: (p, sc) == ('person', 'anchor') and t in tasks,
        h222b=lambda p, a, b, s: (p, s) == ('person', 'anchor') and a in tasks and b in tasks and levels[tasks.index(a)] <= levels[tasks.index(b)],
        h222c=lambda observer, pred, a, t, b, u, s: (
            observer, symbol(pred), a, b, s) == ('author', 'r2hn', 'person', 'person', 'anchor') and t in tasks and u in tasks and tasks.index(t) >= tasks.index(u))
    return values


@lru_cache(None)
def minimum_checks():
    doc = fixture(['r2hr'], 'r zperson[] a.r zanchor[] d.q[k r2hr[k zperson[] k zanchor[]]].')
    for bits in product((False, True), repeat=9):
        edges = {p for p, flag in zip(product(TASKS, repeat=2), bits) if flag}
        values = task_values(doc)
        values['h222b'] = lambda p, a, b, s: (p, s) == ('person', 'anchor') and (a, b) in edges
        preorder = all((a, a) in edges for a in TASKS) and all((a, b) in edges or (b, a) in edges for a, b in product(TASKS, repeat=2)) and all(
            not ((a, b) in edges and (b, c) in edges) or (a, c) in edges for a, b, c in product(TASKS, repeat=3))
        wanted = preorder and all(('topic', b) in edges for b in TASKS)
        assert evaluate(doc, values, PEOPLE, SCENES, True) == [wanted], bits
    rows = {}
    for name, tasks, levels, expected in [('baseline', TASKS, (0, 1, 2), True), ('tied_minima', TASKS, (0, 0, 1), True),
        ('all_tied', TASKS, (0, 0, 0), True), ('singleton', TASKS[:1], (0,), True), ('empty', (), (), False),
        ('outside', TASKS[1:], (1, 2), False), ('not_minimum', TASKS, (1, 0, 2), False)]:
        actual = evaluate(doc, task_values(doc, tasks, levels), PEOPLE, SCENES, True)
        assert actual == [expected], (name, actual); rows[name] = actual
    refuse(doc, task_values(doc), ('wh', 'hzzzz', 'h222a', 'h222b'))
    return dict(combinations=512, cases=rows, unknown_inputs_refused=4, fixed_task_and_tied_minima=True)


@lru_cache(None)
def expectation_checks():
    text = 'r zscope[a] c.r zdifficulty[a a] c.r ztruth[a a d] c.r zrank[a '+PREDICATE+' a a a a d] c.r zperson[] a.r zanchor[] d.r zobserver[] a.r ztask[] a.'
    text += 'd zpredicate[person a task a] e[b point[k ztruth[v person v task v point]]].'
    text += 'q[k r2ho[k zobserver[] k zperson[] r[p zpredicate] p zscope k zanchor[] p zrank]].'
    text += 'q[k r2hq[k zobserver[] k zperson[] r[p zpredicate] k ztask[] p zscope p zdifficulty k zanchor[] p zrank]].'
    doc = fixture(['r2hq'], text)
    def model(edges, tasks=TASKS, levels=(0, 1, 2), variant='baseline'):
        values = unknowns(doc)
        values.update(zscope=lambda t: t in tasks, zdifficulty=lambda a, b: a in tasks and b in tasks and levels[tasks.index(a)] <= levels[tasks.index(b)],
            zperson=lambda: 'person', zanchor=lambda: 'anchor', zobserver=lambda: 'author', ztask=lambda: 'topic',
            zrank=lambda observer, pred, a, t, b, u, s: (observer, symbol(pred), a, b, s) == (
                'second' if variant == 'wrong_observer' else 'author', 'r2hn' if variant == 'wrong_predicate' else 'zpredicate',
                'second' if variant == 'wrong_left_actor' else 'person', 'second' if variant == 'wrong_right_actor' else 'person',
                'two' if variant == 'wrong_context' else 'anchor') and (t, u) in edges)
        return values
    for bits in product((False, True), repeat=9):
        edges = {p for p, flag in zip(product(TASKS, repeat=2), bits) if flag}
        valid = all((a, a) in edges for a in TASKS) and all(not ((a, b) in edges and (b, c) in edges) or (a, c) in edges for a, b, c in product(TASKS, repeat=3))
        strict = all((b, 'topic') in edges and ('topic', b) not in edges for b in TASKS[1:])
        assert evaluate(doc, model(edges), PEOPLE, SCENES, True) == [valid, valid and strict], bits
    edges = {(a, b) for a, b in product(TASKS, repeat=2) if TASKS.index(a) >= TASKS.index(b)}
    rows = {}
    for name in ('baseline', 'wrong_observer', 'wrong_predicate', 'wrong_left_actor', 'wrong_right_actor', 'wrong_context'):
        actual = evaluate(doc, model(edges, variant=name), PEOPLE, SCENES, True)
        assert actual == [name == 'baseline']*2, (name, actual); rows[name] = actual
    for name, levels, expected in [('tied_minima', (0, 0, 1), True), ('all_tied', (0, 0, 0), False)]:
        # Values involving a tied minimum do not constrain this background.
        # The finite evaluator is eager, so this is value independence, not lazy lookup.
        probe = deepcopy(doc); probe['statements'] = doc['statements'][1:]
        values = model(edges, levels=levels)
        if name == 'tied_minima':
            tied_pairs = [pair for pair in product(TASKS, repeat=2) if 'harder' in pair]
            for bits in product((False, True), repeat=len(tied_pairs)):
                changed = {pair for pair in edges if 'harder' not in pair} | {pair for pair, flag in zip(tied_pairs, bits) if flag}
                assert evaluate(probe, model(changed, levels=levels), PEOPLE, SCENES, True) == [True]
        actual = evaluate(probe, values, PEOPLE, SCENES, True); assert actual == [expected]; rows[name] = actual
    refuse(doc, model(edges), ('zscope', 'zdifficulty', 'zrank'))
    return dict(combinations=512, tied_comparison_combinations=32, cases=rows, unknown_inputs_refused=3,
        predicate_not_executed=True, explicit_actor_task_and_context_bindings=True,
        all_strict_alternatives_checked=True, tied_minimum_not_an_alternative=True,
        nontransitivity_ties_reversal_and_incomparability_distinguished=True)


def boundary_document():
    roots = ['r2hz', 'rsx', 'rsy', 'rsw', 'wh']
    suffix = ''.join('q[k '+operation+'['+package+' k wh[]]].' for package in ('k r2hz[]', 'k rsw[k r2hz[]]') for operation in ('rsx', 'rsy'))
    doc = fixture(roots, suffix)
    probes = parse('p:r zante[a d] c.r zcausal[a d] c.d r2gt[person a] e[b point[k zante[v person v point]]].d r2hj[person a] e[b point[k zcausal[v person v point]]].')
    replacements = {d['name']: d for d in probes['declarations'][2:]}
    doc['declarations'] = probes['declarations'][:2] + [deepcopy(replacements.get(d['name'], d)) for d in doc['declarations']]
    doc['declarations'] = closure(doc, roots)
    return parse(format_graph(doc, 'compact'))


def boundary_values(doc, causal=(True, True), background=(True, True), variant='baseline'):
    values = unknowns(doc); persons = ('person', 'second')
    def person_task(p): return 'topic' if p == 'person' else 'harder'
    def task_scope(p): return ('topic', 'hardest') if p == 'person' else ('harder', 'hardest')
    values.update(wh=lambda: 'anchor', wa=lambda: 'author', hzzq=lambda: 'node', aa=lambda p: p in persons,
        hzzn=lambda n, p, s: variant != 'empty_people' and (n, s) == ('node', 'anchor') and p in persons,
        hzzzz=lambda p, sc: person_task(p),
        h222a=lambda p, sc, t: p in persons and sc == 'anchor' and t in task_scope(p),
        h222b=lambda p, a, b, s: p in persons and s in ('one', 'two') and a in task_scope(p) and b in task_scope(p) and (a == b or b == 'hardest'),
        h222c=lambda observer, pred, a, t, b, u, s: a in persons and (observer, symbol(pred), b, s) == ('author', 'r2hn', a, 'one') and t in task_scope(a) and u in task_scope(a) and (t == u or background[persons.index(a)] and t == 'hardest'),
        hzzzy=lambda p, sc, s: variant != 'empty_cases' and p in persons and sc == 'anchor' and s in ('one', 'two'),
        zante=lambda p, s: variant != 'no_departure' and p in persons and s == 'one',
        zcausal=lambda p, s: p in persons and s == ('two' if variant == 'wrong_case' else 'one') and causal[persons.index(p)])
    if variant == 'wrong_task': values['hzzzz'] = lambda p, sc: 'hardest'
    if variant == 'wrong_anchor': values['wh'] = lambda: 'two'
    return values


@lru_cache(None)
def package_checks():
    doc = boundary_document()
    for bits in product((False, True), repeat=4):
        expected = [all(bits[:2]), all(bits[2:]), not all(bits[:2]), all(bits[2:])]
        assert evaluate(doc, boundary_values(doc, bits[:2], bits[2:]), PEOPLE, SCENES, True) == expected, bits
    rows = {}
    for name, expected in [('baseline', [True, True, False, True]), ('empty_people', [False, False, True, False]),
        ('empty_cases', [False, False, True, False]), ('no_departure', [False, False, True, False]),
        ('wrong_case', [False, True, True, True]), ('wrong_task', [False, False, True, False]), ('wrong_anchor', [False, False, True, False])]:
        actual = evaluate(doc, boundary_values(doc, variant=name), PEOPLE, SCENES, True)
        assert actual == expected, (name, actual); rows[name] = actual
    probe = deepcopy(doc); probe['statements'] = [doc['statements'][1]]
    values = boundary_values(doc); values['zcausal'] = unknown
    assert evaluate(probe, values, PEOPLE, SCENES, True) == [True]
    refuse(doc, boundary_values(doc), ('h222a', 'h222b', 'h222c', 'hzzzy', 'hzzn', 'zante', 'zcausal'))
    return dict(combinations=16, cases=rows, unknown_inputs_refused=7, content_boundary_test=True,
        native_minimum_and_expectation_executed=True, each_person_keeps_own_fixed_task=True,
        background_does_not_execute_causal_consequence=True, negation_preserves_background=True)


@lru_cache(None)
def task_content_checks():
    doc = fixture(['r2hn', 'r2hb'], 'r zperson[] a.r zanchor[] d.r ztopic[] a.'+
        'q[t[k r2hn[k zperson[] k ztopic[]]][k zanchor[]]].q[t[k r2hb[k zperson[]]][k zanchor[]]].')
    rows = {}
    for name in ('baseline', 'no_actual', 'guided_actual', 'wrong_actual_faculty', 'reliable', 'different_argument'):
        values = judgment_values(doc, name, responses=(True, name == 'reliable'))
        if name == 'different_argument': values['ztopic'] = lambda: 'other'
        expected = [False, True] if name == 'different_argument' else [name == 'baseline']*2
        actual = evaluate(doc, values, JUDGMENT_PEOPLE, JUDGMENT_SCENES, True)
        assert actual == expected, (name, actual); rows[name] = actual
    return dict(cases=rows, explicit_task_matches_fixed_task_content=True, different_task_not_substituted=True)


@lru_cache(None)
def quotation_checks():
    doc = fixture(['r2hz', 'rsu', 'rsv', 'rsw'],
        'q[e[k rsu[k r2hz[]]][r c[k r2hx[]]]].q[e[k rsv[k r2hz[]]][r c[k r2hy[]]]].'+
        'q[e[k rsv[k rsw[k r2hz[]]]][r c[k r2hy[]]]].')
    assert evaluate(doc, unknowns(doc), PEOPLE, SCENES, True) == [True]*3
    return dict(closed_package_without_world_evaluation=True, exact_foreground_and_background_quotes=True)


@lru_cache(None)
def native_checks():
    doc = fixture(['r2hv', 'r2hw', 'r2hm'], '''r zperson[] a.r zanchor[] d.r zpast[] d.r zcopy[] a.
q[t[k r2hv[k zperson[]]][k zanchor[]]].q[t[k r2hw[k zperson[]]][k zanchor[]]].q[t[k r2hm[k zperson[]]][k zanchor[]]].q[k r2he[k zperson[] k zcopy[] k zpast[]]].''')
    people = JUDGMENT_PEOPLE + ('process', 'source', 'author', 'harder', 'hardest'); scenes = ('before', 'anchor', 'one', 'two')
    rows = {}
    for variant in ('baseline', 'familiar', 'no_cause', 'adoption_absent', 'wrong_description', 'no_actual', 'no_departure', 'reliable', 'missing_history', 'not_minimum', 'no_expectation', 'wrong_actor', 'wrong_predicate', 'empty_scope', 'all_tied'):
        values = judgment_values(doc, variant, responses=(True, variant == 'reliable'))
        old_fa, old_dg = values['fa'], values['dg']
        values.update(h2d=lambda: 'source', wa=lambda: 'author', zpast=lambda: 'before', zcopy=lambda: 'copy',
            fa=lambda p, j, s: old_fa(p, j, s) or (p, j, s) == ('person', 'copy', 'before'),
            hzzzm=lambda n, a, d, p, o, s: (n, a, symbol(d), p, o, s) == ('source', 'author', 'r2fh', 'person', 'topic', 'anchor'),
            hzzzo=lambda sc, o, p, a, s: (sc, o, p) == ('anchor', 'topic', 'person') and (a, s) in (('before', 'one'), ('anchor', 'two')),
            hzzzp=lambda *args: True, hzzzq=lambda *args: True, hzzzr=lambda *args: False,
            hx2=lambda p, o, act, s: (p, o, act, s) == ('person', 'topic', 'act', 'one'), hz2=lambda *args: False,
            dg=lambda act, s: old_dg(act, s) or (act, s) in (('act', 'one'), ('copy', 'before')) or variant != 'no_departure' and (act, s) == ('process', 'anchor'),
            hzzzs=lambda p, end, t: (p, end) == ('person', 'anchor') and t in ('before', 'anchor') and not (variant == 'missing_history' and t == 'anchor'),
            ic=lambda a, b, s: (a, b, s) == ('before', 'anchor', 'anchor'),
            ag=lambda proc, a, b: (proc, a, b) == ('process', 'before', 'anchor'),
            la=lambda p, proc, a, b: (p, proc, a, b) == ('person', 'process', 'before', 'anchor'),
            df=lambda p, proc, s: (p, proc, s) == ('person', 'process', 'anchor'),
            hzid=lambda p, proc, old, new, a, b: (p, proc, symbol(old), symbol(new), a, b) == ('person', 'process', 'r2gp', 'r2gq', 'before', 'anchor'),
            g3=lambda proc, p, d, s: (proc, p, symbol(d), s) == ('process', 'person', 'r2gq', 'anchor'),
            hzzzy=lambda p, sc, s: (p, sc, s) == ('person', 'anchor', 'anchor'),
            h3e=lambda p, event, d, s: (p, event, symbol(d), s) == ('person', 'copy', 'r2hf', 'before'),
            h3g=lambda event, p, d, a, b: (event, p, symbol(d), a, b) == ('copy', 'person', 'r2hf', 'before', 'anchor'),
            h3f=lambda p, d, s: variant == 'familiar' and (p, symbol(d), s) == ('person', 'r2hf', 'anchor'),
            hzie=lambda p, f, q, e, s: variant != 'no_cause' and (p, symbol(f), q, symbol(e), s) == (
                'person', 'r2hf' if variant == 'wrong_description' else 'r2hh', 'person', 'r2hb', 'anchor'),
            ea=lambda *args: variant != 'adoption_absent')
        tasks = ('topic', 'harder', 'hardest')
        levels = (1, 0, 2) if variant == 'not_minimum' else (0, 0, 0) if variant == 'all_tied' else (0, 1, 2)
        values.update(
            h222a=lambda p, sc, t: variant != 'empty_scope' and (p, sc) == ('person', 'anchor') and t in tasks,
            h222b=lambda p, a, b, s: (p, s) == ('person', 'anchor') and a in tasks and b in tasks and levels[tasks.index(a)] <= levels[tasks.index(b)],
            h222c=lambda observer, pred, a, t, b, u, s: (observer, symbol(pred), a, b, s) == (
                'author', 'r2hb' if variant == 'wrong_predicate' else 'r2hn', 'person',
                'other' if variant == 'wrong_actor' else 'person', 'anchor') and t in tasks and u in tasks and (
                    t == u or variant != 'no_expectation' and tasks.index(t) > tasks.index(u)))
        actual = evaluate(doc, values, people, scenes, True)
        old_result = variant not in ('familiar', 'no_cause', 'wrong_description', 'no_actual', 'no_departure', 'reliable', 'missing_history')
        expected = [old_result and variant not in ('not_minimum', 'empty_scope'), variant not in ('no_departure', 'missing_history', 'not_minimum', 'no_expectation', 'wrong_actor', 'wrong_predicate', 'empty_scope', 'all_tied'), old_result, True]
        assert actual == expected, (variant, actual, expected); rows[variant] = actual
    return dict(cases=rows, native_departure_cause_minimum_and_expectation_executed=True,
        prior_cause_effect_description_unchanged=True,
        same_world=True, past_experience_activity_witness_executed=True,
        explanation_adoption_not_required=True, prior_experience_can_coexist_with_unfamiliarity=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    phrase = 'auch über den schmalesten Graben'
    start = unit['text'].index(phrase, 474); end = start + len(phrase)
    current = catalog(); dependencies = [d['name'] for d in closure(current.document, ['r2hz'])]
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, *PRIOR, *(p for p, _ in SENTENCES)}
    return dict(status='unasserted_minimum_challenge_and_bound_expectation_candidate', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, end], text=unit['text'][start:end]),
        candidate_definitions=list(MEANINGS), candidate_dependency_sha256=canonical_digest([current.entries[n] for n in dependencies]),
        candidate_dependencies=dependencies, preserved_authored_selection=selection_binding(current, [13, 53]),
        decision='固定課題の最小性を前景に加え、同じ人物と閉じた内容述語を束縛した期待比較を独立した背景へ構成する。nur・dennochと身体描写との対応、本文への統合は未完。',
        interpretation_limits=LIMITS, revised_statement_indices=[],
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
            use='最小幅の溝へのauchを照合。最小の困難に対する尺度期待としての対象側の読みは候補であり、身体描写との同一性を証明したものではない。')],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-16] == old.document['declarations']
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert len(new.document['statements']) == 54 and old.document['statements'] == new.document['statements']
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        record = read(path); validate_hashes(ROOT, record['source_sha256'])
        indices = [s['index'] for s in record['selection']['statements']]
        assert record['selection'] == selection_binding(old, indices) == selection_binding(new, indices)
    for path, indices in SENTENCES:
        record = read(path); validate_hashes(ROOT, record['source_sha256'])
        assert record['selection'] == selection_binding(new, indices)
    for path in PRIOR: validate_hashes(ROOT, read(path)['source_sha256'])
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(selection_binding(new, list(range(54)))['dependencies'])
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert read(AUDIT) == reading()
    return dict(added_definitions=13, added_primitives=3, authored_statements=54, preserved_statements=54,
        revised_statement_indices=[], preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=408, candidate_not_asserted=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items(): write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('minimum', minimum_checks), ('expectation', expectation_checks), ('package', package_checks),
                     ('task_content', task_content_checks), ('native', native_checks), ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_minimum_challenge.py', 'scripts/check_minimum_challenge.py',
        'scripts/register_minimum_challenge.py', 'tests/test_minimum_challenge.py',
        'scripts/check_uncertain_judgment.py', 'scripts/check_abandoned_reliance.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    for path in PRIOR: paths.update(read(path)['source_sha256'])
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='minimum_challenge_and_bound_expectation_candidate_checked', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_covered_characters=0, new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
