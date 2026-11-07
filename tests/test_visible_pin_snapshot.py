from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import os
import pytest
from scripts.visible_pin_snapshot import digest_snapshot


def owner_at(root):
    calls=[]
    def digest(path):
        calls.append(path)
        return sha256((root/path).read_bytes()).hexdigest()
    return SimpleNamespace(digest=digest),calls


def test_duplicate_paths_are_read_twice_and_not_persisted(tmp_path):
    (tmp_path/'a').write_bytes(b'alpha');owner,calls=owner_at(tmp_path);original=owner.digest
    for _ in range(2):
        with digest_snapshot(owner,root=tmp_path) as stats:
            assert owner.digest('a')==owner.digest(Path('a'))==original('a')
            assert owner.digest('a')==sha256(b'alpha').hexdigest()
        assert stats==dict(requests=3,first_reads=1,rechecks=1)
        assert owner.digest is original
    # One explicit baseline read per iteration, plus the two snapshot reads.
    assert calls==['a']*6


def test_same_size_and_timestamp_change_is_rejected(tmp_path):
    p=tmp_path/'a';p.write_bytes(b'alpha');stamp=p.stat();owner,_=owner_at(tmp_path);original=owner.digest
    with pytest.raises(ValueError,match='Pinned input changed'):
        with digest_snapshot(owner,root=tmp_path):
            owner.digest('a');p.write_bytes(b'omega')
            os.utime(p,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    assert owner.digest is original
    with digest_snapshot(owner,root=tmp_path):assert owner.digest('a')==sha256(b'omega').hexdigest()


def test_nested_collection_reuses_reads_but_outer_exit_rechecks(tmp_path):
    p=tmp_path/'a';p.write_bytes(b'alpha');owner,calls=owner_at(tmp_path)
    with pytest.raises(ValueError,match='Pinned input changed'):
        with digest_snapshot(owner,root=tmp_path) as outer:
            owner.digest('a')
            with digest_snapshot(owner,root=tmp_path) as inner:
                assert inner is outer;owner.digest('a')
            p.write_bytes(b'omega')
    assert calls==['a','a']


def test_missing_and_outside_inputs_are_not_accepted(tmp_path):
    owner,_=owner_at(tmp_path);original=owner.digest
    with pytest.raises(ValueError,match='Missing digest reader'):
        with digest_snapshot(SimpleNamespace(),root=tmp_path):pass
    with pytest.raises(FileNotFoundError):
        with digest_snapshot(owner,root=tmp_path):owner.digest('missing')
    assert owner.digest is original
    for path in ('../outside',tmp_path/'absolute'):
        with pytest.raises(ValueError,match='outside pinned root'):
            with digest_snapshot(owner,root=tmp_path):owner.digest(path)
    assert owner.digest is original


def test_exception_and_reader_mutation_restore_original(tmp_path):
    owner,_=owner_at(tmp_path);original=owner.digest
    with pytest.raises(RuntimeError,match='diagnostic'):
        with digest_snapshot(owner,root=tmp_path):raise RuntimeError('diagnostic')
    assert owner.digest is original
    with pytest.raises(ValueError,match='reader changed'):
        with digest_snapshot(owner,root=tmp_path):owner.digest=lambda p:'invented'
    assert owner.digest is original


def test_other_threads_and_different_owners_are_rejected(tmp_path):
    (tmp_path/'a').write_bytes(b'alpha');owner,_=owner_at(tmp_path);other,_=owner_at(tmp_path)
    with digest_snapshot(owner,root=tmp_path):
        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(ValueError,match='single-threaded'):pool.submit(owner.digest,'a').result()
        with pytest.raises(ValueError,match='Conflicting'):
            with digest_snapshot(other,root=tmp_path):pass
        assert owner.digest('a')==sha256(b'alpha').hexdigest()
