"""Reproduce the reversed legacy arguments and check a shared literal contract."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts import check_periodical_profile as prior
from scripts.compose_designation_order import ROOT, PARENT, PARENT_BASIS, FULL, CORE, BASIS, ANNOTATIONS, build, parent, closure

REPORT = 'reports/designation-order-v1.json'
AUDIT = 'data/designation-order-audit-v1.json'
INDEX = 'data/semantic-review-index-v36.json'


@lru_cache(None)
def document(mode='pair'):
    d = parse((ROOT / FULL).read_text(encoding='utf-8'))
    indices = [26, 41] if mode != 'joint' else [*prior.prior.SELECTION, 41]
    d['statements'] = [d['statements'][i] for i in indices]
    roots = [s['body']['symbol'] for s in d['statements']]
    if mode == 'legacy':
        legacy = deepcopy(parent().entries['hzmd']['declaration'])
        legacy['name'] = 'zlegacy'
        d['declarations'].append(legacy)
        d['statements'].insert(0, {'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'zlegacy', 'arguments': []}})
        roots.append('zlegacy')
    d['declarations'] = closure(d, roots)
    return d


def unknown(*args):
    raise ValueError('Unknown designation-use interpretation')


def model(variant='baseline', honor=True, periodical=True, seen=None, legacy_literal=True):
    inherited = variant if variant in prior.prior.EXPECTED_FALSE else 'baseline'
    values = prior.model(inherited)
    old_du = values['du']
    # The old catalog labels du(node, author, ...), although its old test
    # interpretation accepted (author, node, ...). Reproduce both explicitly.
    if legacy_literal:
        values['du'] = lambda node, author, target, content, scene: old_du(author, node, target, content, scene)
    facts = []
    for label, enabled, use, target, content in (
        ('honor', honor and variant != 'no_projected_classification', 'mention', 'hzmb', 'hzmc'),
        ('periodical', periodical, 'naming', 'hzwf', 'hzwe')):
        if not enabled or variant == label + '_missing':
            continue
        row = ['author', use, target, content, 'note']
        edits = {'other_author': (0, 'other'), 'other_use': (1, 'citation'),
            'other_target': (2, 'hzwf' if label == 'honor' else 'hzmb'),
            'other_description': (3, 'hzwe' if label == 'honor' else 'hzmc'), 'other_context': (4, 'branch')}
        for suffix, (at, value) in edits.items():
            if variant == label + '_' + suffix:
                row[at] = value
        if variant == label + '_swapped_author_use':
            row[0], row[1] = row[1], row[0]
        if variant == 'crossed_contents':
            row[3] = 'hzwe' if label == 'honor' else 'hzmc'
        facts.append(tuple(row))

    def uses(author, node, target, content, context):
        if variant == 'unknown_use':
            return unknown()
        first, second = json.loads(target.syntax), json.loads(content.syntax)
        if seen is not None:
            seen.append((author, node, first, second, context))
        if first.get('kind') != 'function_ref' or second.get('kind') != 'function_ref':
            return False
        return (author, node, first['symbol'], second['symbol'], context) in facts

    values['hzwh'] = uses
    return values


def evaluate(doc, values):
    return [r['value'] for r in evaluate_document(doc, individuals=prior.DOMAIN, situations=prior.SCENES,
        primitives={d['name']: values[d['name']] for d in doc['declarations'] if d['kind'] == 'primitive'},
        max_steps=3000000, memoize_definitions=False, memoize_expressions=False)]


def legacy_checks():
    old = evaluate(document('legacy'), model(legacy_literal=False))
    literal = evaluate(document('legacy'), model())
    assert old == [True, True, True] and literal == [False, True, True]
    assert parent().entries['du']['arguments'][:2] == ['node', 'author']
    assert parent().entries['hzwh']['arguments'][:2] == ['著者', '記述の使用箇所']
    return dict(old_test_interpretation=old, literal_catalog_interpretation=literal,
        order=['legacy_honorific', 'revised_honorific', 'periodical'],
        regression_reproduced=True, no_new_primitive=True)


def binding_checks():
    rows = {}
    for honor, periodical in product((False, True), repeat=2):
        actual = evaluate(document(), model(honor=honor, periodical=periodical))
        assert actual == [honor, periodical]
        rows[str((honor, periodical))] = actual
    variants = {}
    for label in ('honor', 'periodical'):
        for suffix in ('missing', 'swapped_author_use', 'other_author', 'other_use', 'other_target', 'other_description', 'other_context'):
            name = label + '_' + suffix
            actual = evaluate(document(), model(name))
            assert actual == ([False, True] if label == 'honor' else [True, False]), (name, actual)
            variants[name] = actual
    assert evaluate(document(), model('crossed_contents')) == [False, False]
    assert evaluate(document(), model('no_courtesy')) == [False, True]
    seen = []
    assert evaluate(document(), model(seen=seen)) == [True, True]
    assert [(r[0], r[1], r[4]) for r in seen] == [('author', 'mention', 'note'), ('author', 'naming', 'note')]
    try:
        evaluate(document(), model('unknown_use'))
    except ValueError as error:
        assert 'Unknown designation-use' in str(error)
    else:
        raise AssertionError('Unknown use was guessed')
    return dict(independent_uses=rows, contrasts=variants, crossed_properties_refused=True,
        courtesy_separate_from_description=True, unknown_use_refused=True, same_author_use_order=True,
        factual_classification_and_publication_policy_unevaluated=True)


def joint_checks():
    rows = {}
    for variant in ('baseline', 'no_projected_classification', 'no_courtesy', 'other_current_question',
            'no_note_link', 'other_trial_question', 'periodical_swapped_author_use', 'honor_swapped_author_use'):
        false = prior.prior.EXPECTED_FALSE.get(variant, ())
        expected = [i not in false for i in range(11)] + [variant != 'periodical_swapped_author_use']
        if variant == 'honor_swapped_author_use':
            expected[9] = False
        actual = evaluate(document('joint'), model(variant))
        assert actual == expected, (variant, actual, expected)
        rows[variant] = actual
    assert 'du' not in {d['name'] for d in document('joint')['declarations']}
    return dict(cases=rows, twelve_connected_assertions=True, legacy_du_absent_from_joint_selection=True,
        ordinary_evaluation=True, memoization=False)


def legacy_scope_checks():
    old = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    new = parse((ROOT / FULL).read_text(encoding='utf-8'))
    def consumers(doc):
        from noema.meaning_catalog import _references
        deps = {}
        for declaration in doc['declarations']:
            refs = _references(declaration.get('body'))
            deps[declaration['name']] = {declaration['name']} | set().union(*(deps[r] for r in refs))
        return [i for i, statement in enumerate(doc['statements']) if 'du' in
            set().union(*(deps[r] for r in _references(statement)))]
    assert consumers(old) == [8, 26] and consumers(new) == [8]
    # The remaining direct source use already passes node then author.
    direct = deepcopy(new)
    direct['statements'] = [direct['statements'][8]]
    direct['declarations'] = closure(direct, ['rq', 'dq', 'wa', 'dr', 'ds', 'wh', 'du'])
    values = {d['name']: unknown for d in direct['declarations'] if d['kind'] == 'primitive'}
    values.update(dq=lambda: 'mention', wa=lambda: 'author', wh=lambda: 'text',
        du=lambda node, author, target, content, scene: (node, author, scene) == ('mention', 'author', 'text')
        and json.loads(target.syntax) == {'kind': 'function_ref', 'symbol': 'dr'}
        and json.loads(content.syntax) == {'kind': 'function_ref', 'symbol': 'ds'})
    assert evaluate(direct, values) == [True]
    swapped = deepcopy(direct)
    arguments = swapped['statements'][0]['body']['arguments']
    arguments[0], arguments[1] = arguments[1], arguments[0]
    assert evaluate(swapped, values) == [False]
    return dict(previous_active_du_consumers=[8, 26], current_active_du_consumers=[8],
        remaining_use_has_literal_node_author_order=True, swapped_order_rejected=True,
        unexecuted_legacy_definitions_not_certified=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    for name, body in build().items():
        assert (ROOT / name).read_text(encoding='utf-8') == body, name
    assert len(old.document['statements']) == len(new.document['statements']) == 42
    changed = [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b]
    assert changed == []
    assert set(new.entries) == set(old.entries)
    changed_bodies = [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']]
    assert changed_bodies == ['hzmd']
    assert all(substantive(new.entries[n]) == substantive(entry) for n, entry in old.entries.items() if n != 'hzmd')
    old_order = [d['name'] for d in old.document['declarations'] if d['name'] != 'hzwh']
    new_order = [d['name'] for d in new.document['declarations'] if d['name'] != 'hzwh']
    assert old_order == new_order
    from noema.meaning_catalog import _references
    affected = [i for i, statement in enumerate(new.document['statements']) if
        'hzmd' in {d['name'] for d in closure(new.document, _references(statement))}]
    assert affected == [26]
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for name in index['works']['kant-1784']['reviews']:
        review = json.loads((ROOT / name).read_text(encoding='utf-8'))
        indices = [r['index'] for r in review['selection']['statements']]
        before, after = selection_binding(old, indices), selection_binding(new, indices)
        assert before == review['selection'] and before['statements'] == after['statements']
        assert before['dependencies'] == after['dependencies'] and not set(indices) & set(affected)
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in before['dependencies'])
    assert load_annotations(ROOT, BASIS, ANNOTATIONS).show()['entries'] == load_annotations(
        ROOT, PARENT_BASIS, 'data/periodical-profile-identifiers-v1.json').show()['entries']
    for name in (FULL, CORE):
        d = parse((ROOT / name).read_text(encoding='utf-8'))
        for notation in ('full', 'compact'):
            text = format_graph(d, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    return dict(changed_statement_indices=changed, preserved_statements=42, statement_count=42,
        changed_definition_symbols=changed_bodies, changed_dependency_statement_indices=affected,
        new_definitions=0, new_primitives=0, preserved_review_meanings=10, review_provenance_rebound=True, roundtrips=True)


def substantive(entry):
    return {k: v for k, v in entry.items() if k not in ('meaning_basis', 'declaration_document')}


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0020')
    return dict(status='honorific_argument_order_corrected_in_active_statement',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[177, 255], text=unit['text'][177:255]),
        defect='旧duの引数名は箇所・著者だが、hzmdと旧テストは著者・箇所の順を用いていた。型がどちらも個体であるため構文検査だけでは検出されなかった。',
        resolution='現行辞書のhzmdを改訂し、著者・箇所の順が明示された既存hzwhを使う。文26の表記と意味上の意図を保ち、刊行物の呼称と同じ関係に接続する。',
        historical_evidence_preserved=True, whole_unit_semantically_verified=False,
        active_du_consumers_before=[8, 26], active_du_consumers_after=[8],
        remaining_active_use='文8は箇所dq・著者waの順であり、規約どおりの解釈で成立し、交換した反例では成立しない。',
        remaining=['偶発性と内容対応の採用規約', '著者注全体の意味確認', '本文から未参照の旧定義の正しさは今回保証しない'],
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in (inv, PARENT, PARENT_BASIS,
            'data/exercise-capacity-basis-v1.json', 'scripts/check_projected_classification.py',
            'data/chance-reading-v1.json', 'data/footnote-audit-v2.json')})


def build_report():
    results = {}
    for label, fn in [('legacy', legacy_checks), ('bindings', binding_checks), ('joint', joint_checks),
            ('legacy_scope', legacy_scope_checks), ('structure', structure)]:
        results[label] = fn()
        print(label + ' checked', flush=True)
    note = audit()
    assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == note
    validate_hashes(ROOT, note['source_sha256'])
    paths = set(build()) | set(parent().source_sha256) | set(note['source_sha256']) | {
        AUDIT, INDEX, 'docs/designation-order-v1.md', 'scripts/compose_designation_order.py',
        'scripts/check_designation_order.py', 'tests/test_designation_order.py', 'scripts/check_periodical_profile.py',
        'scripts/check_current_footnote.py', 'scripts/compose_falling_depiction.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/identifiers.py', 'noema/script.py'}
    source = note['source']
    return dict(status='partial_honorific_argument_order_corrected', document=FULL, **results,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'],
            source=source['text'], definitions=['hzmd'], status='explicit_interpretive_annotation', full_semantic_equivalence=False),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit()))
    report = build_report()
    if args.verify_only:
        assert json.loads((ROOT / REPORT).read_text(encoding='utf-8')) == report
    else:
        write_exact(ROOT / REPORT, encoded(report))
    print('Literal designation argument order and connected footnote checked', flush=True)


if __name__ == '__main__':
    main()
