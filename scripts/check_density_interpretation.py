"""Check a connected source reading without certifying old/new equivalence."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.integration_audit import audit_integration, dependency_path
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_equation_presentation import structural_checks as presentation_structure
from scripts.check_material_velocity import structural_checks as velocity_structure
from scripts.check_rod_setup import guarded
from scripts.compose_density_interpretation import ROOT, PARENT, PARENT_BASIS, FULL, CORE, REVIEW, INDEX, SOURCE, BINDINGS, LOCAL, BUILDERS, review_packet

REPORT = ROOT / 'reports/density-interpretation-v1.json'
CONNECTED = ('seov', 'seou', 'seon', 'seom', 'seof', 'seoe', 'seoc', 'seob', 'senz', 'sjs', 'seol', 'seok', 'seoj', 'seor', 'senx', 'senv', 'sent', 'sens')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def structural_checks(doc, parent):
    require(doc['declarations'][:len(parent['declarations'])] == parent['declarations'], 'Historical definitions changed')
    require(len(doc['declarations']) == len(parent['declarations']) + len(LOCAL), 'Unexpected declarations')
    require(len(doc['statements']) == len(parent['statements']), 'Statement count changed')
    require(doc['statements'][:INDEX] == parent['statements'][:INDEX], 'Earlier statements changed')
    require(doc['statements'][INDEX+1:] == parent['statements'][INDEX+1:], 'Later statements changed')
    revised, previous = deepcopy(doc['statements'][INDEX]), parent['statements'][INDEX]
    quote = revised['body']['arguments'][-1]
    expected = dict(kind='quote', body=dict(kind='call', symbol='seov', arguments=[
        dict(kind='call', symbol=BINDINGS[n], arguments=[]) for n, _ in SOURCE]))
    require(quote == expected, 'Interpretation lost fixed argument order or identity')
    revised['body']['arguments'][-1] = deepcopy(previous['body']['arguments'][-1])
    require(revised == previous, 'Source attribution changed beyond its quoted reading')
    paths = {s: dependency_path(doc, INDEX, s) for s in CONNECTED}
    require(all(paths.values()), 'An explanation is still outside the authored content')
    require(dependency_path(doc, INDEX, 'zqd') is None, 'Old opaque velocity assignment survived in this statement')
    require(all(d['kind'] == 'primitive' and d['parameters'] == [] for d in doc['declarations'][len(parent['declarations']):]),
        'Interpretation inputs must be fixed values')
    # These inspect the real definitions, not the propositional abstraction below.
    presentation_structure(doc)
    velocity_structure(doc)
    return dict(dependency_paths=paths, attribution_arguments_preserved=True, one_quote_revised=True,
        old_assignment_not_referenced=True, new_fixed_inputs=len(LOCAL))


def attribution_checks(doc, parent):
    selected = extract_document(doc, statement_indices=[INDEX]).document
    expected = deepcopy(selected['statements'][0]['body']['arguments'][-1]['body'])
    selected['statements'][0]['kind'] = 'ask'
    probes = []
    for present, explain, order in product((False, True), repeat=3):
        model = guarded(selected)
        model.update(rd=lambda: 'author', zqa=lambda: 'earlier', zqb=lambda: 'node',
            zqc=lambda: 'scope', ri=lambda: 'text',
            uh=lambda node, author, content, scope, context: present and
                (node, author, scope, context) == ('node', 'author', 'scope', 'text') and json.loads(content.syntax) == expected,
            uf=lambda author, earlier, node, context: explain and
                (author, earlier, node, context) == ('author', 'earlier', 'node', 'text'),
            ue=lambda earlier, node, context: order and (earlier, node, context) == ('earlier', 'node', 'text'))
        def values(candidate):
            return [r['value'] for r in evaluate_document(candidate,
                individuals=('author', 'earlier', 'node', 'scope', 'other'), situations=('text', 'other'), primitives=model)]
        require(values(selected) == [present and explain and order], 'Attribution changed or physical content executed')
        probes.append(dict(present=present, explain=explain, order=order, result=present and explain and order))
    # The last model is all true; none of the quoted physical relations may run.
    contrasts = {}
    for i, name in enumerate(('node', 'author', 'earlier', 'scope', 'context')):
        changed = deepcopy(selected)
        actual = changed['statements'][0]['body']['arguments'][i]['symbol']
        previous_callback = model[actual]
        model[actual] = lambda: 'other'
        contrasts[name] = values(changed)
        require(contrasts[name] == [False], 'Changed discourse referent accepted: ' + name)
        model[actual] = previous_callback
    quote_contrasts = {}
    for i, (name, _) in enumerate(SOURCE):
        changed = deepcopy(selected)
        original = changed['statements'][0]['body']['arguments'][-1]['body']['arguments'][i]
        # Closed, same-typed identity lambda: value-equivalent syntax is still a different quote.
        ds = {d['name']: d for d in selected['declarations']}
        sort = ds[BINDINGS[name]]['result']
        changed['statements'][0]['body']['arguments'][-1]['body']['arguments'][i] = dict(kind='apply',
            function=dict(kind='lambda', parameters=[dict(name='identity', sort=sort)], body=dict(kind='variable', name='identity')),
            arguments=[original])
        quote_contrasts[name] = values(changed)
        require(quote_contrasts[name] == [False], 'Equivalent quote syntax was silently substituted')
    # The historical quotation references zqd, so keep the full declaration set for this comparison.
    old_quote_probe = deepcopy(doc)
    old_quote_probe['statements'] = [deepcopy(parent['statements'][INDEX])]
    old_quote_probe['statements'][0]['kind'] = 'ask'
    old_model = guarded(old_quote_probe)
    old_model.update(model)
    old_value = evaluate_document(old_quote_probe, individuals=('author', 'earlier', 'node', 'scope', 'other'),
        situations=('text',), primitives=old_model)[0]['value']
    require(old_value is False, 'Historical attitude was automatically transferred')
    return dict(cases=probes, discourse_contrasts=contrasts, quoted_argument_contrasts=quote_contrasts,
        physical_content_not_executed=True, old_quote_not_substituted=True)


def conditional_contrasts():
    """Truth-table abstraction of ONE conditional case, not a physical model.

    A and B are the assignment truth values at the old/new frame. R groups
    the remaining premises; F is existence of the required formula witness.
    pi is the separate seon guard. No real domain is discretized here.
    """
    doc = parse('n:r aa[] c.r ab[] c.r ac[] c.r ad[] c.r ae[] c.r af[] c.r ag[] c.'
        'q[y[w[k aa[]][w[k ab[]][k ac[]]]][k ad[]]].'
        'q[w[k ag[]][y[w[k ae[]][w[k af[]][k ac[]]]][k ad[]]]].')
    rows = []
    for bits in product((False, True), repeat=7):
        olda, oldb, rest, law, newa, newb, pi = bits
        model = {name: (lambda value=value: value) for name, value in zip(('aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag'), bits, strict=True)}
        actual = [r['value'] for r in evaluate_document(doc, individuals=('case',), situations=('context',), primitives=model)]
        expected = [not (olda and oldb and rest) or law, pi and (not (newa and newb and rest) or law)]
        require(actual == expected, 'Conditional abstraction differs')
        if pi and olda == newa and oldb == newb:
            require(actual[0] == actual[1], 'Matching assignments did not preserve this conditional case')
        rows.append(dict(old_assignment=[olda, oldb], new_assignment=[newa, newb], other_premises=rest,
            formula_witness=law, pi=pi, results=actual))
    lost = next(r for r in rows if r['old_assignment'] == [True, True] and r['new_assignment'] == [False, True]
        and r['other_premises'] and not r['formula_witness'] and r['pi'])
    added = next(r for r in rows if r['old_assignment'] == [False, True] and r['new_assignment'] == [True, True]
        and r['other_premises'] and not r['formula_witness'] and r['pi'])
    require(lost['results'] == [False, True] and added['results'] == [True, False], 'Missing counterexamples')
    return dict(cases=rows, lost_case=lost, added_case=added, scope='propositional_case_abstraction_only',
        real_histories_or_source_equivalence_proven=False)


def build_report():
    texts, documents, sizes = {}, {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder()
        require((ROOT / basis['document']).read_text(encoding='utf-8') == text, 'Stored manuscript differs')
        require(json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) == basis, 'Stored basis differs')
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            require(parse(form) == doc and parse(decode(encode(form, 'v2'))) == doc, 'Roundtrip differs')
        texts[basis['document']] = doc
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[basis['document']] = dict(characters=len(text), declarations=len(doc['declarations']), statements=len(doc['statements']))
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = texts[FULL]
    require(extract_document(doc, statement_indices=[INDEX]).document == texts[CORE], 'Standalone manuscript differs')
    require(json.loads((ROOT / REVIEW).read_text(encoding='utf-8')) == review_packet(), 'Review packet differs')
    structure = structural_checks(doc, parent)
    integration = audit_integration(doc)
    previous = json.loads((ROOT / 'reports/equation-presentation-v1.json').read_text(encoding='utf-8'))
    alignment = deepcopy(previous['alignment'])
    alignment['segments'][1].update(definitions=['seov', 'seou', 'seon', 'seom', 'seof', 'seoe'],
        review_ja='実際の引用内容へ総量・密度・速度の説明を接続した改訂読解。旧帰属との双方向一致、追加条件、基礎的な電気量と単位の意味確認は未完。')
    paths = [PARENT, PARENT_BASIS, FULL, CORE, REVIEW,
        *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'data/density-formula-review-v2.json', 'scripts/compose_density_interpretation.py',
        'scripts/check_density_interpretation.py', 'tests/test_density_interpretation.py',
        'scripts/compose_additive_charge.py', 'scripts/compose_local_density.py',
        'scripts/compose_material_velocity.py', 'scripts/check_equation_presentation.py',
        'scripts/check_material_velocity.py', 'scripts/check_rod_setup.py', 'noema/extraction.py',
        'noema/integration_audit.py', 'noema/finite_semantics.py', 'reports/equation-presentation-v1.json',
        'reports/manuscript-integration-v1.json']
    return dict(status='connected_partial_interpretation_not_verified_source_equivalence',
        documents=documents, sizes=sizes, structure=structure, attribution=attribution_checks(doc, parent),
        conditional_contrasts=conditional_contrasts(),
        unreferenced_definition_count=len(integration['unreferenced_definitions']),
        alignment=alignment, new_definitions=0, new_primitives=len(LOCAL), new_author_statements=0,
        revised_author_statements=1, preserved_author_statements=len(doc['statements'])-1,
        original_files_unchanged=True, roundtrips=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args(argv)
    result = build_report()
    if args.verify_only:
        require(json.loads(REPORT.read_text(encoding='utf-8')) == result, 'Stored report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Explanations reached from source quotation; attribution preserved; interpretation differences exposed')


if __name__ == '__main__':
    main()
