from copy import deepcopy
import json
import xml.etree.ElementTree as ET

import pytest

from scripts.check_written_math_corrections import ROOT, LEDGER, NS, DOCUMENT, apply_correction, digest, reviewed_math, noema_checks


def records():
    return json.loads(LEDGER.read_text(encoding='utf-8'))['corrections']


def test_review_keeps_snapshot_and_changes_only_denominator_tokens():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';before=path.read_bytes()
    rows=reviewed_math()
    assert set(rows)=={'M0257','M0273'}
    for row,correction in zip(rows.values(),records(),strict=True):
        old=ET.fromstring(row['snapshot_mathml']);new=ET.fromstring(row['reviewed_mathml'])
        old_fraction=next(old.iter(NS+'mfrac'));new_fraction=next(new.iter(NS+'mfrac'))
        assert ET.tostring(old_fraction[0])==ET.tostring(new_fraction[0])
        old_tokens=list(old.iter());new_tokens=list(new.iter())
        assert len(old_tokens)==len(new_tokens)
        changes=[]
        for a,b in zip(old_tokens,new_tokens,strict=True):
            assert (a.tag,a.attrib,a.tail)==(b.tag,b.attrib,b.tail)
            if a.text!=b.text:changes.append((a.tag,a.text,b.text))
        assert changes==[(NS+'mi',correction['from'],correction['to'])]
    assert path.read_bytes()==before
    assert 'sin' in list(ET.fromstring(rows['M0257']['reviewed_mathml']).itertext())


def test_corrections_are_hash_bound_and_do_not_mutate_callers():
    row=reviewed_math()['M0257'];correction=records()[0];original=deepcopy(correction)
    result=apply_correction(row['snapshot_mathml'],correction)
    assert result==row['reviewed_mathml'] and correction==original
    with pytest.raises(ValueError,match='hash'):
        apply_correction(row['snapshot_mathml']+' ',correction)
    with pytest.raises(ValueError,match='hash'):
        apply_correction(result,correction)


@pytest.mark.parametrize('field,value,match',[
    ('operation','replace_everywhere','operation'),('occurrences',2,'Ambiguous'),('from','not_present','missing or ambiguous')])
def test_unknown_or_ambiguous_patches_are_rejected(field,value,match):
    row=reviewed_math()['M0257'];correction=records()[0];correction[field]=value
    with pytest.raises(ValueError,match=match):apply_correction(row['snapshot_mathml'],correction)


def test_repeated_target_in_denominator_is_rejected_even_with_matching_hash():
    raw='<math xmlns="http://www.w3.org/1998/Math/MathML"><mfrac><mn>1</mn><mrow><mi>v</mi><mi>v</mi></mrow></mfrac></math>'
    correction=records()[1];correction['snapshot_math_sha256']=digest(raw.encode('utf-8'))
    with pytest.raises(ValueError,match='ambiguous'):apply_correction(raw,correction)


def test_noema_counterexamples_distinguish_the_two_readings():
    text,result=noema_checks();rows=result['claims']
    assert DOCUMENT.read_text(encoding='utf-8')==text and len(rows)==9
    rejected={'parallel_case_snapshot_has_same_value','snapshot_lowercase_speed_preserves_light_speed'}
    assert {name for name,row in rows.items() if row['status']=='invalid'}==rejected
    assert rows['zero_motion_masks_sin_cos_error']['status']=='valid'
    assert rows['zero_added_speed_masks_case_error']['status']=='valid'


def test_no_translation_or_whole_unit_completion_is_claimed():
    report=json.loads((ROOT/'reports/written-math-corrections-v1.json').read_text(encoding='utf-8'))
    assert report['scope']['new_semantically_verified_units']==0
    assert not report['scope']['new_translation_alignment_claimed']
    assert not report['scope']['whole_page_reviewed']
    assert not report['scope']['whole_formula_semantics_verified']
    assert not report['scope']['source_snapshot_modified']
