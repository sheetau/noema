"""Check a directed action's content and independent delivery/duty stages."""
import argparse
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.finite_semantics import Content, Message
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_command_delivery import ROOT, PARENT, generic_composed, source_composed, core_composed

REPORT = ROOT / 'reports/command-delivery-v1.json'
DOMAIN = ('person', 'action', 'issuer', 'office', 'notice', 'other')
SCENES = ('now', 'later')
EXTRA = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] a.r zf[] d.r zg[] a.
d zh[person a] h[a] f[k hzz[v person]].
'''


def syntax(q):
    return json.dumps(q['body'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def finite_checks():
    text = generic_composed()[0]
    doc = parse(text + '''r za[] a.r zb[] a.r zc[a a] e.r zd[] f.r ze[] a.
q[e[c[k rew[k za[] p zc]][k zb[]]][k zd[]]].
q[u[e[c[k rew[k za[] p zc]][k zb[]]][j s[k zc[k za[] k zb[]]]]]].
q[u[e[c[k rew[k za[] p zc]][k zb[]]][c[k rew[k ze[] p zc]][k zb[]]]]].
''')
    rows = []
    for first, last in product((False, True), repeat=2):
        content = Content(SCENES, (first, last))
        model = {'za': lambda: 'person', 'zb': lambda: 'action', 'ze': lambda: 'other',
            'zc': lambda person, action: content if (person, action) == ('person', 'action') else Content(SCENES, (not first, not last)),
            'zd': lambda: Message('direct', content)}
        actual = values(doc, model, DOMAIN, SCENES)
        if actual != [True, True, True]:
            raise ValueError('Directive force or actor/action content differs')
        rows.append({'content': [first, last], 'results': actual})
    return rows


def source_setup(text):
    base = candidate(text, EXTRA)
    message = apply_description(base, quoted('function_ref', 'hzz'), [quoted('call', 'za')])
    alias = apply_description(base, quoted('function_ref', 'zh'), [quoted('call', 'za')])
    other = apply_description(base, quoted('function_ref', 'hzz'), [quoted('call', 'zg')])
    item = lambda n: quoted('call', n)['body']
    direct = [item(n) for n in ('zc', 'za', 'ze', 'zb')] + [message, item('zf')]
    duty = [item(n) for n in ('za', 'zb', 'zd', 'zc', 'ze')] + [message, item('zf')]
    statements = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': name, 'arguments': args}} for name, args in (
        ('hzaa', direct), ('hzab', direct), ('hzn', [item(n) for n in ('za', 'zb', 'zd', 'zc', 'zf')]),
        ('hzac', duty), ('hzad', duty))]
    doc = parse(format_graph({**base, 'statements': statements}, 'compact') + 'q[t[k zzq[k za[] k zb[]]][k zf[]]].')
    return doc, message, alias, other


def source_checks():
    documents = [source_setup(builder()[0]) for builder in (source_composed, core_composed)]
    def model_for(doc, message, alias, other, bits=(True, True, True, True, True, False), variant='baseline'):
        occurs, sender, conveys, receives, required, done = bits
        expected_desc = syntax(alias if variant == 'message_alias' else other if variant == 'message_other_actor' else message)
        def message_fields(notice, recipient, action, desc, scene, *, receipt=False):
            expected = ['notice', 'person', 'action', expected_desc, 'now']
            names = ('receipt_notice', 'receipt_person', 'receipt_action', 'receipt_description', 'receipt_context') if receipt else (
                'notice', 'recipient', 'action', 'description', 'context')
            for i, field in enumerate(names):
                if variant == field:
                    expected[i] = syntax(alias) if i == 3 else 'later' if i == 4 else 'other'
            return [notice, recipient, action, desc.syntax, scene] == expected
        def norm(source, person, role, action, desc, sign, scene):
            expected = ['issuer', 'person', 'office', 'action', 'zzq', 'now']
            for i, field in enumerate(('norm_source', 'norm_person', 'norm_role', 'norm_action', 'norm_description', 'norm_context')):
                if variant == field:
                    expected[i] = 'later' if i == 5 else 'other'
            return required and sign and [source, person, role, action, symbol(desc), scene] == expected
        model = guarded(doc)
        model.update({key: (lambda val=val: val) for key, val in zip(('za', 'zb', 'zc', 'zd', 'ze', 'zf', 'zg'),
            ('person', 'action', 'issuer', 'office', 'notice', 'now', 'other'))})
        model.update(
            dg=lambda act, scene: occurs and (act, scene) == ('notice', 'now'),
            f3=lambda actor, act, scene: sender and (actor, act, scene) == (
                'other' if variant == 'sender' else 'issuer', 'notice', 'now'),
            f2=lambda *args: conveys and message_fields(*args),
            h6e=lambda *args: receives and message_fields(*args, receipt=True),
            h7a=norm,
            cf=lambda person, role, scene: variant != 'no_office' and (person, role, scene) == ('person', 'office', 'now'),
            cb=lambda person, act, role, scene: (person, act, role, scene) == ('person', 'action', 'office', 'now'),
            cg=lambda person, act, scene: done and (person, act, scene) == ('person', 'action', 'now'))
        return model
    def run(bits=(True, True, True, True, True, False), variant='baseline'):
        rows = [values(doc, model_for(doc, msg, alias, other, bits, variant), DOMAIN, SCENES)
                for doc, msg, alias, other in documents]
        if rows[0] != rows[1]:
            raise ValueError('Independent command library differs from cumulative source')
        return rows[0]
    rows = []
    for bits in product((False, True), repeat=6):
        occurs, sender, conveys, receives, required, done = bits
        sent = occurs and sender and conveys
        expected = [sent, sent and receives, required, sent and required, sent and required and not done, done]
        actual = run(bits)
        if actual != expected:
            raise ValueError('Delivery/receipt/duty/performance collapsed: ' + str((bits, actual)))
        rows.append({'states': list(bits), 'results': actual})
    contrasts = {}
    for variant in ('sender', 'notice', 'recipient', 'action', 'description', 'context', 'message_alias', 'message_other_actor',
                    'receipt_notice', 'receipt_person', 'receipt_action', 'receipt_description', 'receipt_context',
                    'norm_source', 'norm_person', 'norm_role', 'norm_action', 'norm_description', 'norm_context', 'no_office'):
        actual = run(variant=variant)
        expected = ([True, False, True, True, True, False] if variant.startswith('receipt_') else
            [True, True, False, False, False, False] if variant.startswith('norm_') or variant == 'no_office' else
            [False, False, True, False, False, False])
        if actual != expected:
            raise ValueError('Command referent differs: ' + str((variant, actual)))
        contrasts[variant] = actual
    for doc, msg, alias, other in documents:
        # Issuance and a separate duty can be known before receipt, understanding
        # or fulfillment is assessed. Keep the exact query scope explicit.
        selected = {**doc, 'statements': [doc['statements'][i] for i in (0, 2, 3)]}
        model = model_for(selected, msg, alias, other)
        for name in ('h6e', 'cg'):
            model[name] = guarded(selected)[name]
        if values(selected, model, DOMAIN, SCENES) != [True, True, True]:
            raise ValueError('Issuing a directive inferred receipt or performance')
        for unknown, positions in (('h6e', [1]), ('h7a', [2]), ('cg', [4]), ('f2', [0])):
            selected = {**doc, 'statements': [doc['statements'][i] for i in positions]}
            model = model_for(selected, msg, alias, other)
            model[unknown] = guarded(selected)[unknown]
            try:
                values(selected, model, DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):
                    raise
            else:
                raise ValueError('Unknown directive stage was silently completed')
    return {'cases': rows, 'contrasts': contrasts, 'same_results_in_standalone_core': True,
        'message_description': documents[0][1], 'issuance_and_duty_do_not_require_receipt_or_performance': True,
        'unknown_stages_refused': True}


def alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
        if u['id'] == 'kant-1784:u0012')
    excerpt = 'dem von seinen Oberen etwas anbefohlen wird'
    if unit['text'].count(excerpt) != 1:
        raise ValueError('Ambiguous source range')
    start = unit['text'].index(excerpt)
    return {'segments': [{'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'range': [start, start + len(excerpt)],
        'text': excerpt, 'status': 'partial', 'definitions': ['rew', 'hzz', 'hzaa', 'hzab', 'hzac', 'hzad'],
        'review_ja': '同じ本人に同じ対象行為の実行を求める発話を構成し、その発出・受領・職務要求・実行を分けた。受領を原文の必要条件に追加しない。上官という役割関係、命令権、軍人の概念は未記述。'}],
        'new_source_ranges': True, 'semantic_completion': False}


def build_report():
    documents, sizes = {}, {}
    source_doc = None
    for builder, stem in ((generic_composed, 'directed-action'), (source_composed, 'kant-command-delivery'),
                          (core_composed, 'command-delivery-core')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored command delivery differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Command delivery roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = {'characters': len(text), 'statements': len(doc['statements'])}
        if stem == 'kant-command-delivery':
            source_doc = doc
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if source_doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or source_doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for stem in
        ('directed-action', 'kant-command-delivery', 'command-delivery-core')],
        'scripts/compose_command_delivery.py', 'scripts/check_command_delivery.py',
        'noema/extraction.py', 'noema/description_templates.py', 'noema/finite_semantics.py', 'noema/discourse.py',
        'artifacts/written-units-v1/kant-1784.json']
    return json.loads(json.dumps({'status': 'partial_directed_action_delivery_not_authority_or_liability',
        'documents': documents, 'sizes': sizes, 'finite': finite_checks(), 'source': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_primitives': 0, 'new_source_assertions': 0,
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Command delivery report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Directive content and independent delivery, receipt, duty and fulfillment checked')


if __name__ == '__main__':
    main()
