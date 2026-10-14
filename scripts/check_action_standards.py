"""Check nested appraisals of a self-report independently of action and truth."""
import argparse
import hashlib
from itertools import product
import json
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts import check_self_reports as prior
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_self_reports import BELIEF, SOURCE_BELIEF
from scripts.compose_action_standards import ROOT, PARENT, BUILDERS, STANDARD, MEANINGS

REPORT = ROOT / 'reports/action-standards-v1.json'
DOMAIN = (*prior.DOMAIN, 'assessment')
SCENES = prior.prior.SCENES
EXTRA = """r jvfirst[a i[h[a a] e] d] c.r jvsecond[a i[h[a a] e] d] c.
r jvlinked[a i[h[j[a]] e] j[a] d] c.r jvcandidates[a d d] c."""


def setup(text, source=False, standards=None):
    old = prior.setup(text, source); base = old['document']
    old_queries, base['statements'] = base['statements'], []
    base = parse(format_graph(base, 'compact') + EXTRA)
    action = 'r[' + old['action'] + ']'
    rules = ['i[person a action i[h[a a] e]][b point[' + k(n, 'v person', 'v action', 'v point') + ']]' for n in ('jvfirst', 'jvsecond')]
    standards = 'l[' + STANDARD + '][' + ' '.join(rules) + ']' if standards is None else standards
    criterion = k('rng', action, standards)
    refs = {**old['old']['refs'], 'criterion': 'r[' + criterion + ']', 'linked': 'p jvlinked', 'candidates': 'p jvcandidates',
        'judgments': 'p fa' if source else 'p jtjudgments', 'matters': 'p fb' if source else 'p jtmatters'}
    belief = k('hzfr' if source else 'rna', *(refs[n] for n, _ in (SOURCE_BELIEF if source else BELIEF)))
    person, context = refs['person'], refs['context']
    queries = ['t[' + k(n, person, action, standards) + '][' + context + ']' for n in ('rne', 'rnf')]
    queries.append('t[c[' + belief + '][' + person + ']][' + context + ']')
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    doc['statements'] = old_queries + doc['statements']
    return dict(document=doc, old=old, source=source, action=action, standards=standards, criterion=criterion,
        action_syntax=syntax(description(base, old['action'])), criterion_syntax=syntax(description(base, criterion)))


def model_for(data, bits=(False, True, False, False, False, False), variant='baseline'):
    actual, judged, delivered, inner, duty, policy = bits
    model = prior.model_for(data['old'], (delivered, delivered, delivered, inner, duty, policy))
    model.update({n: f for n, f in guarded(data['document']).items() if n not in model})
    jname, mname = ('fa', 'fb') if data['source'] else ('jtjudgments', 'jtmatters')
    oldj, oldm = model[jname], model[mname]
    model[jname] = lambda person, judgment, point: oldj(person, judgment, point) or (
        variant != 'no_outer_judgment' and (person, judgment, point) == ('leader', 'assessment', 'now'))
    model[mname] = lambda judgment, subject, point: oldm(judgment, subject, point) or (
        (judgment, subject, point) == ('assessment', 'coholder' if variant == 'wrong_subject' else 'leader', 'now'))
    model['jvlinked'] = lambda judgment, desc, bindings, point: variant != 'wrong_link' and (
        judgment, bindings.items, point) == ('assessment', ('leader',), 'now') and desc.syntax == data['criterion_syntax']
    model['jvcandidates'] = lambda judgment, context, point: variant != 'empty_candidates' and (
        judgment, context, point) == ('assessment', 'now', 'elsewhere' if variant == 'other_candidate' else 'belief')
    def applicable(person, desc):
        return person == ('coholder' if variant == 'wrong_person' else 'leader') and desc.syntax == data['action_syntax'] and variant != 'wrong_action'
    model['jvfirst'] = lambda person, desc, point: applicable(person, desc) and (judged if point == 'belief' else actual)
    model['jvsecond'] = lambda person, desc, point: applicable(person, desc)
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model, individuals=DOMAIN,
        situations=SCENES, max_steps=24_000_000)]


def checks(texts):
    data = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=6):
        actual, judged, delivered, inner, duty, policy = bits
        expected = [delivered, inner, duty, policy, delivered, False, not actual, actual, judged]
        result = values(data, model_for(data, bits))
        if result != expected: raise ValueError('Nested appraisal conflated: ' + repr((bits, result)))
        grid.append(dict(bits=list(bits), result=result))
    print('64 action-appraisal/report/judgment/duty/policy profiles passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = setup(text, True); cases = {}
        for variant in ('baseline', 'wrong_subject', 'wrong_link', 'empty_candidates', 'other_candidate', 'no_outer_judgment', 'wrong_person', 'wrong_action'):
            result = values(data, model_for(data, variant=variant))
            expected = [False] * 6 + [True, False, variant == 'baseline']
            if result != expected: raise ValueError('Source appraisal contrast failed: ' + repr((variant, result)))
            cases[variant] = result
        rows.append(cases); print('Source action-appraisal contrasts passed', flush=True)
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Action-standard artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Action-standard roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = unit['text'][unit['text'].index('der es seiner'):unit['text'].index(', der also')]; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_action_standards.py', 'scripts/check_action_standards.py', 'scripts/check_self_reports.py',
        'scripts/check_scoped_nonprescription.py', 'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py',
        'scripts/check_rod_setup.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'noema/specialization.py', 'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_appraisal_of_a_described_self_report', documents=documents, sizes=sizes,
        interpretation=checks(texts), parent_preserved=True, roundtrips=True, new_definitions=3, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Action-standard record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Described-action appraisal remains independent of execution and inner truth')


if __name__ == '__main__': main()
