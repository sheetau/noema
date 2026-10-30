import json
import sqlite3
import time

import pytest

from scripts.long_run import LongRun, PauseRequested


def test_pause_keeps_committed_step_and_retries_unfinished_step(tmp_path):
    path = tmp_path / 'run'; calls = []
    with pytest.raises(PauseRequested):
        with LongRun(path, {'input': 'fixed'}) as run:
            run.step('one', {}, lambda: calls.append('one') or {'value': 1})
            def interrupted():
                calls.append('two')
                (path / 'PAUSE').touch()
                run.boundary()
            run.step('two', {}, interrupted)
    assert json.loads((path / 'status.json').read_text())['status'] == 'paused'
    (path / 'PAUSE').unlink()
    with LongRun(path, {'input': 'fixed'}, resume=True) as run:
        assert run.step('one', {}, lambda: pytest.fail('Repeated completed step')) == {'value': 1}
        run.step('two', {}, lambda: calls.append('two') or True)
    assert calls == ['one', 'two', 'two']


def test_resume_refuses_changed_inputs_and_concurrent_owner(tmp_path):
    path = tmp_path / 'run'
    with LongRun(path, {'sha': 'one'}):
        with pytest.raises(ValueError, match='owned'):
            with LongRun(path, {'sha': 'one'}, resume=True): pass
    with pytest.raises(ValueError, match='changed'):
        with LongRun(path, {'sha': 'two'}, resume=True): pass
    # Failed acquisition/manifest validation releases its own handles.
    with LongRun(path, {'sha': 'one'}, resume=True): pass


def test_heartbeat_and_reuse_validation_and_corruption(tmp_path):
    path = tmp_path / 'run'
    with LongRun(path, {}, heartbeat=0.02) as run:
        with run.activity('slow item'):
            time.sleep(0.08)
        run.step('result', {}, lambda: {'output_sha': 'known'})
    rows = [json.loads(line) for line in (path / 'events.jsonl').read_text().splitlines()]
    assert any(row['event'] == 'heartbeat' and row['active'] == ['slow item'] for row in rows)
    def reject(_): raise ValueError('Output changed')
    with pytest.raises(ValueError, match='Output changed'):
        with LongRun(path, {}, resume=True) as run:
            run.step('result', {}, lambda: None, validate=reject)
    db = sqlite3.connect(path / 'steps.sqlite')
    db.execute("UPDATE steps SET value='null'"); db.commit(); db.close()
    with pytest.raises(ValueError, match='Damaged'):
        with LongRun(path, {}, resume=True) as run:
            run.step('result', {}, lambda: None)


def test_killed_process_retains_only_committed_steps(tmp_path):
    import os
    from pathlib import Path
    import subprocess
    import sys
    path = tmp_path / 'run'
    script = tmp_path / 'child.py'
    script.write_text('''import os,sys
from scripts.long_run import LongRun
with LongRun(sys.argv[1], {}) as run:
    run.step('done', {}, lambda: 42)
    run.step('unfinished', {}, lambda: os._exit(7))
''', encoding='utf-8')
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    result = subprocess.run([sys.executable, '-X', 'utf8', str(script), str(path)],
                            env=environment, creationflags=0x08000000 if os.name == 'nt' else 0)
    assert result.returncode == 7
    with LongRun(path, {}, resume=True) as run:
        assert run.step('done', {}, lambda: pytest.fail('Lost durable step')) == 42
        assert run.step('unfinished', {}, lambda: 'retried') == 'retried'
