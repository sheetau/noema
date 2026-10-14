"""Verify the opt-in quotation prototype and its concrete Kant blocker."""
import argparse
import hashlib
import json
from pathlib import Path

from noema.extraction import extract_document
from noema.grammar import parse as legacy_parse, format_graph as legacy_format
from noema.ranked import parse, format_graph, promote
from noema.ranked_semantics import evaluate_document
from noema.script import transcribe
from noema.semantics import SemanticError

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'examples/v014/kant-unrestricted-others.noema'
EXAMPLE = 'examples/v015/person-dependent-reports.noema'
KANT = 'examples/v015/kant-nonrestriction-description.noema'
REPORT = ROOT / 'reports/ranked-quotation-v1.json'


def kant_example():
    parent = legacy_parse((ROOT / PARENT).read_text(encoding='utf-8'))
    selected = extract_document(parent, roots=['hzg2', 'hzg3'], statement_indices=[]).document
    old = legacy_format(selected, 'compact') + 'q[e[r[p hzg2]][r[p hzg2]]].'
    try:
        legacy_parse(old)
    except SemanticError as exc:
        if 'disquote-free' not in str(exc):
            raise
        refusal = str(exc)
    else:
        raise ValueError('Historical blocker unexpectedly disappeared')
    new = parse(format_graph(promote(selected), 'compact') + 'q[e[r b[p hzg2]][r b[p hzg2]]].')
    return format_graph(new, 'compact') + '\n', refusal


def person_cases():
    doc = parse((ROOT / EXAMPLE).read_text(encoding='utf-8'))
    rows = []
    for alice in (False, True):
        for bob in (False, True):
            descriptions = {}; selected_calls = []
            def register(first, second):
                descriptions.update(alice=first, bob=second)
                return True
            def selected(person):
                selected_calls.append(person)
                return descriptions[person]
            def attributed(value):
                if selected_calls:
                    raise ValueError('Attribution evaluated its quoted body')
                return value.rank == 1
            model = dict(register=register, selected=selected, attributed=attributed, anchor=lambda: 'now',
                satisfied=lambda person, context: alice if person == 'alice' else not bob,
                frustrated=lambda person, context: bob if person == 'bob' else not alice)
            result = [r['value'] for r in evaluate_document(doc, individuals=('alice', 'bob'), situations=('now',), primitives=model)]
            if result != [True, True, alice and bob]:
                raise ValueError('Different personal descriptions were conflated')
            rows.append(dict(alice=alice, bob=bob, result=result, selected_persons=selected_calls))
    return rows


def build_report():
    text, refusal = kant_example()
    if (ROOT / KANT).read_text(encoding='utf-8') != text:
        raise ValueError('Stored Kant quotation example differs')
    documents = {}
    for name in (EXAMPLE, KANT):
        doc = parse((ROOT / name).read_text(encoding='utf-8'))
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(transcribe(form, alphabet='v2')) != doc:
                raise ValueError('Ranked quotation roundtrip differs')
        documents[name] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']))
    doc = parse(text)
    def forbidden(*args):
        raise ValueError('Quoted Kant predicate was evaluated')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    result = evaluate_document(doc, individuals=('person',), situations=('context',), primitives=model)
    if [r['value'] for r in result] != [True]:
        raise ValueError('Ranked description identity differs')
    paths = [PARENT, EXAMPLE, KANT, 'noema/ranked.py', 'noema/ranked_discourse.py', 'noema/ranked_semantics.py',
        'noema/ranked_render.py', 'noema/discourse.py', 'noema/finite_semantics.py', 'noema/render.py',
        'tests/test_ranked_quotation.py', 'scripts/check_ranked_quotation.py']
    return dict(status='opt_in_ranked_quotation_prototype_not_default_language', documents=documents,
        historical_kant_refusal=refusal, general_nonrestriction_predicate_now_quotable=True,
        kant_author_statement_integrated=False, quotation_does_not_execute_predicate=True,
        personal_description_cases=person_cases(), roundtrips=True,
        limitations=['Rank checks cover explicit disquotation syntax and named definition dependencies.',
            'Latent evaluation through arbitrary function-valued arguments is not tracked; this is not a complete effect system.',
            'No consistency or termination theorem is claimed. Existing interpreter budgets and issuer checks remain required.',
            'Historical CLI/parser remain unchanged; use the explicit noema.ranked entry point.',
            'No source coverage or semantic-completion count is increased.'],
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths})


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args(argv)
    text, _ = kant_example()
    path = ROOT / KANT
    if path.exists():
        if path.read_text(encoding='utf-8') != text:
            raise ValueError('Existing ranked example differs')
    elif args.verify_only:
        raise ValueError('Ranked example is missing')
    else:
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
    result = build_report()
    if args.verify_only:
        if json.loads(REPORT.read_text(encoding='utf-8')) != result:
            raise ValueError('Stored ranked quotation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Personal descriptions and the Kant quotation blocker checked; higher-order effect limit remains open')


if __name__ == '__main__':
    main()
