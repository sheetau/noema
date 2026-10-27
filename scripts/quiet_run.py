"""Run a module or script without Windows child console windows.

Usage: python -X utf8 -m scripts.quiet_run -m scripts.project_work ...
       python -X utf8 -m scripts.quiet_run path/to/script.py ...

The scoped adapter covers subprocess and multiprocessing launches in this
interpreter, without editing historical validators or their evidence. It does
not retrofit running processes or install a hook in arbitrary descendants.
"""
from contextlib import contextmanager
from copy import copy
import os
from pathlib import Path
import runpy
import subprocess
import sys


@contextmanager
def hidden_children():
    if os.name != 'nt':
        yield
        return
    # Both subprocess and multiprocessing call this Windows API. Patching only
    # subprocess.Popen would leave ProcessPoolExecutor workers opening consoles.
    import _winapi
    original = _winapi.CreateProcess

    def create_process(application, command, proc_attrs, thread_attrs, inherit,
                       flags, environment, directory, startup):
        startup = copy(startup)
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        return original(application, command, proc_attrs, thread_attrs, inherit,
                        flags | subprocess.CREATE_NO_WINDOW,
                        environment, directory, startup)

    _winapi.CreateProcess = create_process
    try:
        yield
    finally:
        _winapi.CreateProcess = original


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if args else 2
    module = args[0] == '-m'
    if module:
        args.pop(0)
    if not args or args[0].startswith('-'):
        raise SystemExit('Supply -m MODULE or SCRIPT, followed by its arguments')
    previous = sys.argv
    sys.argv = args
    try:
        with hidden_children():
            if module:
                runpy.run_module(args[0], run_name='__main__', alter_sys=True)
            else:
                previous_path = sys.path[:]
                sys.path.insert(0, str(Path(args[0]).resolve().parent))
                try:
                    runpy.run_path(args[0], run_name='__main__')
                finally:
                    sys.path[:] = previous_path
    finally:
        sys.argv = previous
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
