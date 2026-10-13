"""Distinguish acquired attitudes, continuing states and difficult goals."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_retained_attitudes import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/retained-attitudes-v1.json'
SCENES = ('before', 'acquired', 'middle', 'now', 'future', 'alternative')
DOMAIN = ('person', 'change', 'other')


def values(doc, model, scenes=SCENES):
    return [row['value'] for row in evaluate_document(doc, individuals=DOMAIN, situations=scenes,
        primitives=model, max_steps=20_000_000, memoize_definitions=True, memoize_expressions=True)]


def generic_checks():
    doc = parse(generic_composed()[0] + '''
r za[d] c.r zb[d d] c.r zc[] a.r zd[a] e.r ze[] a.r zf[] d.r zg[] d.r zh[] d.
r zi[a d d] c.r zj[a a d d] c.
q[k raf[p za p zb k zc[] p zd k ze[] k zf[] k zg[] k zh[] p zi p zj]].
''')
    rows = []
    scenes = SCENES[:4]
    for prior, later, middle, current, change, affected in product((False, True), repeat=6):
        model = {'za': lambda point: True, 'zb': lambda a, b: scenes.index(a) < scenes.index(b),
            'zc': lambda: 'person', 'zd': lambda person: Content(scenes, (prior, later, middle, current)),
            'ze': lambda: 'change', 'zf': lambda: 'before', 'zg': lambda: 'acquired', 'zh': lambda: 'now',
            'zi': lambda act, a, b: change and (act, a, b) == ('change', 'before', 'acquired'),
            'zj': lambda person, act, a, b: affected and (person, act, a, b) == ('person', 'change', 'before', 'acquired')}
        actual = values(doc, model, scenes)
        if actual != [not prior and later and middle and current and change and affected]:
            raise ValueError('Acquisition, affected subject or intervening persistence was omitted')
        rows.append(dict(prior=prior, later=later, middle=middle, current=current,
                         change=change, affected=affected, result=actual[0]))
    return rows


QUERY = 'r za[] a.r zb[] d.q[t[k ha2[k za[]]][k zb[]]].q[t[k hb2[k za[]]][k zb[]]].'


def source_model(doc, variant='baseline'):
    model = guarded(doc)
    def history(person, anchor, point):
        return person == 'person' and anchor == 'now' and point != 'alternative' and not (
            variant == 'missing_anchor' and point == 'now' or variant == 'missing_before' and point == 'before')
    def liked(person, description, point):
        return (person, symbol(description)) == ('person', 'bm' if variant == 'different_attitude_target' else 'bf') and (
            point in ('acquired', 'middle', 'now') and not (variant == 'lost_middle' and point == 'middle' or
                variant == 'lost_now' and point == 'now') or
            variant == 'already_liked' and point == 'before' or variant == 'future_liked' and point == 'future')
    def changes(act, first, second):
        return variant != 'no_change' and (act, first, second) == (
            'change', 'alternative' if variant == 'alternative_change' else 'before', 'acquired')
    def affected(person, act, first, second):
        return (person, act, first, second) == (
            'other' if variant == 'different_person' else 'person',
            'other' if variant == 'different_process' else 'change',
            'alternative' if variant == 'alternative_change' else 'before', 'acquired')
    model.update(za=lambda: 'person', zb=lambda: 'now',
        aa=lambda person: person == 'person',
        ae=lambda person, plan, start: variant == 'already_capable' and (person, plan, start) == ('person', 'change', 'now'),
        af=lambda person, plan, start, end: (person, plan, start, end) == ('person', 'change', 'now', 'future'),
        ap=lambda person, plan, start, end: (person, plan, start, end) == ('person', 'change', 'now', 'future'),
        ab=lambda ability, person, point: (ability, person, point) == ('other', 'person', 'future'),
        ac=lambda person, ability, act, point: (person, ability, act, point) == ('person', 'other', 'change', 'future'),
        ad=lambda *args: False,
        ia=history, ic=lambda a, b, anchor: SCENES.index(a) < SCENES.index(b), id=liked, ag=changes, la=affected,
        uu=lambda person, description, point: Fraction(3 if (person, symbol(description), point) == (
            'other' if variant == 'different_burden_person' else 'person',
            'bf' if variant == 'different_burden_goal' else 'up',
            'future' if variant == 'different_burden_context' else 'now') else 0),
        uv=lambda burden, context: variant != 'low_burden' and burden == 3 and context == 'now')
    return {name: callback for name, callback in model.items() if name in guarded(doc)}


def source_checks():
    doc = candidate(source_composed()[0], QUERY)
    rows = {}
    for variant in ('baseline', 'already_liked', 'lost_middle', 'lost_now', 'no_change', 'different_person',
            'different_process', 'alternative_change', 'missing_anchor', 'missing_before', 'different_attitude_target',
            'future_liked', 'already_capable', 'low_burden', 'different_burden_person', 'different_burden_goal', 'different_burden_context'):
        actual = values(doc, source_model(doc, variant))
        acquired = variant in ('baseline', 'future_liked', 'low_burden', 'different_burden_person', 'different_burden_goal', 'different_burden_context')
        difficult = variant not in ('already_capable', 'low_burden', 'different_burden_person', 'different_burden_goal', 'different_burden_context')
        if actual != [acquired, difficult]:
            raise ValueError('Attitude acquisition or activity burden differs: ' + variant + repr(actual))
        rows[variant] = actual
    return rows


def connection_checks():
    doc = abstract(candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k hc2[k za[]]][k zb[]]].'), {'ha2', 'hb2', 'h5'})
    rows = []
    for acquisition, burden, explanation in product((False, True), repeat=3):
        model = guarded(doc)
        model.update(za=lambda: 'person', zb=lambda: 'now')
        for name, flag in (('ha2', acquisition), ('hb2', burden), ('h5', explanation)):
            model[name] = lambda person, flag=flag: Content(SCENES, tuple(person == 'person' and point == 'now' and flag for point in SCENES))
        actual = values(doc, model)
        if actual != [acquisition and burden and explanation]:
            raise ValueError('New attitude was inferred to be a cause or conflated with another condition')
        rows.append(dict(acquisition=acquisition, burden=burden, explanation=explanation, result=actual))
    return rows


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(u for u in json.loads(path.read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0010')
    if hashlib.sha256(unit['text'].encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Third paragraph changed')
    text = unit['text']
    segments = []
    for start, end, definitions in (
        (text.index('schwer,'), text.index('. Er hat'), ['bf', 'up', 'uy', 'hb2']),
        (text.index('Er hat'), text.index(', und ist'), ['h7', 'ha2']),
    ):
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], start=start, end=end,
            source=text[start:end], definitions=definitions, status='partial_explicit_reading', full_semantic_equivalence=False))
    return {'segments': segments, 'verified_full_units': 0,
        'unrepresented_meanings_inside_ranges': ['almost become nature', 'affection beyond favorable acceptance',
            'emphasis sogar', 'self-work mechanism and difficulty beyond activity burden'],
        'generalization_and_inference_not_claimed': True}


def build_report():
    documents = {}
    for builder, name in ((generic_composed, 'retained-attitudes'), (source_composed, 'kant-retained-attitudes')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + name + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored retained attitude differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Retained attitude roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['statements'] != parent['statements'] or doc['declarations'][:len(parent['declarations'])] != parent['declarations']:
        raise ValueError('Earlier Kant definitions or claims changed')
    paths = list(documents) + [PARENT, 'data/retained-attitudes-basis-v1.json', 'data/kant-retained-attitudes-basis-v1.json',
        'scripts/compose_retained_attitudes.py', 'scripts/check_retained_attitudes.py', 'scripts/compose_transitions.py',
        'noema/finite_semantics.py', 'noema/discourse.py', 'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return {'status': 'partial_acquired_attitude_and_difficult_activity', 'documents': documents,
        'generic': generic_checks(), 'source': source_checks(), 'connection': connection_checks(), 'alignment': alignment(),
        'parent_preserved': True, 'roundtrips': True, 'new_primitives': 0,
        'finite_interpretations_not_all_histories': True, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'notation_size': {'canonical_source_document_characters': len(text), 'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Retained attitude report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Acquisition, retained attitude and activity difficulty checked')


if __name__ == '__main__':
    main()
