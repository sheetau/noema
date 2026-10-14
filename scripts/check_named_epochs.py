"""Verify referent identity without turning epoch labels into universal truths."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_opening_opportunities as opening
from scripts.compose_limits import call as k, both
from scripts.compose_named_epochs import ROOT, PARENT, BUILDERS, EPONYM, LABELS, REFERENCED, ASPECT, SOURCE_EPONYM, MEANINGS

REPORT = ROOT / 'reports/named-epochs-v1.json'
DOMAIN = ('epoch', 'other', 'ruler', 'pretender', 'crown', 'author', 'node')
SCENES = ('before', 'now', 'after')
EXTRA = '''r jssubject[] a.r jsperson[] a.r jsoffice[] a.r jsnode[] a.r jsauthor[] a.r jscontext[] d.
r jsscope[a] c.r jspeople[a] c.r jsreferent[a] e.r jsaspect[a] e.
r jshistory[d] c.r jsbefore[d d] c.r jsperiods[a d] c.r jseligible[a] c.
r jstenures[a a b b d] c.r jsholds[a a d] c.r jspresents[a a i[h[a] e] i[h[a] e] d] c.'''
REFS = {n: 'k js' + n + '[]' for n in ('subject', 'person', 'office', 'node', 'author', 'context')}
REFS.update({n: 'p js' + n for n in ('scope', 'people', 'history', 'before', 'periods', 'eligible', 'tenures', 'holds', 'presents')})
SOURCE_DOMAIN = (*opening.SOURCE_DOMAIN, 'crown', 'pretender')


def finish(base, refs, aspect, label, source=False, **extra):
    referent = 'p jsreferent'
    labels = {**refs, 'referent': 'r[' + referent + ']', 'aspect': 'r[' + aspect + ']', 'label': 'r[' + label + ']'}
    if source:
        # Person identification uses the explicit person catalogue, not epochs.
        identity = k('hzfm', refs['person'], refs['people'], refs['context'], refs['office'], refs['tenures'])
    else:
        identity = k('rmv', refs['person'], refs['people'], k('rmu', refs['office'],
            'n p ' + number_word(1740) + ' b', 'n p ' + number_word(1786) + ' b', refs['eligible'], refs['tenures']), refs['context'])
    attributed = k('rmx', *(labels[n] for n, _ in LABELS))
    referenced = k('rmy', *(labels[n] for n, _ in REFERENCED))
    factive = k('rmz', *(labels[n] for n, _ in REFERENCED))
    truth = 't[c[' + label + '][' + refs['subject'] + ']][' + refs['context'] + ']'
    aspect_truth = 't[c[' + aspect + '][' + refs['subject'] + ']][' + refs['context'] + ']'
    queries = [identity, attributed, referenced, factive, truth, aspect_truth, both(identity, factive, truth)]
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    descriptions = {name: syntax(description(base, expr)) for name, expr in (('referent', referent), ('aspect', aspect), ('label', label))}
    return dict(document=doc, source=source, descriptions=descriptions, refs=refs, labels=labels, **extra)


def setup(text):
    base = candidate(text, EXTRA)
    return finish(base, REFS, 'p jsaspect', k('rmw', *(REFS[n] for n, _ in EPONYM)))


def generic_model(data, bits=(True, True, True, True), variant='baseline'):
    aspect, reign, recorded, named = bits; desc = data['descriptions']; model = guarded(data['document'])
    def tenure(person, office, first, last, point):
        return recorded and office == 'crown' and (first, last) == (1740, 1786) and (person == 'ruler' or variant == 'ambiguous' and person == 'pretender')
    def presents(node, author, referent, label, point):
        return named and (node, author, point) == ('node', 'author', 'now') and referent.syntax == desc['referent'] and label.syntax in (
            (desc['aspect'],) if variant == 'wrong_label' else (desc['aspect'], desc['label']))
    model.update(jssubject=lambda: 'epoch', jsperson=lambda: 'ruler', jsoffice=lambda: 'crown', jsnode=lambda: 'node',
        jsauthor=lambda: 'author', jscontext=lambda: 'now', jsscope=lambda item: item in ('epoch', 'other'),
        jspeople=lambda person: person in ('ruler', 'pretender') and variant != 'empty_people',
        jsreferent=lambda item: Content(SCENES, (item == 'epoch',) * 3),
        jsaspect=lambda item: Content(SCENES, (aspect and item == 'epoch',) * 3),
        jshistory=lambda point: point in SCENES, jsbefore=lambda a, b: SCENES.index(a) < SCENES.index(b),
        jsperiods=lambda item, point: item == 'epoch' and point == 'now', jseligible=lambda person: person in ('ruler', 'pretender'),
        jstenures=tenure, jsholds=lambda person, office, point: reign and (person, office, point) == ('ruler', 'crown', 'now'),
        jspresents=presents)
    return model


def source_setup(text):
    old = opening.source_setup(text); base = old['document']; base['statements'] = []
    base = parse(format_graph(base, 'compact') + EXTRA)
    epoch_refs = old['old']['refs']
    refs = {**REFS, 'history': epoch_refs['history'], 'before': epoch_refs['before'], 'periods': epoch_refs['periods'],
        'context': epoch_refs['context']}
    aspect_refs = {**epoch_refs, 'progress': old['target']}
    aspect = k('hzfj', *(aspect_refs[n] for n, _ in ASPECT))
    label = k('hzfk', *(refs[n] for n, _ in SOURCE_EPONYM))
    return finish(base, refs, aspect, label, True, old=old)


def source_model(data, variant='baseline'):
    model = opening.source_model(data['old'], 'no_decline' if variant == 'no_progress' else 'baseline')
    model.update({n: f for n, f in guarded(data['document']).items() if n not in model})
    desc = data['descriptions']; eligible = model['aa']
    model.update(jssubject=lambda: 'epoch', jsperson=lambda: 'guide', jsoffice=lambda: 'crown',
        jsnode=lambda: 'answernode', jsauthor=lambda: 'author',
        jsscope=lambda item: item == 'epoch', jspeople=lambda person: person in ('guide', 'pretender'),
        jsreferent=lambda item: Content(opening.epoch.indications.SOURCE_SCENES,
            (item == 'epoch',) * len(opening.epoch.indications.SOURCE_SCENES)),
        aa=lambda person: eligible(person) or person in ('guide', 'pretender'),
        jstenures=lambda person, office, first, last, point: office == 'crown' and (first, last) == ((1741, 1786) if variant == 'wrong_year' else (1740, 1786)) and (
            person == 'guide' or variant == 'ambiguous' and person == 'pretender'),
        jsholds=lambda person, office, point: (person, office) == ('guide', 'crown') and point == ('work' if variant == 'no_overlap' else 'last'),
        jspresents=lambda node, author, referent, label, point: (node, author, point) == ('answernode', 'author', 'last') and
            referent.syntax == desc['referent'] and label.syntax in ((desc['aspect'],) if variant == 'wrong_label' else (desc['aspect'], desc['label'])))
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model,
        individuals=SOURCE_DOMAIN if data['source'] else DOMAIN,
        situations=opening.epoch.indications.SOURCE_SCENES if data['source'] else SCENES, max_steps=48_000_000)]


def checks(texts):
    generic = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=4):
        aspect, reign, recorded, named = bits
        expected = [recorded, named, named, named and aspect, reign, aspect, recorded and named and aspect and reign]
        actual = values(generic, generic_model(generic, bits))
        if actual != expected: raise ValueError('Epoch label conflation: ' + repr((bits, actual)))
        grid.append(dict(bits=list(bits), result=actual))
    print('16 naming/reference/property profiles passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = source_setup(text); cases = {}
        for variant, expected in (
            ('baseline', [True] * 7), ('ambiguous', [False, True, True, True, True, True, False]),
            ('wrong_year', [False, True, True, True, True, True, False]),
            ('no_overlap', [True, True, True, True, False, True, False]),
            ('no_progress', [True, True, True, False, True, False, False]),
            ('wrong_label', [True, False, False, False, True, True, False])):
            actual = values(data, source_model(data, variant))
            if actual != expected: raise ValueError('Named epoch source connection failed: ' + repr((variant, actual)))
            cases[variant] = actual; print('Named epoch:', variant, 'passed', flush=True)
        rows.append(cases)
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Named epoch artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Named epoch roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0014')
    phrase = 'In diesem Betracht ist dieses Zeitalter das Zeitalter der Aufklärung, oder das Jahrhundert Friederichs.'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_named_epochs.py', 'scripts/check_named_epochs.py', 'scripts/check_opening_opportunities.py',
        'scripts/check_enlightening_epoch.py', 'scripts/check_clear_indications.py', 'scripts/check_declining_hindrances.py',
        'scripts/check_free_pursuit.py', 'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py',
        'scripts/check_scoped_counts.py', 'scripts/check_described_appraisals.py', 'scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json'}
    reference = dict(url='https://www.dhm.de/archiv/sammlungen/kunstgewerbe/89_1157.html', accessed='2026-10-14',
        catalogue_excerpt='Statuette des Königs Friedrichs II. von Preußen (geb. 1712, reg. 1740-1786)',
        first_year=1740, last_year=1786, institution='Prussian kingship',
        status='editorial_reference_profile; contextual_candidate_for_Kants_person_not_a_proof_of_reference_or_language_completion')
    return dict(status='partial_scoped_epoch_classification_and_personal_label', documents=documents, sizes=sizes,
        interpretation=checks(texts), parent_preserved=True, roundtrips=True, new_definitions=10, new_primitives=0, new_author_statements=0,
        reference_evidence=reference,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Named epoch report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Scoped epoch classification, personal reference and label attribution checked')


if __name__ == '__main__': main()
