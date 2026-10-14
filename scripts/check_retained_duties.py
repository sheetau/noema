"""Check duty retention, candidate applicability and same-case fulfillment separately."""
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
from scripts.compose_retained_duties import ROOT, PARENT, BUILDERS, BASE, POINT, CASES, PERMISSION, DESCRIPTION, RULE, MEANINGS

REPORT = ROOT / 'reports/retained-duties-v1.json'
DOMAIN = ('person', 'otherperson', 'office', 'scholar', 'issuer', 'authority', 'dutya', 'dutyb', 'speechact', 'entrya', 'entryb')
SCENES = ('anchor', 'speech', 'quiet', 'other')
EXTRA = '''r jxperson[] a.r jxoffice[] a.r jxanchor[] d.r jxpoint[] d.r jxitems[a] c.r jxissuers[a] a.r jxactions[a] a.r jxsigns[a] c.
r jxchoice[a ''' + DESCRIPTION + ' ' + DESCRIPTION + '] ' + DESCRIPTION + '.r jxrequired' + RULE[1:] + '''.
r jxfirst[a a] e.r jxsecond[a a] e.r jxalias[a a] e.r jxtrigger[] e.r jxcases[d] c.
r jxauthority[] a.r jxpublicrole[] a.r jxpublicact[] a.r jxpublic[a a] e.'''


def select(data, indices):
    result = dict(data); result['document'] = deepcopy(data['document'])
    result['document']['statements'] = [result['document']['statements'][i] for i in indices]
    return result


def setup(text, source=False):
    base = parse(text); base['statements'] = []; base = parse(format_graph(base, 'compact') + EXTRA)
    refs = {n: 'p jx' + n for n in ('items', 'issuers', 'actions', 'signs', 'cases')}
    refs.update({n: 'k jx' + n + '[]' for n in ('person', 'office', 'anchor', 'point', 'authority', 'publicrole', 'publicact')})
    refs.update(descriptions='i[item a][k jxchoice[v item r[p jxfirst] r[p jxsecond]]]', required='p h7a' if source else 'p jxrequired',
        trigger='c[p jxpublic][k jxperson[] k jxpublicact[]]' if source else 'k jxtrigger[]', publicdescription='r[p jxpublic]')
    queries = [k(name, *(refs[n] for n, _ in fields)) for name, fields in (('rp3', BASE), ('rp4', POINT), ('rp5', CASES), ('rp6', CASES), ('rp7', POINT), ('rpa', CASES))]
    removed = 0
    if source:
        spec = specialize_definition(base, 'hzgu', 'jxpermission', {len(PERMISSION) - 1: description(base, 'p jxpublic')})
        base = spec.document; removed = spec.disquotations_removed
        permission = k('rdm', refs['authority'], refs['person'], refs['publicrole'], refs['publicact'], 'r[p jxpublic]', 'e[n p a b][n p a b]', refs['anchor'], 'p h7a', 'p h7b')
        retained = k('jxpermission', *(refs[n] for n, _ in PERMISSION if n != 'publicdescription'))
        queries += [permission, retained, 'e[r[' + retained + ']][r[' + retained + ']]']
    else: queries += ['e[r[' + queries[2] + ']][r[' + queries[2] + ']]']
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=source, refs=refs, disquotations_removed=removed,
        first_syntax=syntax(description(base, 'p jxfirst')), second_syntax=syntax(description(base, 'p jxsecond')),
        alias_syntax=syntax(description(base, 'p jxalias')), public_syntax=syntax(description(base, 'p jxpublic')))


def model_for(data, bits=(True, True, True, True, True, False), variant='baseline', permitted=True):
    initiala, initialb, retaineda, retainedb, performeda, performedb = bits
    def action(item): return 'dutya' if item == 'entrya' or variant == 'conflicting' else 'dutyb'
    def trigger(point): return point == 'speech' and variant != 'no_instance'
    def normative(source, person, role, act, desc, sign, point):
        if point == 'anchor' and variant == 'public_prohibited' and (source, person, role, act) == ('authority', 'person', 'scholar', 'speechact') and desc.syntax == data['public_syntax'] and not sign: return True
        if point == 'speech':
            who = 'otherperson' if variant == 'other_person' else 'person'
            office = 'scholar' if variant == 'other_office' else 'office'
            issuer = 'authority' if variant == 'other_issuer' else 'issuer'
        else: who, office, issuer = 'person', 'office', 'issuer'
        if (source, person, role) != (issuer, who, office): return False
        for index, item in enumerate(('entrya', 'entryb')):
            expected = data['first_syntax'] if index == 0 or variant == 'conflicting' else data['second_syntax']
            if point == 'speech' and variant == 'other_description': expected = data['alias_syntax']
            polarity = index == 0
            if point == 'speech' and variant == 'flipped_sign': polarity = not polarity
            enabled = (initiala, initialb)[index] if point == 'anchor' else (retaineda, retainedb)[index]
            if point in ('anchor', 'speech', 'quiet') and enabled and act == action(item) and desc.syntax == expected and sign == polarity: return True
        return False
    def first(person, act):
        return Content(SCENES, tuple((person, act) == ('person', 'dutya') and performeda and (point == 'quiet' if variant == 'split_fulfillment' else point == 'speech') for point in SCENES))
    def second(person, act):
        return Content(SCENES, tuple((person, act, point) == ('person', 'dutyb', 'speech') and performedb for point in SCENES))
    model = guarded(data['document'])
    model.update(jxperson=lambda: 'person', jxoffice=lambda: 'office', jxanchor=lambda: 'anchor', jxpoint=lambda: 'speech',
        jxitems=lambda item: variant != 'empty_items' and item in ('entrya', 'entryb'), jxissuers=lambda item: 'issuer', jxactions=action,
        jxsigns=lambda item: item == 'entrya', jxchoice=lambda item, first, second: first if item == 'entrya' or variant == 'conflicting' else second,
        jxrequired=normative, jxfirst=first, jxalias=first, jxsecond=second,
        jxtrigger=lambda: Content(SCENES, tuple(trigger(point) for point in SCENES)), jxcases=lambda point: variant != 'empty_cases' and point in ('speech', 'quiet'),
        jxauthority=lambda: 'authority', jxpublicrole=lambda: 'scholar', jxpublicact=lambda: 'speechact',
        jxpublic=lambda person, act: Content(SCENES, tuple((person, act) == ('person', 'speechact') and trigger(point) for point in SCENES)))
    if data['source']:
        model.update(h7a=normative, h7b=lambda source, person, role, act, desc, sign, point: permitted and (source, person, role, act, sign, point) == ('authority', 'person', 'scholar', 'speechact', True, 'anchor') and desc.syntax == data['public_syntax'])
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model, individuals=DOMAIN, situations=SCENES, max_steps=30_000_000)]


def checks(texts):
    data = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=6):
        initial = all(bits[:2]); retained = initial and all(bits[2:4]); fulfilled = retained and bits[4] and not bits[5]
        expected = [initial, retained, retained, retained, fulfilled, fulfilled, True]
        result = values(data, model_for(data, bits))
        if result != expected: raise ValueError('Signed retention grid differs: ' + repr((bits, result, expected)))
        grid.append(dict(bits=list(bits), result=result))
    print('64 initial/retained/signed-performance profiles passed', flush=True); rows = []
    for text in texts[1:]:
        data = setup(text, True); profiles = []; cases = {}
        for permitted, keepa, keepb, performs in product((False, True), repeat=4):
            retained = keepa and keepb; fulfilled = retained and performs
            expected = [True, retained, retained, retained, fulfilled, fulfilled, permitted, permitted and retained, True]
            result = values(data, model_for(data, (True, True, keepa, keepb, performs, False), permitted=permitted))
            if result != expected: raise ValueError('Source permission/retention grid differs: ' + repr((permitted, keepa, keepb, performs, result)))
            profiles.append(dict(bits=[permitted, keepa, keepb, performs], result=result))
        for variant, expected in (
            ('empty_items', [False] * 6 + [True, False, True]),
            ('empty_cases', [True, True, False, False, True, False, True, False, True]),
            ('no_instance', [True, True, True, False, True, False, True, True, True]),
            ('split_fulfillment', [True, True, True, True, False, False, True, True, True]),
            ('conflicting', [True, True, True, True, False, False, True, True, True]),
            ('public_prohibited', [True, True, True, True, True, True, False, False, True]),
            *[(name, [True, False, False, False, False, False, True, False, True]) for name in ('other_person', 'other_office', 'other_issuer', 'other_description', 'flipped_sign')]):
            result = values(data, model_for(data, variant=variant))
            if result != expected: raise ValueError('Duty retention contrast differs: ' + repr((variant, result, expected)))
            cases[variant] = result
        rows.append(dict(profiles=profiles, cases=cases, disquotations_removed=data['disquotations_removed'])); print('Source retained duty contrasts passed', flush=True)
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Retained-duty artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Retained-duty roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']: raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = 'unbeschadet ihrer Amtspflicht'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_retained_duties.py', 'scripts/check_retained_duties.py', 'scripts/compose_described_norms.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/grammar.py', 'noema/meaning_basis.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_retained_office_requirements_and_joint_candidate_fulfillment', documents=documents, sizes=sizes, interpretation=checks(texts), parent_preserved=True, roundtrips=True,
        new_definitions=10, new_primitives=0, new_author_statements=0, alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args(); result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Retained-duty record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print('Permission, non-waiver, applicability and joint fulfillment remain distinct')


if __name__ == '__main__': main()
