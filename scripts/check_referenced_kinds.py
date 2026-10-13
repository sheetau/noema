"""Check profile equivalence and non-vacuous reference-dependent activity kinds."""
import argparse
import hashlib
from itertools import product
import json

from noema.first_order_proofs import verify
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_learned_familiarity import source_model as previous_model, alignment as previous_alignment
from scripts.check_rod_setup import guarded
from scripts.compose_referenced_kinds import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/referenced-kinds-v1.json'


def profile_checks():
    doc = parse(generic_composed()[0] + '''r za[] a.r zb[] a.r zc[] d.r zd[] d.
r ze[a] c.r zf[a a d] c.r zg[a d] c.
q[k rck[k za[] k zc[] k zb[] k zd[] p ze p zf]].
q[k rcl[k za[] k zc[] k zb[] k zd[] p ze p zf p zg]].''')
    domain, scenes = ('left', 'right', 'featureone', 'featuretwo'), ('earlier', 'later')
    rows, matched = 0, 0
    for flags in product((False, True), repeat=8):
        selected = flags[:2]
        left, right, eligible = flags[2:4], flags[4:6], flags[6:8]
        model = {'za': lambda: 'left', 'zb': lambda: 'right', 'zc': lambda: 'earlier', 'zd': lambda: 'later',
            'ze': lambda f: f in domain[2:] and selected[domain[2:].index(f)],
            'zf': lambda obj, f, point: f in domain[2:] and ((obj, point) == ('left', 'earlier') and left[domain[2:].index(f)]
                or (obj, point) == ('right', 'later') and right[domain[2:].index(f)]),
            'zg': lambda obj, point: (obj, point) == ('left', 'earlier') and eligible[0]
                or (obj, point) == ('right', 'later') and eligible[1]}
        agreement = any(selected) and all(not selected[i] or left[i] == right[i] for i in range(2))
        actual = values(doc, model, domain, scenes)
        if actual != [agreement, agreement and all(eligible)]:
            raise ValueError('Feature agreement or eligible scope differs')
        rows += 1
        matched += actual[1]
    return {'cases': rows, 'eligible_matches': matched}


def profile_laws():
    text = generic_composed()[0] + '''r za[] a.r zb[] a.r zc[] a.r zd[] d.r ze[] d.r zf[] d.
r zg[a] c.r zh[a a d] c.r zi[a d] c.'''
    def relation(first, point, second, otherpoint, guarded=False):
        return f'k {"rcl" if guarded else "rck"}[k {first}[] k {point}[] k {second}[] k {otherpoint}[] p zg p zh' + (' p zi' if guarded else '') + ']'
    xy, yx = relation('za', 'zd', 'zb', 'ze'), relation('zb', 'ze', 'za', 'zd')
    yz, xz = relation('zb', 'ze', 'zc', 'zf'), relation('za', 'zd', 'zc', 'zf')
    guarded = relation('za', 'zd', 'zb', 'ze', True)
    claims = {
        'nonempty_scope_is_reflexive': f'y[g f a[k zg[v f]]][{relation("za", "zd", "za", "zd")}]',
        'fixed_scope_is_symmetric': f'y[{xy}][{yx}]',
        'fixed_scope_is_transitive': f'y[w[{xy}][{yz}]][{xz}]',
        'eligible_match_implies_both_eligible': f'y[{guarded}][w[k zi[k za[] k zd[]]][k zi[k zb[] k ze[]]]]',
        'eligible_match_implies_profile_match': f'y[{guarded}][{xy}]',
        'same_profile_implies_same_individual': f'y[{xy}][e[k za[]][k zb[]]]',
        'profiles_are_independent_of_context': f'y[{xy}][{relation("za", "ze", "zb", "ze")}]',
        'profile_alone_implies_eligibility': f'y[{xy}][{guarded}]',
    }
    rows = verify(parse(text + ''.join(f's[{body}].' for body in claims.values())))
    if [row['status'] for row in rows] != ['valid'] * 5 + ['invalid'] * 3:
        raise ValueError('Fixed-profile laws failed')
    return {name: {'status': row['status'], 'countermodel_found': row['countermodel'] is not None,
        'formula_sha256': hashlib.sha256(row['formula'].encode()).hexdigest()} for name, row in zip(claims, rows, strict=True)}


def native_model(doc, variant):
    model = previous_model(doc, 'baseline')
    stds = ('jump', 'limb') if variant in ('multiple_coherent_references', 'inconsistent_references') else ('jump',)
    model.update(zd=lambda: 'other', ze=lambda: 'before',
        h3u=lambda who, anchor, act, point: variant != 'no_reference' and (who, anchor, point) ==
            ('shackle' if variant == 'wrong_reference_person' else 'person', 'case' if variant == 'wrong_reference_anchor' else 'anchor',
             'before' if variant == 'wrong_reference_case' else 'case') and act in stds,
        h3w=lambda feature, anchor: variant != 'no_features' and (feature, anchor) == ('feature', 'anchor'),
        h3v=lambda who, act, feature, point: (who, feature) == ('person', 'feature') and
            ((act, point) == ('other', 'before') and variant != 'different_selected_feature'
             or point == 'case' and act in stds and not (variant == 'inconsistent_references' and act == 'limb')),
        h3h=lambda who, act, point: who == 'person' and (point == 'case' and act in stds
            or (act, point) == ('other', 'before') and variant != 'familiar_without_current_candidate'),
        dg=lambda act, case: case == 'case' and act in stds,
        h2u=lambda who, ditch, act, case: variant != 'wrong_reference_ditch' and (who, ditch, case) == ('person', 'small', 'case') and act in stds,
        h2v=lambda act, case: variant != 'reference_not_unsteady' and case == 'case' and act in stds,
        h3e=lambda who, event, desc, point: (who, event, symbol(desc), point) ==
            ('person', 'experience', 'h3j' if variant == 'only_broad_activity_familiar' else 'h3y', 'before'),
        h3f=lambda who, desc, case: variant in ('familiar', 'familiar_without_current_candidate', 'only_broad_activity_familiar')
            and (who, symbol(desc), case) == ('person', 'h3j' if variant == 'only_broad_activity_familiar' else 'h3y', 'case'),
        h3g=lambda event, who, desc, before, case: (event, who, symbol(desc), before, case) ==
            ('experience', 'person', 'h3j' if variant == 'only_broad_activity_familiar' else 'h3y', 'before', 'case'),
        ea=lambda who, factor, subject, effect, point: (who, symbol(factor), subject, symbol(effect), point) ==
            ('person', 'h3l' if variant == 'old_broad_reason' else 'h4b', 'person', 'h3o', 'case'))
    return model


def native_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.r zc[] d.r zd[] a.r ze[] d.
q[k h3x[k za[] k zd[] k ze[] k zc[]]].q[k h4g[k za[] k zc[]]].
q[t[k h4a[k za[]]][k zb[]]].q[t[k h4b[k za[]]][k zb[]]].
q[t[k h4c[k za[]]][k zb[]]].q[t[k h4d[k za[]]][k zc[]]].''')
    domain = ('person', 'shackle', 'release', 'limb', 'movement', 'small', 'jump', 'experience', 'other', 'feature')
    scenes = ('before', 'case', 'anchor')
    expected = {'baseline': [True, True, False, True, True, True],
        'different_selected_feature': [False, True, False, True, True, True],
        'multiple_coherent_references': [True, True, False, True, True, True],
        'familiar': [True, True, True, False, False, False],
        'familiar_without_current_candidate': [False, True, True, False, False, False],
        'only_broad_activity_familiar': [True, True, False, True, True, True],
        'old_broad_reason': [True, True, False, True, False, False]}
    for name in ('no_reference', 'no_features', 'wrong_reference_person', 'wrong_reference_anchor', 'wrong_reference_case',
                 'wrong_reference_ditch', 'reference_not_unsteady', 'inconsistent_references'):
        expected[name] = [False] * 6
    rows = {}
    for variant, wanted in expected.items():
        actual = values(doc, native_model(doc, variant), domain, scenes)
        if actual != wanted:
            raise ValueError('Referenced kind or reason scope differs: ' + str((variant, actual)))
        rows[variant] = actual
    return rows


def attribution_checks():
    doc = parse(source_composed()[0])
    doc['statements'] = doc['statements'][-1:]
    rows = {}
    for variant in ('baseline', 'old_broad_content', 'wrong_node', 'wrong_author', 'wrong_context', 'reversed_order'):
        model = guarded(doc)
        expected = ['reason', 'author', 'h3r' if variant == 'old_broad_content' else 'h4e', 'anchor']
        if variant in ('wrong_node', 'wrong_author', 'wrong_context'):
            expected[{'wrong_node': 0, 'wrong_author': 1, 'wrong_context': 3}[variant]] = 'other'
        model.update(h3s=lambda: 'reason', h3a=lambda: 'conditional', wa=lambda: 'author', wh=lambda: 'anchor',
            uc=lambda node, author, desc, ctx: [node, author, json.loads(desc.syntax)['symbol'], ctx] == expected,
            ue=lambda first, last, ctx: (first, last, ctx) == (('reason', 'conditional', 'anchor') if variant == 'reversed_order'
                else ('conditional', 'reason', 'anchor')))
        actual = values(doc, model, ('reason', 'conditional', 'author', 'other'), ('anchor',))
        if actual != [variant == 'baseline']:
            raise ValueError('New reference-sensitive content was not kept in attribution')
        rows[variant] = actual
    return {'cases': rows, 'content_unexecuted': True}


def alignment():
    row = previous_alignment()
    row['definitions'] = ['h3x', 'h3y', 'h3z', 'h4g', 'h4a', 'h4b', 'h4c', 'h4d', 'h4e', 'h4f']
    row['remaining'][0] = 'which features and prior depictions dergleichen selects'
    return row


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'referenced-kinds'), (source_composed, 'kant-referenced-kinds')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored kind reference differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Referenced kind roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'][:-1] != parent['statements'][:-1]:
        raise ValueError('Prior definitions or earlier assertions changed')
    if parent['statements'][-1]['body']['symbol'] != 'h3t' or doc['statements'][-1]['body']['symbol'] != 'h4f':
        raise ValueError('Broad activity attribution was not replaced')
    paths = list(documents) + [PARENT, 'data/referenced-kinds-basis-v1.json', 'data/kant-referenced-kinds-basis-v1.json',
        'scripts/compose_referenced_kinds.py', 'scripts/check_referenced_kinds.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'noema/first_order_proofs.py', 'scripts/check_learned_familiarity.py', 'artifacts/written-units-v1/kant-1784.json',
        'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_fixed_feature_kind_reference', 'documents': documents,
        'profiles': profile_checks(), 'laws': profile_laws(), 'native_cases': native_checks(), 'attribution': attribution_checks(),
        'alignment': alignment(), 'roundtrips': True, 'prior_declarations_preserved': True,
        'source_attribution_replaced': {'old': 'h3t', 'new': 'h4f', 'earlier_statements_preserved': 12},
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Referenced kinds report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Fixed feature equivalence, coherent kind references and scoped familiarity checked')


if __name__ == '__main__':
    main()
