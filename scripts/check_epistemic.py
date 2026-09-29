"""Countermodels for recognition, alternatives and rational phi uncertainty."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_epistemic import composed, einstein_composed
from scripts.check_quantities import ARITHMETIC

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/epistemic-v1.json'
FUNCTION = {'kind': 'function', 'parameters': ['number'], 'result': 'number'}
FAMILY = {'kind': 'function', 'parameters': ['situation'], 'result': FUNCTION}


def awareness_checks():
    text = composed()[0] + '''
r xa[] a.r xb[] d.r xc[d] c.
d xd[] i[e][r[b scene[k xc[v scene]]]].
d xe[] i[e][r[b scene[u[u[k xc[v scene]]]]]].
d xf[] i[e][r[b scene[u[k xc[v scene]]]]].
'''
    bodies = {
        'has_alternative': 'k sa[k xa[] k xb[]]',
        'all_true': 'k sb[k xa[] k xb[] s[k xd[]]]',
        'description_supported': 'k sc[k xa[] k xb[] k xd[]]',
        'recognized_supported': 'k sd[k xa[] k xb[] k xd[]]',
        'factive_recognized': 'k se[k xa[] k xb[] k xd[]]',
        'all_false': 'k sf[k xa[] k xb[] s[k xd[]]]',
        'unsettled': 'k sg[k xa[] k xb[] s[k xd[]]]',
        'equivalent_description_recognized': 'k se[k xa[] k xb[] k xe[]]',
        'content_equal': 'e[s[k xd[]]][s[k xe[]]]',
        'negative_recognized': 'k se[k xa[] k xb[] k xf[]]',
        'positive_not_recognized_as_true': 'u[k se[k xa[] k xb[] k xd[]]]',
    }
    doc = parse(text + ''.join('q[' + b + '].' for b in bodies.values()))
    scenes = ('now', 'later')
    cases = [
        ('one_description_only', (True, True), scenes, 'direct', 'alice', 'now'),
        ('both_descriptions_recognized', (True, True), scenes, 'all', 'alice', 'now'),
        ('true_but_no_recognition', (True, True), scenes, 'none', 'alice', 'now'),
        ('two_live_truth_values', (True, False), scenes, 'all', 'alice', 'now'),
        ('false_belief_is_not_factive', (False, True), ('later',), 'all', 'alice', 'now'),
        ('empty_alternatives_are_not_knowledge', (True, True), (), 'all', 'alice', 'now'),
        ('settled_false_and_recognized_negative', (False, False), scenes, 'all', 'alice', 'now'),
        ('another_agent_has_no_given_alternatives', (True, True), scenes, 'all', 'bob', 'now'),
        ('later_stage_has_no_recognition_yet', (True, True), scenes, 'all', 'alice', 'later'),
    ]
    results = {}
    for label, flags, alternatives, awareness, agent, current in cases:
        valuation = dict(zip(scenes, flags))
        def accessible(who, here, there):
            return who == 'alice' and there in alternatives
        def recognized(who, description, here):
            structure = json.loads(description.syntax)
            return (who == 'alice' and here == 'now' and awareness != 'none'
                    and (awareness == 'all' or structure['body']['kind'] == 'call'))
        primitives = {'ra': accessible, 'rb': recognized, 'xa': lambda: agent,
                      'xb': lambda: current, 'xc': lambda scene: valuation[scene]}
        actual = {label: row['value'] for label, row in zip(bodies, evaluate_document(
            doc, individuals=('alice', 'bob'), situations=scenes, primitives=primitives), strict=True)}
        available = alternatives if agent == 'alice' else ()
        all_true = bool(available) and all(valuation[s] for s in available)
        all_false = bool(available) and all(not valuation[s] for s in available)
        aware = agent == 'alice' and current == 'now' and awareness != 'none'
        aware_other = aware and awareness == 'all'
        factive = current in available
        expected = {
            'has_alternative': bool(available), 'all_true': all_true,
            'description_supported': all_true, 'recognized_supported': aware and all_true,
            'factive_recognized': factive and aware and all_true,
            'all_false': all_false, 'unsettled': bool(available) and not all_true and not all_false,
            'equivalent_description_recognized': factive and aware_other and all_true,
            'content_equal': True, 'negative_recognized': factive and aware_other and all_false,
            'positive_not_recognized_as_true': not (factive and aware and all_true)}
        if actual != expected:
            raise ValueError('Epistemic countermodel differs: ' + label)
        results[label] = {'expected': expected, 'actual': actual}
    return results


def query(symbol, args, alternatives, expressions=()):
    doc = parse(einstein_composed()[0])
    primitives = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    primitives.update(ARITHMETIC)
    primitives['ra'] = lambda who, here, there: who == 'alice' and there in alternatives[here]
    arguments = []
    for index, (sort, value) in enumerate(args):
        name = 'zz' + number_word(index)
        doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
        primitives[name] = lambda value=value: value
        arguments.append({'kind': 'call', 'symbol': name, 'arguments': []})
    doc['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': symbol, 'arguments': arguments + list(expressions)}}]
    return evaluate_document(doc, individuals=('alice', 'bob'), situations=('early', 'late', 'alternative'),
                             primitives=primitives)[0]['value']


def phi_checks():
    alternatives = {'early': ('early', 'alternative'), 'late': ('late',), 'alternative': ()}
    def make_family(other):
        return FunctionValue(('situation',), FUNCTION, lambda scene: FunctionValue(
            ('number',), 'number', lambda v: other(v) if scene == 'alternative' else Fraction(2)))
    family = make_family(lambda v: 2 + (v - 3) ** 2)
    def arguments(agent, stage, speed=None, family=family):
        args = [('individual', agent), ('situation', stage), (FAMILY, family)]
        return args if speed is None else args + [('number', Fraction(speed))]
    cases = {}
    for label, args, expected in (
        ('same_at_three_does_not_identify_function', arguments('alice', 'early', 3), False),
        ('different_at_four', arguments('alice', 'early', 4), True),
        ('later_single_candidate', arguments('alice', 'late', 4), False),
        ('other_agent_is_not_assigned_knowledge', arguments('bob', 'early', 4), False),
        ('empty_alternatives_do_not_witness_uncertainty', arguments('alice', 'alternative', 4), False),
        ('different_descriptions_same_function', arguments('alice', 'early', 4, make_family(lambda v: Fraction(1) + 1)), False),
    ):
        actual = query('sq', args, alternatives)
        if actual != expected:
            raise ValueError('Phi pointwise countermodel differs: ' + label)
        cases[label] = {'expected': expected, 'actual': actual}
    numeric = (3, 5, Fraction(5, 4), 0, 0, 0, 0, 2, 4, 6, 8, Fraction(19, 5), -5, 12, 16)
    args = [('situation', 'early'), (FAMILY, family)] + [('number', Fraction(v)) for v in numeric]
    actual = query('su', args, alternatives)
    if not actual:
        raise ValueError('Situation-indexed phi is disconnected from coordinate equations')
    cases['actual_phi_two_reaches_four_coordinate_equations'] = {'expected': True, 'actual': actual}
    wrong = deepcopy(args)
    for index, value in zip((-4, -3, -2, -1), (Fraction(19, 10), Fraction(-5, 2), 6, 8), strict=True):
        wrong[index] = ('number', Fraction(value))
    actual = query('su', wrong, alternatives)
    if actual:
        raise ValueError('Phi was implicitly replaced by one')
    cases['silently_setting_phi_to_one_fails'] = {'expected': False, 'actual': actual}
    candidate = parse('m:d zz[] i[h[b] b][r[i[x b][n p c b]]].')['declarations'][0]['body']
    for symbol, expressions in (('sp', ()), ('sr', (candidate,))):
        try:
            query(symbol, arguments('alice', 'early'), alternatives, expressions)
        except ValueError as error:
            if 'rational number domain' not in str(error):
                raise
            cases[symbol + '_whole_rational_domain_not_sampled'] = {'refused': str(error)}
        else:
            raise ValueError('Infinite rational search should be refused')
    return cases


def build_report():
    documents = {}
    for compose in (composed, einstein_composed):
        text, basis = compose()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored document differs')
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Epistemic roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    source = json.loads((ROOT / 'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:u0085')
    expected_hash = 'b535ff072428fe122e7bd1948027a3d49d43ce3e9be5a1e2c97dae869dbd1806'
    if unit['text_sha256'] != expected_hash or hashlib.sha256(unit['text'].encode('utf-8')).hexdigest() != expected_hash:
        raise ValueError('Original phi source unit differs')
    phrase = 'eine vorläufig unbekannte Funktion von'
    start = unit['text'].index(phrase)
    files = ['scripts/compose_epistemic.py', 'scripts/check_epistemic.py', 'noema/discourse.py',
             'noema/finite_semantics.py', 'noema/grammar.py', 'noema/semantics.py', 'noema/language.py',
             'noema/script.py', 'noema/render.py', 'noema/meaning_basis.py',
             'examples/fragments/epistemic.noema.inc', 'examples/fragments/epistemic-phi.noema.inc',
             'examples/v011/einstein-coordinates.noema', 'data/coordinates-basis-v1.json',
             'data/epistemic-basis-v1.json', 'data/einstein-epistemic-basis-v1.json',
             'scripts/check_quantities.py', *documents]
    return {'status': 'partial_description_and_epistemic_draft', 'documents': documents, 'roundtrips': True,
            'awareness_countermodels': awareness_checks(), 'phi_countermodels': phi_checks(),
            'source_alignment': {'unit': unit['id'], 'sha256': expected_hash,
                                 'selection': {'start': start, 'end': start + len(phrase), 'text': phrase},
                                 'definitions': ['sp', 'sq', 'sr', 'su'], 'status': 'partial',
                                 'remaining_ja': '未知性の一般的意味、候補状況の根拠、著者と論述段階への帰属、後続の導出と実数の関数全域を未記述。'},
            'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'general_knowledge_theory_complete': False, 'whole_phi_function_machine_verified': False,
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Epistemic report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Recognition, alternatives and phi checks reproduced; source coverage remains partial')


if __name__ == '__main__':
    main()
