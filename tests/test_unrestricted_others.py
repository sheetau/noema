from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import pytest
from noema.grammar import parse, format_graph
from scripts.check_unrestricted_others import ROOT, REPORT, PARENT, setup, select, model_for, values, coverage_instance, SOURCE_CASES, SOURCE_POPULATION, k
from scripts.check_rod_setup import guarded


@lru_cache(maxsize=1)
def base(): return setup((ROOT / 'examples/v014/unrestricted-others-core.noema').read_text(encoding='utf-8'), True)


def data(indices=None): return select(base(), indices if indices is not None else tuple(range(7)))


def test_one_compatible_candidate_does_not_establish_nonrestriction():
    item = data((2, 3))
    assert values(item, model_for(item, (True, True, False, False, True, False))) == [True, False]


def test_nonrestriction_does_not_mean_that_there_are_no_duties():
    item = data((0, 3))
    assert values(item, model_for(item)) == [True, True]


def test_nonrestriction_is_not_itself_permission():
    item = data((3, 4, 5))
    assert values(item, model_for(item, permissions=(False, False))) == [True, False, False]


def test_permission_for_one_person_does_not_cover_another():
    item = data((4, 5))
    assert values(item, model_for(item, permissions=(True, False))) == [False, False]
    assert values(item, model_for(item, permissions=(False, True))) == [False, False]


def test_a_second_eligible_activity_also_requires_permission():
    item = data((4, 5))
    assert values(item, model_for(item, variant='second_activity')) == [False, False]


def test_negative_requirements_keep_their_polarity():
    item = data((1, 2, 3))
    assert values(item, model_for(item, (True, True, True, True, True, True))) == [False] * 3


def test_conflicting_requirements_are_not_removed_to_make_a_candidate_fit():
    item = data((0, 1, 2, 3))
    assert values(item, model_for(item, variant='conflicting')) == [True, False, False, False]


@pytest.mark.parametrize('variant', ('other_office', 'other_description', 'other_sign'))
def test_the_catalogue_must_match_the_same_normative_records(variant):
    item = data((0, 2, 3))
    assert values(item, model_for(item, variant=variant)) == [False] * 3


@pytest.mark.parametrize('variant', ('empty_target', 'empty_cases'))
def test_missing_activity_candidates_do_not_establish_nonrestriction(variant):
    item = data((2, 3))
    assert values(item, model_for(item, variant=variant)) == [False, False]


@pytest.mark.parametrize('variant', ('empty_population', 'empty_activities', 'all_excluded'))
def test_a_universal_permission_claim_need_not_have_an_instance(variant):
    item = data((4, 5))
    assert values(item, model_for(item, variant=variant)) == [True, False]


def test_other_means_outside_the_previous_group_not_just_outside_the_speaker():
    item = data(())
    text = format_graph(item['document'], 'compact') + 'r jupermit[a a] c.'
    query = k('rpr', 'p jupopulation', 'p juexcluded', 'p juactivities', 'i[person a activity a][e[n p a b][n p a b]]', 'p jupermit')
    item['document'] = parse(text + 'q[' + query + '].')
    model = model_for(item); model['jupermit'] = lambda person, activity: person != 'earlier'
    assert values(item, model) == [True]
    model['juexcluded'] = lambda person: False
    assert values(item, model) == [False]


def test_an_empty_catalogue_is_not_automatically_a_complete_catalogue():
    item = data((3,)); assert values(item, model_for(item, variant='empty_items')) == [True]
    covered = coverage_instance(base())
    assert values(covered, model_for(covered, variant='empty_items')) == [False]
    assert values(covered, model_for(covered, (False, False, True, False, True, False), variant='empty_items')) == [True]


def test_a_requirement_outside_the_office_roles_is_not_an_office_requirement():
    item = coverage_instance(base()); model = model_for(item); original = model['h7a']
    model['h7a'] = lambda s, p, r, a, d, b, t: original(s, p, r, a, d, b, t) or ((s, p, r, a, b, t) == ('authority', 'person', 'scholar', 'dutya', False, 'anchor') and d.syntax == item['first_syntax'])
    assert values(item, model) == [True]
    model['juofficeroles'] = lambda role: role in ('office', 'otheroffice', 'scholar')
    assert values(item, model) == [False]


def test_catalogued_requirements_must_actually_be_in_the_office_role_scope():
    item = data((0, 2, 3)); model = model_for(item)
    model['juofficeroles'] = lambda role: role == 'scholar'
    assert values(item, model) == [False, False, False]


def test_full_description_quantification_is_not_replaced_by_two_known_descriptions():
    item = data(())
    item['document'] = parse(format_graph(item['document'], 'compact') + 'q[' + item['coverage'] + '].')
    with pytest.raises(ValueError, match='description domain'): values(item, model_for(item))


def test_coverage_can_be_quoted_without_evaluating_the_full_domain():
    item = data((6,))
    assert values(item, guarded(item['document'])) == [True]


def test_unknown_duty_content_is_not_completed_as_a_satisfied_constraint():
    item = data((3,)); model = model_for(item)
    model['jufirst'] = guarded(item['document'])['jufirst']
    with pytest.raises(ValueError, match='Unrelated primitive'): values(item, model)


@lru_cache(maxsize=1)
def public_case():
    from scripts import check_public_divergent_judgments as previous
    source = previous.setup((ROOT / 'examples/v014/kant-unrestricted-others.noema').read_text(encoding='utf-8'))
    doc = deepcopy(source['document']); doc['statements'] = []
    refs = {n: 'p jz' + n for n in ('items', 'issuers', 'actions', 'signs', 'cases')}
    refs.update(person='v person', anchor='k jzanchor[]', officeroles='i[role a][e[v role][k jzoffice[]]]', offices='i[item a][k jzoffice[]]', descriptions='i[item a][r[p jzduty]]',
        trigger='c[' + source['action'] + '][v person v activity]')
    unrestricted = 'i[person a activity a][' + k('hzgz', *(refs[n] for n, _ in SOURCE_CASES)) + ']'
    population = 'i[person a][x[e[v person][k jzperson[]]][e[v person][k juprior[]]]]'
    fields = dict(population=population, excluded='i[person a][e[v person][k juprior[]]]', activities='i[person a activity a][e[v activity][k jzactivity[]]]',
        unrestricted=unrestricted, authority='k jzauthority[]', roles='i[person a][k jzrole[]]', target='r[' + source['action'] + ']', anchor='k jzanchor[]')
    queries = ['c[' + unrestricted + '][k jzperson[] k jzactivity[]]'] + [k(name, *(fields[n] for n, _ in SOURCE_POPULATION)) for name in ('hzg3', 'hzg4')]
    doc = parse(format_graph(doc, 'compact') + 'r juprior[] a.' + ''.join('q[' + q + '].' for q in queries))
    return source | dict(document=doc)


@pytest.mark.parametrize('bits,expected', (
    ((True, True, True, True, True), [True, True, True]),
    ((True, True, False, True, True), [True, False, False]),
    ((True, True, True, True, False), [False, True, False]),
    ((False, True, True, True, True), [False, True, False]),
))
def test_the_same_bound_public_presentation_is_used_for_nonrestriction_and_population_permission(bits, expected):
    from scripts import check_public_divergent_judgments as previous
    item = public_case(); model = previous.model_for(item, bits); model['juprior'] = lambda: 'other'
    assert previous.values(item, model) == expected


def test_saved_evidence_preserves_history_and_limits_the_coverage_claim():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items(): assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-unrestricted-others.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 12
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['interpretation']['coverage']['full_domain_verified'] is False
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
