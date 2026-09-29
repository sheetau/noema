"""Validate transfer bindings, capacity and non-factive future expectations."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.compose_payment_expectation import ROOT, generic_composed, source_composed
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/payment-expectation-v1.json'


def candidate(text, questions):
    doc = parse(text)
    doc['statements'] = []
    return parse(format_graph(doc, 'compact') + '\n' + questions)


def values(doc, model, people, scenes, *, memoize=False):
    return [r['value'] for r in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=2_000_000, memoize_definitions=memoize)]


def payment_checks():
    doc = candidate(generic_composed()[0], '''
r qa[] a.r qb[] a.r qc[] a.r qd[] a.r qe[] d.
r qf[a a a a d] c.r qg[a d] c.r qh[a a i[h[a] e] d] c.r qi[a d] c.
d qj[person a] e[b scene[k qi[v person v scene]]].
d qk[person a] e[b scene[k qi[v person v scene]]].
q[k rf[k qa[] k qb[] k qc[] k qd[] r[p qj] k qe[] p qf p qg p qh]].
''')
    people = ('payer', 'receiver', 'transfer', 'medium', 'other')
    scenes = ('sale', 'other')
    rows = {}
    variants = ('baseline', 'same_person', 'wrong_transfer', 'wrong_payer', 'wrong_receiver', 'wrong_medium',
                'wrong_time', 'unaccepted_medium', 'gift', 'different_transfer_consideration', 'different_receiver_consideration', 'different_task')
    for variant in variants:
        def forbidden(*args):
            raise ValueError('Payment evaluated the service as already performed')
        model = {'qa': lambda: 'payer', 'qb': lambda: 'payer' if variant == 'same_person' else 'receiver',
            'qc': lambda: 'transfer', 'qd': lambda: 'medium', 'qe': lambda: 'sale', 'qi': forbidden,
            'qf': lambda transfer, payer, receiver, medium, scene: (transfer, payer, receiver, medium, scene) == (
                'other' if variant == 'wrong_transfer' else 'transfer', 'other' if variant == 'wrong_payer' else 'payer',
                'other' if variant == 'wrong_receiver' else 'payer' if variant == 'same_person' else 'receiver',
                'other' if variant == 'wrong_medium' else 'medium', 'other' if variant == 'wrong_time' else 'sale'),
            'qg': lambda medium, scene: variant != 'unaccepted_medium' and (medium, scene) == ('medium', 'sale'),
            'qh': lambda transfer, receiver, task, scene: variant != 'gift' and (transfer, receiver, symbol(task), scene) == (
                'other' if variant == 'different_transfer_consideration' else 'transfer',
                'other' if variant == 'different_receiver_consideration' else 'payer' if variant == 'same_person' else 'receiver',
                'qk' if variant == 'different_task' else 'qj', 'sale')}
        actual = values(doc, model, people, scenes)[0]
        if actual != (variant == 'baseline'):
            raise ValueError('Payment component binding differs: ' + variant)
        rows[variant] = {'payment': actual, 'service_evaluated': False}
    return rows


def forecast_checks():
    doc = candidate(generic_composed()[0], '''
r qa[] d.r qb[d] c.r qc[d d] c.r qd[d] c.
q[k ri[b scene[k qd[v scene]] k qa[] p qb p qc]].
q[k qd[k qa[]]].
''')
    scenes = ('now', 'near', 'far')
    rows = []
    for s1, s2, f1, f2, t1, t2, actual_now in product((False, True), repeat=7):
        selected = {scene for scene, flag in zip(scenes[1:], (s1, s2)) if flag}
        future = {scene for scene, flag in zip(scenes[1:], (f1, f2)) if flag}
        true_cases = {scene for scene, flag in zip(scenes[1:], (t1, t2)) if flag}
        model = {'qa': lambda: 'now', 'qb': lambda scene: scene in selected,
            'qc': lambda start, end: start == 'now' and end in future,
            'qd': lambda scene: actual_now if scene == 'now' else scene in true_cases}
        actual = values(doc, model, ('observer',), scenes)
        expected = [bool(selected) and selected <= future and selected <= true_cases, actual_now]
        if actual != expected:
            raise ValueError('Future forecast confused candidate and actual truth')
        rows.append({'selected': sorted(selected), 'future': sorted(future), 'true_candidates': sorted(true_cases),
            'forecast': actual[0], 'current_truth': actual[1]})
    model = {'qa': lambda: 'now', 'qb': lambda scene: scene == 'now', 'qc': lambda *args: True, 'qd': lambda *args: True}
    same = values(doc, model, ('observer',), scenes)
    if same != [False, True]:
        raise ValueError('Current truth was accepted as future expectation')
    return {'cases': rows, 'current_as_future': same}


def takeover_checks():
    doc = candidate(generic_composed()[0], '''
r qa[] a.r qb[] d.r qc[a] c.r qd[a a i[h[a] e] d] c.r qe[a d] c.
d qf[person a] e[b scene[k qe[v person v scene]]].
d qg[person a] e[b scene[k qe[v person v scene]]].
q[k rh[k qa[] r[p qf] k qb[] p qc p qd]].
''')
    people = ('person', 'worker', 'alternate', 'tool')
    rows = {}
    for variant in ('baseline', 'second_worker', 'self', 'artifact', 'wrong_beneficiary', 'wrong_task', 'wrong_time', 'none'):
        who = {'second_worker': 'alternate', 'self': 'person', 'artifact': 'tool'}.get(variant, 'worker')
        def forbidden(*args):
            raise ValueError('Undertaking executed or completed the work')
        model = {'qa': lambda: 'person', 'qb': lambda: 'future', 'qc': lambda person: person != 'tool', 'qe': forbidden,
            'qd': lambda other, person, task, scene: variant != 'none' and (other, person, symbol(task), scene) == (
                who, 'alternate' if variant == 'wrong_beneficiary' else 'person',
                'qg' if variant == 'wrong_task' else 'qf', 'now' if variant == 'wrong_time' else 'future')}
        actual = values(doc, model, people, ('now', 'future'))[0]
        if actual != (variant in ('baseline', 'second_worker')):
            raise ValueError('Prospective undertaking differs: ' + variant)
        rows[variant] = {'undertaken': actual, 'work_evaluated': False}
    return rows


def varying_worker_checks():
    doc = candidate(generic_composed()[0], '''
r qa[] a.r qb[] d.r qc[a] c.r qd[a a i[h[a] e] d] c.r qe[d] c.r qf[d d] c.
d qg[person a] e[b scene[e[v person][v person]]].
q[k ri[b scene[k rh[k qa[] r[p qg] v scene p qc p qd]] k qb[] p qe p qf]].
q[g other a[w[k qc[v other]][w[u[e[v other][k qa[]]]][f scene d[y[k qe[v scene]][k qd[v other k qa[] r[p qg] v scene]]]]]]].
''')
    rows = {}
    for variant in ('different_workers', 'same_worker', 'missing_second'):
        def undertaking(other, person, task, scene):
            if person != 'person' or symbol(task) != 'qg':
                return False
            if scene == 'near':
                return other == 'first'
            if scene == 'far':
                return variant != 'missing_second' and other == ('first' if variant == 'same_worker' else 'second')
            return False
        model = {'qa': lambda: 'person', 'qb': lambda: 'now', 'qc': lambda *args: True, 'qd': undertaking,
            'qe': lambda scene: scene in ('near', 'far'), 'qf': lambda start, end: start == 'now' and end in ('near', 'far')}
        actual = values(doc, model, ('person', 'first', 'second'), ('now', 'near', 'far'))
        expected = [variant != 'missing_second', variant == 'same_worker']
        if actual != expected:
            raise ValueError('A single fixed worker was inferred across alternative futures')
        rows[variant] = {'future_undertaking': actual[0], 'one_worker_for_every_candidate': actual[1]}
    return rows


PEOPLE = ('person', 'worker', 'transfer', 'medium', 'plan')
SCENES = ('now', 'paid', 'future')


def source_model(doc, variant):
    def forbidden(*args):
        raise ValueError('Source capacity or expectation executed the described thinking task')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(za=lambda: 'person', wh=lambda: 'now', aa=lambda person: person in ('person', 'worker'),
        ae=lambda person, plan, start: variant != 'no_method' and (person, plan, start) == ('person', 'plan', 'now'),
        af=lambda person, plan, start, end: (person, plan, start, end) == ('person', 'plan', 'now', 'paid'),
        ap=lambda person, plan, start, end: variant != 'empty_results' and (person, plan, start, end) == ('person', 'plan', 'now', 'paid'),
        ti=lambda transfer, payer, receiver, medium, scene: variant != 'no_transfer' and
            (transfer, payer, receiver, medium) == ('transfer', 'person', 'worker', 'medium') and
            scene in (('now', 'paid') if variant == 'already_paid' else ('paid',)),
        tj=lambda medium, scene: medium == 'medium',
        tk=lambda transfer, receiver, task, scene: variant != 'gift' and
            (transfer, receiver, symbol(task)) == ('transfer', 'worker', 'bm'),
        sj=lambda person, scene: variant != 'failed_goal' and (person, scene) == ('person', 'paid'),
        tl=lambda *args: variant == 'thinking_required',
        s2=lambda person, context, scene: variant != 'empty_cases' and (person, context, scene) == ('person', 'now', 'now'),
        ts=lambda other, person, task, scene: (other, person, symbol(task), scene) == (
            'person' if variant == 'self_takes_over' else 'medium' if variant == 'artifact_takes_over' else 'worker',
            'worker' if variant == 'wrong_beneficiary' else 'person', 'bm', 'future'),
        tu=lambda person, task, context: variant != 'not_unpleasant' and (person, symbol(task), context) == ('person', 'bm', 'now'),
        tw=lambda person, task, context, scene: variant != 'empty_forecast' and (person, symbol(task), context, scene) == (
            'person', 'bm' if variant == 'wrong_forecast_description' else 'tz', 'now', 'future'),
        tx=lambda start, end: variant != 'not_future' and (start, end) == ('now', 'future'))
    return model


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.q[t[k to[k za[]]][k wh[]]].q[t[k tp[k za[]]][k wh[]]].
q[t[k tq[k za[]]][k wh[]]].q[t[k tr[k za[]]][k wh[]]].
q[t[k tz[k za[]]][k wh[]]].q[t[k t2[k za[]]][k wh[]]].q[t[k t3[k za[]]][k wh[]]].
''')
    rows = {}
    variants = ('baseline', 'already_paid', 'no_method', 'empty_results', 'no_transfer', 'gift', 'failed_goal',
        'thinking_required', 'empty_cases', 'self_takes_over', 'artifact_takes_over', 'wrong_beneficiary',
        'not_unpleasant', 'empty_forecast', 'wrong_forecast_description', 'not_future')
    for variant in variants:
        actual = values(doc, source_model(doc, variant), PEOPLE, SCENES, memoize=True)
        capacity = variant not in ('no_method', 'empty_results', 'no_transfer', 'gift')
        without_thinking = variant not in ('no_method', 'empty_results', 'failed_goal', 'thinking_required')
        conditional = variant != 'empty_cases' and (not capacity or without_thinking)
        expectation = variant not in ('self_takes_over', 'artifact_takes_over', 'wrong_beneficiary',
            'not_unpleasant', 'empty_forecast', 'wrong_forecast_description', 'not_future')
        expected = [variant == 'already_paid', capacity, without_thinking, conditional, False, expectation, conditional and expectation]
        if actual != expected:
            raise ValueError('Integrated payment expectation differs: ' + variant + ' ' + repr(actual))
        rows[variant] = dict(zip(('payment_now', 'capacity', 'without_own_thinking', 'conditional',
            'undertaking_now', 'expectation', 'combined'), actual))
    ordinary = values(doc, source_model(doc, 'baseline'), PEOPLE, SCENES)
    if ordinary != list(rows['baseline'].values()):
        raise ValueError('Ordinary evaluation and memoized source baseline differ')
    return {'cases': rows, 'definitions_replaced_by_primitives': False, 'pure_definition_memoization': True,
        'ordinary_baseline_agrees': True, 'described_thinking_executed': False}


def attribution_checks():
    from scripts.check_kant_discourse import base_model, DOMAIN, NODES
    doc = parse(source_composed()[0])
    rows = {}
    for variant in ('baseline', 'wrong_node', 'wrong_author', 'wrong_description', 'wrong_context', 'reversed_order'):
        model = base_model(doc)
        def forbidden(*args):
            raise ValueError('An attributed hypothetical sentence asserted an actual payment or prediction')
        for name in ('ti', 'tj', 'tk', 'tl', 'ts', 'tu', 'tw', 'tx', 'ae', 'af', 'ap', 's2'):
            model[name] = forbidden
        def present(node, author, description, context):
            if node == 'illustration':
                return (author, symbol(description), context) == ('author', 'sy', 'text')
            return (node, author, symbol(description), context) == ('other' if variant == 'wrong_node' else 'payment',
                'other' if variant == 'wrong_author' else 'author', 'tr' if variant == 'wrong_description' else 't3',
                'other' if variant == 'wrong_context' else 'text')
        def before(a, b, context):
            return context == 'text' and ((a in NODES and b in NODES and NODES.index(a) < NODES.index(b)) or (a, b) in (
                ('conclusion', 'explanation'), ('explanation', 'illustration'),
                ('payment', 'illustration') if variant == 'reversed_order' else ('illustration', 'payment')))
        model.update(mw=lambda: 'explanation', s3=lambda: 'illustration', t4=lambda: 'payment',
            ua=lambda *args: True, ub=lambda *args: True, uc=lambda *args: True, ud=lambda *args: True,
            uf=lambda *args: True, qa=lambda *args: True, s5=lambda *args: True, s4=present, ue=before)
        actual = values(doc, model, (*DOMAIN, 'explanation', 'illustration', 'payment', 'other'), ('text',))
        if actual != [True, True, True, True, variant == 'baseline']:
            raise ValueError('Payment sentence attribution differs: ' + variant)
        rows[variant] = {'statements': actual, 'underlying_content_evaluated': False}
    return rows


def alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Original source differs')
    phrase = 'Ich habe nicht nöthig zu denken, wenn ich nur bezahlen kann; andere werden das verdrießliche Geschäft schon für mich übernehmen.'
    if unit['text'].count(phrase) != 1:
        raise ValueError('Payment source is missing or ambiguous')
    start = unit['text'].index(phrase)
    return {'unit': unit['id'], 'unit_sha256': digest, 'start': start, 'end': start + len(phrase), 'source': phrase,
        'status': 'partial_explicit_reading', 'capacity': 'tp', 'conditional': 'tr', 'expectation': 't2', 'combined': 't3',
        'remaining': ['general meaning of payment and thinking', 'focus and discourse effects of nur and schon',
            'irony and scope', 'convenience sentence and remaining paragraph', 'facsimile review'], 'full_semantic_equivalence': False}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored payment expectation differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Payment expectation roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/payment-expectation-basis-v1.json', 'data/kant-payment-expectation-basis-v1.json',
        'examples/v014/kant-delegated-judgment.noema', 'data/kant-delegated-judgment-basis-v1.json',
        'scripts/compose_payment_expectation.py', 'scripts/check_payment_expectation.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'payment_capacity_and_future_undertaking_with_scoped_attribution', 'documents': documents,
        'payment_bindings': payment_checks(), 'forecasts': forecast_checks(), 'takeover': takeover_checks(),
        'varying_workers': varying_worker_checks(),
        'source': source_checks(), 'attribution': attribution_checks(), 'alignment': alignment(), 'roundtrips': True,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Payment expectation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('12 payment bindings, 128 forecasts, 8 takeover, 3 worker-scope, 16 source and 6 attribution cases checked')


if __name__ == '__main__':
    main()
