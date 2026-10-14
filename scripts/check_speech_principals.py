"""Check positive self-attribution and audience-independent role distinctions."""
import argparse
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded, callbacks
from scripts.compose_limits import call as k
from scripts.compose_speech_principals import ROOT, PARENT, BUILDERS, CORE, OWN, ATTRIBUTED, RELATIONS, PRIVATE, PUBLIC, PAIR, SHARED, GENERIC_PAIR

REPORT = ROOT / 'reports/speech-principals-v1.json'
FIELDS = list(dict(PAIR + GENERIC_PAIR).items())
SYMBOLS = {name: 'jq' + chr(97 + i // 26) + chr(97 + i % 26) for i, (name, _) in enumerate(FIELDS)}
SCENES = ('now', 'elsewhere')
MESSAGES = {'officemessage': 'jqzx', 'publicmessage': 'jqzy'}


def expression(name):
    return 'r[p ' + MESSAGES[name] + ']' if name in MESSAGES else 'k ' + SYMBOLS[name] + '[]'


def bound(fields, prefix):
    return [expression(n if n in dict(SHARED) or n in dict(RELATIONS) else prefix + n) for n, _ in fields]


def fixture():
    extra = ''.join('r ' + SYMBOLS[n] + '[] ' + t + '.' for n, t in FIELDS if n not in MESSAGES)
    extra += ('r jqzz[a d] c.d jqzx[subject a] f[j s[b point[k jqzz[v subject v point]]]].'
              'd jqzy[subject a] f[j s[b point[k jqzz[v subject v point]]]].'
              'd jqzw[subject a] f[j q[b point[k jqzz[v subject v point]]]].')
    queries = [k('rhe', *bound(OWN + ATTRIBUTED, 'public')), k('rhf', *bound(CORE + RELATIONS, 'office')),
               k('rhg', *(expression(n) for n, _ in GENERIC_PAIR)),
               k('hzb3', *bound(PRIVATE, 'office')), k('hzb4', *bound(PUBLIC, 'public')),
               k('hzb5', *(expression(n) for n, _ in PAIR)),
               k('zzp', expression('person'), expression('officeactivity'), expression('officerole'), expression('context')),
               k('zzo', expression('person'), expression('publicactivity'), expression('publicrole'), expression('context')),
               k('h6v', *(expression(n) for n in ('person', 'publicactivity', 'publicrole', 'publicrecipient', 'publicchannel', 'publicsubject', 'publicmessage', 'context'))),
               k('rhh', expression('publicaudience'), 'i[reader a][k h6t[' + expression('publicrecipient') + ' v reader ' + expression('context') + ']]')]
    return extra + ''.join('q[' + q + '].' for q in queries)


def model_for(doc, *, bits=(True,) * 7, office_size=2, actual=(True, False, False), intended=(True, True, True), variant='baseline'):
    office_occurs, office_voice, entrusted, own_occurs, own_voice, scholar, public = bits
    readers = tuple('reader' + str(i) for i in range(3))
    members = tuple('member' + str(i) for i in range(office_size))
    scalar = {n: n for n, t in FIELDS if t in ('a', 'd')}
    scalar['person'] = 'speaker'; scalar['context'] = 'now'
    if variant == 'principal_is_self': scalar['officeprincipal'] = 'speaker'
    if variant == 'same_activity': scalar['publicactivity'] = scalar['officeactivity']
    domain = tuple(dict.fromkeys([*scalar.values(), *readers, *members, 'outsider', 'other']))
    model = guarded(doc)
    for n, value in scalar.items(): model[SYMBOLS[n]] = lambda value=value: value
    def match(actual_values, expected, category, labels):
        expected = list(expected)
        for i, label in enumerate(labels):
            if variant == category + '_' + label: expected[i] = 'elsewhere' if label == 'context' else 'other'
        return list(actual_values) == expected
    def selected(which, reader):
        if which == 'office': return reader in members
        return any(chosen and reader == name for name, chosen in zip(readers, actual)) or (variant == 'outsider' and reader == 'outsider')
    def message_ok(message, which, category):
        name = MESSAGES[which + 'message']
        if variant == category + '_alias': name = MESSAGES['office' + 'message' if which == 'public' else 'publicmessage']
        if variant == category + '_force': name = 'jqzw'
        return message.syntax == syntax(quoted('function_ref', name))
    def occurs(activity, context):
        return any(flag and (activity, context) == (scalar[which + 'activity'], 'now') for which, flag in (('office', office_occurs), ('public', own_occurs)))
    def presents(person, activity, context):
        return any(match((person, activity, context), ('speaker', scalar[which + 'activity'], 'now'), which + '_presenter',
                         ('person', 'activity', 'context')) for which in ('office', 'public'))
    def conveys(activity, reader, subject, message, context):
        return any(selected(which, reader) and not (variant == 'missing_delivery' and which == 'public' and reader == 'reader0') and
                   match((activity, subject, context), (scalar[which + 'activity'], scalar[which + 'subject'], 'now'), which + '_delivery',
                         ('activity', 'subject', 'context')) and message_ok(message, which, which + '_delivery') for which in ('office', 'public'))
    def voices(person, activity, principal, role, subject, message, context):
        return any(flag and match((person, activity, principal, role, subject, context),
                   ('speaker', scalar[which + 'activity'], scalar['officeprincipal'] if which == 'office' else 'speaker', scalar[which + 'role'], scalar[which + 'subject'], 'now'),
                   which + '_voice', ('person', 'activity', 'principal', 'role', 'subject', 'context')) and message_ok(message, which, which + '_voice')
                   for which, flag in (('office', office_voice), ('public', own_voice)))
    def positioned(person, activity, role, context):
        return any(match((person, activity, role, context), ('speaker', scalar[which + 'activity'], scalar[which + 'role'], 'now'),
                         which + '_position', ('person', 'activity', 'role', 'context')) for which in ('office', 'public'))
    def delegation(person, role, context):
        return entrusted and match((person, role, context), ('speaker', 'officerole', 'now'), 'delegation', ('person', 'role', 'context'))
    def serves(person, principal, role, context):
        return match((person, principal, role, context), ('speaker', scalar['officeprincipal'], 'officerole', 'now'), 'service', ('person', 'principal', 'role', 'context'))
    def directed(activity, recipient, context):
        return any(match((activity, recipient, context), (scalar[which + 'activity'], scalar[which + 'recipient'], 'now'),
                         which + '_direction', ('activity', 'recipient', 'context')) for which in ('office', 'public'))
    def audience(recipient, reader, context):
        return (match((recipient, context), ('officerecipient', 'now'), 'office_audience', ('recipient', 'context')) and reader in members) or (
            match((recipient, context), ('publicrecipient', 'now'), 'public_audience', ('recipient', 'context')) and any(
                chosen and reader == name for name, chosen in zip(readers, intended)))
    def channel(activity, channel, subject, message, context):
        return match((activity, channel, subject, context), (scalar['publicactivity'], 'publicchannel', 'publicsubject', 'now'),
                     'channel', ('activity', 'channel', 'subject', 'context')) and message_ok(message, 'public', 'channel')
    relation_values = dict(occurs=occurs, presents=presents, conveys=conveys, voices=voices, positioned=positioned, entrusted=delegation, serves=serves,
                           officeaudience=lambda reader: selected('office', reader), publicaudience=lambda reader: selected('public', reader))
    callbacks(doc, model, {SYMBOLS[n]: fn for n, fn in relation_values.items()})
    model.update(dg=occurs, f3=presents, f2=conveys, cb=positioned, cf=delegation,
        ca=lambda person, activity, context: any(match((person, activity, context), ('speaker', scalar[which + 'activity'], 'now'),
            which + '_reason', ('person', 'activity', 'context')) for which in ('office', 'public')),
        cc=directed, cd=lambda role, context: scholar and (role, context) == ('publicrole', 'now'),
        ce=lambda recipient, context: public and (recipient, context) == ('publicrecipient', 'now'),
        aa=lambda reader: reader in readers or reader in members or reader == 'speaker',
        h6n=lambda reader, context: context == 'now' and reader in readers,
        h6t=audience, h6u=channel)
    used = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {n: fn for n, fn in model.items() if n in used}, domain


def evaluate(doc, **options):
    model, domain = model_for(doc, **options)
    return values(doc, model, domain, SCENES)


def finite_checks(texts):
    docs = [candidate(text, fixture()) for text in texts]
    def run(**options):
        rows = [evaluate(doc, **options) for doc in docs]
        if rows[0] != rows[1]: raise ValueError('Extracted speech principals differ')
        return rows[0]
    states = []
    for bits in product((False, True), repeat=7):
        private = all(bits[:3]); own = all(bits[3:5]); public = all(bits[5:])
        expected = [own, private, own and private, private, own and public, private and own and public, bits[2], public, public, True]
        row = run(bits=bits)
        if row != expected: raise ValueError('Attribution or public classification collapsed: ' + repr((bits, row, expected)))
        states.append(dict(bits=list(bits), results=row))
    reach = []
    for actual, intended in product(product((False, True), repeat=3), repeat=2):
        has_actual = any(actual); subset = has_actual and all(not a or i for a, i in zip(actual, intended))
        all_public = all(intended); realized_public = has_actual and all_public
        expected = [has_actual, True, has_actual, True, realized_public, realized_public, True, True, all_public, subset]
        row = run(actual=actual, intended=intended)
        if row != expected: raise ValueError('Actual and intended readers collapsed: ' + repr((actual, intended, row)))
        reach.append(dict(actual=list(actual), intended=list(intended), results=row))
    sizes = []
    for size, public in product((0, 1, 2, 8, 64), (False, True)):
        row = run(office_size=size, bits=(True,) * 6 + (public,))
        present = size > 0
        expected = [True, present, present, present, public, present and public, True, public, public, True]
        if row != expected: raise ValueError('Audience size changed role classification')
        sizes.append(dict(office_size=size, public_classification=public, results=row))
    baseline = [True] * 10
    specs = {}
    def failed(names, indices):
        for name in names:
            row = baseline.copy()
            for index in indices: row[index] = False
            specs[name] = row
    for which in ('office', 'public'):
        actual_indices = (1, 2, 3, 5) if which == 'office' else (0, 2, 4, 5)
        failed([which + '_voice_' + n for n in ('person', 'activity', 'principal', 'role', 'subject', 'context', 'alias', 'force')], actual_indices)
        failed([which + '_presenter_' + n for n in ('person', 'activity', 'context')], actual_indices)
        failed([which + '_delivery_' + n for n in ('activity', 'subject', 'context', 'alias', 'force')], actual_indices)
    failed(['delegation_' + n for n in ('person', 'role', 'context')], (1, 2, 3, 5, 6))
    failed(['service_' + n for n in ('person', 'principal', 'role', 'context')], (1, 2, 3, 5))
    failed(['office_position_' + n for n in ('person', 'activity', 'role', 'context')], (1, 2, 3, 5, 6))
    failed(['public_position_' + n for n in ('person', 'activity', 'role', 'context')], (4, 5, 7, 8))
    failed(['office_reason_' + n for n in ('person', 'activity', 'context')], (3, 5, 6))
    failed(['public_reason_' + n for n in ('person', 'activity', 'context')], (4, 5, 7, 8))
    failed(['office_direction_' + n for n in ('activity', 'recipient', 'context')], (3, 5))
    failed(['public_direction_' + n for n in ('activity', 'recipient', 'context')], (4, 5, 7, 8))
    failed(['office_audience_' + n for n in ('recipient', 'context')], (3, 5))
    failed(['public_audience_' + n for n in ('recipient', 'context')], (4, 5, 8, 9))
    failed(['channel_' + n for n in ('activity', 'channel', 'subject', 'context', 'alias', 'force')], (4, 5, 8))
    failed(['principal_is_self'], (1, 2, 3, 5))
    failed(['same_activity'], (2, 5))
    failed(['outsider'], (4, 5, 9))
    failed(['missing_delivery'], (0, 2, 4, 5))
    contrasts = {}
    for variant, expected in specs.items():
        row = run(variant=variant)
        if row != expected: raise ValueError('Bound attribution or reader range differs: ' + repr((variant, row, expected)))
        contrasts[variant] = row
    for doc in docs:
        # All normative, belief, inner-message-truth and actual-receipt inputs
        # are guarded. None is needed to ask these presentation questions.
        for name in (SYMBOLS['voices'], SYMBOLS['serves'], 'dg', 'f3', 'f2', 'cb', 'cf', 'ca', 'cc', 'cd', 'ce', 'h6n', 'h6t', 'h6u'):
            model, domain = model_for(doc); model[name] = guarded(doc)[name]
            try: values(doc, model, domain, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Missing speech interpretation silently supplied: ' + name)
    return dict(state_cases=states, reach_cases=reach, size_cases=sizes, binding_contrasts=contrasts,
                standalone_agrees=True, unknown_relations_refused=True, norms_belief_and_message_truth_not_executed=True,
                public_is_not_audience_size=True, self_attribution_is_positive_evidence=True)


def alignment():
    source = json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'kant-1784:u0012')
    excerpts = [
        ('Der Gebrauch also, den ein angestellter Lehrer von seiner Vernunft vor seiner Gemeinde macht, ist bloß ein Privatgebrauch', ['rhf', 'hzb3']),
        ('einen fremden Auftrag ausrichtet', ['rhf', 'hzb3']),
        ('als Gelehrter, der durch Schriften zum eigentlichen Publikum, nämlich der Welt, spricht', ['rhh', 'hzb4']),
        ('in seiner eigenen Person zu sprechen', ['rhe', 'rhg', 'hzb5']),
    ]
    segments = []
    for excerpt, definitions in excerpts:
        if unit['text'].count(excerpt) != 1: raise ValueError('Ambiguous speech principal source range')
        start = unit['text'].index(excerpt)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(excerpt)], text=excerpt,
            definitions=definitions, status='partial', review_ja='他者の委任・本人への帰属・職務と公衆への使用の分類を、人数と分けて部分接続する。実際の受け手と想定宛先を区別する。媒体、自由、理由付け、全体の意味一致は未完。'))
    return dict(segments=segments, semantic_completion=False)


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored speech principals differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Speech principal roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_speech_principals.py', 'scripts/check_speech_principals.py', 'scripts/compose_institutional_voice.py',
        'scripts/check_closed_policies.py', 'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py',
        'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_speech_principals_and_distinct_reader_scopes', documents=documents, sizes=sizes,
        finite=finite_checks(texts[1:]), alignment=alignment(), new_definitions=7, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Speech principal report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Positive self-attribution, delegated speech and distinct reader scopes checked')


if __name__ == '__main__': main()
