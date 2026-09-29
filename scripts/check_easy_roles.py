"""Check same-method ease, assumed authority, cohorts and both causal results."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_easy_roles import ROOT, generic_composed, source_composed
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/easy-roles-v1.json'


def easy_checks():
    doc = parse(generic_composed()[0] + '''
r za[a a d] c.r zb[a a d d] c.r zc[a a d d] c.r zd[a a d] b.r ze[b] c.r zf[] a.r zg[] d.r zh[] e.
q[k nd[k zf[] k zh[] k zg[] p za p zb p zc p zd p ze]].
''')
    scenes = ('now', 'first', 'second')
    subsets = [set(s for s, on in zip(scenes[1:], bits) if on) for bits in product((False, True), repeat=2)]
    rows = []
    for enabled, outcomes, selected, successful, cheap in product((False, True), subsets, subsets, subsets, (False, True)):
        model = {'za': lambda a, p, s: enabled and (a, p, s) == ('actor', 'plan', 'now'),
            'zb': lambda a, p, s, e: (a, p, s) == ('actor', 'plan', 'now') and e in outcomes,
            'zc': lambda a, p, s, e: (a, p, s) == ('actor', 'plan', 'now') and e in selected,
            'zd': lambda *args: Fraction(1 if cheap else 9), 'ze': lambda value: value <= 2,
            'zf': lambda: 'actor', 'zg': lambda: 'now',
            'zh': lambda: Content(scenes, tuple(s in successful for s in scenes))}
        actual = evaluate_document(doc, individuals=('actor', 'plan'), situations=scenes, primitives=model)[0]['value']
        expected = enabled and bool(selected) and selected <= outcomes and selected <= successful and cheap
        if actual != expected:
            raise ValueError('Ease differs from independently checked selected outcomes')
        rows.append({'available': enabled, 'outcomes': sorted(outcomes), 'selected': sorted(selected),
            'successful': sorted(successful), 'low_burden': cheap, 'easy': actual})
    contrasts = {}
    for coupled in (False, True):
        model.update({'za': lambda a, p, s: a == 'actor' and p in ('cheap', 'costly') and s == 'now',
            'zb': lambda a, p, s, e: a == 'actor' and s == 'now' and e == ('first' if p == ('cheap' if coupled else 'costly') else 'second'),
            'zc': lambda a, p, s, e: a == 'actor' and s == 'now' and e == ('first' if p == ('cheap' if coupled else 'costly') else 'second'),
            'zd': lambda a, p, s: Fraction(1 if p == 'cheap' else 9),
            'zh': lambda: Content(scenes, (False, True, False))})
        actual = evaluate_document(doc, individuals=('actor', 'cheap', 'costly'), situations=scenes, primitives=model)[0]['value']
        if actual != coupled:
            raise ValueError('Easy and successful methods were combined across different plans')
        contrasts['same_method' if coupled else 'different_methods'] = actual
    return {'cases': rows, 'method_binding': contrasts}


def candidate(questions):
    doc = parse(source_composed()[0])
    doc['statements'] = []
    return parse(format_graph(doc, 'compact') + '''
r za[] a.r zb[] a.r zc[] d.r zd[a] c.
''' + questions)


def role_checks():
    doc = candidate('q[k og[k za[] k zb[] k zc[]]].q[t[k od[k za[] k zb[]]][k zc[]]].q[k oj[k mv[] p zd k zc[]]].')
    scenes = ('now', 'success', 'failure')
    domain = ('actor', 'target', 'other', 'method', 'act', 'group')
    variants = ('baseline', 'high_burden', 'no_method', 'empty_selected', 'selected_outside_outcomes', 'selected_failure',
        'wrong_actor', 'wrong_target', 'different_act', 'not_self_initiated', 'empty_targets', 'empty_others',
        'self_target', 'nonhuman_target', 'wrong_ease_context', 'already_done_without_method')
    rows = {}
    for variant in variants:
        model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update({'za': lambda: 'actor', 'zb': lambda: 'target', 'zc': lambda: 'now', 'mv': lambda: 'group',
            'zd': lambda p: variant != 'empty_targets' and p == ('actor' if variant == 'self_target' else 'target'),
            'aa': lambda p: p in ('actor', 'target') and not (p == 'target' and variant == 'nonhuman_target'),
            'ae': lambda a, p, s: variant not in ('no_method', 'already_done_without_method') and (a, p, s) == ('actor', 'method', 'now'),
            'af': lambda a, p, s, e: (a, p, s) == ('actor', 'method', 'now') and e == ('failure' if variant == 'selected_outside_outcomes' else 'success'),
            'ap': lambda a, p, s, e: variant != 'empty_selected' and (a, p, s) == ('actor', 'method', 'now') and e == ('failure' if variant == 'selected_failure' else 'success'),
            'oa': lambda a, act, s: variant != 'not_self_initiated' and a == 'actor' and act == 'act' and (s == 'success' or variant == 'already_done_without_method'),
            'ob': lambda act, a, target, s: (act, a, target) == ('other' if variant == 'different_act' else 'act',
                'other' if variant == 'wrong_actor' else 'actor', 'other' if variant == 'wrong_target' else 'target') and (s == 'success' or variant == 'already_done_without_method'),
            'oc': lambda *args: Fraction(9 if variant == 'high_burden' else 1),
            'oe': lambda score, s: score <= 2 and s == ('failure' if variant == 'wrong_ease_context' else 'now'),
            'of': lambda group, a, s: variant != 'empty_others' and (group, a, s) == ('group', 'actor', 'now')})
        actual = [r['value'] for r in evaluate_document(doc, individuals=domain, situations=scenes, primitives=model)]
        easy = variant in ('baseline', 'empty_targets', 'empty_others', 'self_target', 'nonhuman_target')
        expected = [easy, variant == 'already_done_without_method', variant == 'baseline']
        if actual != expected:
            raise ValueError('Role/ease/cohort binding differs: ' + variant)
        rows[variant] = dict(zip(('easy_for_pair', 'currently_assumed', 'cohort_condition'), actual))
    return rows


def target_interface_checks():
    # Isolate only the new reference boundary; kg's full semantics is tested in
    # the preceding transition/concession reports, not re-proved by this stub.
    doc = candidate('q[k oi[k mv[] k za[] k zc[]]].')
    for d in doc['declarations']:
        if d['name'] == 'kg':
            d['kind'] = 'primitive'
            d['parameters'] = [p['sort'] for p in d['parameters']]
            del d['body']
    doc = parse(format_graph(doc, 'compact'))
    rows = []
    for member, prior_condition in product((False, True), repeat=2):
        model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update(mv=lambda: 'group', za=lambda: 'target', zc=lambda: 'now',
            mp=lambda group: SequenceValue(('target',) if member else (), '"individual"'),
            kg=lambda person: Content(('now', 'other'), (prior_condition and person == 'target', False)))
        actual = evaluate_document(doc, individuals=('group', 'target'), situations=('now', 'other'), primitives=model)[0]['value']
        if actual != (member and prior_condition):
            raise ValueError('Antecedent group and qualifying property disconnected')
        rows.append({'member': member, 'qualifying_property_assumed': prior_condition, 'target': actual})
    return {'cases': rows, 'prior_property_is_stubbed': True, 'full_kg_semantics_reverified': False}


def explanation_checks():
    doc = candidate('q[k ol[k mv[] k zc[]]].')
    rows = {}
    for missing in (None, ('mq', 'ms'), ('mr', 'ms'), ('mq', 'ok'), ('mr', 'ok')):
        seen = []
        def forbidden(*args):
            raise ValueError('Explaining either result executed its contents')
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        def adopted(a, factor, b, effect, scene):
            pair = (symbol(factor), symbol(effect))
            seen.append(list(pair))
            return a == b == 'group' and scene == 'now' and pair != missing
        model.update(mv=lambda: 'group', zc=lambda: 'now', ea=adopted)
        actual = evaluate_document(doc, individuals=('group',), situations=('now',), primitives=model)[0]['value']
        if actual != (missing is None) or seen != [['mq', 'ms'], ['mr', 'ms'], ['mq', 'ok'], ['mr', 'ok']]:
            raise ValueError('Both results must retain both listed causes')
        rows['all' if missing is None else '/'.join(missing)] = {'adopted': actual, 'references': seen}
    return rows


def attribution_checks():
    from scripts.check_kant_discourse import base_model, DOMAIN, NODES
    doc = parse(source_composed()[0])
    rows = {}
    for variant in ('baseline', 'missing_order', 'wrong_author'):
        model = base_model(doc)
        def forbidden(*args):
            raise ValueError('Attribution executed the two-result explanation')
        for name in ('ea', 'oa', 'ob', 'oc', 'oe', 'of', 'mp', 'mv'):
            model[name] = forbidden
        def claim(node, who, desc, scene):
            return who == ('reader' if variant == 'wrong_author' else 'author') and scene == 'text'
        model.update(mw=lambda: 'explanation', ua=lambda *args: True, ub=lambda *args: True, uc=claim,
            ud=lambda *args: True, uf=lambda *args: True,
            ue=lambda a, b, ctx: ctx == 'text' and ((a in NODES and b in NODES and NODES.index(a) < NODES.index(b)) or
                (variant != 'missing_order' and (a, b) == ('conclusion', 'explanation'))))
        actual = evaluate_document(doc, individuals=(*DOMAIN, 'explanation'), situations=('text',), primitives=model)[-1]['value']
        if actual != (variant == 'baseline'):
            raise ValueError('Author or narrative order differs: ' + variant)
        rows[variant] = actual
    return rows


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored easy role differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Easy role roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Kant source differs')
    phrase = 'und warum es Anderen so leicht wird, sich zu deren Vormündern aufzuwerfen.'
    if unit['text'].count(phrase) != 1:
        raise ValueError('Guardians clause missing or ambiguous')
    start = unit['text'].index(phrase)
    files = [*documents, 'data/easy-roles-basis-v1.json', 'data/kant-easy-guardians-basis-v1.json',
        'examples/v014/kant-motive-explanations.noema', 'data/kant-motive-explanations-basis-v1.json',
        'scripts/compose_easy_roles.py', 'scripts/check_easy_roles.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'partial_second_result_and_two_result_explanation', 'documents': documents,
        'ease': easy_checks(), 'roles': role_checks(), 'target_interface': target_interface_checks(),
        'explanations': explanation_checks(), 'attribution': attribution_checks(),
        'alignment': {'unit': unit['id'], 'unit_sha256': digest, 'start': start, 'end': start+len(phrase), 'source': phrase,
            'definitions': ['od', 'og', 'oi', 'oj', 'ok', 'ol', 'mx'], 'status': 'partial_second_result',
            'remaining': ['guardianship historical and evaluative meaning', 'ease scale and generic scope', 'causal mechanisms',
                'natural personification', 'first sentence semantic review', 'rest of paragraph', 'facsimile review']},
        'roundtrips': True, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Easy role report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('256 ease cases, 2 method contrasts, 16 role scopes, 4 target interfaces, 5 cause and 3 attribution cases checked')


if __name__ == '__main__':
    main()
