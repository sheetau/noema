"""Deduplicate digest requests in one synchronous pin collection.

Every distinct path is hashed on first use and rehashed before returning.
No digest or validation outcome survives the context. Historical readers and
validators are restored on every exit, including failures.
"""
from contextlib import contextmanager
from pathlib import Path
from threading import Lock,get_ident

_LOCK=Lock()
_ACTIVE=None


@contextmanager
def digest_snapshot(owner, *, root):
    global _ACTIVE
    root=Path(root).resolve();thread=get_ident()
    if _ACTIVE is not None:
        active=_ACTIVE
        if (active['owner'] is not owner or active['root']!=root or active['thread']!=thread
                or owner.digest is not active['reader']):
            raise ValueError('Conflicting digest snapshot')
        yield active['stats']
        return
    original=getattr(owner,'digest',None)
    if not callable(original):raise ValueError('Missing digest reader')
    if not _LOCK.acquire(blocking=False):
        raise ValueError('Digest snapshot is already active')
    snapshot={}
    stats=dict(requests=0,first_reads=0,rechecks=0)
    def key(path):
        p=Path(path)
        if p.is_absolute() or not (root/p).resolve().is_relative_to(root):
            raise ValueError('Digest path outside pinned root')
        return p.as_posix()
    def reader(path):
        if get_ident()!=thread:raise ValueError('Digest snapshot is single-threaded')
        name=key(path);stats['requests']+=1
        if name not in snapshot:
            snapshot[name]=original(name);stats['first_reads']+=1
        return snapshot[name]
    try:
        _ACTIVE=dict(owner=owner,root=root,thread=thread,reader=reader,stats=stats)
        owner.digest=reader
        yield stats
        if owner.digest is not reader:raise ValueError('Digest reader changed during collection')
        for name,expected in snapshot.items():
            if original(key(name))!=expected:raise ValueError('Pinned input changed during collection: '+name)
            stats['rechecks']+=1
    finally:
        owner.digest=original
        snapshot.clear();_ACTIVE=None
        _LOCK.release()
