"""Exercise conditional continuations and their same-act causal content."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_conditioned_persistence import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v99.json'
AUDIT = 'data/conditioned-persistence-reading-v1.json'
REPORT = 'reports/conditioned-persistence-v1.json'
DOC = 'docs/conditioned-persistence-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
FIRST = 'data/nature-sentence-reading-v1.json'
SECOND = 'data/confirmed-incapacity-reading-v1.json'
PRIOR = 'reports/instrumental-misuse-v1.json'
PEOPLE = ('person', 'object', 'faculty', 'act', 'other', 'judgment', 'method')
SCENES = ('anchor', 'keep', 'stop', 'first', 'last', 'released', 'trial', 'trial2', 'trial3', 'success', 'failure')
EXTRA = 'r zobject[] a.r zperson[] a.r zanchor[] d.r zcandidates[d d] c.r zcontinuations[d d d] c.'
ARGS = 'k zobject[] k zperson[] k zanchor[] p zcandidates p zcontinuations'


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
    values.update(zobject=lambda: 'object', zperson=lambda: 'person', zanchor=lambda: 'anchor')
    return values


@lru_cache(None)
def generic_checks():
    doc = fixture('r2eu', EXTRA + '''r zcondition[d] c.r zresult[d] c.
q[k r2eu[b point[k zcondition[v point]] b point[k zresult[v point]] k zanchor[] p zcandidates p zcontinuations]].''')
    scenes = ('anchor', 'left', 'right', 'l1', 'l2', 'r1', 'r2')
    points = ('l1', 'l2', 'r1', 'r2')
    def model(bits):
        left, right, *rest = bits; conditions, results = rest[:4], rest[4:]
        values = initial(doc)
        values.update(zcandidates=lambda a, b: a == 'anchor' and (b == 'left' and left or b == 'right' and right),
            zcontinuations=lambda a, b, p: a == 'anchor' and (b == 'left' and p in points[:2] or b == 'right' and p in points[2:]),
            zcondition=lambda p: p in points and conditions[points.index(p)],
            zresult=lambda p: p in points and results[points.index(p)])
        return values
    for bits in product((False, True), repeat=10):
        left, right, *rest = bits; conditions, results = rest[:4], rest[4:]
        eligible = (left and all(conditions[:2]), right and all(conditions[2:]))
        want = any(eligible) and all(not e or all(results[2*i:2*i+2]) for i, e in enumerate(eligible))
        actual = evaluate(doc, model(bits), ('person',), scenes, True)
        assert actual == [want], (bits, actual)
    variants = {}
    base = (True, True, True, True, False, False, True, True, False, False)
    for name in ('release_can_succeed', 'no_current_result', 'missing_future', 'wrong_anchor', 'wrong_branch', 'late_failure', 'prefix_not_guaranteed'):
        values = model(base)
        if name == 'missing_future': values['zcontinuations'] = lambda a, b, p: a == 'anchor' and b == 'left' and p in points[:2]
        if name == 'wrong_anchor': values['zcontinuations'] = lambda a, b, p: a == 'elsewhere' and p in points
        if name == 'wrong_branch': values['zcontinuations'] = lambda a, b, p: a == 'anchor' and b == 'outside' and p in points
        if name == 'late_failure': values['zresult'] = lambda p: p == 'l1'
        if name == 'prefix_not_guaranteed': values['zcondition'] = lambda p: p in ('l1', 'l2', 'r1')
        actual = evaluate(doc, values, ('person',), scenes, True)
        assert actual == [name in ('release_can_succeed', 'no_current_result', 'prefix_not_guaranteed')], (name, actual)
        variants[name] = actual
    for name in ('zcandidates', 'zcontinuations', 'zcondition', 'zresult'):
        values = model(base); values[name] = unknown
        try: evaluate(doc, values, ('person',), scenes, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=1024, contrasts=variants, unknown_inputs_refused=4,
        no_current_condition_or_result_required=True, empty_candidate_and_inapplicable_profiles_refused=True,
        branch_local_points_preserved=True, not_an_until_operator=True)


def source_values(doc, variant='baseline', boundary=False):
    values = initial(doc); points = ('first', 'last')
    values.update(
        zcandidates=lambda a, b: a == 'anchor' and b in ('keep', 'stop'),
        zcontinuations=lambda a, b, p: a == 'anchor' and (b == 'keep' and p in points or b == 'stop' and p == 'released'),
        hx2=lambda p, o, a, s: (p, o, a) == ('person', 'object', 'act') and s in points,
        fa=lambda p, j, s: variant == 'examined' and (p, j) == ('person', 'judgment') and s in points,
        fb=lambda j, o, s: (j, o) == ('judgment', 'object'),
        hz2=lambda j, a, s: (j, a) == ('judgment', 'act'),
        hh2=lambda f, p, s: (f, p) == ('faculty', 'person'),
        hi2=lambda p, f, a, s: (p, f, a) == ('person', 'faculty', 'other' if variant == 'split_use' else 'act') and s in points,
        hj2=lambda a, positive, s: not positive and a == ('other' if variant == 'split_use' else 'act') and s in points,
        dg=lambda a, s: a == 'act' and s in points,
        g3=lambda a, p, result, s: (a, p, symbol(result)) == (
            'other' if variant == 'cause_act' else 'act', 'other' if variant == 'cause_person' else 'person',
            'h26' if variant == 'cause_lifetime' else 'bf') and s in points and not (variant == 'missing_last_cause' and s == 'last'),
        zstate=lambda p, s: p == 'person' and s in points and not (variant == 'mature_last' and s == 'last'))
    if variant == 'missing_stop_future':
        values['zcontinuations'] = lambda a, b, p: (a, b) == ('anchor', 'keep') and p in points
    if variant == 'only_release': values['zcandidates'] = lambda a, b: (a, b) == ('anchor', 'stop')
    if boundary: return values
    # The full source closure executes the existing assessed current-capacity bf.
    trials = {'first': 'trial', 'last': 'trial2', 'released': 'trial3', 'anchor': 'trial3'}
    available = lambda p, m, s: (p, m) == ('person', 'method') and s in ('trial', 'trial2', 'trial3')
    values.update(aa=lambda p: p == 'person', ab=lambda f, p, s: (f, p) == ('faculty', 'person'),
        ac=lambda p, f, a, s: (p, f, a, s) == ('person', 'faculty', 'act', 'success'), ad=lambda *args: False,
        hzsc=lambda p, anchor, s: p == 'person' and trials.get(anchor) == s,
        hzsd=lambda p, anchor, s: p == 'person' and anchor in trials,
        hzse=lambda p, s: p == 'person' and s in trials.values(), hzsf=lambda *args: False,
        hzsg=lambda p, m, anchor, s: (p, m) == ('person', 'method') and anchor in trials,
        hzsh=lambda p, m, anchor, s: (p, m) == ('person', 'method') and anchor in trials,
        ae=available, af=lambda p, m, s, end: available(p, m, s) and end in ('success', 'failure'),
        ap=lambda p, m, s, end: available(p, m, s) and end == (
            'success' if s == 'trial3' or variant == 'mature_last' and s == 'trial2' else 'failure'))
    return values


@lru_cache(None)
def source_document(boundary):
    doc = fixture('r2ey bf r2ew', EXTRA + 'q[k r2ey[' + ARGS + ']].q[t[k bf[k zperson[]]][k zanchor[]]].q[t[k r2ew[k zobject[] k zperson[]]][k zanchor[]]].')
    if boundary:
        replacement = parse('p:r zstate[a d] c.d bf[person a] e[b point[k zstate[v person v point]]].')
        doc = deepcopy(doc)
        doc['declarations'] = [replacement['declarations'][0]] + [
            deepcopy(replacement['declarations'][1]) if d['name'] == 'bf' else d for d in doc['declarations']]
        doc['declarations'] = closure(doc, ['r2ey', 'bf', 'r2ew', 'zobject', 'zperson', 'zanchor', 'zcandidates', 'zcontinuations'])
    return parse(format_graph(doc, 'compact'))


@lru_cache(None)
def binding_checks():
    doc = source_document(True); rows = {}
    variants = ('baseline', 'cause_act', 'cause_person', 'cause_lifetime', 'missing_last_cause',
        'mature_last', 'split_use', 'examined', 'missing_stop_future', 'only_release')
    for name in variants:
        actual = evaluate(doc, source_values(doc, name, True), PEOPLE, SCENES, True)
        assert actual == [name == 'baseline', False, False], (name, actual)
        rows[name] = actual
    for name in ('hx2', 'fa', 'fb', 'hz2', 'hh2', 'hi2', 'hj2', 'dg', 'g3', 'zstate'):
        values = source_values(doc, boundary=True); values[name] = unknown
        try: evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(cases=rows, unknown_inputs_refused=10, bf_boundary_isolated=True,
        same_act_cause_required=True, causal_content_not_in_antecedent=True)


@lru_cache(None)
def native_checks():
    doc = source_document(False); rows = {}
    for name in ('baseline', 'mature_last', 'cause_act', 'missing_last_cause'):
        actual = evaluate(doc, source_values(doc, name), PEOPLE, SCENES, True)
        assert actual == [name == 'baseline', False, False], (name, actual)
        rows[name] = actual
    for name in ('hzsc', 'hzsh'):
        values = source_values(doc); values[name] = unknown
        try: evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    refused = fixture('r2ez', EXTRA + 'q[k r2ez[' + ARGS + ']].')
    try: evaluate(refused, source_values(refused), PEOPLE, SCENES, True)
    except ValueError as error: assert 'Cannot finitely quantify' in str(error) and 'description' in str(error), str(error)
    else: raise AssertionError('Finite replacement of the description domain accepted')
    return dict(cases=rows, unknown_inputs_refused=2, native_current_capacity_executed=True,
        native_conditionals_and_future_quantifiers_executed=True, whole_category_evaluation_explicitly_refused=True)


@lru_cache(None)
def reused_checks():
    current = catalog(); old = parent(); report = read(PRIOR); validate_hashes(ROOT, report['source_sha256'])
    assert current.document['statements'] == old.document['statements']
    assert current.document['declarations'][:-6] == old.document['declarations']
    assert all(current.entries[n] == entry for n, entry in old.entries.items())
    for path, indices in ((FIRST, [51]), (SECOND, [11, 12])):
        record = read(path); validate_hashes(ROOT, record['source_sha256'])
        assert record['decision'] == 'equivalent_under_stated_reading_for_this_sentence'
        assert record['selection'] == selection_binding(current, indices)
    return dict(report=PRIOR, every_inherited_declaration_and_meaning_preserved=True,
        finite_evidence_reused_without_claiming_new_execution=True, first_sentence_review_preserved=True,
        second_sentence_review_preserved=True, preserved_reviewed_sentence_characters=247,
        modal_and_persistence_definitions_unchanged=['rjm', 'rjo', 'h26', 'h2l', 'h2m'])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, FIRST, SECOND, PRIOR}
    return dict(status='unasserted_conditional_continuation_alternative', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[293, 473], text=unit['text'][293:473]),
        alignment=[], candidate_definitions=list(MEANINGS), selection=selection_binding(catalog(), [10, 52, 53]),
        decision='継続使用を条件とする作用を表せるようにした未採用候補。実際の残余生涯の結果と区別し、第三文の唯一の読みや全文一致は認定しない。',
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
            use='第三文の持続と、続く文の足枷を投げ捨てる仮定および脱出の記述を照合。条件付き候補を検討する根拠であり、唯一の読みの証明ではない。')],
        interpretation_limits=LIMITS, revised_statement_indices=[], preserved_statement_indices=list(range(54)),
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False, new_verified_sentence_characters=0,
        preserved_reviewed_sentence_characters=247, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert len(new.document['statements']) == 54 and new.document['statements'] == old.document['statements']
    assert set(new.entries) - set(old.entries) == set(MEANINGS)
    assert new.document['statements'][10]['body']['symbol'] == 'ho2'
    assert new.document['statements'][52]['body']['symbol'] == 'r2et'
    assert new.document['statements'][53]['body']['symbol'] == 'h3b'
    reviews = read(INDEX)['works']['kant-1784']['reviews']; assert len(reviews) == 12
    for path in reviews:
        review = read(path); validate_hashes(ROOT, review['source_sha256'])
        ids = [s['index'] for s in review['selection']['statements']]
        assert review['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    record = reading(); assert record == read(AUDIT); validate_hashes(ROOT, record['source_sha256'])
    assert not record['alignment']
    assert not set(MEANINGS) & set(record['selection']['dependencies'])
    assert 'h26' not in {d['name'] for d in closure(new.document, ['r2ey'])}
    return dict(new_definitions=6, new_primitives=0, preserved_statements=54, revised_statement_indices=[],
        authored_statements=54, preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=247, new_profile_not_asserted=True, no_new_covered_characters=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('binding', binding_checks), ('native', native_checks),
                     ('reused', reused_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | set(read(PRIOR)['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_conditioned_persistence.py', 'scripts/check_conditioned_persistence.py',
        'scripts/register_conditioned_persistence.py', 'tests/test_conditioned_persistence.py'}
    return dict(status='conditional_continuation_candidate_checked_not_author_claim', document=FULL, **results,
        alignment=[], whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=247, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
