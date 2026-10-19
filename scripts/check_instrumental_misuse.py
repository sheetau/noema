"""Check same-act binding without equating unexamined use and misuse."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_instrumental_misuse import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v98.json'
AUDIT = 'data/instrumental-misuse-reading-v1.json'
REPORT = 'reports/instrumental-misuse-v1.json'
DOC = 'docs/instrumental-misuse-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
FIRST = 'data/nature-sentence-reading-v1.json'
SECOND = 'data/confirmed-incapacity-reading-v1.json'
COMPONENTS = {'confirmed-incapacity': ['r2eo', 'r2em'], 'current-deprivation': ['bf'],
              'nature-sentence': ['h26', 'h2j', 'ho2', 'h3b']}
COVERAGE_REPORTS = ('reports/described-routines-v1.json', 'reports/reformulations-v1.json', 'reports/relational-fetters-v1.json')
PEOPLE = ('person', 'object', 'faculty', 'act', 'other', 'judgment', 'method')
SCENES = ('now', 'later', 'trial', 'trial2', 'success', 'failure', 'outside')
CONSTANTS = 'r zobject[] a.r zperson[] a.r zfaculty[] a.r zact[] a.r zpoint[] d.'
ARGS = 'k zobject[] k zperson[] k zfaculty[] k zact[] k zpoint[]'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, suffix):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots.split()), statements=[])
    return parse(format_graph(doc, 'compact') + suffix)


def initial(doc):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(zobject=lambda: 'object', zperson=lambda: 'person', zfaculty=lambda: 'faculty',
                  zact=lambda: 'act', zpoint=lambda: 'now')
    return values


@lru_cache(None)
def generic_checks():
    doc = fixture('r2ep', CONSTANTS + '''r zuse[a a a d] c.r zjudgments[a a d] c.r zmatters[a a d] c.r zexamines[a a d] c.
q[k r2ep[k zperson[] k zobject[] k zact[] k zpoint[] p zuse p zjudgments p zmatters p zexamines]].''')
    def model(bits=(True, True, True, True), variant='baseline'):
        values = initial(doc)
        def matches(actual, expected, prefix, labels):
            wanted = list(expected)
            for i, label in enumerate(labels):
                if variant == prefix + '_' + label: wanted[i] = 'outside' if label == 'point' else 'other'
            return list(actual) == wanted
        values.update(
            zuse=lambda p, o, a, s: bits[0] and matches((p, o, a, s), ('person', 'object', 'act', 'now'), 'use', ('person', 'object', 'act', 'point')),
            zjudgments=lambda p, j, s: bits[1] and matches((p, j, s), ('person', 'judgment', 'now'), 'judgment', ('person', 'judgment', 'point')),
            zmatters=lambda j, o, s: bits[2] and matches((j, o, s), ('judgment', 'object', 'now'), 'matter', ('judgment', 'object', 'point')),
            zexamines=lambda j, a, s: bits[3] and matches((j, a, s), ('judgment', 'act', 'now'), 'examination', ('judgment', 'act', 'point')))
        return values
    for bits in product((False, True), repeat=4):
        assert evaluate(doc, model(bits), PEOPLE, SCENES, True) == [bits[0] and not all(bits[1:])], bits
    contrasts = {}
    for prefix, fields in [('use', ('person', 'object', 'act', 'point')),
        ('judgment', ('person', 'judgment', 'point')), ('matter', ('judgment', 'object', 'point')),
        ('examination', ('judgment', 'act', 'point'))]:
        for field in fields:
            name = prefix + '_' + field
            actual = evaluate(doc, model(variant=name), PEOPLE, SCENES, True)
            assert actual == [prefix != 'use'], (name, actual)
            contrasts[name] = actual
    for name in ('zuse', 'zjudgments', 'zmatters', 'zexamines'):
        values = model(); values[name] = unknown
        try: evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=16, contrasts=contrasts, unknown_inputs_refused=4,
        no_template_or_fixed_arity_requirement=True, irrelevant_judgment_not_counted=True)


@lru_cache(None)
def body_document(boundary):
    doc = fixture('r2eq', CONSTANTS + 'q[k r2eq[' + ARGS + ']].')
    if boundary:
        replacement = parse('p:r zlasting[a d] c.d h26[person a] e[b point[k zlasting[v person v point]]].')
        doc = deepcopy(doc)
        doc['declarations'] = [replacement['declarations'][0]] + [
            deepcopy(replacement['declarations'][1]) if d['name'] == 'h26' else d for d in doc['declarations']]
        doc['declarations'] = closure(doc, ['r2eq', 'zobject', 'zperson', 'zfaculty', 'zact', 'zpoint'])
    return parse(format_graph(doc, 'compact'))


def body_values(doc, bits=(True, False, True, True, True, True), variant='baseline'):
    used, reviewed, misused, occurs, caused, persists = bits
    values = initial(doc)
    def matches(actual, expected, prefix, labels):
        wanted = list(expected)
        for i, label in enumerate(labels):
            if variant == prefix + '_' + label: wanted[i] = 'outside' if label == 'point' else 'other'
        return list(actual) == wanted
    values.update(
        hx2=lambda p, o, a, s: used and matches((p, o, a, s), ('person', 'object', 'act', 'now'), 'use', ('person', 'object', 'act', 'point')),
        fa=lambda p, j, s: reviewed and (p, j, s) == ('person', 'judgment', 'now'),
        fb=lambda j, o, s: (j, o, s) == ('judgment', 'object', 'now'),
        hz2=lambda j, a, s: (j, a, s) == ('judgment', 'act', 'now'),
        hh2=lambda f, p, s: matches((f, p, s), ('faculty', 'person', 'now'), 'natural', ('faculty', 'person', 'point')),
        hi2=lambda p, f, a, s: matches((p, f, a, s), ('person', 'faculty', 'act', 'now'), 'facultyuse', ('person', 'faculty', 'act', 'point')),
        hj2=lambda a, positive, s: (variant in ('also_positive', 'only_positive') if positive else misused and variant != 'only_positive') and
            matches((a, s), ('act', 'now'), 'appraisal', ('act', 'point')),
        dg=lambda a, s: occurs and matches((a, s), ('act', 'now'), 'occurrence', ('act', 'point')),
        g3=lambda a, p, result, s: caused and symbol(result) == ('bf' if variant == 'cause_result' else 'h26') and
            matches((a, p, s), ('act', 'person', 'now'), 'cause', ('act', 'person', 'point')),
        zlasting=lambda p, s: persists and matches((p, s), ('person', 'now'), 'result', ('person', 'point')))
    return values


@lru_cache(None)
def binding_checks():
    doc = body_document(True); rows = []
    for bits in product((False, True), repeat=6):
        actual = evaluate(doc, body_values(doc, bits), PEOPLE, SCENES, True)
        assert actual == [bits[0] and not bits[1] and all(bits[2:])], (bits, actual)
        rows.append(dict(bits=bits, values=actual))
    variants = ['baseline', 'only_positive', 'also_positive', 'cause_result']
    for prefix, fields in [('use', ('person', 'object', 'act', 'point')), ('natural', ('faculty', 'person', 'point')),
        ('facultyuse', ('person', 'faculty', 'act', 'point')), ('appraisal', ('act', 'point')),
        ('occurrence', ('act', 'point')), ('cause', ('act', 'person', 'point')), ('result', ('person', 'point'))]:
        variants.extend(prefix + '_' + field for field in fields)
    contrasts = {}
    for name in variants:
        actual = evaluate(doc, body_values(doc, variant=name), PEOPLE, SCENES, True)
        assert actual == [name in ('baseline', 'also_positive')], (name, actual)
        contrasts[name] = actual
    split = deepcopy(doc)
    split['statements'] = parse('p:r zobject[] a.r zperson[] a.r zfaculty[] a.r zpoint[] d.r zprobe[a a a a d] c.' +
        'q[g act a[k zprobe[k zobject[] k zperson[] k zfaculty[] v act k zpoint[]]]].')['statements']
    split['statements'][0]['body']['body']['symbol'] = 'r2eq'
    values = body_values(split)
    values.update(hi2=lambda p, f, a, s: (p, f, a, s) == ('person', 'faculty', 'other', 'now'),
        hj2=lambda a, positive, s: not positive and (a, s) == ('other', 'now'),
        dg=lambda a, s: (a, s) == ('other', 'now'),
        g3=lambda a, p, result, s: (a, p, symbol(result), s) == ('other', 'person', 'h26', 'now'))
    assert evaluate(split, values, PEOPLE, SCENES, True) == [False]
    for name in ('hx2', 'fa', 'fb', 'hz2', 'hh2', 'hi2', 'hj2', 'dg', 'g3', 'zlasting'):
        values = body_values(doc); values[name] = unknown
        try: evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=10, split_activities_refused=True,
        persistence_boundary_isolated=True, not_a_native_persistence_test=True)


def native_values(doc, variant='baseline'):
    values = body_values(doc, variant=variant)
    history = ('now', 'later')
    available = lambda p, m, s: (p, m) == ('person', 'method') and s in ('trial', 'trial2')
    values.update(aa=lambda p: p == 'person', ab=lambda f, p, s: (f, p) == ('faculty', 'person'),
        ac=lambda p, f, a, s: (p, f, a, s) == ('person', 'faculty', 'act', 'success'), ad=lambda *args: False,
        ia=lambda p, anchor, s: (p, anchor) == ('person', 'now') and s in history,
        ib=lambda p, anchor, s: (p, anchor) == ('person', 'now') and s in history,
        ic=lambda a, b, anchor: anchor == 'now' and (a, b) == ('now', 'later'),
        hzsc=lambda p, anchor, s: p == 'person' and (anchor, s) in (('now', 'trial'), ('later', 'trial2')),
        hzsd=lambda p, anchor, s: p == 'person' and anchor in history,
        hzse=lambda p, s: p == 'person' and s in ('trial', 'trial2'),
        hzsf=lambda *args: False,
        hzsg=lambda p, m, anchor, s: (p, m) == ('person', 'method') and anchor in history,
        hzsh=lambda p, m, anchor, s: p == 'person' and anchor in history and variant != 'missing_assessment',
        ae=available, af=lambda p, m, s, end: available(p, m, s) and end in ('success', 'failure'),
        ap=lambda p, m, s, end: available(p, m, s) and end == ('success' if variant == 'mature_later' and s == 'trial2' else 'failure'))
    return values


@lru_cache(None)
def native_checks():
    doc = body_document(False); rows = {}
    for name in ('baseline', 'mature_later', 'missing_assessment', 'cause_act'):
        actual = evaluate(doc, native_values(doc, name), PEOPLE, SCENES, True)
        assert actual == [name == 'baseline'], (name, actual)
        rows[name] = actual
    for name in ('hzsc', 'hzsh'):
        values = native_values(doc); values[name] = unknown
        try: evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(cases=rows, unknown_inputs_refused=2, native_h26_and_current_capacity_executed=True,
        bounded_profile_not_proof_of_perpetuity=True)


@lru_cache(None)
def presentation_checks():
    doc = fixture('r2et', 'q[k r2et[]].'); rows = {}
    for variant in ('baseline', 'node', 'author', 'target', 'depiction', 'context', 'obsolete_target', 'reversed'):
        wanted = ['node', 'author', 'r2es', 'h2b', 'now']
        if variant in ('node', 'author', 'target', 'depiction', 'context'):
            wanted[('node', 'author', 'target', 'depiction', 'context').index(variant)] = 'outside' if variant == 'context' else 'other'
        if variant == 'obsolete_target': wanted[2] = 'h2a'
        if variant == 'reversed': wanted[2:4] = ['h2b', 'r2es']
        values = initial(doc); values.update(h2d=lambda: 'node', wa=lambda: 'author', wh=lambda: 'now',
            rbt=lambda n, a, target, depiction, s: [n, a, symbol(target), symbol(depiction), s] == wanted)
        actual = evaluate(doc, values, PEOPLE + ('node', 'author'), SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    values['rbt'] = unknown
    try: evaluate(doc, values, PEOPLE + ('node', 'author'), SCENES, True)
    except ValueError as error: assert 'Unknown' in str(error)
    else: raise AssertionError('Unknown presentation accepted')
    refused = fixture('r2er', CONSTANTS + 'q[t[k r2er[k zobject[] k zperson[]]][k zpoint[]]].')
    try: evaluate(refused, initial(refused), PEOPLE, SCENES, True)
    except ValueError as error: assert 'Cannot finitely quantify' in str(error) and 'description' in str(error), str(error)
    else: raise AssertionError('Finite substitutes for the description domain accepted')
    return dict(cases=rows, unknown_inputs_refused=1, world_contents_not_executed_by_attribution=True,
        whole_category_evaluation_explicitly_refused=True)


@lru_cache(None)
def reused_checks():
    current = catalog(); rows = {}
    for name, roots in COMPONENTS.items():
        path = 'reports/' + name + '-v1.json'; report = read(path); validate_hashes(ROOT, report['source_sha256'])
        old = parse((ROOT / report['document']).read_text(encoding='utf-8'))
        assert closure(old, roots) == closure(current.document, roots)
        dependencies = {d['name'] for d in closure(current.document, roots)}
        rebound = [n for n in dependencies if current.entries[n]['meaning_basis'] not in report['source_sha256']]
        historical = load_catalog(ROOT, 'data/' + name + '-basis-v1.json') if rebound else None
        if historical:
            assert historical.document == old
            assert all(report['source_sha256'][p] == h for p, h in historical.source_sha256.items())
        for n in dependencies:
            basis = current.entries[n]['meaning_basis']
            if n in rebound:
                assert historical.entries[n].keys() == current.entries[n].keys()
                provenance = {'meaning_basis', 'declaration_document'}
                assert {k: v for k, v in historical.entries[n].items() if k not in provenance} == {
                    k: v for k, v in current.entries[n].items() if k not in provenance}, (path, n)
            else:
                assert report['source_sha256'][basis] == current.source_sha256[basis], (path, n)
        rows[path] = dict(roots=roots, dependency_count=len(dependencies), declarations_and_meaning_conventions_unchanged=True,
            identical_conventions_reissued_under_new_basis=sorted(rebound))
    first = read(FIRST); validate_hashes(ROOT, first['source_sha256'])
    assert first['decision'] == 'equivalent_under_stated_reading_for_this_sentence'
    assert first['selection'] == selection_binding(current, [51])
    second = read(SECOND); validate_hashes(ROOT, second['source_sha256'])
    assert second['decision'] == 'equivalent_under_stated_reading_for_this_sentence'
    assert second['selection'] == selection_binding(current, [11, 12])
    return dict(reports=rows, finite_evidence_reused_without_claiming_new_execution=True,
        first_sentence_review_preserved=True, second_sentence_review_preserved=True,
        preserved_reviewed_sentence_characters=247)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, FIRST, SECOND}
    paths.update(COVERAGE_REPORTS)
    paths.update('reports/' + name + '-v1.json' for name in COMPONENTS)
    spans = [(316, 344, ['r2ep', 'r2eq', 'r2er']), (345, 416, ['r2eq', 'r2er', 'ho2']),
             (427, 438, ['r2es', 'r2et', 'h2b'])]
    return dict(status='same_use_activity_connection_candidate', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[293, 473], text=unit['text'][293:473]),
        alignment=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[a, b], text=unit['text'][a:b],
            definitions=roots, status='explicit_interpretive_annotation') for a, b, roots in spans],
        selection=selection_binding(catalog(), [10, 52]),
        decision='機械的な表現使用・自然的能力の誤用・結果生成を同じ活動へ接続する部分候補。第三文全体の意味一致は未確認。',
        references=[
            dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
                use='第三文の機械的道具という同格、能力の使用から誤用への言い直し、足枷の描写を照合。'),
            dict(url='https://www.duden.de/rechtschreibung/immerwaehrend', title='Duden immerwährend', accessed='2026-10-20',
                use='持続を表す語の比較資料。現代の説明から1784年の唯一の持続範囲や無期限性を確定せず、現行h26との同義性も認定しない。')],
        interpretation_limits=LIMITS, revised_statement_indices=[52], preserved_statement_indices=[10, 53],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False, new_verified_sentence_characters=0,
        preserved_reviewed_sentence_characters=247, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-5] == old.document['declarations']
    assert len(new.document['statements']) == len(old.document['statements']) == 54
    assert [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b] == [52]
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS)
    assert new.document['statements'][10]['body']['symbol'] == 'ho2'
    assert new.document['statements'][53]['body']['symbol'] == 'h3b'
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        review = read(path); validate_hashes(ROOT, review['source_sha256'])
        ids = [s['index'] for s in review['selection']['statements']]
        assert 52 not in ids and review['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    assert len(read(INDEX)['works']['kant-1784']['reviews']) == 12
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    record = reading(); assert record == read(AUDIT); validate_hashes(ROOT, record['source_sha256'])
    assert sum(not c.isspace() for c in record['source']['text']) == 161
    from scripts.audit_written_progress_extended import collect_alignment
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    covered = set()
    for path in COVERAGE_REPORTS:
        historical = read(path); validate_hashes(ROOT, historical['source_sha256'])
        records = collect_alignment(historical, {unit['id']: unit}, set(new.entries), path)
        covered.update(i for row in records for a, b in [row['range']] for i in range(a, b))
    for row in record['alignment']:
        a, b = row['range']
        assert set(range(a, b)) <= covered
        assert set(row['definitions']) <= set(record['selection']['dependencies'])
    assert all(d['name'] not in ('rbo', 'hw2', 'hy2') for d in closure(new.document, ['r2ep', 'r2eq']))
    return dict(new_definitions=5, new_primitives=0, preserved_statements=53, revised_statement_indices=[52],
        authored_statements=54, preserved_reformulation_index=10, preserved_conditional_index=53,
        preserved_review_selections=12, reviewed_nonblank_characters=2212, preserved_reviewed_sentence_characters=247,
        whole_third_sentence_nonblank_characters=161, fixed_coverage_reports=3, no_new_covered_characters=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('binding', binding_checks), ('native', native_checks),
                     ('presentation', presentation_checks), ('reused', reused_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_instrumental_misuse.py', 'scripts/check_instrumental_misuse.py', 'scripts/register_instrumental_misuse.py',
        'tests/test_instrumental_misuse.py', 'scripts/compose_grounded_step.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/audit_written_progress_extended.py', 'noema/constructed.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    for name in COMPONENTS: paths.update(read('reports/' + name + '-v1.json')['source_sha256'])
    for path in COVERAGE_REPORTS: paths.update(read(path)['source_sha256'])
    return dict(status='same_use_activity_connection_candidate_checked', document=FULL, **results,
        alignment=record['alignment'], whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=247, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
