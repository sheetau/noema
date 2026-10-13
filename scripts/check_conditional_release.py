"""Check tied minima, actual release and fixed-reference hypothetical cases."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, evaluate_document
from noema.first_order_proofs import verify
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.compose_conditional_release import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/conditional-release-v1.json'


def values(doc, model, domain, scenes):
    return [row['value'] for row in evaluate_document(doc, individuals=domain, situations=scenes,
        primitives=model, max_steps=8_000_000, memoize_definitions=True, memoize_expressions=True)]


def minimum_checks():
    doc = parse(generic_composed()[0] + '''r za[a] c.r zb[a a] c.r zc[] a.r zd[] a.r ze[] a.
q[k rcd[p za p zb]].q[k rce[k zc[] p za p zb]].q[k rce[k zd[] p za p zb]].q[k rce[k ze[] p za p zb]].''')
    domain = (0, 1, 2)
    pairs = tuple(product(domain, repeat=2))
    valid, tied = 0, 0
    for bits in product((False, True), repeat=9):
        edges = {pair for pair, yes in zip(pairs, bits) if yes}
        preorder = (all((x, x) in edges for x in domain)
            and all((x, y) in edges or (y, x) in edges for x, y in pairs)
            and all((x, z) in edges for x, y in edges for mid, z in edges if y == mid))
        minima = [preorder and all((x, y) in edges for y in domain) for x in domain]
        actual = values(doc, {'za': lambda x: True, 'zb': lambda x, y: (x, y) in edges,
            'zc': lambda: 0, 'zd': lambda: 1, 'ze': lambda: 2}, domain, ('now',))
        if actual != [preorder] + minima:
            raise ValueError('Contextual preorder/minimum disagrees with the finite relation')
        valid += preorder
        tied += sum(minima) > 1
    empty = values(doc, {'za': lambda x: False, 'zb': lambda x, y: True,
        'zc': lambda: 0, 'zd': lambda: 1, 'ze': lambda: 2}, domain, ('now',))
    if empty != [False] * 4:
        raise ValueError('Empty comparison scope supplied a superlative')
    return {'relations': 512, 'total_preorders': valid, 'models_with_tied_minima': tied, 'empty_scope': empty}


def minimum_laws():
    text = generic_composed()[0] + 'r za[a] c.r zb[a a] c.r zc[] a.r zd[] a.'
    first, second = 'k rce[k zc[] p za p zb]', 'k rce[k zd[] p za p zb]'
    claims = {
        'minimum_belongs_to_scope': f'y[{first}][k za[k zc[]]]',
        'two_minima_have_the_same_rank': f'y[w[{first}][{second}]][w[k zb[k zc[] k zd[]]][k zb[k zd[] k zc[]]]]',
        'eligible_item_below_minimum_is_minimum': f'y[w[{first}][w[k za[k zd[]]][k zb[k zd[] k zc[]]]]][{second}]',
        'minimum_is_a_unique_individual': f'y[w[{first}][{second}]][e[k zc[]][k zd[]]]',
    }
    results = verify(parse(text + ''.join(f's[{body}].' for body in claims.values())))
    if [row['status'] for row in results] != ['valid'] * 3 + ['invalid']:
        raise ValueError('Minimum general laws failed')
    return {name: {'status': row['status'], 'countermodel_found': row['countermodel'] is not None,
        'formula_sha256': hashlib.sha256(row['formula'].encode()).hexdigest()} for name, row in zip(claims, results, strict=True)}


def release_checks():
    doc = parse(generic_composed()[0] + '''
r za[d] c.r zb[d d] c.r zc[a d d] c.r zd[a a d d] c.r ze[a a d] c.r zf[a a a d d] c.r zg[a a] e.
r zh[] a.r zi[] a.r zj[] a.r zk[] d.r zl[] d.
q[k rcf[p za p zb k zj[] k zh[] k zi[] k zk[] k zl[] p zg p zc p zd p ze p zf]].
''')
    scenes = ('before', 'after', 'outside')
    domain = ('object', 'person', 'process', 'other')
    def run(flags, variant=''):
        pre, post, changed, affected, agent, terminates = flags
        def matches(actual, expected, prefix, fields):
            expected = list(expected)
            for i, field in enumerate(fields):
                if variant == prefix + '_' + field:
                    expected[i] = 'outside' if field in ('before', 'after') else 'other'
            return tuple(actual) == tuple(expected)
        model = {'za': lambda point: point in scenes[:2], 'zb': lambda a, b: (a, b) == scenes[:2],
            'zc': lambda p, a, b: changed and matches((p, a, b), ('process', 'before', 'after'), 'change', ('process', 'before', 'after')),
            'zd': lambda who, p, a, b: affected and matches((who, p, a, b), ('person', 'process', 'before', 'after'), 'affected', ('person', 'process', 'before', 'after')),
            'ze': lambda who, p, b: agent and matches((who, p, b), ('person', 'process', 'after'), 'agent', ('person', 'process', 'after')),
            'zf': lambda p, obj, who, a, b: terminates and matches((p, obj, who, a, b), ('process', 'object', 'person', 'before', 'after'), 'terminates', ('process', 'object', 'person', 'before', 'after')),
            'zg': lambda obj, who: Content(scenes, (pre, post, False) if matches((obj, who), ('object', 'person'), 'state', ('object', 'person')) else (False,) * 3),
            'zh': lambda: 'object', 'zi': lambda: 'person', 'zj': lambda: 'process', 'zk': lambda: 'before', 'zl': lambda: 'after'}
        return values(doc, model, domain, scenes)
    rows = []
    for flags in product((False, True), repeat=6):
        actual = run(flags)
        if actual != [flags[0] and not flags[1] and all(flags[2:])]:
            raise ValueError('State absence was confused with person-performed causal release')
        rows.append({'before_after_change_affected_agent_termination': flags, 'result': actual})
    bindings = {}
    for prefix, fields in (('change', ('process', 'before', 'after')), ('affected', ('person', 'process', 'before', 'after')),
        ('agent', ('person', 'process', 'after')), ('terminates', ('process', 'object', 'person', 'before', 'after')),
        ('state', ('object', 'person'))):
        for field in fields:
            variant = prefix + '_' + field
            actual = run((True, False, True, True, True, True), variant)
            if actual != [False]:
                raise ValueError('Release mixed participants/endpoints: ' + variant)
            bindings[variant] = actual
    return {'cases': rows, 'bindings': bindings}


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.r zc[] d.
q[t[k h2w[k za[] k zb[]]][k zc[]]].q[t[k h2x[k za[] k zb[]]][k zc[]]].q[t[k h2y[k za[]]][k zb[]]].''')
    scenes = ('before', 'case', 'anchor')
    domain = ('person', 'shackle', 'release', 'limb', 'movement', 'small', 'tie', 'wide', 'jump', 'jumpsecond')
    variants = {
        'baseline': [True, True, True], 'still_bound': [False, True, False], 'not_person_agent': [False, True, False],
        'no_termination': [False, True, False], 'no_jump': [True, False, False], 'steady_jump': [True, False, False],
        'unselected_tie_has_no_jump': [True, True, True], 'selected_tie_has_no_jump': [True, False, False],
        'selected_wider_ditch': [True, False, False], 'selected_outside_scope': [True, False, False],
        'comparison_unknown': [True, False, False],
        'no_candidates': [True, False, False], 'no_hypothetical_cases': [True, True, False],
        'wrong_jump_person': [True, False, False], 'wider_ditch_only': [True, False, False],
    }
    rows = {}
    for variant, expected in variants.items():
        widths = {'small': 1, 'tie': 1, 'wide': 2}
        def jumps(person, ditch, act, point):
            allowed = [('small', 'jump'), ('tie', 'jumpsecond')]
            if variant in ('unselected_tie_has_no_jump', 'selected_tie_has_no_jump'):
                allowed = allowed[:1]
            if variant == 'wider_ditch_only':
                allowed = [('wide', 'jump')]
            return variant != 'no_jump' and (person, point) == ('shackle' if variant == 'wrong_jump_person' else 'person', 'case') and (ditch, act) in allowed
        model = guarded(doc)
        model.update(za=lambda: 'person', zb=lambda: 'anchor', zc=lambda: 'case',
            h3d=lambda who, anchor: 'wide' if (who, anchor) != ('person', 'anchor') else 'tie' if variant == 'selected_tie_has_no_jump' else 'wide' if variant == 'selected_wider_ditch' else 'movement' if variant == 'selected_outside_scope' else 'small',
            h2s=lambda obj, who, anchor: (obj, who, anchor) == ('shackle', 'person', 'anchor'),
            h2r=lambda who, case, point: (who, case) == ('person', 'case') and point in ('before', 'case'),
            ic=lambda first, last, case: (first, last, case) == ('before', 'case', 'case'),
            ag=lambda process, first, last: (process, first, last) == ('release', 'before', 'case'),
            la=lambda who, process, first, last: (who, process, first, last) == ('person', 'release', 'before', 'case'),
            df=lambda who, process, last: variant != 'not_person_agent' and (who, process, last) == ('person', 'release', 'case'),
            h2q=lambda process, obj, who, first, last: variant != 'no_termination' and (process, obj, who, first, last) == ('release', 'shackle', 'person', 'before', 'case'),
            h2e=lambda obj, limb, who, point: (obj, limb, who) == ('shackle', 'limb', 'person') and (point == 'before' or (variant == 'still_bound' and point == 'case')),
            h2f=lambda limb, who, point: (limb, who) == ('limb', 'person'),
            h2g=lambda who, movement, point: (who, movement) == ('person', 'movement'),
            h2h=lambda obj, limb, who, movement, point: (obj, limb, who, movement) == ('shackle', 'limb', 'person', 'movement'),
            h2p=lambda who, ditch, anchor: variant != 'no_candidates' and (who, anchor) == ('person', 'anchor') and ditch in widths,
            h2n=lambda ditch, case: ditch in widths and case == 'case',
            h2o=lambda first, second, case: variant != 'comparison_unknown' and case == 'case' and first in widths and second in widths and widths[first] <= widths[second],
            h2u=jumps, h2v=lambda act, case: variant != 'steady_jump' and (act, case) in (('jump', 'case'), ('jumpsecond', 'case')),
            dg=lambda act, case: (act, case) in (('jump', 'case'), ('jumpsecond', 'case')),
            h2t=lambda who, anchor, case: variant != 'no_hypothetical_cases' and (who, anchor, case) == ('person', 'anchor', 'case'))
        actual = values(doc, model, domain, scenes)
        if actual != expected:
            raise ValueError('Native conditional release changed fixed referents or scope: ' + str((variant, actual)))
        rows[variant] = actual
    return rows


def attribution_checks():
    doc = parse(source_composed()[0])
    doc['statements'] = doc['statements'][-1:]
    rows = {}
    for variant in ('baseline', 'node', 'author', 'description', 'context'):
        expected = ['node', 'author', 'h2z', 'anchor']
        if variant != 'baseline':
            expected[('node', 'author', 'description', 'context').index(variant)] = 'other'
        model = guarded(doc)
        model.update(h3a=lambda: 'node', wa=lambda: 'author', wh=lambda: 'anchor',
            uc=lambda node, author, description, context: [node, author, json.loads(description.syntax)['symbol'], context] == expected)
        actual = values(doc, model, ('node', 'author', 'other'), ('anchor',))
        if actual != [variant == 'baseline']:
            raise ValueError('Attribution executed its hypothetical content or changed scope')
        rows[variant] = actual
    return {'cases': rows, 'hypothetical_content_unexecuted': True}


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0010')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source unit changed')
    start, end = text.index('Wer sie auch abwürfe'), text.index(', weil er zu dergleichen')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': end, 'source': text[start:end],
        'definitions': ['h2w', 'h3c', 'h2x', 'h2y', 'h2z', 'h3b'], 'status': 'partial_explicit_reading',
        'full_semantic_equivalence': False, 'remaining': ['concessive/scalar auch and dennoch', 'nur restriction',
            'counterfactual selection theory', 'uncertainty and motion foundations', 'because of unfamiliar free movement',
            'complete figurative connection to intellectual independence']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'conditional-release'), (source_composed, 'kant-conditional-release')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored conditional release differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Conditional release roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'][:-1] != parent['statements']:
        raise ValueError('Earlier Kant draft changed')
    paths = list(documents) + [PARENT, 'data/conditional-release-basis-v1.json', 'data/kant-conditional-release-basis-v1.json',
        'scripts/compose_conditional_release.py', 'scripts/check_conditional_release.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'noema/first_order_proofs.py', 'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    report = {'status': 'partial_conditional_release_and_unsteady_minimum_crossings', 'documents': documents,
        'minima': minimum_checks(), 'minimum_laws': minimum_laws(), 'release': release_checks(),
        'source_cases': source_checks(), 'attribution': attribution_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True,
        'reading_review': {'comparison_url': 'https://korpora.org/kant/aa08/036.html', 'location': 'AA VIII 36, lines 10–12',
            'method': '固定版と電子本文を比較。原刊画像の照合ではない。',
            'interpretation': '同じ対象を除去する仮定内でも、文脈で幅が最小の溝に対する不確かな跳躍があるという部分的な読み。'},
        'notation_size': {'canonical_source_document_characters': len(text), 'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}
    return json.loads(json.dumps(report, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Conditional release report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Tied contextual minima, agent-bound release and hypothetical reference scope checked')


if __name__ == '__main__':
    main()
