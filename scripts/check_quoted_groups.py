"""Check group scope without evaluating or collapsing quoted utterances."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_quoted_groups import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/quoted-groups-v1.json'


def parts_of(sequence):
    return [json.loads(item.syntax)['symbol'] for item in sequence.items]


def generic_checks():
    prefix = generic_composed()[0] + 'r za[] f.r zb[] f.r zc[a] e.r wa[] d.\n'
    def forbidden(*args):
        raise ValueError('Group scope evaluated a quoted utterance or topic')
    rows = []
    for length in range(4):
        for names in product(('za', 'zb'), repeat=length):
            sequence = 'l[i[f]][' + ' '.join('r[k ' + name + '[]]' for name in names) + ']'
            doc = parse(prefix + 'q[k gb[' + sequence + ' r[p zc] k wa[]]].'
                        + 'q[k gc[' + sequence + ' r[k za[]]]].q[k gc[' + sequence + ' r[k zb[]]]].')
            model = {'za': forbidden, 'zb': forbidden, 'zc': forbidden, 'wa': lambda: 'context',
                'ga': lambda parts, topic, scene: parts_of(parts) == ['za', 'zb']
                      and json.loads(topic.syntax) == {'kind': 'function_ref', 'symbol': 'zc'} and scene == 'context'}
            actual = [r['value'] for r in evaluate_document(doc, individuals=('object',), situations=('context',), primitives=model)]
            expected = [names == ('za', 'zb'), 'za' in names, 'zb' in names]
            if actual != expected:
                raise ValueError('Group order, repetition or membership differs')
            rows.append({'parts': list(names), 'whole_role': actual[0], 'first_member': actual[1], 'second_member': actual[2]})
    # Even a permissive role interpretation cannot make an empty formula valid.
    doc = parse(prefix + 'q[k gb[l[i[f]][] r[p zc] k wa[]]].')
    model['ga'] = lambda *args: True
    if evaluate_document(doc, individuals=('object',), situations=('context',), primitives=model)[0]['value']:
        raise ValueError('Empty quoted group accepted')
    return {'ordered_sequences': rows, 'empty_rejected_even_if_role_primitive_true': True,
            'underlying_contents_evaluated': False}


def source_checks():
    doc = parse(source_composed()[0])
    doc['statements'] = []
    text = format_graph(doc, 'compact') + '''
q[t[k bo[]][k wh[]]].
q[k gb[l[i[f]][r[k bl[k ao[]]]] r[p bi] k wh[]]].
q[k gb[l[i[f]][r[k bn[k ao[]]]] r[p bi] k wh[]]].
q[k gb[l[i[f]][r[k bn[k ao[]]] r[k bl[k ao[]]]] r[p bi] k wh[]]].
q[k gb[l[i[f]][r[k bl[k ao[]]] r[k bl[k ao[]]]] r[p bi] k wh[]]].
q[k gc[k bt[] r[k bl[k ao[]]]]].
q[k gc[k bt[] r[k bn[k ao[]]]]].
'''
    doc = parse(text)
    from scripts.check_kant_discourse import base_model, DOMAIN
    variants = {
        'whole_only': ({('bl', 'bn')}, [True, False, False, False, False]),
        'latin_only': ({('bl',)}, [False, True, False, False, False]),
        'german_only': ({('bn',)}, [False, False, True, False, False]),
        'both_separate_only': ({('bl',), ('bn',)}, [False, True, True, False, False]),
        'reversed_only': ({('bn', 'bl')}, [False, False, False, True, False]),
        'duplicate_only': ({('bl', 'bl')}, [False, False, False, False, True]),
        'whole_and_parts': ({('bl', 'bn'), ('bl',), ('bn',)}, [True, True, True, False, False]),
        'wrong_topic': ({('bl', 'bn')}, [False] * 5),
        'wrong_context': ({('bl', 'bn')}, [False] * 5),
    }
    results = {}
    for name, (roles, expected) in variants.items():
        model = base_model(doc)
        def forbidden(*args):
            raise ValueError('Grouped motto evaluated an utterance or topic')
        for declaration in doc['declarations']:
            if declaration['kind'] == 'primitive' and declaration['parameters']:
                model[declaration['name']] = forbidden
        model['ga'] = lambda parts, topic, scene: (tuple(parts_of(parts)) in roles
            and json.loads(topic.syntax) == {'kind': 'function_ref', 'symbol': 'bf' if name == 'wrong_topic' else 'bi'}
            and scene == ('other' if name == 'wrong_context' else 'text'))
        actual = [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=('text', 'other'), primitives=model)]
        if actual != expected + [True, True]:
            raise ValueError('Source quoted scope differs: ' + name)
        results[name] = dict(zip(('whole', 'latin', 'german', 'reverse', 'duplicate', 'latin_member', 'german_member'), actual, strict=True))
    return results


def attribution_check():
    from scripts.check_kant_discourse import base_model, NODES, DOMAIN
    doc = parse(source_composed()[0])
    results = {}
    for variant in ('baseline', 'reversed_explanation', 'missing_explanation', 'missing_latin_quote'):
        model = base_model(doc)
        seen = []
        def forbidden(*args):
            raise ValueError('Attribution evaluated quoted contents or the motto role')
        for declaration in doc['declarations']:
            if declaration['kind'] == 'primitive' and declaration['parameters']:
                model[declaration['name']] = forbidden
        def describe(node, author, description, context):
            seen.append([node, json.loads(description.syntax)['symbol']])
            return (author, context) == ('author', 'text') and not (variant == 'missing_latin_quote' and node == 'latin')
        model.update(ua=describe, ub=describe, uc=describe, ud=lambda *args: True,
            ue=lambda a, b, scene: a in NODES and b in NODES and NODES.index(a) < NODES.index(b),
            uf=lambda author, explained, gloss, scene: variant != 'missing_explanation'
                and (author, explained, gloss, scene) == ('author', * (('german', 'latin') if variant == 'reversed_explanation' else ('latin', 'german')), 'text'))
        actual = evaluate_document(doc, individuals=DOMAIN, situations=('text',), primitives=model)[0]['value']
        if actual != (variant == 'baseline') or seen != [[n, s] for n, s in zip(NODES, ('bi', 'bf', 'bp', 'bl', 'bn', 'bo'), strict=True)]:
            raise ValueError('Grouped source discourse differs: ' + variant)
        results[variant] = {'actual': actual, 'references': seen, 'contents_evaluated': False}
    return results


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored grouped quote differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Quoted group roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    from scripts.check_kant_discourse import source_alignment
    alignment = source_alignment()
    alignment['segments'][3]['reading'] = 'independent_lexical_review_compositional_discernment_candidate'
    alignment['segments'][5]['reading'] = 'ordered_latin_and_german_group_as_motto_candidate'
    alignment.update(motto_scope_uniquely_verified=False, facsimile_review='pending',
        consulted_transcription='https://de.wikisource.org/wiki/Beantwortung_der_Frage:_Was_ist_Aufkl%C3%A4rung%3F',
        facsimile_attempts=[{'url': 'https://ds.ub.uni-bielefeld.de/viewer/image/2239816_004/513/', 'result': 'access_denied'},
                           {'url': 'https://www.deutschestextarchiv.de/book/view/kant_aufklaerung_1784/17', 'result': 'image_not_viewed_in_this_environment'}])
    files = [*documents, 'data/quoted-groups-basis-v1.json', 'data/kant-quoted-group-basis-v1.json',
        'examples/v013/kant-reasoned-judgment.noema', 'data/kant-reasoned-judgment-basis-v1.json',
        'scripts/compose_quoted_groups.py', 'scripts/check_quoted_groups.py', 'scripts/check_kant_discourse.py',
        'data/kant-opening-alignment-v1.json', 'noema/discourse.py', 'noema/finite_semantics.py', 'noema/language.py']
    return {'status': 'quoted_group_scope_candidate', 'documents': documents, 'roundtrips': True,
        'generic_checks': generic_checks(), 'source_checks': source_checks(), 'attribution': attribution_check(),
        'source_alignment': alignment, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Quoted group report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('15 quoted sequences, 9 source scopes and 4 discourse cases checked')


if __name__ == '__main__':
    main()
