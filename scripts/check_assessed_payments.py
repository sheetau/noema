"""Check remittance, unmet requirements and public criticism independently."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_office_speech as office
from scripts.compose_assessed_payments import ROOT, PARENT, BUILDERS, generic_composed

REPORT = ROOT / 'reports/assessed-payments-v1.json'
EXTRA = office.EXTRA + 'r zp[] a.r zq[] a.r zs[a] e.r zt[a] e.'
DOMAIN = (*office.DOMAIN, 'collector', 'medium')


def evaluate(doc, model):
    names = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return values(doc, {name: value for name, value in model.items() if name in names}, DOMAIN, office.SCENES)


def description(base, expression):
    probe = parse(format_graph(base, 'compact') + 'q[e[r['+expression+']][r['+expression+']]].')
    return probe['statements'][-1]['body']['arguments'][0]


def source_setup(text):
    base = candidate(text, EXTRA)
    payment = apply_description(base, quoted('function_ref', 'hzah'), [quoted('call', 'zp'), quoted('call', 'zq')])
    criticism = apply_description(base, quoted('function_ref', 'rfd'),
        [description(base, 'l[h[a] e][p zs]'), description(base, 'l[h[a] e][p zt]')])
    duty = [quoted('call', name)['body'] for name in ('za', 'zb', 'zc', 'zd')]
    duty += [payment, quoted('call', 'zk')['body']]
    public = [quoted('call', name)['body'] for name in ('ze', 'zf', 'zg', 'zh', 'zi')]
    public += [criticism, quoted('call', 'zj')['body']]
    queries = [(name, duty) for name in ('hzai', 'hzaj')]
    queries += [(name, duty+public) for name in ('hzak', 'hzal')]
    base['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': name, 'arguments': args}}
                          for name, args in queries]
    doc = parse(format_graph(base, 'compact') +
        'q[t[c[k hzah[k zp[] k zq[]]][k za[] k zb[]]][k zk[]]].'
        'q[t[k zzq[k za[] k ze[]]][k zk[]]].'
        'q[t[k rfc[k zi[] l[h[a] e][p zs] l[h[a] e][p zt]]][k zk[]]].')
    return doc, payment, criticism


def model_for(doc, payment, criticism, bits=(True, True, False, True, True), variant='baseline'):
    required, allowed, forbidden, paid, spoken = bits
    old_variant = variant if variant in ('private_audience', 'missing_reader', 'speech_is_official') else 'baseline'
    model = office.model_for(doc, (required, allowed, forbidden, False, spoken), old_variant)
    original_norm = model['h7a']
    def require(source, person, role, action, desc, sign, context):
        expected = ['issuer', 'person', 'office', 'duty', 'now']
        for i, field in enumerate(('issuer', 'person', 'role', 'action', 'context')):
            if variant == 'required_'+field:
                expected[i] = 'elsewhere' if i == 4 else 'other'
        match = [source, person, role, action, context] == expected and desc.syntax == syntax(payment)
        if variant == 'required_description':
            match = False
        ordinary_execution = json.loads(desc.syntax) == {'kind': 'function_ref', 'symbol': 'zzq'}
        return bool(required and sign and match or ordinary_execution and
                    original_norm(source, person, role, action, desc, sign, context))
    def moves(transfer, payer, receiver, medium, context):
        expected = ['duty', 'person', 'collector', 'medium', 'now']
        for i, field in enumerate(('transfer', 'payer', 'receiver', 'medium', 'context')):
            if variant == 'moved_'+field:
                expected[i] = 'elsewhere' if i == 4 else 'other'
        return paid and [transfer, payer, receiver, medium, context] == expected
    def publication(activity, channel, subject, desc, context):
        return variant != 'criticism_description' and (activity, channel, subject, desc.syntax, context) == (
            'speech', 'channel', 'topic', syntax(criticism), 'now')
    model.update(zp=lambda: 'collector', zq=lambda: 'medium', h7a=require, ti=moves,
        tj=lambda medium, context: variant != 'unaccepted_medium' and (medium, context) == ('medium', 'now'),
        h6u=publication, zs=lambda subject: Content(office.SCENES, (True, True)),
        zt=lambda subject: Content(office.SCENES, (True, True)))
    # No entrusted office, service consideration or actual criticism truth is
    # required merely to interpret the remittance obligation and speech scope.
    model['cf'] = guarded(doc).get('cf', lambda *args: False)
    if variant == 'wrong_authority':
        model['zj'] = lambda: 'other'
    return model


def source_checks(texts):
    setups = [source_setup(text) for text in texts]
    rows = []
    for bits in product((False, True), repeat=5):
        required, allowed, forbidden, paid, spoken = bits
        expected = [required, required and not paid, required and spoken, required and allowed and not forbidden,
                    paid, spoken, False]
        actual = [evaluate(doc, model_for(doc, payment, criticism, bits)) for doc, payment, criticism in setups]
        if actual != [expected]*len(setups):
            raise ValueError('Remittance, obligation, speech or truth collapsed: '+repr((bits, actual)))
        rows.append({'states': list(bits), 'results': actual[0]})
    variants = {
        **{name: [False, False, False, False, True, True, False] for name in
           ('required_issuer', 'required_person', 'required_role', 'required_action', 'required_context', 'required_description')},
        **{name: [True, True, True, True, False, True, False] for name in
           ('moved_transfer', 'moved_payer', 'moved_receiver', 'moved_medium', 'moved_context', 'unaccepted_medium')},
        **{name: [True, False, False, False, True, True, False] for name in
           ('private_audience', 'missing_reader', 'speech_is_official', 'criticism_description')},
        'wrong_authority': [True, False, True, False, True, True, False],
    }
    contrasts = {}
    for variant, expected in variants.items():
        actual = [evaluate(doc, model_for(doc, payment, criticism, variant=variant)) for doc, payment, criticism in setups]
        if actual != [expected]*len(setups):
            raise ValueError('Remittance binding differs: '+variant+repr(actual))
        contrasts[variant] = actual[0]
    doc, payment, criticism = setups[0]
    selected = {**doc, 'statements': [doc['statements'][i] for i in (0, 3)]}
    model = model_for(selected, payment, criticism)
    for name in ('ti', 'tj', 'cg', 'zs', 'zt'):
        model[name] = guarded(selected)[name]
    if evaluate(selected, model) != [True, True]:
        raise ValueError('Normative conditions required execution or opinion truth')
    for name, index in (('ti', 1), ('zs', 6)):
        selected = {**doc, 'statements': [doc['statements'][index]]}
        model = model_for(selected, payment, criticism); model[name] = guarded(selected)[name]
        try:
            evaluate(selected, model)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):
                raise
        else:
            raise ValueError('Unknown performance/criterion was silently filled in')
    return {'cases': rows, 'contrasts': contrasts, 'standalone_agrees': True,
        'norms_do_not_require_payment_speech_or_criticism_truth': True,
        'unknown_performance_and_criterion_refused': True, 'entrusted_office_not_required': True,
        'payment_description': payment, 'criticism_description': criticism}


def transfer_checks(text):
    extra = 'r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.'
    query = ('q[k rfa[k za[] k zb[] k zc[] k zd[] k ze[] p ti p tj]].'
             'q[k rf[k za[] k zb[] k zc[] k zd[] r[p bm] k ze[] p ti p tj p tk]].')
    doc = candidate(text, extra+query)
    rows = []
    for moved, accepted, consideration in product((False, True), repeat=3):
        model = guarded(doc)
        model.update(za=lambda: 'person', zb=lambda: 'collector', zc=lambda: 'duty', zd=lambda: 'medium', ze=lambda: 'now',
            ti=lambda transfer, payer, receiver, medium, context: moved and (transfer, payer, receiver, medium, context) == ('duty', 'person', 'collector', 'medium', 'now'),
            tj=lambda medium, context: accepted and (medium, context) == ('medium', 'now'),
            tk=lambda transfer, receiver, purpose, context: consideration and (transfer, receiver, context) == ('duty', 'collector', 'now'))
        actual = evaluate(doc, model)
        expected = [moved and accepted, moved and accepted and consideration]
        if actual != expected:
            raise ValueError('Assessed remittance was forced to be service consideration')
        rows.append({'states': [moved, accepted, consideration], 'results': actual})
    model['zb'] = lambda: 'person'
    model['ti'] = lambda *args: True
    if evaluate(doc, model) != [False, False]:
        raise ValueError('Self-transfer accepted as remittance to another party')
    return {'cases': rows, 'self_transfer_rejected': True, 'no_service_consideration_needed': True}


def criticism_checks():
    text = generic_composed()[0]
    rows = []
    for suitable, just in product((False, True), repeat=2):
        for sizes in product((0, 1, 2), repeat=2):
            lists = ['l[h[a] e]['+' '.join(['p '+name]*size)+']' for name, size in zip(('zc', 'zd'), sizes)]
            doc = parse(text+'r za[] a.r zb[] d.r zc[a] e.r zd[a] e.'+
                'q[t[k rfc[k za[] '+' '.join(lists)+']][k zb[]]].'+
                'q[e[c[k rfd['+' '.join(lists)+']][k za[]]][j s[k rfc[k za[] '+' '.join(lists)+']]]].'+
                'q[u[e[c[k rfd['+' '.join(lists)+']][k za[]]][j q[k rfc[k za[] '+' '.join(lists)+']]]]].')
            model = {'za': lambda: 'object', 'zb': lambda: 'now',
                'zc': lambda subject: Content(('now',), (suitable,)), 'zd': lambda subject: Content(('now',), (just,))}
            actual = values(doc, model, ('object', 'other'), ('now',))
            expected = bool(sizes[0] and not suitable or sizes[1] and not just)
            if actual != [expected, True, True]:
                raise ValueError('Suitability/justice scopes differ')
            rows.append({'suitable': suitable, 'just': just, 'list_sizes': list(sizes), 'result': actual[0]})
    return {'cases': rows, 'empty_lists_do_not_invent_a_defect': True, 'duplicates_do_not_change_truth': True,
            'assertion_and_question_distinguished_even_for_false_content': True}


def alignment():
    source = json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'kant-1784:u0012')
    excerpts = (
        ('Der Bürger kann sich nicht weigern, die ihm auferlegten Abgaben zu leisten', ['rfa', 'rfb', 'hzah', 'hzai'],
         '対価を必須としない納付内容と、役割・出所を保持した実行要求への部分接続。市民・賦課の制度、拒否の意思、金額と期限の説明は未完。'),
        ('als Gelehrter, wider die Unschiklichkeit oder auch Ungerechtigkeit solcher Ausschreibungen öffentlich seine Gedanken äußert', ['rfc', 'rfd', 'hzak'],
         '同じ本人の公的発言を、同じ対象に関する適切さ・公正さの別の基準からの批判へ接続する。基準や思考の全説明、「市民の義務に反しない」という判断と直前の制裁・誘発可能性は未完。'))
    rows = []
    for excerpt, definitions, review in excerpts:
        if unit['text'].count(excerpt) != 1:
            raise ValueError('Assessed-payment excerpt is ambiguous')
        start = unit['text'].index(excerpt)
        rows.append({'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'range': [start, start+len(excerpt)],
            'text': excerpt, 'definitions': definitions, 'status': 'partial', 'review_ja': review})
    return {'segments': rows, 'semantic_completion': False, 'normative_noncontravention_not_yet_equated_with_permission': True}


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored assessed-payment document differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Assessed-payment roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = {'characters': len(text), 'statements': len(doc['statements'])}
    doc, parent = parse(texts[1]), parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents, PARENT, *['data/'+stem+'-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_assessed_payments.py', 'scripts/check_assessed_payments.py', 'scripts/check_office_speech.py',
        'scripts/check_public_assessment.py', 'noema/description_templates.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return json.loads(json.dumps({'status': 'partial_required_remittance_and_public_criticism', 'documents': documents, 'sizes': sizes,
        'transfers': transfer_checks(texts[1]), 'criticism': criticism_checks(), 'source': source_checks(texts[1:]),
        'alignment': alignment(), 'roundtrips': True, 'parent_preserved': True,
        'new_primitives': 0, 'new_author_statements': 0, 'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Assessed-payment report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Required remittance, fulfillment and public criticism checked separately')


if __name__ == '__main__':
    main()
