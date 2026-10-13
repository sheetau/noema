from copy import deepcopy
from itertools import product
import json

import pytest

from noema.extraction import extract_document, extract_basis
from noema.finite_semantics import evaluate_document
from noema.grammar import parse
from noema.semantics import SemanticError
from scripts.extract_document import main


def test_default_retains_all_statements_and_transitive_quoted_aliases():
    doc = parse('n:r aa[] a.r ab[] c.d ac[] a[k aa[]].d ad[] a[k aa[]].'
                'r ae[i[h[] a]] c.q[k ae[r[p ac]]].q[u[e[r[p ac]][r[p ad]]]].q[k ae[r[p ac]]].')
    before = deepcopy(doc)
    result = extract_document(doc)
    assert doc == before
    assert result.retained_symbols == ['aa', 'ac', 'ad', 'ae']
    assert result.removed_symbols == ['ab']
    assert result.statement_indices == [0, 1, 2]
    assert result.document['statements'] == doc['statements']
    assert result.document['declarations'] == [d for d in doc['declarations'] if d['name'] != 'ab']
    assert extract_document(result.document).document == result.document


def test_statement_selection_preserves_source_order_multiplicity_and_scope():
    doc = parse('n:r aa[] c.r ab[] c.a[k aa[]][q[k ab[]].].q[k aa[]].q[k aa[]].')
    selected = extract_document(doc, statement_indices=[2, 0])
    assert selected.statement_indices == [0, 2]
    assert selected.document['statements'] == [doc['statements'][0], doc['statements'][2]]
    assert selected.retained_symbols == ['aa', 'ab']
    assert len(extract_document(doc).document['statements']) == 3


def test_explicit_library_roots_keep_data_and_do_not_confuse_bound_names():
    doc = parse('n:r aa[] a.r ab[] c.d ac[ab a] a[v ab].d ad[] j[a][l[a][k aa[]]].q[k ab[]].')
    result = extract_document(doc, roots=['ac', 'ad', 'ac'], statement_indices=[])
    assert result.retained_symbols == ['aa', 'ac', 'ad']
    assert result.document['statements'] == []
    assert result.roots == ['ac', 'ad']
    with pytest.raises(SemanticError, match='Empty document'):
        extract_document(doc, statement_indices=[])


def test_reference_inside_fold_and_nested_quote_is_kept():
    doc = parse('n:r aa[] c.r ab[] c.d ac[] j[c][l[c][k aa[]]].'
        'd ad[] c[q[k ac[]][k aa[]][i[value c item c][x[v value][v item]]]].'
        'q[e[r[r[p ad]]][r[r[p ad]]]].')
    result = extract_document(doc)
    assert result.retained_symbols == ['aa', 'ac', 'ad']
    assert result.document['statements'] == doc['statements']


@pytest.mark.parametrize('kwargs', [
    {'roots': 'aa'}, {'roots': ['unknown']}, {'roots': [True]},
    {'statement_indices': [True]}, {'statement_indices': [-1]},
    {'statement_indices': [1]}, {'statement_indices': [0, 0]}, {'statement_indices': '0'},
])
def test_invalid_selections_are_rejected(kwargs):
    with pytest.raises(SemanticError):
        extract_document(parse('n:r aa[] c.q[k aa[]].'), **kwargs)


def test_invalid_unused_declaration_is_not_silently_repaired():
    doc = parse('n:r aa[] c.d ab[] c[k aa[]].q[k aa[]].')
    doc['declarations'][1]['body']['symbol'] = 'missing'
    with pytest.raises(SemanticError):
        extract_document(doc)


def test_finite_interpretations_and_intensional_identity_are_unchanged():
    doc = parse('n:r aa[] c.r ab[] c.r ac[] c.d ad[] c[k aa[]].d ae[] c[k aa[]].'
                'q[w[k ad[]][k ab[]]].q[u[e[r[p ad]][r[p ae]]]].')
    result = extract_document(doc)
    for first, second, unused in product((False, True), repeat=3):
        model = {'aa': lambda: first, 'ab': lambda: second, 'ac': lambda: unused}
        expected = evaluate_document(doc, individuals=('item',), situations=('now',), primitives=model)
        actual = evaluate_document(result.document, individuals=('item',), situations=('now',),
            primitives={k: v for k, v in model.items() if k in result.retained_symbols})
        assert actual == expected


def test_basis_projection_preserves_meanings_and_caveats_without_stale_maps():
    doc = parse('n:r aa[] c.r ab[] c.d ac[] c[k aa[]].q[k ac[]].')
    basis = {'version': 'old', 'document': 'old.noema', 'primitives': [
        {'symbol': name, 'parameters': [], 'result': 'truth', 'arguments': [], 'meaning_ja': name}
        for name in ('aa', 'ab')], 'definitions': {'ac': 'alias'}, 'unresolved': ['unresolved'],
        'role_linkage': {'old_map': 'ab'}}
    before = deepcopy(basis)
    selected = extract_document(doc)
    projected = extract_basis(doc, basis, selected, version='new', document_path='new.noema')
    assert basis == before
    assert projected['primitives'] == basis['primitives'][:1]
    assert projected['definitions'] == basis['definitions']
    assert projected['unresolved'] == basis['unresolved']
    assert 'role_linkage' not in projected
    selected.document['statements'] = []
    with pytest.raises(SemanticError, match='does not match'):
        extract_basis(doc, basis, selected, version='new', document_path='new.noema')


def test_cli_keeps_statements_by_default_and_never_overwrites(tmp_path):
    source, out, manifest = [tmp_path / name for name in ('source.noema', 'out.noema', 'manifest.json')]
    source.write_text('n:r aa[] c.r ab[] c.q[k aa[]].', encoding='utf-8')
    main(['--input', str(source), '--output', str(out), '--manifest', str(manifest)])
    assert len(parse(out.read_text(encoding='utf-8'))['statements']) == 1
    assert json.loads(manifest.read_text(encoding='utf-8'))['removed_symbols'] == ['ab']
    previous = out.read_bytes()
    with pytest.raises(SystemExit):
        main(['--input', str(source), '--output', str(out)])
    assert out.read_bytes() == previous
    assert not previous.startswith(b'\xef\xbb\xbf') and b'\r\n' not in previous


def test_cli_rejects_conflicting_output_paths_before_writing(tmp_path):
    source, output = tmp_path / 'source.noema', tmp_path / 'out.noema'
    source.write_text('n:r aa[] c.q[k aa[]].', encoding='utf-8')
    with pytest.raises(SystemExit):
        main(['--input', str(source), '--output', str(output), '--manifest', str(output)])
    assert not output.exists()
    with pytest.raises(SystemExit):
        main(['--input', str(source), '--output', str(output), '--basis-input', str(source)])
    assert not output.exists()
