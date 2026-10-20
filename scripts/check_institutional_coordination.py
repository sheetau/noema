"""Check fixed participants, instrumental alternatives and nonfactive requirements."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_institutional_coordination import (
    ROOT, LIBRARY, BASIS, MEANINGS, OUTCOME, build, parent)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/institutional-coordination-v1.json'
DOC = 'docs/institutional-coordination-v1.md'
PRIOR = 'reports/use-definitions-v1.json'
DOMAIN = ('one', 'two', 'three', 'community', 'government', 'work', 'arrangement',
          'mechanism', 'normsource', 'roleone', 'roletwo', 'other')
SCENES = ('reference', 'future', 'other')
GROUP_ARGS = 'p zpeople k zcommunity[] k zreference[] p zhuman p zmember'
RESULT_ARGS = ('p zpeople k zcommunity[] k zgovernment[] k zwork[] k zarrangement[] '
               'r[k zgoal[]] k zreference[] p zhuman p zmember p zdirects p zprevents')
COORD_ARGS = RESULT_ARGS + ' k zmechanism[] p zgoverning p zcoordinated p zartificial p zsupplies'
REQUIRE_ARGS = (GROUP_ARGS + ' k zmechanism[] k zwork[] k zsource[] p zroles p zassigned '
                'r[p zpassive] p h7k')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture():
    doc = deepcopy(catalog().document)
    # The existing primitive is passed with its unchanged native type.
    doc['declarations'].append(deepcopy(parent().entries['h7k']['declaration']))
    extra = '''
r zpeople[a] c.r zhuman[a] c.r zmember[a a d] c.
r zcommunity[] a.r zgovernment[] a.r zwork[] a.r zarrangement[] a.
r zmechanism[] a.r zsource[] a.r zreference[] d.r zpoint[] d.
r zgoal[] e.r zactual[] c.
d zpassive[bindings j[a]] e[b point[k zactual[]]].
r zgoverning[a a d] c.r zcoordinated[a h[a] c a d] c.
r zartificial[a a d] c.r zsupplies[a a a d] c.
r zroles[a] a.r zassigned[a a a a d] c.
''' + 'r zdirects' + OUTCOME[1:] + '.r zprevents' + OUTCOME[1:] + '.'
    queries = ('q[k r2zn[' + GROUP_ARGS + ']].'
               'q[k r2zp[' + RESULT_ARGS + ' k zpoint[]]].'
               'q[k r2zq[' + COORD_ARGS + ' k zpoint[]]].'
               'q[t[k r2zr[' + COORD_ARGS + ']][k zpoint[]]].'
               'q[k r2zs[' + REQUIRE_ARGS + ']].')
    return parse(format_graph(doc, 'compact') + extra + queries)


def model(flags=(True, False, False, True), variant='baseline', selected=('one', 'two')):
    doc = fixture()
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    people = set(selected)
    roles = dict(one='roleone', two='roletwo')
    v.update(zcommunity=lambda: 'community', zgovernment=lambda: 'government',
             zwork=lambda: 'work', zarrangement=lambda: 'arrangement',
             zmechanism=lambda: 'mechanism', zsource=lambda: 'normsource',
             zreference=lambda: 'reference', zpoint=lambda: 'future',
             zpeople=lambda p: p in people,
             zhuman=lambda p: p in {'one', 'two', 'three'} and not (variant == 'nonhuman' and p == 'two'),
             zmember=lambda p, c, s: p in {'one', 'two', 'three'} and (c, s) == (
                 'other' if variant == 'other_community_membership' else 'community',
                 'future' if variant == 'membership_only_at_result' else 'reference'),
             zroles=lambda p: roles.get(p, 'other'))

    def outcome(side, government, person, work, arrangement, goal, point):
        expected = ('other' if variant == 'other_government' else 'government',
                    'other' if variant == 'other_work' else 'work',
                    'other' if variant == 'other_arrangement' else 'arrangement',
                    'zpassive' if variant == 'other_goal' else 'zgoal',
                    'reference' if variant == 'result_at_reference_only' else 'future')
        offset = {'one': 0, 'two': 2}.get(person)
        return offset is not None and flags[offset + side] and (
            government, work, arrangement, symbol(goal), point) == expected

    def coordinated(arrangement, members, work, point):
        actual_members = {p for p in DOMAIN if members(p)}
        wanted = {'one'} if variant == 'only_successful_member_coordinated' else people
        return variant != 'no_coordination' and actual_members == wanted and (
            arrangement, work, point) == ('arrangement', 'work', 'future')

    def required(source, person, role, code, bindings, polarity, reference):
        return variant != 'no_requirement' and person in roles and (
            source, role, symbol(code), code.rank, tuple(bindings.items), polarity, reference) == (
            'government' if variant == 'source_is_not_mechanism_or_government' else 'normsource',
            roles[person], 'zgoal' if variant == 'wrong_required_content' else 'zpassive', 0,
            (roles[person], person, 'work') if variant == 'reversed_binding_order' else (
                person, roles[person], 'other' if variant == 'requirement_for_other_work' else 'work'),
            False if variant == 'negative_requirement' else True,
            'future' if variant == 'requirement_only_at_result' else 'reference')

    v.update(zdirects=lambda *args: outcome(0, *args),
             zprevents=lambda *args: outcome(1, *args),
             zgoverning=lambda g, c, s: (g, c, s) == (
                 'government', 'other' if variant == 'governs_other_community' else 'community', 'reference'),
             zcoordinated=coordinated,
             zartificial=lambda a, w, s: variant != 'spontaneous_only' and (a, w, s) == (
                 'arrangement', 'work', 'future'),
             zsupplies=lambda m, a, w, s: (m, a, w, s) == (
                 'other' if variant == 'other_mechanism' else 'mechanism',
                 'other' if variant == 'other_supplied_arrangement' else 'arrangement', 'work', 'future'),
             zassigned=lambda p, r, m, w, s: p in roles and (r, m, w, s) == (
                 'other' if variant == 'other_assigned_role' else roles.get(p),
                 'other' if variant == 'other_assignment_mechanism' else 'mechanism',
                 'other' if variant == 'other_assignment_work' else 'work', 'reference'),
             h7k=required)
    return v


@lru_cache(None)
def alternatives_checks():
    rows = []
    for flags in product((False, True), repeat=4):
        expected = (flags[0] or flags[1]) and (flags[2] or flags[3])
        values = evaluate(fixture(), model(flags), DOMAIN, SCENES, True)
        assert values == [True, expected, expected, expected, True], (flags, values)
        rows.append(dict(two_person_direction_prevention_flags=list(flags), values=values))
    for selected, expected in [((), [False] * 5),
                               (('one',), [True] * 5),
                               (('one', 'two', 'three'), [True, False, False, False, False])]:
        actual = evaluate(fixture(), model(selected=selected), DOMAIN, SCENES, True)
        assert actual == expected, (selected, actual)
    return dict(combinations=rows, empty_group_refused=True, mixed_outcomes_accepted=True,
                unselected_community_member_need_not_succeed=True,
                extra_selected_member_cannot_be_ignored=True, truth_of_goal_not_executed=True)


@lru_cache(None)
def binding_checks():
    groups = [
        (('nonhuman', 'other_community_membership', 'membership_only_at_result'), [False] * 5),
        (('other_government', 'other_work', 'other_arrangement', 'other_goal', 'result_at_reference_only'),
         [True, False, False, False, True]),
        (('only_successful_member_coordinated', 'no_coordination', 'governs_other_community',
          'spontaneous_only', 'other_mechanism', 'other_supplied_arrangement'),
         [True, True, False, False, True]),
        (('no_requirement', 'source_is_not_mechanism_or_government', 'wrong_required_content',
          'reversed_binding_order', 'requirement_for_other_work', 'negative_requirement',
          'requirement_only_at_result', 'other_assigned_role', 'other_assignment_mechanism',
          'other_assignment_work'), [True, True, True, True, False]),
    ]
    rows = {}
    for variants, expected in groups:
        for variant in variants:
            actual = evaluate(fixture(), model(variant=variant), DOMAIN, SCENES, True)
            assert actual == expected, (variant, actual)
            rows[variant] = actual
    names = ('zpeople', 'zhuman', 'zmember', 'zdirects', 'zprevents', 'zgoverning',
             'zcoordinated', 'zartificial', 'zsupplies', 'zroles', 'zassigned', 'h7k')
    for name in names:
        values = model(); values[name] = unknown
        try:
            evaluate(fixture(), values, DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    # Goal truth and fulfilment deliberately remain unknown throughout the successful cases.
    assert model()['zgoal'] is unknown and model()['zactual'] is unknown
    quoted = deepcopy(fixture())
    quoted['statements'] = []
    quoted = parse(format_graph(quoted, 'compact') +
                   'd zclosed[] e[k r2zr[' + COORD_ARGS + ']].'
                   'q[e[r b[k zclosed[]]][r b[k zclosed[]]]].')
    assert evaluate(quoted, {d['name']: unknown for d in quoted['declarations']
                             if d['kind'] == 'primitive'}, DOMAIN, SCENES, True) == [True]
    return dict(contrasts=rows, unknown_input_rejections=len(names),
                requirement_not_fulfilment=True, normative_source_not_invented=True,
                description_rank_preserved=True, rank_one_target_quote_does_not_execute_inputs=True,
                semantic_boundaries=[
                    'All input relations use explicit finite fixture interpretations.',
                    'Required property is a native closed test description; passive conduct remains to be composed.',
                    'No source-sentence equivalence or factual government action is established.'])


@lru_cache(None)
def structure_checks():
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    assert set(catalog().entries) == set(MEANINGS)
    assert not catalog().document['statements']
    assert not set(MEANINGS) & set(parent().entries)
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    doc = catalog().document
    for notation in ('compact', 'full'):
        text = format_graph(doc, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(new_definitions=len(MEANINGS), new_primitives=0, roundtrips=True,
                unchanged_active_manuscript=True, new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('alternatives', alternatives_checks), ('bindings', binding_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(parent().source_sha256) | {
        PRIOR, DOC, 'scripts/compose_institutional_coordination.py',
        'scripts/check_institutional_coordination.py', 'tests/test_institutional_coordination.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/compose_qualitative_influence.py', 'scripts/compose_grounded_step.py'}
    return dict(status='institutional_coordination_dependency_group_not_sentence_review',
                document=LIBRARY, **results, whole_sentence_semantically_verified=False,
                whole_unit_semantically_verified=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
