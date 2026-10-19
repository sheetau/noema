"""Check actual causal contribution, its judgment scope and preserved claims."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_guardian_causation import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, parent, build, closure
from scripts.check_scoped_groups import source_model as previous_values, PEOPLE, SCENES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_guardian_causation_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v61.json'
REPORT = 'reports/guardian-causation-v1.json'
AUDIT = 'data/guardian-causation-reading-v1.json'
DOC = 'docs/guardian-causation-v1.md'


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def causal_checks():
    d = deepcopy(catalog().document); d.update(declarations=closure(d, ['rqqu', 'ec']), statements=[])
    d = parse(format_graph(d, 'compact') + '''r ja[] a.r jb[] a.r js[] d.r jp[a d] c.r jq[a d] c.
d jfactor[person a] e[b scene[k jp[v person v scene]]].
d jresult[person a] e[b scene[k jq[v person v scene]]].
q[k rqqu[k ja[] r[p jfactor] k jb[] r[p jresult] k js[]]].
q[k ec[k ja[] r[p jfactor] k jb[] r[p jresult] k js[]]].''')
    rows = []
    for factor, result, cause, adoption in product((False, True), repeat=4):
        key = ('source', 'jfactor', 'target', 'jresult', 'now')
        v = dict(ja=lambda: 'source', jb=lambda: 'target', js=lambda: 'now',
            jp=lambda p, s: factor and (p, s) == ('source', 'now'), jq=lambda p, s: result and (p, s) == ('target', 'now'),
            hzie=lambda a, p, b, q, s: cause and (a, symbol(p), b, symbol(q), s) == key,
            ea=lambda a, p, b, q, s: adoption and (a, symbol(p), b, symbol(q), s) == key)
        actual = evaluate(d, v, ('source', 'target'), ('now',))
        assert actual == [factor and result and cause, factor and result and adoption]
        rows.append(dict(factor=factor, result=result, cause=cause, adoption=adoption, values=actual))
    return dict(combinations=rows, existing_causal_relation_reused=True, ordinary_evaluation=True)


def majority_checks():
    d = deepcopy(catalog().document); d.update(declarations=closure(d, ['rqyc']), statements=[])
    d = parse(format_graph(d, 'compact') + '''r jp[] j[a].r js[] d.r jq[a d] c.
d jselected[person a] e[b scene[k jq[v person v scene]]].
q[t[k rqyc[k jp[] p jselected]][k js[]]].''')
    people = ('one', 'two', 'three', 'four')
    def values(population, selected, threshold, recognized=True, human=True):
        return dict(jp=lambda: SequenceValue(tuple(population), '"individual"'), js=lambda: 'now',
            jq=lambda p, s: p in selected and s == 'now', aa=lambda p: human and p in people,
            hr=lambda p, s: recognized and s == 'now', u4=lambda q, s: q >= threshold and s == 'now',
            ha=lambda a, b: a+b, hb=lambda a, b: a*b, hc=lambda a, b: a<b,
            hd=lambda b: Fraction(int(b)), pa=lambda a, b: a/b if b else Fraction(0))
    rows = []
    for bits, recognized, threshold in product(product((False, True), repeat=4), (False, True), (Fraction(1, 2), Fraction(3, 4))):
        selected = {p for p, flag in zip(people, bits) if flag}; share = Fraction(len(selected), 4)
        actual = evaluate(d, values(people, selected, threshold, recognized), people, ('now',))[0]
        assert actual == (recognized and share > Fraction(1, 2) and share >= threshold)
        rows.append(dict(selected=list(bits), recognized=recognized, threshold=str(threshold), value=actual))
    invalid = {}
    for name, pop, human in [('empty', (), True), ('duplicate', ('one', 'one', 'two', 'three'), True), ('nonhuman', people, False)]:
        actual = evaluate(d, values(pop, set(people), Fraction(1, 2), human=human), people, ('now',))[0]
        assert not actual; invalid[name] = actual
    for name in ('hr', 'u4', 'jq'):
        v = values(people, set(people), Fraction(1, 2)); v[name] = unknown
        try: evaluate(d, v, people, ('now',))
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    return dict(combinations=rows, invalid_populations=invalid, unknown_inputs_refused=3, property_is_an_argument=True)


@lru_cache(None)
def questions():
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, ['dk', 'dl', 'dn', 'rqyd', 'do', 'rqyb', 'uw', 'uy', 'db', 'mv']), statements=[])
    text = format_graph(d, 'compact') + 'r za[] a.r zb[] a.r zc[] d.'
    for n, arg in [('dk', 'db'), ('dl', 'db'), ('dn', 'mv'), ('rqyd', 'mv'), ('do', 'db'), ('rqyb', 'db')]:
        text += 'q[t[k ' + n + '[k ' + arg + '[]]][k zc[]]].'
    text += 'q[t[k uw[k zb[]]][k zc[]]].q[t[k uy[k zb[]]][k zc[]]].'
    return parse(text)


def source_values(variant='baseline'):
    base = 'no_causal_adoption' if variant in ('no_adoption', 'both_absent') else variant
    v = previous_values(questions(), base)
    old_members = v['mp']
    v['mp'] = lambda group: SequenceValue(old_members(group).items, '"individual"')
    key = ['guards', 'dl', 'population', 'rqyd', 'actual']
    replacements = {'cause_wrong_group': (0, 'population'), 'cause_wrong_factor': (1, 'dk'),
        'cause_wrong_target': (2, 'guards'), 'cause_wrong_result': (3, 'dn'), 'cause_wrong_context': (4, 'belief')}
    if variant in replacements:
        i, value = replacements[variant]; key[i] = value
    if variant == 'cause_reversed': key = ['population', 'rqyd', 'guards', 'dl', 'actual']
    v['hzie'] = lambda a, p, b, q, s: variant not in ('no_causation', 'both_absent') and (a, symbol(p), b, symbol(q), s) == tuple(key)
    if variant == 'no_burden': v['uu'] = lambda *args: Fraction(1)
    if variant == 'no_judgment': v['u2'] = lambda *args: False
    if variant == 'unrecognized_population': v['hr'] = lambda *args: False
    return v


def source_checks():
    variants = ('baseline', 'actual_danger', 'female_not_judging', 'female_outside_population', 'empty_female_class',
        'empty_guards', 'duplicate_guard', 'uncovered_target', 'irrelevant_guard', 'nonhuman_guard', 'no_current_role',
        'not_prior', 'wrong_assumption_act', 'claimed_only', 'separate_activities', 'no_activity',
        'no_adoption', 'no_causation', 'both_absent', 'cause_wrong_group', 'cause_wrong_factor', 'cause_wrong_target',
        'cause_wrong_result', 'cause_wrong_context', 'cause_reversed', 'no_burden', 'no_judgment', 'unrecognized_population')
    rows = {}
    for variant in variants:
        actual = evaluate(questions(), source_values(variant), PEOPLE, SCENES, True)
        current = variant in ('baseline', 'actual_danger', 'no_adoption')
        old = variant in ('baseline', 'actual_danger', 'no_causation') or variant.startswith('cause_')
        assert actual[4:6] == [current, old], (variant, actual)
        assert actual[6] == (variant == 'actual_danger')
        if variant == 'no_burden': assert actual[2:4] == [False, True] and not actual[7]
        if variant == 'no_judgment': assert actual[2:4] == [False, False] and actual[7]
        rows[variant] = actual
    d = deepcopy(questions()); d['statements'] = d['statements'][4:6]
    d['declarations'] = closure(d, _references(d['statements']))
    # Ordinary evaluation expands nested contents across every situation. Use a
    # separate finite model with one human in each group and one belief/outcome
    # situation; execute the same declarations, without replacing definitions.
    small_people = ('person', 'guardone', 'population', 'guards', 'appointment', 'activity', 'low', 'high')
    small_scenes = ('actual', 'belief', 'prior')
    ordinary = {}
    for variant in ('baseline', 'no_causation', 'no_adoption'):
        v = source_values(variant)
        v.update(mp=lambda group: SequenceValue(('person',) if group == 'population' else
                ('guardone',) if group == 'guards' else (), '"individual"'),
            aa=lambda person: person in ('person', 'guardone'),
            hr=lambda population, scene: population.items == ('person',) and scene == 'actual',
            uq=lambda person, description, context, outcome: person == 'person' and symbol(description) == 'up'
                and context in ('actual', 'belief') and outcome == 'belief',
            ur=lambda person, scene: (person, scene) == ('person', 'belief'))
        cached = evaluate(d, v, small_people, small_scenes, True)
        plain = evaluate(d, v, small_people, small_scenes)
        assert plain == cached == rows[variant][4:6]
        ordinary[variant] = dict(ordinary=plain, memoized=cached)
    for name in ('hzie', 'df', 'dg', 'u2', 'u4'):
        v = source_values(); v[name] = unknown
        try: evaluate(d, v, PEOPLE, SCENES, True)
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    return dict(contrasts=rows, current_definitions_executed=True, ordinary_comparisons=ordinary,
        ordinary_domain=dict(individuals=list(small_people), situations=list(small_scenes),
            population_size=1, guardian_count=1, belief_also_prospective_outcome=True),
        unknown_inputs_refused=5, actual_danger_not_required=True, burden_excluded_from_causal_result=True)


def specialization_checks():
    d = deepcopy(catalog().document); d.update(declarations=closure(d, ['u5', 'rqyc', 'mp', 'mv']), statements=[])
    d = parse(format_graph(d, 'compact') + 'r zc[] d.q[t[k u5[k mp[k mv[]]]][k zc[]]].q[t[k rqyc[k mp[k mv[]] p uz]][k zc[]]].')
    rows = {}
    for variant in ('baseline', 'female_not_judging', 'no_burden', 'no_judgment', 'unrecognized_population'):
        actual = evaluate(d, source_values(variant), PEOPLE, SCENES, True)
        assert actual[0] == actual[1]; rows[variant] = actual
    return dict(contrasts=rows, previous_joint_predicate_reproduced=True)


def attribution_checks():
    d = parse((ROOT / CORE).read_text(encoding='utf-8')); rows = {}
    for variant in ('baseline', 'other_node', 'other_author', 'other_content', 'other_context', 'reversed_order'):
        v = {x['name']: unknown for x in d['declarations'] if x['kind'] == 'primitive'}
        v.update(dq=lambda: 'guardians', wa=lambda: 'author', t4=lambda: 'payment', wh=lambda: 'text',
            uc=lambda n, a, p, s: (n, a, symbol(p), s) == (
                'other' if variant == 'other_node' else 'guardians', 'other' if variant == 'other_author' else 'author',
                'un' if variant == 'other_content' else 'dp', 'actual' if variant == 'other_context' else 'text'),
            ue=lambda a, b, s: (a, b, s) == (('guardians', 'payment', 'text') if variant == 'reversed_order' else ('payment', 'guardians', 'text')))
        actual = evaluate(d, v, ('guardians', 'payment', 'author', 'other'), ('text', 'actual'))
        assert actual == [variant == 'baseline']; rows[variant] = actual
    return dict(contrasts=rows, causal_burden_judgment_and_gender_facts_unknown=True)


def structure():
    old, new = parent(), catalog()
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 44
    assert set(new.entries) - set(old.entries) == {'rqyb', 'rqyc', 'rqyd'}
    assert [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']] == ['do']
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n != 'do')
    saved = deepcopy(old.entries['do']['declaration']); saved['name'] = 'rqyb'
    assert new.entries['rqyb']['declaration'] == saved
    affected = [i for i, s in enumerate(new.document['statements']) if 'do' in {d['name'] for d in closure(new.document, _references(s))}]
    assert affected == [7]
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review = json.loads((ROOT / path).read_text(encoding='utf-8')); ids = [s['index'] for s in review['selection']['statements']]
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a == review['selection'] and a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in a['dependencies'])
    for ids in ([2, 3], [4, 42], [6], [5, 43]):
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in a['dependencies'])
    for path, text in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == text
    for path in (FULL, CORE, LIBRARY):
        d = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(d, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    return dict(preserved_statements=44, changed_definitions=['do'], affected_statements=affected,
        new_primitives=0, new_definitions=3, preserved_review_meanings=11,
        preceding_four_sentence_meanings_preserved=True, roundtrips=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    u = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    start = u['text'].index('den Schritt zur Mündigkeit,'); end = u['text'].index('Nachdem')
    text = u['text'][start:end].rstrip()
    paths = (PARENT, PARENT_BASIS, INDEX, inv, EVIDENCE, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'reports/scoped-groups-v1.json', 'docs/scoped-groups-v1.md', 'reports/motive-causes-v1.json')
    return dict(status='actual_contribution_and_judgment_result_separated_not_whole_sentence_review', reviewer='assistant_review',
        source=dict(unit=u['id'], unit_sha256=u['text_sha256'], range=[start, start+len(text)], text=text),
        reading='後見人の働きかけが、人々が成熟への一歩を危険だと判断することへ実際に寄与するという結果の読みを採る。負担の挿入説明は原因の対象と分ける。',
        counterexample='旧doでは集団の活動と結果が同時にあり、原因説明へ採用されるだけで足りた。実際の寄与がない場合も真になった。',
        decisions=['実際の因果的寄与hzieを再利用し、新たな基本関係は作らない。',
            '危険判断uxだけの分布rqydを因果結果へ渡す。負担を含むdnは別の事実条件として保持する。',
            '一般化した割合の定義rqycは性質を引数に取り、元のuzを渡した場合のu5との一致を検査する。',
            '著者による帰属と内容の真理は分け、現実の歴史的因果が検証されたとはしない。'],
        evidence_limit='歴史辞典のsorgenには実現へ向けて配慮・手配する用法があり、試みの意味もある。動詞だけから成功を必然とするものではなく、今回の結果の読みは本文の前後に対する解釈である。目的的な働きかけの条件は未完。',
        remaining=['目的的な働きかけと因果的寄与の接続', 'gütigstの評価とschon・auchの焦点、監督の意味',
            '当該文と第二段落全体、二作品全文の意味確認'],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    results = {}
    for name, fn in [('causal', causal_checks), ('majority', majority_checks), ('source', source_checks),
            ('specialization', specialization_checks), ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = audit(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == r
    validate_hashes(ROOT, r['source_sha256'])
    paths = set(build()) | set(parent().source_sha256) | set(r['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_guardian_causation.py', 'scripts/check_guardian_causation.py', 'scripts/register_guardian_causation.py',
        'scripts/fetch_guardian_causation_evidence.py', 'tests/test_guardian_causation.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_scoped_groups.py', 'scripts/check_described_appraisals.py', 'scripts/check_described_explanations.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/check_designation_order.py',
        'scripts/compose_falling_depiction.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='guardians_actual_causal_contribution_to_judgments', document=FULL, **results,
        alignment=dict(**r['source'], definitions=['rqyb', 'rqyc', 'rqyd', 'do', 'dp'], status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit())); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__': main()
