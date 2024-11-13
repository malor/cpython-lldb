import contextlib
import io
import re
import os
import subprocess
import sys

import pexpect
import pytest


@pytest.fixture(scope="session")
def lldb_session(tmpdir_factory):
    """Starts LLDB in the background with Python as the target process.

    LLDB is started via pexpect.spawn; bidirectional communication with the child process is
    performed via pipes attached to its stdin/stdout/stderr.

    This fixture has the session scope, so that LLDB is only launched once and reused across
    different tests. That is managed via a separate, function-scoped fixture -- lldb.
    """

    session = pexpect.spawn(
        "lldb",
        args=["-O", "settings set use-color 0", sys.executable],
        cwd=tmpdir_factory.mktemp("lldb").strpath,
        encoding="utf-8",
        timeout=6,
        maxread=65536,
        env={
            "PYTHONDONTWRITEBYTECODE": "true",
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
            "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", "1"),
            "LANG": os.environ.get("LANG"),
        },
    )
    session.expect("Current executable set to")

    yield session


@pytest.fixture(scope="session")
def lldb_no_symbols_session(tmpdir_factory):
    """Starts LLDB in the background with Python as the target process.

    Same as lldb_session, but also creates a copy of libpython w/o debugging symbols and updates
    LD_LIBRARY_PATH to point to it.
    """

    tmpdir = tmpdir_factory.mktemp("lldb")
    with tmpdir.as_cwd():
        libpython = (
            subprocess.check_output(
                "ldd %s | grep libpython | awk '{print $3}'" % (sys.executable),
                shell=True,
            )
            .decode("utf-8")
            .strip()
        )
        libpython_copy = tmpdir.join(os.path.basename(libpython)).strpath
        subprocess.check_call(["cp", libpython, libpython_copy])
        subprocess.check_call(["strip", "-S", libpython_copy])

    session = pexpect.spawn(
        "lldb",
        args=["-O", "settings set use-color 0", sys.executable],
        cwd=tmpdir.strpath,
        encoding="utf-8",
        timeout=6,
        maxread=65536,
        env={
            "PYTHONDONTWRITEBYTECODE": "true",
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
            "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", "1"),
            "LD_LIBRARY_PATH": ".",
            "LANG": os.environ.get("LANG"),
        },
    )
    session.expect("Current executable set to")

    yield session


@contextlib.contextmanager
def _lldb_manager(lldb_session):
    prev_cwd = os.getcwd()
    os.chdir(lldb_session.cwd)

    try:
        yield lldb_session
    finally:
        os.chdir(prev_cwd)

        lldb_session.sendline("kill")
        lldb_session.expect(re.compile(r"Process \d+ exited"))
        lldb_session.expect(re.escape("(lldb) "))
        lldb_session.sendline("breakpoint delete --force")
        lldb_session.expect("All breakpoints removed. ")
        lldb_session.expect(re.escape("(lldb) "))


@pytest.fixture
def lldb(lldb_session):
    """Re-usable LLDB session.

    Returns a context manager that can be used to retrieve a pexpect.spawn handle controlling an
    LLDB instance running in the background. The context manager will automatically clean up the
    state (such as breakpoints) and terminate the Python process under debug, so that another
    session can be created w/o restarting LLDB.

    As a side effect, the context manager will temporarily change the current working directory
    created for this LLDB instance.
    """

    return lambda: _lldb_manager(lldb_session)


@pytest.fixture
def lldb_no_symbols(lldb_no_symbols_session):
    """Same as lldb, but uses a copy of libpython with stripped debugging symbols."""

    return lambda: _lldb_manager(lldb_no_symbols_session)


def normalize_stacktrace(trace):
    """Replace absolute paths in a stacktrace to make them consistent between runs."""

    return re.sub('File "(.*)test.py"', 'File "test.py"', trace)


def run_lldb(lldb_manager, code, breakpoint, commands):
    """Run arbitrary LLDB commands after the given Python snippets hits a specified breakpoint.

    Returns a list that contains an output each command has produced. As a side effect, absolute
    paths in the stacktraces are automatically truncated to the final (i.e. file name) part.
    """

    outputs = []

    with lldb_manager() as lldb:
        with io.open("test.py", "wb") as fp:
            if isinstance(code, str):
                code = code.encode("utf-8")

            fp.write(code)

        lldb.sendline("breakpoint set -r %s" % breakpoint)
        lldb.expect(r"Breakpoint \d+")
        lldb.expect(re.escape("(lldb) "))
        lldb.sendline("run test.py")
        lldb.expect(r"Process \d+ stopped")
        lldb.expect(re.escape("(lldb) "))

        for command in commands:
            lldb.sendline(command)
            lldb.expect(re.escape("%s\r\n" % command))
            lldb.expect(re.escape("(lldb) "))

            outputs.append(normalize_stacktrace(lldb.before.replace("\r\n", "\n")))

    return outputs
