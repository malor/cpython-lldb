# coding: utf-8

import os
import re
import subprocess
import sys
import unittest


class BaseTestCase(unittest.TestCase):
    def assert_lldb_repr(self, value, expected, code_value=None):
        args = [
            'lldb',
            sys.executable,
            '-o', 'breakpoint set -r builtin_id',
            '-o', 'run -c "id(%s)"' % (code_value or repr(value)),
            '-o', 'script import sys',
            '-o', 'script sys.path.insert(0, "%s")' % os.path.dirname(os.path.abspath(__file__)),
            '-o', 'command script import cpython_lldb',
            '-o', 'frame info',
            '-o', 'quit'
        ]

        actual = [
            line
            for line in subprocess.check_output(args).decode('utf-8').splitlines()
            if 'frame #0' in line
        ][-1]
        match = re.search('v=' + expected, actual)
        self.assertIsNotNone(match, "Expected output '%s' is not found in '%s'" % (expected, actual))


class TestPrettyPrint(BaseTestCase):
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


if __name__ == "__main__":
    unittest.main()
