"""Check source attribution and ordering without endorsing the source's claims."""
import argparse
import hashlib
import json
from pathlib import Path

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_kant_discourse import composed, generic_composed

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/kant-opening-discourse-v1.json'
NODES = ('first', 'second', 'third', 'latin', 'german', 'conclusion')
DOMAIN = ('author', 'reader', *NODES)


def base_model(doc):
    model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update({name: (lambda value=value: value) for name, value in zip(
        ('wa', 'wb', 'wc', 'wd', 'we', 'wf', 'wg'), ('author', *NODES), strict=True)})
    model.update({'ao': lambda: 'reader', 'wh': lambda: 'text'})
    return model


def discourse_checks():
    doc = parse(composed()[0])
    cases = {}
    for variant in ('baseline', 'wrong_author', 'wrong_context', 'wrong_definition', 'quotes_swapped',
                    'wrong_conclusion', 'explanation_reversed', 'missing_quote', 'missing_inference',
                    'missing_premise', 'reversed_text_order', 'self_order', 'nontransitive_order', 'merged_nodes'):
        observed = {'definitions': [], 'quotations': [], 'claims': [], 'inferences': [], 'explanations': []}
        def author_context(who, context):
            return who == ('reader' if variant == 'wrong_author' else 'author') and context == (
                'other' if variant == 'wrong_context' else 'text')
        def define(node, who, description, context):
            observed['definitions'].append([node, description.syntax])
            expected = {'first': 'bi', 'second': 'bf', 'third': 'bp'}
            if variant == 'wrong_definition':
                expected['first'] = 'bf'
            return author_context(who, context) and json.loads(description.syntax) == {
                'kind': 'function_ref', 'symbol': expected.get(node)}
        def quote(node, who, description, context):
            observed['quotations'].append([node, description.syntax])
            symbols = {'latin': 'bl', 'german': 'bn'}
            if variant == 'quotes_swapped':
                symbols = {'latin': 'bn', 'german': 'bl'}
            expected = {'kind': 'call', 'symbol': symbols.get(node),
                        'arguments': [{'kind': 'call', 'symbol': 'ao', 'arguments': []}]}
            return (variant != 'missing_quote' and author_context(who, context)
                    and json.loads(description.syntax) == expected)
        def claim(node, who, description, context):
            observed['claims'].append([node, description.syntax])
            return (author_context(who, context) and node == 'conclusion' and json.loads(description.syntax) == {
                'kind': 'call', 'symbol': 'bk' if variant == 'wrong_conclusion' else 'bo', 'arguments': []})
        def inference(who, premises, conclusion, context):
            selected = [x for x in DOMAIN if premises(x)]
            observed['inferences'].append(selected)
            expected = list(NODES[:-1])
            if variant == 'missing_premise':
                expected.remove('third')
            return (variant != 'missing_inference' and author_context(who, context)
                    and conclusion == 'conclusion' and selected == expected)
        def before(first, second, context):
            if context != 'text' or first not in NODES or second not in NODES:
                return False
            if variant == 'self_order' and first == second == 'first':
                return True
            if variant == 'nontransitive_order' and (first, second) == ('first', 'third'):
                return False
            return NODES.index(first) > NODES.index(second) if variant == 'reversed_text_order' else NODES.index(first) < NODES.index(second)
        def explain(who, source, gloss, context):
            observed['explanations'].append([source, gloss])
            return author_context(who, context) and (source, gloss) == (
                ('german', 'latin') if variant == 'explanation_reversed' else ('latin', 'german'))
        model = base_model(doc)
        model.update({'ua': define, 'ub': quote, 'uc': claim, 'ud': inference, 'ue': before, 'uf': explain})
        # These meanings must not execute merely because their descriptions are
        # attributed to the source. In particular, am remains false.
        semantic_calls = []
        def not_endorsed(*args):
            semantic_calls.append('evaluated')
            return False
        model.update({name: not_endorsed for name in ('am', 'al', 'ae', 'af')})
        if variant == 'merged_nodes':
            model['we'] = lambda: 'german'
        result = evaluate_document(doc, individuals=DOMAIN, situations=('text', 'other'), primitives=model,
                                   max_steps=1000000)
        expected = variant == 'baseline'
        if result != [{'kind': 'assert', 'value': expected}] or semantic_calls:
            raise ValueError('Opening discourse differs: ' + variant)
        cases[variant] = {'expected': expected, 'actual': result[0]['value'],
                          'underlying_contents_evaluated': bool(semantic_calls), 'observed': observed}
    return cases


def imperative_checks():
    doc = parse(composed()[0])
    doc['statements'] = []
    prefix = format_graph(doc, 'compact')
    source = prefix + '''
q[t[k bm[k ao[]]][k wh[]]].
q[t[k bb[k ao[]]][k wh[]]].
q[t[o[k bn[k ao[]]]][k wh[]]].
q[t[o[k bg[k ao[]]]][k wh[]]].
q[e[k bl[k ao[]]][k bn[k ao[]]]].
q[u[e[r[k bl[k ao[]]]][r[k bn[k ao[]]]]]].
q[u[e[k bn[k ao[]]][j s[k bm[k ao[]]]]]].
'''
    candidate = parse(source)
    model = base_model(candidate)
    model.update({'ab': lambda faculty, person, scene: (faculty, person) == ('faculty', 'reader'),
                  'ac': lambda person, faculty, act, scene: (person, faculty, act) == ('reader', 'faculty', 'act'),
                  'ad': lambda guide, person, act, scene: (guide, person, act) == ('guide', 'reader', 'act'),
                  'al': lambda person, goal, scene: person == 'reader' and goal.values == (True,),
                  'wh': lambda: 'text'})
    result = evaluate_document(candidate, individuals=(*DOMAIN, 'faculty', 'act', 'guide'), situations=('text',),
                               primitives=model, max_steps=1000000)
    expected = [True, False, True, False, True, True, True]
    actual = [row['value'] for row in result]
    if actual != expected:
        raise ValueError('Literal German directive or separate Latin act differs')
    labels = ('own_faculty_use_can_be_guided', 'independent_use_fails_under_guidance',
              'german_directive_uses_literal_goal', 'old_directive_added_an_extra_condition',
              'latin_uses_selected_contextual_gloss', 'quoted_forms_remain_distinct', 'directive_is_not_assertion')
    return {label: {'expected': e, 'actual': a} for label, e, a in zip(labels, expected, actual, strict=True)}


def generic_checks():
    text = generic_composed()[0] + '''
r xa[] a.r xb[] a.r xc[] d.
s[k uc[k xa[] k xb[] r[b scene[e[n p a b][n p b b]]] k xc[]]].
q[s[r[e[n p a b][n p b b]]]].
'''
    doc = parse(text)
    model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update({'xa': lambda: 'claim', 'xb': lambda: 'speaker', 'xc': lambda: 'text',
                  'uc': lambda node, who, description, context: (node, who, context) == ('claim', 'speaker', 'text')})
    result = evaluate_document(doc, individuals=('claim', 'speaker'), situations=('text',), primitives=model)
    expected = [{'kind': 'assert', 'value': True}, {'kind': 'ask', 'value': False}]
    if result != expected:
        raise ValueError('Attributing a false mathematical claim endorsed it')
    # Empty roots and using a conclusion as its own premise are not an argument.
    for condition in ('u[e[v node][v node]]', 'e[v node][k xa[]]'):
        doc = parse(generic_composed()[0] + 'r xa[] a.q[k va[i[node a][' + condition + '] k xa[]]].')
        model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
        model['xa'] = lambda: 'claim'
        if evaluate_document(doc, individuals=('claim',), situations=('text',), primitives=model)[0]['value']:
            raise ValueError('Empty or circular premise selection accepted')
    return {'false_math_claim_attributed_without_endorsement': result,
            'empty_premises_rejected': True, 'self_premise_rejected': True}


def source_alignment():
    source = json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'kant-1784:u0008')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != '53d3770fd7c81854403bfe093fe32c056af5a4bdf0b24df71896fc94602d36e9':
        raise ValueError('Original opening unit differs')
    old = json.loads((ROOT / 'data/kant-opening-alignment-v1.json').read_text(encoding='utf-8'))
    references = (('ua', 'bi'), ('ua', 'bf'), ('ua', 'bp'), ('ub', 'bl'), ('ub', 'bn'), ('uc', 'bo'))
    result, covered, previous = [], set(), 0
    for segment, node, (relation, definition) in zip(old['segments'], NODES, references, strict=True):
        excerpt = segment['source']
        if unit['text'].count(excerpt) != 1:
            raise ValueError('Opening source range missing or ambiguous')
        start = unit['text'].index(excerpt)
        end = start + len(excerpt)
        if start < previous:
            raise ValueError('Source ranges overlap')
        previous = end
        covered.update(i for i in range(start, end) if not unit['text'][i].isspace())
        result.append({'id': segment['id'], 'start': start, 'end': end, 'source': excerpt,
                       'node': node, 'relation': relation, 'definition': definition, 'status': 'partial',
                       'reading': 'contextual_german_gloss_not_independent_latin_translation' if node == 'latin' else 'draft'})
    if covered != {i for i, char in enumerate(unit['text']) if not char.isspace()}:
        raise ValueError('Opening source character omitted')
    return {'source_unit': unit['id'], 'source_sha256': digest, 'segments': result,
            'all_nonblank_source_characters_accounted_for': True, 'facsimile_review': unit['facsimile_review'],
            'complete_semantic_translation_verified': False}


def build_report():
    documents = {}
    for compose in (generic_composed, composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored discourse document differs')
        doc = parse(text)
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Discourse roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'examples/v011/kant-linked-draft.noema', 'data/kant-linked-basis-v1.json',
             'data/kant-opening-alignment-v1.json', 'data/expository-discourse-basis-v1.json',
             'data/kant-opening-discourse-basis-v1.json', 'examples/fragments/expository-discourse.noema.inc',
             'examples/fragments/kant-opening-discourse.noema.inc', 'scripts/compose_kant_discourse.py',
             'scripts/check_kant_discourse.py', 'noema/discourse.py', 'noema/finite_semantics.py',
             'noema/meaning_basis.py', 'noema/grammar.py', 'noema/language.py', 'noema/semantics.py', 'noema/script.py']
    return {'status': 'six_segment_partial_opening_discourse', 'documents': documents, 'roundtrips': True,
            'discourse_countermodels': discourse_checks(), 'imperative_countermodels': imperative_checks(),
            'other_topic_checks': generic_checks(), 'source_alignment': source_alignment(),
            'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Opening discourse report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Six source segments connected; full semantic coverage remains unverified')


if __name__ == '__main__':
    main()
