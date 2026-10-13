from copy import deepcopy
from itertools import product
import json

import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse
from noema.linking import link_documents, project_document
from noema.semantics import SemanticError


def test_collisions_do_not_identify_unrelated_primitives_or_equal_aliases():
    source = parse('n:r aa[] a.d ab[] a[k aa[]].d ac[] a[k aa[]].q[e[r[p ab]][r[p ac]]].')
    original = deepcopy(source)
    linked = link_documents({'one': source, 'two': source})
    assert source == original
    assert len(linked.document['declarations']) == 6
    assert linked.symbols['one'] == {'aa': 'aa', 'ab': 'ab', 'ac': 'ac'}
    assert set(linked.symbols['one'].values()).isdisjoint(linked.symbols['two'].values())
    for label in ('one', 'two'):
        assert project_document(linked, label) == source
    assert linked == link_documents({'one': source, 'two': source})


def test_explicit_sharing_reuses_only_verified_structure_and_projects_exactly():
    first = parse('n:r aa[] a.d ab[] a[k aa[]].q[e[k ab[]][k aa[]]].')
    second = parse('n:r bb[] a.d bc[] a[k bb[]].q[e[k bc[]][k bb[]]].')
    linked = link_documents({'one': first, 'two': second}, shared={'two': {'bb': ('one', 'aa'), 'bc': ('one', 'ab')}})
    assert len(linked.document['declarations']) == 2
    assert len(linked.document['statements']) == 2
    assert project_document(linked, 'one') == first
    assert project_document(linked, 'two') == second


def test_independent_same_spelling_retains_all_four_truth_assignments():
    source = parse('n:r aa[] c.q[k aa[]].')
    linked = link_documents({'one': source, 'two': source})
    for first, second in product((False, True), repeat=2):
        model = {linked.symbols['one']['aa']: lambda: first, linked.symbols['two']['aa']: lambda: second}
        rows = evaluate_document(linked.document, individuals=('item',), situations=('now',), primitives=model)
        assert [row['value'] for row in rows] == [first, second]


def test_descriptions_are_relocated_without_collapsing_definition_identity():
    first = parse('n:r aa[] a.d ab[] a[k aa[]].')
    second = parse('n:r aa[] a.d ab[] a[k aa[]].d ac[] a[k aa[]].r ad[i[h[] a]] c.q[k ad[r[p ab]]].q[k ad[r[p ac]]].')
    linked = link_documents({'first': first, 'second': second})
    moved = linked.symbols['second']
    model = {'aa': lambda: 'one', moved['aa']: lambda: 'two',
        moved['ad']: lambda description: json.loads(description.syntax)['symbol'] == moved['ab']}
    results = evaluate_document(linked.document, individuals=('one', 'two'), situations=('now',), primitives=model)
    assert [r['value'] for r in results] == [True, False]
    assert project_document(linked, 'second') == second


def test_bound_variables_and_nested_assumptions_survive_global_relocation():
    first = parse('n:r aa[a] a.')
    second = parse('n:r aa[a] a.d ab[aa a] a[k aa[v aa]].'
        'a[f aa a[e[k ab[v aa]][k aa[v aa]]]][q[f aa a[e[k ab[v aa]][k aa[v aa]]]].].')
    linked = link_documents({'first': first, 'second': second})
    assert project_document(linked, 'second') == second


@pytest.mark.parametrize('shared', [
    {'missing': {}}, {'two': {'missing': ('one', 'aa')}},
    {'one': {'aa': ('two', 'aa')}}, {'two': {'aa': ('two', 'aa')}},
    {'two': {'aa': ('one', 'missing')}}, {'two': {'aa': ('one',)}},
    {'two': {'aa': ('one', 'aa'), 'ab': ('one', 'aa')}},
])
def test_invalid_or_collapsing_shares_are_rejected(shared):
    source = parse('n:r aa[] a.r ab[] a.')
    with pytest.raises(SemanticError):
        link_documents({'one': source, 'two': source}, shared=shared)


def test_body_signature_and_relocated_dependencies_must_match():
    first = parse('n:r aa[] a.r ab[] a.d ac[] a[k aa[]].')
    for second in ('n:r aa[] c.', 'n:r aa[] a.r ab[] a.d ac[] a[k ab[]].'):
        doc = parse(second)
        with pytest.raises(SemanticError):
            link_documents({'one': first, 'two': doc}, shared={'two': {d['name']: ('one', d['name']) for d in doc['declarations']}})


def test_fresh_names_do_not_steal_later_source_names():
    one = parse('n:r aa[] a.')
    two = parse('n:r aa[] a.r zza[] a.r zzb[] a.')
    linked = link_documents({'one': one, 'two': two})
    assert linked.symbols['two'] == {'aa': 'zzc', 'zza': 'zza', 'zzb': 'zzb'}
    assert project_document(linked, 'two') == two


def test_edition_changes_and_tampered_projections_are_rejected():
    with pytest.raises(SemanticError):
        link_documents({'one': parse('m:r aa[] a.'), 'two': parse('n:r aa[] a.')})
    linked = link_documents({'one': parse('n:r aa[] a.'), 'two': parse('n:r aa[] a.')})
    moved = deepcopy(linked.document)
    moved['declarations'].pop()
    with pytest.raises(SemanticError):
        project_document(linked, 'two', document=moved)
