"""Audit a partial attribution and explicit finite instances of its universal claim."""
from copy import deepcopy
from itertools import product
import argparse
import hashlib
import json

from noema.ranked import parse, format_graph
from noema.ranked_discourse import normalize_document
from noema.guarded_ranked_semantics import evaluate_document, Content, FunctionValue
from noema.grammar import parse as old_parse
from noema.script import transcribe
from noema.semantics import SemanticError
from scripts.compose_quantified_permissions import ROOT, CORE, SOURCE, PARENT, BASIS, REFERENCES, POINT, CATALOGUE, build_documents, basis
from scripts.compose_limits import call as k
from scripts.compose_described_norms import DESCRIPTION

PEOPLE = ('alice', 'bob')
SCENES = ('anchor', 'left', 'right')
DESCRIPTIONS = ('jfirst', 'jsecond', 'jduone', 'jdutwo')
REPORT = ROOT / 'reports/quantified-permissions-v1.json'


def description(name):
    return {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': name}}


def finite_instances(document):
    """Diagnostic only: instantiate every description quantifier at four literals.

    Keep the stored manuscript unchanged. The returned document is NOT an
    equivalent replacement of the full description domain.
    """
    doc = deepcopy(document)
    declarations = ''.join('r ' + name + '[a a] e.' for name in DESCRIPTIONS)
    declarations += 'r jseed[' + ' '.join([DESCRIPTION] * 4) + '] c.r jwho[] a.r jother[] a.r jact[] a.'
    prelude = parse('o:' + declarations)
    doc['declarations'] = prelude['declarations'] + doc['declarations']
    count = 0
    def instantiate(node):
        nonlocal count
        if isinstance(node, list):
            return [instantiate(child) for child in node]
        if not isinstance(node, dict):
            return node
        if node.get('kind') == 'forall' and isinstance(node['sort'], dict) and node['sort']['kind'] == 'description':
            count += 1
            body = instantiate(node['body'])
            cases = [{'kind': 'apply', 'function': {'kind': 'lambda',
                'parameters': [{'name': node['variable'], 'sort': deepcopy(node['sort'])}], 'body': deepcopy(body)},
                'arguments': [description(name)]} for name in DESCRIPTIONS]
            result = cases.pop()
            for item in reversed(cases):
                result = {'kind': 'and', 'arguments': [item, result]}
            return result
        return {key: instantiate(value) for key, value in node.items()}
    doc = instantiate(doc)
    if count != 2:
        raise ValueError('Expected obligation coverage and target-description quantifiers')
    doc['statements'] = []
    text = format_graph(normalize_document(doc), 'compact')
    text += 'q[k jseed[' + ' '.join('r[p ' + name + ']' for name in DESCRIPTIONS) + ']].'
    for who, target in (('jwho', 'jfirst'), ('jother', 'jsecond')):
        fields = dict(person=k(who), activity=k('jact'), target='r[p ' + target + ']', anchor=k('wh'), required='p h7a')
        fields.update({name: k(REFERENCES[name]) for name, _ in CATALOGUE})
        text += 'q[' + k('rpt', *(fields[name] for name, _ in POINT)) + '].'
    text += 'q[t[s[r b[k hzjq[]]]][k wh[]]].'
    return parse(text)


def model_for(doc, permissions=(True, True), fulfilled=(True, True), variant='baseline'):
    stored = {}
    declarations = {d['name']: d for d in doc['declarations']}
    def forbidden(*args):
        raise ValueError('Unspecified interpretation was executed')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    def install(name, fn):
        symbol = REFERENCES[name]
        type_ = declarations[symbol]['result']
        value = FunctionValue(tuple(type_['parameters']), type_['result'], fn)
        model[symbol] = lambda: value
    def label(desc):
        return json.loads(desc.syntax)['symbol']
    def seed(*descriptions):
        stored.update(zip(DESCRIPTIONS, descriptions))
        return True
    def first(person, activity):
        return Content(SCENES, tuple(activity == 'bob' and point == ('left' if person == 'alice' else 'right') for point in SCENES))
    def second(person, activity):
        return Content(SCENES, tuple(activity == 'bob' and point == ('right' if person == 'alice' else 'left') for point in SCENES))
    def duty(who, yes):
        return lambda person, activity: Content(SCENES, tuple(person == who and activity == 'bob' and yes and
            (point == 'left' or (variant in ('two_targets', 'wrong_alternative') and point == 'right')) for point in SCENES))
    def required(issuer, person, role, activity, desc, sign, anchor):
        expected = 'jduone' if person == 'alice' else 'jdutwo'
        if variant == 'opposite_requirement' and label(desc) == ('jfirst' if person == 'alice' else 'jsecond'):
            return (issuer, role, activity, sign, anchor) == ('alice', 'bob', 'bob', False, 'anchor')
        return (issuer, role, activity, label(desc), sign, anchor) == ('alice', 'alice', 'bob', expected, True, 'anchor')
    def permitted(authority, person, role, activity, desc, sign, anchor):
        allowed = permissions[PEOPLE.index(person)]
        expected = 'jfirst' if person == 'alice' else 'jsecond'
        if variant == 'wrong_person':
            expected = 'jsecond' if person == 'alice' else 'jfirst'
        targets = {expected}
        if variant == 'two_targets' and person == 'alice':
            targets.add('jsecond')
        return allowed and (authority, role, activity, sign, anchor) == ('alice', 'alice' if variant == 'wrong_role' else 'bob', 'bob', True, 'anchor') and label(desc) in targets
    def eligible(person, activity, desc, anchor):
        targets = {'jfirst' if person == 'alice' else 'jsecond'}
        if variant in ('two_targets', 'wrong_alternative') and person == 'alice':
            targets.add('jsecond')
        return activity == 'bob' and label(desc) in targets
    install('population', lambda person, anchor: variant != 'empty_population')
    install('excluded', lambda person, anchor: variant == 'exclude_bob' and person == 'bob')
    install('activities', eligible)
    install('roles', lambda person, anchor: 'bob')
    install('officeroles', lambda person, role, anchor: role == 'alice')
    install('items', lambda person, item, anchor: item == 'alice' and variant != 'empty_items')
    install('issuers', lambda person, item, anchor: 'alice')
    install('offices', lambda person, item, anchor: 'alice')
    install('actions', lambda person, item, anchor: 'bob')
    install('descriptions', lambda person, item, anchor: stored['jduone' if person == 'alice' else 'jdutwo'])
    install('signs', lambda person, item, anchor: True)
    install('cases', lambda person, activity, desc, anchor, point: variant != 'empty_cases' and point in ('left', 'right'))
    model.update(h7a=required, h7b=permitted, jseed=seed, jwho=lambda: 'alice', jother=lambda: 'bob', jact=lambda: 'bob',
        wh=lambda: 'anchor', jfirst=first, jsecond=second, jduone=duty('alice', fulfilled[0]), jdutwo=duty('bob', fulfilled[1]))
    model[REFERENCES['authority']] = lambda: 'alice'
    return model


def instance_values(doc, **options):
    return [row['value'] for row in evaluate_document(doc, individuals=PEOPLE, situations=SCENES,
        primitives=model_for(doc, **options), max_steps=10_000_000)]


def check_matrix(doc):
    rows = []
    for bits in product((False, True), repeat=4):
        permissions, fulfilled = bits[:2], bits[2:]
        result = instance_values(doc, permissions=permissions, fulfilled=fulfilled)
        expected = [True, *fulfilled, all(not duty or grant for duty, grant in zip(fulfilled, permissions))]
        if result != expected:
            raise ValueError(('Per-person permission matrix differs', bits, result, expected))
        rows.append(dict(permissions=list(permissions), duties_fulfilled=list(fulfilled), result=result))
    return rows


def attribution_checks(doc):
    selected = deepcopy(doc)
    selected['statements'] = selected['statements'][-1:]
    rows = []
    for grant in (False, True):
        def forbidden(*args):
            raise ValueError('Attribution executed a quoted condition')
        calls = []
        def attributed(node, author, description, scope, context):
            if (node, author, scope, context) != ('node', 'author', 'scope', 'context'):
                raise ValueError('Attribution bindings differ')
            if description.rank != 1 or json.loads(description.syntax) != {'kind': 'call', 'symbol': 'hzjq', 'arguments': []}:
                raise ValueError('Attribution content differs')
            calls.append(True)
            return grant
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update(hzjo=lambda: 'node', wa=lambda: 'author', hzjp=lambda: 'scope', wh=lambda: 'context', hzjn=attributed)
        actual = evaluate_document(selected, individuals=('node', 'author', 'scope'), situations=('context',), primitives=model)
        if actual != [{'kind': 'assert', 'value': grant}] or calls != [True]:
            raise ValueError('Attribution was made factive')
        rows.append(dict(attribution=grant, result=actual))
    return rows


def build_report():
    texts = build_documents()
    expected_basis = basis(texts)
    if json.loads((ROOT / BASIS).read_text(encoding='utf-8')) != expected_basis:
        raise ValueError('Basis differs')
    documents = {}
    for path, text in texts.items():
        if (ROOT / path).read_text(encoding='utf-8') != text:
            raise ValueError('Document differs: ' + path)
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(transcribe(form, alphabet='v2')) != doc:
                raise ValueError('Notation roundtrip differs')
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']),
            characters=len(text), attribution_checks=attribution_checks(doc))
    parent = old_parse((ROOT / PARENT).read_text(encoding='utf-8'))
    source = parse(texts[SOURCE])
    if source['declarations'][:len(parent['declarations'])] != parent['declarations'] or source['statements'][:-1] != parent['statements']:
        raise ValueError('Historical parent was changed')
    core = parse(texts[CORE]); finite = finite_instances(core)
    rows = check_matrix(finite)
    variants = {}
    for variant, expected in (
        ('wrong_person', [True, True, True, False]), ('wrong_role', [True, True, True, False]),
        ('opposite_requirement', [True, True, True, False]), ('two_targets', [True, True, True, True]),
        ('wrong_alternative', [True, True, True, False]), ('empty_items', [True, False, False, True]),
        ('empty_cases', [True, False, False, True]), ('empty_population', [True, True, True, True])):
        value = instance_values(finite, variant=variant)
        if value != expected:
            raise ValueError('Finite distinction differs: ' + variant)
        variants[variant] = value
    full = deepcopy(finite)
    originals = {d['name']: d for d in core['declarations']}
    full['declarations'] = [deepcopy(originals[d['name']]) if d['name'] in ('rpp', 'rpu') else d for d in full['declarations']]
    full = normalize_document(full)
    try:
        evaluate_document(full, individuals=PEOPLE, situations=SCENES, primitives=model_for(full), max_steps=10_000_000)
    except SemanticError as exc:
        if 'description domain' not in str(exc):
            raise
        refusal = str(exc)
    else:
        raise ValueError('Full description domain was silently sampled')
    unit_path = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / unit_path).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = 'jeder andere, der durch keine Amtspflicht eingeschränkt ist'
    start = unit['text'].index(phrase)
    paths = [PARENT, SOURCE, CORE, BASIS, expected_basis['parent_basis'], unit_path,
        'scripts/compose_quantified_permissions.py', 'scripts/check_quantified_permissions.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/compose_described_norms.py', 'noema/ranked.py', 'noema/ranked_discourse.py',
        'noema/guarded_ranked_semantics.py', 'noema/extraction.py', 'tests/test_quantified_permissions.py']
    return dict(status='experimental_partial_quantified_author_attribution_not_semantic_completion',
        documents=documents, parent_preserved=True, new_definitions=4, new_primitives=16, new_author_attributions=1,
        finite_instantiation=dict(description_literals=list(DESCRIPTIONS), universal_domain_proven=False,
            permission_duty_matrix=rows, distinctions=variants, full_domain_refusal=refusal),
        source_note=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase,
            status='experimental_parameterized_partial_reading_not_added_to_coverage_inventory'),
        limitations=expected_basis['unresolved'], verified_semantic_units=0,
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths})


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args(argv)
    result = build_report()
    if args.verify_only:
        if json.loads(REPORT.read_text(encoding='utf-8')) != result:
            raise ValueError('Stored quantified permission report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('One partial attribution connected; 16 finite cases and eight distinctions checked; full description domain refused')


if __name__ == '__main__':
    main()
