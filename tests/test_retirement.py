import json
import sys
import pytest
from scripts import clean_retired_files as cleanup


def setup(tmp_path,monkeypatch,target):
    (tmp_path/'reports').mkdir()
    (tmp_path/'completed').mkdir()
    (tmp_path/'completed/keep.txt').write_bytes(b'complete')
    (tmp_path/'retired.txt').write_bytes(b'obsolete')
    plan=dict(kept_files=['explicit-keep.txt'],protected_dirs=['completed'],
              files=[dict(path=target,bytes=8)],protected_dirty=[],protected_untracked=[])
    (tmp_path/'plan.json').write_text(json.dumps(plan),encoding='utf-8')
    monkeypatch.setattr(cleanup,'ROOT',tmp_path)
    monkeypatch.setattr(sys,'argv',['cleanup','--plan','plan.json','--run','.runs/check'])


def test_retirement_preserves_completed_edition_and_can_resume(tmp_path,monkeypatch):
    setup(tmp_path,monkeypatch,'retired.txt')
    cleanup.main()
    assert not (tmp_path/'retired.txt').exists()
    assert (tmp_path/'completed/keep.txt').read_bytes()==b'complete'
    cleanup.main()
    assert json.loads((tmp_path/'reports/cleanup-v1.json').read_text())['removed_files']==1


@pytest.mark.parametrize('target',['completed/keep.txt','../outside.txt','explicit-keep.txt'])
def test_rejects_protected_or_external_paths_before_deleting(tmp_path,monkeypatch,target):
    setup(tmp_path,monkeypatch,target)
    with pytest.raises(ValueError):cleanup.main()
    assert (tmp_path/'completed/keep.txt').read_bytes()==b'complete'
    assert (tmp_path/'retired.txt').read_bytes()==b'obsolete'
