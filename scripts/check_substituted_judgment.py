"""Check provider binding, scoped conditionals and effort-free successful methods."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.compose_substituted_judgment import ROOT, generic_composed, source_composed
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/substituted-judgment-v1.json'


def candidate(text, queries):
    doc = parse(text)
    doc['statements'] = []
    return parse(format_graph(doc, 'compact') + '\n' + queries)


def values(doc, model, people, scenes, budget=1_000_000):
    return [r['value'] for r in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=budget)]


def effort_checks():
    doc = candidate(generic_composed()[0], '''
r za[] a.r zb[] d.r zc[a a d] c.r zd[a a d d] c.r ze[a a d d] c.r zf[d] c.r zg[a a d d] c.
q[k rd[k za[] b scene[k zf[v scene]] k zb[] p zc p zd p ze p zg]].
q[k xd[k za[] b scene[k zf[v scene]] k zb[] p zc p zd p ze]].
''')
    scenes = ('start', 'good', 'bad')
    rows = []
    for available, s1, s2, g1, g2, e1, e2 in product((False, True), repeat=7):
        selected = {scene for scene, flag in zip(scenes[1:], (s1, s2)) if flag}
        good = {scene for scene, flag in zip(scenes[1:], (g1, g2)) if flag}
        effort = {scene for scene, flag in zip(scenes[1:], (e1, e2)) if flag}
        model = {'za': lambda: 'person', 'zb': lambda: 'start',
            'zc': lambda person, plan, start: available and (person, plan, start) == ('person', 'plan', 'start'),
            'zd': lambda person, plan, start, end: (person, plan, start) == ('person', 'plan', 'start') and end in scenes[1:],
            'ze': lambda person, plan, start, end: (person, plan, start) == ('person', 'plan', 'start') and end in selected,
            'zf': lambda end: end in good,
            'zg': lambda person, plan, start, end: end in effort}
        actual = values(doc, model, ('person', 'plan'), scenes)
        expected = [available and bool(selected) and selected <= good and selected.isdisjoint(effort),
                    available and bool(selected) and selected <= good]
        if actual != expected:
            raise ValueError('Effort-free attainment differs from independent set oracle')
        rows.append({'available': available, 'selected': sorted(selected), 'goal': sorted(good),
            'effort': sorted(effort), 'effort_free_attainment': actual[0], 'attainment': actual[1]})
    contrasts = {}
    for variant in ('separate_methods', 'same_successful_method', 'outside_outcomes', 'no_available_method'):
        def outcome(person, plan, start, end):
            return (person, start) == ('person', 'start') and (
                (plan, end) == ('hard', 'good') or (plan, end) == ('idle', 'bad'))
        model = {'za': lambda: 'person', 'zb': lambda: 'start',
            'zc': lambda person, plan, start: variant != 'no_available_method' and (person, start) == ('person', 'start') and plan in ('hard', 'idle'),
            'zd': lambda *args: False if variant == 'outside_outcomes' else outcome(*args),
            'ze': outcome, 'zf': lambda end: end == 'good',
            'zg': lambda person, plan, start, end: variant != 'same_successful_method' and plan == 'hard'}
        actual = values(doc, model, ('person', 'hard', 'idle'), scenes)
        expected = {'separate_methods': [False, True], 'same_successful_method': [True, True],
                    'outside_outcomes': [False, False], 'no_available_method': [False, False]}[variant]
        if actual != expected:
            raise ValueError('Unsuccessful rest substituted for successful effort: ' + variant)
        contrasts[variant] = actual
    return {'cases': rows, 'contrasts': contrasts}


def conditional_checks():
    doc = candidate(generic_composed()[0], '''
r za[] a.r zb[d] c.r zc[a d] c.r zd[a d] c.
d ze[person a] e[b scene[k zc[v person v scene]]].
d zf[person a] e[b scene[k zd[v person v scene]]].
q[k rc[k za[] p ze p zf p zb]].q[k re[k za[] p ze p zb]].
''')
    scenes = ('first', 'second')
    rows = []
    for a, b, p, q, r, s in product((False, True), repeat=6):
        selected = {scene for scene, flag in zip(scenes, (a, b)) if flag}
        premise = {scene for scene, flag in zip(scenes, (p, q)) if flag}
        result = {scene for scene, flag in zip(scenes, (r, s)) if flag}
        model = {'za': lambda: 'person', 'zb': lambda scene: scene in selected,
            'zc': lambda person, scene: person == 'person' and scene in premise,
            'zd': lambda person, scene: person == 'person' and scene in result}
        actual = values(doc, model, ('person', 'other'), scenes)
        expected = [bool(selected) and selected.intersection(premise) <= result, bool(selected.intersection(premise))]
        if actual != expected:
            raise ValueError('Hypothetical condition or premise applicability differs')
        rows.append({'cases': sorted(selected), 'premise': sorted(premise), 'result': sorted(result),
            'conditional': actual[0], 'applicable': actual[1]})
    return rows


def provider_checks():
    doc = candidate(generic_composed()[0], '''
r za[] a.r zb[a d] c.r zc[a a d] c.r zd[a a i[h[a] e] d] c.r ze[a d] c.r zf[] d.
d zg[person a] e[b scene[k ze[v person v scene]]].
d zh[person a] e[b scene[k ze[v person v scene]]].
q[k rb[k za[] r[p zg] p zb k zf[] p zc p zd]].
''')
    rows = {}
    for variant in ('baseline', 'self_supply', 'split_kind', 'split_access', 'wrong_task', 'wrong_recipient', 'wrong_context'):
        provider = 'traveler' if variant == 'self_supply' else 'map'
        def forbidden(*args):
            raise ValueError('Referring to a supplied task executed that task')
        model = {'za': lambda: 'traveler', 'zf': lambda: 'trip', 'ze': forbidden,
            'zb': lambda item, scene: (item, scene) == ('other' if variant == 'split_kind' else provider, 'trip'),
            'zc': lambda person, item, scene: (person, item, scene) == ('traveler', 'other' if variant == 'split_access' else provider, 'trip'),
            'zd': lambda item, person, task, scene: (item, person, symbol(task), scene) == (provider,
                'other' if variant == 'wrong_recipient' else 'traveler', 'zh' if variant == 'wrong_task' else 'zg',
                'other' if variant == 'wrong_context' else 'trip')}
        actual = values(doc, model, ('traveler', 'map', 'other'), ('trip', 'other'))[0]
        if actual != (variant == 'baseline'):
            raise ValueError('Other-topic substituted provider binding differs: ' + variant)
        rows[variant] = {'accepted': actual, 'task_evaluated': False}
    return rows


def source_model(doc, variant='baseline'):
    def forbidden(*args):
        raise ValueError('A substituted task was executed instead of referred to')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(za=lambda: 'person', wh=lambda: 'text',
        aa=lambda person: person in ('person', 'other', 'guide', 'doctor'),
        sc=lambda provider, scene: (provider, scene) == ('book', 'case'),
        sd=lambda provider, scene: variant != 'inaccessible_text' and (provider, scene) == ('book', 'case'))
    def access(person, provider, scene):
        return (person, scene) == ('person', 'case') and provider in ('book', 'guide', 'doctor') and not (
            variant in ('missing_access', 'shared_human_provider') and provider == 'doctor')
    def supply(provider, person, task, scene):
        if variant == 'shared_human_provider':
            return (person, scene) == ('person', 'case') and (provider, symbol(task)) in (
                ('book', 'bm'), ('guide', 'sm'), ('guide', 'sn'))
        expected = {'book': 'bm', 'guide': 'sm', 'doctor': 'sn'}
        if variant == 'wrong_task':
            expected['guide'] = 'sn'
        if variant == 'split_provider':
            expected['other'] = expected.pop('doctor')
        return (person, scene) == ('other' if variant == 'wrong_beneficiary' else 'person', 'case') and symbol(task) == expected.get(provider)
    def role(provider, description, scene):
        if variant == 'shared_human_provider':
            return (provider, scene) == ('guide', 'case') and symbol(description) in ('so', 'sq')
        expected = {'guide': 'so', 'doctor': 'sq'}
        if variant == 'wrong_role':
            expected['doctor'] = 'so'
        return scene == 'case' and symbol(description) == expected.get(provider)
    model.update(sa=access, sb=supply, si=role,
        sj=lambda person, scene: variant != 'failed_goal' and (person, scene) == ('person', 'outcome'),
        ae=lambda person, plan, start: variant != 'unavailable_plan' and (person, plan, start) == ('person', 'plan', 'case'),
        af=lambda person, plan, start, end: (person, plan, start, end) == ('person', 'plan', 'case', 'outcome'),
        ap=lambda person, plan, start, end: variant != 'empty_results' and (person, plan, start, end) == ('person', 'plan', 'case', 'outcome'),
        sk=lambda person, plan, start, end: variant == 'own_effort',
        s2=lambda person, context, scene: variant != 'empty_cases' and
            (person, context, scene) == ('other' if variant == 'wrong_perspective' else 'person', 'text', 'case'))
    return model


SOURCE_PEOPLE = ('person', 'other', 'book', 'guide', 'doctor', 'plan')
SOURCE_SCENES = ('text', 'case', 'outcome')


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.
q[t[k sv[k za[]]][k zb[]]].q[t[k sx[k za[]]][k zb[]]].
q[k re[k za[] p sv i[scene d][k s2[k za[] k wh[] v scene]]]].
q[t[k sy[k za[]]][k wh[]]].q[t[k sv[k za[]]][k wh[]]].
''')
    rows = {}
    false_premise = ('inaccessible_text', 'missing_access', 'wrong_task', 'split_provider', 'wrong_beneficiary', 'wrong_role')
    false_result = ('failed_goal', 'unavailable_plan', 'empty_results', 'own_effort')
    for variant in ('baseline', 'shared_human_provider', *false_premise, *false_result, 'empty_cases', 'wrong_perspective'):
        model = source_model(doc, variant)
        model['zb'] = lambda: 'case'
        actual = values(doc, model, SOURCE_PEOPLE, SOURCE_SCENES)
        expected = [variant not in false_premise, variant not in false_result,
                    variant not in (*false_premise, 'empty_cases', 'wrong_perspective'),
                    variant not in (*false_result, 'empty_cases', 'wrong_perspective'), False]
        if actual != expected:
            raise ValueError('Source conditional binding differs: ' + variant + ' ' + repr(actual))
        rows[variant] = dict(zip(('premise_in_case', 'result_in_case', 'applicable', 'conditional', 'premise_in_actual_context'), actual))
    return {'cases': rows, 'task_contents_evaluated': False, 'definitions_replaced_by_primitives': False}


def task_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.q[t[k sm[k za[]]][k wh[]]].q[t[k sn[k za[]]][k wh[]]].
q[t[k so[k za[]]][k wh[]]].q[t[k sq[k za[]]][k wh[]]].
''')
    rows = {}
    for variant in ('baseline', 'wrong_actor', 'wrong_judgment', 'wrong_matter', 'wrong_subject', 'missing_moral', 'missing_regimen', 'missing_spiritual', 'missing_health'):
        model = source_model(doc)
        model.update(wh=lambda: 'case',
            fa=lambda person, judgment, scene: (person, judgment, scene) == ('other' if variant == 'wrong_actor' else 'person', 'judgment', 'case'),
            fb=lambda judgment, matter, scene: (judgment, matter, scene) == ('other' if variant == 'wrong_judgment' else 'judgment', 'other' if variant == 'wrong_matter' else 'matter', 'case'),
            se=lambda judgment, person, scene: variant != 'missing_moral' and (judgment, person, scene) == ('judgment', 'other' if variant == 'wrong_subject' else 'person', 'case'))
        for key, missing in (('sf', 'missing_regimen'), ('sg', 'missing_spiritual'), ('sh', 'missing_health')):
            model[key] = lambda matter, person, scene, missing=missing: variant != missing and (
                matter, person, scene) == ('matter', 'other' if variant == 'wrong_subject' else 'person', 'case')
        actual = values(doc, model, ('person', 'other', 'judgment', 'matter'), ('case',))
        expected = [variant not in ('wrong_actor', 'wrong_subject', 'missing_moral')]
        expected += [variant not in ('wrong_actor', 'wrong_subject', 'wrong_judgment', 'wrong_matter', missing)
                     for missing in ('missing_regimen', 'missing_spiritual', 'missing_health')]
        if actual != expected:
            raise ValueError('Task constituent binding differs: ' + variant)
        rows[variant] = actual
    return rows


def attribution_checks():
    from scripts.check_kant_discourse import base_model, DOMAIN, NODES
    doc = parse(source_composed()[0])
    rows = {}
    for variant in ('baseline', 'wrong_node', 'wrong_author', 'wrong_property', 'wrong_context', 'closed_list', 'reversed_examples', 'reversed_order'):
        model = base_model(doc)
        def forbidden(*args):
            raise ValueError('A hypothetical illustration asserted actual possession or effort')
        for name in ('sa', 'sb', 'sc', 'sd', 'se', 'sf', 'sg', 'sh', 'si', 'sj', 'sk', 's2', 'ae', 'af', 'ap'):
            model[name] = forbidden
        observed = []
        def perspective(node, author, description, context):
            actual = (node, author, symbol(description), context)
            observed.append(list(actual))
            return actual == ('other' if variant == 'wrong_node' else 'illustration',
                'other' if variant == 'wrong_author' else 'author', 'sv' if variant == 'wrong_property' else 'sy',
                'other' if variant == 'wrong_context' else 'text')
        def examples(node, author, descriptions, context):
            return variant != 'closed_list' and (node, author, context) == ('illustration', 'author', 'text') and [
                symbol(item) for item in descriptions.items] == (['su', 'st', 'ss'] if variant == 'reversed_examples' else ['ss', 'st', 'su'])
        def before(a, b, context):
            return context == 'text' and ((a in NODES and b in NODES and NODES.index(a) < NODES.index(b))
                or (a, b) == ('conclusion', 'explanation') or (a, b) == (
                    ('illustration', 'explanation') if variant == 'reversed_order' else ('explanation', 'illustration')))
        model.update(mw=lambda: 'explanation', s3=lambda: 'illustration', ua=lambda *args: True, ub=lambda *args: True,
            uc=lambda *args: True, ud=lambda *args: True, uf=lambda *args: True, qa=lambda *args: True,
            ue=before, s4=perspective, s5=examples)
        actual = values(doc, model, (*DOMAIN, 'explanation', 'illustration', 'other'), ('text',))
        if actual != [True, True, True, variant == 'baseline']:
            raise ValueError('Illustrative first-person attribution differs: ' + variant)
        rows[variant] = {'statements': actual, 'perspective_references': observed, 'underlying_scenario_evaluated': False}
    return rows


def source_alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Original source differs')
    phrase = 'Habe ich ein Buch, das für mich Verstand hat, einen Seelsorger, der für mich Gewissen hat, einen Arzt der für mich die Diät beurtheilt, u. s. w. so brauche ich mich ja nicht selbst zu bemühen.'
    if unit['text'].count(phrase) != 1:
        raise ValueError('Conditional source is missing or ambiguous')
    start = unit['text'].index(phrase)
    return {'unit': unit['id'], 'unit_sha256': digest, 'start': start, 'end': start + len(phrase), 'source': phrase,
        'status': 'partial_explicit_reading', 'definitions': {'examples': ['ss', 'st', 'su'], 'premise': 'sv',
        'effort_free_attainment': 'sx', 'conditional': 'sy', 'nonexhaustive_list': 'sz'},
        'remaining': ['full meanings of book, conscience, religious and medical roles', 'contextual goal and effort scope',
            'discourse effects of ja and irony', 'previous convenience sentence', 'following payment sentence',
            'remaining paragraph', 'facsimile review'], 'full_semantic_equivalence': False}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored substituted judgment differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Substituted judgment roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/substituted-judgment-basis-v1.json', 'data/kant-delegated-judgment-basis-v1.json',
        'data/delegation-reading-review-v1.json', 'examples/v014/kant-nature-depiction.noema', 'data/kant-nature-depiction-basis-v1.json',
        'scripts/compose_substituted_judgment.py', 'scripts/check_substituted_judgment.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'three_substituted_tasks_in_an_attributed_hypothetical_frame', 'documents': documents,
        'effort': effort_checks(), 'conditional_cases': conditional_checks(), 'providers': provider_checks(), 'source': source_checks(),
        'task_bindings': task_checks(), 'attribution': attribution_checks(), 'alignment': source_alignment(),
        'roundtrips': True, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Substituted judgment report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('128 effort models, 4 method contrasts, 64 conditionals, 7 provider, 14 source, 9 task and 8 attribution cases checked')


if __name__ == '__main__':
    main()
