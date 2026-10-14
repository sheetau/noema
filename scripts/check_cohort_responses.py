"""Check temporal membership, quantifier scope and unperformed response descriptions."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json
from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_deserved_responses import RESPONSE, BASIS, STANDARD
from scripts.compose_cohort_responses import ROOT, PARENT, BUILDERS, PAIRING, SOURCE_PAIRING, REPLY, TARGET, DUAL, MEANINGS

REPORT = ROOT / 'reports/cohort-responses-v1.json'
DOMAIN = ('oldgroup', 'newgroup', 'early', 'late', 'alice', 'bob', 'subject', 'act', 'listener')
SCENES = ('now', 'gap', 'later', 'last', 'outside')
HISTORY = SCENES[:-1]
PEOPLE = ('alice', 'bob')
FIELDS = PAIRING + [('subject', 'a'), ('response', 'h[a a a] e'), ('audience', 'h[a] c'), ('ground', 'h[a] e')]
EXTRA = ''.join('r jq' + n + '[] ' + t + '.' if t in ('a', 'd') else 'r jq' + n + t[1:] + '.' for n, t in FIELDS)
# Function declarations above have h[...] written as the primitive parameter list.
EXTRA += 'r jqstandard[a ' + RESPONSE + ' ' + BASIS + ' d] c.'
REFS = {n: ('k jq' + n + '[]' if t in ('a', 'd') else 'p jq' + n) for n, t in FIELDS}


def select(data, indices):
    result = dict(data); result['document'] = deepcopy(data['document'])
    result['document']['statements'] = [result['document']['statements'][i] for i in indices]
    return result


def setup(text, source=False, empty_standards=False):
    base = parse(text); base['statements'] = []; base = parse(format_graph(base, 'compact') + EXTRA)
    message = 'i[person a][j s[c[p jqground][v person]]]'
    raw = k('hzgb', REFS['audience'], 'r[' + message + ']') if source else REFS['response']
    refs = dict(REFS, group=REFS['nextgroup'], epoch=REFS['later'], response=raw, message='r[' + message + ']')
    scoped = k('hzgj', *(refs[n] for n, _ in DUAL)) if source else k('rok', *(refs[n] for n, _ in REPLY))
    pair = k('hzgi' if source else 'roj', *(refs[n] for n, _ in (SOURCE_PAIRING if source else PAIRING)))
    args = [refs[n] for n, _ in TARGET]
    queries = [pair]
    for point in ('later', 'last'):
        for name in ('rol', 'rom'): queries.append('t[' + k(name, *args) + '][k jq' + point + 'point[]]')
    base = parse(format_graph(base, 'compact') + 'r jqlaterpoint[] d.r jqlastpoint[] d.r jqspeaker[] a.r jqactivity[] a.')
    queries += [k('ron', *args), 'e[r[' + scoped + ']][r[' + scoped + ']]']
    removed = 0
    if source:
        spec = specialize_definition(base, 'ro6', 'jqmerit', {1: description(base, 'p jqground')})
        base = spec.document; removed = spec.disquotations_removed
        rule = 'i[subject a response ' + RESPONSE + ' basis ' + BASIS + '][b point[' + k('jqstandard', 'v subject', 'v response', 'v basis', 'v point') + ']]'
        standards = 'l[' + STANDARD + '][' + ('' if empty_standards else rule) + ']'
        merit = k('jqmerit', 'r[' + scoped + ']', standards)
        queries.append('t[c[' + merit + '][k jqsubject[]]][k jqcontext[]]')
        for point in ('context', 'laterpoint'):
            queries.append('t[c[' + scoped + '][k jqspeaker[] k jqactivity[] k jqsubject[]]][k jq' + point + '[]]')
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=source, scoped=scoped, disquotations_removed=removed,
        response_syntax=syntax(description(base, scoped)), basis_syntax=syntax(description(base, 'p jqground')),
        message_syntax=syntax(description(base, message)))


def model_for(data, bits=(True, True, True, False, False, True), variant='baseline', ground=True, worthy=True):
    # Membership followed by Alice/Bob responses at later and last.
    members = {p for p, enabled in zip(PEOPLE, bits[:2]) if enabled}
    events = {(p, s) for (p, s), enabled in zip(product(PEOPLE, ('later', 'last')), bits[2:]) if enabled}
    spans = {'early': {'now'}, 'late': {'later', 'last'}}
    if variant == 'overlapping_periods': spans['late'].add('now')
    if variant == 'outside_history': spans['late'] = {'outside'}
    if variant == 'gapped_period': spans['late'] = {'gap', 'last'}
    def belongs(group, person, context):
        if context != 'now': return False
        if variant == 'missing_member' and (group, person) == ('newgroup', 'bob'): return False
        if variant == 'extra_member' and (group, person) == ('newgroup', 'act'): return True
        return person in members and group in ('oldgroup', 'newgroup')
    def present(person, point):
        # The overlapping persons are intentional: temporal groups need not be disjoint.
        return person in members and point in ('now', 'later', 'last')
    def before(first, second):
        if variant == 'cyclic' and (first, second) == ('last', 'now'): return True
        return first in HISTORY and second in HISTORY and HISTORY.index(first) < HISTORY.index(second)
    def event(person, activity, subject, point):
        return (person, point) in events and activity == 'act' and subject == 'subject'
    model = guarded(data['document'])
    model.update(jqfirstgroup=lambda: 'oldgroup', jqnextgroup=lambda: 'oldgroup' if variant == 'same_group' else 'newgroup',
        jqearlier=lambda: 'late' if variant == 'reversed' else 'early', jqlater=lambda: 'early' if variant == 'reversed' else 'late',
        jqcontext=lambda: 'later' if variant == 'future_context' else 'now',
        jqpopulation=lambda p: p in PEOPLE and not (variant == 'changed_population' and p == 'bob'),
        jqhuman=lambda p: p in PEOPLE and not (variant == 'nonhuman' and p == 'bob'),
        jqpresent=present, jqbelongs=belongs, jqhistory=lambda s: s in HISTORY, jqbefore=before,
        jqperiods=lambda epoch, point: point in spans.get(epoch, set()),
        jqsubject=lambda: 'subject', jqresponse=lambda p, a, target: Content(SCENES, tuple(event(p, a, target, s) for s in SCENES)),
        jqlaterpoint=lambda: 'later', jqlastpoint=lambda: 'last', jqspeaker=lambda: 'alice', jqactivity=lambda: 'act',
        jqaudience=lambda p: p == 'listener' and variant != 'empty_audience',
        jqground=lambda p: Content(SCENES, (ground and p == 'subject',) * len(SCENES)),
        jqstandard=lambda subject, response, basis, point: worthy and subject == 'subject' and response.syntax == data['response_syntax'] and basis.syntax == data['basis_syntax'] and variant != 'wrong_standard')
    if data['source']:
        actual = lambda p, s: (p, s) in events or (p, s) == ('alice', 'now')
        model.update(aa=model['jqhuman'], ic=lambda first, second, context: context == 'now' and before(first, second),
            dg=lambda act, point: variant != 'no_occurrence' and act == 'act' and any(actual(p, point) for p in PEOPLE),
            f3=lambda p, act, point: variant != 'no_presenter' and act == 'act' and actual(p, point),
            f2=lambda act, audience, subject, desc, point: variant != 'no_conveyance' and (act, audience, subject) == ('act', 'listener', 'other' if variant == 'wrong_subject' else 'subject') and desc.syntax == data['message_syntax'] and variant != 'wrong_message')
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model, individuals=DOMAIN, situations=SCENES, max_steps=10_000_000)]


PAIR_CASES = ('baseline', 'missing_member', 'extra_member', 'changed_population', 'nonhuman', 'overlapping_periods', 'gapped_period', 'outside_history', 'same_group', 'reversed', 'cyclic', 'future_context')
SOURCE_CASES = ('baseline', 'no_occurrence', 'no_presenter', 'no_conveyance', 'wrong_subject', 'wrong_message', 'empty_audience', 'wrong_standard')


def checks(texts):
    data = select(setup(texts[0]), (1, 2, 3, 4, 5)); grid = []
    for bits in product((False, True), repeat=6):
        members = [i for i in range(2) if bits[i]]
        at = lambda time: [bits[2 + 2 * i + time] for i in members]
        expected = [any(at(0)), bool(members) and all(at(0)), any(at(1)), bool(members) and all(at(1)),
            bool(members) and all(bits[2 + 2 * i] or bits[3 + 2 * i] for i in members)]
        result = values(data, model_for(data, bits))
        if result != expected: raise ValueError('Temporal quantifier oracle failed: ' + repr((bits, result, expected)))
        grid.append(dict(bits=list(bits), result=result))
    print('64 membership and temporal response profiles passed', flush=True)
    pairs = []
    for index, text in enumerate(texts):
        data = select(setup(text, index > 0), (0,)); cases = {}
        for variant in PAIR_CASES:
            result = values(data, model_for(data, variant=variant))
            if result != [variant == 'baseline']: raise ValueError('Temporal cohort mismatch: ' + repr((variant, result)))
            cases[variant] = result
        pairs.append(cases)
    rows = []
    for text in texts[1:]:
        data = select(setup(text, True), (1, 2, 3, 4, 5, 6, 7, 8, 9)); cases = {}
        for variant in SOURCE_CASES:
            actual = variant in ('baseline', 'wrong_standard')
            expected = [actual, False, actual, False, actual, True, variant != 'wrong_standard', actual, actual]
            result = values(data, model_for(data, variant=variant))
            if result != expected: raise ValueError('Source response mismatch: ' + repr((variant, result, expected)))
            cases[variant] = result
        rows.append(dict(cases=cases, disquotations_removed=data['disquotations_removed']))
        print('Source response and merit contrasts passed', flush=True)
    return dict(grid=grid, temporal_cohorts=pairs, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Cohort response artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Cohort response roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']: raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = 'Welt und Nachwelt'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_cohort_responses.py', 'scripts/check_cohort_responses.py', 'scripts/compose_successive_cohorts.py', 'scripts/compose_deserved_responses.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/grammar.py', 'noema/meaning_basis.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_temporal_cohorts_and_scoped_responses', documents=documents, sizes=sizes, interpretation=checks(texts), parent_preserved=True, roundtrips=True,
        new_definitions=7, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
            range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]), verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args(); result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Cohort response record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print('Temporal groups, individual responses and response-worthiness remain distinct')


if __name__ == '__main__': main()
