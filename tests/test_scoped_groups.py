import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_scoped_groups import (
    agency_checks, alignment, attribution_checks, coverage_checks, inclusion_checks, source_checks, values,
)
from scripts.compose_scoped_groups import ROOT, generic_composed, source_composed


def test_entire_included_class_is_nonempty_and_within_population_and_selection():
    rows = inclusion_checks()
    assert len(rows) == 64
    assert all(row['included'] for row in rows if row['valid'])
    assert all(set(row['included']) <= set(row['population']) & set(row['selected'])
               for row in rows if row['valid'])
    assert any(set(row['included']) & set(row['selected']) and not row['valid'] for row in rows)


def test_collective_coverage_does_not_require_every_actor_for_every_target():
    result = coverage_checks()
    assert json.loads(json.dumps(result)) == result
    rows = result['cases']
    assert len(rows) == 16
    assert sum(row['valid'] for row in rows) == 7
    assert any(row['valid'] and not row['all_pairs'] for row in rows)
    assert not any(result['empty_scopes'].values())


def test_shared_agency_does_not_combine_unrelated_events():
    rows = agency_checks()
    assert json.loads(json.dumps(rows)) == rows
    assert len(rows) == 64
    split = next(row for row in rows if row['occurs'] == ['one', 'two']
                 and row['participation'] == [['a', 'one'], ['b', 'two']])
    assert not split['shared_activity']
    assert all(row['occurs'] for row in rows if row['shared_activity'])


def test_empty_actor_group_and_identical_label_are_rejected():
    doc = parse(generic_composed()[0] + '''
r za[] a.r zb[] a.r zc[] d.r zd[a a i[h[a] e] i[h[a] e] d] c.
r ze[a] c.r zf[a d] c.r zg[a a d] c.
d zh[person a] e[b scene[e[v person][v person]]].
d zi[person a] e[b scene[u[e[v person][v person]]]].
q[k rr[p ze k zc[] p zf p zg]].
q[k rq[k za[] k zb[] r[p zh] r[p zh] k zc[] p zd]].
q[k rq[k za[] k zb[] r[p zh] r[p zi] k zc[] p zd]].
''')
    model = {'za': lambda: 'node', 'zb': lambda: 'author', 'zc': lambda: 'context',
             'zd': lambda *args: True, 'ze': lambda *args: False,
             'zf': lambda *args: True, 'zg': lambda *args: True}
    assert values(doc, model, ('node', 'author'), ('context',)) == [False, False, True]


def test_source_covers_women_and_collective_roles_without_making_danger_actual():
    rows = source_checks()
    assert len(rows) == 20
    assert rows['baseline']['causal_claim_content'] and not rows['baseline']['actual_danger']
    assert rows['actual_danger']['causal_claim_content'] and rows['actual_danger']['actual_danger']
    assert not rows['female_not_judging']['included_class_and_large_share']
    assert not rows['female_outside_population']['included_class_and_large_share']
    assert not rows['uncovered_target']['collective_role']
    assert not rows['irrelevant_guard']['collective_role']
    assert not rows['wrong_assumption_act']['individual_role']
    assert not rows['claimed_only']['individual_role']
    assert not rows['separate_activities']['shared_activity']
    assert not rows['danger_instead_of_judgment']['causal_claim_content']


def test_attribution_never_evaluates_gender_beauty_danger_or_causal_claims():
    rows = attribution_checks()
    assert len(rows) == 8
    assert rows['baseline']['statements'] == [True]*8
    assert all(row['statements'][:6] == [True]*6 for row in rows.values())
    assert all(not row['underlying_contents_evaluated'] for row in rows.values())
    assert [name for name, row in rows.items() if all(row['statements'])] == ['baseline']


def test_sentence_alignment_remains_partial_with_unrepresented_qualifiers():
    row = alignment()
    assert len(row['segments']) == 4
    assert all(s['status'] == 'partial_explicit_reading' for s in row['segments'])
    assert row['segments'][1]['source'].startswith('(darunter')
    assert row['segments'][-1]['source'].startswith(': dafür')
    assert not row['full_semantic_equivalence']
    assert 'gutigst irony and degree' in row['remaining']


def test_group_basis_roundtrips_and_original_script():
    for compose, counts in ((generic_composed, (0, 4)), (source_composed, (117, 151))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            formatted = format_graph(doc, notation)
            assert parse(formatted) == parse(decode(encode(formatted, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
