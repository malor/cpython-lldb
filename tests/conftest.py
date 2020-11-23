import io
import itertools
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest


@pytest.fixture
def strip_symbols():
    executable = sys.executable

    libpython = subprocess.check_output("ldd %s | grep libpython | awk '{print $3}'" % (executable), shell=True).decode("utf-8").strip()
    libpython_backup = libpython + ".backup"

    try:
        subprocess.check_call("cp %s %s" % (libpython, libpython_backup), shell=True)
        subprocess.check_call("strip -S %s" % (libpython), shell=True)
        yield
    except Exception:
        pytest.skip("Cannot strip symbols")

    subprocess.check_call("cp %s %s" % (libpython_backup, libpython), shell=True)


def extract_command_output(lldb_output, command):
    wo_head = itertools.dropwhile(lambda line: line != '(lldb) {}'.format(command),
                                  lldb_output.splitlines())
    wo_tail = itertools.takewhile(lambda line: line != '(lldb) quit',
                                  wo_head)

    return u'\n'.join(list(wo_tail)[1:]) + '\n'


def normalize_stacktrace(trace):
    """Replace absolute paths in a stacktrace to make them consistent between runs."""

    return re.sub('File "(.*)test.py"', 'File "test.py"', trace)


def run_lldb(code, breakpoint, commands, no_symbols=False):
    commands = list(itertools.chain(*(('-o', command) for command in commands)))

    old_cwd = os.getcwd()
    d = tempfile.mkdtemp()
    os.chdir(d)
    try:
        with io.open('test.py', 'wb') as fp:
            if isinstance(code, str):
                code = code.encode('utf-8')

            fp.write(code)

        args = ['lldb']
        if no_symbols:
            args += ['-o', 'settings set symbols.enable-external-lookup false']
        args += [
            sys.executable,
            '-o', 'breakpoint set -r %s' % (breakpoint),
            '-o', 'run "test.py"',
            *commands,
            '-o', 'quit'
        ]

        return normalize_stacktrace(
            subprocess.check_output(args).decode('utf-8'))
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(d, ignore_errors=True)
