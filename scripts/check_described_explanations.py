"""Countermodels separate explanation adoption, co-occurrence and descriptions."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_described_explanations import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/described-explanations-v1.json'


def symbol(description):
    syntax = json.loads(description.syntax)
    if syntax['kind'] != 'function_ref':
        raise ValueError('This fixture only interprets its declared property references')
    return syntax['symbol']


def generic_checks():
    doc = parse(generic_composed()[0] + '''
r ya[a d] c.r yb[a d] c.r yc[a d] c.
r wa[] a.r wb[] a.r wc[] d.
d za[object a] e[b scene[k ya[v object v scene]]].
d zb[object a] e[b scene[k yb[v object v scene]]].
d zc[object a] e[b scene[k yc[v object v scene]]].
q[e[p za][p zb]].
q[u[e[r[p za]][r[p zb]]]].
q[k eb[k wa[] r[p za] k wb[] r[p zc] k wc[]]].
q[k ec[k wa[] r[p za] k wb[] r[p zc] k wc[]]].
q[k ed[k wa[] r[p za] r[p zb] r[p zc] k wc[]]].
q[k ea[k wa[] r[p za] k wb[] r[p zc] k wc[]]].
''')
    results = []
    for factor_true, effect_true, selected, excluded in product((False, True), repeat=4):
        model = {'wa': lambda: 'subject', 'wb': lambda: 'subject', 'wc': lambda: 'context',
            'ya': lambda *args: factor_true, 'yb': lambda *args: factor_true, 'yc': lambda *args: effect_true,
            'ea': lambda a, f, b, e, scene: (a, b, scene, symbol(e)) == ('subject', 'subject', 'context', 'zc')
                  and ((symbol(f) == 'za' and selected) or (symbol(f) == 'zb' and excluded))}
        actual = [r['value'] for r in evaluate_document(doc, individuals=('subject', 'other'),
                    situations=('context', 'other'), primitives=model)]
        expected = [True, True, factor_true and effect_true, selected and factor_true and effect_true,
                    selected and not excluded, selected]
        if actual != expected:
            raise ValueError('Explanation truth and description contrast differs')
        results.append({'factor_true': factor_true, 'effect_true': effect_true,
                        'selected_adopted': selected, 'excluded_adopted': excluded,
                        'same_property_values': actual[0], 'different_descriptions': actual[1],
                        'cooccurrence': actual[2], 'adopted_and_cooccurring': actual[3],
                        'contrast': actual[4], 'adoption': actual[5]})
    return results


def source_checks():
    doc = parse(source_composed()[0])
    doc['statements'] = []
    text = format_graph(doc, 'compact') + '''
q[e[k bj[k ao[]]][k bs[k ao[]]]].
q[u[e[r[p bj]][r[p bs]]]].
q[k bd[k ao[] k wh[]]].
'''
    doc = parse(text)
    from scripts.check_kant_discourse import base_model
    variants = ('selected_only', 'excluded_only', 'both_adopted', 'neither_adopted', 'wrong_factor_subject',
                'wrong_effect_subject', 'wrong_effect_description', 'wrong_context', 'reversed_explanation',
                'not_a_person', 'false_factors_can_still_be_adopted')
    results = {}
    for variant in variants:
        seen = []
        def adoption(a, factor, b, effect, scene):
            f, e = symbol(factor), symbol(effect)
            seen.append([a, f, b, e, scene])
            if variant == 'reversed_explanation':
                return (a, f, b, e, scene) == ('reader', 'bf', 'reader', 'bs', 'text')
            expected = ('other' if variant == 'wrong_factor_subject' else 'reader',
                        'other' if variant == 'wrong_effect_subject' else 'reader',
                        'bj' if variant == 'wrong_effect_description' else 'bf',
                        'other' if variant == 'wrong_context' else 'text')
            if (a, b, e, scene) != expected:
                return False
            adopted = {'bs', 'bj'} if variant == 'both_adopted' else {'bj'} if variant == 'excluded_only' else set() if variant == 'neither_adopted' else {'bs'}
            return f in adopted
        model = base_model(doc)
        def forbidden(*args):
            raise ValueError('Source still uses the old extensional explanation relation')
        model.update({'aa': lambda person: person == 'reader' and variant != 'not_a_person',
            'ai': lambda *args: variant == 'false_factors_can_still_be_adopted',
            'aj': lambda *args: variant == 'false_factors_can_still_be_adopted',
            'ak': lambda *args: variant == 'false_factors_can_still_be_adopted', 'ea': adoption, 'ah': forbidden})
        actual = [r['value'] for r in evaluate_document(doc, individuals=('reader', 'other'),
                    situations=('text', 'other'), primitives=model)]
        expected = [True, True, variant in ('selected_only', 'false_factors_can_still_be_adopted')]
        if actual != expected:
            raise ValueError('Kant described cause differs: ' + variant)
        results[variant] = {'same_factor_content_values': actual[0], 'distinct_factor_descriptions': actual[1],
                            'classification_under_adopted_explanation': actual[2], 'adoptions_queried': seen}
    return results


def legacy_collapse_check():
    # Both factors have exactly the same content value, yet the new relation
    # can select one description and exclude the other. The old relation
    # cannot distinguish its identical argument tuples.
    doc = parse(source_composed()[0])
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + '''
q[e[k bj[k ao[]]][k bs[k ao[]]]].
q[w[k ah[k bs[k ao[]] k bf[k ao[]] k wh[]]][u[k ah[k bj[k ao[]] k bf[k ao[]] k wh[]]]]].
''')
    from scripts.check_kant_discourse import base_model
    results = []
    for adopted in (False, True):
        calls = []
        model = base_model(doc)
        def legacy(factor, effect, scene):
            calls.append((factor, effect, scene))
            return adopted
        model.update(aa=lambda person: person == 'reader', ah=legacy)
        actual = [r['value'] for r in evaluate_document(doc, individuals=('reader', 'other'),
                    situations=('text', 'other'), primitives=model)]
        if actual != [True, False] or len(calls) != 2 or calls[0] != calls[1]:
            raise ValueError('Legacy equal-content counterexample differs')
        results.append({'legacy_adoption_value': adopted, 'identical_argument_tuples': True, 'contrast': actual[1]})
    return results


def attribution_check():
    from scripts.check_kant_discourse import base_model, NODES, DOMAIN
    doc = parse(source_composed()[0])
    model = base_model(doc)
    def forbidden(*args):
        raise ValueError('Source attribution evaluated an explanation or its content')
    for name in ('aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag', 'ah', 'ai', 'aj', 'ak', 'al', 'am', 'ap', 'ea'):
        model[name] = forbidden
    seen = []
    def described(node, author, description, context):
        seen.append([node, json.loads(description.syntax)['symbol']])
        return author == 'author' and context == 'text'
    model.update(ua=described, ub=described, uc=described, ud=lambda *args: True, uf=lambda *args: True,
        ue=lambda a, b, context: a in NODES and b in NODES and NODES.index(a) < NODES.index(b))
    rows = evaluate_document(doc, individuals=DOMAIN, situations=('text',), primitives=model)
    expected = [['first', 'bi'], ['second', 'bf'], ['third', 'bp'], ['latin', 'bl'], ['german', 'bn'], ['conclusion', 'bo']]
    if rows != [{'kind': 'assert', 'value': True}] or seen != expected:
        raise ValueError('Source discourse no longer refers to described explanation')
    return {'references': seen, 'contents_evaluated': False}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored described explanation differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Description explanation roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    from scripts.check_kant_discourse import source_alignment
    alignment = source_alignment()
    alignment.update(cause_reading='described_factor_adoption_not_extensional_cooccurrence',
                     causal_mechanism_proved=False, deficit_conjunction_reading_verified=False)
    files = [*documents, 'data/described-explanations-basis-v1.json', 'data/kant-described-explanations-basis-v1.json',
        'examples/v013/kant-contextual-ability.noema', 'data/kant-contextual-ability-basis-v1.json',
        'scripts/compose_described_explanations.py', 'scripts/check_described_explanations.py',
        'scripts/check_kant_discourse.py', 'data/kant-opening-alignment-v1.json', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'described_causal_explanation_partial_source_reading', 'documents': documents,
        'generic_truth_combinations': generic_checks(), 'source_checks': source_checks(),
        'legacy_content_collapse': legacy_collapse_check(), 'attribution': attribution_check(),
        'source_alignment': alignment, 'roundtrips': True,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Description explanation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('16 truth/adoption combinations, 11 source cases and 2 legacy collapse cases checked')


if __name__ == '__main__':
    main()
