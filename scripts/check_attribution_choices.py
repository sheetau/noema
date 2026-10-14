"""Verify outer attribution choices without asserting or evaluating their contents."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.check_bound_revision import assemble
from scripts.compose_limits import call as k, op
from scripts.compose_parameterized_goals import UNIVERSAL_SOURCE
from scripts.compose_attribution_choices import ROOT, PARENT, BUILDERS, CLAIMS

REPORT = ROOT / 'reports/attribution-choices-v1.json'
EXTRA = 'r jynode[] a.r jyauthor[] a.r jycontext[] d.r jyclaims[' + CLAIMS[2:-3] + '] c.'
SIMPLE = '''r jyfirsttruth[d] c.r jysecondtruth[d] c.
d jyfirst[] e[b scene[k jyfirsttruth[v scene]]].
d jyalias[] e[b scene[k jyfirsttruth[v scene]]].
d jysecond[] e[b scene[k jysecondtruth[v scene]]].'''
DOMAIN = ('node', 'author', 'other')
SCENES = ('text', 'other')


def roundtrips(doc):
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        if parse(text) != doc or parse(decode(encode(text, 'v2'))) != doc:
            raise ValueError('Attribution choice roundtrip differs')


def setup(text, source=False, variant='baseline'):
    if source:
        assembled = assemble(text); base = assembled['document']
        refs = dict(source='k jbsource[]', role='k jbrole[]', description='r[' + assembled['policy_text'] + ']', eligible='p jbeligible')
        expressions = [k(n, *(refs[x] for x, _ in UNIVERSAL_SOURCE)) for n in ('hzds', 'hzdt')]
        alias = 'b scene[t[' + expressions[0] + '][v scene]]'
    else:
        base = candidate(text, SIMPLE)
        expressions = ['k jyfirst[]', 'k jysecond[]']; alias = 'k jyalias[]'
    base = parse(format_graph(base, 'compact') + EXTRA)
    joint = 'b scene[' + op('x', 't[' + expressions[0] + '][v scene]', 't[' + expressions[1] + '][v scene]') + ']'
    quotes = ['r[' + expression + ']' for expression in expressions]
    listed = quotes[::-1] if variant == 'reordered' else [quotes[0], *quotes] if variant == 'duplicate' else [] if variant == 'empty' else quotes
    sequence = 'l[i[e]][' + ' '.join(listed) + ']'
    prefix = ['k jynode[]', 'k jyauthor[]', sequence, 'k jycontext[]']
    queries = ''
    for target in (('hzdy', 'hzdz') if source else ('rj4', 'rj5')):
        queries += 'q[' + k(target, *prefix, *([] if source else ['p jyclaims'])) + '].'
    for chosen in [*quotes, 'r[' + alias + ']']:
        queries += 'q[' + k('hzd2' if source else 'rj6', *prefix, *([] if source else ['p jyclaims']), chosen) + '].'
    queries += 'q[' + k('uc' if source else 'jyclaims', 'k jynode[]', 'k jyauthor[]', 'r[' + joint + ']', 'k jycontext[]') + '].'
    doc = parse(format_graph(base, 'compact') + queries)
    descriptions = [description(base, expr) for expr in [*expressions, alias, joint]]
    return doc, descriptions


def model_for(doc, descriptions, bits=(True, False, False), source=False, variant='baseline'):
    first, second, joined = bits
    targets = [syntax(d) for d in descriptions]
    who = 'other' if variant == 'other_author' else 'author'
    where = 'other' if variant == 'other_node' else 'node'
    when = 'other' if variant == 'other_context' else 'text'
    model = guarded(doc)
    # The alias is also claimed, but it is not a member of the declared candidates.
    def claim(node, author, target, context):
        return (node, author, context) == (where, who, when) and (
            target.syntax == targets[0] and first or target.syntax == targets[1] and second
            or target.syntax == targets[2] or target.syntax == targets[3] and joined)
    model.update(jynode=lambda: 'node', jyauthor=lambda: 'author', jycontext=lambda: 'text')
    model['uc' if source else 'jyclaims'] = claim
    return model


def checks(texts, source=False):
    setups = [setup(t, source) for t in texts]; cases = []
    for bits in product((False, True), repeat=3):
        first, second, joined = bits
        want = [first or second, first and second, first, second, False, joined]
        rows = [values(doc, model_for(doc, desc, bits, source), DOMAIN, SCENES) for doc, desc in setups]
        if rows != [want] * len(setups): raise ValueError('Attribution disjunction collapsed into a disjunctive assertion')
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant in ('other_author', 'other_node', 'other_context', 'reordered', 'duplicate', 'empty'):
        selected = [setup(t, source, variant) for t in texts] if variant in ('reordered', 'duplicate', 'empty') else setups
        want = [True, False, True, False, False, False] if variant in ('reordered', 'duplicate') else [False] * 6
        rows = [values(doc, model_for(doc, desc, source=source, variant=variant), DOMAIN, SCENES) for doc, desc in selected]
        if rows != [want] * len(setups): raise ValueError('Attribution context/choice contrast ' + variant)
        contrasts[variant] = want
    for doc, desc in setups:
        model = model_for(doc, desc, source=source)
        name = 'uc' if source else 'jyclaims'; model[name] = guarded(doc)[name]
        try: values(doc, model, DOMAIN, SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc): raise
        else: raise ValueError('Unknown attribution supplied by default')
        roundtrips(doc)
    return dict(cases=cases, contrasts=contrasts, unknown_attribution_refused=True,
        underlying_contents_not_executed=True, claimed_nonmember_not_selected=True,
        source_node_author_and_context_preserved=True, standalone_agrees=True,
        candidates_not_claimed_exhaustive=True, no_automatic_reading_selection=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored attribution choices differ')
        roundtrips(doc); documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrase = 'Ein Zeitalter kann sich nicht verbünden und darauf verschwören'
    if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source range')
    start = unit['text'].index(phrase)
    segment = dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
        range=[start, start + len(phrase)], text=phrase, definitions=['rj4', 'rj5', 'rj6', 'hzdy', 'hzdz', 'hzd2'])
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_attribution_choices.py', 'scripts/check_attribution_choices.py', 'scripts/check_bound_revision.py',
        'scripts/check_assessed_payments.py', 'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py',
        'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'noema/specialization.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_explicit_attribution_choices', documents=documents, sizes=sizes,
        generic=checks([texts[0], texts[2]]), source=checks(texts[1:], True),
        alignment=dict(segments=[segment], semantic_completion=False), new_definitions=6, new_primitives=0,
        new_author_statements=0, parent_preserved=True, roundtrips=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Attribution choice report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Attribution alternatives, explicit choices and unevaluated complete policies checked')


if __name__ == '__main__': main()
