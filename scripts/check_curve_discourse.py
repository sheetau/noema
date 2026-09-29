"""Verify attribution scope without evaluating or endorsing quoted clock laws."""
import argparse
import hashlib
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.compose_curve_discourse import ROOT, composed, generic_composed

REPORT = ROOT / 'reports/curve-discourse-v1.json'
DOMAIN = ('author', 'otherauthor', 'previous', 'assumption', 'conclusion', 'scope', 'otherscope')


def source_checks():
    doc = parse(composed()[0])
    results = {}
    for label in ('baseline', 'wrong_author', 'wrong_context', 'wrong_assumption_scope', 'wrong_claim_scope',
                  'missing_assumption', 'missing_scoped_claim', 'wrong_premise_description', 'wrong_result_description',
                  'missing_inference', 'wrong_inference_premise', 'reversed_order', 'not_presented_as_proved', 'merged_nodes'):
        events, semantic_calls = [], []
        model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
        for name, value in zip(('wa', 'wb', 'wc', 'wd', 'we', 'wf'),
                               ('author', 'previous', 'assumption', 'conclusion', 'scope', 'text'), strict=True):
            model[name] = lambda value=value: value
        if label == 'merged_nodes':
            model['wd'] = lambda: 'assumption'
        def actor_context(author, context):
            return author == ('otherauthor' if label == 'wrong_author' else 'author') and context == ('other' if label == 'wrong_context' else 'text')
        def assumption(node, author, description, scope, context):
            events.append({'act': 'assume', 'node': node, 'scope': scope, 'syntax': description.syntax})
            expected = {'kind': 'call', 'symbol': 'qd' if label == 'wrong_premise_description' else 'qc', 'arguments': []}
            return (label != 'missing_assumption' and actor_context(author, context) and node == 'assumption'
                    and scope == ('otherscope' if label == 'wrong_assumption_scope' else 'scope') and json.loads(description.syntax) == expected)
        def claim(node, author, description, scope, context):
            events.append({'act': 'scoped_claim', 'node': node, 'scope': scope, 'syntax': description.syntax})
            expected = {'kind': 'call', 'symbol': 'qc' if label == 'wrong_result_description' else 'qd', 'arguments': []}
            return (label != 'missing_scoped_claim' and actor_context(author, context) and node == 'conclusion'
                    and scope == ('otherscope' if label == 'wrong_claim_scope' else 'scope') and json.loads(description.syntax) == expected)
        def inference(author, premises, conclusion, context):
            members = [item for item in DOMAIN if premises(item)]
            events.append({'act': 'inference', 'premises': members, 'conclusion': conclusion})
            return (label != 'missing_inference' and actor_context(author, context) and conclusion == 'conclusion'
                    and members == (['previous'] if label == 'wrong_inference_premise' else ['assumption']))
        order = [('previous', 'assumption'), ('assumption', 'conclusion'), ('previous', 'conclusion')]
        def before(first, last, context):
            return context == 'text' and ((last, first) if label == 'reversed_order' else (first, last)) in order
        def proved(author, node, context):
            events.append({'act': 'presented_as_proved', 'node': node})
            return label != 'not_presented_as_proved' and actor_context(author, context) and node == 'previous'
        def do_not_evaluate(*args):
            semantic_calls.append(True)
            raise ValueError('Attributed content was evaluated without an explicit request')
        for name in ('aa', 'ab', 'ac', 'ad', 'ta', 'tb', 'tc', 'td', 'te'):
            model[name] = do_not_evaluate
        model.update(ug=assumption, uh=claim, ud=inference, ue=before, ui=proved)
        rows = evaluate_document(doc, individuals=DOMAIN, situations=('text', 'other'), primitives=model)
        actual = all(row['value'] for row in rows)
        if actual != (label == 'baseline') or semantic_calls:
            raise ValueError('Curve discourse differs: ' + label)
        results[label] = {'expected': label == 'baseline', 'actual': actual, 'statements': rows,
                          'underlying_contents_evaluated': bool(semantic_calls), 'acts': events}
    return results


def truth_separation_checks():
    # Use visibly true/false arithmetic content to distinguish attribution
    # from truth and to show that a false consequent can be presented as a
    # conclusion even when it is not a valid inference.
    base = generic_composed()[0]
    ids = 'r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.\n'
    results = {}
    for premise_value in (False, True):
        for result_value in (False, True):
            premise = 'r[b world[e[n p a b][n p ' + ('a' if premise_value else 'b') + ' b]]]'
            result = 'r[b world[e[n p a b][n p ' + ('a' if result_value else 'b') + ' b]]]'
            text = (base + ids + 's[k vd[k za[] k ze[] k zd[] k zb[] k zc[] ' + premise + ' ' + result + ']].'
                    'q[t[s[' + premise + ']][k ze[]]].q[t[s[' + result + ']][k ze[]]].')
            doc = parse(text)
            model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
            model.update(za=lambda: 'author', zb=lambda: 'assumption', zc=lambda: 'conclusion', zd=lambda: 'scope', ze=lambda: 'text',
                         ug=lambda node, author, content, scope, context: (node, author, scope, context) == ('assumption', 'author', 'scope', 'text'),
                         uh=lambda node, author, content, scope, context: (node, author, scope, context) == ('conclusion', 'author', 'scope', 'text'),
                         ue=lambda first, last, context: (first, last, context) == ('assumption', 'conclusion', 'text'),
                         ud=lambda author, premises, conclusion, context: (author, conclusion, context) == ('author', 'conclusion', 'text')
                            and [x for x in DOMAIN if premises(x)] == ['assumption'])
            rows = evaluate_document(doc, individuals=DOMAIN, situations=('text',), primitives=model)
            if [row['value'] for row in rows] != [True, premise_value, result_value]:
                raise ValueError('Attribution was confused with truth')
            results[f'{premise_value}_{result_value}'] = {'attributed': True, 'premise_truth': premise_value,
                                                          'result_truth': result_value, 'material_implication_truth': not premise_value or result_value}
    return results


def source_alignment():
    path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source artifact differs')
    source = json.loads(path.read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:u0128')
    text = unit['text']
    boundaries = (0, text.index('so erhält man den Satz:'), text.index('Man schließt daraus,'), len(text))
    rows = []
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        selected = text[start:end]
        rows.append({'range': [start, end], 'text_sha256': hashlib.sha256(selected.encode('utf-8')).hexdigest(),
                     'status': 'partial' if index < 2 else 'unwritten',
                     'definitions': ['qc', 'vd'] if index == 0 else ['qd', 'vd'] if index == 1 else []})
    return {'unit': unit['id'], 'text_sha256': unit['text_sha256'], 'segments': rows,
            'exact_model_equation_is_source_approximation': False,
            'uncovered': ['complete preceding polygonal result', 'clock-to-curve worldline and units',
                          'M0241 second-order approximation and higher-order qualification', 'Earth clock inference',
                          'facsimile review and full semantic equivalence']}


def build_report():
    text, basis = composed()
    generic, generic_basis = generic_composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or (ROOT / generic_basis['document']).read_text(encoding='utf-8') != generic:
        raise ValueError('Stored conditional text differs')
    for content in (text, generic):
        doc = parse(content)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Conditional roundtrip differs')
    files = [basis['document'], generic_basis['document'], 'data/curve-discourse-basis-v1.json',
             'data/conditional-discourse-basis-v1.json', 'examples/fragments/conditional-discourse.noema.inc',
             'examples/fragments/expository-discourse.noema.inc', 'scripts/compose_curve_discourse.py',
             'scripts/check_curve_discourse.py', 'scripts/compose_kant_discourse.py', 'scripts/compose_limits.py',
             'examples/v014/integrals.noema', 'data/integrals-basis-v1.json',
             'examples/v014/einstein-path-observations.noema', 'data/path-observations-basis-v1.json',
             'noema/discourse.py', 'noema/finite_semantics.py', 'reports/written-units-v1.json']
    return {'status': 'partial_conditional_curve_discourse', 'basis_audit': audit_basis(parse(text), basis),
            'generic_basis_audit': audit_basis(parse(generic), generic_basis), 'roundtrips': True,
            'source_checks': source_checks(), 'truth_separation_checks': truth_separation_checks(),
            'source_alignment': source_alignment(), 'physical_aliases': {'source': 'path-observations-basis-v1',
            'symbols': {'ma': 'ta', 'me': 'tb', 'mc': 'tc', 'mb': 'td', 'mi': 'te'}},
            'source_inference_machine_proved': False, 'source_approximation_completed': False,
            'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Conditional report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('14 attribution cases and 4 truth combinations checked without endorsing quoted contents')


if __name__ == '__main__':
    main()
