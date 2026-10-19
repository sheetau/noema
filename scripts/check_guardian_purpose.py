"""Check intended action independently of success, then bind its causal witness."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_guardian_purpose import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, parent, build, closure
from scripts.check_guardian_causation import source_values as previous_values, PEOPLE, SCENES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_guardian_causation_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v62.json'
REPORT = 'reports/guardian-purpose-v1.json'
AUDIT = 'data/guardian-purpose-reading-v1.json'
DOC = 'docs/guardian-purpose-v1.md'


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def goal_key(description):
    node = json.loads(description.syntax)
    assert node['kind'] == 'call' and len(node['arguments']) == 1
    target = node['arguments'][0]
    assert target['kind'] == 'call' and target['arguments'] == []
    return node['symbol'], target['symbol']


def purpose_checks():
    d = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r ja[] a.r js[] d.r jactors[a] c.r occurs[a d] c.r performs[a a d] c.r aims[a a i[e] d] c.
r truth[d] c.d jgoal[] e[b scene[k truth[v scene]]].
q[k rqyf[p jactors k ja[] r[k jgoal[]] k js[] p occurs p performs p aims]].''')
    rows = []
    for occurs, first, second, aim_first, aim_second in product((False, True), repeat=5):
        def aims(actor, act, goal, scene):
            assert json.loads(goal.syntax) == {'kind': 'call', 'symbol': 'jgoal', 'arguments': []}
            return (act, scene) == ('work', 'now') and {'one': aim_first, 'two': aim_second}.get(actor, False)
        v = dict(ja=lambda: 'work', js=lambda: 'now', jactors=lambda a: a in ('one', 'two'),
            occurs=lambda a, s: occurs and (a, s) == ('work', 'now'),
            performs=lambda a, act, s: (act, s) == ('work', 'now') and {'one': first, 'two': second}.get(a, False),
            aims=aims, truth=unknown)
        actual = evaluate(d, v, ('one', 'two', 'work'), ('now',))
        assert actual == [all((occurs, first, second, aim_first, aim_second))]
        rows.append(dict(bits=[occurs, first, second, aim_first, aim_second], values=actual))
    v['jactors'] = lambda a: False
    assert evaluate(d, v, ('one', 'two', 'work'), ('now',)) == [False]
    v['jactors'] = lambda a: a in ('one', 'two')
    for name in ('occurs', 'performs', 'aims'):
        uncertain = dict(v); uncertain[name] = unknown
        try: evaluate(d, uncertain, ('one', 'two', 'work'), ('now',))
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    return dict(combinations=rows, goal_truth_unknown_and_not_executed=True, empty_group_rejected=True,
        unknown_inputs_refused=3, ordinary_evaluation=True)


@lru_cache(None)
def questions():
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, ['do', 'rqyh', 'rqyg', 'rqyd', 'db', 'mv', 'dn', 'uw']), statements=[])
    text = format_graph(d, 'compact') + 'r zc[] d.r zact[] a.r zb[] a.'
    for name, arg in [('do', 'db'), ('rqyh', 'db')]:
        text += 'q[t[k ' + name + '[k ' + arg + '[]]][k zc[]]].'
    text += 'q[k rqyg[k db[] k zact[] k zc[]]].'
    for name, arg in [('rqyd', 'mv'), ('dn', 'mv'), ('uw', 'zb')]:
        text += 'q[t[k ' + name + '[k ' + arg + '[]]][k zc[]]].'
    return parse(text)


def source_values(variant='baseline'):
    v = previous_values(variant)
    old_cause = v['hzie']
    key = ['activity', 'rqye', 'population', 'rqyd', 'actual']
    changes = {'event_wrong_act': (0, 'activitytwo'), 'event_wrong_factor': (1, 'dl'),
        'event_wrong_target': (2, 'guards'), 'event_wrong_result': (3, 'dn'), 'event_wrong_context': (4, 'belief'),
        'split_purpose_and_cause': (0, 'activitytwo')}
    if variant in changes:
        i, value = changes[variant]; key[i] = value
    if variant == 'event_reversed': key = ['population', 'rqyd', 'activity', 'rqye', 'actual']
    def causation(a, p, b, q, s):
        group = old_cause(a, p, b, q, s) and variant != 'no_group_cause'
        event = variant not in ('no_causation', 'no_event_cause') and (a, symbol(p), b, symbol(q), s) == tuple(key)
        return group or event
    def aims(actor, act, goal, scene):
        actors = ('guardone',) if variant == 'only_one_goal' else ('guardone', 'guardtwo')
        if variant == 'outsider_goal': actors = ('other',)
        target = 'db' if variant == 'goal_wrong_target' else 'mv'
        content = 'dn' if variant == 'goal_wrong_content' else 'rqyd'
        return variant != 'no_goal' and actor in actors and (act, goal_key(goal), scene) == (
            'activitytwo' if variant == 'goal_wrong_act' else 'activity', (content, target),
            'belief' if variant == 'goal_wrong_context' else 'actual')
    v.update(hzie=causation, hzu=aims, zact=lambda: 'activity')
    if variant == 'split_purpose_and_cause':
        v['df'] = lambda actor, act, scene: actor in ('guardone', 'guardtwo') and act in ('activity', 'activitytwo') and scene == 'actual'
    return v


def source_checks():
    inherited = ('baseline', 'actual_danger', 'no_adoption', 'no_causation', 'female_not_judging',
        'female_outside_population', 'empty_female_class', 'empty_guards', 'duplicate_guard', 'uncovered_target',
        'irrelevant_guard', 'nonhuman_guard', 'no_current_role', 'not_prior', 'wrong_assumption_act', 'claimed_only',
        'separate_activities', 'no_activity', 'no_burden', 'no_judgment', 'unrecognized_population')
    additions = ('no_goal', 'only_one_goal', 'outsider_goal', 'goal_wrong_act', 'goal_wrong_target',
        'goal_wrong_content', 'goal_wrong_context', 'no_event_cause', 'no_group_cause', 'event_wrong_act',
        'event_wrong_factor', 'event_wrong_target', 'event_wrong_result', 'event_wrong_context',
        'event_reversed', 'split_purpose_and_cause')
    rows = {}
    for variant in (*inherited, *additions):
        actual = evaluate(questions(), source_values(variant), PEOPLE, SCENES, True)
        assert actual[0] == (variant in ('baseline', 'actual_danger', 'no_adoption', 'no_group_cause')), (variant, actual)
        if variant in additions: assert actual[1] == (variant != 'no_group_cause'), (variant, actual)
        assert actual[5] == (variant == 'actual_danger')
        if variant in ('no_burden', 'no_judgment'): assert actual[2] and not actual[4]
        if variant == 'split_purpose_and_cause': assert actual[1:3] == [True, True]
        rows[variant] = actual
    d = deepcopy(questions()); d['statements'] = d['statements'][:3]
    d['declarations'] = closure(d, _references(d['statements']))
    small_people = ('person', 'guardone', 'population', 'guards', 'appointment', 'activity', 'low', 'high')
    small_scenes = ('actual', 'belief', 'prior'); ordinary = {}
    for variant in ('baseline', 'no_goal', 'no_event_cause'):
        v = source_values(variant)
        v.update(mp=lambda group: SequenceValue(('person',) if group == 'population' else
                ('guardone',) if group == 'guards' else (), '"individual"'),
            aa=lambda p: p in ('person', 'guardone'),
            hr=lambda pop, scene: pop.items == ('person',) and scene == 'actual',
            uq=lambda p, description, context, outcome: p == 'person' and symbol(description) == 'up'
                and context in ('actual', 'belief') and outcome == 'belief',
            ur=lambda p, scene: (p, scene) == ('person', 'belief'))
        plain = evaluate(d, v, small_people, small_scenes)
        cached = evaluate(d, v, small_people, small_scenes, True)
        assert plain == cached == rows[variant][:3]
        ordinary[variant] = dict(ordinary=plain, memoized=cached)
    for name in ('hzu', 'hzie', 'df', 'dg', 'u2'):
        v = source_values(); v[name] = unknown
        try: evaluate(d, v, PEOPLE, SCENES, True)
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    return dict(contrasts=rows, current_definitions_executed=True, ordinary_comparisons=ordinary,
        ordinary_domain=dict(individuals=list(small_people), situations=list(small_scenes)),
        unknown_inputs_refused=5, purpose_without_success=True, same_event_required=True,
        all_selected_actors_aim_is_an_explicit_reading=True)


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
    return dict(contrasts=rows, purpose_and_causation_not_executed=True)


def structure():
    old, new = parent(), catalog()
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 44
    assert set(new.entries) - set(old.entries) == {'rqye', 'rqyf', 'rqyg', 'rqyh'}
    assert [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']] == ['do']
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n != 'do')
    before = [d['name'] for d in old.document['declarations'] if d['name'] != 'hzu']
    after = [d['name'] for d in new.document['declarations'] if d['name'] in old.entries and d['name'] != 'hzu']
    assert before == after
    saved = deepcopy(old.entries['do']['declaration']); saved['name'] = 'rqyh'
    assert new.entries['rqyh']['declaration'] == saved
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
        new_primitives=0, new_definitions=4, relocated_unchanged_primitive='hzu', preserved_review_meanings=11,
        preceding_four_sentence_meanings_preserved=True, roundtrips=True)


def audit():
    previous = 'data/guardian-causation-reading-v1.json'
    r = json.loads((ROOT / previous).read_text(encoding='utf-8'))
    paths = (PARENT, PARENT_BASIS, INDEX, previous, EVIDENCE, 'artifacts/written-units-v1/kant-1784.json',
        'artifacts/first-cause-reading-v1/page-482.jpg', 'reports/guardian-causation-v1.json')
    return dict(status='purpose_and_causal_contribution_bound_not_whole_sentence_review', reviewer='assistant_review',
        source=r['source'],
        reading='後見人の各参加者が、人々の危険判断を同じ行為の目的として目指し、その行為が実際の判断分布へ寄与するという読み。',
        counterexample='前版は意図しない寄与も許す。目的だけを別条件として加えても、目的の活動Aと原因の活動Bを混ぜることができる。',
        decisions=['既存hzuを再利用して、各行為者の目的を同じ生起行為に結ぶ。',
            '因果要因を特定の行為の生起rqyeとし、目的を持った同じ行為から同じ母集団のrqydへの寄与を要求する。',
            '目的記述はrqyd(mv)に固定し、目的を持つこと自体から達成や客観的な危険を導かない。',
            '目的が未達でもrqyf・rqygで記述できる。結果を伴う本文の読みでは目的と実際の寄与と結果を別々に要求する。'],
        evidence_limit='保存済みSorgenの項は実現へ向けた手配・試みの用法を支える。各人に同じ目的を要求する分配的な読み、同じ活動の範囲、結果の成立は本文に対する解釈であり、辞典の語だけから必然としない。',
        remaining=['各参加者の目的という読みと、集合的目的・行為の粒度の全文中での適否',
            '監督の語義、gütigstの評価、schon・auchの焦点', '当該文・第二段落・二作品全文の意味確認'],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    results = {}
    for name, fn in [('purpose', purpose_checks), ('source', source_checks), ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = audit(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == r
    validate_hashes(ROOT, r['source_sha256'])
    previous = json.loads((ROOT / 'reports/guardian-causation-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT, previous['source_sha256'])
    paths = set(build()) | set(parent().source_sha256) | set(r['source_sha256']) | set(previous['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_guardian_purpose.py', 'scripts/check_guardian_purpose.py', 'scripts/register_guardian_purpose.py',
        'tests/test_guardian_purpose.py'}
    return dict(status='purpose_and_actual_contribution_share_an_action', document=FULL, **results,
        alignment=dict(**r['source'], definitions=['rqye', 'rqyf', 'rqyg', 'rqyh', 'do', 'dp'], status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit())); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__': main()
