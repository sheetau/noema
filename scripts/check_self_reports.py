"""Verify self-report delivery independently of judgment, duty and policy truth."""
import argparse
import hashlib
from itertools import product
import json

from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_scoped_nonprescription as prior
from scripts.compose_limits import call as k
from scripts.compose_self_reports import ROOT, PARENT, BUILDERS, BELIEF, SOURCE_BELIEF, REPORT as REPORT_FIELDS, SOURCE_REPORT, SETTINGS, SOURCE_SETTINGS, MEANINGS

REPORT = ROOT / 'reports/self-reports-v1.json'
DOMAIN = (*prior.DOMAIN, 'speech', 'listener')
EXTRA = '''r juactivity[] a.r juaudience[a] c.r juoccurs[a d] c.r jupresents[a a d] c.r juconveys[a a a i[h[a] f] d] c.'''


def setup(text, source=False):
    old = prior.setup(text, source); base = old['document']; base['statements'] = []
    base = parse(format_graph(base, 'compact') + EXTRA)
    beliefs = {**old['refs'], 'criterion': 'r[' + old['duty'] + ']',
        'judgments': 'p fa' if source else 'p jtjudgments', 'matters': 'p fb' if source else 'p jtmatters'}
    fields = SOURCE_BELIEF if source else BELIEF
    specialized = specialize_definition(base, 'hzfs' if source else 'rnb', 'juclaim', {0: description(base, old['duty'])})
    base = specialized.document
    message = k('juclaim', *(beliefs[n] for n, _ in fields if n != 'criterion'))
    belief = k('hzfr' if source else 'rna', *(beliefs[n] for n, _ in fields))
    refs = {**beliefs, 'activity': 'k juactivity[]', 'audience': 'p juaudience', 'message': 'r[' + message + ']',
        'occurs': 'p juoccurs', 'presents': 'p jupresents', 'conveys': 'p juconveys'}
    report = k('hzft' if source else 'rnc', *(refs[n] for n, _ in (SOURCE_REPORT if source else REPORT_FIELDS)))
    action = k('hzfu' if source else 'rnd', *(refs[n] for n, _ in (SOURCE_SETTINGS if source else SETTINGS)))
    person, activity, context = (refs[n] for n in ('person', 'activity', 'context'))
    current = lambda expr: 't[' + expr + '][' + context + ']'
    apply = lambda function: 'c[' + function + '][l[a][' + person + ']]'
    content = 'c[' + belief + '][' + person + ']'
    queries = [report, current(content), current(apply(old['duty'])), current(apply(old['policy'])),
        current('c[' + action + '][' + person + ' ' + activity + ']'),
        'e[c[' + message + '][' + person + ']][j q[' + content + ']]']
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=source, old=old, message=message, action=action,
        message_syntax=syntax(description(base, message)), disquotations_removed=specialized.disquotations_removed)


def model_for(data, bits=(True, True, True, True, False, True), variant='baseline'):
    occurs, presents, conveys, belief, duty, policy = bits
    model = prior.model_for(data['old'], (False, False, policy, policy, duty, belief),
        'empty_candidates' if variant == 'empty_candidates' else 'baseline')
    model.update({n: f for n, f in guarded(data['document']).items() if n not in model})
    actual_occurs = lambda act, point: occurs and (act, point) == ('speech', 'now')
    actual_presents = lambda person, act, point: presents and (person, act, point) == (
        'coholder' if variant == 'wrong_speaker' else 'leader', 'otheract' if variant == 'wrong_act' else 'speech', 'now')
    actual_conveys = lambda act, listener, subject, desc, point: conveys and (act, listener, subject, point) == (
        'speech', 'listener', 'listener' if variant == 'wrong_subject' else 'leader',
        'belief' if variant == 'other_context' else 'now') and desc.syntax == data['message_syntax'] and variant != 'wrong_message'
    model.update(juactivity=lambda: 'speech', juaudience=lambda person: person == 'listener' and variant != 'empty_audience',
        juoccurs=actual_occurs, jupresents=actual_presents, juconveys=actual_conveys)
    if data['source']: model.update(dg=actual_occurs, f3=actual_presents, f2=actual_conveys)
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model, individuals=DOMAIN,
        situations=prior.SCENES, max_steps=16_000_000)]


def checks(texts):
    generic = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=6):
        occurs, presents, conveys, belief, duty, policy = bits; delivered = occurs and presents and conveys
        expected = [delivered, belief, duty, policy, delivered, False]
        actual = values(generic, model_for(generic, bits))
        if actual != expected: raise ValueError('Self-report and truth conflated: ' + repr((bits, actual)))
        grid.append(dict(bits=list(bits), result=actual))
    print('64 self-report/judgment/duty/policy profiles passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = setup(text, True); cases = {}
        for variant in ('baseline', 'wrong_speaker', 'wrong_act', 'wrong_subject', 'other_context', 'wrong_message', 'empty_audience', 'empty_candidates'):
            actual = values(data, model_for(data, variant=variant))
            expected = [True, True, False, True, True, False] if variant == 'baseline' else (
                [True, False, False, True, True, False] if variant == 'empty_candidates' else
                [False, True, False, True, False, False])
            if actual != expected: raise ValueError('Self-report source contrast failed: ' + repr((variant, actual)))
            cases[variant] = actual
        rows.append(dict(cases=cases, disquotations_removed=data['disquotations_removed']))
        print('Self-report source contrasts passed', flush=True)
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Self-report artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Self-report roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = 'zu sagen: daß er es für Pflicht halte, in Religionsdingen den Menschen nichts vorzuschreiben, sondern ihnen darin volle Freiheit zu lassen'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_self_reports.py', 'scripts/check_self_reports.py', 'scripts/check_scoped_nonprescription.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_described_appraisals.py',
        'scripts/check_rod_setup.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'noema/specialization.py', 'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_self_report_of_a_duty_judgment', documents=documents, sizes=sizes,
        interpretation=checks(texts), parent_preserved=True, roundtrips=True, new_definitions=8, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Self-report record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Self-report delivery, judgment, duty and policy remain independent')


if __name__ == '__main__': main()
