"""Evaluate all six footnote assertions in one shared finite interpretation.

This checks joint consistency and selected countermodels, not source equivalence.
The hypothetical receipt and present nonreceipt share the same person and work.
"""
import argparse
import json
from pathlib import Path

from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references, load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from scripts import check_announced_answer as announced
from scripts import check_courteous_reference as courtesy
from scripts.compose_subject_bound_departure import closure

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = 'examples/v016/kant-courteous-reference.noema'
BASIS = 'data/courteous-reference-basis-v1.json'
AUDIT = 'data/footnote-audit-v1.json'
REPORT = ROOT / 'reports/footnote-joint-v1.json'
SYMBOLS = ('hzjt', 'hzju', 'hzkk', 'hzkt', 'hzle', 'hzlr')
INDIVIDUALS = (
    'author', 'answer', 'document', 'mendelssohn', 'name', 'citation',
    'announcement', 'question', 'frame', 'counterframe', 'withholding',
    'read', 'naming', 'weekly_issue', 'weekly_series', 'weekly_name',
    'monthly_issue', 'monthly_series', 'monthly_name', 'calendar', 'year',
    'month8', 'day12', 'day29', 'trial', 'mention', 'other',
)
SCENES = ('past', 'now', 'future', 'branch', 'note')
POINTS = SCENES[:3]


def document():
    doc = parse((ROOT / DOCUMENT).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc, SYMBOLS)
    doc['statements'] = doc['statements'][18:24]
    assert tuple(s['body']['symbol'] for s in doc['statements']) == SYMBOLS
    return doc


def unknown(*args):
    raise ValueError('Unknown interpretation in joint footnote model')


def model(doc, variant='baseline', seen=None):
    values = announced.model(doc)
    own = courtesy.model()
    for name in ('dg', 'hzih'):
        first, second = values[name], own[name]
        own[name] = lambda *args, a=first, b=second: a(*args) or b(*args)
    values.update(own)
    values.update(hzik=lambda: 'document', hzla=lambda: 'trial')
    # Exactly one common actual history; the branch is a distinct hypothetical
    # context. Its earlier receipt never becomes an actual receipt.
    values['hzkm'] = lambda ctx: 'frame' if ctx == 'note' else 'counterframe'
    values['hzkn'] = lambda ctx: 'now'
    values['h7q'] = lambda frame, ctx, point: (
        frame == ('frame' if ctx == 'note' else 'counterframe') and point in POINTS
    )
    values['ic'] = lambda left, right, ctx: (
        left in POINTS and right in POINTS and POINTS.index(left) < POINTS.index(right)
    )

    def received(person, item, moment, ctx):
        if variant == 'unknown_branch_receipt' and ctx == 'branch':
            return unknown()
        contexts = ('branch', 'note') if variant == 'actual_receipt' else ('branch',)
        target = 'other' if variant == 'other_branch_recipient' else 'author'
        return (person, item, moment) == (target, 'answer', 'past') and ctx in contexts

    def selected(person, description, actual, candidate):
        syntax = json.loads(description.syntax)
        if seen is not None:
            seen.setdefault('antecedents', []).append(syntax)
        return (person, actual, candidate) == ('author', 'note', 'branch') and syntax == {
            'kind': 'function_ref', 'symbol': 'hzkr',
        }

    occurs = values['dg']
    values['dg'] = lambda act, ctx: occurs(act, ctx) or (
        (act, ctx) == ('withholding', 'branch') or
        variant == 'actual_withholding' and (act, ctx) == ('withholding', 'note')
    )
    values['hzji'] = received
    values['hzko'] = selected
    values['hzkp'] = lambda act, person, work, ctx: (
        (act, person, work) == ('withholding', 'author',
            'other' if variant == 'other_withheld_work' else 'document') and
        (ctx == 'branch' or variant == 'actual_withholding' and ctx == 'note')
    )
    values['hzkq'] = lambda work, act, ctx: (
        variant != 'no_counterfactual_influence' and
        (work, act, ctx) == ('answer', 'withholding', 'branch')
    )
    values['hzlb'] = lambda person, work, time, ctx: (
        (person, work, time, ctx) == ('author', 'document', 'now', 'note')
    )
    values['hzkz'] = lambda person, work, role, ctx: (
        variant != 'no_trial_role' and
        (person, work, role, ctx) == ('author', 'document', 'trial', 'note')
    )

    def trial(role, description, ctx):
        syntax = json.loads(description.syntax)
        if seen is not None:
            seen.setdefault('questions', []).append(syntax)
        symbol = 'hzll' if variant == 'other_trial_question' else 'hzld'
        return (role, ctx) == ('trial', 'note') and syntax == {
            'kind': 'call', 'symbol': symbol, 'arguments': [],
        }

    values['hzky'] = trial
    if variant == 'no_courtesy':
        values['hzlq'] = lambda *args: False
    if variant == 'no_answer_membership':
        contains = values['hzjw']
        values['hzjw'] = lambda *args: args != ('answer', 'monthly_issue', 'note') and contains(*args)
    if variant == 'no_citation':
        values['hzjj'] = lambda *args: False
    # These remain unknown even in a model that satisfies every assertion.
    # The trial refers to a question; it does not assert its answer.
    for name in ('hzku', 'hzkw', 'hzkx', 'hzlf', 'hzlg', 'hzlh', 'hzli'):
        values[name] = unknown
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {n: values[n] for n in required}


def evaluate(doc, values):
    return [row['value'] for row in evaluate_document(
        doc, individuals=INDIVIDUALS, situations=SCENES, primitives=values,
        max_steps=3000000, memoize_definitions=False, memoize_expressions=False,
    )]


EXPECTED_FALSE = {
    'baseline': (), 'actual_withholding': (), 'actual_receipt': (1, 3),
    'other_branch_recipient': (3,), 'other_withheld_work': (3,),
    'no_counterfactual_influence': (3,), 'no_trial_role': (4,),
    'other_trial_question': (4,), 'no_courtesy': (5,),
    'no_answer_membership': (2,), 'no_citation': (0,),
}


def checks():
    doc = document()
    rows = {}
    seen = {}
    for variant, false_indices in EXPECTED_FALSE.items():
        actual = evaluate(doc, model(doc, variant, seen))
        assert actual == [i not in false_indices for i in range(6)], (variant, actual)
        rows[variant] = actual
    assert seen['antecedents'] and all(x == {'kind': 'function_ref', 'symbol': 'hzkr'} for x in seen['antecedents'])
    assert seen['questions'] and all(x == {'kind': 'call', 'symbol': 'hzld', 'arguments': []} for x in seen['questions'])
    try:
        evaluate(doc, model(doc, 'unknown_branch_receipt'))
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown counterfactual receipt was filled in')
    return dict(contrasts=rows, stored_graph_without_lowering=True,
                memoization=False, question_contents_unknown=True,
                unknown_branch_receipt_refused=True)


def validate_audit():
    audit = json.loads((ROOT / AUDIT).read_text(encoding='utf-8'))
    validate_hashes(ROOT, audit['source_sha256'])
    catalog = load_catalog(ROOT, BASIS)
    assert audit['selection'] == selection_binding(catalog, list(range(18, 24)))
    for target, expected in audit['direct_reference_users'].items():
        actual = [name for name, entry in catalog.entries.items()
                  if target in _references(entry['declaration'].get('body'))]
        assert actual == expected, target
    inventory = json.loads((ROOT / audit['inventory']).read_text(encoding='utf-8'))
    unit = next(u for u in inventory['units'] if u['id'] == audit['unit'])
    assert audit['text'] == unit['text'] and audit['unit_sha256'] == unit['text_sha256']
    cursor = 0
    for clause in audit['clauses']:
        start, end = clause['range']
        assert start == cursor and start < end
        assert clause['source'] == unit['text'][start:end]
        assert all(n in catalog.entries for n in clause['symbols'])
        assert clause['assessment'] in ('represented_under_reading', 'open', 'structural_marker')
        cursor = end
    assert cursor == len(unit['text'])
    assert audit['decision'] == 'incomplete' and audit['open_items']
    return audit


def build_report():
    audit = validate_audit()
    prior = json.loads((ROOT / 'reports/courteous-reference-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT, prior['source_sha256'])
    pins = set(prior['source_sha256']) | set(audit['source_sha256']) | {
        AUDIT, 'reports/courteous-reference-v1.json',
        'scripts/check_footnote_joint.py', 'tests/test_footnote_joint.py',
        'docs/footnote-audit-v1.md',
    }
    return dict(status='joint_finite_model_and_incomplete_whole_footnote_audit',
        document=DOCUMENT, selection=audit['selection'], checks=checks(),
        review_decision='incomplete', clause_count=len(audit['clauses']),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(pins)})


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('All six footnote assertions checked in shared models; whole unit remains incomplete')


if __name__ == '__main__':
    main()
