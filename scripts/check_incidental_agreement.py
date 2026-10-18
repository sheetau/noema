"""Check contingent outcomes, directed intentions and the adopted source question."""
from copy import deepcopy
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.diagnostic_short_circuit import lower
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_incidental_agreement import ROOT, PARENT, PARENT_BASIS, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, build, parent, closure
from scripts.check_designation_order import substantive
from scripts import check_designation_order as joint
from scripts import check_thought_correspondence as thought

REPORT = 'reports/incidental-agreement-v1.json'
AUDIT = 'data/incidental-agreement-reading-v1.json'
INDEX = 'data/semantic-review-index-v37.json'
DOC = 'docs/incidental-agreement-v1.md'


def unknown(*args):
    raise ValueError('Unknown incidental-outcome interpretation')


def evaluate(doc, values, individuals=('process', 'actor', 'activity', 'other'), scenes=('here', 'there'), diagnostic=False):
    values = {d['name']: values[d['name']] for d in doc['declarations'] if d['kind'] == 'primitive'}
    if diagnostic:
        doc, values = lower(doc, values)
    return [r['value'] for r in evaluate_document(doc, individuals=individuals, situations=scenes,
        primitives=values, max_steps=5000000, memoize_definitions=False, memoize_expressions=False)]


def generic_document(goal=False):
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc, ['rqw7' if goal else 'rqw6'])
    text = format_graph(doc, 'compact') + 'r jscene[] d.'
    if goal:
        text += '''r jprocess[] a.r jcomponent[a a a d] c.
r jaims[a a i[h[j[a]] e] j[a] d] c.r jresult[j[a]] e.
q[k rqw7[k jprocess[] r[p jresult] l[a][k jprocess[]] k jscene[] p jcomponent p jaims]].'''
    else:
        text += 'r joutcome[d] c.r jalternative[d d] c.q[k rqw6[b point[k joutcome[v point]] k jscene[] p jalternative]].'
    return parse(text)


def modal_checks():
    doc = generic_document()
    cases = 0
    for actual, other, reflexive, accessible in product((False, True), repeat=4):
        values = dict(jscene=lambda: 'here', joutcome=lambda s: actual if s == 'here' else other,
            jalternative=lambda a, b: a == 'here' and (reflexive if b == 'here' else accessible))
        assert evaluate(doc, values) == [actual and reflexive and accessible and not other]
        cases += 1
    for name in ('joutcome', 'jalternative'):
        values = dict(jscene=lambda: 'here', joutcome=lambda s: s == 'here', jalternative=lambda *a: True)
        values[name] = unknown
        try:
            evaluate(doc, values)
        except ValueError as error:
            assert 'Unknown incidental' in str(error)
        else:
            raise AssertionError(name)
    return dict(combinations=cases, empty_or_nonreflexive_scope_refused=True, necessary_outcome_refused=True,
        actual_outcome_required=True, unknown_is_not_contingency=True, ordinary_evaluation=True)


def intention_checks():
    doc = generic_document(True)
    seen = []
    def aims(actor, act, goal, bindings, scene):
        seen.append((json.loads(goal.syntax), bindings.items))
        return (actor, act, scene) == ('actor', 'activity', 'here')
    rows = {}
    for variant in ('baseline', 'designed', 'other_process', 'other_actor', 'other_activity', 'other_scene', 'no_actors'):
        row = ['process', 'actor', 'activity', 'here']
        for name, at in (('process', 0), ('actor', 1), ('activity', 2), ('scene', 3)):
            if variant == 'other_' + name:
                row[at] = 'there' if at == 3 else 'other'
        values = dict(jscene=lambda: 'here', jprocess=lambda: 'process', jresult=unknown,
            jcomponent=lambda *args: variant != 'no_actors' and tuple(args) == tuple(row),
            jaims=aims if variant != 'baseline' else lambda *args: False)
        rows[variant] = evaluate(doc, values)
        assert rows[variant] == [variant != 'designed'], (variant, rows[variant])
    assert seen and all(s == {'kind': 'function_ref', 'symbol': 'jresult'} and b == ('process',) for s, b in seen)
    for name in ('jcomponent', 'jaims'):
        values = dict(jscene=lambda: 'here', jprocess=lambda: 'process', jresult=unknown,
            jcomponent=lambda *args: True, jaims=lambda *args: False)
        values[name] = unknown
        try:
            evaluate(doc, values)
        except ValueError as error:
            assert 'Unknown incidental' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, quoted_goal_and_ordered_bindings_preserved=True,
        goal_content_not_executed=True, unknown_intention_not_negated=True, ordinary_evaluation=True)


def source_document(presentation=False):
    doc = parse((ROOT / FULL).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc, ['hzle' if presentation else 'hzld'])
    doc['statements'] = [doc['statements'][22]] if presentation else []
    if not presentation:
        doc = parse(format_graph(doc, 'compact') + 'r jextent[] a.q[h[k hzld[]][k jextent[]]].')
    return doc


def argument_checks():
    # Exercise the actual adapter with a literal, total interpretation of its
    # called relation; the full relation is separately used by source_checks.
    catalog = load_catalog(ROOT, BASIS)
    adapter = catalog.entries['hzwk']['declaration']
    base = parse('p:r hzkv[a a a d] c.r jfirst[] a.r jsecond[] a.r jextent[] a.r jscene[] d.')
    base['declarations'].append(deepcopy(adapter))
    prefix = format_graph(base, 'compact')
    rows = {}
    for label, bindings in (
        ('right', 'k jfirst[] k jsecond[] k jextent[]'),
        ('empty', ''), ('short', 'k jfirst[] k jsecond[]'),
        ('long', 'k jfirst[] k jsecond[] k jextent[] k jfirst[]'),
        ('swapped', 'k jsecond[] k jfirst[] k jextent[]'),
        ('other_extent', 'k jfirst[] k jsecond[] k jfirst[]')):
        doc = parse(prefix + 'q[t[k hzwk[l[a][' + bindings + ']]][k jscene[]]].')
        values = dict(jfirst=lambda: 'first', jsecond=lambda: 'second', jextent=lambda: 'extent', jscene=lambda: 'here',
            hzkv=lambda *args: args == ('first', 'second', 'extent', 'here'))
        rows[label] = evaluate(doc, values, ('first', 'second', 'extent'))
        assert rows[label] == [label == 'right'], (label, rows[label])
    return dict(contrasts=rows, ordinary_adapter_evaluation=True, no_truncation_or_reordering=True)


def source_values(doc, variant='baseline'):
    inherited = variant if variant in ('no_cause', 'no_occurrence', 'other_first_document', 'other_second_document',
        'other_causal_extent', 'empty_possible', 'unknown_match', 'one_way') else 'baseline'
    values = thought.source_model(doc, inherited)
    # The alternative has attributed contents but lacks the correspondence.
    # These are explicit synthetic interpretations, not claims about the papers.
    base = {n: values[n] for n in ('hzlf', 'hzlg', 'hzlh', 'hzli')}
    for n in base:
        fn = base[n]
        values[n] = lambda *a, fn=fn: fn(*a[:-1], 'possible' if a[-1] == 'outside' else a[-1])
    match = values['hzli']
    values['hzli'] = lambda *a: (variant == 'necessary' or a[-1] != 'outside') and match(*a)
    values.update(
        hzwi=lambda process, actor, act, scene: (process, actor, act, scene) == ('episode', 'author', 'present', 'possible'),
        hzwj=lambda process, anchor, other: process == ('other_episode' if variant == 'other_basis_process' else 'episode')
            and anchor == 'possible' and other in (() if variant == 'empty_basis' else
                ('outside',) if variant == 'no_anchor' else ('possible',) if variant == 'no_alternative' else ('possible', 'outside')),
        hztl=lambda actor, act, goal, bindings, scene: variant == 'designed' and
            (actor, act, scene) == ('author', 'present', 'possible') and
            json.loads(goal.syntax) == {'kind': 'function_ref', 'symbol': 'hzwk'} and bindings.items == ('present', 'prior', 'partial'))
    for variant_name, name in [('unknown_basis', 'hzwj'), ('unknown_components', 'hzwi'), ('unknown_intention', 'hztl')]:
        if variant == variant_name:
            values[name] = unknown
    return values


def source_checks():
    doc = source_document()
    assert 'hzkw' not in {d['name'] for d in doc['declarations']}
    rows = {}
    for variant in ('baseline', 'designed', 'necessary', 'empty_basis', 'no_anchor', 'no_alternative',
        'other_basis_process', 'no_cause', 'no_occurrence', 'other_first_document', 'other_second_document',
        'other_causal_extent', 'empty_possible', 'one_way'):
        rows[variant] = evaluate(doc, source_values(doc, variant), thought.previous.DOMAIN, thought.previous.SCENES, True)
        assert rows[variant] == [variant == 'baseline'], (variant, rows[variant])
    for variant in ('unknown_basis', 'unknown_components', 'unknown_intention', 'unknown_match'):
        try:
            evaluate(doc, source_values(doc, variant), thought.previous.DOMAIN, thought.previous.SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(variant)
    presentation = source_document(True)
    seen = []
    assert evaluate(presentation, thought.previous.presentation_model(presentation, seen=seen),
        thought.previous.DOMAIN, thought.previous.SCENES) == [True]
    assert seen and all(s == {'kind': 'call', 'symbol': 'hzld', 'arguments': []} for s in seen)
    return dict(contrasts=rows, unknown_inputs_refused=True, opaque_chance_removed_from_active_question=True,
        candidate_diagnostic_short_circuit=True, presentation_ordinary_evaluation=True,
        quoted_question_does_not_assert_actual_agreement=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 42
    assert set(new.entries) - set(old.entries) == (set(PRIMITIVES) | set(MEANINGS)) - {'hzlc'}
    assert [n for n in old.entries if substantive(old.entries[n]) != substantive(new.entries[n])] == ['hzlc']
    affected = [i for i, s in enumerate(new.document['statements']) if 'hzlc' in
        {d['name'] for d in closure(new.document, _references(s))}]
    assert affected == [22]
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for name in index['works']['kant-1784']['reviews']:
        review = json.loads((ROOT / name).read_text(encoding='utf-8'))
        indices = [r['index'] for r in review['selection']['statements']]
        before, after = selection_binding(old, indices), selection_binding(new, indices)
        assert before == review['selection'] and before['statements'] == after['statements']
        assert before['dependencies'] == after['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in before['dependencies'])
    for name, body in build().items():
        assert (ROOT / name).read_text(encoding='utf-8') == body, name
    for name in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / name).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=42, changed_definition_symbols=['hzlc'], affected_statements=affected,
        new_primitives=2, new_definitions=4, preserved_review_meanings=10, roundtrips=True)


def joint_checks():
    doc = parse((ROOT / FULL).read_text(encoding='utf-8'))
    doc['statements'] = [doc['statements'][i] for i in [*joint.prior.prior.SELECTION, 41]]
    doc['declarations'] = closure(doc, [s['body']['symbol'] for s in doc['statements']])
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(joint.model())
    assert evaluate(doc, values, joint.prior.DOMAIN, joint.prior.SCENES) == [True] * 12
    return dict(connected_assertions=12, ordinary_evaluation=True, question_answers_left_unknown=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0020')
    return dict(status='contextual_incidental_outcome_adopted_not_whole_unit_review', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[394, 462], text=unit['text'][394:462]),
        primary_source='https://korpora.org/Kant/aa08/042.html',
        reading='別回答をまだ受領していない文脈で、計画して一致させたのではない符合が、説明上の条件から必然とはされない形でどこまで生じ得るかを問う読みを採る。',
        distinction='非目的性だけで偶然一般を定義しない。指定した比較条件に対する結果の非必然性を併せ、原因不明・無原因・確率的独立・全物理過程の非決定性を補わない。',
        expectation='思想の一致一般が意外だという判断や数値確率を追加しない。合理的に同じ問題を考えることや共通の背景原因は排除しない。',
        limits=['語義資料は唯一の歴史的解釈を証明しない。採用する比較条件と目的内容は文脈に依存する。',
            '未知の目標は非目的性の証拠にならない。入力の関係を根拠なしに偽へ初期化する仕組みはない。',
            'これは人が指定して書く意味構成であり、自然言語からの自動抽出や無制限の意味同値判定ではない。'],
        remaining=['内容対応規約の採用範囲の確認', '著者注全体を改訂本文で再読する意味確認'],
        whole_unit_semantically_verified=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in (inv, PARENT, PARENT_BASIS,
            'data/chance-reading-v1.json', 'data/footnote-audit-v2.json')})


def build_report():
    results = {}
    for name, fn in [('modal', modal_checks), ('intentions', intention_checks), ('arguments', argument_checks), ('source', source_checks),
        ('joint', joint_checks), ('structure', structure)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    note = audit()
    assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == note
    validate_hashes(ROOT, note['source_sha256'])
    paths = set(build()) | set(parent().source_sha256) | set(note['source_sha256']) | {
        AUDIT, INDEX, DOC, 'scripts/compose_incidental_agreement.py', 'scripts/check_incidental_agreement.py',
        'tests/test_incidental_agreement.py', 'scripts/check_designation_order.py', 'scripts/check_thought_correspondence.py',
        'scripts/check_exploratory_question.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/diagnostic_short_circuit.py', 'noema/meaning_catalog.py',
        'noema/semantic_reviews.py', 'noema/script.py'}
    source = note['source']
    return dict(status='partial_contextual_incidental_agreement', document=FULL, **results,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'], source=source['text'],
            definitions=['rqw6', 'rqw7', 'hzwk', 'hzwl', 'hzlc'], status='explicit_interpretive_annotation', full_semantic_equivalence=False),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit()))
    write_exact(ROOT / REPORT, encoded(build_report()))
    print('Incidental agreement checked', flush=True)


if __name__ == '__main__':
    main()
