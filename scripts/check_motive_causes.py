"""Check normal-case motives and distinguish actual causes from adopted ones."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document, SequenceValue
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts.compose_motive_causes import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, build, parent, closure
from scripts.check_designation_order import substantive

REPORT = 'reports/motive-causes-v1.json'
AUDIT = 'data/motive-causes-reading-v1.json'
INDEX = 'data/semantic-review-index-v39.json'
DOC = 'docs/motive-causes-v1.md'
DOMAIN = ('group', 'alice', 'bob', 'act', 'otheract')
SCENES = ('anchor', 'ordinary', 'exception')


def unknown(*args):
    raise ValueError('Unknown motive-cause interpretation')


def symbol(value):
    return json.loads(value.syntax)['symbol']


def evaluate(doc, values, individuals=DOMAIN, scenes=SCENES):
    return [r['value'] for r in evaluate_document(doc, individuals=individuals, situations=scenes,
        primitives={d['name']: values[d['name']] for d in doc['declarations'] if d['kind'] == 'primitive'},
        max_steps=3000000, memoize_definitions=False, memoize_expressions=False)]


@lru_cache(None)
def motive_document(legacy=False):
    doc = deepcopy(parent().document) if legacy else parse((ROOT / FULL).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc, ['mq', 'mr', 'mv', 'wh'])
    doc['statements'] = []
    return parse(format_graph(doc, 'compact') + 'q[t[k mq[k mv[]]][k wh[]]].q[t[k mr[k mv[]]][k wh[]]].')


def motive_values(variant='baseline'):
    def reason(person, act, description, scene):
        return (person, symbol(description)) in {('alice', 'mb'), ('bob', 'mc')} and act == 'act' and scene in SCENES[1:]
    def normal(person, factor, anchor, first, second):
        pairs = {('alice', 'mc'), ('bob', 'mb')} if variant == 'other_factor' else {('alice', 'mb'), ('bob', 'mc')}
        if variant == 'other_person':
            pairs = {('group', 'mb'), ('group', 'mc')}
        if (person, symbol(factor)) not in pairs or anchor != ('ordinary' if variant == 'other_anchor' else 'anchor'):
            return False
        edges = set() if variant == 'incomparable' else {('exception', 'ordinary')} if variant == 'reversed' else {('ordinary', 'exception')}
        if variant == 'cycle':
            edges.add(('exception', 'ordinary'))
        if variant == 'reflexive':
            edges.add(('ordinary', 'ordinary'))
        return (first, second) in edges
    values = dict(mv=lambda: 'group', wh=lambda: 'anchor',
        mp=lambda group: SequenceValue(() if variant == 'outside_group' else ('alice', 'bob'), '"individual"'),
        aa=lambda p: p in ('alice', 'bob'),
        ma=lambda p, a, s: p in ('alice', 'bob') and a == 'act' and s in SCENES[1:],
        mb=lambda p, a, s: (p, a) == ('alice', 'act'),
        mc=lambda p, a, s: (p, a) == ('bob', 'act'),
        md=lambda p, a, s: p in ('alice', 'bob') and a == 'act' and
            (variant == 'all_occasions' or s == ('exception' if variant == 'only_exception' else 'ordinary')),
        me=reason,
        mh=lambda p, base, s: variant != 'empty_scope' and p in ('alice', 'bob') and base == 'anchor' and s in SCENES[1:],
        hzwm=normal)
    if variant == 'no_reason':
        values['me'] = lambda *args: False
    if variant == 'other_action':
        values['me'] = lambda p, act, desc, s: act == 'otheract'
    if variant == 'missing_effort':
        values['mb'] = lambda *args: False
    if variant == 'missing_fear':
        values['mc'] = lambda *args: False
    return values


def motive_checks():
    new, old = motive_document(), motive_document(True)
    assert evaluate(old, motive_values()) == [False, False]
    assert evaluate(new, motive_values()) == [True, True]
    assert evaluate(old, motive_values('all_occasions')) == [True, True]
    rows = {}
    for variant in ('baseline', 'all_occasions', 'only_exception', 'incomparable', 'reversed', 'cycle', 'reflexive',
        'other_factor', 'other_person', 'other_anchor', 'outside_group', 'empty_scope', 'no_reason', 'other_action',
        'missing_effort', 'missing_fear'):
        expected = [True, True] if variant in ('baseline', 'all_occasions') else [False, True] if variant == 'missing_effort' \
            else [True, False] if variant == 'missing_fear' else [False, False]
        rows[variant] = evaluate(new, motive_values(variant))
        assert rows[variant] == expected, (variant, rows[variant])
    for name in ('hzwm', 'mh', 'me', 'mb', 'mc'):
        values = motive_values();values[name] = unknown
        try:
            evaluate(new, values)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, prior_all_occasions_rejects_exception=True, distinct_people_and_motives=True,
        actual_mf_mg_mj_mk_mq_mr_executed=True, unknown_inputs_refused=5, ordinary_evaluation=True)


@lru_cache(None)
def causal_document(factors=('mq', 'mr'), results=('ms', 'ok')):
    doc = parse((ROOT / FULL).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc, ['rqxa', 'na'])
    doc['statements'] = []
    text = format_graph(doc, 'compact') + 'r jgroup[] a.r jscene[] d.'
    for name in ('mq', 'mr', 'ms', 'ok'):
        text += 'r j' + name + '[a d] c.d ' + name + '[subject a] e[b scene[k j' + name + '[v subject v scene]]].'
    base = parse(text)
    # Use the actual stored old and revised outer compositions. The four
    # content properties in THIS isolated fixture have explicit interpretations;
    # it does not pretend to re-evaluate the entire population/ease manuscript.
    for n in ('mt', 'mu', 'ol'):
        row = deepcopy(parent().entries[n]['declaration'])
        if n == 'ol':
            row['name'] = 'zlegacy'
        base['declarations'].append(row)
    revised = deepcopy(load_catalog(ROOT, BASIS).entries['ol']['declaration'])
    revised['name'] = 'zrevised';base['declarations'].append(revised)
    seq = lambda names: 'l[i[h[a] e]][' + ' '.join('r[p ' + n + ']' for n in names) + ']'
    return parse(format_graph(base, 'compact') + 'q[k rqxa[k jgroup[] ' + seq(factors) + ' k jgroup[] ' + seq(results) + ' k jscene[]]].' +
        'q[k zrevised[k jgroup[] k jscene[]]].q[k zlegacy[k jgroup[] k jscene[]]].')


def causal_values(bits=(True,) * 8, variant='baseline'):
    values = dict(jgroup=lambda: 'group', jscene=lambda: 'anchor', ea=lambda *args: variant != 'no_adoption')
    for name, bit in zip(('mq', 'mr', 'ms', 'ok'), bits[:4], strict=True):
        values['j' + name] = lambda subject, scene, bit=bit: bit and (subject, scene) == ('group', 'anchor')
    pairs = list(product(('mq', 'mr'), ('ms', 'ok')))
    links = {pair for pair, bit in zip(pairs, bits[4:], strict=True) if bit}
    def cause(source, factor, target, result, scene):
        expected = ['group', 'group', 'anchor']
        if variant == 'other_source': expected[0] = 'alice'
        if variant == 'other_target': expected[1] = 'bob'
        if variant == 'other_scene': expected[2] = 'ordinary'
        pair = (symbol(factor), symbol(result))
        if variant == 'reversed': pair = pair[::-1]
        return [source, target, scene] == expected and pair in links
    values['hzie'] = cause
    return values


def causal_checks():
    doc = causal_document();count = 0
    for bits in product((False, True), repeat=8):
        actual = evaluate(doc, causal_values(bits), ('group', 'alice', 'bob'), ('anchor',))
        assert actual == [all(bits), all(bits), True], (bits, actual)
        count += 1
    contrasts = {}
    for variant in ('baseline', 'other_source', 'other_target', 'other_scene', 'reversed', 'no_adoption'):
        contrasts[variant] = evaluate(doc, causal_values(variant=variant), ('group', 'alice', 'bob'), ('anchor', 'ordinary'))
        assert contrasts[variant] == ([True, True, False] if variant == 'no_adoption' else
            [True, True, True] if variant == 'baseline' else [False, False, True])
    for factors, results in (((), ('ms', 'ok')), (('mq', 'mr'), ()), ((), ())):
        assert evaluate(causal_document(factors, results), causal_values(), ('group',), ('anchor',)) == [False, True, True]
    for name in ('hzie', 'jmq', 'jmr', 'jms', 'jok'):
        values = causal_values();values[name] = unknown
        try:
            evaluate(doc, values, ('group',), ('anchor',))
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    separate = deepcopy(doc);separate['statements'] = []
    separate['declarations'].append(dict(kind='primitive', name='jtarget', parameters=[], result='individual'))
    text = format_graph(separate, 'compact')
    for source, target in (('jgroup', 'jtarget'), ('jtarget', 'jgroup')):
        text += 'q[k rqxa[k ' + source + '[] l[i[h[a] e]][r[p mq] r[p mr]] k ' + target + \
            '[] l[i[h[a] e]][r[p ms] r[p ok]] k jscene[]]].'
    separate = parse(text)
    values = causal_values();values['jtarget'] = lambda: 'bob'
    for n in ('ms', 'ok'):
        values['j' + n] = lambda subject, scene: (subject, scene) == ('bob', 'anchor')
    values['hzie'] = lambda source, factor, target, result, scene: (source, target, scene) == ('group', 'bob', 'anchor') \
        and symbol(factor) in ('mq', 'mr') and symbol(result) in ('ms', 'ok')
    assert evaluate(separate, values, ('group', 'bob'), ('anchor',)) == [True, False]
    return dict(combinations=count, contrasts=contrasts, empty_factor_or_result_lists_refused=3,
        unknown_inputs_refused=5, ordinary_evaluation=True, actual_outer_source_definitions_executed=True,
        four_content_properties_explicitly_abstracted=True, complete_population_and_ease_semantics_reverified=False,
        direct_specialization_matches_general_condition=True, causal_adoption_not_enough=True,
        distinct_cause_and_effect_subjects_checked=True)


def attribution_checks():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    rows = {};seen = []
    for variant in ('baseline', 'other_author', 'other_node', 'other_content', 'other_scene', 'reverse_order'):
        def claims(node, author, content, scene):
            seen.append(json.loads(content.syntax))
            return (node, author, symbol(content), scene) == (
                'other' if variant == 'other_node' else 'cause', 'other' if variant == 'other_author' else 'author',
                'ol' if variant == 'other_content' else 'mx', 'other' if variant == 'other_scene' else 'text')
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(mw=lambda: 'cause', wa=lambda: 'author', wh=lambda: 'text', wg=lambda: 'opening', uc=claims,
            ue=lambda first, second, scene: (first, second, scene) == (
                ('cause', 'opening', 'text') if variant == 'reverse_order' else ('opening', 'cause', 'text')))
        rows[variant] = evaluate(doc, values, ('author', 'cause', 'opening', 'other'), ('text',))
        assert rows[variant] == [variant == 'baseline']
    assert seen and all(s == {'kind': 'call', 'symbol': 'mx', 'arguments': []} for s in seen)
    return dict(contrasts=rows, all_causal_and_motive_facts_left_unknown=True,
        source_quote_rank_preserved=True, ordinary_evaluation=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 42
    assert set(new.entries) - set(old.entries) == {'rqxa', 'hzwm'}
    changed = [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']]
    assert set(changed) == {'mj', 'mk', 'ol'}
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n not in MEANINGS)
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
        new_definitions=1, new_primitive_relations=1, preserved_review_meanings=11, roundtrips=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    stop = unit['text'].index('Es ist so bequem')
    return dict(status='two_semantic_defects_in_first_sentence_repaired_not_whole_paragraph_review', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[0, stop], text=unit['text'][:stop]),
        consulted='https://korpora.org/Kant/aa08/035.html',
        findings=['旧mj・mkは全ての評価機会で回避を要求し、通常の回避傾向に例外がある場合を排除していた。',
            '旧olは二要因と二結果への説明の採用を要求するだけで、内容の成立や実際の因果的寄与を主張する条件になっていなかった。'],
        decisions=['非数値の通常性比較rqt4を再利用し、本人・要因記述・基準文脈を保持する。',
            '原文の原因であるという主張をrqquとhzieの意味に合わせる。本文は著者への帰属なので、主張の現実の真理をアシスタントが認定しない。',
            '引用可能性を保つため、固定した四内容への因果条件を脱引用のない形へ特殊化する。'],
        resolved_old_obligations=['motive_meaningsの全機会必須という過強な条件', '原因の主張と説明への採用の混同'],
        remaining=['怠惰・臆病の程度と規範的評価、候補と通常性の文脈的な選び方',
            '自然による解放・ラテン語・長期性、好みと生涯、容易さと後見の語義・作用範囲',
            '書物・宗教上の助言者・医師、支払いの焦点、女性についての挿入句、皮肉、身体的描写を含む第二段落全体の意味確認'],
        whole_unit_semantically_verified=False,
        test_limit='因果の一般形と現行olの固定特殊化は、四内容に明示的な解釈を与える検査で照合する。割合・自然による解放・容易さの全定義を今回一括して実行検証したとはしない。',
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in (inv, PARENT, PARENT_BASIS,
            'reports/caused-conditions-v1.json', 'docs/motive-explanations-v1.md', 'docs/easy-roles-v1.md')})


def build_report():
    results = {}
    for name, fn in [('motives', motive_checks), ('causality', causal_checks), ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn();print(name + ' checked', flush=True)
    reading = audit()
    assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == reading
    paths = set(build()) | set(parent().source_sha256) | set(reading['source_sha256']) | {AUDIT, INDEX, DOC,
        'scripts/compose_motive_causes.py', 'scripts/check_motive_causes.py', 'tests/test_motive_causes.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    source = reading['source']
    return dict(status='partial_normal_motives_and_actual_causal_claim', document=FULL, **results,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'], source=source['text'],
            definitions=['mj', 'mk', 'mq', 'mr', 'rqxa', 'ol', 'mx'], status='explicit_interpretive_annotation', full_semantic_equivalence=False),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit()))
    write_exact(ROOT / REPORT, encoded(build_report()))
    print('Normal motive dispositions and actual causal claim checked', flush=True)


if __name__ == '__main__':
    main()
