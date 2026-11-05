import json
import pytest
from scripts.verify_language_edition import verify, confined, digest, LOCK, REPORT
from scripts.finalize_language_edition import selection_only


def fixture(root):
    (root/'data').mkdir();(root/'reports').mkdir()
    (root/'text').write_bytes(b'original')
    lock=dict(edition='1.0',files={'text':digest(b'original')})
    raw=json.dumps(lock).encode();(root/LOCK).write_bytes(raw)
    (root/REPORT).write_text(json.dumps(dict(status='complete_under_stated_scope',files=1,
                                            artifact_lock_sha256=digest(raw))),encoding='utf-8')


def test_detects_changed_same_length_bytes(tmp_path):
    fixture(tmp_path);assert verify(tmp_path)['unchanged']
    (tmp_path/'text').write_bytes(b'modified')
    with pytest.raises(ValueError,match='Changed release artifact'):verify(tmp_path)


def test_missing_and_tampered_seal(tmp_path):
    fixture(tmp_path);(tmp_path/'text').unlink()
    with pytest.raises(FileNotFoundError):verify(tmp_path)
    (tmp_path/LOCK).write_bytes(b'{"edition":"1.0","files":{}}')
    with pytest.raises(ValueError,match='seal differs'):verify(tmp_path)


def test_rejects_path_outside_edition(tmp_path):
    with pytest.raises(ValueError):confined(tmp_path,'../outside')


def test_selection_exception_does_not_hide_semantic_change():
    a=dict(review_index='fixed',verification=dict(general_language='v1',writing_freeze='frozen'))
    b=dict(review_index='fixed',verification=dict(general_language='v2',writing_freeze='frozen'))
    assert selection_only(a,b)
    b['review_index']='different';assert not selection_only(a,b)
    b['review_index']='fixed';b['verification']['writing_freeze']='different'
    assert not selection_only(a,b)
