"""Check joint clauses, same-candidate permission/power and self-imposition tests."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k, app, op
from scripts.compose_self_legislation import ROOT, PARENT, BUILDERS, CLAUSE, CLAUSES, CLAUSE_FIELDS, PACKAGE, POWER, SELF, CRITERION, SOURCE_SELF, SOURCE_CRITERION, RULE, CONTROL, EDGE, TRUE

REPORT = ROOT / 'reports/self-legislation-v1.json'
DOMAIN = ('people', 'monarch', 'law', 'otherlaw', 'frame', 'role', 'assessor', 'other')
SCENES = ('now', 'left', 'right', 'endleft', 'endright', 'other')
EXTRA = '''r jspeople[] a.r jslaw[] a.r jsactor[] a.r jsframe[] a.r jsrole[] a.r jsassessor[] a.
r jsstart[] d.r jsend[] d.r jscontext[] d.
r jscontrolled[''' + CONTROL[2:-3] + '] c.r jsrecognizes[' + EDGE[2:-3] + '] c.' + '''
r jsrequired[''' + RULE[2:-3] + '] c.r jsallowed[' + RULE[2:-3] + '] c.' + '''
r jscandidates[a a d d] c.r jseligible[a a a d] c.r jsadmissible[a a a d] c.r jsvalid[j[a]] c.
r jstruth[j[a] d] c.
d jsexercise[bindings j[a]] e[b scene[k jstruth[v bindings v scene]]].
d jstargeta[bindings j[a]] e[b scene[k jstruth[v bindings v scene]]].
d jstargetb[bindings j[a]] e[b scene[k jstruth[v bindings v scene]]].
r jsnode[] a.r jsauthor[] a.'''
REFS = dict(framework='k jsframe[]', actor='k jsactor[]', capacity='k jsrole[]', exercise='r[p jsexercise]',
    law='k jslaw[]', people='k jspeople[]', start='k jsstart[]', end='k jsend[]', context='k jscontext[]',
    exercisevalid='p jsvalid', controlled='p jscontrolled', recognizes='p jsrecognizes',
    clauses='p jsclauses', assessor='k jsassessor[]', candidates='p jscandidates',
    required='p jsrequired', allowed='p jsallowed', eligible='p jseligible', admissible='p jsadmissible')


def roundtrips(doc):
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        if parse(text) != doc or parse(decode(encode(text, 'v2'))) != doc: raise ValueError('Self legislation roundtrip differs')


def setup(text, source=False, empty=False):
    clauses = []
    for target, status, relation, constructor in (('jstargeta', TRUE, 'p jsrequired', 'hzd3'), ('jstargetb', 'u[' + TRUE + ']', 'p jsallowed', 'hzd4')):
        refs = dict(role='k jsrole[]', target='r[p ' + target + ']', bindings='i[law a people a][l[a][v people v law]]',
            polarity=TRUE, status=status, valid='i[bindings j[a]][k rdr[v bindings n p c b]]', relation=relation)
        fields = [(n, t) for n, t in CLAUSE_FIELDS if not source or n != 'relation']
        clauses.append(k(constructor if source else 'rj7', *(refs[n] for n, _ in fields)))
    catalog = 'd jsclauses[law a] ' + CLAUSES + '[l[' + CLAUSE + '][' + ('' if empty else ' '.join(clauses)) + ']].'
    refs = REFS | dict(clauses='k jsclauses[k jslaw[]]')
    queries = 'q[' + k('rka', *(refs[n] for n, _ in PACKAGE)) + '].'
    queries += 'q[' + k('rkc', *(refs[n] for n, _ in POWER)) + '].'
    current = refs | dict(start='k jscontext[]')
    queries += 'q[' + k('rkc', *(current[n] for n, _ in POWER)) + '].'
    if source:
        content = k('hzd5', *(REFS[n] for n, _ in SOURCE_SELF))
        question = k('hzd6', *(REFS[n] for n, _ in SOURCE_SELF))
        queries += 'q[t[' + content + '][k jscontext[]]].'
        queries += ''.join('q[t[' + k(n, *(REFS[x] for x, _ in SOURCE_CRITERION)) + '][k jscontext[]]].' for n in ('hzd7', 'hzea'))
    else:
        content = 'b scene[' + k('rkd', *((REFS | dict(context='v scene'))[n] for n, _ in SELF)) + ']'
        question = k('rkg', *(REFS[n] for n, _ in SELF if n != 'context'))
        queries += 'q[' + k('rkd', *(REFS[n] for n, _ in SELF)) + '].'
        queries += ''.join('q[' + k(n, *(REFS[x] for x, _ in CRITERION)) + '].' for n in ('rke', 'rkf'))
    queries += 'q[t[o[' + question + ']][k jscontext[]]].q[e[' + question + '][j s[' + content + ']]].'
    return candidate(text, EXTRA + catalog + queries), question


def model_for(doc, bits=(True, True, True, True, True, False), variant='baseline', admissible=True):
    first, second, controlled, recognized, permitted, forbidden = bits
    model = guarded(doc)
    exercise = syntax(quoted('function_ref', 'jsexercise'))
    targets = [syntax(quoted('function_ref', n)) for n in ('jstargeta', 'jstargetb')]
    bindings = ('people', 'people', 'law')
    def norm(kind, source, person, role, target, bound, polarity, scene):
        if (source, person, role, bound.items, polarity) == ('law', 'people', 'role', ('people', 'law'), True):
            if variant == 'other_people' or variant == 'other_law': return False
            if kind == 'required' and target.syntax == targets[0]: return first and scene == 'endleft'
            if kind == 'allowed' and target.syntax == targets[1]:
                if scene in ('left', 'right'): return True
                if scene == 'endleft': return not second or variant == 'split_endpoints'
                if scene == 'endright': return not (second and variant == 'split_endpoints')
                return True
        expected_scene = 'right' if variant == 'split_permission' else 'left'
        if (source, person, role, target.syntax, bound.items, scene) == ('assessor', 'people', 'role', exercise, bindings, expected_scene):
            return forbidden and not polarity if kind == 'required' else permitted and polarity
        return False
    def controls(actor, target, bound, start):
        return controlled and (actor, target.syntax, bound.items, start) == (
            'monarch' if variant == 'other_actor' else 'people',
            targets[0] if variant == 'other_exercise' else exercise,
            ('people', 'law', 'people') if variant == 'wrong_bindings' else bindings,
            'right' if variant == 'split_control' else 'left')
    def recognizes(framework, actor, role, target, bound, start, end):
        return recognized and (framework, actor, role, target.syntax, bound.items, start) == ('frame', 'people', 'role', exercise, bindings, 'left') and end in (('endleft', 'endright') if variant == 'split_endpoints' else ('endleft',))
    model.update(jspeople=lambda: 'people', jslaw=lambda: 'law', jsactor=lambda: 'people', jsframe=lambda: 'frame',
        jsrole=lambda: 'role', jsassessor=lambda: 'assessor', jsstart=lambda: 'left', jsend=lambda: 'endleft', jscontext=lambda: 'now',
        jscontrolled=controls, jsrecognizes=recognizes, jsvalid=lambda b: variant != 'invalid_exercise' and len(b.items) == 3,
        jsrequired=lambda *a: norm('required', *a), jsallowed=lambda *a: norm('allowed', *a),
        jscandidates=lambda people, law, context, branch: variant != 'empty_candidates'
            and (people, law, context) == ('people', 'law', 'other' if variant == 'other_context' else 'now')
            and branch in (('left', 'right') if variant == 'split_permission' else ('left',)),
        jseligible=lambda actor, people, law, context: (actor, people, law, context) == ('monarch', 'people', 'law', 'now'),
        jsadmissible=lambda actor, people, law, context: admissible and (actor, people, law, context) == ('monarch', 'people', 'law', 'now'))
    if 'h7k' in model: model.update(h7k=model['jsrequired'], h7l=model['jsallowed'])
    return model


def checks(texts, source=False):
    docs = [setup(t, source)[0] for t in texts]; cases = []
    for bits in product((False, True), repeat=6):
        first, second, controlled, recognized, permitted, forbidden = bits
        package = first and second; power = package and controlled and recognized
        possible = power and permitted and not forbidden
        want = [package, power, False, possible, possible, possible, possible, False]
        rows = [values(d, model_for(d, bits), DOMAIN, SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Self legislation collapsed clauses, power, permission or question force')
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant in ('split_endpoints', 'split_permission', 'split_control', 'other_people', 'other_law', 'other_actor', 'other_exercise', 'wrong_bindings', 'invalid_exercise', 'empty_candidates', 'other_context', 'empty_clauses'):
        selected = [setup(t, source, True)[0] for t in texts] if variant == 'empty_clauses' else docs
        package = variant not in ('split_endpoints', 'other_people', 'other_law', 'empty_clauses')
        power = variant in ('split_permission', 'empty_candidates', 'other_context')
        want = [package, power, False, False, False, False, False, False]
        rows = [values(d, model_for(d, variant=variant), DOMAIN, SCENES) for d in selected]
        if rows != [want] * len(docs): raise ValueError('Self legislation contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    criteria = []
    for admissible, possible in product((False, True), repeat=2):
        bits = (True, True, True, True, possible, False)
        for doc in docs:
            row = values(doc, model_for(doc, bits, admissible=admissible), DOMAIN, SCENES)
            if row[4:6] != [not admissible or possible, admissible == possible]: raise ValueError('Necessary and sufficient criteria conflated')
        criteria.append(dict(admissible=admissible, possible=possible, results=row[4:6]))
    for doc in docs:
        for name in (('h7k', 'h7l') if source else ('jsrequired', 'jsallowed')) + ('jscontrolled', 'jsrecognizes', 'jscandidates'):
            model = model_for(doc); model[name] = guarded(doc)[name]
            try: values(doc, model, DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown normative or candidate relation supplied by default')
        roundtrips(doc)
    return dict(cases=cases, contrasts=contrasts, criteria=criteria, standalone_agrees=True,
        same_transition_for_all_clauses=True, same_candidate_for_permission_and_power=True,
        actual_permission_or_enactment_not_required=True, exercise_contents_not_executed=True, unknown_relations_refused=True)


def question_checks(texts):
    results = {}
    for variant in ('baseline', 'other_author', 'other_node', 'other_context', 'assertion_instead'):
        for text in texts:
            doc, question = setup(text, True); doc['statements'] = []
            target = description(doc, question)
            if variant == 'assertion_instead':
                target = description(doc, 'j s[k hzd5[' + ' '.join(REFS[n] for n, _ in SOURCE_SELF) + ']]')
            query = k('hzcr', 'k jsnode[]', 'k jsauthor[]', 'r[' + question + ']', 'k jscontext[]')
            doc = parse(format_graph(doc, 'compact') + 'q[' + query + '].')
            model = guarded(doc)
            model.update(jsnode=lambda: 'law', jsauthor=lambda: 'other', jscontext=lambda: 'now',
                hzcr=lambda node, author, desc, context: (node, author, desc.syntax, context) == (
                    'otherlaw' if variant == 'other_node' else 'law',
                    'monarch' if variant == 'other_author' else 'other', syntax(target),
                    'left' if variant == 'other_context' else 'now'))
            if values(doc, model, DOMAIN, SCENES) != [variant == 'baseline']: raise ValueError('Question presentation supplied an answer or changed force')
        results[variant] = variant == 'baseline'
    return dict(cases=results, unknown_norms_and_candidates_not_executed=True, no_answer_asserted=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored self legislation differs')
        roundtrips(doc); documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrases = ['Der Probierstein alles dessen, was über ein Volk als Gesetz beschlossen werden kann, liegt in der Frage:', 'ob ein Volk sich selbst wohl ein solches Gesetz auferlegen könnte?']
    segments = []
    for phrase in phrases:
        if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source range')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
            range=[start, start + len(phrase)], text=phrase, definitions=['rj7', 'rka', 'rkb', 'rkc', 'rkd', 'rke', 'rkf', 'rkg', 'hzd3', 'hzd4', 'hzd5', 'hzd6', 'hzd7', 'hzea']))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_self_legislation.py', 'scripts/check_self_legislation.py', 'scripts/check_assessed_payments.py',
        'scripts/check_closed_policies.py', 'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py',
        'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_hypothetical_self_legislation', documents=documents, sizes=sizes,
        generic=checks([texts[0], texts[2]]), source=checks(texts[1:], True), question=question_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=14, new_primitives=0,
        new_author_statements=0, parent_preserved=True, roundtrips=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Self legislation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Joint normative changes, hypothetical self-imposition and scoped criteria checked')


if __name__ == '__main__': main()
