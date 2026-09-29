"""Check figurative attribution without turning depictions into actual facts."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_figurative_frames import ROOT, generic_composed, source_composed
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/figurative-frames-v1.json'


def generic_checks():
    prefix = generic_composed()[0] + '''
r ya[a d] c.r yb[a d] c.r wa[] a.r wb[] a.r wc[] a.r wd[] d.
d za[person a] e[b scene[k ya[v person v scene]]].
d zb[person a] e[b scene[k yb[v person v scene]]].
'''
    doc = parse(prefix + '''
q[k qh[k wa[] k wb[] r[p za] r[p zb] k wd[]]].
q[k qi[k wa[] k wb[] r[p za] r[p zb] k za[k wc[]] k wd[]]].
q[k qh[k wa[] k wb[] r[p za] r[p za] k wd[]]].
q[e[k za[k wc[]]][k zb[k wc[]]]].
''')
    rows = []
    for target_true, depiction_true, framed in product((False, True), repeat=3):
        model = {'ya': lambda *args: target_true, 'yb': lambda *args: depiction_true,
            'wa': lambda: 'node', 'wb': lambda: 'author', 'wc': lambda: 'person', 'wd': lambda: 'context',
            'qa': lambda *args: framed}
        actual = [r['value'] for r in evaluate_document(doc, individuals=('node', 'author', 'person'), situations=('context',), primitives=model)]
        expected = [framed, framed and target_true, False, target_true == depiction_true]
        if actual != expected:
            raise ValueError('Figurative framing confused content truth or description identity')
        rows.append({'target_true': target_true, 'depiction_true': depiction_true, 'framed': framed,
            'framing_condition': actual[0], 'target_and_framing': actual[1], 'identical_description_accepted': actual[2], 'equal_contents': actual[3]})
    return rows


def source_candidate(questions):
    doc = parse(source_composed()[0])
    doc['statements'] = []
    return parse(format_graph(doc, 'compact') + '\n' + questions)


def frame_binding_checks():
    doc = source_candidate('q[k qh[k mw[] k wa[] r[p kf] r[p qg] k wh[]]].')
    rows = {}
    variants = ('baseline', 'wrong_node', 'wrong_author', 'wrong_target', 'wrong_depiction', 'wrong_context', 'reversed')
    for variant in variants:
        seen = []
        def forbidden(*args):
            raise ValueError('Figurative reference evaluated its target or depiction')
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        def framing(node, author, target, depiction, context):
            values = (node, author, symbol(target), symbol(depiction), context)
            seen.append(list(values))
            expected = ('other' if variant == 'wrong_node' else 'explanation',
                'other' if variant == 'wrong_author' else 'author',
                'kc' if variant == 'wrong_target' else 'qg' if variant == 'reversed' else 'kf',
                'qf' if variant == 'wrong_depiction' else 'kf' if variant == 'reversed' else 'qg',
                'other' if variant == 'wrong_context' else 'text')
            return values == expected
        model.update(mw=lambda: 'explanation', wa=lambda: 'author', wh=lambda: 'text', qa=framing)
        actual = evaluate_document(doc, individuals=('explanation', 'author', 'other'), situations=('text', 'other'), primitives=model)[0]['value']
        if actual != (variant == 'baseline'):
            raise ValueError('Figurative reference binding differs: ' + variant)
        rows[variant] = {'accepted': actual, 'references': seen, 'contents_evaluated': False}
    return rows


def depiction_checks():
    doc = source_candidate('r za[] a.q[t[k qg[k za[]]][k wh[]]].')
    scenes = ('prior', 'life', 'text', 'other')
    domain = ('person', 'nature', 'other')
    variants = ('baseline', 'wrong_declarer', 'wrong_person', 'wrong_status', 'not_prior', 'not_long_ago', 'empty_life', 'outside_history')
    rows = {}
    for variant in variants:
        model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
        seen = []
        def declaration(agent, person, description, point):
            values = (agent, person, symbol(description), point)
            seen.append(values)
            return values == ('other' if variant == 'wrong_declarer' else 'nature',
                'other' if variant == 'wrong_person' else 'person', 'kc' if variant == 'wrong_status' else 'qf',
                'life' if variant == 'not_prior' else 'prior')
        def forbidden(*args):
            raise ValueError('Depiction evaluated the declared status as an actual fact')
        model.update(za=lambda: 'person', wh=lambda: 'text', qb=lambda: 'nature', qc=declaration, kb=forbidden,
            ia=lambda person, ctx, point: person == 'person' and ctx == 'text' and point in ('prior', 'life') and not (variant == 'outside_history' and point == 'prior'),
            ib=lambda person, ctx, point: variant != 'empty_life' and (person, ctx, point) == ('person', 'text', 'life'),
            ic=lambda a, b, ctx: (a, b) == ('prior', 'life'), kd=lambda *args: variant != 'not_long_ago')
        actual = evaluate_document(doc, individuals=domain, situations=scenes, primitives=model, max_steps=2_000_000)[0]['value']
        if actual != (variant == 'baseline'):
            raise ValueError('Nature declaration depiction differs: ' + variant)
        rows[variant] = {'depiction_true_in_supplied_interpretation': actual, 'status_evaluated': False,
            'declarer_is_asserted_human': False}
    return rows


def attribution_checks():
    from scripts.check_kant_discourse import base_model, DOMAIN, NODES
    doc = parse(source_composed()[0])
    rows = {}
    for framed in (False, True):
        model = base_model(doc)
        def forbidden(*args):
            raise ValueError('Figurative annotation asserted a natural speech event')
        for name in ('qb', 'qc', 'ea', 'mp', 'mv', 'kb', 'la'):
            model[name] = forbidden
        model.update(mw=lambda: 'explanation', ua=lambda *args: True, ub=lambda *args: True, uc=lambda *args: True,
            ud=lambda *args: True, uf=lambda *args: True,
            ue=lambda a, b, ctx: ctx == 'text' and ((a in NODES and b in NODES and NODES.index(a) < NODES.index(b)) or (a, b) == ('conclusion', 'explanation')),
            qa=lambda node, author, target, depiction, ctx: framed and
                (node, author, symbol(target), symbol(depiction), ctx) == ('explanation', 'author', 'kf', 'qg', 'text'))
        actual = [r['value'] for r in evaluate_document(doc, individuals=(*DOMAIN, 'explanation'), situations=('text',), primitives=model)]
        if actual != [True, True, framed]:
            raise ValueError('Framing annotation was mixed with the causal claims')
        rows['framed' if framed else 'unframed'] = {'statements': actual, 'depiction_and_target_evaluated': False}
    return rows


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored figurative frame differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Figurative frame roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Kant source differs')
    phrase = 'nachdem sie die Natur längst von fremder Leitung frei gesprochen (naturaliter majorennes)'
    if unit['text'].count(phrase) != 1:
        raise ValueError('Depiction source missing or ambiguous')
    start = unit['text'].index(phrase)
    files = [*documents, 'data/figurative-frames-basis-v1.json', 'data/kant-nature-depiction-basis-v1.json',
        'data/figurative-reading-review-v1.json', 'examples/v014/kant-finite-ratio.noema', 'data/kant-finite-ratio-basis-v1.json',
        'scripts/compose_figurative_frames.py', 'scripts/check_figurative_frames.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'explicit_figurative_reading_without_literal_assertion', 'documents': documents,
        'truth_cases': generic_checks(), 'bindings': frame_binding_checks(), 'depiction': depiction_checks(), 'attribution': attribution_checks(),
        'alignment': {'unit': unit['id'], 'unit_sha256': digest, 'start': start, 'end': start+len(phrase), 'source': phrase,
            'target_definition': 'kf', 'depiction_definition': 'qg', 'status': 'explicit_interpretive_annotation',
            'remaining': ['general meaning of nature and declaration', 'evaluative effects of the metaphor', 'independent Latin reading',
                'causal meaning', 'rest of paragraph', 'facsimile review']},
        'roundtrips': True, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Figurative frame report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('8 truth cases, 7 description bindings, 8 depiction scopes and 2 attribution cases checked')


if __name__ == '__main__':
    main()
