"""Finite countermodels for assessment standards; no natural-language inference."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_contextual_ability import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/contextual-ability-v1.json'
LABELS = ('possible', 'guaranteed', 'assessed_ability', 'all_methods_assessable', 'decisive', 'assessed_inability')


def generic_document():
    text = generic_composed()[0] + '''
r za[] a.r zb[] d.r zd[a a d] c.r ze[a a d d] c.r zf[a a d d] c.r zg[d] c.
'''
    args = 'k za[] b scene[k zg[v scene]] k zb[] p zd p ze'
    for name in ('xb', 'xc', 'xd', 'xe', 'xf', 'xg'):
        parameters = 'k za[] k zb[] p zd p ze p zf' if name == 'xe' else args + (' p zf' if name in ('xd', 'xf', 'xg') else '')
        text += 'q[k ' + name + '[' + parameters + ']].\n'
    return parse(text)


def interpret_generic(doc, available, outcomes, selected, success):
    model = {'za': lambda: 'actor', 'zb': lambda: 'start',
             'zd': lambda actor, plan, start: actor == 'actor' and start == 'start' and plan in available,
             'ze': lambda actor, plan, start, end: actor == 'actor' and start == 'start' and end in outcomes.get(plan, set()),
             'zf': lambda actor, plan, start, end: actor == 'actor' and start == 'start' and end in selected.get(plan, set()),
             'zg': lambda scene: scene in success}
    return dict(zip(LABELS, (row['value'] for row in evaluate_document(
        doc, individuals=('actor', 'plan', 'backup'), situations=('start', 'left', 'right'), primitives=model)), strict=True))


def exhaustive_checks():
    doc = generic_document()
    subsets = [set(s for i, s in enumerate(('left', 'right')) if mask & (1 << i)) for mask in range(4)]
    count = 0
    for enabled, outcomes, selected, success in product((False, True), subsets, subsets, subsets):
        valid_plan = bool(selected) and selected <= outcomes
        witness = enabled and valid_plan and selected <= success
        valid = not enabled or valid_plan
        expected = dict(zip(LABELS, (enabled and bool(outcomes & success),
            enabled and bool(outcomes) and outcomes <= success, witness, valid,
            valid or witness, valid and not witness), strict=True))
        actual = interpret_generic(doc, {'plan'} if enabled else set(), {'plan': outcomes}, {'plan': selected}, success)
        if actual != expected:
            raise ValueError('Finite assessment differs: ' + repr((enabled, outcomes, selected, success, actual)))
        count += 1
    return {'models': count, 'outcome_domain_size': 2, 'available_methods_max': 1,
            'all_match_independent_set_semantics': True, 'infinite_domain_theorem_proved': False}


def contrast_checks():
    doc = generic_document()
    both = {'left', 'right'}
    cases = {
        'exception_outside_selected_scope': ({'plan'}, {'plan': both}, {'plan': {'left'}}, {'left'}, (True, False, True, True, True, False)),
        'failure_inside_selected_scope': ({'plan'}, {'plan': both}, {'plan': both}, {'left'}, (True, False, False, True, True, True)),
        'empty_scope_is_unknown_not_inability': ({'plan'}, {'plan': both}, {'plan': set()}, {'left'}, (True, False, False, False, False, False)),
        'foreign_result_invalidates_assessment': ({'plan'}, {'plan': {'left'}}, {'plan': {'right'}}, {'left'}, (True, True, False, False, False, False)),
        'unavailable_success_is_not_ability': (set(), {'plan': both}, {'plan': {'left'}}, {'left'}, (False, False, False, True, True, True)),
        'bad_unused_method_does_not_invalidate': ({'plan'}, {'plan': both}, {'plan': {'left'}, 'backup': set()}, {'left'}, (True, False, True, True, True, False)),
        'successful_method_suffices_despite_other_missing_assessment': ({'plan', 'backup'}, {'plan': both, 'backup': both}, {'plan': {'left'}, 'backup': set()}, {'left'}, (True, False, True, False, True, False)),
        'missing_assessment_prevents_inability_claim': ({'plan', 'backup'}, {'plan': both, 'backup': both}, {'plan': both, 'backup': set()}, {'left'}, (True, False, False, False, False, False)),
        'one_successful_method_suffices': ({'plan', 'backup'}, {'plan': both, 'backup': {'left'}}, {'plan': both, 'backup': {'left'}}, {'left'}, (True, True, True, True, True, False)),
        'one_method_must_cover_all_selected_results': ({'plan', 'backup'}, {'plan': both, 'backup': both}, {'plan': both, 'backup': both}, {'left'}, (True, False, False, True, True, True)),
        'changing_goal_does_not_change_selected_results': ({'plan'}, {'plan': both}, {'plan': {'left'}}, {'right'}, (True, False, False, True, True, True)),
    }
    results = {}
    for name, (available, outcomes, selected, success, expected) in cases.items():
        actual = interpret_generic(doc, available, outcomes, selected, success)
        if tuple(actual.values()) != expected:
            raise ValueError('Ability contrast differs: ' + name)
        results[name] = actual
    return results


def source_checks():
    doc = parse(source_composed()[0])
    doc['statements'] = []
    prefix = format_graph(doc, 'compact') + '\nr za[] d.r zb[] a.\n'
    args = 'k ao[] k bb[k ao[]] k wh[]'
    text = prefix + 'q[k ba[' + args + ']].q[k bc[k ao[] k wh[]]].'
    text += 'q[k xd[' + args + ' p ae p af p ap]].q[k xg[' + args + ' p ae p af p ap]].'
    text += 'q[k be[k ao[] k zb[] k wh[] k za[]]].'
    doc = parse(text)
    individuals = ('reader', 'plan', 'faculty', 'act', 'change')
    scenes = ('start', 'after', 'left', 'right')
    results = {}
    variants = {
        'exception_outside_scope': ({'left'}, {'left'}, (False, False, True, False, False)),
        'failure_inside_scope': ({'left', 'right'}, {'left', 'right'}, (False, True, False, True, False)),
        'valid_exit': ({'left', 'right'}, {'left'}, (False, True, False, True, True)),
        'missing_assessment_not_exit': ({'left', 'right'}, set(), (False, True, False, True, False)),
        'foreign_assessment_not_exit': ({'left', 'right'}, {'start'}, (False, True, False, True, False)),
        'missing_assessment_not_immaturity': (set(), {'left'}, (False, False, False, False, False)),
    }
    from scripts.check_kant_discourse import base_model
    for name, (before, after, expected) in variants.items():
        model = base_model(doc)
        model.update({'ao': lambda: 'reader', 'wh': lambda: 'start', 'za': lambda: 'after', 'zb': lambda: 'change',
            'aa': lambda person: person == 'reader',
            'ab': lambda faculty, person, scene: (faculty, person) == ('faculty', 'reader'),
            'ac': lambda person, faculty, act, scene: (person, faculty, act, scene) == ('reader', 'faculty', 'act', 'left'),
            'ae': lambda person, plan, scene: (person, plan) == ('reader', 'plan'),
            'af': lambda person, plan, start, end: (person, plan) == ('reader', 'plan') and end in ('left', 'right'),
            'ap': lambda person, plan, start, end: (person, plan) == ('reader', 'plan') and end in (after if start == 'after' else before),
            'ag': lambda change, before, after: (change, before, after) == ('change', 'start', 'after'),
            'ak': lambda person, scene: True,
            'ah': lambda factor, effect, scene: all(factor.values)})
        actual = [r['value'] for r in evaluate_document(doc, individuals=individuals, situations=scenes,
                                                       primitives=model, max_steps=1000000)]
        if actual != list(expected):
            raise ValueError('Kant contextual ability differs: ' + name + repr(actual))
        results[name] = dict(zip(('old_guarantee', 'immaturity', 'assessed_ability', 'assessed_inability', 'exit'), actual, strict=True))
    return results


def attribution_check():
    from scripts.check_kant_discourse import base_model, NODES, DOMAIN
    doc = parse(source_composed()[0])
    model = base_model(doc)
    def unexpected(*args):
        raise ValueError('Attribution evaluated the selected ability standard')
    for name in ('aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag', 'ah', 'ai', 'aj', 'ak', 'al', 'am', 'ap'):
        model[name] = unexpected
    seen = []
    def describe(node, author, description, scene):
        seen.append((node, json.loads(description.syntax)['symbol']))
        return author == 'author' and scene == 'text'
    model.update(ua=describe, ub=describe, uc=describe,
        ud=lambda *args: True, uf=lambda *args: True,
        ue=lambda left, right, scene: left in NODES and right in NODES and NODES.index(left) < NODES.index(right))
    rows = evaluate_document(doc, individuals=DOMAIN, situations=('text',), primitives=model)
    expected = [('first', 'bi'), ('second', 'bf'), ('third', 'bp'), ('latin', 'bl'), ('german', 'bn'), ('conclusion', 'bo')]
    if seen != expected or rows != [{'kind': 'assert', 'value': True}]:
        raise ValueError('Updated ability definition not connected to source discourse')
    return {'references': [list(row) for row in seen], 'underlying_contents_evaluated': False}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored ability document differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Ability roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    from scripts.check_kant_discourse import source_alignment
    alignment = source_alignment()
    alignment['ability_reading'] = 'explicit_contextual_assessment_not_guarantee_over_all_outcomes'
    alignment['source_specifies_unique_selection_standard'] = False
    files = [*documents, 'examples/v013/kant-opening-discourse.noema', 'data/kant-opening-discourse-basis-v1.json',
        'data/contextual-ability-basis-v1.json', 'data/kant-contextual-ability-basis-v1.json',
        'data/kant-opening-alignment-v1.json', 'scripts/compose_contextual_ability.py', 'scripts/check_contextual_ability.py',
        'scripts/check_kant_discourse.py', 'scripts/compose_limits.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'contextual_ability_partial_reading', 'documents': documents, 'roundtrips': True,
        'exhaustive_finite_models': exhaustive_checks(), 'contrasts': contrast_checks(), 'source_checks': source_checks(),
        'attribution': attribution_check(), 'source_alignment': alignment,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Contextual ability report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('128 finite assessments, 11 contrasts, 6 source cases; source equivalence remains partial')


if __name__ == '__main__':
    main()
