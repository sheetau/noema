import json

import pytest

from noema.grammar import parse
from scripts.check_wave_directions import REPORT, build_report
from scripts.compose_wave_directions import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_direction_normalization_inverse_frequency_sign_and_phase(result):
    claims=result['polynomial']['claims']
    assert len(claims)==9
    assert claims['wrong_aberration_sign']['status']=='invalid'
    assert all(r['status']=='valid' for n,r in claims.items() if n!='wrong_aberration_sign')
    assert result['polynomial']['rational_polynomial_lemmas_only']
    assert not result['polynomial']['all_real_cut_field_laws_proved']


def test_component_and_domain_contrasts_execute_actual_cut_expressions(result):
    rows=result['expressions']['cases']
    assert len(rows)==33
    assert sum(row==[True] for row in rows.values())==21
    assert all(row==[False] for name,row in rows.items() if not name.startswith('valid_'))
    assert result['expressions']['domain_rejection_independent_of_two_oracle_fallbacks']
    assert result['expressions']['cumulative_and_standalone_agree']


def test_phase_and_positive_root_special_cases(result):
    assert result['expressions']['specials']=={'parallel_-3':[True],'parallel_0':[True],'parallel_3':[True],'phase':[True]}


def test_finite_checks_do_not_decode_or_quantify_the_real_number_universe(result):
    assert result['expressions']['unregistered_predicate_not_decoded_by_sampling']
    assert result['finite_refusal']['refused']


def test_parent_and_original_author_claims_are_preserved(result):
    text,basis=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['statements'])==173
    audit=result['documents'][basis['document']]
    assert (audit['primitive_count'],audit['definition_count'])==(595,952)
    assert result['sizes']['wave-directions-core']=={'characters':3525,'statements':0}
    assert result['new_primitives']==result['new_author_statements']==0


def test_seven_math_associations_do_not_certify_the_wave_or_observer_interpretation(result):
    assert len(result['alignment']['segments'])==7
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
