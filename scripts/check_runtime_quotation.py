"""Reproduce higher-order quotation ceiling checks without changing old editions."""
import argparse
import hashlib
import json
from pathlib import Path

from noema.ranked import parse, format_graph
from noema.ranked_semantics import evaluate_document as previous_evaluate
from noema.guarded_ranked_semantics import evaluate_document
from noema.script import transcribe
from noema.semantics import SemanticError

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/runtime-quotation-v1.json'
REJECTED = 'examples/v015/runtime-quotation-rejected.noema'
ACCEPTED = 'examples/v015/runtime-quotation-accepted.noema'
PERSONAL = 'examples/v015/person-dependent-reports.noema'
KANT = 'examples/v015/kant-nonrestriction-description.noema'

TRUE = 'e[n p a b][n p a b]'
CHAIN = ('o:r touch[] c.d aa[] i[c][r[k touch[]]].'
         'd ab[] i b[c][r b[s[k aa[]]]].d ac[] i c[c][r c[s[k ab[]]]].')
ROUTES = ('apply', 'named', 'callback', 'returned', 'identity', 'question', 'sequence', 'equality')


def route_document(route, ceiling, target_rank):
    """The same higher-order operation via eight language execution routes."""
    rank = ('', ' b', ' c')[ceiling]
    body = TRUE if target_rank is None else 's[k ' + ('aa', 'ab', 'ac')[target_rank] + '[]]'
    text = CHAIN + 'd run[] h[] c[i[][' + body + ']].'
    before = ''
    result = 'c'
    call = 'c[s[k template[]]][k run[]]'
    if route == 'apply':
        expression = 'c[v fn][]'
    elif route == 'named':
        before = 'd relay[fn h[] c] c[c[v fn][]].'
        expression = 'k relay[v fn]'
    elif route == 'callback':
        before = 'r bridge[h[] c] c.'
        expression = 'k bridge[v fn]'
    elif route == 'returned':
        result, expression = 'h[] c', 'i[][c[v fn][]]'
        call = 'c[' + call + '][]'
    elif route == 'identity':
        result, expression = 'h[] c', 'v fn'
        call = 'c[' + call + '][]'
    elif route == 'question':
        result, expression = 'g[]', 'j v[i[][c[v fn][]]]'
        call = 'h[' + call + '][]'
    elif route == 'sequence':
        result, expression = 'j[h[] c]', 'l[h[] c][v fn]'
        call = 'q[' + call + '][' + TRUE + '][i[state c item h[] c][c[v item][]]]'
    elif route == 'equality':
        expression = 'e[v fn][i[][' + TRUE + ']]'
    else:
        raise ValueError(route)
    text += before + 'd template[] i' + rank + '[h[h[] c] ' + result + '][r' + rank
    text += '[i[fn h[] c][' + expression + ']]].q[' + call + '].'
    return parse(text)


def check_routes():
    rows = []
    for route in ROUTES:
        for ceiling in range(3):
            for target in (None, 0, 1, 2):
                calls = []
                model = {'touch': lambda: calls.append('touch') is None}
                if route == 'callback':
                    model['bridge'] = lambda fn: fn()
                expected = target is None or target < ceiling
                try:
                    result = evaluate_document(route_document(route, ceiling, target),
                        individuals=('person',), situations=('now',), primitives=model)
                except SemanticError as exc:
                    if expected or 'Runtime quotation ceiling' not in str(exc):
                        raise
                    if calls:
                        raise ValueError('A forbidden body executed before rejection')
                    accepted = False
                else:
                    if not expected or [r['value'] for r in result] != [True]:
                        raise ValueError('Unexpected higher-order interpretation')
                    if calls != ([] if target is None else ['touch']):
                        raise ValueError('An allowed evaluation was omitted')
                    accepted = True
                rows.append(dict(route=route, ceiling=ceiling, target_rank=target, accepted=accepted))
    return rows


def check_personal_descriptions():
    doc = parse((ROOT / PERSONAL).read_text(encoding='utf-8'))
    rows = []
    for alice in (False, True):
        for bob in (False, True):
            stored = {}; calls = []
            def register(first, second):
                stored.update(alice=first, bob=second)
                return True
            def selected(person):
                calls.append(person)
                return stored[person]
            def attributed(description):
                if calls:
                    raise ValueError('Attribution executed its quoted body')
                return description.rank == 1
            model = dict(register=register, selected=selected, attributed=attributed, anchor=lambda: 'now',
                satisfied=lambda person, context: alice if person == 'alice' else not bob,
                frustrated=lambda person, context: bob if person == 'bob' else not alice)
            results = evaluate_document(doc, individuals=('alice', 'bob'), situations=('now',), primitives=model)
            values = [r['value'] for r in results]
            if values != [True, True, alice and bob]:
                raise ValueError('Different personal descriptions were conflated')
            rows.append(dict(alice=alice, bob=bob, values=values, selected_persons=calls))
    return rows


def artifacts():
    return {name: format_graph(route_document('apply', ceiling, 1), 'compact') + '\n'
            for name, ceiling in ((REJECTED, 0), (ACCEPTED, 2))}


def build_report():
    roundtrips = []
    for name, expected in artifacts().items():
        if (ROOT / name).read_text(encoding='utf-8') != expected:
            raise ValueError('Stored example differs: ' + name)
        doc = parse(expected)
        for notation in ('full', 'compact'):
            text = format_graph(doc, notation)
            if parse(text) != doc or parse(transcribe(text, alphabet='v2')) != doc:
                raise ValueError('Quotation notation roundtrip differs')
        roundtrips.append(name)
    previous = previous_evaluate(parse((ROOT / REJECTED).read_text(encoding='utf-8')),
        individuals=('person',), situations=('now',), primitives={'touch': lambda: True})
    if previous[0]['value'] is not True:
        raise ValueError('Historical higher-order escape no longer reproduces')
    kant = parse((ROOT / KANT).read_text(encoding='utf-8'))
    def forbidden(*args):
        raise ValueError('Quoted Kant condition executed')
    model = {d['name']: forbidden for d in kant['declarations'] if d['kind'] == 'primitive'}
    result = evaluate_document(kant, individuals=('person',), situations=('context',), primitives=model)
    if [r['value'] for r in result] != [True]:
        raise ValueError('Kant quotation identity changed')
    rows = check_routes()
    paths = [REJECTED, ACCEPTED, PERSONAL, KANT, 'noema/guarded_ranked_semantics.py',
        'noema/ranked_semantics.py', 'noema/ranked_discourse.py', 'noema/ranked.py',
        'scripts/check_runtime_quotation.py', 'tests/test_runtime_quotation.py']
    return dict(status='opt_in_runtime_quotation_ceilings_not_static_effect_typing',
        prior_escape_reproduced=True, runtime_cases=rows,
        accepted_cases=sum(r['accepted'] for r in rows), rejected_cases=sum(not r['accepted'] for r in rows),
        personal_description_cases=check_personal_descriptions(),
        kant_quotation_does_not_execute_predicate=True, kant_author_statement_integrated=False,
        roundtrip_examples=roundtrips,
        limitations=['The parser still accepts some terms whose evaluation is rejected by the runtime ceiling.',
            'The rule covers evaluation in this interpreter and synchronous calls into other guarded interpretations.',
            'Python model callbacks are trusted implementations, not sandboxed programs.',
            'No static effect soundness, logical consistency or termination theorem is claimed.',
            'Infinite description domains remain unsupported by the finite evaluator.',
            'No source coverage or semantic-completion count is increased.'],
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths})


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args(argv)
    for name, expected in artifacts().items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != expected:
                raise ValueError('Existing example differs: ' + name)
        elif args.verify_only:
            raise ValueError('Missing example: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(expected)
    report = build_report()
    if args.verify_only:
        if json.loads(REPORT.read_text(encoding='utf-8')) != report:
            raise ValueError('Stored runtime quotation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(f"Runtime ceiling: {report['accepted_cases']} accepted / {report['rejected_cases']} rejected; personal contents retained")


if __name__ == '__main__':
    main()
