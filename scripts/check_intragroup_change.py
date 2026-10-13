"""Check cross-member causal activities without universal group success."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_self_achievement import source_model as achievement_model
from scripts.compose_intragroup_change import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/intragroup-change-v1.json'


def generic_checks():
    doc = parse(generic_composed()[0] + '''
r za[d] c.r zb[d d] c.r zc[a] c.r zd[] a.r ze[] a.r zf[] a.r zg[] a.r zh[] d.r zi[] d.
r zj[a d] c.r zk[a] e.r zl[a] e.r zm[a d d] c.r zn[a a d d] c.r zo[a d] c.
r zp[a a d] c.r zq[a a d] c.r zr[a a i[h[a] e] d] c.
q[k rda[p za p zb p zc k zd[] k ze[] k zf[] k zg[] k zh[] k zi[] p zj p zk p zl r[p zl] p zm p zn p zo p zp p zq p zr]].''')
    domain = ('actor', 'target', 'process', 'part', 'other')
    scenes = ('before', 'after', 'outside')
    baseline_state = (True, True, True, False, False, True)
    def run(state=baseline_state, actions=(True,) * 9, variant='baseline'):
        assessed_before, assessed_after, prior_before, prior_after, goal_before, goal_after = state
        actor_member, target_member, changes, affected, process_occurs, part_occurs, partof, participates, produces = actions
        actor = 'target' if variant == 'same_person' else 'actor'
        part = 'process' if variant == 'whole_as_part' else 'part'
        def match(actual, expected, relation, fields):
            expected = list(expected)
            for i, field in enumerate(fields):
                if variant == relation + '_' + field:
                    expected[i] = 'outside' if field in ('start', 'end') else 'zk' if field == 'description' else 'other'
            return tuple(actual) == tuple(expected)
        model = {
            'za': lambda point: point in scenes[:2] and variant != 'empty_history' and not (
                variant == 'missing_start' and point == 'before' or variant == 'missing_end' and point == 'after'),
            'zb': lambda first, last: (first, last) == ('before', 'after') or variant == 'cyclic_history' and (first, last) == ('after', 'before'),
            'zc': lambda person: person == actor and actor_member or person == 'target' and target_member,
            'zd': lambda: actor, 'ze': lambda: 'target', 'zf': lambda: 'process', 'zg': lambda: part,
            'zh': lambda: 'before', 'zi': lambda: 'after',
            'zj': lambda who, point: who == ('other' if variant == 'assessment_target' else 'target') and (
                point == 'before' and assessed_before or point == 'after' and assessed_after),
            'zk': lambda who: Content(scenes, (prior_before, prior_after, False) if who == 'target' else (False,) * 3),
            'zl': lambda who: Content(scenes, (goal_before, goal_after, False) if who == 'target' else (False,) * 3),
            'zm': lambda act, first, last: changes and match((act, first, last), ('process', 'before', 'after'), 'change', ('process', 'start', 'end')),
            'zn': lambda who, act, first, last: affected and match((who, act, first, last), ('target', 'process', 'before', 'after'),
                'affected', ('target', 'process', 'start', 'end')),
            'zo': lambda act, point: process_occurs and (act, point) == ('process', 'after') or part_occurs and (act, point) == (part, 'after'),
            'zp': lambda who, act, point: participates and match((who, act, point), (actor, part, 'after'), 'participates', ('actor', 'part', 'end')),
            'zq': lambda act, process, point: partof and match((act, process, point), (part, 'process', 'after'), 'partof', ('part', 'process', 'end')),
            'zr': lambda act, who, desc, point: produces and match((act, who, symbol(desc), point), (part, 'target', 'zl', 'after'),
                'produces', ('part', 'target', 'description', 'end'))}
        return values(doc, model, domain, scenes)
    accepted_states = 0
    for flags in product((False, True), repeat=6):
        result = run(state=flags)
        if result != [flags == baseline_state]:
            raise ValueError('Unassessed or unchanged capacity accepted')
        accepted_states += result[0]
    accepted_actions = 0
    for flags in product((False, True), repeat=9):
        result = run(actions=flags)
        if result != [all(flags)]:
            raise ValueError('Mere membership or unrelated activity accepted')
        accepted_actions += result[0]
    variants = ['same_person', 'empty_history', 'missing_start', 'missing_end', 'cyclic_history', 'assessment_target']
    for relation, fields in (('change', ('process', 'start', 'end')), ('affected', ('target', 'process', 'start', 'end')),
            ('participates', ('actor', 'part', 'end')), ('partof', ('part', 'process', 'end')),
            ('produces', ('part', 'target', 'description', 'end'))):
        variants += [relation + '_' + field for field in fields]
    rows = {}
    for variant in variants + ['whole_as_part']:
        actual = run(variant=variant)
        if actual != [variant == 'whole_as_part']:
            raise ValueError('Internal change binding failed: ' + variant)
        rows[variant] = actual
    return {'state_cases': 64, 'accepted_states': accepted_states, 'activity_cases': 512,
        'accepted_activities': accepted_actions, 'binding_and_history_cases': rows}


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] a.r zc[] d.r zd[] d.r ze[] d.r zf[] j[a].
r zg[] a.r zh[] a.r zi[] a.
q[k h6b[k za[] k zg[] k zh[] k zb[] k zi[] k zc[] k zd[] k ze[]]].
q[k h6c[k za[] k zb[] k zc[] k zd[] k ze[]]].''')
    domain = ('other', 'person', 'part', 'process', 'faculty', 'plan', 'group', 'outsider', 'object')
    scenes = ('before', 'end', 'anchor')
    variants = ('baseline', 'external_assistance', 'whole_as_part', 'outside_actor', 'outside_target', 'single_person',
        'unrelated_part', 'no_change', 'other_person_changed', 'guided_outcome', 'unassessed_before', 'unassessed_after',
        'already_capable', 'no_internal_participation', 'no_result', 'wrong_result_description', 'different_part_result',
        'future_achievement', 'nonhuman_member', 'duplicate_member')
    rows = {}
    for variant in variants:
        model = achievement_model(doc, variant)
        end = 'anchor' if variant == 'future_achievement' else 'end'
        actor = 'person' if variant == 'single_person' else 'other'
        part = 'process' if variant == 'whole_as_part' else 'part'
        members = ('person',) if variant in ('outside_actor', 'single_person') else ('other',) if variant == 'outside_target' else (
            ('person', 'other', 'object') if variant == 'nonhuman_member' else ('person', 'other', 'other') if variant == 'duplicate_member' else ('person', 'other'))
        old_occurs, old_participates = model['dg'], model['df']
        model.update(za=lambda: 'group', zg=lambda: actor, zh=lambda: 'person', zi=lambda: part,
            mp=lambda group: SequenceValue(members if group == 'group' else (), '"individual"'),
            h6a=lambda activity, process, point: (activity, process, point) == (
                'object' if variant == 'unrelated_part' else part, 'process', end),
            dg=lambda activity, point: old_occurs(activity, point) or (activity, point) == (part, end),
            df=lambda who, activity, point: old_participates(who, activity, point) or (
                variant != 'no_internal_participation' and (who, activity, point) == (actor, part, end)) or (
                variant == 'external_assistance' and (who, activity, point) == ('outsider', part, end)),
            g3=lambda activity, target, desc, point: variant != 'no_result' and (activity, target, symbol(desc), point) == (
                'object' if variant == 'different_part_result' else part, 'person',
                'bf' if variant == 'wrong_result_description' else 'h4l', end))
        actual = [row['value'] for row in evaluate_document(doc, individuals=domain, situations=scenes, primitives=model,
            max_steps=32_000_000, memoize_definitions=True, memoize_expressions=True)]
        expected = variant in ('baseline', 'external_assistance', 'whole_as_part')
        if actual != [expected, expected]:
            raise ValueError('Native internal change differs: ' + str((variant, actual)))
        rows[variant] = actual
    return {'cases': rows, 'other_group_members_need_not_acquire_capacity': True,
        'public_classification_and_modal_claim_not_asserted': True}


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0011')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source unit changed')
    start = text.index('sich selbst aufkläre')
    end = start + len('sich selbst aufkläre')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': end,
        'source': text[start:end], 'definitions': ['h6b', 'h6c', 'h6d'], 'status': 'partial_explicit_reading',
        'full_semantic_equivalence': False,
        'remaining': ['public audience and shared discourse', 'group-wide development and dissemination of reasoned self-assessment',
            'eher possible comparison', 'freedom condition and near inevitability', 'collective identity, causation and source equivalence']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'intragroup-change'), (source_composed, 'kant-intragroup-change')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored intragroup change differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Intragroup change roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/intragroup-change-basis-v1.json', 'data/kant-intragroup-change-basis-v1.json',
        'scripts/compose_intragroup_change.py', 'scripts/check_intragroup_change.py', 'scripts/check_self_achievement.py',
        'noema/discourse.py', 'noema/finite_semantics.py', 'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_internal_participation_in_capacity_change_not_public_enlightenment',
        'documents': documents, 'generic': generic_checks(), 'source_cases': source_checks(), 'alignment': alignment(),
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
            raise ValueError('Intragroup change report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Same group, distinct people, one change and causal activity parts checked')


if __name__ == '__main__':
    main()
