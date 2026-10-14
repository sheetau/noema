"""Evaluate the complete continuing policy without dropping temporal conditions."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, FunctionValue
from noema.higher_order_semantics import evaluate_document
from scripts import check_institutional_choices as prior

ROOT = prior.ROOT
REPORT = ROOT / 'reports/continuing-policies-v1.json'
LIMIT = 16_000_000


def evaluate(data, model, scenes):
    stats = {}
    rows = evaluate_document(data['document'], individuals=prior.DOMAIN, situations=scenes,
        primitives=model, max_steps=LIMIT, statistics=stats)
    return [row['value'] for row in rows], stats


def future_model(data, failure=None):
    model, scenes = prior.policy_model(data)
    scenes = (*scenes, 'later')
    order = ('selection', 'actual', 'later')
    model['jnhistories'] = lambda point: FunctionValue(('situation',), 'truth',
        lambda item: item in (order if point in order else (point,)))
    model['jnbefore'] = lambda a, b: a in order and b in order and order.index(a) < order.index(b)
    model['jvthreats'] = lambda community: Content(scenes, tuple(
        point.startswith('w') and point[2] == '1' for point in scenes))
    state = model['jnstate']
    model['jnstate'] = lambda community, institution, point: (
        False if point == 'later' and (community, institution) == failure
        else state(community, institution, point))
    return model, scenes


def policy_checks(texts):
    cases = []
    for stem, text in texts.items():
        data = prior.policy_setup(text, continuing=True)
        for variant, expected in (('baseline', True), ('wrong_activity', False), ('inactive_policy', False)):
            print('Continuing policy', stem, variant, flush=True)
            model, scenes = prior.policy_model(data, variant)
            result, stats = evaluate(data, model, scenes)
            if result != [expected]: raise ValueError('Continuing policy mismatch: ' + repr((stem, variant, result)))
            cases.append(dict(document=stem, variant=variant, result=result, statistics=stats))
        for failure in (None, ('alpha', 'new'), ('beta', 'old')):
            print('Future continuation', stem, failure, flush=True)
            model, scenes = future_model(data, failure)
            if not (model['jnstate']('alpha', 'new', 'actual') and model['jnstate']('beta', 'old', 'actual')):
                raise ValueError('Future fixture changed the present configuration')
            result, stats = evaluate(data, model, scenes)
            if result != [failure is None]: raise ValueError('Future failure ignored: ' + repr((stem, failure, result)))
            cases.append(dict(document=stem, variant='future', future_failure=failure,
                present_configurations=True, result=result, statistics=stats))
    return cases


def choice_differential(text):
    data = prior.setup(text, source=True)
    cases = []
    for bits in product((False, True), repeat=4):
        old = prior.values(data['document'], prior.model_for(data, bits), prior.DOMAIN, prior.SCENES)
        new, stats = evaluate(data, prior.model_for(data, bits), prior.SCENES)
        if new != old: raise ValueError('Higher-order cache changed a choice')
        cases.append(dict(inputs=list(bits), reference=old, cached=new, statistics=stats))
    return cases


def recorded_configuration_comparison(text):
    # These are exactly the input constructor and variants pinned by the earlier
    # report. The new full-continuation checks above do not substitute these terms.
    previous = json.loads(prior.REPORT.read_text(encoding='utf-8'))['policy']['cases'][-3:]
    data = prior.policy_setup(text, continuing=False); cases = []
    for old in previous:
        model, scenes = prior.policy_model(data, old['variant'])
        result, stats = evaluate(data, model, scenes)
        if result != old['results']: raise ValueError('Cached configuration policy differs from pinned reference evidence')
        cases.append(dict(variant=old['variant'], reference=old['results'], cached=result, statistics=stats))
    return cases


def build_report():
    previous = json.loads(prior.REPORT.read_text(encoding='utf-8'))
    # Refuse to compare against a historical observation whose inputs changed.
    for name, digest in previous['source_sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Historical institutional fixture changed: ' + name)
    stems = ('kant-institutional-choices', 'institutional-choices-core')
    texts = {stem: (ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8') for stem in stems}
    cases = policy_checks(texts)
    comparisons = choice_differential(texts[stems[1]])
    configuration = recorded_configuration_comparison(texts[stems[1]])
    paths = {*previous['source_sha256'], 'reports/institutional-choices-v1.json',
        'noema/higher_order_semantics.py', 'scripts/check_continuing_policies.py',
        'tests/test_higher_order_semantics.py'}
    return dict(status='verified_finite_continuing_policy_examples_not_source_completion',
        engine_contract='Deterministic, pure primitives respecting Noema values; no Python identity-dependent meanings.',
        continuing_policy_cases=cases, choice_differential=comparisons, recorded_configuration_comparison=configuration,
        original_reference_preserved=True, max_steps_per_interpretation=LIMIT,
        new_definitions=0, new_primitives=0, new_author_statements=0,
        alignment=previous['alignment'], verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    report = build_report()
    # Roundtrip converts tuple-valued fixture labels to the saved JSON shape.
    report = json.loads(json.dumps(report, ensure_ascii=False))
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Continuing policy report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Full continuing policies and separate future failures checked without dropping conditions')


if __name__ == '__main__': main()
