"""Check the adopted content convention and reread the complete author note.

The small propositional oracle below is diagnostic test data, NOT Noema's
general meaning comparison algorithm or a natural-language translator.
"""
from copy import deepcopy
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.definition_comparison import DefinitionComparator
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_footnote_reading import ROOT, PARENT, PARENT_BASIS, FULL, CORE, BASIS, ANNOTATIONS, SELECTION, CONVENTIONS, build, parent, closure
from scripts.check_designation_order import substantive
from scripts import check_incidental_agreement as incidental
from scripts import check_designation_order as designation

REPORT = 'reports/footnote-reading-v1.json'
AUDIT = 'data/footnote-audit-v3.json'
INDEX = 'data/semantic-review-index-v38.json'
DOC = 'docs/footnote-reading-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
FACSIMILE = 'artifacts/author-signature-facsimile-v1/page-494.jpg'
PRIOR_REPORTS = ['reports/incidental-agreement-v1.json', 'reports/designation-order-v1.json',
    'reports/periodical-profile-v1.json', 'reports/defined-thoughts-v1.json', 'reports/described-thoughts-v1.json',
    'reports/thought-correspondence-v1.json', 'reports/current-footnote-v1.json']
PREFIX = 'p:r ja[d] c.r jb[d] c.r jc[d] c.'
A, B, C = ('k ' + n + '[v scene]' for n in ('ja', 'jb', 'jc'))


def quote(formula, force='s'):
    text = 'r[j ' + force + '[b scene[' + formula + ']]]'
    doc = parse(PREFIX + 'q[e[' + text + '][' + text + ']].')
    return doc['statements'][0]['body']['arguments'][0]


def finite_content(value):
    """Retain force and atom identity; reject anything outside the test fragment."""
    if value.get('kind') != 'quote' or value.get('rank', 0) != 0:
        raise ValueError('Unknown test-fragment description')
    msg = value['body']
    if msg.get('kind') != 'message' or msg.get('force') not in ('assert', 'ask', 'direct'):
        raise ValueError('Unknown test-fragment message')
    content = msg['content']
    if content.get('kind') != 'content':
        raise ValueError('Unknown test-fragment content')
    atoms = set()
    def visit(node):
        kind = node['kind']
        if kind == 'call' and node['symbol'] in ('ja', 'jb', 'jc') and node['arguments'] == [
            {'kind': 'variable', 'name': content['variable']}]:
            atoms.add(node['symbol'])
            return ('atom', node['symbol'])
        if kind in ('and', 'or', 'not', 'implies'):
            return (kind, *(visit(n) for n in node['arguments']))
        raise ValueError('Unknown test-fragment expression')
    tree = visit(content['body'])
    return msg['force'], atoms, tree


def truth(tree, assignment):
    op, *args = tree
    if op == 'atom':
        return assignment[args[0]]
    bits = [truth(t, assignment) for t in args]
    return {'and': lambda: all(bits), 'or': lambda: any(bits), 'not': lambda: not bits[0],
        'implies': lambda: not bits[0] or bits[1]}[op]()


def finite_preserves(source, target):
    force, atoms, first = finite_content(source)
    target_force, target_atoms, second = finite_content(target)
    if force != target_force or not atoms <= target_atoms:
        return False
    names = sorted(atoms | target_atoms)
    return all(not truth(second, dict(zip(names, bits))) or truth(first, dict(zip(names, bits)))
        for bits in product((False, True), repeat=len(names)))


def criterion_checks():
    conjunction = quote('w[' + A + '][' + B + ']')
    reversed_ = quote('w[' + B + '][' + A + ']')
    comparison = DefinitionComparator(parse(PREFIX)).compare(conjunction, reversed_)
    assert comparison['status'] == 'not_established'
    pairs = {
        'conjunction_order': (conjunction, reversed_, [True, True]),
        'additional_content': (quote(A), conjunction, [True, False]),
        'same_sampled_truth': (quote(A), quote(B), [False, False]),
        'negation': (quote(A), quote('u[' + A + ']'), [False, False]),
        'different_question': (quote(A), quote(A, 'q'), [False, False]),
        'condition_direction': (quote('y[' + A + '][' + B + ']'), quote('y[' + B + '][' + A + ']'), [False, False]),
        'different_tautological_subject': (quote('x[' + A + '][u[' + A + ']]'), quote('x[' + B + '][u[' + B + ']]'), [False, False]),
    }
    rows = {}
    for name, (a, b, expected) in pairs.items():
        rows[name] = [finite_preserves(a, b), finite_preserves(b, a)]
        assert rows[name] == expected, (name, rows[name])
    assert truth(finite_content(quote(A))[2], {'ja': True}) == truth(finite_content(quote(B))[2], {'jb': True})
    # A conjunction may supply two comparison items, but negation is not
    # distributed over it. This is a reading constraint, not a text splitter.
    assert [finite_preserves(quote(A), conjunction), finite_preserves(quote(B), conjunction)] == [True, True]
    negated = quote('u[w[' + A + '][' + B + ']]')
    assert not finite_preserves(quote('u[' + A + ']'), negated)
    assert not finite_preserves(quote('u[' + B + ']'), negated)
    for unsupported in ('f who a[k ja[v scene]]', 'r[k ja[v scene]]'):
        try:
            finite_content(quote(unsupported))
        except ValueError:
            pass
        else:
            raise AssertionError('Unsupported description silently classified')
    return dict(contrasts=rows, all_boolean_assignments_checked=True, scope_preserved=True,
        definition_expansion_not_required_for_every_correspondence=True,
        sampled_truth_not_sufficient=True, unknown_fragment_refused=True,
        diagnostic_oracle_only=True, automatic_general_synonym_classifier=False)


def source_checks():
    doc = parse((ROOT / FULL).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc, ['hzld'])
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + 'r jextent[] a.q[h[k hzld[]][k jextent[]]].')
    rows = {}
    for name, left, right, expected in (
        ('reordered_claim', quote('w[' + A + '][' + B + ']'), quote('w[' + B + '][' + A + ']'), True),
        ('same_truth_distinct_content', quote(A), quote(B), False),
        ('claim_vs_question', quote(A), quote(A, 'q'), False),
        ('one_way_extra_content', quote(A), quote('w[' + A + '][' + B + ']'), False)):
        values = incidental.source_values(doc)
        descriptions = {'author': left, 'other': right}
        def matching(a, b, topic, scene):
            return topic == 'full' and scene == 'possible' and a in descriptions and b in descriptions and \
                finite_preserves(descriptions[a], descriptions[b])
        values['hzli'] = matching
        rows[name] = incidental.evaluate(doc, values, incidental.thought.previous.DOMAIN, incidental.thought.previous.SCENES, True)
        assert rows[name] == [expected], (name, rows[name])
    values = incidental.source_values(doc)
    values['hzli'] = incidental.unknown
    try:
        incidental.evaluate(doc, values, incidental.thought.previous.DOMAIN, incidental.thought.previous.SCENES, True)
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown correspondence supplied as false')
    return dict(contrasts=rows, active_question_checked=True, diagnostic_short_circuit=True,
        unknown_correspondence_refused=True, real_paper_contents_not_invented=True)


def joint_checks():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    rows = {}
    for variant in ('baseline', 'other_current_question', 'other_trial_question'):
        values = {d['name']: incidental.unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(designation.model(variant))
        false = designation.prior.prior.EXPECTED_FALSE[variant]
        rows[variant] = incidental.evaluate(doc, values, designation.prior.DOMAIN, designation.prior.SCENES)
        assert rows[variant] == [i not in false for i in range(11)] + [True]
    return dict(cases=rows, selected_statements=SELECTION, ordinary_evaluation=True,
        real_answers_and_comparison_left_unknown=True, shared_question_and_trial_checked=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert new.document == old.document
    assert set(new.entries) == set(old.entries)
    changed = [n for n in old.entries if substantive(old.entries[n]) != substantive(new.entries[n])]
    assert set(changed) == set(CONVENTIONS)
    for n in old.entries:
        assert old.entries[n]['declaration'] == new.entries[n]['declaration']
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review = json.loads((ROOT / path).read_text(encoding='utf-8'))
        indices = [s['index'] for s in review['selection']['statements']]
        before, after = selection_binding(old, indices), selection_binding(new, indices)
        assert before == review['selection'] and before['statements'] == after['statements']
        assert before['dependencies'] == after['dependencies']
        assert not set(changed) & set(before['dependencies'])
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in before['dependencies'])
    for name, body in build().items():
        assert (ROOT / name).read_text(encoding='utf-8') == body, name
    for name in (FULL, CORE):
        d = parse((ROOT / name).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(d, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    return dict(preserved_statement_count=42, new_primitives=0, new_definitions=0,
        changed_declarations=[], changed_conventions=sorted(changed), preserved_review_meanings=10, roundtrips=True)


def audit():
    old = json.loads((ROOT / 'data/footnote-audit-v2.json').read_text(encoding='utf-8'))
    unit = next(u for u in json.loads((ROOT / INVENTORY).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0020')
    clauses = deepcopy(old['clauses'])
    for row in clauses:
        assert row['source'] == unit['text'][slice(*row['range'])]
    assert clauses[0]['range'][0] == 0 and clauses[-1]['range'][1] == len(unit['text'])
    assert all(a['range'][1] == b['range'][0] for a, b in zip(clauses, clauses[1:]))
    clauses[1].update(assessment='represented_under_reading', symbols=['hzkk', 'hzwg', 'hzwe', 'rqw4', 'rqw5'],
        reason='13日付の掲載号と、系列の名称使用内でのBüschingへの編集上の帰属・暦上の週刊周期を分けて記述する。欠刊のない実績、印刷者、単独の全記事著者は補わない。')
    clauses[4]['reason'] += ' 現行hzmdは著者・使用箇所の規約が明示されたhzwhを使い、旧引数順の欠陥を含まない。'
    clauses[4]['symbols'].append('hzwh')
    clauses[8].update(assessment='represented_under_reading', symbols=['hzld', 'hzlc', 'hzwl', 'rqw6', 'rqw7', 'hzkv', 'rqrx', 'rqry'],
        reason='共通の粒度で二回答の内容を比較し、双方の内容保持がある論点の範囲を問う。計画された一致ではなく比較条件から必然でない結果が、同じ過程の寄与でどこまで生じ得るかという読みを採る。定義展開や真偽値だけへ内容対応を狭めず、実際の一致・最大値・確率を補わない。')
    paths = {INVENTORY, FACSIMILE, PARENT, PARENT_BASIS, 'data/footnote-audit-v2.json',
        'data/incidental-agreement-reading-v1.json', 'data/periodical-profile-reading-v1.json',
        'data/designation-order-audit-v1.json'}
    return dict(schema_version='noema-whole-unit-reading-1', reviewer='assistant_review',
        decision='equivalent_under_stated_reading', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], text=unit['text'], range=[0, len(unit['text'])]),
        selection=selection_binding(load_catalog(ROOT, BASIS), SELECTION), clauses=clauses,
        sources_revisited=[dict(path=FACSIMILE, visually_inspected=True, page=494),
            dict(url='https://korpora.org/Kant/aa08/042.html', use='著者注全体、二つの回答、指示・時制・反事実・試みと問いの接続を再読。')],
        interpretation=['週刊・編集上の帰属・敬称は呼称の使用内の描写として保つ。',
            '他方の回答をまだ受領していないことと、それを受領していたなら現在の論説を差し控えたという反事実を区別する。',
            'magはこの提示への容認、nurはこの箇所で与える試みという種類への限定と読む。',
            'wiefernは同じ問いへの二回答が一致する論点の範囲。内容保持を共通粒度で両方向に要求し、表記・同時の真・任意の論理的同値で代用しない。',
            'Zufallは前回採用した非目的的・文脈上非必然な符合の読み。過程・結果・因果的寄与を同じ状況へ結ぶ。'],
        unresolved=[], not_required_for_expression=old['not_required_for_expression'],
        limits=['実装者であるアシスタントの採用読解に基づく判断。独立査読・歴史的事実の証明・意味同値の自動証明ではない。',
            '文0と40は表題と現在の回答を照応させる文脈証拠であり、著者注の原文文字数へ追加しない。',
            '同義関係を全入力で決める算法、二回答の実際の一致範囲、唯一の哲学的な偶然理論を完成したという判断ではない。',
            '原刊の綴りや書体の復元は対象外。採用した意味と提示の関係を確認する。'],
        supersedes='data/footnote-audit-v2.json', source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def build_report():
    results = {}
    for name, fn in [('criterion', criterion_checks), ('source', source_checks), ('joint', joint_checks), ('structure', structure)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    note = audit()
    assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == note
    paths = set(build()) | set(parent().source_sha256) | set(note['source_sha256']) | {
        AUDIT, INDEX, DOC, 'scripts/compose_footnote_reading.py', 'scripts/check_footnote_reading.py',
        'tests/test_footnote_reading.py', 'scripts/check_incidental_agreement.py', 'noema/definition_comparison.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/diagnostic_short_circuit.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    for name in PRIOR_REPORTS:
        record = json.loads((ROOT / name).read_text(encoding='utf-8'))
        validate_hashes(ROOT, record['source_sha256'])
        paths.add(name)
        paths.update(record['source_sha256'])
    source = note['source']
    return dict(status='whole_footnote_reading_supported_by_explicit_review_not_automatic_proof', document=FULL,
        **results, alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'],
            source=source['text'], definitions=['hzjt', 'hzju', 'hzkk', 'hzkt', 'hzle', 'hzlr', 'hzlt', 'hzlz', 'hzmd', 'hzwg'],
            status='explicit_interpretive_annotation', full_semantic_equivalence=False),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        note='Whole-unit judgment is registered separately; finite tests do not award semantic completion.',
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit()))
    write_exact(ROOT / REPORT, encoded(build_report()))
    print('Whole author note reread; formal evidence recorded separately', flush=True)


if __name__ == '__main__':
    main()
