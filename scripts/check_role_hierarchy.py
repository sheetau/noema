"""Check scoped partial orders and roles without inferring command authority."""
import argparse
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.first_order_proofs import verify
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_closed_policies import quoted
from scripts.check_command_delivery import syntax
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_role_hierarchy import ROOT, PARENT, BUILDERS, generic_composed, source_composed, core_composed

REPORT = ROOT / 'reports/role-hierarchy-v1.json'
DOMAIN = ('issuer', 'person', 'higher', 'office', 'organization', 'notice', 'action', 'other')
SCENES = ('now', 'later')


def order_checks():
    doc = parse(generic_composed()[0] + '''r za[a] c.r zb[a a] c.r zc[] a.r zd[] a.
q[k rex[p za p zb]].q[k rey[k zc[] k zd[] p za p zb]].''')
    domain = (0, 1, 2)
    pairs = tuple(product(domain, repeat=2))
    accepted = above = 0
    for bits in product((False, True), repeat=9):
        edges = {pair for pair, present in zip(pairs, bits) if present}
        valid = not any(x == y for x, y in edges) and all((x, z) in edges
            for x, y in edges for mid, z in edges if y == mid)
        actual = values(doc, {'za': lambda x: True, 'zb': lambda x, y: (x, y) in edges,
            'zc': lambda: 0, 'zd': lambda: 1}, domain, SCENES)
        if actual != [valid, valid and (0, 1) in edges]:
            raise ValueError('Scoped strict order differs from independent edge check')
        accepted += valid
        above += actual[1]
    cases = {
        'empty_scope': (set(), {(0, 1)}, [True, False]),
        'same_role': ({0}, {(0, 0)}, [False, False]),
        'incomparable': ({0, 1, 2}, {(0, 2)}, [True, False]),
        'outside_cycle': ({0, 1}, {(0, 1), (2, 2), (2, 0), (1, 2)}, [True, True]),
        'missing_transitive_edge': ({0, 1, 2}, {(0, 2), (2, 1)}, [False, False]),
        'transitive_edge_present': ({0, 1, 2}, {(0, 2), (2, 1), (0, 1)}, [True, True]),
        'reversed_order': ({0, 1}, {(1, 0)}, [True, False]),
        'cycle': ({0, 1}, {(0, 1), (1, 0)}, [False, False]),
    }
    rows = {}
    for name, (scope, edges, expected) in cases.items():
        actual = values(doc, {'za': lambda x: x in scope, 'zb': lambda x, y: (x, y) in edges,
            'zc': lambda: 0, 'zd': lambda: 1}, domain, SCENES)
        if actual != expected:
            raise ValueError('Scope or non-direct order confused: ' + name)
        rows[name] = actual
    return {'relations': 512, 'strict_partial_orders': accepted, 'orders_with_requested_edge': above, 'contrasts': rows}


def setup(text):
    extra = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] a.r zf[] d.r zg[] a.r zh[] a.
r zi[a a d] c.r zj[a a a d] c.r zk[a a a d] c.
'''
    doc = candidate(text, extra)
    message = apply_description(doc, quoted('function_ref', 'hzz'), [quoted('call', 'zb')])
    item = lambda n: quoted('call', n)['body']
    roles = [item(n) for n in ('za', 'zb', 'zc', 'zd', 'ze', 'zf')]
    roles += [{'kind': 'function_ref', 'symbol': n} for n in ('zi', 'zj', 'zk')]
    command = roles + [item('zg'), item('zh'), message]
    direct = [item(n) for n in ('za', 'zb', 'zg', 'zh')] + [message, item('zf')]
    duty = [item(n) for n in ('zb', 'zh', 'zd', 'za', 'zf')]
    queries = [('hzae', roles), ('hzaa', direct), ('hzn', duty), ('hzaf', command), ('hzag', command)]
    doc['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': name, 'arguments': args}} for name, args in queries]
    return parse(format_graph(doc, 'compact')), message


def order_laws():
    text = generic_composed()[0] + 'r za[a] c.r zb[a a] c.r zc[] a.r zd[] a.r ze[] a.'
    edge = lambda x, y: 'k rey[k ' + x + '[] k ' + y + '[] p za p zb]'
    ab, bc, ac = edge('zc', 'zd'), edge('zd', 'ze'), edge('zc', 'ze')
    claims = {
        'no_self_superiority': 'u[' + edge('zc', 'zc') + ']',
        'both_roles_in_scope': f'y[{ab}][w[k za[k zc[]]][k za[k zd[]]]]',
        'asymmetry': f'y[{ab}][u[{edge("zd", "zc")}]]',
        'transitivity': f'y[w[{ab}][{bc}]][{ac}]',
        'all_roles_comparable': f'y[k rex[p za p zb]][x[{ab}][{edge("zd", "zc")}]]',
        'only_immediate_superiors': f'y[w[{ab}][{bc}]][u[{ac}]]',
    }
    results = verify(parse(text + ''.join('s[' + body + '].' for body in claims.values())))
    if [row['status'] for row in results] != ['valid'] * 4 + ['invalid'] * 2:
        raise ValueError('Strict order laws failed')
    return {name: {'status': row['status'], 'countermodel_found': row['countermodel'] is not None,
        'formula_sha256': hashlib.sha256(row['formula'].encode()).hexdigest()}
        for name, row in zip(claims, results, strict=True)}


def holder_checks():
    doc = parse(generic_composed()[0] + '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] a.
r zf[] a.r zg[] a.r zh[] a.r zi[] d.r zj[a a d] c.r zk[a a a d] c.r zl[a a a d] c.
q[k rez[k za[] k zb[] k zd[] k ze[] k zh[] k zi[] p zj p zk p zl]].
q[k rez[k zb[] k zc[] k zf[] k zg[] k zh[] k zi[] p zj p zk p zl]].
q[k rez[k za[] k zc[] k zd[] k zg[] k zh[] k zi[] p zj p zk p zl]].
q[k rez[k zb[] k zb[] k zf[] k ze[] k zh[] k zi[] p zj p zk p zl]].''')
    domain = ('a', 'b', 'c', 'top', 'mid', 'alt', 'bottom', 'org')
    model = {name: (lambda val=val: val) for name, val in zip(
        ('za', 'zb', 'zc', 'zd', 'ze', 'zf', 'zg', 'zh', 'zi'), (*domain, 'now'))}
    model.update(zj=lambda role, org, ctx: role in ('top', 'mid', 'alt', 'bottom') and (org, ctx) == ('org', 'now'),
        zk=lambda person, role, org, ctx: (person, role) in {('a', 'top'), ('b', 'mid'), ('b', 'alt'), ('c', 'bottom')}
            and (org, ctx) == ('org', 'now'),
        zl=lambda high, low, org, ctx: (high, low) in {('top', 'mid'), ('alt', 'bottom'), ('alt', 'mid')}
            and (org, ctx) == ('org', 'now'))
    actual = values(doc, model, domain, SCENES)
    if actual != [True, True, False, False]:
        raise ValueError('Role holders were collapsed into a global ranking of people')
    return {'two_roles_for_same_holder': actual, 'personal_transitivity_not_inferred': True,
        'self_superiority_excluded_even_with_ordered_held_roles': True}


def model_for(doc, message, bits=(True, True, True), variant='baseline'):
    ordered, sent, required = bits
    model = guarded(doc)
    constants = dict(zip(('za', 'zb', 'zc', 'zd', 'ze', 'zf', 'zg', 'zh'),
        ('issuer', 'person', 'higher', 'office', 'organization', 'now', 'notice', 'action')))
    if variant == 'same_person':
        constants['za'] = 'person'
    if variant == 'same_role':
        constants['zc'] = 'office'
    model.update({name: (lambda val=val: val) for name, val in constants.items()})
    def members(role, organization, context):
        roles = ('higher',) if variant == 'missing_lower' else ('office',) if variant == 'missing_upper' else ('higher', 'office')
        return role in roles and (organization, context) == (
            'other' if variant == 'member_organization' else 'organization', 'later' if variant == 'member_context' else 'now')
    def holders(person, role, organization, context):
        pairs = {('issuer', 'higher'), ('person', 'office')}
        if variant == 'upper_holder':
            pairs = {('other', 'higher'), ('person', 'office')}
        if variant == 'lower_holder':
            pairs = {('issuer', 'higher'), ('other', 'office')}
        return (person, role) in pairs and (organization, context) == (
            'other' if variant == 'holder_organization' else 'organization', 'later' if variant == 'holder_context' else 'now')
    def above(high, low, organization, context):
        edges = {('higher', 'office')} if ordered else set()
        if variant == 'reverse':
            edges = {('office', 'higher')}
        if variant == 'cycle':
            edges.add(('office', 'higher'))
        return (high, low) in edges and (organization, context) == (
            'other' if variant == 'order_organization' else 'organization', 'later' if variant == 'order_context' else 'now')
    model.update(zi=members, zj=holders, zk=above,
        cf=lambda person, role, context: (person, role) in (
            {('person', 'office')} if variant == 'upper_not_entrusted' else {('issuer', 'higher'), ('person', 'office')}) and context == 'now',
        dg=lambda act, context: sent and (act, context) == ('notice', 'now'),
        f3=lambda person, act, context: (person, act, context) == ('issuer', 'notice', 'now'),
        f2=lambda act, person, action, desc, context: (act, person, action, desc.syntax, context) == (
            'notice', 'person', 'other' if variant == 'message_action' else 'action', syntax(message), 'now'),
        cb=lambda person, action, role, context: (person, action, role, context) == ('person', 'action', 'office', 'now'),
        h7a=lambda issuer, person, role, action, desc, sign, context: required and sign and
            (issuer, person, role, action, symbol(desc), context) == ('other' if variant == 'norm_issuer' else 'issuer',
                'person', 'office', 'action', 'zzq', 'now'))
    # Extracted libraries have fewer primitives; the interpreter demands exact inventories.
    names = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {key: val for key, val in model.items() if key in names}


def source_checks():
    documents = [setup(builder()[0]) for builder in (source_composed, core_composed)]
    def run(bits=(True, True, True), variant='baseline'):
        rows = [values(doc, model_for(doc, msg, bits, variant), DOMAIN, SCENES) for doc, msg in documents]
        if rows[0] != rows[1]:
            raise ValueError('Standalone roles differ from cumulative source')
        return rows[0]
    states = []
    for bits in product((False, True), repeat=3):
        rank, sent, duty = bits
        expected = [rank, sent, duty, rank and sent, rank and sent and duty]
        actual = run(bits)
        if actual != expected:
            raise ValueError('Rank, issuance and duty collapsed')
        states.append({'states': list(bits), 'results': actual})
    contrasts = {}
    for variant in ('missing_lower', 'missing_upper', 'member_organization', 'member_context', 'upper_holder',
                    'lower_holder', 'holder_organization', 'holder_context', 'reverse', 'cycle',
                    'order_organization', 'order_context', 'upper_not_entrusted', 'same_person', 'same_role',
                    'message_action', 'norm_issuer'):
        actual = run(variant=variant)
        expected = ([True, False, True, False, False] if variant == 'message_action' else
                    [True, True, False, True, False] if variant == 'norm_issuer' else
                    [False, False, False, False, False] if variant == 'same_person' else
                    [False, True, True, False, False])
        if actual != expected:
            raise ValueError('Role referent mismatch: ' + str((variant, actual, expected)))
        contrasts[variant] = actual
    for doc, msg in documents:
        selected = {**doc, 'statements': [doc['statements'][3]]}
        model = model_for(selected, msg)
        model['h7a'] = guarded(selected)['h7a']
        if values(selected, model, DOMAIN, SCENES) != [True]:
            raise ValueError('Superior issuance unexpectedly requires a duty')
        for primitive, query in (('zk', 0), ('zj', 0), ('f2', 3), ('h7a', 4)):
            selected = {**doc, 'statements': [doc['statements'][query]]}
            model = model_for(selected, msg)
            model[primitive] = guarded(selected)[primitive]
            try:
                values(selected, model, DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):
                    raise
            else:
                raise ValueError('Unknown role or command stage was completed')
    return {'cases': states, 'contrasts': contrasts, 'standalone_agrees': True,
        'issuance_without_known_duty': True, 'unknowns_refused': True, 'message_description': documents[0][1]}


def alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
        if u['id'] == 'kant-1784:u0012')
    excerpt = 'dem von seinen Oberen etwas anbefohlen wird'
    if unit['text'].count(excerpt) != 1:
        raise ValueError('Ambiguous source excerpt')
    start = unit['text'].index(excerpt)
    return {'segments': [{'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'range': [start, start + len(excerpt)],
        'text': excerpt, 'status': 'partial', 'definitions': ['rex', 'rey', 'rez', 'hzae', 'hzaf', 'hzag'],
        'review_ja': '同一組織・状況の役職順序と保持を明示し、上位者による提示と別に存在する職務要求へ接続した。軍制、権限、正当性、語義全体は未完。'}],
        'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents, sizes = {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored role hierarchy differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Role hierarchy roundtrip failed')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = {'characters': len(text), 'statements': len(doc['statements'])}
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    source = parse(source_composed()[0])
    if source['declarations'][:len(parent['declarations'])] != parent['declarations'] or source['statements'] != parent['statements']:
        raise ValueError('Parent was modified')
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_role_hierarchy.py', 'scripts/check_role_hierarchy.py', 'scripts/check_command_delivery.py',
        'scripts/check_conditional_release.py', 'noema/extraction.py', 'noema/finite_semantics.py', 'noema/first_order_proofs.py',
        'noema/description_templates.py', 'noema/discourse.py', 'artifacts/written-units-v1/kant-1784.json']
    return json.loads(json.dumps({'status': 'partial_scoped_roles_not_military_institution_or_authority',
        'documents': documents, 'sizes': sizes, 'orders': order_checks(), 'order_laws': order_laws(),
        'holders': holder_checks(), 'source': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_primitives': 0, 'new_source_assertions': 0,
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Role hierarchy report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Scoped partial orders and independent role, issuance and duty checked')


if __name__ == '__main__':
    main()
