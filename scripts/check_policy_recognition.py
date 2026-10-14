"""Verify content-sensitive attitudes and their actual nested policy connection."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_policy_recognition import ROOT, PARENT, SOURCE, CORE, BASIS, CODE, build, basis, definitions
from scripts.check_public_permission_risk import setup as risk_setup, DOMAIN, SCENES
from scripts.compose_public_permission_risk import INPUTS, FIELD_SYMBOLS
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k

REPORT = ROOT / 'reports/policy-recognition-v1.json'


@lru_cache(maxsize=1)
def generic_setup():
    target = 'r c[b point[k jdtruth[v point]]]'
    alias = 'r c[b point[w[k jdtruth[v point]][e[n p a b][n p a b]]]]'
    text = 'p:' + definitions()
    text += 'r jdtruth[d] c.r jdperson[] a.r jdcontext[] d.'
    text += 'r jdaware[a ' + CODE + ' d] c.r jdcandidates[a ' + CODE + ' d d] c.'
    text += 'r jdstore[' + CODE + ' ' + CODE + '] c.'
    queries = [k('jdstore', target, alias)]
    for symbol in ('rro', 'rrp', 'rrq'):
        args = [k('jdperson'), target, k('jdcontext'), 'p jdcandidates']
        if symbol != 'rro': args.append('p jdaware')
        queries.append(k(symbol, *args))
    queries.append('t[s[' + target + ']][k jdcontext[]]')
    return parse(text + ''.join('q[' + q + '].' for q in queries))


def generic_values(aware=True, selected=('one',), truths=(True, True, True), variant='baseline'):
    stored = {}
    def capture(target, alias):
        assert target.rank == alias.rank == 2 and target.syntax != alias.syntax
        stored.update(target=target, alias=alias)
        return True
    def matches(person, code, context, which):
        return (person, context) == ('other' if variant == 'wrong_person' else 'person',
            'one' if variant == 'wrong_context' else 'current') and code.syntax == stored[
                'alias' if variant == which else 'target'].syntax
    def awareness(person, code, context):
        if variant == 'unknown_awareness': raise ValueError('Unknown awareness')
        return aware and matches(person, code, context, 'wrong_awareness_target')
    def candidates(person, code, context, candidate):
        if variant == 'unknown_candidates': raise ValueError('Unknown candidates')
        return candidate in selected and matches(person, code, context, 'wrong_candidate_target')
    model = dict(jdstore=capture, jdperson=lambda: 'person', jdcontext=lambda: 'current',
        jdtruth=lambda point: dict(zip(('current', 'one', 'two'), truths))[point],
        jdaware=awareness, jdcandidates=candidates)
    return [r['value'] for r in evaluate_document(generic_setup(), individuals=('person', 'other'),
        situations=('current', 'one', 'two'), primitives=model)]


@lru_cache(maxsize=1)
def source_setup():
    fixture = risk_setup()
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    names = {d['name'] for d in doc['declarations']}
    doc['declarations'] += [deepcopy(d) for d in fixture['document']['declarations'] if d['name'] not in names]
    captures = deepcopy(fixture['document']['statements'][:3])
    doc['statements'] = []
    text = 'r jdsafety[' + CODE + '] c.'
    target = 'r c[k hzmsafety[]]'
    queries = [k('jdsafety', target)]
    for symbol in ('rro', 'rrp', 'rrq'):
        args = [k('hzmruler'), target, k('wh'), 'p hznalternatives']
        if symbol != 'rro': args.append('p hznawareness')
        queries.append(k(symbol, *args))
    queries += ['t[s[r d[k hzninsight[]]]][k wh[]]', 't[s[' + target + ']][k wh[]]']
    doc = parse(format_graph(doc, 'compact') + text + ''.join('q[' + q + '].' for q in queries))
    statements = captures + doc['statements']
    doc['statements'] = []
    # Closed local descriptions are supplied by Noema definitions, so the
    # model needs no mutable capture state. This permits pure memoization.
    fixture_primitives = [d for d in doc['declarations'] if d['name'].startswith('jd')]
    selectors = ''.join(definition(FIELD_SYMBOLS[n], 'person a activity a anchor d', fixture['arguments'][n], t) for n,t in INPUTS)
    stub = {**doc, 'declarations': fixture_primitives}
    replacements = {d['name']: d for d in parse(format_graph(stub, 'compact') + selectors)['declarations']}
    doc['declarations'] = fixture_primitives + [replacements.get(d['name'], d) for d in doc['declarations'] if not d['name'].startswith('jd')]
    doc = parse(format_graph(doc, 'compact'))
    doc['statements'] = statements
    argument_codes = captures[0]['body']['arguments']
    target = {'kind': 'apply', 'function': {'kind': 'function_ref', 'symbol': 'rrh'},
        'arguments': [code if name == 'message' else code['body'] for (name,_),code in zip(INPUTS,argument_codes,strict=True)]}
    policy_call = next(d['body'] for d in doc['declarations'] if d['name'] == 'hzmpolicy')
    policy = {'kind': 'apply', 'function': {'kind': 'function_ref', 'symbol': 'rrj'},
        'arguments': [code['body'] for code in policy_call['arguments']]}
    return {**fixture, 'document': doc, 'target_syntax': target, 'policy_syntax': policy,
        'argument_bodies': [code['body'] for code in argument_codes]}


def source_values(aware=True, candidates=('safe',), actual_safe=True, actual_grant=False, variant='baseline', memoize=True):
    data = source_setup()
    def forbidden(*args): raise AssertionError('Attitude required an unspecified primitive or action execution')
    model = {d['name']: forbidden for d in data['document']['declarations'] if d['kind'] == 'primitive'}
    safety = {'kind': 'call', 'symbol': 'hzmsafety', 'arguments': []}
    def matches(person, code, context):
        return (person, context) == ('other' if variant == 'wrong_person' else 'ruler',
            'safe' if variant == 'wrong_context' else 'anchor') and json.loads(code.syntax) == safety
    def alternatives(person, code, context, candidate):
        return matches(person, code, context) and candidate in candidates
    def prospects(policy, context, outcome):
        # Validate the exact original policy; evaluate its safety separately
        # in each epistemic candidate, without changing its population anchor.
        validated = policy.rank == 1 and json.loads(policy.syntax) == data['policy_syntax']
        result = {'anchor': 'safe' if actual_safe else 'bad', 'safe': 'safe', 'bad': 'bad', 'outside': 'safe'}[context]
        return validated and outcome == result
    def allowed(ruler, person, role, act, code, sign, point):
        return ((ruler, person, role, act, sign) == ('ruler', 'person', 'role', 'act', True)
            and json.loads(code.syntax) == data['target_syntax']
            and (point in ('safe','bad') or (point == 'anchor' and actual_grant)))
    model.update(jdcapture=lambda *codes: [json.loads(code.syntax) for code in codes] == data['argument_bodies'],
        jdtargets=lambda code, alias: json.loads(code.syntax) == data['target_syntax'] and code.syntax != alias.syntax,
        jdpolicy=lambda code: code.rank == 1 and json.loads(code.syntax) == data['policy_syntax'],
        jdsafety=lambda code: code.rank == 2 and json.loads(code.syntax) == safety,
        jdrole=lambda: 'role', jdsubject=lambda: 'topic', jdrecipient=lambda: 'world', jdchannel=lambda: 'channel',
        hzmruler=lambda: 'ruler', wh=lambda: 'anchor',
        hzmpeople=lambda person, point: (person,point) == ('person','anchor'),
        hzmactivities=lambda person, act, point: act == 'act' and point == 'anchor',
        h7a=lambda *args: False, h7b=allowed,
        hzmadverse=lambda point: point in ('bad','outside'), hznalternatives=alternatives,
        hznawareness=lambda person, code, context: aware and matches(person, code, context),
        hzmprospects=prospects)
    return [r['value'] for r in evaluate_document(data['document'], individuals=DOMAIN,
        situations=SCENES, primitives=model, max_steps=100_000_000,
        memoize_definitions=memoize, memoize_expressions=memoize)]


def attribution(doc):
    selected = deepcopy(doc); selected['statements'] = selected['statements'][-1:]
    rows = []
    for granted in (False, True):
        def forbidden(*args): raise AssertionError('Attribution executed the attitude or policy')
        def attributed(node, author, code, scope, context):
            assert (node, author, scope, context) == ('node', 'author', 'scope', 'context')
            assert code.rank == 3 and json.loads(code.syntax) == {'kind': 'call', 'symbol': 'hzninsight', 'arguments': []}
            return granted
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update(hznreport=attributed, hznnode=lambda: 'node', wa=lambda: 'author',
            hznscope=lambda: 'scope', wh=lambda: 'context')
        result = evaluate_document(selected, individuals=('node', 'author', 'scope'), situations=('context',), primitives=model)
        assert result == [{'kind': 'assert', 'value': granted}]
        rows.append(result)
    return rows


def build_report():
    texts = build(); assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    documents = {}
    for path, text in texts.items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            formatted = format_graph(doc, notation)
            assert parse(formatted) == doc and parse(transcribe(formatted, alphabet='v2')) == doc
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']),
            characters=len(text), attribution=attribution(doc))
    parent, source = [parse((ROOT / path).read_text(encoding='utf-8')) for path in (PARENT, SOURCE)]
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'][:-1] == parent['statements'][:-1]
    matrix = []
    for aware, one, two, current, first, second in product((False, True), repeat=6):
        selected = tuple(p for p, flag in (('one', one), ('two', two)) if flag)
        judgment = bool(selected) and (not one or first) and (not two or second)
        result = generic_values(aware, selected, (current, first, second))
        assert result == [True, judgment, aware and judgment, aware and judgment and current, current]
        matrix.append(dict(aware=aware, selected=selected, truths=[current, first, second], result=result))
    contrasts = {}
    for variant in ('wrong_person', 'wrong_context', 'wrong_awareness_target', 'wrong_candidate_target'):
        result = generic_values(variant=variant)
        assert result == [True, variant == 'wrong_awareness_target', False, False, True]
        contrasts[variant] = result
    source_cases = []
    for aware, actual in product((False, True), repeat=2):
        for candidates in ((), ('safe',), ('bad',), ('safe', 'bad')):
            judgment = candidates == ('safe',)
            result = source_values(aware=aware, candidates=candidates, actual_safe=actual)
            assert result == [True]*4 + [judgment, aware and judgment, aware and judgment and actual, aware and judgment and actual, actual]
            source_cases.append(dict(aware=aware, actual_safe=actual, candidates=candidates, result=result))
    uncached = source_values(actual_safe=False, memoize=False)
    assert uncached == source_values(actual_safe=False)
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0016')
    segments = []
    for phrase in ('sieht ein', 'es ohne Gefahr sei, seinen Unterthanen zu erlauben, von ihrer eigenen Vernunft öffentlichen Gebrauch zu machen'):
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start+len(phrase)],
            text=phrase, status='explicit_interpretive_annotation', definitions=['rro','rrp','rrq','hzninsight','hznattribution']))
    paths = [PARENT, SOURCE, CORE, BASIS, 'scripts/compose_policy_recognition.py', 'scripts/check_policy_recognition.py',
        'tests/test_policy_recognition.py', 'scripts/check_public_permission_risk.py', 'scripts/compose_public_permission_risk.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/guarded_ranked_semantics.py', 'artifacts/written-units-v1/kant-1784.json']
    # JSON round-trip keeps stored tuples and in-memory lists comparable.
    result = dict(status='partial_policy_recognition_source_connection', documents=documents,
        parent_declarations_and_first_16_statements_preserved=True, revised_fragment_attributions=1,
        finite_interpretation=dict(matrix=matrix, contrasts=contrasts, source_cases=source_cases,
            pure_fixture_memoization_checked_against_uncached_false_actual_case=uncached), roundtrips=True,
        alignment=dict(semantic_completion=False, segments=segments), limitations=basis()['unresolved'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})
    return json.loads(json.dumps(result))


def main():
    cli = argparse.ArgumentParser(description=__doc__); cli.add_argument('--verify-only', action='store_true'); args = cli.parse_args()
    result = build_report()
    if args.verify_only:
        assert json.loads(REPORT.read_text(encoding='utf-8')) == result
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Description-sensitive recognition and the nested source policy verified')


if __name__ == '__main__':
    main()
