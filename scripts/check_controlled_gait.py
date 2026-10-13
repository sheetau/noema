"""Check full-episode positive control and keep gait separate from independence."""
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
from scripts.check_self_achievement import source_model as achievement_model
from scripts.compose_controlled_gait import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/controlled-gait-v1.json'


def generic_checks():
    doc = parse(generic_composed()[0] + '''r za[d] c.r zb[d d] c.r zc[d] c.r zd[] a.r ze[] a.r zf[] d.
r zg[a d] c.r zh[a a d] c.r zi[a a d] c.r zj[a a d] c.
q[k rcq[p za p zb p zc k zd[] k ze[] k zf[] p zg p zh p zi p zj]].''')
    domain, scenes = ('person', 'act', 'other'), ('start', 'middle', 'end', 'future', 'outside')
    def run(flags, variant='baseline'):
        balance, placement, occurs, walk = flags[:3], flags[3:6], flags[6], flags[7]
        def phase(point):
            if variant == 'empty':
                return False
            if variant == 'singleton':
                return point == 'end'
            return point in scenes[:3] and not (variant == 'omitted_middle' and point == 'middle') and not (
                variant == 'missing_end' and point == 'end') or variant == 'past_completion' and point == 'future'
        def control(who, act, point, pattern, name):
            return ((who, act) == ('other' if variant == name + '_person' else 'person', 'other' if variant == name + '_act' else 'act')
                and point in scenes[:3] and pattern[scenes.index(point)])
        model = {'za': lambda point: point != 'outside' and not (variant == 'foreign_middle' and point == 'middle'),
            'zb': lambda first, last: scenes.index(first) < scenes.index(last) or variant == 'cycle' and (first, last) == ('end', 'start'),
            'zc': phase, 'zd': lambda: 'person', 'ze': lambda: 'act', 'zf': lambda: 'end',
            'zg': lambda act, point: occurs and (act, point) == ('other' if variant == 'occurs_act' else 'act',
                'middle' if variant == 'occurs_point' else 'end'),
            'zh': lambda who, act, point: walk and (who, act, point) == ('other' if variant == 'walk_person' else 'person',
                'other' if variant == 'walk_act' else 'act', 'middle' if variant == 'walk_point' else 'end'),
            'zi': lambda who, act, point: control(who, act, point, balance, 'balance'),
            'zj': lambda who, act, point: control(who, act, point, placement, 'placement')}
        return values(doc, model, domain, scenes)
    accepted = 0
    for flags in product((False, True), repeat=8):
        actual = run(flags)
        if actual != [all(flags)]:
            raise ValueError('Endpoints or absence of failure substituted for full control')
        accepted += actual[0]
    variants = ('empty', 'singleton', 'omitted_middle', 'missing_end', 'past_completion', 'foreign_middle', 'cycle',
        'occurs_act', 'occurs_point', 'walk_person', 'walk_act', 'walk_point',
        'balance_person', 'balance_act', 'placement_person', 'placement_act')
    contrasts = {}
    for variant in variants:
        actual = run((True,) * 8, variant)
        if actual != [False]:
            raise ValueError('Gait interval or participant mismatch accepted: ' + variant)
        contrasts[variant] = actual
    return {'truth_cases': 256, 'accepted_truth_cases': accepted, 'scope_and_binding_cases': contrasts}


def general_laws():
    text = generic_composed()[0] + '''r za[d] c.r zb[d d] c.r zc[d] c.r zd[] a.r ze[] a.r zf[] d.r zk[] d.
r zg[a d] c.r zh[a a d] c.r zi[a a d] c.r zj[a a d] c.r zl[a a d] c.'''
    def episode(last):
        return f'k rcq[p za p zb p zc k zd[] k ze[] k {last}[] p zg p zh p zi p zj]'
    body = episode('zf')
    end_control = 'w[k zi[k zd[] k ze[] k zf[]]][k zj[k zd[] k ze[] k zf[]]]'
    controls = 'f point d[y[k zc[v point]][w[k zi[k zd[] k ze[] v point]][k zj[k zd[] k ze[] v point]]]]'
    completion = 'f point d[y[k zc[v point]][x[e[v point][k zf[]]][k zb[v point k zf[]]]]]'
    structure = ('w[k tb[p za p zc p zb]][w[k zc[k zf[]]][w[k zc[k zk[]]][w[k zb[k zk[] k zf[]]][w['
        + completion + '][w[k zg[k ze[] k zf[]]][k zh[k zd[] k ze[] k zf[]]]]]]]]')
    claims = {
        'completed_episode_has_control_at_endpoint': f'y[{body}][{end_control}]',
        'completed_episode_has_control_everywhere_in_scope': f'y[{body}][{controls}]',
        'completed_episode_has_no_phase_after_completion': f'y[{body}][{completion}]',
        'same_episode_has_unique_completion': f'y[w[{body}][{episode("zk")} ]][e[k zf[]][k zk[]]]',
        'two_controlled_endpoints_are_enough': 'y[w[' + structure + '][w[' + end_control +
            '][w[k zi[k zd[] k ze[] k zk[]]][k zj[k zd[] k ze[] k zk[]]]]]][' + body + ']',
        'no_fall_is_enough': 'y[w[' + structure + '][f point d[y[k zc[v point]][u[k zl[k zd[] k ze[] v point]]]]]][' + body + ']',
    }
    results = verify(parse(text + ''.join(f's[{formula}].' for formula in claims.values())))
    if [row['status'] for row in results] != ['valid'] * 4 + ['invalid'] * 2:
        raise ValueError('Full-episode control laws failed')
    return {name: {'status': row['status'], 'countermodel_found': row['countermodel'] is not None,
        'formula_sha256': hashlib.sha256(row['formula'].encode()).hexdigest()} for name, row in zip(claims, results, strict=True)}


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] a.r zc[] d.r zd[] d.r ze[] d.r zf[] j[a].r zg[] a.r zh[] d.
q[k h4y[k za[] k zg[] k zh[] k ze[]]].q[t[k h4z[k za[]]][k ze[]]].q[t[k h4q[k za[]]][k ze[]]].''')
    domain = ('person', 'other', 'process', 'faculty', 'plan', 'gait')
    scenes = ('before', 'middle', 'end', 'anchor')
    variants = ('baseline', 'external_support', 'no_achievement', 'no_walk', 'no_balance', 'middle_unbalanced',
        'middle_uncontrolled_placement', 'empty_scope', 'singleton_scope', 'omitted_middle', 'wrong_scope_act',
        'wrong_scope_completion', 'phase_after_completion', 'future_completion', 'other_person_balance', 'other_act_placement')
    rows = {}
    for variant in variants:
        end = 'anchor' if variant == 'future_completion' else 'end'
        anchor = 'end' if variant == 'future_completion' else 'anchor'
        model = achievement_model(doc, 'no_self_work' if variant == 'no_achievement' else 'baseline')
        old_occurs = model['dg']
        def phase(act, last, point):
            if variant == 'empty_scope':
                return False
            if (act, last) != ('process' if variant == 'wrong_scope_act' else 'gait',
                    'anchor' if variant == 'wrong_scope_completion' else end):
                return False
            if variant == 'singleton_scope':
                return point == end
            return (point in scenes[:3] or point == 'anchor' and variant in ('phase_after_completion', 'future_completion')) and not (
                variant == 'omitted_middle' and point == 'middle')
        model.update(zg=lambda: 'gait', zh=lambda: end, ze=lambda: anchor,
            ia=lambda who, ctx, point: who in ('person', 'other') and point in scenes,
            ic=lambda first, last, ctx: scenes.index(first) < scenes.index(last),
            dg=lambda act, point: old_occurs(act, point) or (act, point) == ('gait', end),
            zai=lambda who, act, point: variant != 'no_walk' and (who, act, point) == ('person', 'gait', end),
            zaj=lambda who, act, point: variant == 'external_support' and (who, act, point) == ('person', 'gait', end),
            h4v=lambda who, act, point: variant != 'no_balance' and (who, act) ==
                ('other' if variant == 'other_person_balance' else 'person', 'gait') and not (
                    variant == 'middle_unbalanced' and point == 'middle'),
            h4w=lambda who, act, point: (who, act) == ('person', 'process' if variant == 'other_act_placement' else 'gait')
                and not (variant == 'middle_uncontrolled_placement' and point == 'middle'), h4x=phase)
        actual = values(doc, model, domain, scenes)
        expected = [True, True, variant != 'no_achievement'] if variant in ('baseline', 'external_support', 'no_achievement') else [False, False, True]
        if actual != expected:
            raise ValueError('Gait mixed with independence, support or other phases: ' + str((variant, actual)))
        rows[variant] = actual
    return rows


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0010')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source unit changed')
    start = text.index('einen sicheren Gang zu thun')
    end = start + len('einen sicheren Gang zu thun')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': end, 'source': text[start:end],
        'definitions': ['h4y', 'h4z'], 'status': 'partial_explicit_reading', 'full_semantic_equivalence': False,
        'remaining': ['biomechanics and scope completeness', 'full meanings of secure gait', 'stable intellectual activity as metaphor target',
            'dennoch concession and Daher inference', 'final counting of people satisfying the complete conclusion']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'controlled-gait'), (source_composed, 'kant-controlled-gait')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored controlled gait differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Gait roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/controlled-gait-basis-v1.json', 'data/kant-controlled-gait-basis-v1.json',
        'scripts/compose_controlled_gait.py', 'scripts/check_controlled_gait.py', 'scripts/check_self_achievement.py',
        'noema/discourse.py', 'noema/finite_semantics.py', 'noema/first_order_proofs.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_controlled_gait_depiction_not_intellectual_achievement', 'documents': documents,
        'generic': generic_checks(), 'general_laws': general_laws(), 'source_cases': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0,
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
            raise ValueError('Controlled gait report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Positive whole-episode gait control and separation from independence checked')


if __name__ == '__main__':
    main()
