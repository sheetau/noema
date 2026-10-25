from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.reader_course import *
from scripts.check_reader_course import (saved_assets,saved_geometry_checks,dictionary_checks,guide_checks,semantic_checks,distribution_checks,verify_published)


def response():
    return dict(schema=SCHEMA,exercise_sha256='test-identity',participant='synthetic-test',role='author',prior_answer_exposure=True,
        answers={x['id']:dict(option=x['correct'],note='synthetic grader fixture') for x in curriculum()['exercises']})

def test_all_current_grammar_operations_and_the_exact_public_dictionary_are_in_the_course():
    assert set(curriculum()['keywords'])==set(KEYWORDS)|set(SHARING)
    assert guide_checks()==dict(grammar_operations=49,row_markers=4,name_markers=2,worked_documents=2)
    assert dictionary_checks()==dict(words=375,definitions=352,primitive_declarations=23)

def test_exercise_geometry_is_independently_decoded_from_distributed_html():
    rows=saved_geometry_checks()
    assert [x['id'] for x in rows]==[f'{i:02}' for i in range(1,18)]
    assert sum(x['pages'] for x in rows)==26
    assert all(x['pages']==1 for x in rows[:14]) and all(x['pages']==4 for x in rows[14:])

def test_reading_contrasts_have_small_independent_semantic_models():
    assert semantic_checks()==dict(models=24,individuals=2,relation_tables=16,giving_fixed_slot_diagnostics=[0,1,2],
        quotation_without_truth=True,definition_without_assertion=True,referent_identity_contrast=True)

def test_shared_expression_is_really_visible_in_the_sharing_exercise():
    w=PublicWriter(vocabulary());w.document(vocabulary().encode(basic_documents()['12']))
    assert w.share_count>=1

def test_zip_separates_learner_pages_from_answer_key_and_native_exam_sources():
    assert distribution_checks()==dict(learner_files=['dictionary.html','exercises.html','index.html'],answer_files_distributed=False,external_resources=0)

def test_all_synthetic_correct_answers_do_not_count_as_independent_human_reading():
    r=grade(response(),'test-identity')
    assert r['counts']==dict(correct=17,incorrect=0,unknown=0,unanswered=0)
    assert r['declared_role']=='author' and r['prior_answer_exposure'] is True
    assert r['independence']=='not_verified_by_software'
    assert 'independent_reading_verified' not in r

def test_unanswered_unknown_wrong_and_correct_answers_remain_separate():
    data=response();data['answers']['01']['option']=None;data['answers']['02']['option']='unknown'
    data['answers']['03']['option']='a' if data['answers']['03']['option']!='a' else 'b'
    r=grade(data,'test-identity')
    assert r['counts']==dict(correct=14,incorrect=1,unknown=1,unanswered=1)
    assert r['results'][0]['note']=='synthetic grader fixture'

def test_self_reported_independence_is_not_software_certification():
    data=response();data['role']='independent';data['prior_answer_exposure']=False
    assert grade(data,'test-identity')['independence']=='not_verified_by_software'

@pytest.mark.parametrize('change',['missing','extra','wrong-edition','bad-schema','option','answer-fields','participant','role','exposure','note'])
def test_incomplete_or_foreign_response_formats_are_rejected(change):
    data=response()
    if change=='missing':del data['answers']['01']
    elif change=='extra':data['answers']['18']=dict(option='a',note='')
    elif change=='wrong-edition':data['exercise_sha256']='other-identity'
    elif change=='bad-schema':data['schema']='other-schema'
    elif change=='option':data['answers']['01']['option']='hidden-answer'
    elif change=='answer-fields':data['answers']['01']['correct']=True
    elif change=='participant':data['participant']=123
    elif change=='role':data['role']='certified-independent'
    elif change=='exposure':data['prior_answer_exposure']='false'
    else:data['answers']['01']['note']=None
    with pytest.raises(ValueError):grade(data,'test-identity')

@pytest.mark.parametrize('field',['source_sha256','artifact_sha256'])
def test_grading_checks_current_published_sources_and_artifacts(tmp_path,field):
    from scripts.check_reader_course import REPORT
    (tmp_path/'reports').mkdir();(tmp_path/'input').write_text('original',encoding='utf-8')
    report=dict(exercise_sha256='fixed',source_sha256={},artifact_sha256={})
    report[field]['input']=digest(b'original')
    (tmp_path/REPORT).write_text(json.dumps(report),encoding='utf-8')
    assert verify_published(tmp_path)=='fixed'
    (tmp_path/'input').write_text('amended',encoding='utf-8')
    with pytest.raises(ValueError,match='Published course input differs'):verify_published(tmp_path)

def test_exercise_identity_tracks_questions_and_visible_pages_but_does_not_expose_answer_keys():
    assets=saved_assets();original=exercise_identity(assets);changed=deepcopy(assets)
    changed['01'][0]+='\n'
    assert exercise_identity(changed)!=original
    html=(OUT/'learner/exercises.html').read_text(encoding='utf-8')
    assert original in html and 'reviewer/' not in html and '"correct"' not in html and '"reason"' not in html

@pytest.mark.parametrize('change',['missing','duplicate','malformed','different-valid-document'])
def test_saved_exercise_tampering_cannot_reuse_a_previous_pass(tmp_path,monkeypatch,change):
    from scripts import check_reader_course as check
    target=tmp_path/'learner';target.mkdir()
    text=(OUT/'learner/exercises.html').read_text(encoding='utf-8')
    if change=='missing':text=text.replace('data-question="01"','data-question="99"',1)
    elif change=='duplicate':text=text.replace('data-question="02"','data-question="01"',1)
    else:
        assets=saved_assets();old=assets['01'][0]
        text=text.replace(old,assets['02'][0] if change=='different-valid-document' else old.replace('<circle','<ellipse',1),1)
    (target/'exercises.html').write_text(text,encoding='utf-8');monkeypatch.setattr(check,'OUT',tmp_path)
    with pytest.raises((ValueError,KeyError)):check.saved_geometry_checks()
