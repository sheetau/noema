"""Reuse validated vocabulary prefixes only within one pinned authoring run.

This opt-in adapter is for the data-only vocabulary subclasses whose only
override is __init__. Each prefix is constructed by its original validator
before reuse. Snapshots are deep copies, never persistent pass/fail evidence.
The caller must pin the complete transitive inputs and publish only after the
context exits successfully. SVG recognition and semantic tests remain fresh.
"""
from contextlib import contextmanager
from copy import deepcopy
from functools import wraps
from hashlib import sha256
from pathlib import Path
import re
from threading import Lock
from types import FunctionType

_LOCK = Lock()


def _verify(root, pins):
    if not isinstance(pins, dict) or not pins:
        raise ValueError('Missing vocabulary input pins')
    for name, expected in pins.items():
        if (not isinstance(name, str) or Path(name).is_absolute()
                or not isinstance(expected, str)
                or re.fullmatch('[0-9a-f]{64}', expected) is None):
            raise ValueError('Invalid vocabulary input pin')
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Vocabulary input outside root or missing: ' + name)
        if sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Vocabulary input changed: ' + name)


@contextmanager
def vocabulary_session(classes, *, root, pins):
    """Temporarily memoize an explicit single-inheritance prefix chain.

    Pass classes from most derived to least derived, stopping before the first
    class that overrides another method. Explicit constructor arguments,
    preinitialized objects and unlisted subclasses use the original route.
    File contents are verified before construction and again before success.
    This adapter is single-threaded and cannot be nested.
    """
    if _LOCK.locked():
        raise ValueError('A vocabulary session is already active')
    root = Path(root).resolve()
    pins = dict(pins)
    classes = tuple(classes)
    if not classes or len(set(classes)) != len(classes):
        raise ValueError('Invalid vocabulary prefix chain')
    originals = {}
    for i, cls in enumerate(classes):
        allowed = {'__init__', '__module__', '__doc__', '__qualname__',
                   '__dict__', '__weakref__', '__firstlineno__', '__static_attributes__'}
        if (not isinstance(cls, type) or len(cls.__bases__) != 1
                or set(vars(cls)) - allowed
                or not isinstance(vars(cls).get('__init__'), FunctionType)):
            raise ValueError('Only explicit data-only vocabulary subclasses are supported')
        if i + 1 < len(classes) and cls.__bases__[0] is not classes[i + 1]:
            raise ValueError('Vocabulary prefix chain is not contiguous')
        original = cls.__init__
        code = Path(original.__code__.co_filename).resolve()
        if not code.is_relative_to(root) or code.relative_to(root).as_posix() not in pins:
            raise ValueError('Unpinned vocabulary constructor')
        originals[cls] = original
    _verify(root, pins)
    if not _LOCK.acquire(blocking=False):
        raise ValueError('A vocabulary session is already active')
    snapshots, wrappers = {}, {}
    stats = dict(hits=0, misses=0, bypasses=0)

    def wrap(cls, original):
        @wraps(original)
        def initialize(self, *args, **kwargs):
            if type(self) not in originals or args or kwargs or self.__dict__:
                stats['bypasses'] += 1
                return original(self, *args, **kwargs)
            if cls in snapshots:
                stats['hits'] += 1
                self.__dict__.update(deepcopy(snapshots[cls]))
                return None
            stats['misses'] += 1
            original(self)
            snapshots[cls] = deepcopy(self.__dict__)
            return None
        return initialize

    try:
        for cls, original in originals.items():
            wrappers[cls] = wrap(cls, original)
            cls.__init__ = wrappers[cls]
        yield stats
        if any(cls.__init__ is not wrappers[cls] for cls in classes):
            raise ValueError('Vocabulary constructor changed during session')
        _verify(root, pins)
    finally:
        for cls, original in originals.items():
            cls.__init__ = original
        snapshots.clear()
        _LOCK.release()
