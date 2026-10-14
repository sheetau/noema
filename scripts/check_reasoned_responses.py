"""Separate coincident judgments, reason use, support and motivated response."""
import argparse
import hashlib
from itertools import product
import json
from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts import check_recognized_benefits as prior
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_deserved_responses import RESPONSE, BASIS, STANDARD
from scripts.compose_limits import call as k
from scripts.compose_reasoned_responses import ROOT, PARENT, BUILDERS, PAIR, RELATIONS, CONFIG, SOURCE, DESCRIPTION, MEANINGS

REPORT = ROOT / 'reports/reasoned-responses-v1.json'
DOMAIN = ('judgment', 'appraisal', *[p for p in prior.DOMAIN if p != 'judgment'])
SCENES = prior.SCENES
EXTRA = '''r jsperson[] a.r jssubject[] a.r jsactivity[] a.r jscontext[] d.r jsreasonnode[] a.r jsassessmentnode[] a.
r jsreason[j[a]] e.r jsassessment[j[a]] e.r jsresponse[a a a] e.
r jsjudgments[a a d] c.r jsmatters[a a d] c.r jslinked[a ''' + DESCRIPTION + ''' j[a] d] c.r jscandidates[a d d] c.
r jsuses[a a d] c.r jssupports[a a d] c.r jsmotivates[a a a d] c.
r jsstandard[a ''' + RESPONSE + ' ' + BASIS + ''' d] c.'''


def setup(text, source=False):
    old = prior.setup(text, True) if source else None
    base = old['document'] if source else parse(text); base['statements'] = []; base = parse(format_graph(base, 'compact') + EXTRA)
    reason = old['criterion'] if source else 'p jsreason'
    response = old['response'] if source else 'p jsresponse'
    removed = old['disquotations_removed'] if source else 0
    ground = None
    if source:
        ground = 'i[actor a][c[' + reason + '][l[a][k jrtarget[] v actor k jractivity[]]]]'
        spec = specialize_definition(base, 'ro6', 'jsmerit', {1: description(base, ground)}); base = spec.document; removed += spec.disquotations_removed
        rule = 'i[subject a response ' + RESPONSE + ' basis ' + BASIS + '][b point[k jsstandard[v subject v response v basis v point]]]'
        merit = k('jsmerit', 'r[' + response + ']', 'l[' + STANDARD + '][' + rule + ']')
        assessment = 'i[bindings j[a]][b point[w[k rdr[v bindings n p b b]][g actor a[w[a[v bindings][n p a b][v actor]][t[c[' + merit + '][v actor]][v point]]]]]]'
        firstbindings = 'i[person a subject a][l[a][v person v subject k jractivity[]]]'
    else:
        assessment = 'p jsassessment'; firstbindings = 'i[person a subject a][l[a][v person v subject]]'
    secondbindings = 'i[person a subject a][l[a][v subject]]'
    fields = dict(reasonbindings=firstbindings, assessmentbindings=secondbindings, response=response,
        **{n: 'p js' + n for n in ('judgments', 'matters', 'linked', 'candidates', 'uses', 'supports', 'motivates')})
    calls = []
    for original, target in (('hzgm' if source else 'rov', 'jsmotivated'), ('hzgn' if source else 'row', 'jssupported')):
        spec = specialize_definition(base, original, target, {0: description(base, reason), 2: description(base, assessment)})
        base = spec.document; removed += spec.disquotations_removed
        calls.append(k(target, *(fields[n] for n, _ in (SOURCE if source else CONFIG) if n not in ('reasoncriterion', 'assessmentcriterion'))))
    pairs = dict(fields, person='k jsperson[]', subject='k jssubject[]', reason='k jsreasonnode[]', assessment='k jsassessmentnode[]',
        reasoncriterion='r[' + reason + ']', assessmentcriterion='r[' + assessment + ']', context='k jscontext[]',
        reasonbindings='c[' + firstbindings + '][k jsperson[] k jssubject[]]', assessmentbindings='c[' + secondbindings + '][k jsperson[] k jssubject[]]')
    if source: pairs.update(judgments='p fa', matters='p fb', uses='p fc', supports='p fd')
    at = lambda expression: 't[' + expression + '][k jscontext[]]'
    actual = lambda expression: at('c[' + expression + '][k jsperson[] k jsactivity[] k jssubject[]]')
    queries = [k(name, *(pairs[n] for n, _ in PAIR + RELATIONS)) for name in ('rot', 'rou')]
    queries += [actual(response), *(actual(call) for call in calls), 'e[r[' + calls[0] + ']][r[' + calls[0] + ']]',
        at('c[' + assessment + '][c[' + secondbindings + '][k jsperson[] k jssubject[]]]')]
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=source, old=old, reason=reason, assessment=assessment, response=response, disquotations_removed=removed,
        reason_syntax=syntax(description(base, reason)), assessment_syntax=syntax(description(base, assessment)),
        response_syntax=syntax(description(base, response)), ground_syntax=syntax(description(base, ground)) if ground else None)


def model_for(data, bits=(True,) * 6, variant='baseline', actual=True):
    reason, assessment, uses, supports, response, motive = bits
    model = prior.model_for(data['old'], (actual, True, reason, True, True, response)) if data['source'] else guarded(data['document'])
    model.update({n: f for n, f in guarded(data['document']).items() if n not in model})
    firstslots = ('alice', 'giver', 'benefit') if data['source'] else ('alice', 'giver')
    def judgment(person, node, point):
        if variant == 'other_judge' and node == 'appraisal': return (person, point) == ('other', 'now')
        return (person, point) == ('alice', 'now') and node in ('judgment', 'appraisal')
    def matter(node, subject, point):
        return point == 'now' and node in ('judgment', 'appraisal') and subject == ('other' if variant == 'other_subject' and node == 'appraisal' else 'giver')
    def linked(node, criterion, bindings, point):
        if point != 'now': return False
        if node == 'judgment': return criterion.syntax == data['reason_syntax'] and tuple(bindings.items) == firstslots
        return node == 'appraisal' and criterion.syntax == data['assessment_syntax'] and tuple(bindings.items) == ('giver',) and variant != 'wrong_assessment_description'
    def candidates(node, context, point):
        return context == 'now' and point == 'belief' and node in ('judgment', 'appraisal') and not (variant == 'empty_assessment_candidates' and node == 'appraisal')
    use = lambda conclusion, premise, point: uses and (conclusion, premise, point) == (('judgment', 'appraisal', 'now') if variant == 'reverse_use' else ('appraisal', 'judgment', 'now'))
    support = lambda premise, conclusion, point: supports and (premise, conclusion, point) == (('appraisal', 'judgment', 'now') if variant == 'reverse_support' else ('judgment', 'appraisal', 'now'))
    motivation = lambda person, act, node, point: motive and (person, act, node, point) == ('other' if variant == 'other_motive_person' else 'alice', 'benefit' if variant == 'other_motive_action' else 'reply', 'judgment' if variant == 'other_motive_judgment' else 'appraisal', 'belief' if variant == 'other_motive_time' else 'now')
    model.update(jsperson=lambda: 'alice', jssubject=lambda: 'giver', jsactivity=lambda: 'reply', jscontext=lambda: 'now',
        jsreasonnode=lambda: 'judgment', jsassessmentnode=lambda: 'judgment' if variant == 'same_judgment' else 'appraisal',
        jsreason=lambda bindings: Content(SCENES, tuple(reason and tuple(bindings.items) == ('alice', 'giver') and point == 'belief' for point in SCENES)),
        jsassessment=lambda bindings: Content(SCENES, tuple(assessment and tuple(bindings.items) == ('giver',) and point == 'belief' for point in SCENES)),
        jsresponse=lambda person, act, subject: Content(SCENES, tuple(response and (person, act, subject, point) == ('alice', 'reply', 'giver', 'now') for point in SCENES)),
        jsjudgments=judgment, jsmatters=matter, jslinked=linked, jscandidates=candidates, jsuses=use, jssupports=support, jsmotivates=motivation,
        jsstandard=lambda subject, reply, basis, point: assessment and subject == 'giver' and reply.syntax == data['response_syntax'] and basis.syntax == data['ground_syntax'])
    if data['source']: model.update(fa=judgment, fb=matter, fc=use, fd=support)
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model, individuals=DOMAIN, situations=SCENES, max_steps=100_000_000)]


def checks(texts):
    data = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=6):
        reason, assessment, used, supported, response, motive = bits; pair = reason and assessment and used
        expected = [pair, pair and supported, response, pair and response and motive, pair and supported and response and motive, True, False]
        result = values(data, model_for(data, bits))
        if result != expected: raise ValueError('Reason-use matrix mismatch: ' + repr((bits, result, expected)))
        grid.append(dict(bits=list(bits), result=result))
    print('64 recognition/evaluation/use/support/response/motive profiles passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = setup(text, True); profiles = []; cases = {}
        for actual, perceived, used, motive in product((False, True), repeat=4):
            bits = (perceived, True, used, True, True, motive); pair = perceived and used
            expected = [pair, pair, True, pair and motive, pair and motive, True, actual]
            result = values(data, model_for(data, bits, actual=actual))
            if result != expected: raise ValueError('Source reason-use profile mismatch: ' + repr((actual, bits, result, expected)))
            profiles.append(dict(bits=[actual, perceived, used, motive], result=result))
        for variant in ('other_judge', 'other_subject', 'wrong_assessment_description', 'empty_assessment_candidates', 'reverse_use', 'reverse_support',
            'other_motive_person', 'other_motive_action', 'other_motive_judgment', 'other_motive_time'):
            pair = variant in ('reverse_support', 'other_motive_person', 'other_motive_action', 'other_motive_judgment', 'other_motive_time')
            motivated = variant == 'reverse_support'
            expected = [pair, pair and variant != 'reverse_support', True, motivated, False, True, True]
            result = values(data, model_for(data, variant=variant))
            if result != expected: raise ValueError('Source reason-use contrast mismatch: ' + repr((variant, result, expected)))
            cases[variant] = result
        rows.append(dict(profiles=profiles, cases=cases, disquotations_removed=data['disquotations_removed']))
        print('Source reason-linked response contrasts passed', flush=True)
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Reasoned-response artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Reasoned-response roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']: raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = 'dankbaren'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_reasoned_responses.py', 'scripts/check_reasoned_responses.py', 'scripts/check_recognized_benefits.py',
        'scripts/compose_personal_criteria.py', 'scripts/compose_deserved_responses.py', 'scripts/compose_policy_norms.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/grammar.py', 'noema/meaning_basis.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_reason_linked_evaluation_and_response_not_complete_gratitude', documents=documents, sizes=sizes, interpretation=checks(texts), parent_preserved=True, roundtrips=True,
        new_definitions=6, new_primitives=0, new_author_statements=0, alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args(); result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Reasoned-response record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print('Coincident judgment, reason use, support and motivated response remain distinct')


if __name__ == '__main__': main()
