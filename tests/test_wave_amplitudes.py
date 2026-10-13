from copy import deepcopy
import hashlib
import json
import xml.etree.ElementTree as ET

import pytest

from noema.grammar import parse
from scripts.check_wave_amplitudes import REPORT, LEDGER, NS, build_report, reviewed_formula
from scripts.compose_wave_amplitudes import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_transverse_vector_identities_and_two_field_norm_factors_are_proved(result):
    claims=result['polynomial']['claims']
    assert len(claims)==12
    rejected={'snapshot_square_root_value','longitudinal_electric_field_is_not_a_transverse_wave'}
    assert all(row['status']==('invalid' if name in rejected else 'valid') for name,row in claims.items())
    assert not result['polynomial']['all_real_cut_laws_proved']


def test_shared_magnitudes_are_bound_to_all_six_components_in_both_documents(result):
    rows=result['amplitudes']['cases']
    assert len(rows)==61
    assert sum(name.startswith('valid_') for name in rows)==45
    assert all(row==[True,True] for name,row in rows.items() if name.startswith('valid_'))
    assert all(rows['changed_transformed_'+str(i)]==[False,True] for i in range(6))
    assert result['amplitudes']['cumulative_and_standalone_agree']


def test_squared_ratio_does_not_certify_the_sign_or_physical_wave_conditions(result):
    rows=result['amplitudes']['cases']
    for name in ('negative_old_amplitude','negative_new_amplitude','nonunit_direction',
                 'longitudinal_electric_component','reversed_magnetic_orientation','different_magnetic_magnitude'):
        assert rows[name]==[False,True]
    assert rows['wrong_old_amplitude']==rows['wrong_new_amplitude']==[False,False]


def test_direct_squared_ratio_rejects_snapshot_value_and_invalid_domains(result):
    rows=result['ratios']
    assert len(rows)==12
    accepted={'reviewed_oblique','reviewed_transverse','parallel_forward','parallel_reverse','zero_wave'}
    assert all(row==[name in accepted] for name,row in rows.items())


def test_facsimile_review_removes_only_the_reviewed_denominator_root(result):
    raw=ET.fromstring(result['facsimile']['snapshot_mathml'])
    reviewed=ET.fromstring(result['facsimile']['reviewed_mathml'])
    original_fraction=next(raw.iter(NS+'mfrac'));new_fraction=next(reviewed.iter(NS+'mfrac'))
    assert len(list(original_fraction[1].iter(NS+'msqrt')))==1
    assert not list(new_fraction[1].iter(NS+'msqrt'))
    assert ET.tostring(original_fraction[0])==ET.tostring(new_fraction[0])
    assert ''.join(original_fraction[1].itertext())==''.join(new_fraction[1].itertext())
    assert not result['facsimile']['source_snapshot_modified']
    assert not result['facsimile']['whole_page_semantics_verified']


def test_correction_rejects_changed_raw_hash_or_unreviewed_operation(result):
    correction=json.loads(LEDGER.read_text(encoding='utf-8'))['correction']
    with pytest.raises(ValueError,match='hash differs'):
        reviewed_formula(result['facsimile']['snapshot_mathml']+' ',correction)
    changed=deepcopy(correction);changed['review_status']='pending'
    with pytest.raises(ValueError,match='Unreviewed'):
        reviewed_formula(result['facsimile']['snapshot_mathml'],changed)


def test_correction_does_not_remove_an_unrelated_or_ambiguous_root(result):
    correction=json.loads(LEDGER.read_text(encoding='utf-8'))['correction']
    raw=result['facsimile']['snapshot_mathml']
    tree=ET.fromstring(raw);fraction=next(tree.iter(NS+'mfrac'))
    root=next(fraction[1].iter(NS+'msqrt'));fraction[1].append(deepcopy(root))
    changed=ET.tostring(tree,encoding='unicode');correction['snapshot_math_sha256']=hashlib.sha256(changed.encode('utf-8')).hexdigest()
    with pytest.raises(ValueError,match='Ambiguous'):
        reviewed_formula(changed,correction)


def test_real_domain_is_not_certified_by_sampling(result):
    assert result['finite_refusal']['refused']
    assert result['amplitudes']['rational_cut_oracles_not_general_real_proof']


def test_parent_author_statements_and_basis_are_preserved(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])-len(parent['declarations'])==12
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['sizes']['einstein-wave-amplitudes']['statements']==173


def test_two_math_associations_do_not_mark_measurement_or_prose_complete(result):
    assert {row['math_id'] for row in result['alignment']['segments']}=={'M0345','M0347'}
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
