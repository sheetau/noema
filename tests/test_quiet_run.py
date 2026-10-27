import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.quiet_run import hidden_children, main


def console_handle():
    import ctypes
    return ctypes.windll.kernel32.GetConsoleWindow()


@pytest.mark.skipif(os.name != 'nt', reason='Windows console behavior')
def test_python_shell_and_pool_have_no_console():
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing
    with hidden_children():
        code = 'import ctypes; print(ctypes.windll.kernel32.GetConsoleWindow())'
        direct = subprocess.run([sys.executable, '-c', code], capture_output=True,
                                text=True, check=True)
        assert direct.stdout.strip() == '0'
        shell = subprocess.run(subprocess.list2cmdline([sys.executable, '-c', code]),
                               shell=True, capture_output=True, text=True, check=True)
        assert shell.stdout.strip() == '0'
        with ProcessPoolExecutor(1, mp_context=multiprocessing.get_context('spawn')) as pool:
            assert pool.submit(console_handle).result(timeout=30) == 0


def test_streams_input_exit_status_and_arguments_are_preserved():
    with hidden_children():
        result = subprocess.run([sys.executable, '-c',
            'import sys; print(sys.stdin.read()+sys.argv[1]); '
            'print("failure",file=sys.stderr); sys.exit(7)', 'a b'],
            input='input:', capture_output=True, text=True)
    assert result.stdout.strip() == 'input:a b'
    assert result.stderr.strip() == 'failure'
    assert result.returncode == 7


def test_script_exit_and_state_restored(tmp_path):
    script = tmp_path / 'target.py'
    script.write_text('import sys\nassert sys.argv[1:] == ["a b"]\nraise SystemExit(9)\n',
                      encoding='utf-8')
    previous_argv, previous_path = sys.argv, list(sys.path)
    if os.name == 'nt':
        import _winapi
        original = _winapi.CreateProcess
    with pytest.raises(SystemExit) as error:
        main([str(script), 'a b'])
    assert error.value.code == 9
    assert sys.argv is previous_argv
    assert sys.path == previous_path
    if os.name == 'nt':
        assert _winapi.CreateProcess is original


def test_module_cli_preserves_nonzero_exit():
    with hidden_children():
        result = subprocess.run([sys.executable, '-m', 'scripts.quiet_run',
            '-m', 'noema', 'definitely-not-a-command'],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    assert result.returncode == 2
    assert 'invalid choice' in result.stderr
