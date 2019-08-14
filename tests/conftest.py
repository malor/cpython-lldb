import contextlib
import os
import shutil
import subprocess
import sys
import tempfile

import pytest


@contextlib.contextmanager
def strip_symbols(executable):
    libpython = subprocess.check_output("ldd %s | grep libpython | awk '{print $3}'" % (executable), shell=True).decode("utf-8").strip()
    libpython_backup = libpython + ".backup"

    try:
        subprocess.check_call("cp %s %s" % (libpython, libpython_backup), shell=True)
        subprocess.check_call("strip -S %s" % (libpython), shell=True)
        yield
    except Exception:
        pytest.skip("Cannot strip symbols")

    subprocess.check_call("cp %s %s" % (libpython_backup, libpython), shell=True)



def run_lldb(code, breakpoint, command, no_symbols=False):
    old_cwd = os.getcwd()
    d = tempfile.mkdtemp()
    try:
        with open('test.py', 'w') as fp:
            fp.write(code)

        args = [
            'lldb',
        ]
        if no_symbols:
            args += ['-o', 'settings set symbols.enable-external-lookup false']
        args += [
            sys.executable,
            '-o', 'breakpoint set -r %s' % (breakpoint),
            '-o', 'run "test.py"',
            '-o', command,
            '-o', 'quit'
        ]

        if no_symbols:
            with strip_symbols(sys.executable):
                return subprocess.check_output(args).decode('utf-8')
        else:
            return subprocess.check_output(args).decode('utf-8')
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(d, ignore_errors=True)
