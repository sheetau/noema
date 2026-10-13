import re

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_kant_linked_draft import projection_checks, evaluation_checks, alignment
from scripts.compose_kant_linked_draft import ROOT, linkage, source_composed


def test_common_ancestor_and_full_source_projections_are_exact():
    row = projection_checks()
    assert row['both_complete_source_asts_recovered']
    assert row['common_declarations'] == 343
    assert row['common_statement_prefix_present_once'] == 8
    assert row['linked_declarations'] == 415 and row['linked_statements'] == 9
    assert set(row['renamed_branch_symbols']) == {'rab', 'rac', 'rad', 'rae', 'raf'}


def test_current_and_relocated_definitions_retain_distinct_meanings():
    rows = evaluation_checks()
    assert len(rows['permission_history']) == 5
    assert rows['retained_attitude']['lost_middle'] == [False, True]
    assert rows['confinement']['baseline'] == [True, True, False]
    assert rows['confinement']['already_confined'] == [False, True, False]


def test_linking_does_not_add_source_coverage_or_promote_meaning_completion():
    row = alignment()
    assert len(row['segments']) == 4
    assert not row['new_source_ranges'] and not row['semantic_completion']
    assert all(not s['full_semantic_equivalence'] for s in row['segments'])


def test_linked_basis_documents_every_primitive_definition_and_relocation():
    text, basis = source_composed()
    result = audit_basis(parse(text), basis)
    assert (result['primitive_count'], result['definition_count']) == (177, 238)
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert basis['linkage']['symbols']['confinement']['raf'] != 'raf'
    assert basis['linkage']['symbols']['current']['raf'] == 'raf'
    linked, pairs, ancestor = linkage()
    mapping = linked.symbols['confinement']
    reverse = {new: old for old, new in mapping.items() if old != new}
    common = {d['name'] for d in ancestor['declarations']}
    for old, original in pairs['confinement'][1]['definitions'].items():
        if old not in common:
            explanation = re.sub(r'(?<![a-z2-7])[a-z2-7]+(?![a-z2-7])',
                lambda token: reverse.get(token[0], token[0]), basis['definitions'][mapping[old]])
            assert explanation == original
