"""Distinguish avoidance motives, assessment scope and attributed explanations."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_motive_explanations import ROOT, generic_composed, source_composed
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/motive-explanations-v1.json'


def episode_checks():
    doc = parse(generic_composed()[0] + '''
r za[a a d] c.r zb[a a d] c.r zc[a a d] c.r zd[a a i[h[a a d] c] d] c.r ze[] a.r zf[] d.
q[k nb[k ze[] k zf[] p za p zb r[p zb] p zc p zd]].
''')
    rows = []
    for option, factor, avoid, reason in product((False, True), repeat=4):
        model = {'ea': lambda *args: False, 'za': lambda p, a, s: option and (p, a, s) == ('person', 'act', 'text'),
            'zb': lambda p, a, s: factor and (p, a, s) == ('person', 'act', 'text'),
            'zc': lambda p, a, s: avoid and (p, a, s) == ('person', 'act', 'text'),
            'zd': lambda p, a, desc, s: reason and (p, a, symbol(desc), s) == ('person', 'act', 'zb', 'text'),
            'ze': lambda: 'person', 'zf': lambda: 'text'}
        actual = evaluate_document(doc, individuals=('person', 'act', 'other'), situations=('text',), primitives=model)[0]['value']
        if actual != all((option, factor, avoid, reason)):
            raise ValueError('Avoidance episode conditions differ')
        rows.append({'option': option, 'factor': factor, 'avoidance': avoid, 'reason': reason, 'episode': actual})
    model['zb'] = lambda p, a, s: a == 'other'
    actual = evaluate_document(doc, individuals=('person', 'act', 'other'), situations=('text',), primitives=model)[0]['value']
    if actual:
        raise ValueError('Factor for another action was reused')
    return {'cases': rows, 'different_action_rejected': True}


def source_candidate(questions):
    doc = parse(source_composed()[0])
    doc['statements'] = []
    return parse(format_graph(doc, 'compact') + '\n' + questions)


def motive_checks():
    doc = source_candidate('q[t[k mq[k mv[]]][k wh[]]].q[t[k mr[k mv[]]][k wh[]]].')
    domain = ('group', 'alice', 'bob', 'act', 'otheract')
    scenes = ('text', 'first', 'second')
    variants = ('both_different_people', 'effort_only', 'fear_only', 'neither', 'empty_scope',
        'missing_second_episode', 'outside_group', 'wrong_reason_description', 'wrong_action', 'wrong_person')
    rows = {}
    for variant in variants:
        model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
        def reason(p, a, description, s):
            name = symbol(description)
            if variant in ('neither', 'wrong_reason_description') or a != 'act' or s not in scenes[1:]:
                return False
            if variant == 'missing_second_episode' and s == 'second':
                return False
            return (p == 'alice' and name == 'mb' and variant != 'fear_only') or (p == 'bob' and name == 'mc' and variant != 'effort_only')
        model.update({'mv': lambda: 'group', 'wh': lambda: 'text',
            'mp': lambda group: SequenceValue(() if variant == 'outside_group' else ('alice', 'bob'), '"individual"'),
            'aa': lambda p: p in ('alice', 'bob'),
            'ma': lambda p, a, s: p in ('alice', 'bob') and a == 'act' and s in scenes[1:],
            'mb': lambda p, a, s: a == ('otheract' if variant == 'wrong_action' else 'act'),
            'mc': lambda p, a, s: a == ('otheract' if variant == 'wrong_action' else 'act'),
            'md': lambda p, a, s: p == 'group' if variant == 'wrong_person' else a == 'act',
            'me': reason,
            'mh': lambda p, ctx, s: variant != 'empty_scope' and p in ('alice', 'bob') and ctx == 'text' and s in scenes[1:]})
        actual = [r['value'] for r in evaluate_document(doc, individuals=domain, situations=scenes, primitives=model)]
        expected = [variant in ('both_different_people', 'effort_only'), variant in ('both_different_people', 'fear_only')]
        if actual != expected:
            raise ValueError('Motive and scope binding differs: ' + variant)
        rows[variant] = {'effort_pattern_present': actual[0], 'fear_pattern_present': actual[1]}
    return rows


def explanation_checks():
    doc = source_candidate('q[k mu[k mv[] k wh[]]].')
    rows = {}
    for variant in ('both', 'effort_only', 'fear_only', 'neither', 'wrong_factor_subject', 'wrong_effect_subject',
                    'wrong_effect', 'wrong_context', 'reversed'):
        seen = []
        def forbidden(*args):
            raise ValueError('Adopted explanation evaluated a factor or its outcome')
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        def adoption(a, f, b, effect, scene):
            factor, target = symbol(f), symbol(effect)
            seen.append([a, factor, b, target, scene])
            if variant == 'reversed':
                return factor == 'ms' and target in ('mq', 'mr')
            expected = ('other' if variant == 'wrong_factor_subject' else 'group',
                'other' if variant == 'wrong_effect_subject' else 'group',
                'mq' if variant == 'wrong_effect' else 'ms', 'other' if variant == 'wrong_context' else 'text')
            return (a, b, target, scene) == expected and factor in (
                set() if variant == 'neither' else {'mq'} if variant == 'effort_only' else {'mr'} if variant == 'fear_only' else {'mq', 'mr'})
        model.update(mv=lambda: 'group', wh=lambda: 'text', ea=adoption)
        actual = evaluate_document(doc, individuals=('group', 'other'), situations=('text', 'other'), primitives=model)[0]['value']
        if actual != (variant == 'both'):
            raise ValueError('Listed explanation differs: ' + variant)
        rows[variant] = {'adopted': actual, 'references': seen, 'contents_evaluated': False}
    empty = source_candidate('q[k na[k mv[] l[i[h[a] e]][] r[p ms] k wh[]]].')
    model = {d['name']: (lambda *args: True) for d in empty['declarations'] if d['kind'] == 'primitive'}
    model.update(mv=lambda: 'group', wh=lambda: 'text')
    if evaluate_document(empty, individuals=('group',), situations=('text',), primitives=model)[0]['value']:
        raise ValueError('Empty list of causes accepted')
    return {'cases': rows, 'empty_list_rejected': True}


def attribution_check():
    from scripts.check_kant_discourse import base_model, DOMAIN, NODES
    doc = parse(source_composed()[0])
    model = base_model(doc)
    def forbidden(*args):
        raise ValueError('Attribution evaluated an explanation or its contents')
    for name in ('ea', 'ma', 'mb', 'mc', 'md', 'me', 'mh', 'mp', 'mv', 'ha', 'kb', 'la'):
        model[name] = forbidden
    seen = []
    def claim(node, author, description, context):
        seen.append([node, json.loads(description.syntax)['symbol']])
        return author == 'author' and context == 'text'
    model.update(mw=lambda: 'explanation', ua=lambda *args: True, ub=lambda *args: True, uc=claim,
        ud=lambda *args: True, uf=lambda *args: True,
        ue=lambda a, b, ctx: a in NODES and b in NODES and NODES.index(a) < NODES.index(b))
    result = evaluate_document(doc, individuals=(*DOMAIN, 'explanation'), situations=('text',), primitives=model)
    if result != [{'kind': 'assert', 'value': True}] * 2 or seen != [['conclusion', 'bo'], ['explanation', 'mx']]:
        raise ValueError('Author attribution disconnected from new explanation')
    return {'claims': seen, 'explanation_and_contents_evaluated': False}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored motive explanation differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Motive explanation roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Kant source differs')
    phrase = 'Faulheit und Feigheit sind die Ursachen, warum'
    if not unit['text'].startswith(phrase):
        raise ValueError('Cause introduction differs')
    files = [*documents, 'data/motive-explanations-basis-v1.json', 'data/kant-motive-explanations-basis-v1.json',
        'examples/v014/kant-release-transition.noema', 'data/kant-release-transition-basis-v1.json',
        'scripts/compose_motive_explanations.py', 'scripts/check_motive_explanations.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'partial_motive_patterns_and_attributed_causes', 'documents': documents,
        'episodes': episode_checks(), 'motives': motive_checks(), 'explanations': explanation_checks(), 'attribution': attribution_check(),
        'alignment': {'unit': unit['id'], 'unit_sha256': digest, 'start': 0, 'end': len(phrase), 'source': phrase,
            'definitions': ['mj', 'mk', 'mq', 'mr', 'ms', 'mt', 'mu', 'mx'], 'status': 'partial_first_explanandum',
            'remaining': ['degree and normative evaluation of traits', 'causal mechanisms', 'guardians second explanandum', 'metaphor', 'rest of paragraph', 'facsimile review']},
        'roundtrips': True, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Motive explanation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('16 episodes, 10 motive scopes, 9 cause bindings and unevaluated author attribution checked')


if __name__ == '__main__':
    main()
