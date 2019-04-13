# coding: utf-8

import itertools
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


class BaseTestCase(unittest.TestCase):
    def run_lldb(self, code, breakpoint, command):
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

    @staticmethod
    def extract_traceback(response):
        before_start = lambda line: line != '(lldb) py-bt'
        before_end = lambda line: line != '(lldb) quit'
        lines = response.splitlines()

        return list(itertools.takewhile(before_end, itertools.dropwhile(before_start, lines)))[1:]


class TestPrettyPrint(BaseTestCase):
    def assert_lldb_repr(self, value, expected, code_value=None):
        response = self.run_lldb(
            code='id(%s)' % (code_value or repr(value)),
            breakpoint='builtin_id',
            command='frame info',
        )

        actual = [
            line
            for line in response.splitlines()
            if 'frame #0' in line
        ][-1]
        match = re.search(r'v=(.*)\) at', actual)
        self.assertIsNotNone(match)

        if isinstance(value, (set, dict)):
            # sets and dicts can have different order of keys depending on
            # CPython version, so we evaluate the representation and compare
            # it to the expected value
            self.assertEqual(value, eval(match.group(1), {}, {}))
        else:
            # for other data types we can do an exact string match using
            # a regular expression (e.g. to account for optional 'u' and 'b'
            # in unicode / bytes literals, etc)
            self.assertTrue(
                re.match(expected, match.group(1)),
                "Expected: %s\nActual: %s" % (expected, match.group(1))
            )

    def test_int(self):
        self.assert_lldb_repr(-10, '-10')
        self.assert_lldb_repr(0, '0')
        self.assert_lldb_repr(42, '42')
        self.assert_lldb_repr(-2 ** 32, '-4294967296')
        self.assert_lldb_repr(2 ** 32, '4294967296')
        self.assert_lldb_repr(-2 ** 64, '-18446744073709551616')
        self.assert_lldb_repr(2 ** 64, '18446744073709551616')

    def test_bool(self):
        self.assert_lldb_repr(True, 'True')
        self.assert_lldb_repr(False, 'False')

    def test_none(self):
        self.assert_lldb_repr(None, 'None')

    def test_float(self):
        self.assert_lldb_repr(0.0, '0\.0')
        self.assert_lldb_repr(42.42, '42\.42')
        self.assert_lldb_repr(-42.42, '-42\.42')

    def test_bytes(self):
        self.assert_lldb_repr(b'', "b?''")
        self.assert_lldb_repr(b'hello', "b?'hello'")
        self.assert_lldb_repr(b'\x42\x42', "b?'BB'")
        self.assert_lldb_repr(b'\x42\x00\x42', r"b?'B\\x00B'")
        self.assert_lldb_repr(b'\x00\x00\x00\x00', r"b?'\\x00\\x00\\x00\\x00'")

    def test_str(self):
        self.assert_lldb_repr('', "u''")
        self.assert_lldb_repr('hello', "u'hello'")
        self.assert_lldb_repr(u'привет',
                              "u'\\\\u043f\\\\u0440\\\\u0438\\\\u0432\\\\u0435\\\\u0442'")
        self.assert_lldb_repr(u'𐅐𐅀𐅰',
                              "u'\\\\U00010150\\\\U00010140\\\\U00010170'")

    def test_list(self):
        self.assert_lldb_repr([], '\[\]')
        self.assert_lldb_repr([1, 2, 3], '\[1, 2, 3\]')
        self.assert_lldb_repr([1, 3.14159, u'hello', False, None],
                              '\[1, 3.14159, u\'hello\', False, None\]')

    def test_tuple(self):
        self.assert_lldb_repr((), '\(\)')
        self.assert_lldb_repr((1, 2, 3), '\(1, 2, 3\)')
        self.assert_lldb_repr((1, 3.14159, u'hello', False, None),
                              '\(1, 3.14159, u\'hello\', False, None\)')

    def test_set(self):
        self.assert_lldb_repr(set(), 'set\(\[\]\)')
        self.assert_lldb_repr(set([1, 2, 3]), 'set\(\[1, 2, 3\]\)')
        self.assert_lldb_repr(set([1, 3.14159, u'hello', False, None]),
                              'set\(\[False, 1, 3.14159, None, u\'hello\'\]\)')
        self.assert_lldb_repr(set(range(16)),
                              'set\(\[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15\]\)')

    def test_dict(self):
        self.assert_lldb_repr({}, '{}')
        self.assert_lldb_repr({1: 2, 3: 4}, '{1: 2, 3: 4}')
        self.assert_lldb_repr({1: 2, 'a': 'b'}, "{1: 2, u'a': u'b'}")
        self.assert_lldb_repr({i: i for i in range(16)},
                              ('{0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,'
                               ' 9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14, 15: 15}'))

    def test_unsupported(self):
        self.assert_lldb_repr(object(), '\'0x[0-9a-f]+\'', code_value='object()')


class TestPacktrace(BaseTestCase):
    maxDiff = 2000

    def assert_backtrace(self, code, breakpoint, expected):
        response = self.run_lldb(
            code=code,
            breakpoint=breakpoint,
            command='py-bt',
        )
        actual = u'\n'.join(self.extract_traceback(response))

        self.assertEqual(actual, expected)

    def test_simple(self):
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

        backtrace = '''Traceback (most recent call last):
  File "test.py", line 15, in <module>
    fc()
  File "test.py", line 12, in fc
    fb()
  File "test.py", line 8, in fb
    fa()
  File "test.py", line 2, in fa
    abs(1)'''

        self.assert_backtrace(code, 'builtin_abs', backtrace)

    def test_class(self):
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

        backtrace = '''Traceback (most recent call last):
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
    abs(1)'''

        self.assert_backtrace(code, 'builtin_abs', backtrace)


if __name__ == "__main__":
    unittest.main()
