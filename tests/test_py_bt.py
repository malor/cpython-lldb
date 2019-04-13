import itertools


from .conftest import run_lldb


def extract_traceback(response):
    before_start = lambda line: line != '(lldb) py-bt'
    before_end = lambda line: line != '(lldb) quit'
    lines = response.splitlines()

    return list(itertools.takewhile(before_end, itertools.dropwhile(before_start, lines)))[1:]


def assert_backtrace(code, breakpoint, expected):
    response = run_lldb(
        code=code,
        breakpoint=breakpoint,
        command='py-bt',
    )
    actual = u'\n'.join(extract_traceback(response))

    assert actual == expected


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
    abs(1)'''.lstrip()

    assert_backtrace(code, 'builtin_abs', backtrace)


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
    abs(1)'''.lstrip()

    assert_backtrace(code, 'builtin_abs', backtrace)
