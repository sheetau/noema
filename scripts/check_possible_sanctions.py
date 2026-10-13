"""Check possible outcomes, punitive response bindings and independent permission."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, SequenceValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.check_public_assessment import syntax
from scripts.check_closed_policies import quoted
from scripts.compose_possible_sanctions import ROOT, PARENT, BUILDERS, generic_composed

REPORT = ROOT/'reports/possible-sanctions-v1.json'
SCENES = ('now', 'possible', 'other')
DOMAIN = ('authority', 'measure', 'person', 'offense', 'group', 'issuer', 'role', 'other')
ARGS = 'k zc[] k zd[] r[p zk] p zh p zi p zj'
SANCTION = 'r[k hzat['+ARGS+']]'
EXTRA = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] a.r zf[] d.
r zg[a d d] c.r zh[a a d] c.r zi[a a a d] c.r zj[a a a a i[h[a] e] d] c.
r zk[a] e.r zl[a] e.r zm[] a.r zn[] a.'''


def setup(text):
    doc = candidate(text, EXTRA+
        'q[k hzar[k zd[] k ze[] r[p zl] k zf[] p zg]].'+
        'q[k hzau[k za[] k zb[] '+ARGS+' k zf[] p zg]].'+
        'q[k hzav[k zm[] k za[] k zn[] k zb[] '+SANCTION+' k zf[]]].'+
        'q[t[c[k hzat['+ARGS+']][k za[] k zb[]]][k zf[]]].')
    desc = doc['statements'][2]['body']['arguments'][4]
    return doc, syntax(desc)


def model_for(doc, sanction, bits=(True, True, True, True, True, True), variant='baseline'):
    causal, executed, adverse, intended, response, permitted = bits
    model = guarded(doc)
    for name, value in zip(('za', 'zb', 'zc', 'zd', 'ze', 'zm', 'zn'), DOMAIN[:7]):
        model[name] = lambda value=value: value
    model['zf'] = lambda: 'now'
    def prospective(act, context, scene):
        if variant == 'empty_candidates':
            return False
        return act in ('offense', 'measure') and context == ('other' if variant == 'wrong_evaluation_context' else 'now') and scene in (
            ('possible', 'other') if variant in ('split_causes_and_effect', 'mixed_candidates') else ('possible',))
    model['zg'] = prospective
    model['dg'] = lambda act, scene: (act, scene) == ('offense', 'possible') and (causal or variant == 'cooccurrence_only')
    model['g3'] = lambda act, group, description, scene: causal and (act, group, description.syntax, scene) == (
        'measure' if variant == 'wrong_causal_activity' else 'offense',
        'other' if variant == 'wrong_effect_subject' else 'group', syntax(quoted('function_ref', 'zk' if variant == 'wrong_effect_description' else 'zl')),
        'other' if variant == 'split_causes_and_effect' else 'possible')
    model['zl'] = lambda group: Content(SCENES, (False, causal or variant == 'cooccurrence_only', False))
    actual_scene = 'now' if variant == 'actual_only' else 'possible'
    model['cg'] = lambda actor, measure, scene: executed and (actor, measure, scene) == (
        'other' if variant == 'wrong_authority' else 'authority', 'measure', actual_scene)
    model['zh'] = lambda measure, person, scene: adverse and (measure, person, scene) == (
        'offense' if variant == 'wrong_adverse_measure' else 'measure',
        'other' if variant == 'wrong_adverse_person' else 'person', actual_scene)
    model['zi'] = lambda actor, measure, person, scene: intended and (actor, measure, person, scene) == (
        'authority', 'offense' if variant == 'wrong_intended_measure' else 'measure',
        'other' if variant == 'wrong_intended_person' else 'person', actual_scene)
    model['zj'] = lambda actor, measure, person, offense, assessment, scene: response and (
        actor, measure, person, offense, assessment.syntax, scene) == (
        'authority', 'measure', 'person', 'measure' if variant == 'wrong_offense' else 'offense',
        syntax(quoted('function_ref', 'zl' if variant == 'wrong_assessment' else 'zk')),
        'other' if variant == 'split_response' else actual_scene)
    expected = ('issuer', 'authority', 'role', 'measure', sanction, True, 'now')
    model['h7b'] = lambda source, person, role, act, description, sign, context: permitted and (
        source, person, role, act, description.syntax, sign, context) == expected
    model['h7a'] = lambda source, person, role, act, description, sign, context: variant == 'opposed_requirement' and (
        source, person, role, act, description.syntax, not sign, context) == expected
    # zk remains guarded: an assessment used as a reason is not asserted true.
    return model


def evaluate(doc, model):
    names = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return values(doc, {name: value for name, value in model.items() if name in names}, DOMAIN, SCENES)


def source_checks(texts):
    setups = [setup(text) for text in texts]
    rows = []
    for bits in product((False, True), repeat=6):
        causal, executed, adverse, intended, response, permitted = bits
        expected = [causal, executed and adverse and intended and response, permitted, False]
        actual = [evaluate(doc, model_for(doc, desc, bits)) for doc, desc in setups]
        if actual != [expected]*len(setups):
            raise ValueError('Possibility, response, permission or actuality collapsed: '+repr((bits, actual)))
        rows.append({'states': list(bits), 'results': actual[0]})
    cases = {
        'empty_candidates': [False, False, True, False],
        'wrong_evaluation_context': [False, False, True, False],
        'cooccurrence_only': [False, True, True, False],
        'wrong_causal_activity': [False, True, True, False],
        'wrong_effect_subject': [False, True, True, False],
        'wrong_effect_description': [False, True, True, False],
        'split_causes_and_effect': [False, True, True, False],
        'mixed_candidates': [True, True, True, False],
        'actual_only': [True, False, True, True],
        'wrong_authority': [True, False, True, False],
        'wrong_adverse_measure': [True, False, True, False],
        'wrong_adverse_person': [True, False, True, False],
        'wrong_intended_measure': [True, False, True, False],
        'wrong_intended_person': [True, False, True, False],
        'wrong_offense': [True, False, True, False],
        'wrong_assessment': [True, False, True, False],
        'split_response': [True, False, True, False],
        'opposed_requirement': [True, True, False, False],
    }
    contrasts = {}
    for name, expected in cases.items():
        bits = (name != 'cooccurrence_only', True, True, True, True, True)
        actual = [evaluate(doc, model_for(doc, desc, bits, name)) for doc, desc in setups]
        if actual != [expected]*len(setups):
            raise ValueError('Outcome binding contrast failed: '+name+repr(actual))
        contrasts[name] = actual[0]
    doc, desc = setups[0]
    causal_doc = {**doc, 'statements': [doc['statements'][0]]}
    causal_rows = []
    for occurs, produces, effect in product((False, True), repeat=3):
        model = model_for(causal_doc, desc)
        model['dg'] = lambda act, scene: occurs and (act, scene) == ('offense', 'possible')
        model['g3'] = lambda act, group, description, scene: produces and (
            act, group, description.syntax, scene) == ('offense', 'group', syntax(quoted('function_ref', 'zl')), 'possible')
        model['zl'] = lambda group: Content(SCENES, (False, effect, False))
        result = evaluate(causal_doc, model)
        if result != [occurs and produces and effect]:
            raise ValueError('Occurrence, causal production and effect truth were conflated')
        causal_rows.append({'states': [occurs, produces, effect], 'result': result[0]})
    permission = {**doc, 'statements': [doc['statements'][2]]}
    model = model_for(permission, desc)
    for name in ('cg', 'zh', 'zi', 'zj', 'zl', 'dg', 'g3', 'zg'):
        model[name] = guarded(permission)[name]
    if evaluate(permission, model) != [True]:
        raise ValueError('Permission executed the described sanction')
    unknown = {**doc, 'statements': [doc['statements'][1]]}
    model = model_for(unknown, desc); model['zh'] = guarded(unknown)['zh']
    try:
        evaluate(unknown, model)
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):
            raise
    else:
        raise ValueError('Unknown adverse effect silently accepted')
    return {'cases': rows, 'contrasts': contrasts, 'causal_cases': causal_rows, 'standalone_agrees': True,
        'assessment_not_executed': True, 'permission_without_execution_information': True,
        'unknown_adverse_effect_refused': True, 'sanction_description': json.loads(desc)}


def extent_checks(text):
    doc = candidate(text, '''r za[] a.r zb[a] e.r zc[b] c.r zd[] d.
q[t[k hzas[k za[] p zb p zc]][k zd[]]].''')
    def run(population, count, threshold, outsider=None):
        model = guarded(doc)
        model.update(arithmetic())
        model.update(pa=lambda a, b: a/b if b else Fraction(0), za=lambda: 'group', zd=lambda: 'now',
            mp=lambda group: SequenceValue(tuple(population), '"individual"'), aa=lambda person: person != outsider,
            zb=lambda person: Content(SCENES, (person in population[:count], False, False)),
            zc=lambda ratio: ratio >= threshold)
        return evaluate(doc, model)[0]
    rows = []
    for size in range(1, 6):
        population = DOMAIN[:size]
        for count in range(size+1):
            for threshold in (Fraction(1, 3), Fraction(2, 3), Fraction(1)):
                actual = run(population, count, threshold)
                if actual != (Fraction(count, size) >= threshold):
                    raise ValueError('Extent threshold was hardcoded')
                rows.append({'size': size, 'count': count, 'threshold': str(threshold), 'result': actual})
    invalid = {name: run(population, len(population), Fraction(1, 3), outsider) for name, population, outsider in (
        ('empty', (), None), ('duplicate', ('person', 'person'), None), ('ineligible', ('person', 'other'), 'other'))}
    if any(invalid.values()):
        raise ValueError('Invalid population accepted')
    return {'cases': rows, 'invalid': invalid, 'criterion_is_explicit_not_a_fixed_universal_threshold': True}


def alignment():
    source = json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'kant-1784:u0012')
    segments = []
    for excerpt, names, note in (
        ('das allgemeine Widersetzlichkeiten veranlassen könnte', ['hzar', 'hzas'],
         '抵抗の広がりを指定基準で評価し、同じ候補状況での行為・因果・結果を接続する。抵抗の性質、評価基準、因果の基礎説明は未完。'),
        ('bestraft werden', ['hzat', 'hzau', 'hzav'],
         '意図した不利益を、同じ本人の対象行為の評価への応答として加える操作的な読み。可能結果と規範的許可を別々に保持する。刑罰制度、vorwitzig、Skandal、納付すべき時期と譲歩の談話は未完。')):
        if unit['text'].count(excerpt) != 1:
            raise ValueError('Ambiguous source excerpt')
        start = unit['text'].index(excerpt)
        segments.append({'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'range': [start, start+len(excerpt)],
            'text': excerpt, 'definitions': names, 'status': 'partial', 'review_ja': note})
    return {'segments': segments, 'semantic_completion': False, 'possibility_not_automatically_a_normative_permission': True}


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored possible sanction differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Possible sanctions roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = {'characters': len(text), 'statements': len(doc['statements'])}
    doc, parent = parse(texts[1]), parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    parse(generic_composed()[0]+'q[e[r[p rfn]][r[p rfn]]].')
    try:
        parse(generic_composed()[0]+'q[e[r[p rfk]][r[p rfk]]].')
    except ValueError as exc:
        if 'disquot' not in str(exc).lower():
            raise
    else:
        raise ValueError('Causal description evaluation became unrestricted quotation')
    paths = [*documents, PARENT, *['data/'+stem+'-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_possible_sanctions.py', 'scripts/check_possible_sanctions.py',
        'scripts/check_conditional_release.py', 'scripts/check_scoped_counts.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'artifacts/written-units-v1/kant-1784.json']
    return json.loads(json.dumps({'status': 'partial_possible_causal_outcomes_and_intentional_adverse_responses',
        'documents': documents, 'sizes': sizes, 'source': source_checks(texts[1:]), 'extent': extent_checks(texts[2]),
        'alignment': alignment(), 'parent_preserved': True, 'roundtrips': True,
        'causal_disquotation_cannot_be_quoted': True, 'new_primitives': 0, 'new_author_statements': 0,
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Possible sanctions report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Possible causal outcomes, intentional responses and independent permission checked')


if __name__ == '__main__':
    main()
