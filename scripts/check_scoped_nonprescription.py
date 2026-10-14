"""Test scoped freedom, institutional headship and non-factive self-duty judgments."""
import argparse
import hashlib
from itertools import product
import json

from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_personal_criteria import APPRAISAL
from scripts.compose_scoped_nonprescription import ROOT, PARENT, BUILDERS, HEAD, FRAME, FIELD, CONFIG, DUTY, SOURCE_FIELD, SOURCE_CONFIG, SOURCE_DUTY, MEANINGS

REPORT = ROOT / 'reports/scoped-nonprescription-v1.json'
DOMAIN = ('leader', 'coholder', 'crown', 'suboffice', 'organization', 'alice', 'bob', 'faith', 'commerce', 'act', 'otheract', 'judge', 'assessor', 'external')
SCENES = ('now', 'belief', 'elsewhere')
EXTRA = '''r jtsource[] a.r jtperson[] a.r jtoffice[] a.r jtorganization[] a.r jtcontext[] d.r jttopic[] a.r jtanchor[] d.r jtassessor[] a.r jtjudgment[] a.
r jtmembers[a a d] c.r jtholders[a a a d] c.r jtabove[a a a d] c.r jtpeople[a] c.r jtroles[a] a.
r jtactivities[a a a d] c.r jtassessed[a a d] c.r jteligible[a] c.r jtexecution[a a] e.
r jtinnerrequired[a a a a i[h[a a] e] c d] c.r jtinnerallowed[a a a a i[h[a a] e] c d] c.
r jtouterrequired[a a a i[h[j[a]] e] j[a] c d] c.r jtouterallowed[a a a i[h[j[a]] e] j[a] c d] c.
r jtjudgments[a a d] c.r jtmatters[a a d] c.r jtlinked[a i[h[j[a]] e] j[a] d] c.r jtcandidates[a d d] c.'''
REFS = {n: 'k jt' + n + '[]' for n in ('source', 'person', 'office', 'organization', 'context', 'topic', 'anchor', 'assessor', 'judgment')}
REFS.update({n: 'p jt' + n for n in ('members', 'holders', 'above', 'people', 'roles', 'activities', 'assessed', 'eligible', 'judgments', 'matters', 'linked', 'candidates')})


def setup(text, source=False, execution='p jtexecution'):
    base = candidate(text, EXTRA)
    refs = {**REFS, 'descriptions': 'i[person a activity a][r[' + execution + ']]',
        'eligible': 'p aa' if source else 'p jteligible',
        'required': 'p h7a' if source else 'p jtinnerrequired', 'allowed': 'p h7b' if source else 'p jtinnerallowed'}
    policy = k('hzfp' if source else 'rm6', *(refs[n] for n, _ in (SOURCE_CONFIG if source else CONFIG)))
    duty_refs = {**refs, 'policy': 'r[' + policy + ']',
        'required': 'p h7k' if source else 'p jtouterrequired', 'allowed': 'p h7l' if source else 'p jtouterallowed'}
    duty = k('hzfq' if source else 'rm7', *(duty_refs[n] for n, _ in (SOURCE_DUTY if source else DUTY)))
    bindings = 'l[a][' + refs['person'] + ']'
    judgment_refs = {**refs, 'criterion': 'r[' + duty + ']', 'subject': refs['person'], 'bindings': bindings,
        'judgments': 'p fa' if source else refs['judgments'], 'matters': 'p fb' if source else refs['matters']}
    queries = [k('hzfn' if source else 'rm2', *(refs[n] for n, _ in HEAD)), k('rm3', *(refs[n] for n, _ in FRAME)),
        k('rm4', *(refs[n] for n, _ in FIELD)), k('hzfo' if source else 'rm5', *(refs[n] for n, _ in (SOURCE_FIELD if source else FIELD))),
        't[c[' + duty + '][' + bindings + ']][' + refs['context'] + ']',
        k('rlg', *(judgment_refs[n] for n, _ in APPRAISAL)),
        't[c[' + policy + '][' + bindings + ']][' + refs['context'] + ']']
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=source, refs=refs, execution=execution, policy=policy, duty=duty,
        execution_syntax=syntax(description(base, execution)), policy_syntax=syntax(description(base, policy)),
        duty_syntax=syntax(description(base, duty)))


def model_for(data, bits=(False, False, True, True, False, True), variant='baseline'):
    require, prohibit, allow, abstain, actual_duty, believed_duty = bits
    model = guarded(data['document'])
    def target(source, person, role, act, desc, point):
        return source == 'leader' and person in ('alice', 'bob') and role == 'suboffice' and act == 'act' and desc.syntax == data['execution_syntax']
    def required(source, person, role, act, desc, sign, point):
        return target(source, person, role, act, desc, point) and (require if sign else prohibit)
    def allowed(source, person, role, act, desc, sign, point):
        return target(source, person, role, act, desc, point) and (allow if sign else abstain)
    def outer(source, person, role, desc, bindings, sign, point):
        correct = (source, person, role) == ('assessor', 'leader', 'crown') and desc.syntax == data['policy_syntax'] and bindings.items == ('leader',) and sign
        return correct and (believed_duty if point == 'belief' else actual_duty)
    model.update(jtsource=lambda: 'leader', jtperson=lambda: 'leader', jtoffice=lambda: 'crown', jtorganization=lambda: 'organization',
        jtcontext=lambda: 'now', jttopic=lambda: 'faith', jtanchor=lambda: 'now', jtassessor=lambda: 'assessor', jtjudgment=lambda: 'judge',
        jtmembers=lambda role, org, point: role in ('crown', 'suboffice') and org == 'organization',
        jtholders=lambda person, role, org, point: (role, org) == ('crown', 'organization') and (person == 'leader' or variant == 'coholder' and person == 'coholder'),
        jtabove=lambda high, low, org, point: org == 'organization' and (high, low) == ('crown', 'suboffice') and variant != 'incomparable',
        jtpeople=lambda person: person in ('alice', 'bob') and variant != 'empty_people', jtroles=lambda person: 'suboffice',
        jtactivities=lambda person, act, topic, anchor: person in ('alice', 'bob') and act == 'act' and (topic, anchor) == ('faith', 'now') and variant != 'empty_activities',
        jtassessed=lambda person, act, point: not (variant == 'unassessed' and person == 'bob'),
        jteligible=lambda person: person in ('leader', 'alice', 'bob'),
        jtinnerrequired=required, jtinnerallowed=allowed, jtouterrequired=outer, jtouterallowed=lambda *args: False,
        jtjudgments=lambda person, judge, point: (person, judge, point) == ('leader', 'judge', 'now'),
        jtmatters=lambda judge, subject, point: (judge, subject, point) == ('judge', 'leader', 'now'),
        jtlinked=lambda judge, criterion, bindings, point: (judge, point) == ('judge', 'now') and criterion.syntax == data['duty_syntax'] and bindings.items == (('coholder',) if variant == 'wrong_subject' else ('leader',)),
        jtcandidates=lambda judge, context, point: (judge, context, point) == ('judge', 'now', 'belief') and variant != 'empty_candidates')
    if data['source']:
        model.update(aa=model['jteligible'], cf=lambda person, role, point: (person, role) == ('leader', 'crown') and variant != 'unentrusted',
            h7a=required, h7b=allowed, h7k=outer, h7l=model['jtouterallowed'], fa=model['jtjudgments'], fb=model['jtmatters'])
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model, individuals=DOMAIN,
        situations=SCENES, max_steps=8_000_000)]


def checks(texts):
    generic = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=6):
        require, prohibit, allow, abstain, actual_duty, believed_duty = bits
        unprescribed = not require and not prohibit; free = unprescribed and allow and abstain
        expected = [True, True, unprescribed, free, actual_duty, believed_duty, free]
        actual = values(generic, model_for(generic, bits))
        if actual != expected: raise ValueError('Non-prescription/duty conflation: ' + repr((bits, actual)))
        grid.append(dict(bits=list(bits), result=actual))
    print('64 norm and self-duty profiles passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = setup(text, True); cases = {}
        for variant, expected in (
            ('baseline', [True, True, True, True, False, True, True]),
            ('coholder', [False, True, True, True, False, True, True]),
            ('incomparable', [False, True, True, True, False, True, True]),
            ('unentrusted', [False, True, True, True, False, True, True]),
            ('empty_people', [True, False, False, False, False, True, False]),
            ('empty_activities', [True, False, False, False, False, True, False]),
            ('unassessed', [True, False, False, False, False, True, False]),
            ('empty_candidates', [True, True, True, True, False, False, True]),
            ('wrong_subject', [True, True, True, True, False, False, True])):
            actual = values(data, model_for(data, variant=variant))
            if actual != expected: raise ValueError('Scoped duty source contrast failed: ' + repr((variant, actual)))
            cases[variant] = actual
        rows.append(cases); print('Scoped self-duty source contrasts passed', flush=True)
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Scoped non-prescription artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Non-prescription roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    segments = []
    for phrase in ('Ein Fürst', 'daß er es für Pflicht halte, in Religionsdingen den Menschen nichts vorzuschreiben, sondern ihnen darin volle Freiheit zu lassen'):
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
            range=[start, start + len(phrase)], text=phrase, definitions=['rm2', 'hzfn'] if phrase == 'Ein Fürst' else
                ['rm3', 'rm4', 'rm5', 'rm6', 'rm7', 'hzfo', 'hzfp', 'hzfq', 'rlg']))
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_scoped_nonprescription.py', 'scripts/check_scoped_nonprescription.py', 'scripts/compose_personal_criteria.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_described_appraisals.py',
        'scripts/check_rod_setup.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_scoped_nonprescription_and_self_attributed_duty', documents=documents, sizes=sizes,
        interpretation=checks(texts), parent_preserved=True, roundtrips=True, new_definitions=10, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=segments), verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Scoped non-prescription report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Scoped non-prescription, positive freedom and self-duty judgments checked')


if __name__ == '__main__': main()
