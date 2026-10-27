from hashlib import sha256
import os
from pathlib import Path
from types import ModuleType

import pytest

from scripts.visible_vocabulary_session import vocabulary_session


@pytest.fixture
def model(tmp_path):
    code = '''
COUNTS = {'a': 0, 'b': 0, 'c': 0}
FAIL = False
class Base:
    def read(self): return self.values
class A(Base):
    def __init__(self, extra=None):
        COUNTS['a'] += 1
        self.values = ['a']
        if extra is not None: self.values.append(extra)
class B(A):
    def __init__(self):
        super().__init__()
        COUNTS['b'] += 1
        if FAIL: raise ValueError('incomplete prefix')
        self.values.append('b')
class C(B):
    def __init__(self):
        super().__init__()
        COUNTS['c'] += 1
        self.values.append('c')
'''
    path = tmp_path / 'model.py'
    path.write_text(code, encoding='utf-8')
    module = ModuleType('vocabulary_session_fixture')
    exec(compile(code, str(path), 'exec'), module.__dict__)
    pins = {'model.py': sha256(path.read_bytes()).hexdigest()}
    return module, tmp_path, pins


def session(model):
    m, root, pins = model
    return vocabulary_session((m.C, m.B, m.A), root=root, pins=pins)


def test_each_prefix_validated_once_and_results_match_originals(model):
    m, _, _ = model
    expected = [cls().read()[:] for cls in (m.C, m.B, m.A)]
    m.COUNTS = dict.fromkeys(m.COUNTS, 0)
    with session(model) as stats:
        actual = [cls().read()[:] for cls in (m.C, m.B, m.A, m.C)]
        assert actual == [*expected, expected[0]]
        assert m.COUNTS == {'a': 1, 'b': 1, 'c': 1}
        assert stats == {'hits': 3, 'misses': 3, 'bypasses': 0}


def test_snapshots_are_isolated_from_caller_mutation(model):
    m, _, _ = model
    with session(model):
        first = m.C(); first.values.append('changed')
        assert m.C().values == ['a', 'b', 'c']
        assert m.B().values == ['a', 'b']


def test_explicit_arguments_and_unlisted_subclasses_are_not_cached(model):
    m, _, _ = model
    class Foreign(m.C):
        def read(self): return ['different dispatch']
    with session(model) as stats:
        m.C()
        assert m.A('argument').values == ['a', 'argument']
        assert Foreign().read() == ['different dispatch']
        assert m.COUNTS == {'a': 3, 'b': 2, 'c': 2}
        assert stats['bypasses'] == 4


def test_preinitialized_instance_uses_original_constructor(model):
    m, _, _ = model
    with session(model) as stats:
        instance = m.A(); instance.values.append('changed')
        m.A.__init__(instance)
        assert instance.values == ['a'] and stats['bypasses'] == 1


def test_failed_prefix_is_not_saved(model):
    m, _, _ = model
    with session(model):
        m.FAIL = True
        with pytest.raises(ValueError, match='incomplete prefix'): m.B()
        m.FAIL = False
        assert m.B().values == ['a', 'b']
        assert m.COUNTS['b'] == 2


def test_input_change_with_same_size_and_mtime_aborts_and_restores(model):
    m, root, _ = model; path = root / 'model.py'; stat = path.stat()
    original = m.A.__init__
    with pytest.raises(ValueError, match='input changed'):
        with session(model):
            m.C()
            path.write_bytes(path.read_bytes().replace(b"['a']", b"['x']"))
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert m.A.__init__ is original


def test_bad_pin_rejects_before_any_constructor(model):
    m, root, pins = model; pins['model.py'] = '0' * 64
    with pytest.raises(ValueError, match='input changed'):
        with session(model): pass
    assert not any(m.COUNTS.values())


def test_exception_restores_and_nested_session_rejected(model):
    m, _, _ = model; original = m.A.__init__
    with pytest.raises(RuntimeError, match='caller'):
        with session(model):
            m.C()
            with pytest.raises(ValueError, match='already active'):
                with session(model): pass
            raise RuntimeError('caller')
    assert m.A.__init__ is original
    with session(model): assert m.C().values == ['a', 'b', 'c']


def test_behavior_overrides_and_unpinned_code_are_rejected(model):
    m, root, pins = model
    m.C.custom = lambda self: None
    with pytest.raises(ValueError, match='data-only'):
        with session(model): pass
    del m.C.custom
    with pytest.raises(ValueError, match='Unpinned'):
        with vocabulary_session((m.C,), root=root, pins={'other': '0'*64}): pass
