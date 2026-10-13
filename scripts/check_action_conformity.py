"""Check scoped nonviolation without equating it to permission or global compliance."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_closed_policies import quoted
from scripts.check_public_assessment import syntax
from scripts import check_assessed_payments as payments
from scripts.compose_action_conformity import ROOT, PARENT, BUILDERS, DESCRIPTION, DESCRIPTIONS, RULE, generic_composed

REPORT = ROOT / 'reports/action-conformity-v1.json'


def local_checks():
    text = generic_composed()[0] + '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.
r zf[a a] e.r zg'''+'['+'a a a a '+DESCRIPTION+' c d] c.'+'''
q[k rfe[k za[] r[p zf] k zb[] k zc[] k zd[] k ze[] p zg]].'''
    doc = parse(text)
    from noema.finite_semantics import Content
    rows = []
    for positive, negative, truth in product((False, True), repeat=3):
        model = {'za': lambda: 'source', 'zb': lambda: 'person', 'zc': lambda: 'role', 'zd': lambda: 'action',
            'ze': lambda: 'now', 'zf': lambda person, action: Content(('now',), (truth,)),
            'zg': lambda source, person, role, action, desc, sign, context: (positive if sign else negative)}
        actual = values(doc, model, ('source', 'person', 'role', 'action'), ('now',))
        expected = (not positive or truth) and (not negative or not truth)
        if actual != [expected]:
            raise ValueError('Polarity requirements collapsed')
        rows.append({'states': [positive, negative, truth], 'conforms': actual[0]})
    return {'cases': rows, 'permission_not_consulted': True, 'opposed_requirements_cannot_both_be_satisfied': True}


def source_setup(text, names=('zzq', 'zu')):
    base, payment, criticism = payments.source_setup(text)
    extra = 'd zu[person a action a] e[b context[k zl[v action v context]]].'
    extra += 'd zx[person a action a] e[k zu[v person v action]].r zv[a] c.'
    extra += 'd zw[] '+DESCRIPTIONS+'[l['+DESCRIPTION+']['+' '.join('r[p '+name+']' for name in names)+']].'
    statements, base['statements'] = base['statements'], []
    base = parse(format_graph(base, 'compact') + extra)
    base['statements'] = statements
    probe = parse(format_graph(base, 'compact') +
        'q[k rff[p zv k zw[] k za[] k zc[] k ze[] k zk[] p h7a]].'
        'q[k hzao[k za[] k zc[] k ze[] k zk[] p zv k zw[]]].')
    scope = probe['statements'][-2:]
    public = base['statements'][2]['body']['arguments']
    source_set = {'kind': 'function_ref', 'symbol': 'zv'}
    descriptions = {'kind': 'call', 'symbol': 'zw', 'arguments': []}
    queries = [base['statements'][1], base['statements'][3], *scope]
    queries += [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': name,
        'arguments': [*public, source_set, descriptions]}} for name in ('hzap', 'hzaq')]
    queries += [base['statements'][5]]
    base['statements'] = queries
    return parse(format_graph(base, 'compact')), payment, criticism


def coverage_checks():
    """Evaluate the actual coverage body on two explicit description instances.

    This is a finite restriction for testing, never a replacement of the stored
    unbounded definition. No description's content needs to be executed.
    """
    count = accepted = 0
    names = ('zf', 'zh')
    for source_mask, description_mask in product(range(4), repeat=2):
        listed = ' '.join('r[p '+name+']' for i, name in enumerate(names) if description_mask & (1 << i))
        text = generic_composed()[0] + '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.
r zf[a a] e.r zh[a a] e.r zi[a] c.r zg[a a a a '''+DESCRIPTION+''' c d] c.
q[k rfh[p zi l['''+DESCRIPTION+']['+listed+'] k zb[] k zc[] k zd[] k ze[] p zg]].'
        doc = parse(text)
        early = [d for d in doc['declarations'] if d['name'] in names]
        doc['declarations'] = early + [d for d in doc['declarations'] if d['name'] not in names]
        definition = next(d for d in doc['declarations'] if d['name'] == 'rfh')
        quantified = definition['body']['body']
        assert quantified['kind'] == 'forall' and quantified['sort']['kind'] == 'description'
        instance = lambda name: {'kind': 'apply', 'function': {'kind': 'lambda',
            'parameters': [{'name': quantified['variable'], 'sort': deepcopy(quantified['sort'])}],
            'body': deepcopy(quantified['body'])}, 'arguments': [quoted('function_ref', name)]}
        definition['body']['body'] = {'kind': 'and', 'arguments': [instance(name) for name in names]}
        doc = parse(format_graph(doc, 'compact'))
        for states in product((0, 1, 2), repeat=4):
            # Four source/description pairs: absent, positive or negative demand.
            records = {(source, syntax(quoted('function_ref', name)), state == 1)
                for (source, name), state in zip(product(('source0', 'source1'), names), states) if state}
            model = guarded(doc)
            model.update(za=lambda: 'source0', zb=lambda: 'person', zc=lambda: 'role', zd=lambda: 'action',
                ze=lambda: 'now', zi=lambda source: source in [
                    'source'+str(i) for i in range(2) if source_mask & (1 << i)],
                zg=lambda source, person, role, action, desc, sign, context: (
                    source, desc.syntax, sign) in records)
            result = values(doc, model, ('source0', 'source1', 'person', 'role', 'action'), ('now',))
            expected = all(not state or (bool(source_mask & (1 << (i//2))) and
                bool(description_mask & (1 << (i % 2)))) for i, state in enumerate(states))
            if result != [expected]:
                raise ValueError('Coverage body lost a source, description or requirement polarity')
            count += 1
            accepted += expected
    return {'restricted_description_instances': list(names), 'norm_and_scope_cases': count,
        'accepted_cases': accepted, 'body_evaluated_without_coverage_oracle': True,
        'description_contents_not_executed': True, 'full_description_domain_verified': False}


def fixture_model(doc, payment, criticism, bits=(False, False, True, False, True, False), sources=('issuer', 'authority')):
    ban, quality_required, quality, paid, spoken, allowed = bits
    model = payments.model_for(doc, payment, criticism, (True, allowed, False, paid, spoken))
    inherited = model['h7a']
    records = []
    if ban:
        records.append(('issuer', syntax(quoted('function_ref', 'zzq')), False))
    if quality_required:
        records.append(('authority', syntax(quoted('function_ref', 'zu')), True))
    def required(source, person, role, action, desc, sign, context):
        if (person, role, action, context) == ('person', 'office', 'speech', 'now'):
            return (source, desc.syntax, sign) in records
        return inherited(source, person, role, action, desc, sign, context)
    model.update(h7a=required, zv=lambda source: source in sources,
        zl=lambda action, context: quality if (action, context) == ('speech', 'now') else True)
    def coverage(scope, descriptions, person, role, action, context, rule):
        # Exact for this explicitly declared finite normative table. The actual
        # Noema quantification over all descriptions is not executed here.
        if (person, role, action, context) != ('person', 'office', 'speech', 'now'):
            return False
        listed = {description.syntax: description for description in descriptions.items}
        for source, target, sign in records:
            if not scope(source) or target not in listed:
                return False
            if not rule(source, person, role, action, listed[target], sign, context):
                raise ValueError('Coverage fixture and required-relation binding differ')
        return True
    model['rfh'] = coverage
    return model


def evaluate(doc, model):
    names = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return values(doc, {name: value for name, value in model.items() if name in names}, payments.DOMAIN, payments.office.SCENES)


def source_checks(texts):
    setups = [source_setup(text) for text in texts]
    setups = [(abstract(doc, {'rfh'}), payment, criticism) for doc, payment, criticism in setups]
    rows = []
    for bits in product((False, True), repeat=6):
        ban, demanded, quality, paid, spoken, allowed = bits
        conforms = (not ban or not spoken) and (not demanded or quality)
        expected = [not paid, allowed, conforms, conforms, spoken and conforms, not spoken or conforms, spoken]
        actual = [evaluate(doc, fixture_model(doc, payment, criticism, bits)) for doc, payment, criticism in setups]
        if actual != [expected]*len(setups):
            raise ValueError('Action conformity was confused with permission/payment: '+repr((bits, actual)))
        rows.append({'states': list(bits), 'results': actual[0]})
    cases = {
        'missing_banning_source': (('zzq', 'zu'), ('authority',), (True, False, True, False, True, False), [True, False, True, False, False, False, True]),
        'missing_positive_property': (('zzq',), ('issuer', 'authority'), (False, True, False, False, True, False), [True, False, True, False, False, False, True]),
        'equal_value_alias_is_not_the_required_description': (('zzq', 'zx'), ('issuer', 'authority'), (False, True, True, False, True, False), [True, False, True, False, False, False, True]),
        'duplicate_descriptions': (('zzq', 'zu', 'zu'), ('issuer', 'authority'), (False, True, True, False, True, False), [True, False, True, True, True, True, True]),
        'empty_scope_with_unlisted_requirement': ((), (), (True, False, True, False, True, False), [True, False, True, False, False, False, True]),
        'no_requirement_for_this_action': ((), (), (False, False, True, False, True, False), [True, False, True, True, True, True, True]),
        'inactive_antecedent_with_nonconformity': (('zzq', 'zu'), ('issuer', 'authority'), (False, True, False, False, False, False), [True, False, False, False, False, True, False]),
    }
    contrasts = {}
    for name, (names, sources, bits, expected) in cases.items():
        actual = []
        for text in texts:
            doc, payment, criticism = source_setup(text, names)
            doc = abstract(doc, {'rfh'})
            actual.append(evaluate(doc, fixture_model(doc, payment, criticism, bits, sources)))
        if actual != [expected]*len(texts):
            raise ValueError('Missing normative scope silently accepted: '+name+repr(actual))
        contrasts[name] = actual[0]
    doc, payment, criticism = setups[0]
    scoped = {**doc, 'statements': [doc['statements'][2]]}
    model = fixture_model(scoped, payment, criticism, (False, True, True, False, True, False))
    model['zl'] = guarded(scoped)['zl']
    try:
        evaluate(scoped, model)
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):
            raise
    else:
        raise ValueError('Unknown action property was silently declared compliant')
    return {'cases': rows, 'contrasts': contrasts, 'standalone_agrees': True,
        'scope_coverage_abstracted_to_the_explicit_normative_table': True,
        'arbitrary_description_domain_not_finitely_verified': True, 'unknown_action_property_refused': True}


def limits_checks(text):
    base, payment, criticism = source_setup(text)
    queries = ('q[k hzan[k za[] k zc[] k ze[] k zk[]]].',
               'q[k rfh[p zv k zw[] k za[] k zc[] k ze[] k zk[] p h7a]].')
    rows = []
    for query in queries:
        doc = candidate(format_graph(base, 'compact'), query)
        model = fixture_model(doc, payment, criticism)
        try:
            evaluate(doc, model)
        except ValueError as exc:
            if 'Cannot finitely quantify the description domain' not in str(exc):
                raise
            rows.append(str(exc))
        else:
            raise ValueError('Universal description condition was replaced with a finite list')
    parse(generic_composed()[0]+'q[e[r[p rfh]][r[p rfh]]].')
    refused = {}
    for name in ('rfe', 'rff', 'rfg', 'rfi'):
        try:
            parse(generic_composed()[0]+'q[e[r[p '+name+']][r[p '+name+']]].')
        except ValueError as exc:
            if 'disquot' not in str(exc).lower():
                raise
            refused[name] = str(exc)
        else:
            raise ValueError('Unrestricted reflective evaluation introduced')
    return {'unbounded_quantification_refusals': rows, 'coverage_can_be_quoted_without_execution': True,
        'quotations_with_disquotation_refused': refused}


def alignment():
    source = json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'kant-1784:u0012')
    excerpt = 'Eben derselbe handelt demohngeachtet der Pflicht eines Bürgers nicht entgegen, wenn er,'
    if unit['text'].count(excerpt) != 1:
        raise ValueError('Noncontravention source range is ambiguous')
    start = unit['text'].index(excerpt)
    return {'segments': [{'unit': unit['id'], 'unit_sha256': unit['text_sha256'],
        'range': [start, start+len(excerpt)], 'text': excerpt, 'definitions': ['hzan', 'hzao', 'hzap', 'hzaq'],
        'status': 'partial', 'review_ja': '同じ納付要求を受ける人の公的発言が、市民側の役割でその行為へ課される全要求を満たすという条件文。許可や別の納付行為の未履行と区別する操作的解釈。義務の制度的な対応、因果的な違反帰属、demohngeachtetの譲歩と処罰可能性の前文は未完。'}],
        'semantic_completion': False, 'source_claim_not_reduced_to_positive_permission': True}


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored action-conformity document differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Action conformity roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = {'characters': len(text), 'statements': len(doc['statements'])}
    doc, parent = parse(texts[1]), parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents, PARENT, *['data/'+stem+'-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_action_conformity.py', 'scripts/check_action_conformity.py', 'scripts/check_assessed_payments.py',
        'scripts/check_office_speech.py', 'noema/description_templates.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return json.loads(json.dumps({'status': 'partial_action_relative_noncontravention_with_explicit_scope_coverage',
        'documents': documents, 'sizes': sizes, 'local': local_checks(), 'coverage': coverage_checks(), 'source': source_checks(texts[1:]),
        'limits': limits_checks(texts[2]), 'alignment': alignment(), 'parent_preserved': True, 'roundtrips': True,
        'new_primitives': 0, 'new_author_statements': 0, 'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Action conformity report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Action-relative conformity, scope completeness and separate payment/speech states checked')


if __name__ == '__main__':
    main()
