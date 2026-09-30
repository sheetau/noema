"""Check directed conditional presentations without endorsing their contents."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.check_described_appraisals import candidate, source_model as appraisal_model
from scripts.check_described_explanations import symbol
from scripts.check_scoped_interventions import DOMAIN, STATE, source_model as prevention_model
from scripts.compose_directed_presentations import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/directed-presentations-v1.json'
SOURCE_DOMAIN = (*DOMAIN, 'warning', 'otherwarning')
SOURCE_SCENES = ('actual', 'prior', 'belief', 'loss')


def values(doc, model, people, scenes, budget=10_000_000):
    return [row['value'] for row in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=budget, memoize_definitions=True)]


def presentation_checks():
    doc = parse(generic_composed()[0] + '''
r za[] d.r zb[a] c.r zc[a] c.r zd[a] a.r ze[a d] c.r zf[a a d] c.
r zg[a a a i[h[a] f] d] c.r zh[a d] c.
d zi[person a] f[j s[b context[k zh[v person v context]]]].
q[k r2[p zb p zc p zd r[p zi] k za[] p ze p zf p zg]].
''')
    people = ('a', 'b', 'x', 'y', 'subjectx', 'subjecty', 'act')
    rows = []
    def forbidden(*args):
        raise ValueError('Presentation evaluated the described assertion')
    for occurs, first_sender, second_sender, first_recipient, second_recipient in product((False, True), repeat=5):
        model = {'za': lambda: 'now', 'zb': lambda p: p in ('a', 'b'), 'zc': lambda p: p in ('x', 'y'),
            'zd': lambda p: 'subjectx' if p == 'x' else 'subjecty',
            'ze': lambda act, context: occurs and (act, context) == ('act', 'now'),
            'zf': lambda sender, act, context: (act, context) == ('act', 'now')
                and ((sender == 'a' and first_sender) or (sender == 'b' and second_sender)),
            'zg': lambda act, recipient, subject, description, context: (act, symbol(description), context) == ('act', 'zi', 'now')
                and ((recipient, subject) == ('x', 'subjectx') and first_recipient
                     or (recipient, subject) == ('y', 'subjecty') and second_recipient), 'zh': forbidden}
        result = values(doc, model, people, ('now',))
        if result != [all((occurs, first_sender, second_sender, first_recipient, second_recipient))]:
            raise ValueError('Bound presentation differs')
        rows.append({'occurs': occurs, 'senders': [first_sender, second_sender],
                     'recipients': [first_recipient, second_recipient], 'presented': result[0]})
    return rows


def temporal_checks():
    doc = parse(generic_composed()[0] + '''
r za[] d.r zb[d d] c.r zc[d] c.q[k r3[k za[] p zb p zc]].
''')
    scenes, rows = ('first', 'now', 'third'), []
    for flags in product((False, True), repeat=6):
        before = dict(zip(scenes, flags[:3]))
        holds = dict(zip(scenes, flags[3:]))
        model = {'za': lambda: 'now', 'zb': lambda a, b: b == 'now' and before[a], 'zc': lambda s: holds[s]}
        result = values(doc, model, ('object',), scenes)
        expected = any(s != 'now' and before[s] and holds[s] for s in scenes)
        if result != [expected]:
            raise ValueError('Earlier time and prerequisite used different situations')
        rows.append({'before': before, 'prerequisite': holds, 'valid': result[0]})
    return rows


def conditional_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.
d zq[person a] f[j q[k eu[v person]]].
q[t[k eu[k za[]]][k zb[]]].q[t[k e2[k za[]]][k zb[]]].q[t[k et[k za[]]][k zb[]]].
q[e[o[k ev[k za[]]]][o[k zq[k za[]]]]].q[u[e[k ev[k za[]]][k zq[k za[]]]]].
''')
    rows = []
    for attempt, danger, nonempty, actual_danger in product((False, True), repeat=4):
        model = appraisal_model(doc)
        def forbidden(*args):
            raise ValueError('Possibility of harm required a high degree of danger')
        model.update(za=lambda: 'person', zb=lambda: 'actual',
            ei=lambda person, description, context: attempt and (person, symbol(description), context) == ('person', 'bb', 'case'),
            f4=lambda person, context, case: nonempty and (person, context, case) == ('person', 'actual', 'case'),
            uq=lambda person, description, context, outcome: (person, symbol(description), outcome) == ('person', 'up', 'loss')
                and ((context == 'case' and danger) or (context == 'actual' and actual_danger)),
            ur=lambda person, outcome: (person, outcome) == ('person', 'loss'), us=forbidden, ut=forbidden)
        required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
        model = {name: value for name, value in model.items() if name in required}
        result = values(doc, model, SOURCE_DOMAIN, ('actual', 'case', 'loss'))
        expected = [nonempty and (not attempt or danger), nonempty and attempt, actual_danger, True, True]
        if result != expected:
            raise ValueError('Conditional message, applicability or force differs')
        rows.append({'case_attempt': attempt, 'case_danger': danger, 'nonempty_cases': nonempty,
            'actual_danger': actual_danger, 'conditional': result[0], 'applicable': result[1],
            'same_assertion_and_question_content': result[3], 'different_message_force': result[4]})
    return rows


def source_model(doc, variant):
    model = prevention_model(doc, 'baseline')
    targets = ('person', 'other', 'third')
    def equations(group, person, context):
        return FunctionValue(('individual', STATE), 'truth', lambda variable, state:
            True if variable == 'restriction' else not state('restriction') if
            (group == 'guards' and person in targets and context == 'prior' and variant != 'no_prior_effect') else False)
    def occurs(act, context):
        return (act == 'activity' and context == 'prior') or (
            variant != 'no_presentation_event' and act in ('warning', 'otherwarning') and context == 'actual')
    def presents(sender, act, context):
        return sender in ('guardone', 'guardtwo') and context == 'actual' and act == (
            'otherwarning' if variant == 'split_senders' and sender == 'guardtwo' else 'warning')
    def conveys(act, recipient, subject, description, context):
        return recipient in targets and (act, subject, symbol(description), context) == (
            'otherwarning' if variant == 'split_recipients' and recipient == 'third' else 'warning',
            'other' if variant == 'wrong_subject' else recipient,
            'zq' if variant == 'wrong_message_force' else 'ev',
            'prior' if variant == 'wrong_presentation_context' else 'actual')
    def forbidden(*args):
        raise ValueError('Presentation evaluated its conditional content')
    model.update(za=lambda: 'actual', zb=lambda: 'prior', eh=equations, ei=lambda *args: False,
        dg=occurs, df=lambda sender, act, context: sender in ('guardone', 'guardtwo') and (act, context) == ('activity', 'prior'),
        ep=lambda act, person, context: person in targets and (act, context) == ('activity', 'prior')
            and not (variant == 'unrestricted_prior_target' and person == 'other'),
        dd=lambda earlier, later: (earlier, later) == (
            ('actual', 'prior') if variant == 'reversed_time' else ('actual', 'actual') if variant == 'same_time' else ('prior', 'actual')),
        f2=conveys, f3=presents, f4=forbidden)
    if variant == 'empty_audience':
        model['u3'] = lambda *args: False
    if variant == 'empty_senders':
        base_members = model['mp']
        model['mp'] = lambda group: SequenceValue((), '"individual"') if group == 'guards' else base_members(group)
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: value for name, value in model.items() if name in required}


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] d.r zb[] d.
d zq[person a] f[j q[k eu[v person]]].
q[t[k ew[k db[]]][k za[]]].q[t[k ex[k db[]]][k za[]]].
q[g person a[k dj[v person k zb[]]]].
''')
    rows = {}
    for variant in ('baseline', 'split_senders', 'split_recipients', 'wrong_subject', 'wrong_message_force',
                    'wrong_presentation_context', 'no_presentation_event', 'empty_audience', 'empty_senders',
                    'reversed_time', 'same_time', 'no_prior_effect', 'unrestricted_prior_target'):
        result = values(doc, source_model(doc, variant), SOURCE_DOMAIN, SOURCE_SCENES)
        presentation = variant in ('baseline', 'reversed_time', 'same_time', 'no_prior_effect', 'unrestricted_prior_target')
        expected = [presentation, variant == 'baseline', False]
        if result != expected:
            raise ValueError('Directed source presentation or stable recipient scope differs: ' + variant + repr(result))
        rows[variant] = {'presentation': result[0], 'after_same_recipients_prevented': result[1],
            'earlier_context_has_same_selection': result[2], 'communicated_conditional_evaluated': False}
    return rows


def degree_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.q[t[k et[k za[]]][k zb[]]].q[t[k uw[k za[]]][k zb[]]].
q[t[k e3[k za[]]][k zb[]]].q[t[k e4[]][k zb[]]].
''')
    rows = {}
    for variant in ('some_danger_not_high', 'actually_high', 'no_danger', 'empty_audience'):
        model = source_model(doc, variant)
        original_degree, original_prospects = model['us'], model['uq']
        model.update(za=lambda: 'person', zb=lambda: 'actual',
            us=lambda person, description, context: 'high' if variant == 'actually_high' and context == 'actual'
                else original_degree(person, description, context),
            uq=lambda person, description, context, outcome: not (variant == 'no_danger' and context == 'actual')
                and original_prospects(person, description, context, outcome))
        result = values(doc, model, SOURCE_DOMAIN, SOURCE_SCENES)
        expected = [variant != 'no_danger', variant == 'actually_high',
                    variant in ('some_danger_not_high', 'empty_audience'), variant == 'some_danger_not_high']
        if result != expected:
            raise ValueError('Not-so-great danger was confused with absence of danger: ' + variant + repr(result))
        rows[variant] = dict(zip(('possible_adversity', 'very_high_danger', 'not_so_great', 'scoped_claim'), result))
    return rows


def alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
                if u['id'] == 'kant-1784:u0009')
    text = unit['text']
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Pinned source differs')
    start = text.index('so zeigen sie ihnen nachher')
    end = text.index('Nun ist diese Gefahr', start)
    excerpt = text[start:end].rstrip()
    degree_end = text.index(', denn', end)
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'segments': [
        {'start': start, 'end': start+len(excerpt), 'source': excerpt,
         'definitions': ['et', 'eu', 'ev', 'ew', 'ex'], 'status': 'partial_explicit_reading'},
        {'start': end, 'end': degree_end, 'source': text[end:degree_end],
         'definitions': ['e3', 'e4'], 'status': 'partial_explicit_reading'}],
        'full_semantic_equivalence': False,
        'remaining': ['evidential force of showing', 'literal walking depiction', 'earlier cognitive change',
            'model grounding for preceding prevention', 'comparative standard and concession', 'learning and discouragement', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored directed presentation differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Directed presentation roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/directed-presentations-basis-v1.json', 'data/kant-directed-presentations-basis-v1.json',
        'examples/v014/kant-scoped-interventions.noema', 'data/kant-scoped-interventions-basis-v1.json',
        'scripts/compose_directed_presentations.py', 'scripts/check_directed_presentations.py',
        'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'directed_conditional_presentation_after_model_relative_prevention', 'documents': documents,
        'presentation': presentation_checks(), 'temporal': temporal_checks(), 'conditional': conditional_checks(),
        'source': source_checks(), 'degree': degree_checks(), 'alignment': alignment(), 'roundtrips': True,
        'inherited_statements_unchanged': parse(source_composed()[0])['statements'] == parse(
            (ROOT / 'examples/v014/kant-scoped-interventions.noema').read_text(encoding='utf-8'))['statements'],
        'definitions_replaced_by_primitives': False,
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Directed presentation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('32 presentation, 64 temporal, 16 conditional, 13 source and 4 danger-degree cases verified')


if __name__ == '__main__':
    main()
