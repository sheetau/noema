"""Check actual achievement, fallible recognition and correctly bound responses."""
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
from scripts.compose_cohort_responses import DUAL
from scripts.compose_recognized_benefits import ROOT, PARENT, BUILDERS, GOAL, DESCRIPTION, RECOGNITION, SOURCE_RECOGNITION, MEANINGS

REPORT = ROOT / 'reports/recognized-benefits-v1.json'
DOMAIN = ('alice', 'giver', 'other', 'benefit', 'reply', 'judgment', 'oldgroup', 'newgroup', 'early', 'late', 'listener')
SCENES = ('past', 'done', 'now', 'hypast', 'hydone', 'belief', 'future')
ACTUAL = ('past', 'done', 'now', 'future')
BELIEF = ('hypast', 'hydone', 'belief')
EXTRA = '''r jrtarget[] a.r jrperson[] a.r jractivity[] a.r jrreply[] a.r jrcontext[] d.
r jrstate[a] e.r jrhistory[d d] c.r jrorder[d d d] c.
r jrrecord[a a a ''' + GOAL + ''' d d] c.r jrfavor[a ''' + GOAL + ''' d] c.
r jrjudgments[a a d] c.r jrmatters[a a d] c.r jrlinked[a ''' + DESCRIPTION + ''' j[a] d] c.r jrcandidates[a d d] c.
r jrresponse[a a a] e.r jrfirstgroup[] a.r jrnextgroup[] a.r jrearlier[] a.r jrlater[] a.
r jrbelongs[a a d] c.r jrperiods[a d] c.r jraudience[a] c.'''


def select(data, indices):
    result = dict(data); result['document'] = deepcopy(data['document'])
    result['document']['statements'] = [result['document']['statements'][i] for i in indices]
    return result


def setup(text, source=False):
    base = parse(text); base['statements'] = []; base = parse(format_graph(base, 'compact') + EXTRA)
    histories = 'i[context d][i[point d][k jrhistory[v context v point]]]'
    orders = 'i[context d][i[first d second d][k jrorder[v context v first v second]]]'
    achievements = 'i[context d][i[person a activity a target a goal ' + GOAL + ' completion d][k jrrecord[v person v activity v target v goal v completion v context]]]'
    removed = 0
    if source:
        spec = specialize_definition(base, 'hzgk', 'jrbenefit', {0: description(base, 'p jrstate')})
        base = spec.document; removed += spec.disquotations_removed
        criterion = k('jrbenefit', histories, orders)
    else: criterion = k('roq', k('rop', 'r[p jrstate]', histories, orders, achievements, 'p jrfavor'))
    fields = dict(activity='k jractivity[]', judgments='p jrjudgments', matters='p jrmatters', linked='p jrlinked', candidates='p jrcandidates')
    spec = specialize_definition(base, 'hzgl' if source else 'ror', 'jrrecognition', {0: description(base, criterion)})
    base = spec.document; removed += spec.disquotations_removed
    recognition = k('jrrecognition', *(fields[n] for n, _ in (SOURCE_RECOGNITION if source else RECOGNITION) if n != 'criterion'))
    message = 'i[person a][j s[c[p jrstate][v person]]]'
    refs = {n: 'k jr' + n + '[]' for n in ('firstgroup', 'nextgroup', 'earlier', 'later', 'context')}
    refs.update(belongs='p jrbelongs', periods='p jrperiods', audience='p jraudience', message='r[' + message + ']')
    response = k('hzgj', *(refs[n] for n, _ in DUAL)) if source else 'p jrresponse'
    gated = k('ros', recognition, response)
    bindings = 'l[a][k jrtarget[] k jrperson[] k jractivity[]]'
    at = lambda expression: 't[' + expression + '][k jrcontext[]]'
    actual = lambda expr: at('c[' + expr + '][k jrtarget[] k jrreply[] k jrperson[]]')
    queries = [at('c[' + criterion + '][' + bindings + ']'), at('c[' + recognition + '][k jrtarget[] k jrperson[]]'), actual(response), actual(gated),
        'e[r[' + gated + ']][r[' + gated + ']]', at('c[' + criterion + '][l[a][k jrperson[] k jrtarget[] k jractivity[]]]'),
        at('c[' + criterion + '][l[a][k jrtarget[] k jrperson[]]]')]
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=source, criterion=criterion, recognition=recognition, response=response, gated=gated,
        criterion_syntax=syntax(description(base, criterion)), goal_syntax=syntax(description(base, 'p jrstate')),
        message_syntax=syntax(description(base, message)), disquotations_removed=removed)


def model_for(data, bits=(True,) * 6, variant='baseline'):
    actual, favored, perceived, preferred, linked, speaks = bits
    def branch(context): return BELIEF if context in BELIEF else ACTUAL
    def history(context, point): return point in branch(context)
    def order(context, first, second):
        points = branch(context)
        return first in points and second in points and points.index(first) < points.index(second)
    def favor(person, goal, context):
        return person == 'alice' and goal.syntax == data['goal_syntax'] and (preferred if context in BELIEF else favored)
    def record(person, activity, target, goal, completion, context):
        endpoint = 'hydone' if context in BELIEF else 'future' if variant == 'future_achievement' else 'done'
        return (perceived if context in BELIEF else actual) and (person, activity, target, completion) == ('giver', 'benefit', 'alice', endpoint) and goal.syntax == data['goal_syntax']
    def judgment_link(judgment, criterion, bindings, context):
        expected = ('alice', 'giver', 'reply' if variant == 'wrong_activity_link' else 'benefit')
        return linked and (judgment, context) == ('judgment', 'now') and criterion.syntax == data['criterion_syntax'] and tuple(bindings.items) == expected and variant != 'wrong_criterion'
    model = guarded(data['document'])
    model.update(jrtarget=lambda: 'alice', jrperson=lambda: 'giver', jractivity=lambda: 'benefit', jrreply=lambda: 'reply', jrcontext=lambda: 'now',
        jrhistory=history, jrorder=order, jrrecord=record, jrfavor=favor,
        jrstate=lambda person: Content(SCENES, tuple(person == 'alice' and point not in ('past', 'hypast') for point in SCENES)),
        jrjudgments=lambda person, judgment, context: (person, judgment, context) == ('alice', 'judgment', 'now'),
        jrmatters=lambda judgment, subject, context: (judgment, subject, context) == ('judgment', 'other' if variant == 'wrong_judgment_subject' else 'giver', 'now'),
        jrlinked=judgment_link,
        jrcandidates=lambda judgment, context, point: variant != 'empty_candidates' and (judgment, context) == ('judgment', 'now') and (point == 'belief' or variant == 'mixed_candidates' and point == 'now'),
        jrresponse=lambda speaker, activity, subject: Content(SCENES, tuple(speaks and (speaker, activity, subject, point) == ('alice', 'reply', 'giver', 'now') for point in SCENES)),
        jrfirstgroup=lambda: 'oldgroup', jrnextgroup=lambda: 'newgroup', jrearlier=lambda: 'early', jrlater=lambda: 'late',
        jrbelongs=lambda group, person, context: variant != 'outside_cohort' and context == 'now' and group in ('oldgroup', 'newgroup') and person == 'alice',
        jrperiods=lambda epoch, point: (epoch, point) in (('early', 'now'), ('late', 'future')),
        jraudience=lambda person: person == 'listener')
    if data['source']:
        def endpoint(point):
            return point == 'hydone' and perceived or point == ('future' if variant == 'future_achievement' else 'done') and actual
        def changes(activity, earlier, later):
            return activity == 'benefit' and (earlier, later) in (('past', 'future' if variant == 'future_achievement' else 'done'), ('hypast', 'hydone'))
        model.update(id=favor, fa=model['jrjudgments'], fb=model['jrmatters'],
            ag=changes, la=lambda target, activity, earlier, later: target == 'alice' and changes(activity, earlier, later),
            dg=lambda activity, point: activity == 'benefit' and endpoint(point) or speaks and (activity, point) == ('reply', 'now'),
            df=lambda person, activity, point: (person, activity) == ('giver', 'benefit') and endpoint(point),
            g3=lambda activity, target, goal, point: variant != 'no_cause' and (activity, target) == ('benefit', 'alice') and endpoint(point) and goal.syntax == data['goal_syntax'],
            f3=lambda speaker, activity, point: speaks and (speaker, activity, point) == ('alice', 'reply', 'now'),
            f2=lambda activity, audience, subject, message, point: speaks and (activity, audience, subject, point) == ('reply', 'listener', 'other' if variant == 'wrong_response_subject' else 'giver', 'now') and message.syntax == data['message_syntax'])
    return model


def values(data, model):
    return [r['value'] for r in evaluate_document(data['document'], primitives=model, individuals=DOMAIN, situations=SCENES, max_steps=40_000_000)]


def checks(texts):
    data = select(setup(texts[0]), range(5)); grid = []
    for bits in product((False, True), repeat=6):
        recognition = all(bits[2:5]); expected = [all(bits[:2]), recognition, bits[5], recognition and bits[5], True]
        result = values(data, model_for(data, bits))
        if result != expected: raise ValueError('Recognition matrix failed: ' + repr((bits, result, expected)))
        grid.append(dict(bits=list(bits), result=result))
    print('64 actual/perceived benefit and response profiles passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = setup(text, True); profiles = []; cases = {}
        for actual, perceived, linked, speaks in product((False, True), repeat=4):
            expected = [actual, perceived and linked, speaks, perceived and linked and speaks, True, False, False]
            result = values(data, model_for(data, (actual, True, perceived, True, linked, speaks)))
            if result != expected: raise ValueError('Source causal recognition mismatch: ' + repr((actual, perceived, linked, speaks, result)))
            profiles.append(dict(bits=[actual, perceived, linked, speaks], result=result))
        for variant, expected in (
            ('future_achievement', [False, True, True, True, True, False, False]),
            ('wrong_activity_link', [True, False, True, False, True, False, False]),
            ('wrong_criterion', [True, False, True, False, True, False, False]),
            ('wrong_judgment_subject', [True, False, True, False, True, False, False]),
            ('empty_candidates', [True, False, True, False, True, False, False]),
            ('no_cause', [False, False, True, False, True, False, False]),
            ('wrong_response_subject', [True, True, False, False, True, False, False]),
            ('outside_cohort', [True, True, False, False, True, False, False])):
            result = values(data, model_for(data, variant=variant))
            if result != expected: raise ValueError('Recognition contrast failed: ' + repr((variant, result, expected)))
            cases[variant] = result
        rows.append(dict(profiles=profiles, cases=cases, disquotations_removed=data['disquotations_removed']))
        print('Source recognition and response contrasts passed', flush=True)
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Recognized-benefit artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Recognized-benefit roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']: raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = 'dankbaren'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_recognized_benefits.py', 'scripts/check_recognized_benefits.py', 'scripts/compose_first_achievers.py', 'scripts/compose_personal_criteria.py', 'scripts/compose_cohort_responses.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/grammar.py', 'noema/meaning_basis.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_recognition_of_favorably_received_achievements_not_complete_gratitude', documents=documents, sizes=sizes, interpretation=checks(texts), parent_preserved=True, roundtrips=True,
        new_definitions=7, new_primitives=0, new_author_statements=0, alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args(); result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Recognized-benefit record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print('Favorable achievement, fallible recognition and response remain distinct')


if __name__ == '__main__': main()
