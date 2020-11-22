import pytest

from .conftest import extract_command_output, run_lldb


def test_simple():
    code = '''
def fa():
    abs(1)
    return 1


def fb():
    1 + 1
    fa()


def fc():
    fb()


fc()
'''.lstrip()

    backtrace = '''
Traceback (most recent call last):
  File "test.py", line 15, in <module>
    fc()
  File "test.py", line 12, in fc
    fb()
  File "test.py", line 8, in fb
    fa()
  File "test.py", line 2, in fa
    abs(1)
'''.lstrip()

    response = run_lldb(
        code=code,
        breakpoint='builtin_abs',
        commands=['py-bt'],
    )
    actual = extract_command_output(response, 'py-bt')
    assert actual == backtrace


def test_class():
    code = '''
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
'''.lstrip()

    backtrace = '''
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
'''.lstrip()

    response = run_lldb(
        code=code,
        breakpoint='builtin_abs',
        commands=['py-bt'],
    )
    actual = extract_command_output(response, 'py-bt')
    assert actual == backtrace


@pytest.mark.serial  # strip_symbols does not play nicely with other tests when run in parallel
@pytest.mark.usefixtures('strip_symbols')
def test_without_symbols():
    code = '''
def f():
    abs(1)

f()
'''.lstrip()

    backtrace = 'No Python traceback found (symbols might be missing)!\n'

    response = run_lldb(
        code=code,
        breakpoint='builtin_abs',
        commands=['py-bt'],
        no_symbols=True,
    )
    actual = extract_command_output(response, 'py-bt')
    assert actual == backtrace


def test_no_backtrace():
    code = '''
def f():
    abs(1)

f()
'''.lstrip()

    backtrace = 'No Python traceback found (symbols might be missing)!\n'

    response = run_lldb(
        code=code,
        breakpoint='breakpoint_does_not_exist',
        commands=['py-bt'],
        no_symbols=True,
    )
    actual = extract_command_output(response, 'py-bt')
    assert actual == backtrace


def test_frame_finding_heuristic_on_short_call_stacks():
    code = u'''
def f():
    abs(1)

f()
'''.lstrip()

    backtrace = u'''
Traceback (most recent call last):
  File "test.py", line 4, in <module>
    f()
  File "test.py", line 2, in f
    abs(1)
'''.lstrip()

    response = run_lldb(
        code=code,
        breakpoint='builtin_abs',
        commands=['py-bt'],
    )
    actual = extract_command_output(response, 'py-bt')
    assert actual == backtrace
