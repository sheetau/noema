"""Verify non-evaluating description construction and exact personal-purpose links."""
import argparse
from copy import deepcopy
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document, Content
from noema.script import transcribe
from scripts.compose_constructed_purposes import ROOT, PARENT, EXAMPLE, build_example

REPORT = ROOT / 'reports/constructed-purposes-v1.json'
PEOPLE = ('alice', 'bob')
SCENES = ('now',)


def construction_checks():
    doc = parse((ROOT / EXAMPLE).read_text(encoding='utf-8'))
    observations = []
    def forbidden(*args):
        raise ValueError('Construction or consistency checking executed quoted contents')
    def choose(person, first, second):
        return first if person == 'alice' else second
    def inspect(person, criterion, message, purpose):
        criterion_body = json.loads(criterion.syntax)
        message_body = json.loads(message.syntax)
        purpose_body = json.loads(purpose.syntax)
        if criterion_body != {'kind': 'function_ref', 'symbol': 'jown' if person == 'alice' else 'jother'}:
            raise ValueError('Personal criterion was replaced')
        if message.rank != 0 or message_body['kind'] != 'apply' or message_body['arguments'] != [criterion_body]:
            raise ValueError('Message does not contain the exact criterion syntax')
        expected_purpose = {'kind': 'apply', 'function': {'kind': 'function_ref', 'symbol': 'hzx'}, 'arguments': [
            {'kind': 'call', 'symbol': 'jrecipient', 'arguments': []},
            {'kind': 'call', 'symbol': 'jsubject', 'arguments': []}, {'kind': 'quote', 'body': message_body}]}
        if purpose.rank != 0 or purpose_body != expected_purpose:
            raise ValueError('Purpose does not contain the exact message syntax')
        observations.append(dict(person=person, criterion=criterion_body['symbol'], message=message_body, purpose=purpose_body))
        return True
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(jselect=choose, jinspect=inspect)
    result = evaluate_document(doc, individuals=PEOPLE, situations=SCENES, primitives=model)
    if result != [{'kind': 'assert', 'value': True}] or len(observations) != 2:
        raise ValueError('Personal construction results differ')
    if observations[0]['message'] == observations[1]['message'] or observations[0]['purpose'] == observations[1]['purpose']:
        raise ValueError('Personal descriptions were conflated')
    doc['statements'] = []
    checked = parse(format_graph(doc, 'compact') +
        'q[f person a[k rqc[k jqcriterion[v person] r[k jrecipient[]] r[k jsubject[]] k jqmessage[v person] k jqpurpose[v person]]]].')
    if evaluate_document(checked, individuals=PEOPLE, situations=SCENES, primitives=model) != [{'kind': 'ask', 'value': True}]:
        raise ValueError('Exact consistency condition differs')
    return observations


def collision_checks():
    """Same finite truth profiles do not justify replacing the descriptions."""
    doc = parse((ROOT / EXAMPLE).read_text(encoding='utf-8')); doc['statements'] = []
    text = format_graph(doc, 'compact') + 'r jalias[] a.r jflip[a] a.'
    # This extra recipient expression has the same value in the test model, but
    # is a different expression. The constructor does not erase the distinction.
    text += 'd jwrong[person a] i[e][k rqb[r[k jalias[]] r[k jsubject[]] k jqmessage[v person]]].'
    text += 'q[f person a[e[s[k jqpurpose[v person]]][s[k jwrong[v person]]]]].'
    text += 'q[f person a[e[k jqpurpose[v person]][k jwrong[v person]]]].'
    text += 'q[f person a[k rqc[k jqcriterion[v person] r[k jrecipient[]] r[k jsubject[]] k jqmessage[v person] k jwrong[v person]]]].'
    text += 'q[f person a[e[c[s[k jqmessage[v person]]][k jsubject[]]][c[s[k jqmessage[k jflip[v person]]]][k jsubject[]]]]].'
    text += 'q[f person a[k rqc[k jqcriterion[v person] r[k jrecipient[]] r[k jsubject[]] k jqmessage[k jflip[v person]] k jqpurpose[k jflip[v person]]]]].'
    doc = parse(text)
    def forbidden(*args):
        raise ValueError('Unspecified model field was evaluated')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(jselect=lambda person, first, second: first if person == 'alice' else second,
        jown=lambda bindings: Content(SCENES, (False,)), jother=lambda bindings: Content(SCENES, (False,)),
        jrecipient=lambda: 'alice', jalias=lambda: 'alice', jsubject=lambda: 'bob',
        jflip=lambda person: 'bob' if person == 'alice' else 'alice',
        h6t=lambda *args: False, fa=lambda *args: False, fb=lambda *args: False, hzv=lambda *args: False)
    result = [r['value'] for r in evaluate_document(doc, individuals=PEOPLE, situations=SCENES, primitives=model)]
    if result != [True, False, False, True, False]:
        raise ValueError(('Finite-profile substitution was not distinguished', result))
    return dict(equal_purpose_profiles=result[0], same_purpose_description=result[1], wrong_purpose_accepted=result[2],
        equal_message_profiles=result[3], other_persons_message_accepted=result[4])


def build_report():
    text = build_example()
    if (ROOT / EXAMPLE).read_text(encoding='utf-8') != text:
        raise ValueError('Stored constructed-purpose example differs')
    doc = parse(text)
    for notation in ('full', 'compact'):
        form = format_graph(doc, notation)
        if parse(form) != doc or parse(transcribe(form, alphabet='v2')) != doc:
            raise ValueError('Construction syntax roundtrip differs')
    paths = [PARENT, EXAMPLE, 'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/constructed_render.py', 'noema/guarded_ranked_semantics.py', 'noema/extraction.py',
        'scripts/compose_constructed_purposes.py', 'scripts/check_constructed_purposes.py', 'tests/test_quotation_construction.py']
    return dict(status='opt_in_typed_quotation_construction_and_exact_purpose_link',
        document=EXAMPLE, declarations=len(doc['declarations']), statements=len(doc['statements']),
        personal_constructions=construction_checks(), finite_profile_contrasts=collision_checks(), roundtrips=True,
        limitations=['This is a syntax constructor, not automatic natural-language translation.',
            'Exact syntax matching is intentionally stricter than extensional equality; synonymous descriptions need not match.',
            'Construction does not prove the truth of the constructed content.',
            'The complete public action description and the Kant author attribution have not yet been connected to these constructors.',
            'The earlier runtime ceiling and finite-domain limits remain; no static effect soundness or termination theorem is claimed.',
            'No source coverage or semantic-completion count is increased.'],
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths})


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args(argv)
    report = build_report()
    if args.verify_only:
        if json.loads(REPORT.read_text(encoding='utf-8')) != report:
            raise ValueError('Stored construction report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Two exact personal message/purpose constructions checked; equal profiles do not replace descriptions')


if __name__ == '__main__':
    main()
