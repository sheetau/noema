"""Check solemn appeals, shared action witnesses and unexecuted conditionals."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_mutual_undertakings as mutual
from scripts import check_purposive_undertakings as purpose
from scripts.compose_limits import call as k, app, op
from scripts.compose_solemn_undertakings import ROOT, PARENT, BUILDERS, ACTION, GROUP, PURPOSE, SOURCE, SOURCE_PURPOSE, INVOKES

REPORT = ROOT / 'reports/solemn-undertakings-v1.json'
EXTRA = mutual.EXTRA + purpose.PURPOSE_EXTRA + '''
r jeceremony[a a d] c.r jeinvokes[''' + INVOKES[2:-3] + '''] c.
r jetitle[a d] c.r jeeffect[j[a] d] c.
d jeauthority[person a] e[b scene[k jetitle[v person v scene]]].
d jealias[person a] e[b scene[k jetitle[v person v scene]]].
d jeresponse[bindings j[a]] e[b scene[k jeeffect[v bindings v scene]]].
'''
FORMULA = 'k rin[p jq p jeresponse]'
REFS = mutual.REFS | dict(authority='r[p jeauthority]', formula='r[' + FORMULA + ']',
    solemn='p jeceremony', invokes='p jeinvokes', proponents='p jwproponents', goal='r[k jwcontent[]]', aims='p jwaims')


def setup(text, source=False):
    fields = (('hzcv', SOURCE), ('hzcw', SOURCE_PURPOSE)) if source else (('rio', ACTION), ('rip', GROUP), ('riq', PURPOSE))
    return candidate(text, EXTRA + ''.join('q[' + k(name, *(REFS[n] for n, _ in args)) + '].' for name, args in fields))


def model_for(doc, bits=(True,) * 4, variant='baseline', aimed=True, components=(True,) * 3):
    solemn_a, solemn_b, invokes_a, invokes_b = bits
    old_variant = 'alternative_witness' if variant in ('separate_witness', 'matching_alternative') else 'baseline'
    model = mutual.model_for(doc, variant=old_variant, components=components)
    authority = syntax(description(doc, 'p ' + ('jealias' if variant == 'authority_alias' else 'jeauthority')))
    formula = syntax(description(doc, 'k rin[p ' + ('jr' if variant == 'formula_alias' else 'jq') + ' p jeresponse]'))
    goal = syntax(description(doc, 'k ' + ('jwother' if variant == 'goal_alias' else 'jwcontent') + '[]'))
    alpha = ('alpha', 'other', 'second') if variant == 'matching_alternative' else ('alpha', 'acta', 'first')
    records = (alpha, ('beta', 'actb', 'second'))
    def ceremony(person, act, scene):
        first = ('alpha', 'actb', 'first') if variant == 'ceremony_act' else alpha
        return (person, act, scene) == first and solemn_a or (person, act, scene) == records[1] and solemn_b
    def invokes(person, act, title, message, bindings, scene):
        first = ('beta', 'acta', 'first') if variant == 'appeal_person' else ('alpha', 'actb', 'first') if variant == 'appeal_act' else ('alpha', 'acta', 'second') if variant == 'appeal_time' else alpha
        for record, active, args in ((first, invokes_a, ('alpha', 'beta')), (records[1], invokes_b, ('beta', 'alpha'))):
            if variant == 'wrong_bindings': args = tuple(reversed(args))
            if active and (person, act, scene) == record and title.syntax == authority and message.syntax == formula and bindings.items == args: return True
        return False
    aims = lambda person, act, target, scene: aimed and (person, act, scene) == alpha and target.syntax == goal
    model.update(jeceremony=ceremony, jeinvokes=invokes, jwproponents=lambda p, c: p == 'alpha' and c == 'now', jwaims=aims)
    if 'hzu' in model: model['hzu'] = aims
    return model


def evaluate(doc, model): return values(doc, model, mutual.PEOPLE, mutual.SCENES)


def conditional_checks(text):
    conditional = app(k('rim', 'p jq', 'p jeresponse'), 'k jf[]')
    directive = app(k('rin', 'p jq', 'p jeresponse'), 'k jf[]')
    doc = candidate(text, EXTRA + 'q[' + op('t', conditional, 'k je[]') + '].q[' + op('e', directive, 'j s[' + conditional + ']') + '].')
    cases = []
    for target, response in product((False, True), repeat=2):
        model = mutual.model_for(doc); model.update(jp=lambda bindings, scene: target, jeeffect=lambda bindings, scene: response)
        result = evaluate(doc, model)
        if result != [target or response, False]: raise ValueError('Conditional appeal became an assertion or required an actual breach')
        cases.append(dict(target=target, response=response, results=result))
    return cases


def action_checks(texts):
    docs = [setup(t) for t in texts]
    for d in docs: d['statements'] = d['statements'][:1]
    cases = []
    for bits in product((False, True), repeat=5):
        rows = [evaluate(d, model_for(d, bits=(bits[3], True, bits[4], True), components=bits[:3])) for d in docs]
        if rows != [[all(bits)]] * len(docs): raise ValueError('Solemn action omitted a required component')
        cases.append(dict(bits=list(bits), results=rows[0]))
    return cases


def group_checks(texts, source=False):
    docs = [setup(t, source) for t in texts]
    cases = []
    for bits in product((False, True), repeat=4):
        want = [all(bits), all(bits)] if source else [bits[0] and bits[2], all(bits), all(bits)]
        rows = [evaluate(d, model_for(d, bits)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Different parties or acts combined into a solemn undertaking')
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant in ('authority_alias', 'formula_alias', 'wrong_bindings', 'ceremony_act', 'appeal_person', 'appeal_act', 'appeal_time', 'separate_witness', 'matching_alternative', 'goal_alias'):
        want = [False, True, True] if variant == 'matching_alternative' else [True, True, False] if variant == 'goal_alias' else [False, False, False]
        if source: want = want[1:]
        rows = [evaluate(d, model_for(d, variant=variant)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Solemn contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    for d in docs:
        # jetitle, jp, jeeffect and jwtruth remain unknown, as do all norm relations.
        if evaluate(d, model_for(d)) != ([True, True] if source else [True, True, True]): raise ValueError('Appeal executed a represented authority or effect')
        for name in ('jeceremony', 'jeinvokes'):
            model = model_for(d); model[name] = guarded(d)[name]
            try: evaluate(d, model)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown appeal was invented')
        for notation in ('compact', 'full'):
            form = format_graph(d, notation)
            if parse(form) != d or parse(decode(encode(form, 'v2'))) != d: raise ValueError('Closed appeal roundtrip changed')
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True, underlying_truth_not_executed=True,
        unknown_appeal_refused=True, closed_roundtrips=True)


def purpose_checks(texts):
    docs = [setup(t, True) for t in texts]; cases = []
    for aimed, first, second in product((False, True), repeat=3):
        want = [first and second, first and second and aimed]
        rows = [evaluate(d, model_for(d, (first, second, first, second), aimed=aimed)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Purpose was added to all parties or solemnity inferred it')
        cases.append(dict(aimed=aimed, first=first, second=second, results=want))
    return cases


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored solemn undertaking differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Solemn undertaking roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrase = 'eidlich'
    if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source range')
    start = unit['text'].index(phrase)
    segment = dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=['rim', 'rin', 'rio', 'rip', 'riq', 'hzcv', 'hzcw'])
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_solemn_undertakings.py', 'scripts/check_solemn_undertakings.py', 'scripts/check_mutual_undertakings.py',
        'scripts/check_purposive_undertakings.py', 'scripts/check_assessed_payments.py', 'scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_solemn_undertaking_interpretation', documents=documents, sizes=sizes,
        conditionals=conditional_checks(texts[0]), actions=action_checks([texts[0], texts[2]]),
        generic=group_checks([texts[0], texts[2]]), source=group_checks(texts[1:], True), purposes=purpose_checks(texts[1:]),
        alignment=dict(segments=[segment], semantic_completion=False), new_definitions=7, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        interpretive_references=['https://www.korpora.org/Kant/aa08/038.html', 'https://korpora.org/Kant/aa06/303.html', 'https://www.korpora.org/Kant/aa06/305.html'],
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Solemn undertaking report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Solemn appeals share actors, acts, bindings and purposes without executing authority or response')


if __name__ == '__main__': main()
