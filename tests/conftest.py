import os
import shutil
import subprocess
import sys
import tempfile


def run_lldb(code, breakpoint, command):
    old_cwd = os.getcwd()
    d = tempfile.mkdtemp()
    try:
        with open('test.py', 'w') as fp:
            fp.write(code)
        args = [
            'lldb',
            sys.executable,
            '-o', 'breakpoint set -r %s' % (breakpoint),
            '-o', 'run "test.py"',
            '-o', command,
            '-o', 'quit'
        ]
        return subprocess.check_output(args).decode('utf-8')
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(d, ignore_errors=True)
