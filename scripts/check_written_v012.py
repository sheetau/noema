"""Check typed answers and partial alignment; no claim of source equivalence."""
import argparse
import hashlib
import json
from pathlib import Path

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_kant_v012 import composed

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/written-v012.json'


def question_checks():
    text, _ = composed()
    doc = parse(text)
    results = {}
    for label, capable, context, active, expected in [
        ('harmful_neutral_helpful_conflicting', True, 'start', True, [[['harmful'], ['both']], [['helpful']]]),
        ('no_effects_does_not_invent_answers', True, 'start', False, [[], []]),
        ('changed_context_is_not_implicit_present', True, 'end', True, [[['helpful']], [['harmful']]]),
        ('changed_prior_definition_changes_topic', False, 'start', True, [[], []]),
    ]:
        observed = []
        def effect(factor, property_, scene, *, promoting=False):
            # Both relations receive the same p bi in this fixed document.
            # Evaluate its closed meaning once per interpretation, not once
            # per candidate. No fact or answer is filled in by this cache.
            if not observed:
                observed.append(list(property_('change').values))
            content = observed[0]
            if not active or content != [False, True]:
                return False
            targets = ({'helpful', 'both', 'outsider'} if promoting else {'harmful', 'both', 'outsider'}) if scene == 'start' else (
                {'harmful'} if promoting else {'helpful'})
            return factor in targets
        predicates = {
            'aa': lambda p: p == 'person',
            'ab': lambda f, p, s: (f, p) == ('faculty', 'person'),
            'ac': lambda p, f, a, s: (p, f, a, s) == ('person', 'faculty', 'act', 'end'),
            'ad': lambda g, p, a, s: False,
            'ae': lambda p, plan, s: capable and (p, plan, s) == ('person', 'plan', 'end'),
            'af': lambda p, plan, s, outcome: (p, plan, s, outcome) == ('person', 'plan', 'end', 'end'),
            'ag': lambda change, before, after: (change, before, after) == ('change', 'start', 'end'),
            'ah': lambda factor, effect_, s: s == 'start' and factor.values == (True, False) and effect_.values == (True, not capable),
            'ai': lambda p, s: s == 'end', 'aj': lambda p, s: s == 'end', 'ak': lambda p, s: True,
            'al': lambda p, goal, s: False, 'am': lambda message, property_: message.force == 'direct',
            'ao': lambda: 'person',
            'ma': lambda factor, s: factor in ('harmful', 'neutral', 'helpful', 'both'),
            'mb': effect,
            'mc': lambda factor, property_, scene: effect(factor, property_, scene, promoting=True),
            'md': lambda: context,
        }
        actual = evaluate_document(doc, individuals=('person', 'faculty', 'act', 'plan', 'change',
                                                     'harmful', 'neutral', 'helpful', 'both', 'outsider'),
                                   situations=('start', 'end'), primitives=predicates, max_steps=30000000)
        if actual != [{'kind': 'assert', 'value': True}] + [{'kind': 'ask', 'answers': a} for a in expected]:
            raise ValueError('Kant question countermodel failed: ' + label)
        if not observed or any(content != [False, capable] for content in observed):
            raise ValueError('Question lost its connection to the prior definition')
        results[label] = {'expected_answers': expected, 'statements': actual, 'topic_content': observed[0]}
    return results


def build_report():
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored question document differs')
    if json.loads((ROOT / 'data/kant-question-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored question basis differs')
    alignment = json.loads((ROOT / 'data/kant-question-alignment-v1.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    source_path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != inventory['works']['kant-1784']['units_sha256']:
        raise ValueError('Source unit artifact changed')
    unit = next(u for u in json.loads(source_path.read_text(encoding='utf-8'))['units'] if u['id'] == alignment['source_unit'])
    if (alignment['document'] != basis['document'] or unit['text_sha256'] != alignment['source_sha256']
            or alignment['unselected_ranges_status'] != 'pending'):
        raise ValueError('Alignment source or document differs')
    ranges, end = [], 0
    for selection in alignment['selections']:
        if not selection['source'] or unit['text'].count(selection['source']) != 1:
            raise ValueError('Missing or ambiguous source excerpt')
        start = unit['text'].index(selection['source'])
        if start < end or selection['status'] != 'partial' or not set(selection['definitions']) <= set(basis['definitions']):
            raise ValueError('Invalid question alignment')
        if start > end:
            ranges.append({'start': end, 'end': start, 'status': 'pending'})
        end = start + len(selection['source'])
        ranges.append({'id': selection['id'], 'start': start, 'end': end, 'status': 'partial'})
    if end < len(unit['text']):
        ranges.append({'start': end, 'end': len(unit['text']), 'status': 'pending'})
    paths = sorted((ROOT / 'examples/v012').glob('*.noema'))
    for path in paths:
        doc = parse(path.read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Question round trip differs')
    number = parse((ROOT / 'examples/v012/number-question.noema').read_text(encoding='utf-8'))
    if evaluate_document(number, individuals=('object',), situations=('now',), primitives={}) != [
            {'kind': 'ask', 'value': True}, {'kind': 'ask', 'value': False}]:
        raise ValueError('Numeric answer check differs')
    files = [p.relative_to(ROOT).as_posix() for p in paths] + [
        'examples/fragments/kant-questions.noema.inc', 'examples/v011/kant-linked-draft.noema',
        'data/kant-linked-basis-v1.json', 'data/kant-question-additions-v1.json',
        'data/kant-question-basis-v1.json', 'data/kant-question-alignment-v1.json', 'reports/written-units-v1.json',
        'scripts/compose_kant_v012.py', 'scripts/check_written_v012.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'noema/grammar.py', 'noema/semantics.py', 'noema/language.py', 'noema/render.py', 'noema/script.py', 'noema/cli.py',
        'noema/meaning_basis.py']
    return {'status': 'partial_semantic_draft', 'edition': '0.12', 'roundtrips': True,
            'basis_audit': audit_basis(parse(text), basis), 'countermodels': question_checks(), 'numeric_candidate_checks': True,
            'source_unit': unit['id'], 'source_ranges': ranges, 'unselected_source_ranges_accounted_for': True,
            'verified_full_units': 0,
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Question verification differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Written 0.12: typed answers and partial Kant questions verified; full units remain incomplete')


if __name__ == '__main__':
    main()
