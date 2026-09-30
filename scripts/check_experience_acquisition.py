"""Test experiences, assessed capacity acquisition and attributed reasons."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_directed_presentations import source_model as presentation_model
from scripts.compose_experience_acquisition import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/experience-acquisition-v1.json'
DOMAIN = ('process', 'trialone', 'trialtwo', 'plan', 'faculty', 'act', 'person', 'other', 'third',
          'population', 'guards', 'high', 'low', 'danger_node', 'learning_node')
SCENES = ('actual', 'begin', 'first', 'second', 'end', 'success', 'belief', 'loss')


def values(doc, model, people=DOMAIN, scenes=SCENES, *, memo=True, budget=20_000_000):
    return [row['value'] for row in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=budget, memoize_definitions=memo)]


def sequence_checks():
    doc = parse(generic_composed()[0] + '''
r za[] j[a].r zb[a] d.r zc[d d] c.r zd[] d.r ze[] d.
q[k r4[k za[] p zb p zc k zd[] k ze[]]].
''')
    count, accepted = 0, 0
    events, scenes = ('a', 'b', 'c'), ('start', 'middle', 'late', 'end')
    for length in range(4):
        for sequence in product(events, repeat=length):
            for indices in product(range(4), repeat=3):
                times = dict(zip(events, indices))
                model = {'za': lambda: SequenceValue(sequence, '"individual"'), 'zb': lambda event: scenes[times[event]],
                    'zc': lambda a, b: scenes.index(a) < scenes.index(b), 'zd': lambda: 'start', 'ze': lambda: 'end'}
                actual = values(doc, model, events, scenes)
                expected = bool(sequence) and all(times[e] < 3 for e in sequence) and all(
                    times[left] < times[right] for left, right in zip(sequence, sequence[1:]))
                if actual != [expected]:
                    raise ValueError('Sequence oracle differs')
                count += 1
                accepted += expected
    # This length would make duplicated evaluation of the prefix exponential.
    many = tuple('event' + str(i) for i in range(24))
    points = tuple('time' + str(i) for i in range(25))
    model = {'za': lambda: SequenceValue(many, '"individual"'), 'zb': lambda event: points[many.index(event)],
        'zc': lambda a, b: points.index(a) < points.index(b), 'zd': lambda: points[0], 'ze': lambda: points[-1]}
    if values(doc, model, many, points, memo=False, budget=5000) != [True]:
        raise ValueError('Long experience sequence failed')
    return {'enumerated_sequences_and_time_assignments': count, 'accepted': accepted,
            'long_sequence_length': 24, 'long_sequence_step_budget': 5000}


def acquisition_checks():
    doc = parse(generic_composed()[0] + '''
r za[a d] c.r zb[a d] c.r zc[a d d] c.r zd[a a d d] c.r ze[a a d] c.r zf[a a a d d] c.
r zg[a] d.r zh[d d] c.r zi[] a.r zj[] a.r zk[] j[a].r zl[] d.r zm[] d.
q[k r5[k zi[] k zj[] k zk[] p zg p zh k zl[] k zm[] p za p zb p zc p zd p ze p zf]].
''')
    scenes = ('begin', 'first', 'second', 'end')
    people = ('learner', 'process', 'one', 'two', 'other')
    rows = []
    def model_for(flags, variant='baseline'):
        assessed_before, assessed_after, capable_before, capable_after, process, contribution = flags
        return {
            'za': lambda person, scene: person == 'learner' and (assessed_before if scene == 'begin' else assessed_after),
            'zb': lambda person, scene: person == 'learner' and (capable_before if scene == 'begin' else capable_after),
            'zc': lambda event, start, end: process and (event, start, end) == ('process', 'begin', 'end'),
            'zd': lambda person, event, start, end: (person, event, start, end) == (
                'other' if variant == 'other_person_changed' else 'learner', 'process', 'begin', 'end'),
            'ze': lambda person, event, scene: person == ('other' if variant == 'other_person_experienced' else 'learner')
                and (event, scene) in (('one', 'first'), ('two', 'second')),
            'zf': lambda event, person, process, start, end: contribution and event in ('one', 'two')
                and (person, process, start, end) == ('learner', 'other' if variant == 'unrelated_process' else 'process',
                    'first' if variant == 'wrong_interval' else 'begin', 'end')
                and not (variant == 'one_unrelated_experience' and event == 'two'),
            'zg': lambda event: 'first' if event == 'one' else 'second',
            'zh': lambda a, b: scenes.index(a) < scenes.index(b), 'zi': lambda: 'learner', 'zj': lambda: 'process',
            'zk': lambda: SequenceValue(() if variant == 'empty' else ('two', 'one') if variant == 'reverse' else
                ('one', 'one') if variant == 'duplicate' else ('one', 'two'), '"individual"'),
            'zl': lambda: 'begin', 'zm': lambda: 'end'}
    for flags in product((False, True), repeat=6):
        result = values(doc, model_for(flags), people, scenes)
        expected = flags[0] and flags[1] and not flags[2] and flags[3] and flags[4] and flags[5]
        if result != [expected]:
            raise ValueError('Acquisition truth conditions differ')
        rows.append({'conditions': list(flags), 'acquired': result[0]})
    contrasts = {}
    for variant in ('other_person_changed', 'other_person_experienced', 'unrelated_process', 'wrong_interval',
                    'one_unrelated_experience', 'empty', 'reverse', 'duplicate'):
        result = values(doc, model_for((True, True, False, True, True, True), variant), people, scenes)
        if result != [False]:
            raise ValueError('Unbound acquisition accepted: ' + variant)
        contrasts[variant] = result[0]
    return {'truth_cases': rows, 'binding_contrasts': contrasts}


def source_model(doc, variant):
    model = presentation_model(doc, 'empty_audience' if variant == 'empty_audience' else 'baseline')
    targets = ('person', 'other', 'third')
    def available(person, plan, point):
        return person in targets and plan == 'plan' and (point == 'end' or
            (point == 'begin' and variant in ('already_capable', 'unassessed_before')))
    def selected(person, plan, start, end):
        return available(person, plan, start) and end == 'success' and not (
            variant == 'unassessed_before' and start == 'begin' or variant == 'unassessed_after' and start == 'end')
    def when(event):
        return 'first' if event == 'trialone' else 'second'
    def outcomes(event, point):
        if variant == 'unknown_result' and event == 'trialone':
            return False
        return event in ('trialone', 'trialtwo') and (point == when(event) or
            variant == 'successful_trial' and event == 'trialone' and point == 'success')
    model.update(za=lambda: 'person', zb=lambda: 'process', zc=lambda: 'end', zd=lambda: 'actual',
        ab=lambda faculty, person, point: (faculty, point) == ('faculty', 'success') and person in targets,
        ac=lambda person, faculty, act, point: person in targets and (faculty, act, point) == ('faculty', 'act', 'success'),
        ad=lambda guide, person, act, point: variant == 'guided_success' and guide == 'guards'
            and person in targets and (act, point) == ('act', 'success'),
        ae=available,
        af=lambda person, plan, start, end: available(person, plan, start) and end == 'success', ap=selected,
        ag=lambda process, start, end: variant != 'no_process' and (process, start, end) == ('process', 'begin', 'end'),
        la=lambda person, process, start, end: person in targets and (process, start, end) == ('process', 'begin', 'end')
            and not (variant == 'wrong_changed_person' and person == 'person'),
        dd=lambda a, b: SCENES.index(a) < SCENES.index(b),
        f5=lambda person, event, description, point: person in targets and event in ('trialone', 'trialtwo')
            and symbol(description) == ('bm' if variant == 'wrong_task' else 'bb') and point == when(event)
            and not (variant == 'wrong_experiencer' and person == 'person'),
        f6=outcomes, f7=when,
        fh=lambda process: SequenceValue(() if process != 'process' or variant == 'no_experiences' else
            ('trialone', 'trialone') if variant == 'duplicate' else ('trialtwo', 'trialone') if variant == 'reversed_experiences'
            else ('trialone', 'trialtwo'), '"individual"'),
        fi=lambda process: 'begin',
        fk=lambda event, person, process, start, end: variant != 'no_contribution' and event in ('trialone', 'trialtwo')
            and person in targets and (process, start, end) == ('process', 'begin', 'end'),
        fl=lambda person, context, end: variant != 'empty_prospects' and person in targets and context == 'actual'
            and (end == ('actual' if variant == 'not_future' else 'end') or variant == 'bad_additional_prospect' and end == 'second'),
        fm=lambda count, context: context == 'actual' and 1 <= count <= (1 if variant == 'too_many' else 3),
        tx=lambda context, end: SCENES.index(context) < SCENES.index(end))
    declared = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: callback for name, callback in model.items() if name in declared}


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] a.r zc[] d.r zd[] d.
q[k fp[k za[] k zb[] k zc[] k zd[]]].q[t[k fr[k za[]]][k zd[]]].
q[t[k up[k za[]]][k zd[]]].q[t[k fs[]][k zd[]]].
''')
    rows = {}
    independent_witness = ('baseline', 'empty_audience', 'empty_prospects', 'not_future', 'bad_additional_prospect')
    for variant in (*independent_witness, 'already_capable', 'unassessed_before', 'unassessed_after',
                    'unknown_result', 'successful_trial', 'guided_success', 'no_process', 'wrong_changed_person',
                    'wrong_task', 'wrong_experiencer', 'no_experiences', 'duplicate', 'reversed_experiences',
                    'no_contribution', 'too_many'):
        result = values(doc, source_model(doc, variant))
        expected = [variant in independent_witness, variant in ('baseline', 'empty_audience'), False, variant == 'baseline']
        if result != expected:
            raise ValueError('Source acquisition or forecast differs: ' + variant + repr(result))
        rows[variant] = dict(zip(('witness', 'prospect', 'current_ability', 'scoped_prospect'), result))
    return {'cases': rows, 'definitions_replaced_by_primitives': False}


def attribution_checks():
    doc = candidate(source_composed()[0], 'q[k ft[]].')
    rows = {}
    def forbidden(*args):
        raise ValueError('Reason attribution evaluated underlying learning or danger')
    for variant in ('baseline', 'wrong_author', 'wrong_content', 'reversed_reason', 'empty_reason', 'extra_reason', 'reversed_text'):
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        def claim(node, author, description, context):
            syntax = json.loads(description.syntax)
            expected = 'fs' if node == 'learning_node' else 'e3' if variant == 'wrong_content' else 'e4'
            return (author, context) == ('person' if variant == 'wrong_author' else 'guards', 'actual') and syntax == {
                'kind': 'call', 'symbol': expected, 'arguments': []}
        def reason(author, premises, conclusion, context):
            expected = [] if variant == 'empty_reason' else ['learning_node', 'person'] if variant == 'extra_reason' else [
                'danger_node' if variant == 'reversed_reason' else 'learning_node']
            return (author, context, conclusion) == ('guards', 'actual',
                'learning_node' if variant == 'reversed_reason' else 'danger_node') and [p for p in DOMAIN if premises(p)] == expected
        model.update(fu=lambda: 'danger_node', fv=lambda: 'learning_node', wa=lambda: 'guards', wh=lambda: 'actual',
            uc=claim, ud=reason, ue=lambda a, b, context: (a, b, context) == (
                'learning_node' if variant == 'reversed_text' else 'danger_node',
                'danger_node' if variant == 'reversed_text' else 'learning_node', 'actual'))
        result = values(doc, model)
        if result != [variant == 'baseline']:
            raise ValueError('Attributed reason differs: ' + variant + repr(result))
        rows[variant] = {'attribution': result[0], 'underlying_contents_evaluated': False}
    return rows


def alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
                if u['id'] == 'kant-1784:u0009')
    text = unit['text']
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Pinned source differs')
    start = text.index('denn sie würden')
    end = text.index('; allein', start)
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': end,
        'source': text[start:end], 'definitions': ['fg', 'fo', 'fp', 'fq', 'fr', 'fs', 'ft'],
        'status': 'partial_explicit_reading', 'full_semantic_equivalence': False,
        'remaining': ['literal falling and walking', 'metaphorical correspondence', 'experience and causal mechanism',
            'degree improvement and modal pragmatics', 'concession and discouragement', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored experience acquisition differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Experience acquisition roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/experience-acquisition-basis-v1.json', 'data/kant-experience-acquisition-basis-v1.json',
        'examples/v014/kant-directed-presentations.noema', 'data/kant-directed-presentations-basis-v1.json',
        'scripts/compose_experience_acquisition.py', 'scripts/check_experience_acquisition.py',
        'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'prospective_experience_acquisition_and_attributed_reason', 'documents': documents,
        'sequences': sequence_checks(), 'acquisition': acquisition_checks(), 'source': source_checks(),
        'attribution': attribution_checks(), 'alignment': alignment(), 'roundtrips': True,
        'inherited_statements_unchanged': parse(source_composed()[0])['statements'] == parse(
            (ROOT / 'examples/v014/kant-directed-presentations.noema').read_text(encoding='utf-8'))['statements'],
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Experience acquisition report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('2560 sequence, 64 acquisition, 8 binding, 20 source and 7 attribution cases verified')


if __name__ == '__main__':
    main()
