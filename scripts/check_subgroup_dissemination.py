"""Check population/subgroup quantifier scope with countermodels and native content."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts import check_described_dissemination as closed
from scripts.compose_subgroup_dissemination import ROOT, PARENT, PARENT_BASIS, FULL, CORE, LIBRARY, BASIS, MEANINGS, RENAMES, rename_calls, build

prior = closed.prior
REPORT = ROOT / 'reports/subgroup-dissemination-v1.json'


@lru_cache(maxsize=2)
def group_document(future=False):
    old = prior.group_document('whole' if future else False)
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8'))
    names = {d['name'] for d in doc['declarations']}
    doc['declarations'] += [deepcopy(d) for d in old['declarations'] if d['name'] not in names]
    doc['statements'] = deepcopy(old['statements']) + rename_calls(old['statements'])
    return parse(format_graph(doc, 'compact'))


def population_checks():
    # All membership, subgroup and qualification subsets of three people.
    from scripts.compose_subject_bound_departure import closure
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc, ['rqti'])
    doc = parse(format_graph(doc, 'compact') +
        'r zpoint[] d.r zmembers[a d] c.r zsubgroup[a d] c.r zqualified[a d] c.'
        'q[k rqti[k zpoint[] p zmembers p zsubgroup p zqualified]].')
    people = ('p', 'q', 'r'); count = 0
    for flags in product((False, True), repeat=9):
        groups = [{p for p, flag in zip(people, flags[i:i+3]) if flag} for i in (0, 3, 6)]
        members, subgroup, qualified = groups
        values = {name: (lambda person, point, group=group: person in group)
                  for name, group in zip(('zmembers', 'zsubgroup', 'zqualified'), groups)}
        values['zpoint'] = lambda: 'first'
        expected = len(members & qualified) >= 2 and bool(members & qualified & subgroup)
        assert prior.evaluate(doc, values, people, ('first',)) == [expected], flags
        count += 1
    return dict(subset_combinations=count,external_or_unqualified_subgroup_witness_excluded=True,
                non_subgroup_qualified_witness_not_required=True)


def appointment_checks():
    doc = group_document(); rows = {}
    cases = [
        ('two_guardians', ('p', 'q'), ('p', 'q'), ('p', 'q'), [True, True]),
        ('one_guardian_one_other', ('p', 'q'), ('p',), ('p', 'q'), [False, True]),
        ('one_person', ('p',), ('p',), ('p',), [False, False]),
        ('unqualified_guardian', ('p', 'q', 'r'), ('r',), ('p', 'q'), [False, False]),
        ('guardian_outside_population', ('p', 'q'), ('r',), ('p', 'q', 'r'), [False, False]),
        ('no_guardians', ('p', 'q'), (), ('p', 'q'), [False, False]),
    ]
    for name, members, appointed, qualified, expected in cases:
        values = prior.group_model(doc, members, appointed, qualified)
        actual = prior.evaluate(doc, values, prior.SMALL, prior.TIMES)
        assert actual == expected, (name, actual); rows[name] = actual
    for variant in ('past_only_appointment', 'no_appointment_event', 'nonhuman'):
        actual = prior.evaluate(doc, prior.group_model(doc, variant=variant), prior.SMALL, prior.TIMES)
        assert actual == [False, False], (variant, actual); rows[variant] = actual
    return dict(contrasts=rows,native_appointment_executed_without_lowering=True)


def future_checks():
    doc = group_document(True); rows = {}
    for variant in ('stable', 'turnover', 'missing_late_guardian', 'missing_late_qualification', 'empty'):
        values = prior.group_model(doc, members=('p', 'q', 'r'), appointed=('p',), qualified=('p', 'q'))
        if variant == 'turnover':
            values['zqualified'] = lambda person, point: person in (('p', 'q') if point == 'first' else ('q', 'r'))
            values['cf'] = lambda person, role, point: role == 'role' and person in (
                ('p', 'r') if point == 'past' else ('p',) if point == 'first' else ('r',))
        if variant == 'missing_late_guardian':
            values['cf'] = lambda person, role, point: (person, role) == ('p', 'role') and point in ('past', 'first')
        if variant == 'missing_late_qualification':
            values['zqualified'] = lambda person, point: person == 'p' or (person == 'q' and point == 'first')
        if variant == 'empty': values['zhistory'] = lambda point: point == 'past'
        actual = prior.evaluate(doc, values, prior.SMALL, prior.TIMES)
        assert actual == [False, variant in ('stable', 'turnover')], (variant, actual)
        assert prior.evaluate(doc, values, prior.SMALL, prior.TIMES, diagnostic=True) == actual
        rows[variant] = actual
    return dict(contrasts=rows,eager_and_diagnostic_agree=True,turnover_preserves_same_point_binding=True)


@lru_cache(maxsize=2)
def native_document(attribution=False):
    old = closed.document('both'); doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    names = {d['name'] for d in doc['declarations']}
    doc['declarations'] += [deepcopy(d) for d in old['declarations'] if d['name'] not in names]
    selected = [old['statements'][0 if attribution else 1]]
    doc['statements'] = deepcopy(selected) + rename_calls(selected)
    return parse(format_graph(doc, 'compact'))


def native_checks():
    doc = native_document(); rows = {}
    for variant in ('baseline', 'missing_appointment', 'split_people', 'borrowed_route'):
        values = closed.native_model(doc, variant)
        actual = prior.evaluate(doc, values, diagnostic=True)
        expected = [variant == 'baseline', variant in ('baseline', 'missing_appointment')]
        assert actual == expected, (variant, actual); rows[variant] = actual
    return dict(contrasts=rows,two_native_thinkers_depart_and_transmit=True,
        same_native_qualification_for_guardian_and_non_guardian=True,
        full_future_uses_explicit_short_circuit_diagnostic=True,
        semantic_definitions_not_replaced_with_opaque_predicates=True)


def attribution_checks():
    doc = native_document(True); rows = []
    for older, newer in product((False, True), repeat=2):
        values = closed.attribution_model(doc); seen = []
        def reports(node, author, description, context):
            body = json.loads(description.syntax)
            assert description.rank == 1 and body['kind'] == 'apply' and len(body['arguments']) == 33
            root = body['function']['symbol']; assert root in ('hzop', 'hzov')
            assert (node, author, context) == ('topic', 'authority', 'before')
            seen.append((root, description.syntax))
            return older if root == 'hzop' else newer
        values['hzon'] = reports
        actual = prior.evaluate(doc, values)
        assert actual == [older, newer] and len(seen) == 2 and seen[0][1] != seen[1][1]
        # Apart from the root, the two closed content arguments are identical.
        left, right = (json.loads(item[1]) for item in seen)
        assert left['arguments'] == right['arguments']
        rows.append(actual)
    return dict(independent_candidate_attributions=rows,closed_arguments_unchanged=33,
        unknown_world_facts_not_evaluated=True,not_automatically_treated_as_synonyms=True)


def unknown_checks():
    doc = group_document(); count = 0
    for name in ('zappointed', 'cf', 'zqualified'):
        values = prior.group_model(doc); values[name] = prior.unknown
        for statement in doc['statements']:
            single = dict(doc, statements=[statement])
            try: prior.evaluate(single, values, prior.SMALL, prior.TIMES)
            except ValueError as error: assert 'Unknown' in str(error)
            else: raise AssertionError(name)
            count += 1
    return dict(unknown_inputs_refused=count)


def structure():
    old, new = load_catalog(ROOT, PARENT_BASIS), load_catalog(ROOT, BASIS)
    assert new.document['statements'] == old.document['statements']
    assert new.document['declarations'][:-7] == old.document['declarations']
    for name, entry in old.entries.items(): assert new.entries[name] == entry, name
    for index in (16, 17, 27, 28, 29, 30, 31):
        assert selection_binding(old, [index]) == selection_binding(new, [index])
    return dict(new_definitions=7,new_primitives=0,existing_statements=32,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs = build()
    for name, body in outputs.items(): assert (ROOT/name).read_text(encoding='utf-8') == body, name
    for name in (FULL, CORE, LIBRARY):
        doc = parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    previous = json.loads((ROOT/'reports/described-dissemination-v1.json').read_text(encoding='utf-8'))
    for path, sha in previous['source_sha256'].items(): assert digest((ROOT/path).read_bytes()) == sha, path
    alignment = deepcopy(previous['alignment'])
    for row in alignment['segments']:
        row.update(definitions=list(MEANINGS),status='partial_alternative_population_subgroup_scope',
            remaining=['reading choice, scalar background and contextual time range', 'author attribution and whole-unit meaning'])
    paths = set(load_catalog(ROOT, BASIS).source_sha256) | set(outputs) | set(previous['source_sha256']) | {
        'reports/described-dissemination-v1.json', 'scripts/compose_subgroup_dissemination.py',
        'scripts/check_subgroup_dissemination.py', 'tests/test_subgroup_dissemination.py', 'docs/subgroup-dissemination-v1.md'}
    result = {}
    for label, check in [('population', population_checks), ('appointment', appointment_checks), ('future', future_checks),
                         ('native', native_checks), ('attribution', attribution_checks), ('unknown', unknown_checks), ('structure', structure)]:
        result[label] = check(); print(label + ' checked', flush=True)
    return dict(status='explicit_reading_alternative_not_whole_unit_completion',document=FULL,**result,
        roundtrips=True,alignment=alignment,new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli = argparse.ArgumentParser(); cli.add_argument('--verify-only', action='store_true'); args = cli.parse_args()
    report = build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('Population/subgroup scope checked without changing historical readings', flush=True)


if __name__ == '__main__':
    main()
