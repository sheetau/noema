"""Check nonrestriction, complete requirement coverage, and all-other-person permission."""
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
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_unrestricted_others import ROOT, PARENT, BUILDERS, BASE, POINT, CASES, SOURCE_CASES, SOURCE_POPULATION, DESCRIPTION, RULE, MEANINGS

REPORT = ROOT / 'reports/unrestricted-others-v1.json'
DOMAIN = ('person', 'other', 'earlier', 'issuer', 'office', 'otheroffice', 'dutya', 'dutyb', 'speecha', 'speechb', 'entrya', 'entryb', 'authority', 'scholar')
SCENES = ('anchor', 'left', 'right')
EXTRA = '''r juperson[] a.r juanchor[] d.r jupoint[] d.r juofficeroles[a] c.r juitems[a] c.r juissuers[a] a.r juoffices[a] a.r juactions[a] a.r jusigns[a] c.
r juchoice[a ''' + DESCRIPTION + ' ' + DESCRIPTION + '] ' + DESCRIPTION + '.r jurequired' + RULE[1:] + '''.
r jufirst[a a] e.r jusecond[a a] e.r jualias[a a] e.r jutarget[a a] e.r jucases[d] c.
r jupopulation[a] c.r juexcluded[a] c.r juactivities[a a] c.r juauthority[] a.r juroles[a] a.r juspeech[] a.'''


def select(data, indices):
    result = dict(data); result['document'] = deepcopy(data['document'])
    result['document']['statements'] = [result['document']['statements'][i] for i in indices]
    return result


def setup(text, source=False):
    base = parse(text); base['statements'] = []; base = parse(format_graph(base, 'compact') + EXTRA)
    refs = {n: 'p ju' + n for n in ('officeroles', 'items', 'issuers', 'offices', 'actions', 'signs', 'cases', 'population', 'excluded', 'activities', 'roles')}
    refs.update({n: 'k ju' + n + '[]' for n in ('person', 'anchor', 'point', 'authority')})
    refs.update(descriptions='i[item a][k juchoice[v item r[p jufirst] r[p jusecond]]]', required='p h7a' if source else 'p jurequired',
        trigger='c[p jutarget][k juperson[] k juspeech[]]', target='r[p jutarget]')
    queries = [k(name, *(refs[n] for n, _ in fields)) for name, fields in (('rpl', BASE), ('rpm', POINT), ('rpn', CASES), ('rpo', CASES))]
    if source:
        per_pair = refs | dict(person='v person', trigger='c[p jutarget][v person v activity]')
        refs['unrestricted'] = 'i[person a activity a][' + k('hzgz', *(per_pair[n] for n, _ in SOURCE_CASES)) + ']'
        queries += [k(name, *(refs[n] for n, _ in SOURCE_POPULATION)) for name in ('hzg3', 'hzg4')]
    coverage = k('rpp', *(refs[n] for n, _ in BASE))
    queries += ['e[r[' + coverage + ']][r[' + coverage + ']]']
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=source, refs=refs, coverage=coverage,
        first_syntax=syntax(description(base, 'p jufirst')), second_syntax=syntax(description(base, 'p jusecond')),
        alias_syntax=syntax(description(base, 'p jualias')), target_syntax=syntax(description(base, 'p jutarget')))


def model_for(data, bits=(True, True, True, False, True, False), variant='baseline', permissions=(True, True), other_free=True):
    initiala, initialb, al, bl, ar, br = bits
    def first(person, activity):
        return Content(SCENES, tuple(activity == 'dutya' and ((person == 'person' and ((point == 'left' and al) or (point == 'right' and ar))) or
            (person == 'other' and ((point == 'left' and other_free) or point == 'right'))) for point in SCENES))
    def second(person, activity):
        return Content(SCENES, tuple((person, activity) == ('person', 'dutyb') and ((point == 'left' and bl) or (point == 'right' and br)) for point in SCENES))
    def action(item): return 'dutya' if item == 'entrya' or variant == 'conflicting' else 'dutyb'
    def requirement(source, person, role, activity, desc, sign, point):
        if variant == 'public_prohibited' and (source, person, role, activity, sign, point) == ('authority', 'person', 'scholar', 'speecha', False, 'anchor') and desc.syntax == data['target_syntax']: return True
        for item, exists in (('entrya', initiala), ('entryb', initialb)):
            expected = data['first_syntax'] if item == 'entrya' or variant == 'conflicting' else data['second_syntax']
            if variant == 'other_description': expected = data['alias_syntax']
            office = 'otheroffice' if variant == 'other_office' else 'office'
            polarity = item == 'entrya'
            if variant == 'other_sign': polarity = not polarity
            if exists and person in ('person', 'other') and (source, role, activity, sign, point) == ('issuer', office, action(item), polarity, 'anchor') and desc.syntax == expected: return True
        return False
    def permission(source, person, role, activity, desc, sign, point):
        return any(grant and (source, person, role, activity, sign, point) == ('authority', who, 'scholar', 'speecha', True, 'anchor') and desc.syntax == data['target_syntax'] for who, grant in zip(('person', 'other'), permissions))
    def target(person, activity):
        return Content(SCENES, tuple(variant != 'empty_target' and person in ('person', 'other') and activity in ('speecha', 'speechb') and point in ('left', 'right') for point in SCENES))
    model = guarded(data['document'])
    model.update(juperson=lambda: 'person', juanchor=lambda: 'anchor', jupoint=lambda: 'left', juofficeroles=lambda role: role in ('office', 'otheroffice'),
        juitems=lambda item: variant != 'empty_items' and item in ('entrya', 'entryb'), juissuers=lambda item: 'issuer', juoffices=lambda item: 'office', juactions=action, jusigns=lambda item: item == 'entrya',
        juchoice=lambda item, first, second: first if item == 'entrya' or variant == 'conflicting' else second,
        jurequired=requirement, jufirst=first, jusecond=second, jualias=first, jutarget=target,
        jucases=lambda point: variant != 'empty_cases' and point in ('left', 'right'),
        jupopulation=lambda person: variant != 'empty_population' and person in ('person', 'other', 'earlier'),
        juexcluded=lambda person: person == 'earlier' or variant == 'all_excluded',
        juactivities=lambda person, activity: variant != 'empty_activities' and person in ('person', 'other', 'earlier') and (activity == 'speecha' or (variant == 'second_activity' and person == 'other' and activity == 'speechb')),
        juauthority=lambda: 'authority', juroles=lambda person: 'scholar', juspeech=lambda: 'speecha')
    if data['source']: model.update(h7a=requirement, h7b=permission)
    return model


def values(data, model, individuals=DOMAIN):
    return [r['value'] for r in evaluate_document(data['document'], individuals=individuals, situations=SCENES, primitives=model, max_steps=60_000_000)]


def coverage_instance(data):
    """Only restrict the description quantifier for a diagnostic model."""
    out = select(data, ()); doc = out['document']
    early = [d for d in doc['declarations'] if d['name'] in ('jufirst', 'jusecond')]
    doc['declarations'] = early + [d for d in doc['declarations'] if d['name'] not in ('jufirst', 'jusecond')]
    definition = next(d for d in doc['declarations'] if d['name'] == 'rpp')
    node = definition['body']
    for _ in range(3): node = node['body']
    assert node['kind'] == 'forall' and node['sort']['kind'] == 'description'
    instances = [{'kind': 'apply', 'function': {'kind': 'lambda', 'parameters': [{'name': node['variable'], 'sort': deepcopy(node['sort'])}],
        'body': deepcopy(node['body'])}, 'arguments': [description(data['document'], 'p ' + name)]} for name in ('jufirst', 'jusecond')]
    node.clear(); node.update(kind='and', arguments=instances)
    out['document'] = parse(format_graph(doc, 'compact') + 'q[' + data['coverage'] + '].')
    return out


def coverage_checks(text):
    data = setup(text); full = select(data, ())
    full['document'] = parse(format_graph(full['document'], 'compact') + 'q[' + data['coverage'] + '].')
    try: values(full, model_for(full))
    except ValueError as exc:
        if 'description domain' not in str(exc): raise
    else: raise ValueError('Full description quantification was silently reduced')
    item = coverage_instance(data); cases = {}
    for name in ('baseline', 'empty_items', 'unlisted_source', 'unlisted_office', 'unlisted_activity', 'unlisted_sign', 'unlisted_description'):
        model = model_for(item, variant='empty_items' if name == 'empty_items' else 'baseline')
        original = model['jurequired']
        if name.startswith('unlisted_'):
            source = 'other' if name == 'unlisted_source' else 'issuer'
            office = 'otheroffice' if name == 'unlisted_office' else 'office'
            act = 'dutyb' if name == 'unlisted_activity' else 'dutya'
            sign = name != 'unlisted_sign'
            expected_desc = item['second_syntax'] if name == 'unlisted_description' else item['first_syntax']
            model['jurequired'] = lambda s, p, r, a, d, b, t, old=original, source=source, office=office, act=act, sign=sign, expected_desc=expected_desc: old(s, p, r, a, d, b, t) or ((s, p, r, a, b, t) == (source, 'person', office, act, sign, 'anchor') and d.syntax == expected_desc)
        for primitive in ('jufirst', 'jusecond', 'jualias'): model[primitive] = guarded(item['document'])[primitive]
        result = values(item, model)
        if result != [name == 'baseline']: raise ValueError('Restricted coverage differs: ' + repr((name, result)))
        cases[name] = result
    empty = model_for(item, (False, False, True, False, True, False), variant='empty_items')
    if values(item, empty) != [True]: raise ValueError('Known absence of requirements was rejected')
    return dict(restricted_descriptions=['jufirst', 'jusecond'], cases=cases, empty_complete_catalogue=True, full_domain_refused=True, full_domain_verified=False)


def checks(texts):
    data = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=6):
        initiala, initialb, al, bl, ar, br = bits; valid = initiala and initialb; left, right = al and not bl, ar and not br
        expected = [valid, valid and left, valid and (left or right), valid and left and right, True]
        result = values(data, model_for(data, bits))
        if result != expected: raise ValueError('Nonrestriction grid differs: ' + repr((bits, result, expected)))
        grid.append(dict(bits=list(bits), result=result))
    print('64 signed requirement/comparison profiles passed', flush=True); sources = []
    for text in texts[1:]:
        data = setup(text, True); profiles, cases = [], {}
        for pa, pb, fa, fb in product((False, True), repeat=4):
            all_allowed = (not fa or pa) and (not fb or pb)
            expected = [True, fa, True, fa, all_allowed, all_allowed and (fa or fb), True]
            result = values(data, model_for(data, (True, True, fa, False, True, False), permissions=(pa, pb), other_free=fb))
            if result != expected: raise ValueError('All-other-person grid differs: ' + repr((pa, pb, fa, fb, result, expected)))
            profiles.append(dict(bits=[pa, pb, fa, fb], result=result))
        for variant, expected in (
            ('empty_items', [True] * 7), ('empty_target', [True, True, False, False, True, False, True]),
            ('empty_cases', [True, True, False, False, True, False, True]), ('conflicting', [True, False, False, False, True, False, True]),
            *[(v, [False, False, False, False, True, False, True]) for v in ('other_office', 'other_description', 'other_sign')],
            *[(v, [True, True, True, True, True, False, True]) for v in ('empty_population', 'empty_activities', 'all_excluded')],
            *[(v, [True, True, True, True, False, False, True]) for v in ('second_activity', 'public_prohibited')]):
            result = values(data, model_for(data, variant=variant))
            if result != expected: raise ValueError('Scope/constraint contrast differs: ' + repr((variant, result, expected)))
            cases[variant] = result
        sources.append(dict(profiles=profiles, cases=cases)); print('All-other-person permission contrasts passed', flush=True)
    return dict(grid=grid, source=sources, coverage=coverage_checks(texts[0]))


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Unrestricted-others artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Unrestricted-others roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']: raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = 'jeder andere, der durch keine Amtspflicht eingeschränkt ist'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_unrestricted_others.py', 'scripts/check_unrestricted_others.py', 'scripts/compose_described_norms.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/grammar.py', 'noema/meaning_basis.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_nonrestricting_requirements_and_all_other_persons', documents=documents, sizes=sizes, interpretation=checks(texts), parent_preserved=True, roundtrips=True,
        new_definitions=12, new_primitives=0, new_author_statements=0, alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args(); result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Unrestricted-others record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print('Nonrestriction, coverage, population scope and independent permission verified')


if __name__ == '__main__': main()
