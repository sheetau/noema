"""Verify assessed attainment, ongoing development and one shared epoch dialogue."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_clear_indications as indications
from scripts.compose_limits import call as k
from scripts.compose_enlightening_epoch import ROOT, PARENT, BUILDERS, FRAME, CHECKED, ATTAINED, PROGRESS, CONTRAST, QUESTION, ANSWER, SOURCE, SOURCE_ANSWER

REPORT = ROOT / 'reports/enlightening-epoch-v1.json'
DOMAIN = ('alice', 'bob', 'epoch')
SCENES = ('past', 'now', 'future')
EXTRA = '''r jqepoch[] a.r jqcontext[] d.r jqhistory[d] c.r jqbefore[d d] c.r jqperiods[a d] c.
r jqpeople[a] c.r jqpresent[a d] c.r jqassessed[a] e.r jqcapable[a] e.r jqprogress[] e.
r jqfirst[] a.r jqsecond[] a.r jqauthor[] a.'''
REFS = {n: 'k jq' + n + '[]' for n in ('epoch', 'context', 'progress')}
REFS.update({n: 'p jq' + n for n in ('history', 'before', 'periods', 'people', 'present', 'assessed', 'capable')})


def finish(base, refs, source=False, **extra):
    if source:
        complete = k('hzfb', *(refs[n] for n, _ in SOURCE))
        answer = k('hzfc', *(refs[n] for n, _ in SOURCE_ANSWER))
        question = k('hzfd', *(refs[n] for n, _ in SOURCE))
        response = k('hzfe', *(refs[n] for n, _ in SOURCE_ANSWER))
        expressions = [k('rmi', *(refs[n] for n, _ in CHECKED)), 't[' + complete + '][' + refs['context'] + ']',
            k('rmk', *(refs[n] for n, _ in PROGRESS)), 't[' + answer + '][' + refs['context'] + ']']
    else:
        question = k('rmm', *(refs[n] for n, _ in QUESTION))
        response = k('rmn', *(refs[n] for n, _ in ANSWER))
        answer = 'b point[' + k('rml', *({**refs, 'context': 'v point'}[n] for n, _ in CONTRAST)) + ']'
        expressions = [k(name, *(refs[n] for n, _ in fields)) for name, fields in (
            ('rmi', CHECKED), ('rmj', ATTAINED), ('rmk', PROGRESS), ('rml', CONTRAST))]
    expressions.append('e[' + question + '][' + response + ']')
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + expr + '].' for expr in expressions))
    return dict(document=doc, refs=refs, question=question, answer=answer, source=source, **extra)


def setup(text): return finish(candidate(text, EXTRA), REFS)


def source_setup(text):
    progress = indications.source_setup(text); base = progress['document']; base['statements'] = []
    base = parse(format_graph(base, 'compact') + EXTRA)
    refs = {**REFS, 'history': 'p jnhistory', 'before': 'p jnbefore', 'people': 'p jnpeople',
        'assessed': 'p fo', 'capable': 'p h4l', 'progress': progress['target']}
    return finish(base, refs, True, progress_data=progress)


def generic_model(data, bits=(True, True, False, False, True), variant='baseline'):
    first_assessed, second_assessed, first_capable, second_capable, progress = bits
    model = guarded(data['document'])
    model.update(jqepoch=lambda: 'epoch', jqcontext=lambda: 'now', jqhistory=lambda point: point in SCENES,
        jqbefore=lambda first, last: SCENES.index(first) < SCENES.index(last),
        jqperiods=lambda epoch, point: epoch == 'epoch' and (point != 'now' if variant == 'hole' else point in SCENES),
        jqpeople=lambda person: person in ('alice', 'bob') and variant != 'empty_people',
        jqpresent=lambda person, point: person in ('alice', 'bob') and not (variant == 'absent_person' and person == 'bob' and point == 'now'),
        jqassessed=lambda person: Content(SCENES, tuple((first_assessed if person == 'alice' else second_assessed) for _ in SCENES)),
        jqcapable=lambda person: Content(SCENES, tuple((first_capable if person == 'alice' else second_capable) for _ in SCENES)),
        jqprogress=lambda: Content(SCENES, (progress,) * len(SCENES)))
    return model


SOURCE_DOMAIN = (*indications.SOURCE_DOMAIN, 'epoch', 'questionnode', 'answernode', 'author')


def source_model(data, variant='baseline'):
    model = indications.source_model(data['progress_data'], 'no_opportunity' if variant == 'no_progress' else 'baseline')
    # The available practice method also needs a nonempty capability evaluation;
    # performing the practice does not itself achieve the capability goal.
    selected = model['ap']; occurs = model['af']; own_use = model['ac']
    model['ap'] = lambda person, plan, start, end: (
        occurs(person, plan, start, end) and not (variant == 'unassessed' and start == 'last')) if plan == 'practice' else selected(person, plan, start, end)
    model['ac'] = lambda person, faculty, act, point: own_use(person, faculty, act, point) or (
        variant == 'attained' and (person, faculty, act, point) == ('person', 'faculty', 'act', 'last'))
    model.update({name: callback for name, callback in guarded(data['document']).items() if name not in model})
    model.update(jqepoch=lambda: 'epoch', jqcontext=lambda: 'last',
        jqperiods=lambda epoch, point: epoch == 'epoch' and point in indications.decline.TIMES and not (variant == 'wrong_epoch' and point == 'last'),
        jqpresent=lambda person, point: person == 'person' and variant != 'absent_person')
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model,
        individuals=SOURCE_DOMAIN if data['source'] else DOMAIN,
        situations=indications.SOURCE_SCENES if data['source'] else SCENES, max_steps=32_000_000)]


def discourse_setup(data):
    base = data['document']; base = {**base, 'statements': []}
    qsyntax = syntax(description(base, data['question'])); asyntax = syntax(description(base, data['answer']))
    body = k('hzcu', 'k jqfirst[]', 'k jqsecond[]', 'k jqauthor[]', 'k jqcontext[]',
        'r[' + data['question'] + ']', 'r[' + data['answer'] + ']')
    doc = parse(format_graph(base, 'compact') + 'q[' + body + '].')
    return {**data, 'document': doc}, qsyntax, asyntax


def discourse_model(data, qsyntax, asyntax, variant='baseline'):
    model = guarded(data['document'])
    model.update(jqfirst=lambda: 'questionnode', jqsecond=lambda: 'answernode', jqauthor=lambda: 'author', jqcontext=lambda: 'last',
        hzcr=lambda node, author, message, point: (node, author, point) == ('questionnode', 'author', 'last') and message.syntax == qsyntax,
        uc=lambda node, author, content, point: (node, author, point) == ('answernode', 'author', 'last') and content.syntax == asyntax and variant != 'wrong_answer',
        ue=lambda first, second, point: (first, second, point) == ('questionnode', 'answernode', 'last') and variant != 'reversed_order',
        hzcs=lambda author, first, second, point: (author, first, second, point) == ('author', 'questionnode', 'answernode', 'last') and variant != 'unrelated_response')
    return model


def checks(texts):
    generic = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=5):
        evaluated = all(bits[:2]); attained = evaluated and all(bits[2:4]); progress = bits[4]
        expected = [evaluated, attained, progress, evaluated and not attained and progress, False]
        actual = values(generic, generic_model(generic, bits))
        if actual != expected: raise ValueError('Epoch statuses conflated: ' + repr((bits, actual)))
        grid.append(dict(bits=list(bits), result=actual))
    for variant in ('hole', 'empty_people', 'absent_person'):
        if values(generic, generic_model(generic, variant=variant)) != [False] * 5:
            raise ValueError('Invalid epoch or present population accepted')
    print('32 attainment/assessment/progress combinations passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = source_setup(text); cases = {}
        for variant, expected in (
            ('baseline', [True, False, True, True, False]), ('attained', [True, True, True, False, False]),
            ('no_progress', [True, False, False, False, False]), ('unassessed', [False, False, True, False, False]),
            ('wrong_epoch', [False] * 5), ('absent_person', [False] * 5)):
            actual = values(data, source_model(data, variant))
            if actual != expected: raise ValueError('Concrete epoch contrast failed: ' + repr((variant, actual)))
            cases[variant] = actual; print('Shared epoch contrast:', variant, 'passed', flush=True)
        discourse, question, answer = discourse_setup(data); attribution = {}
        for variant in ('baseline', 'wrong_answer', 'reversed_order', 'unrelated_response'):
            actual = values(discourse, discourse_model(discourse, question, answer, variant))
            if actual != [variant == 'baseline']: raise ValueError('Question/answer attribution lost its reference')
            attribution[variant] = actual
        rows.append(dict(cases=cases, quoted_dialogue=attribution))
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Enlightening epoch artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Enlightening epoch roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0014')
    phrase = 'Wenn denn nun gefragt wird: Leben wir jetzt in einem aufgeklärten Zeitalter? so ist die Antwort: Nein, aber wohl in einem Zeitalter der Aufklärung.'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_enlightening_epoch.py', 'scripts/check_enlightening_epoch.py', 'scripts/check_clear_indications.py',
        'scripts/check_declining_hindrances.py', 'scripts/check_free_pursuit.py', 'scripts/check_assessed_payments.py',
        'scripts/check_public_assessment.py', 'scripts/check_scoped_counts.py', 'scripts/check_described_appraisals.py',
        'scripts/check_rod_setup.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py',
        'noema/extraction.py', 'noema/specialization.py', 'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_shared_epoch_attainment_and_development_dialogue', documents=documents, sizes=sizes,
        interpretation=checks(texts), parent_preserved=True, roundtrips=True, new_definitions=11, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase,
            definitions=['rmh', 'rmi', 'rmj', 'rmk', 'rml', 'rmm', 'rmn', 'hzfb', 'hzfc', 'hzfd', 'hzfe'])]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Enlightening epoch report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Shared epoch, assessed attainment, development and quoted answer checked')


if __name__ == '__main__': main()
