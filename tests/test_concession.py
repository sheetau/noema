from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_concession import expectation_checks, prior_checks, source_checks, source_alignment
from scripts.compose_concession import ROOT, generic_composed, source_composed


def test_concession_requires_actual_facts_and_nonempty_valid_contrary_expectations():
    result = expectation_checks()
    rows = result['cases']
    assert len(rows) == 256
    assert any(r['concession'] for r in rows)
    for row in rows:
        if row['concession']:
            assert row['premise'][0] and row['conclusion'][0] and any(row['candidates'])
        if not any(row['candidates']):
            assert not row['contrary_expectation']
    assert any(r['premise'][0] and r['conclusion'][0] and not r['concession'] for r in rows)
    assert result['actual_conclusion_cannot_be_contrary_candidate']


def test_prior_time_is_distinct_from_contextually_long_elapsed_time():
    rows = prior_checks()
    assert len(rows) == 7
    assert rows['baseline'] == {'prior': True, 'sufficiently_earlier': True}
    assert rows['not_long_ago'] == {'prior': True, 'sufficiently_earlier': False}
    assert all(not r['prior'] and not r['sufficiently_earlier'] for name, r in rows.items()
        if name not in ('baseline', 'not_long_ago'))


def test_source_preserves_person_perspective_prior_condition_and_population():
    result = source_checks()
    assert len(result['cases']) == 12
    assert [name for name, value in result['cases'].items() if value] == ['baseline']
    assert result['population_connection'] == {'baseline': True, 'still_developmentally_dependent': False}
    alignment = source_alignment()
    assert len(alignment['fragments']) == 2
    assert alignment['developmental_maturity_is_not_actual_intellectual_independence']
    assert 'personification and declaration metaphor' in alignment['remaining']


def test_concession_basis_written_forms_and_unevaluated_quotation():
    for compose, counts in ((generic_composed, (0, 8)), (source_composed, (50, 64))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
    doc['statements'] = []
    quoted = parse(format_graph(doc, 'compact') + '\nq[e[r[k kh[l[a][]]]][r[k kh[l[a][]]]]].')
    def forbidden(*args):
        raise ValueError('Quoted concession evaluated its content')
    primitives = {d['name']: forbidden for d in quoted['declarations'] if d['kind'] == 'primitive'}
    assert evaluate_document(quoted, individuals=('reader',), situations=('text',), primitives=primitives) == [{'kind': 'ask', 'value': True}]
