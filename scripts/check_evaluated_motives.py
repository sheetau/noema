"""Check factual dispositions separately from contextual fault attribution."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts.compose_evaluated_motives import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, build, parent, closure
from scripts.check_motive_causes import evaluate, motive_values, unknown, symbol, DOMAIN, SCENES
from scripts.check_designation_order import substantive

REPORT = 'reports/evaluated-motives-v1.json'
AUDIT = 'data/evaluated-motives-reading-v1.json'
INDEX = 'data/semantic-review-index-v40.json'
DOC = 'docs/evaluated-motives-v1.md'


@lru_cache(None)
def motive_document():
    doc = parse((ROOT / FULL).read_text(encoding='utf-8'))
    doc.update(declarations=closure(doc, ['mq', 'mr', 'mv', 'wh', 'rqxd']), statements=[])
    # Both raw and qualified group conditions are evaluated from the actual
    # episode definitions; no abstraction replaces mf/mg, rqt4 or hziq here.
    text = format_graph(doc, 'compact') + 'r jalice[] a.r jbob[] a.'
    for raw, qualified, person, group in [('rqxb', 'mj', 'jalice', 'mq'), ('rqxc', 'mk', 'jbob', 'mr')]:
        text += 'q[t[k ' + raw + '[k ' + person + '[]]][k wh[]]].'
        text += 'q[t[k ' + qualified + '[k ' + person + '[]]][k wh[]]].'
        text += 'q[k rqxd[k ' + person + '[] r[p ' + raw + '] k wh[]]].'
        text += 'q[t[k ' + group + '[k mv[]]][k wh[]]].'
    return parse(text)


def values(variant='baseline', faults=(True, True), fault_variant='baseline'):
    result = motive_values(variant)
    result.update(jalice=lambda: 'alice', jbob=lambda: 'bob')
    def fault(person, state, scene):
        pairs = {pair for pair, bit in zip([('alice', 'rqxb'), ('bob', 'rqxc')], faults, strict=True) if bit}
        if fault_variant == 'other_person': pairs = {('group', n) for _, n in pairs}
        if fault_variant == 'other_state': pairs = {(p, 'rqxc' if n == 'rqxb' else 'rqxb') for p, n in pairs}
        if fault_variant == 'qualified_state': pairs = {(p, 'mj' if n == 'rqxb' else 'mk') for p, n in pairs}
        return (person, symbol(state)) in pairs and scene == ('ordinary' if fault_variant == 'other_context' else 'anchor')
    result['hziq'] = fault
    return result


def motive_checks():
    doc = motive_document();rows = []
    variants = ('baseline', 'all_occasions', 'only_exception', 'incomparable', 'reversed', 'cycle', 'reflexive',
        'other_factor', 'other_person', 'other_anchor', 'empty_scope', 'no_reason', 'other_action', 'missing_effort', 'missing_fear')
    for variant in variants:
        raw = [True, True] if variant in ('baseline', 'all_occasions') else [False, True] if variant == 'missing_effort' \
            else [True, False] if variant == 'missing_fear' else [False, False]
        for faults in product((False, True), repeat=2):
            expected = [x for fact, fault in zip(raw, faults, strict=True) for x in (fact, fact and fault, fact and fault, fact and fault)]
            actual = evaluate(doc, values(variant, faults))
            assert actual == expected, (variant, faults, actual)
            rows.append(dict(disposition=variant, faults=list(faults), values=actual))
    contrasts = {}
    for variant in ('baseline', 'other_person', 'other_state', 'qualified_state', 'other_context'):
        contrasts[variant] = evaluate(doc, values(fault_variant=variant))
        assert contrasts[variant] == ([True] * 8 if variant == 'baseline' else [True, False, False, False] * 2)
    outside = evaluate(doc, values('outside_group'))
    assert outside == [True, True, True, False] * 2
    # An absent/unknown evaluation is not an exoneration or a condemnation.
    for name in ('hziq', 'hzwm', 'mh', 'me', 'mb', 'mc'):
        v = values();v[name] = unknown
        try:
            evaluate(doc, v)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(combinations=rows, binding_contrasts=contrasts, outside_group=outside,
        unknown_inputs_refused=6, ordinary_evaluation=True, actual_episode_and_group_definitions_executed=True,
        generic_and_static_specializations_agree=True,
        unblamed_rest_and_prudence_not_classified=True,
        moral_correctness_of_supplied_evaluations_not_proved=True)


def generic_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8'))
    # Arbitrary property unrelated to avoidance: the qualifier is reusable.
    doc = parse(format_graph(doc, 'compact') + 'r jperson[] a.r jscene[] d.r jstate[a d] c.' +
        'd jproperty[person a] e[b scene[k jstate[v person v scene]]].' +
        'q[k rqxd[k jperson[] r[p jproperty] k jscene[]]].')
    rows = []
    for actual, blamed in product((False, True), repeat=2):
        v = dict(jperson=lambda: 'alice', jscene=lambda: 'anchor',
            jstate=lambda person, scene: actual and (person, scene) == ('alice', 'anchor'),
            hziq=lambda person, state, scene: blamed and (person, symbol(state), scene) == ('alice', 'jproperty', 'anchor'))
        result = evaluate(doc, v, ('alice', 'bob'), ('anchor', 'ordinary'))
        assert result == [actual and blamed]
        rows.append(dict(actual=actual, blamed=blamed, result=result))
    # Same person/state at two evaluation contexts can receive opposed judgments.
    v['jstate'] = lambda person, scene: person == 'alice'
    a = evaluate(doc, v, ('alice', 'bob'), ('anchor', 'ordinary'))
    v['jscene'] = lambda: 'ordinary'
    b = evaluate(doc, v, ('alice', 'bob'), ('anchor', 'ordinary'))
    assert (a, b) == ([True], [False])
    return dict(combinations=rows, unrelated_property=True, context_dependent_evaluation=True)


def attribution_checks():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    rows = {};seen = []
    for variant in ('baseline', 'other_author', 'other_node', 'other_content', 'other_scene', 'reverse_order'):
        def claims(node, author, content, scene):
            seen.append(json.loads(content.syntax))
            return (node, author, symbol(content), scene) == (
                'other' if variant == 'other_node' else 'cause', 'other' if variant == 'other_author' else 'author',
                'ol' if variant == 'other_content' else 'mx', 'other' if variant == 'other_scene' else 'text')
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        v.update(mw=lambda: 'cause', wa=lambda: 'author', wh=lambda: 'text', wg=lambda: 'opening', uc=claims,
            ue=lambda first, second, scene: (first, second, scene) == (
                ('cause', 'opening', 'text') if variant == 'reverse_order' else ('opening', 'cause', 'text')))
        rows[variant] = evaluate(doc, v, ('author', 'cause', 'opening', 'other'), ('text',))
        assert rows[variant] == [variant == 'baseline']
    assert seen and all(s == {'kind': 'call', 'symbol': 'mx', 'arguments': []} for s in seen)
    return dict(contrasts=rows, all_dispositions_faults_and_causes_left_unknown=True,
        source_quote_rank_preserved=True, ordinary_evaluation=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 42
    assert set(new.entries) - set(old.entries) == {'rqxb', 'rqxc', 'rqxd'}
    changed = [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']]
    assert set(changed) == {'mj', 'mk'}
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n not in MEANINGS)
    for before, after in [('mj', 'rqxb'), ('mk', 'rqxc')]:
        row = deepcopy(old.entries[before]['declaration']);row['name'] = after
        assert row == new.entries[after]['declaration']
    affected = [i for i, s in enumerate(new.document['statements']) if set(changed) &
        {d['name'] for d in closure(new.document, _references(s))}]
    assert affected == [2], affected
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review = json.loads((ROOT / path).read_text(encoding='utf-8'))
        indices = [r['index'] for r in review['selection']['statements']]
        before, after = selection_binding(old, indices), selection_binding(new, indices)
        assert before == review['selection'] and before['statements'] == after['statements']
        assert before['dependencies'] == after['dependencies'] and 2 not in indices
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in before['dependencies'])
    for name, body in build().items():
        assert (ROOT / name).read_text(encoding='utf-8') == body, name
    for name in (FULL, CORE, LIBRARY):
        d = parse((ROOT / name).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(d, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    return dict(preserved_statements=42, changed_definitions=sorted(changed), affected_statements=affected,
        new_definitions=3, new_primitive_relations=0, preserved_review_meanings=11, roundtrips=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    stop = unit['text'].index('Es ist so bequem')
    return dict(status='evaluative_motive_reading_not_whole_paragraph_review', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[0, stop], text=unit['text'][:stop]),
        consulted='https://korpora.org/Kant/aa08/035.html',
        findings=['旧mj・mkは労力・恐れによる回避傾向だけなので、その評価がない休息や慎重な回避も要因の候補にする。'],
        decisions=['原文第一段落の自分の落ち度と勇気への訴え、第二段落の他者に委ねる批判に接続する読みとして、傾向と帰責を結ぶ。唯一の辞書的意味とはしない。',
            '既存hziqを再利用し、新しい語専用の基本関係を追加しない。評価基準は同じ評価状況に保持し、因果内容全体はucで著者へ帰属する。',
            '傾向はrqxb・rqxcとして保存する。評価のない傾向を記述する能力は失わない。汎用rqxdと本文の固定特殊化を区別する。'],
        remaining=['程度・関連行為の範囲・通常性の文脈的選択と、語義全体の確認',
            '自然による解放・生涯・容易さ、第二段落の名詞・比喩・作用範囲と全体の意味確認'],
        whole_unit_semantically_verified=False,
        test_limit='検査は与えた傾向と帰責の解釈の組合せを確かめる。人物の落ち度の正しさ、原文の唯一の解釈、因果機構を証明しない。',
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in (inv, PARENT, PARENT_BASIS,
            'data/motive-causes-reading-v1.json', 'docs/motive-causes-v1.md')})


def build_report():
    results = {}
    for name, fn in [('motives', motive_checks), ('generic', generic_checks), ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn();print(name + ' checked', flush=True)
    reading = audit()
    assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == reading
    paths = set(build()) | set(parent().source_sha256) | set(reading['source_sha256']) | {AUDIT, INDEX, DOC,
        'scripts/compose_evaluated_motives.py', 'scripts/check_evaluated_motives.py', 'tests/test_evaluated_motives.py',
        'scripts/check_motive_causes.py', 'scripts/compose_motive_causes.py', 'scripts/check_designation_order.py',
        'scripts/compose_falling_depiction.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    source = reading['source']
    return dict(status='partial_contextually_evaluated_motives', document=FULL, **results,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'], source=source['text'],
            definitions=['rqxb', 'rqxc', 'rqxd', 'mj', 'mk', 'mq', 'mr', 'mx'],
            status='explicit_interpretive_annotation', full_semantic_equivalence=False),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit()))
    write_exact(ROOT / REPORT, encoded(build_report()))
    print('Evaluative motives checked without new primitives', flush=True)


if __name__ == '__main__':
    main()
