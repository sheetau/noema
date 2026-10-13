"""Execute received-message routes and reject disconnected relay histories."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.compose_message_relays import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/message-relays-v1.json'
DOMAIN = ('a', 'b', 'c', 's0', 's1', 's2', 'topic', 'group')
SCENES = ('t0', 't1', 't2', 'now')
EXTRA = '''r za[d] c.r zb[d d] c.r zc[a] c.r zd[] a.r ze[] j[a].r zf[] a.r zg[] a.r zh[] a.r zi[] d.
r zj[a] a.r zk[a] a.r zl[a] a.r zm[a] d.r zn[a d] c.r zo[a a d] c.
r zp[a a a i[h[a] f] d] c.r zq[a a a i[h[a] f] d] c.r zr[a a a a i[h[a] f] d] c.
r zs[a a i[h[a] f] d] c.r zt[a d] c.
d zu[person a] f[j s[b scene[k zt[v person v scene]]]].
d z4[person a] f[j q[b scene[k zt[v person v scene]]]].
r zv[] a.r zw[a] j[a].r zx[a] a.r zy[a] j[a].r zz[a] d.r z2[] d.r z3[a] c.
'''
ARGS = 'p za p zb p zc k zd[] k ze[] k zf[] k zg[] k zh[] r[p zu] k zi[] p zj p zk p zl p zm p zn p zo p zp p zq p zr'
SOURCE_ARGS = 'k zd[] k ze[] k zf[] k zg[] k zh[] r[p zu] k zi[] k z2[] p zj p zk p zl p zm'


def sequence(items):
    return SequenceValue(tuple(items), '"individual"')


def model_for(doc, variant='baseline', length=2, flags=(True,) * 5):
    occurs, presents, conveys, receives, understands = flags
    senders = {'s0': 'a', 's1': 'b', 's2': 'c'}
    recipients = {'s0': 'b', 's1': 'c', 's2': 'a'}
    times = {'s0': 't0', 's1': 't1', 's2': 't2'}
    steps = ['s0', 's1', 's2'][:length]
    target = recipients[steps[-1]]
    end = times[steps[-1]]
    if variant == 'reversed_steps':
        steps = list(reversed(steps))
    if variant == 'repeated_step':
        steps = ['s0', 's0']
    if variant == 'disconnected_people':
        senders['s1'] = 'a'
    if variant == 'self_transmission':
        recipients['s0'] = 'a'
    if variant == 'same_time':
        times['s1'] = 't0'
    members = ('b', 'c')
    if variant == 'external_intermediary':
        members = ('c',)
    elif variant == 'empty_audience':
        members = ()
    elif variant == 'duplicate_audience':
        members = ('b', 'c', 'c')
    elif variant == 'nonhuman_audience':
        members = ('b', 'topic')
    def history(point):
        return not (variant == 'missing_history' and point == 't0')
    def before(first, last):
        return SCENES.index(first) < SCENES.index(last) or variant == 'cyclic_history' and (first, last) == ('t1', 't0')
    def message(act, recipient, subject, description, point):
        return conveys and act in steps and (recipient, subject, symbol(description), point) == (
            recipients[act], 'group' if variant == 'changed_subject' and act == 's1' else 'topic',
            'z4' if variant == 'changed_force' and act == 's1' else 'zu', times[act])
    def received(act, recipient, subject, description, point):
        return receives and not (variant == 'missing_first_receipt' and act == 's0' or
            variant == 'missing_second_receipt' and act == 's1') and message(act, recipient, subject, description, point)
    def relay(act, previous, person, subject, description, point):
        previous_act = {'s1': 's0', 's2': 's1'}.get(act)
        return variant != 'independent_same_message' and previous_act is not None and (
            previous, person, subject, symbol(description), point) == (
            's2' if variant == 'wrong_predecessor' else previous_act,
            'a' if variant == 'wrong_relay_person' else senders[act],
            'group' if variant == 'wrong_relay_subject' else 'topic',
            'z4' if variant == 'wrong_relay_description' else 'zu',
            'now' if variant == 'wrong_relay_time' else times[act])
    def understood(recipient, subject, description, point):
        return understands and variant != 'not_understood' and (recipient, subject, symbol(description), point) == (target, 'topic', 'zu', end)
    def forbidden(*args):
        raise ValueError('Relay evaluated the content or endorsement')
    model = guarded(doc)
    model.update(za=history, zb=before, zc=lambda person: person in ('a', 'b', 'c') and not (
        variant == 'nonhuman_intermediary' and person == 'b'),
        zd=lambda: steps[0], ze=lambda: sequence(steps[1:]), zf=lambda: 'b' if variant == 'wrong_origin' else 'a',
        zg=lambda: 'b' if variant == 'wrong_target' else target, zh=lambda: 'topic',
        zi=lambda: 'now' if variant == 'wrong_endpoint_time' else end,
        zj=lambda step: senders.get(step, 'a'), zk=lambda step: recipients.get(step, 'a'),
        zl=lambda step: step, zm=lambda step: times.get(step, 'now'),
        zn=lambda act, point: occurs and act in steps and point == times[act],
        zo=lambda person, act, point: presents and act in steps and (person, point) == (senders[act], times[act]),
        zp=message, zq=received, zr=relay, zs=understood, zt=forbidden,
        zv=lambda: 'group', zw=lambda group: sequence(members if group == 'group' else ()),
        zx=lambda person: 's0', zy=lambda person: sequence(()) if person == 'b' else sequence(('s1',)),
        zz=lambda person: 't0' if person == 'b' else 't1',
        z2=lambda: 't0' if variant == 'future_receipt' else 'now', z3=lambda person: person in members)
    native = {'aa': model['zc'], 'dg': model['zn'], 'f3': model['zo'], 'f2': model['zp'],
        'h6e': model['zq'], 'h6f': model['zr'], 'h6g': model['zs'], 'mp': model['zw'],
        'ia': lambda person, anchor, point: person == 'a' and history(point),
        'ic': lambda first, last, anchor: before(first, last)}
    model.update({name: val for name, val in native.items() if name in model})
    model.update({name: val for name, val in arithmetic().items() if name in model})
    return model


def generic_checks():
    text = generic_composed()[0]
    direct = candidate(text, EXTRA + '''
q[k rdb[k zf[] k zg[] k zd[] k zh[] r[p zu] k zi[] p zn p zo p zp]].
q[k rdc[k zf[] k zg[] k zd[] k zh[] r[p zu] k zi[] p zn p zo p zp p zq]].
q[k rdf[''' + ARGS + ''' p zs]].''')
    for flags in product((False, True), repeat=5):
        actual = values(direct, model_for(direct, length=1, flags=flags), DOMAIN, SCENES)
        if actual != [all(flags[:3]), all(flags[:4]), all(flags)]:
            raise ValueError('Presentation, receipt and understanding collapsed')
    route = candidate(text, EXTRA + 'q[k rdd[' + ARGS + ']].q[k rdf[' + ARGS + ' p zs]].')
    rows = {}
    variants = ('baseline', 'not_understood', 'independent_same_message', 'disconnected_people', 'self_transmission',
        'missing_first_receipt', 'missing_second_receipt', 'changed_subject', 'changed_force',
        'wrong_predecessor', 'wrong_relay_person', 'wrong_relay_subject', 'wrong_relay_description', 'wrong_relay_time',
        'reversed_steps', 'repeated_step', 'same_time', 'cyclic_history', 'missing_history',
        'nonhuman_intermediary', 'wrong_origin', 'wrong_target', 'wrong_endpoint_time')
    for variant in variants:
        actual = values(route, model_for(route, variant), DOMAIN, SCENES)
        expected = [True, True] if variant == 'baseline' else [True, False] if variant == 'not_understood' else [False, False]
        if actual != expected:
            raise ValueError('Relay contrast differs: ' + str((variant, actual)))
        rows[variant] = actual
    lengths = {}
    for length in (1, 2, 3):
        actual = values(route, model_for(route, length=length), DOMAIN, SCENES)
        if actual != [True, True]:
            raise ValueError('Valid finite relay or return to origin failed')
        lengths[str(length)] = actual
    collective = candidate(text, EXTRA + 'q[k rde[p z3 p zx p zy p zz p za p zb p zc k zf[] k zh[] r[p zu] p zj p zk p zl p zm p zn p zo p zp p zq p zr]].')
    audiences = {}
    for variant in ('baseline', 'external_intermediary', 'empty_audience', 'missing_second_receipt'):
        actual = values(collective, model_for(collective, variant), DOMAIN, SCENES)
        if actual != [variant in ('baseline', 'external_intermediary')]:
            raise ValueError('Audience routes differ: ' + str((variant, actual)))
        audiences[variant] = actual
    return {'direct_state_cases': 32, 'route_cases': rows, 'route_lengths': lengths, 'audience_cases': audiences,
        'message_truth_and_endorsement_not_evaluated': True}


def source_checks():
    doc = candidate(source_composed()[0], EXTRA + 'q[k h6h[' + SOURCE_ARGS + ']].q[k h6i[' + SOURCE_ARGS + ''']].
q[k h6j[k zv[] p zx p zy p zz k zf[] k zh[] r[p zu] k z2[] p zj p zk p zl p zm]].''')
    rows = {}
    for variant in ('baseline', 'not_understood', 'external_intermediary', 'independent_same_message',
            'changed_force', 'missing_first_receipt', 'missing_second_receipt', 'nonhuman_intermediary',
            'future_receipt', 'empty_audience', 'duplicate_audience', 'nonhuman_audience'):
        actual = values(doc, model_for(doc, variant), DOMAIN, SCENES)
        expected = [True, True, True] if variant in ('baseline', 'external_intermediary') else (
            [True, False, True] if variant == 'not_understood' else [True, True, False] if variant in (
                'empty_audience', 'duplicate_audience', 'nonhuman_audience') else [False, False, False])
        if actual != expected:
            raise ValueError('Native relay contrast differs: ' + str((variant, actual)))
        rows[variant] = actual
    receipt_only = candidate(source_composed()[0], EXTRA + 'q[k h6h[' + SOURCE_ARGS + ']].')
    model = model_for(receipt_only)
    def forbidden(*args):
        raise ValueError('Receipt-only route read an understanding or endorsement assessment')
    model['h6g'] = forbidden
    if values(receipt_only, model, DOMAIN, SCENES) != [True]:
        raise ValueError('Receipt-only route changed')
    def unknown_receipt(*args):
        raise ValueError('Unassessed message receipt')
    model['h6e'] = unknown_receipt
    try:
        values(receipt_only, model, DOMAIN, SCENES)
    except ValueError as exc:
        if 'Unassessed message receipt' not in str(exc):
            raise
    else:
        raise ValueError('Unknown receipt became a known result')
    return {'cases': rows, 'understanding_not_required_for_receipt': True, 'unknown_receipt_refused': True,
        'all_unrelated_source_primitives_guarded': True}


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0011')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source unit changed')
    start = text.index('um sich verbreiten')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': start + len('um sich verbreiten'),
        'source': 'um sich verbreiten', 'definitions': ['h6h', 'h6i', 'h6j'], 'status': 'partial_explicit_reading',
        'full_semantic_equivalence': False, 'remaining': ['reasoned self-appraisal and vocation of independent thought',
            'spirit and attitude versus message relay', 'future modality and surrounding audience',
            'public access and group enlightenment', 'primitive meaning and source equivalence']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'message-relays'), (source_composed, 'kant-message-relays')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored message routes differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Relay roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/message-relays-basis-v1.json', 'data/kant-message-relays-basis-v1.json',
        'scripts/compose_message_relays.py', 'scripts/check_message_relays.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_message_propagation_not_attitude_or_public_enlightenment',
        'documents': documents, 'generic': generic_checks(), 'source_cases': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Relay report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Presentation, receipt, linked relay, understanding and group reach checked')


if __name__ == '__main__':
    main()
