"""Check sustained husbandry and ownership without literalizing a depiction."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_caused_conditions import source_unit, paragraph_review as prior_review
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_scoped_groups import PEOPLE, source_model as group_model
from scripts.compose_husbandry_depiction import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/husbandry-depiction-v1.json'
POINTS = ('early', 'middle', 'actual')
SCENES = (*POINTS, 'belief', 'loss')
DOMAIN = (*PEOPLE, 'livestock_node', 'author')


def values(doc, model, people=DOMAIN, scenes=SCENES):
    return [row['value'] for row in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=5_000_000, memoize_definitions=True)]


def generic_candidate():
    return parse(generic_composed()[0] + '''
r za[] a.r zb[a] c.r zc[d] c.r zd[d] c.r ze[d d] c.r zf[a] c.r zg[a] c.
r zh[a a d] c.r zi[a a d] c.r zj[a a d] c.
q[k rab[k za[] p zb p zc p zd p ze p zf p zg p zh p zi p zj]].
''')


def generic_model(variant='baseline', bits=(True, False, True, True, True)):
    animal, human, maintenance, management, purpose = bits
    scope = () if variant == 'empty_period' else ('middle',) if variant == 'single_point' else (
        'early', 'actual') if variant == 'gapped_period' else POINTS
    history = POINTS[:2] if variant == 'outside_history' else POINTS
    def role(kind, keeper, being, point):
        if variant == 'split_roles':
            responsible = 'one' if kind == 'maintenance' else 'two'
        elif variant == 'rotating_keepers':
            responsible = 'two' if point == 'middle' else 'one'
        else:
            responsible = 'one'
        return (keeper == responsible and being == ('one' if variant == 'wrong_being' else 'animal')
                and point in POINTS and not (variant == 'missing_middle' and point == 'middle'))
    def before(a, b):
        return (variant == 'cyclic_history' and (a, b) == ('actual', 'early')) or POINTS.index(a) < POINTS.index(b)
    return {'za': lambda: 'animal', 'zb': lambda keeper: variant != 'empty_keepers' and keeper in ('one', 'two'),
        'zc': lambda point: point in history, 'zd': lambda point: point in scope, 'ze': before,
        'zf': lambda being: (human if being == 'animal' else being in ('one', 'two') and variant != 'nonhuman_keepers'),
        'zg': lambda being: animal and being == 'animal',
        'zh': lambda *args: maintenance and role('maintenance', *args),
        'zi': lambda *args: management and role('management', *args),
        'zj': lambda *args: purpose and role('purpose', *args)}


def generic_checks():
    doc = generic_candidate()
    rows = []
    for bits in product((False, True), repeat=5):
        actual = values(doc, generic_model(bits=bits), ('animal', 'one', 'two'), POINTS)[0]
        expected = bits[0] and not bits[1] and all(bits[2:])
        if actual != expected:
            raise ValueError('Husbandry roles or animal classification differ')
        rows.append({'animal': bits[0], 'human': bits[1], 'roles': list(bits[2:]), 'accepted': actual})
    return rows


def binding_checks():
    doc = generic_candidate()
    rows = {}
    for variant in ('baseline', 'rotating_keepers', 'empty_keepers', 'nonhuman_keepers', 'split_roles',
                    'wrong_being', 'missing_middle', 'empty_period', 'single_point', 'gapped_period',
                    'outside_history', 'cyclic_history'):
        actual = values(doc, generic_model(variant), ('animal', 'one', 'two'), POINTS)[0]
        if actual != (variant in ('baseline', 'rotating_keepers')):
            raise ValueError('Husbandry temporal or role binding differs: ' + variant)
        rows[variant] = actual
    return rows


def source_model(doc, variant='baseline'):
    model = group_model(doc)
    base_human = model['aa']
    actual_human = variant == 'actual_human'
    def human(person):
        if person == 'person':
            return actual_human
        return base_human(person) and not (variant == 'nonhuman_keepers' and person in ('guardone', 'guardtwo'))
    def role(kind, keeper, being, point):
        selected = 'guardtwo' if variant == 'rotating_keepers' and point == 'middle' else 'guardone'
        if variant == 'split_roles' and kind != 'maintenance':
            selected = 'guardtwo'
        if variant == 'foreign_keeper':
            selected = 'other'
        return (keeper == selected and being == ('other' if variant == 'wrong_being' else 'person')
            and point in POINTS and not (variant == 'missing_middle' and point == 'middle')
            and variant != 'missing_' + kind)
    model.update(za=lambda: 'person', zb=lambda: 'actual',
        aa=human, qd=lambda being: variant != 'not_animal' and being == 'person',
        qe=lambda *args: role('maintenance', *args), ql=lambda *args: role('management', *args),
        qm=lambda *args: role('purpose', *args),
        qn=lambda owner, being, context: variant != 'unowned' and (owner, being, context) == (
            'population' if variant == 'foreign_owner' else 'guards', 'person', 'actual'),
        qo=lambda being, context, point: (being, context) == ('person', 'actual') and point in (
            ('middle',) if variant == 'single_point' else POINTS),
        qr=lambda being, context, point: (being, context) == ('person', 'actual') and point in POINTS,
        dd=lambda a, b: a in POINTS and b in POINTS and POINTS.index(a) < POINTS.index(b),
        qp=lambda: 'livestock_node', wa=lambda: 'author', wh=lambda: 'actual',
        qa=lambda node, author, target, depiction, context: (node, author, symbol(target), symbol(depiction), context)
            == ('livestock_node', 'author', 'qj', 'qk', 'actual'))
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: callback for name, callback in model.items() if name in required}


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.
q[t[k qj[k za[]]][k zb[]]].q[t[k qk[k za[]]][k zb[]]].q[k qq[]].
''')
    rows = {}
    for variant in ('baseline', 'rotating_keepers', 'actual_human', 'not_animal', 'unowned', 'foreign_owner',
                    'foreign_keeper', 'nonhuman_keepers', 'split_roles', 'wrong_being', 'missing_middle',
                    'missing_maintenance', 'missing_management', 'missing_purpose', 'single_point'):
        actual = values(doc, source_model(doc, variant))
        expected = [variant == 'actual_human', variant in ('baseline', 'rotating_keepers'), True]
        if actual != expected:
            raise ValueError('Possessive depiction or literal target differs: ' + variant + repr(actual))
        rows[variant] = dict(zip(('target', 'depiction', 'framing'), actual))
    return rows


def target_checks():
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k qj[k za[]]][k zb[]]].')
    rows = {}
    for variant in ('baseline', 'no_supervision', 'foreign_supervisor', 'nonhuman_supervisor', 'outside_population'):
        model = source_model(doc, 'actual_human')
        if variant in ('no_supervision', 'foreign_supervisor', 'nonhuman_supervisor'):
            model['dc'] = lambda actor, person, context: variant != 'no_supervision' and (actor, person, context) == (
                'other' if variant == 'foreign_supervisor' else 'guardone', 'person', 'actual')
        if variant == 'nonhuman_supervisor':
            old_human = model['aa']
            model['aa'] = lambda person: old_human(person) and person != 'guardone'
        if variant == 'outside_population':
            model['mv'] = lambda: 'guards'
        actual = values(doc, model)[0]
        if actual != (variant == 'baseline'):
            raise ValueError('Target supervision binding differs: ' + variant)
        rows[variant] = actual
    return rows


def attribution_checks():
    full = parse(source_composed()[0])
    prior = parse((ROOT / 'examples/v014/kant-caused-conditions.noema').read_text(encoding='utf-8'))
    if full['statements'][:-1] != prior['statements'] or len(full['statements']) != 9:
        raise ValueError('Inherited source assertions changed')
    doc = deepcopy(full)
    doc['statements'] = full['statements'][-1:]
    rows = {}
    for variant in ('baseline', 'wrong_node', 'wrong_author', 'wrong_target', 'wrong_depiction', 'wrong_context', 'reversed'):
        def forbidden(*args):
            raise ValueError('Attribution evaluated target or depiction content')
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        seen = []
        def framing(node, author, target, depiction, context):
            received = (node, author, symbol(target), symbol(depiction), context)
            seen.append(list(received))
            expected = ('other' if variant == 'wrong_node' else 'livestock_node',
                'other' if variant == 'wrong_author' else 'author',
                'kf' if variant == 'wrong_target' else 'qk' if variant == 'reversed' else 'qj',
                'qg' if variant == 'wrong_depiction' else 'qj' if variant == 'reversed' else 'qk',
                'belief' if variant == 'wrong_context' else 'actual')
            return received == expected
        model.update(qp=lambda: 'livestock_node', wa=lambda: 'author', wh=lambda: 'actual', qa=framing)
        actual = values(doc, model)[0]
        if actual != (variant == 'baseline'):
            raise ValueError('Possessive frame reference differs: ' + variant)
        rows[variant] = {'assertion': actual, 'references': seen, 'contents_evaluated': False}
    return rows


def alignment():
    unit = source_unit()
    phrase = 'ihr Hausvieh'
    if unit['text'].count(phrase) != 1:
        raise ValueError('Possessive livestock phrase missing or ambiguous')
    start = unit['text'].index(phrase)
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': start+len(phrase),
        'source': phrase, 'definitions': ['rab', 'qj', 'qk', 'qq'], 'status': 'partial_explicit_reading',
        'full_semantic_equivalence': False,
        'remaining': ['animal classification and husbandry role boundaries', 'ownership institutions',
                      'evaluative effects and metaphor correspondence', 'facsimile review']}


def paragraph_review():
    review = prior_review()
    row = next(item for item in review['current_obligations'] if item['id'] == 'livestock_possession')
    row['progress_ja'] = '飼育上の役割・集団への帰属・比喩の対象と描写の区別を部分的に構成し、反例で束縛を検査した。'
    row['required_review_ja'] = '動物分類、家畜と他の飼育対象との境界、所有制度、支配と比喩の評価的効果の説明。'
    return review


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored husbandry definition differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Husbandry or alphabet roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/husbandry-depiction-basis-v1.json', 'data/kant-husbandry-depiction-basis-v1.json',
        'data/husbandry-reading-review-v1.json', 'examples/v014/kant-caused-conditions.noema',
        'data/kant-caused-conditions-basis-v1.json', 'scripts/compose_husbandry_depiction.py',
        'scripts/check_husbandry_depiction.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'partial_sustained_husbandry_possession_and_figurative_attribution', 'documents': documents,
        'generic': generic_checks(), 'bindings': binding_checks(), 'source': source_checks(),
        'target_bindings': target_checks(), 'attribution': attribution_checks(),
        'alignment': alignment(), 'paragraph_review': paragraph_review(), 'roundtrips': True,
        'definitions_replaced_by_primitives': False, 'inherited_statements_unchanged': True,
        'new_statements': 1, 'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Husbandry report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('32 role combinations, 12 bindings, 15 source, 5 target and 7 attribution cases checked')


if __name__ == '__main__':
    main()
