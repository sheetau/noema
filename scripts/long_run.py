"""Durable JSON steps, cooperative pause, heartbeat and exclusive run ownership.

Use small deterministic steps; a killed, uncommitted step is run again.
This does not checkpoint an instruction pointer or make arbitrary side effects safe.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import time


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    # Windows indexers/readers can briefly deny an otherwise valid replace.
    # Keep the flushed temporary file and the prior destination intact while
    # retrying only this atomic operation; persistent failures still escape.
    for attempt in range(5):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt==4:raise
            time.sleep(.01*3**attempt)


class PauseRequested(Exception):
    pass


class LongRun:
    """One owner, immutable input manifest, JSON-only committed step results."""
    def __init__(self, directory, manifest, *, resume=False, heartbeat=15):
        self.directory = Path(directory)
        self.manifest = manifest
        self.resume = resume
        if heartbeat <= 0 or heartbeat > 60:
            raise ValueError('Heartbeat must be in (0, 60] seconds')
        self.heartbeat = heartbeat
        self.stop = threading.Event()
        self.mutex = threading.RLock()
        self.started = time.monotonic()
        self.state = dict(status='starting', stage='initializing', completed=0,
                          total=None, total_is_time_estimate=False, active=[], reused=0)

    def __enter__(self):
        if self.resume:
            if not (self.directory / 'manifest.json').is_file():
                raise ValueError('Resume requires an existing run manifest')
        else:
            self.directory.mkdir(parents=True, exist_ok=False)
        self.lock = (self.directory / 'owner.lock').open('a+b')
        try:
            self.lock.seek(0)
            if os.name == 'nt':
                import msvcrt
                if self.lock.read(1) == b'':
                    self.lock.write(b'0'); self.lock.flush()
                self.lock.seek(0); msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock.close()
            raise ValueError('Run already owned by another process') from None
        try:
            path = self.directory / 'manifest.json'
            if self.resume:
                if json.loads(path.read_text(encoding='utf-8')) != self.manifest:
                    raise ValueError('Inputs or implementation changed; use a new run')
            else:
                atomic_json(path, self.manifest)
            self.db = sqlite3.connect(self.directory / 'steps.sqlite')
            self.db.execute('PRAGMA journal_mode=WAL')
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('CREATE TABLE IF NOT EXISTS steps (key TEXT PRIMARY KEY, value TEXT, sha TEXT)')
            self.state['committed_steps'] = self.db.execute('SELECT COUNT(*) FROM steps').fetchone()[0]
            self.events = (self.directory / 'events.jsonl').open('a', encoding='utf-8', newline='\n')
            self.state['status'] = 'running'
            self.emit('resume' if self.resume else 'start')
            self.thread = threading.Thread(target=self._heartbeat, daemon=True)
            self.thread.start()
            return self
        except BaseException:
            if hasattr(self, 'db'): self.db.close()
            if hasattr(self, 'events'): self.events.close()
            self.lock.close()
            raise

    def emit(self, event, **updates):
        with self.mutex:
            self.state.update(updates)
            row = dict(self.state, event=event, pid=os.getpid(),
                       utc=datetime.now(timezone.utc).isoformat(),
                       attempt_seconds=round(time.monotonic() - self.started, 3))
            self.events.write(json.dumps(row, ensure_ascii=False) + '\n')
            self.events.flush(); os.fsync(self.events.fileno())
            atomic_json(self.directory / 'status.json', row)

    def _heartbeat(self):
        while not self.stop.wait(self.heartbeat):
            try:
                self.emit('heartbeat')
            except OSError as error:
                self.heartbeat_error = error
                return

    def boundary(self):
        if hasattr(self, 'heartbeat_error'):
            raise self.heartbeat_error
        if (self.directory / 'PAUSE').exists():
            raise PauseRequested('Pause requested; committed steps retained')

    @contextmanager
    def activity(self, name):
        self.boundary()
        with self.mutex:
            previous = list(self.state['active'])
            self.emit('unit_start', active=previous + [name])
        try:
            yield
        finally:
            self.emit('unit_end', active=previous)

    def step(self, key, inputs, action, *, validate=lambda value: None):
        """Validate on reuse; action must return JSON and handle partial side effects."""
        self.boundary()
        identity = fingerprint([key, inputs])
        row = self.db.execute('SELECT value,sha FROM steps WHERE key=?', (identity,)).fetchone()
        if row is not None:
            if hashlib.sha256(row[0].encode('utf-8')).hexdigest() != row[1]:
                raise ValueError('Damaged checkpoint: ' + key)
            result = json.loads(row[0]); validate(result)
            self.emit('step_reused', reused=self.state['reused'] + 1, step=key)
            return result
        with self.activity(key):
            result = action(); validate(result)
            raw = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
            self.db.execute('INSERT INTO steps VALUES (?,?,?)',
                            (identity, raw, hashlib.sha256(raw.encode('utf-8')).hexdigest()))
            self.db.commit()
        self.emit('step_committed', step=key, committed_steps=self.state['committed_steps'] + 1)
        self.boundary()
        return result

    def __exit__(self, typ, error, tb):
        self.stop.set(); self.thread.join()
        try:
            status = 'complete' if typ is None else 'paused' if issubclass(typ, (PauseRequested, KeyboardInterrupt)) else 'failed'
            self.emit(status, status=status, error=None if error is None else str(error))
        finally:
            self.events.close(); self.db.close(); self.lock.close()
        return False
