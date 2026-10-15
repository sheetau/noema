from copy import deepcopy
import json

import pytest

from noema.extraction import extract_document
from noema.grammar import parse
from noema.language import convert
from noema.linking import project_document
from noema.semantics import SemanticError
from scripts.compose_einstein_reconciliation import ROOT,CURRENT,SOURCE,BASIS,MANIFEST,PREVIOUS,DONORS,assembly,build,document,load,verify_same_candidates
from scripts.check_einstein_reconciliation import numeric_checks


def test_old_symbol_locations_are_completely_accounted_for_without_claiming_meaning_completion():
    linked,inputs,pairs,checks,resolutions,used=assembly()
    old=set(load(PREVIOUS)['works']['einstein-1905']['source_aligned_symbols_absent_from_input'])
    assert set(resolutions)==old and len(old)==143
    assert sum(r['source']=='current' for r in resolutions.values())==83
    assert sum(r['source']!='current' for r in resolutions.values())==60
    assert len(checks)==27
    manifest=load(MANIFEST)
    assert not manifest['semantic_completion'] and not manifest['adds_new_text_coverage']
    assert manifest['unresolved_old_symbol_locations']==[]


@pytest.mark.parametrize('label',('current',*DONORS))
def test_each_source_projects_back_exactly_after_namespace_relocation(label):
    linked,inputs,*_=assembly()
    assert project_document(linked,label)==inputs[label]
    assert project_document(linked,label,document=document(SOURCE))==inputs[label]
    if label!='current':assert inputs[label]['statements']==[]


@pytest.mark.parametrize('label',tuple(DONORS))
def test_older_edition_is_explicitly_convertible_back_to_original_library(label):
    linked,inputs,pairs,*_=assembly()
    original=document(DONORS[label][0]);roots=pairs[label][2].roots
    expected=extract_document(original,roots=roots,statement_indices=[]).document
    assert convert(project_document(linked,label),original['schema_version'])==expected


def test_current_statements_and_corrected_density_reference_are_unchanged():
    linked,*_=assembly();current=document(CURRENT)
    assert linked.document['statements']==current['statements']
    assert len(current['statements'])==175
    assert linked.document['statements'][-1]['body']['arguments'][-1]['body']['symbol']=='seoz'
    previous=document(load(PREVIOUS)['works']['einstein-1905']['source'])
    assert current['statements'][:174]==previous['statements']


def test_unrelated_source_names_never_share_a_declaration():
    linked,inputs,*_=assembly()
    seen=set()
    for label,mapping in linked.symbols.items():
        assert len(set(mapping.values()))==len(mapping)
        assert seen.isdisjoint(mapping.values())
        seen.update(mapping.values())
    assert len(linked.document['declarations'])==sum(len(d['declarations']) for d in inputs.values())


def test_rational_witnesses_and_quoted_identity_survive_in_the_actual_assembled_document():
    result=numeric_checks()
    assert result['clock_rate_examples']==[True,True,False,False]
    assert not result['independent_arithmetic_descriptions_equal']


@pytest.mark.parametrize('change',('body','meaning','signature'))
def test_same_spelling_is_insufficient_provenance(change):
    original=parse('n:r aa[] c.d ab[] c[k aa[]].')
    basis=dict(primitives=[dict(symbol='aa',parameters=[],result='truth',arguments=[],meaning_ja='first convention')],
               definitions={'ab':'alias'},unresolved=[])
    other=deepcopy(original);other_basis=deepcopy(basis)
    if change=='body':other['declarations'][1]['body']={'kind':'not','arguments':[other['declarations'][1]['body']]}
    elif change=='meaning':other_basis['primitives'][0]['meaning_ja']='different convention'
    else:other['declarations'][0]['result']='individual'
    with pytest.raises((ValueError,SemanticError)):
        verify_same_candidates(original,basis,other,other_basis,['ab'])


def test_all_convention_texts_and_caveats_retain_their_source_namespace():
    linked,inputs,pairs,*_=assembly();basis=load(BASIS)
    for label,(doc,old,selected) in pairs.items():
        mapping=linked.symbols[label];primitives={r['symbol']:r for r in basis['primitives']}
        for row in old['primitives']:
            if row['symbol'] in mapping:
                actual=primitives[mapping[row['symbol']]]
                assert actual['source_namespace']==label and actual['source_symbol']==row['symbol']
                assert actual['meaning_ja']=='['+label+' の記号名] '+row['meaning_ja']
        for name,meaning in old['definitions'].items():
            if name in mapping:assert basis['definitions'][mapping[name]]=='['+label+' の記号名] '+meaning
        assert all('['+label+'] '+s in basis['unresolved'] for s in old['unresolved'])


def test_generated_files_are_reproducible():
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
