import re

from .conftest import run_lldb


def test_simple(lldb):
    code = """
def fa():
    abs(1)
    return 1


def fb():
    1 + 1
    fa()


def fc():
    fb()


fc()
""".lstrip()

    backtrace = """
Traceback (most recent call last):
  File "test.py", line 15, in <module>
    fc()
  File "test.py", line 12, in fc
    fb()
  File "test.py", line 8, in fb
    fa()
  File "test.py", line 2, in fa
    abs(1)
""".strip()

    response = run_lldb(
        lldb,
        code=code,
        breakpoint="builtin_abs",
        commands=["py-bt"],
    )[-1]
    actual = response.rstrip()
    assert actual == backtrace


def test_simple_from_the_middle_of_the_call_stack(lldb):
    code = """
def fa():
    abs(1)
    return 1


def fb():
    1 + 1
    fa()


def fc():
    fb()


fc()
""".lstrip()

    response = run_lldb(
        lldb,
        code=code,
        breakpoint="builtin_abs",
        commands=["bt"],
    )[-1]
    pyframes = re.findall(
        r".*frame #(\d+).*(_PyEval_EvalFrameDefault|PyEval_EvalFrameEx).*", response
    )

    backtrace = """
Traceback (most recent call last):
  File "test.py", line 15, in <module>
    fc()
  File "test.py", line 12, in fc
    fb()
""".strip()

    response = run_lldb(
        lldb,
        code=code,
        breakpoint="builtin_abs",
        commands=["frame select %d" % int(pyframes[2][0]), "py-bt"],
    )[-1]
    actual = response.rstrip()
    assert actual == backtrace


def test_simple_from_the_middle_of_the_call_stack_no_pyframes_left(lldb):
    code = """
def fa():
    abs(1)
    return 1


def fb():
    1 + 1
    fa()


def fc():
    fb()


fc()
""".strip()

    response = run_lldb(
        lldb,
        code=code,
        breakpoint="builtin_abs",
        commands=["bt"],
    )[-1]
    pyframes = re.findall(
        r".*frame #(\d+).*(_PyEval_EvalFrameDefault|PyEval_EvalFrameEx).*", response
    )

    backtrace = "No Python traceback found"

    response = run_lldb(
        lldb,
        code=code,
        breakpoint="builtin_abs",
        commands=["frame select %d" % (int(pyframes[-1][0]) + 1), "py-bt"],
    )[-1]
    actual = response.rstrip()
    assert actual == backtrace


def test_class(lldb):
    code = """
class C(object):
    def ca(self):
        abs(1)

    def cb(self):
        self.ca()


class D(object):
    def __init__(self):
        self.f_class()

    @classmethod
    def f_class(cls):
        cls.f_static()

    @staticmethod
    def f_static():
        c = C()
        c.cb()


class E(D):
    @staticmethod
    def f_static():
        D()


E()
""".lstrip()

    backtrace = """
Traceback (most recent call last):
  File "test.py", line 29, in <module>
    E()
  File "test.py", line 11, in __init__
    self.f_class()
  File "test.py", line 15, in f_class
    cls.f_static()
  File "test.py", line 26, in f_static
    D()
  File "test.py", line 11, in __init__
    self.f_class()
  File "test.py", line 15, in f_class
    cls.f_static()
  File "test.py", line 20, in f_static
    c.cb()
  File "test.py", line 6, in cb
    self.ca()
  File "test.py", line 3, in ca
    abs(1)
""".strip()

    response = run_lldb(
        lldb,
        code=code,
        breakpoint="builtin_abs",
        commands=["py-bt"],
    )[-1]
    actual = response.rstrip()
    assert actual == backtrace


def test_without_symbols(lldb_no_symbols):
    code = """
def f():
    abs(1)

f()
""".lstrip()

    backtrace = "No Python traceback found"

    response = run_lldb(
        lldb_no_symbols,
        code=code,
        breakpoint="builtin_abs",
        commands=["py-bt"],
    )[-1]
    actual = response.rstrip()
    assert actual == backtrace


def test_no_backtrace(lldb):
    code = """
def f():
    abs(1)

f()
""".lstrip()

    backtrace = "No Python traceback found"

    response = run_lldb(
        lldb,
        code=code,
        breakpoint="__libc_start_main",
        commands=["py-bt"],
    )[-1]
    actual = response.rstrip()
    assert actual == backtrace


def test_frame_finding_heuristic_on_short_call_stacks(lldb):
    code = """
def f():
    abs(1)

f()
""".lstrip()

    backtrace = """
Traceback (most recent call last):
  File "test.py", line 4, in <module>
    f()
  File "test.py", line 2, in f
    abs(1)
""".strip()

    response = run_lldb(
        lldb,
        code=code,
        breakpoint="builtin_abs",
        commands=["py-bt"],
    )[-1]
    actual = response.rstrip()
    assert actual == backtrace


def test_c_extension(lldb):
    code = """
import test_extension

def f():
  return test_extension.eggs(g, v=42)

def g(v):
  return abs(v)

f()
""".lstrip()

    backtrace = """
Traceback (most recent call last):
  File "test.py", line 9, in <module>
    f()
  File "test.py", line 4, in f
    return test_extension.eggs(g, v=42)
  File "test.py", line 7, in g
    return abs(v)
""".strip()

    response = run_lldb(
        lldb,
        code=code,
        breakpoint="builtin_abs",
        commands=["py-bt"],
    )[-1]
    actual = response.rstrip()
    assert actual == backtrace
