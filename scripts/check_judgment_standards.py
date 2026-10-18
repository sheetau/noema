"""Exercise standards, evidence states and native judgment/ability composition."""
import argparse
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts import check_qualified_judgment as prior
from scripts.compose_judgment_standards import (
    ROOT, FULL, CORE, LIBRARY, BASIS, TARGETS, MEANINGS, LIMITS, build, parent, closure,
)

REPORT = 'reports/judgment-standards-v1.json'
READING = 'data/judgment-standards-reading-v1.json'
INDEX, INVENTORY = prior.INDEX, prior.INVENTORY
DOMAIN = (*prior.DOMAIN, 'standard', 'criterionone', 'criteriontwo', 'otherfaculty')
EXTRA = '''
r zstandard[] a.r zresource[] a.r zjudgment[] a.
r zadopted[a d] c.r zmember[a a d] c.
r zapplicable[a a a a d d] c.r zevidence[a a a a c d d] c.
'''
CONCRETE = '''
d zadequate[p a m a j a c d s d] c[
 c[k hzvx[k zstandard[] p zadopted p zmember p zapplicable p zevidence]][v p v m v j v c v s]
].
'''
SARGS = 'k zstandard[] p zadopted p zmember p zapplicable p zevidence'
ARGS = 'k zstandard[] k zperson[] k zresource[] k zjudgment[] k zqualitycontext[] k zpoint[] p zadopted p zmember p zapplicable p ac p zevidence'
CODE = 'k hzvy[r[k zstandard[]] r[p zadopted] r[p zmember] r[p zapplicable] r[p zevidence]]'


def unknown(*args):
    raise ValueError('Unknown judgment standard input')


@lru_cache(None)
def prefix(roots, native=False):
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc, list(roots) + ['hzvx', 'hzvg'])
    doc['statements'] = []
    return (format_graph(doc, 'compact') + prior.prior.EXTRA + prior.REFERENCES + EXTRA +
        'r zsecure[a a a d d] c.' + (CONCRETE if native else 'r zadequate[a a a d d] c.'))


def evaluate(doc, model):
    return prior.evaluate(doc, model, domain=DOMAIN)


def model(states=((True, False), (True, False)), variant='', used=True, adopted=True):
    m = prior.model()
    keys = {
        'adopted': ['standard', 'now'],
        'member': ['standard', 'now'],
        'applicable': ['person', 'faculty', 'actone', 'now', 'good'],
        'evidence': ['person', 'faculty', 'actone', 'now', 'good'],
        'use': ['person', 'faculty', 'actone', 'good'],
    }
    # Variants are facts about the wrong tuple, not changed argument plumbing.
    if ':' in variant:
        relation, position = variant.split(':')
        keys[relation][int(position)] = 'other' if int(position) < (1 if relation in ('adopted', 'member') else 3) else 'bad'

    def key_matches(key, actual):
        # Both native judgments use the same schema; each retains its own event.
        return list(actual) == key or (key[2] == 'actone' and list(actual) == key[:2] + ['acttwo'] + key[3:])

    def applicability(q, p, r, j, c, s):
        if variant in ('split_faculties', 'second_faculty_complete') and r == 'otherfaculty':
            r = 'faculty'
        return q in ('criterionone', 'criteriontwo') and variant != 'no_applicable' and key_matches(keys['applicable'], [p, r, j, c, s])

    def evidence(q, p, r, j, positive, c, s):
        if q not in ('criterionone', 'criteriontwo'):
            return False
        item = q == 'criteriontwo'
        if variant in ('split_faculties', 'second_faculty_complete'):
            if r not in ('faculty', 'otherfaculty'):
                return False
            permitted = (r == 'otherfaculty') if variant == 'second_faculty_complete' else (r == ('otherfaculty' if item else 'faculty'))
            if not permitted:
                return False
            r = 'faculty'
        return key_matches(keys['evidence'], [p, r, j, c, s]) and states[item][0 if positive else 1]

    def use(p, r, j, s):
        if variant in ('split_faculties', 'second_faculty_complete') and r == 'otherfaculty':
            r = 'faculty'
        return used and key_matches(keys['use'], [p, r, j, s])

    m.update(zstandard=lambda: 'standard', zresource=lambda: 'faculty', zjudgment=lambda: 'actone',
        zadopted=lambda st, c: adopted and [st, c] == keys['adopted'],
        zmember=lambda st, q, c: variant != 'empty_members' and q in ('criterionone', 'criteriontwo') and [st, c] == keys['member'],
        zapplicable=applicability, zevidence=evidence, ac=use)
    if variant in ('split_faculties', 'second_faculty_complete'):
        m['ab'] = lambda r, p, s: r in ('faculty', 'otherfaculty') and p == 'person'
    if variant == 'foreign_owner':
        m['ab'] = lambda r, p, s: (r, p) == ('faculty', 'other')
    if variant == 'wrong_matter':
        m['fb'] = lambda j, matter, s: (j, matter, s) == ('actone', 'two', 'good')
    if variant == 'wrong_judge':
        m['fa'] = lambda p, j, s: (p, j, s) == ('other', 'actone', 'good')
    return m


@lru_cache(None)
def generic():
    return parse(prefix(tuple(TARGETS)) + ''.join('q[k ' + n + '[' + ARGS + ']].' for n in TARGETS))


def evidence_checks():
    count = 0
    for bits in product((False, True), repeat=6):
        states = (bits[:2], bits[2:4])
        used, adopted = bits[4:]
        active = used and adopted
        conflict = any(yes and no for yes, no in states)
        want = [active and all(yes != no for yes, no in states),
            active and all(yes and not no for yes, no in states),
            active and not conflict and any(no for _, no in states),
            active and conflict,
            active and not conflict and any(not yes and not no for yes, no in states)]
        result = evaluate(generic(), model(states, used=used, adopted=adopted))
        assert result == want, (bits, result, want)
        count += 1
    cases = {}
    for variant in ('empty_members', 'no_applicable'):
        result = evaluate(generic(), model(variant=variant))
        assert result == [False] * 5, (variant, result)
        cases[variant] = result
    return dict(combinations=count, empty_scopes=cases, violation_and_gap_can_coexist=True,
        conflict_is_same_item_only=True, evidence_not_actual_truth=True)


def binding_checks():
    cases = {}
    for relation, count in [('adopted', 2), ('member', 2), ('applicable', 5), ('evidence', 5), ('use', 4)]:
        for position in range(count):
            variant = relation + ':' + str(position)
            result = evaluate(generic(), model(variant=variant))
            want = [False, False, False, False, relation == 'evidence']
            assert result == want, (variant, result)
            cases[variant] = result
    for name in ('zadopted', 'zmember', 'zapplicable', 'zevidence', 'ac'):
        m = model()
        m[name] = unknown
        try:
            evaluate(generic(), m)
        except ValueError as exc:
            assert 'Unknown judgment standard' in str(exc)
        else:
            raise AssertionError(name)
    return dict(foreign_bindings=cases, unknown_inputs_refused=5,
        reference_now_and_performance_good_are_distinct=True)


@lru_cache(None)
def criterion():
    return parse(prefix(('hzvx',)) + 'q[c[k hzvx[' + SARGS + ']][k zperson[] k zone[] k zjudgment[] k zqualitycontext[] k zpoint[]]].')


def judgment_checks():
    cases = {}
    for variant, want in [('', True), ('foreign_owner', False), ('wrong_judge', False), ('wrong_matter', False),
        ('use:2', False), ('split_faculties', False), ('second_faculty_complete', True), ('empty_members', False)]:
        result = evaluate(criterion(), model(variant=variant))
        assert result == [want], (variant, result)
        cases[variant or 'baseline'] = result
    # A supported independent judgment is not sufficient for documented conformity.
    old = parse(prefix(('hzvg',)) + 'q[t[c[k hzvg[k zone[]]][k zperson[]]][k zpoint[]]].')
    m = model(((True, False), (False, False)))
    assert evaluate(old, m) == [True] and evaluate(criterion(), m) == [False]
    for name in ('ab', 'fa', 'fb'):
        m = model()
        m[name] = unknown
        try:
            evaluate(criterion(), m)
        except ValueError as exc:
            assert 'Unknown judgment standard' in str(exc)
        else:
            raise AssertionError(name)
    return dict(cases=cases, split_resource_evidence_rejected=True, unknown_inputs_refused=3,
        independent_judgment_can_coexist_with_evidence_gap=True)


def construction_checks():
    doc = parse(prefix(('hzvy',)) + 'r zinspect[i[h[a a a d d] c]] c.q[k zinspect[' + CODE + ']].')
    def inspect(code):
        syntax = json.loads(code.syntax)
        assert syntax == {'kind': 'apply', 'function': {'kind': 'function_ref', 'symbol': 'hzvx'},
            'arguments': [{'kind': 'call', 'symbol': 'zstandard', 'arguments': []}] +
                [{'kind': 'function_ref', 'symbol': s} for s in ('zadopted', 'zmember', 'zapplicable', 'zevidence')]}
        return code.rank == 0
    m = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    m['zinspect'] = inspect
    assert evaluate(doc, m) == [True]
    text = prefix(('hzvy',)) + 'q[c[s[' + CODE + ']][k zperson[] k zone[] k zjudgment[] k zqualitycontext[] k zpoint[]]].'
    executed = parse(text)
    assert evaluate(executed, model()) == [True]
    m = model()
    m['zevidence'] = unknown
    try:
        evaluate(executed, m)
    except ValueError as exc:
        assert 'Unknown judgment standard' in str(exc)
    else:
        raise AssertionError('Unknown evidence was hidden by quotation')
    return dict(five_references_retained=True, construction_nonfactive=True, execution_requires_evidence=True)


def ability_checks():
    text = prefix(('hzvr', 'hzvs'), native=True)
    text += ''.join('q[t[c[k ' + n + '[' + prior.QARGS + ']][k zperson[]]][k zcontext[]]].' for n in ('hzvr', 'hzvs'))
    doc = parse(text)
    cases = {}
    for name, states, want in [('conforming', ((True, False), (True, False)), [True, True]),
        ('evidence_gap', ((True, False), (False, False)), [True, False]),
        ('conflict', ((True, False), (True, True)), [True, False])]:
        result = evaluate(doc, model(states))
        assert result == want, (name, result)
        cases[name] = result
        print('judgment standards ability ' + name + ' checked', flush=True)
    return dict(cases=cases, native_judgment_and_task_indexed_ability_executed=True,
        target_is_documented_conformity_not_actual_goodness=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    for name, text in build().items():
        assert (ROOT / name).read_text(encoding='utf-8') == text, name
    n = len(old.document['declarations'])
    assert new.document['declarations'][:n] == old.document['declarations']
    assert len(new.document['declarations']) == n + 7
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 41
    for name in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / name).read_text(encoding='utf-8'))
        for notation in ('full', 'compact'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert all(d['kind'] == 'definition' for d in parse((ROOT / LIBRARY).read_text(encoding='utf-8'))['declarations'])
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    validate_hashes(ROOT, index['source_sha256'])
    active = index['works']['kant-1784']
    assert active['document'] == 'examples/v016/kant-explanatory-question.noema' and len(active['reviews']) == 10
    cat = load_catalog(ROOT, active['meaning_basis'])
    for name in active['reviews']:
        review = json.loads((ROOT / name).read_text(encoding='utf-8'))
        indices = [x['index'] for x in review['selection']['statements']]
        assert selection_binding(cat, indices) == review['selection'] == selection_binding(new, indices)
    return dict(new_definitions=7, new_primitives=0, preserved_statements=41,
        preserved_review_selections=10, roundtrips=True, source_adoption=False)


def reading():
    unit = next(u for u in json.loads((ROOT / INVENTORY).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0014')
    return dict(status='existing_use_standards_as_composed_judgment_criterion_not_adopted_source_meaning',
        reviewer='assistant_review', source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            range=[148, 412], text=unit['text'][148:412]),
        decision='既存の評価制度を同じ判断へ合成し、目的達成と適切さを区別したまま、元の基準文脈と実行時点を保持する。資料不足と不適合を区別する。原文の質の意味への採用は行わない。',
        limitations=LIMITS, whole_unit_semantically_verified=False)


def build_report():
    result = {}
    for name, fn in [('evidence', evidence_checks), ('bindings', binding_checks), ('judgments', judgment_checks),
        ('construction', construction_checks), ('ability', ability_checks), ('structure', structure)]:
        result[name] = fn()
        print(name + ' checked', flush=True)
    note = reading()
    assert json.loads((ROOT / READING).read_text(encoding='utf-8')) == note
    previous = prior.REPORT
    validate_hashes(ROOT, json.loads((ROOT / previous).read_text(encoding='utf-8'))['source_sha256'])
    paths = set(build()) | set(parent().source_sha256) | {READING, INVENTORY, INDEX, previous,
        'data/secure-use-reading-v1.json', 'scripts/compose_judgment_standards.py', 'scripts/check_judgment_standards.py',
        'scripts/compose_qualified_judgment.py', 'scripts/check_qualified_judgment.py',
        'scripts/check_topical_standing.py', 'scripts/compose_bodily_acquisition.py', 'scripts/compose_collective_attainment.py',
        'scripts/compose_topical_standing.py', 'scripts/compose_falling_depiction.py',
        'tests/test_judgment_standards.py', 'docs/judgment-standards-v1.md',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/constructed_discourse.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    source = note['source']
    return dict(status='partial_existing_standards_composed_with_judgment', document=FULL, **result,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], start=148, end=412, source=source['text'],
            definitions=list(MEANINGS), status='explicit_interpretive_annotation', full_semantic_equivalence=False),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / READING, encoded(reading()))
    report = build_report()
    if args.verify_only:
        assert json.loads((ROOT / REPORT).read_text(encoding='utf-8')) == report
    else:
        write_exact(ROOT / REPORT, encoded(report))
    print('Judgment standards, evidence and both contexts checked', flush=True)


if __name__ == '__main__':
    main()
