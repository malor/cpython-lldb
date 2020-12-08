import collections
import re

from .conftest import run_lldb, extract_command_output


def lldb_repr_from_frame(value):
    # set a breakpoint in the implementation of the builtin function id(), that
    # is conveniently called with a single argument (v), which representation
    # we are trying to scrape from the LLDB output. When the breakpoint is hit,
    # the argument value will be pretty-printed by `frame info` command
    response = run_lldb(
        code='from collections import *; from six.moves import *; id(%s)' % value,
        breakpoint='builtin_id',
        commands=['frame info'],
    )

    actual = [
        line
        for line in response.splitlines()
        if 'frame #0' in line
    ][-1]
    match = re.search(r'v=(.*)\) at', actual)

    return match


def lldb_repr_from_register(value):
    # same as lldb_repr_from_frame(), but also works in cases when the CPython
    # build does not provide information on the arguments of builtin_id():
    # here we use the fact that the value of `v` argument is passed in the
    # CPU register RSI according to the rules of AMD64 calling convention
    response = run_lldb(
        code='from collections import *; from six.moves import *; id(%s)' % value,
        breakpoint='builtin_id',
        commands=['print (PyObject*) $rsi'],
    )
    actual = [
        line.strip()
        for line in response.splitlines()
        if '(PyObject *) $' in line
    ][-1]
    match = re.search(r'^\(PyObject \*\) \$[^=]+ = 0x[0-9a-f]+ (.*)$', actual)

    return match


def assert_lldb_repr(value, expected, code_value=None):
    value_repr = code_value or repr(value)
    match = lldb_repr_from_frame(value_repr) or lldb_repr_from_register(value_repr)
    assert match is not None

    if isinstance(value, (set, frozenset, dict)):
        # sets and dicts can have different order of keys depending on
        # CPython version, so we evaluate the representation and compare
        # it to the expected value
        _globals = {
            'Counter': collections.Counter,
            'OrderedDict': collections.OrderedDict,
        }
        assert value == eval(match.group(1), _globals, {})
    else:
        # for other data types we can do an exact string match using
        # a regular expression (e.g. to account for optional 'u' and 'b'
        # in unicode / bytes literals, etc)
        assert re.match(expected, match.group(1)), "Expected: %s\nActual: %s" % (expected, match.group(1))


def test_int():
    assert_lldb_repr(-10, '-10')
    assert_lldb_repr(0, '0')
    assert_lldb_repr(42, '42')
    assert_lldb_repr(-2 ** 32, '-4294967296')
    assert_lldb_repr(2 ** 32, '4294967296')
    assert_lldb_repr(-2 ** 64, '-18446744073709551616')
    assert_lldb_repr(2 ** 64, '18446744073709551616')


def test_bool():
    assert_lldb_repr(True, 'True')
    assert_lldb_repr(False, 'False')


def test_none():
    assert_lldb_repr(None, 'None')


def test_float():
    assert_lldb_repr(0.0, r'0\.0')
    assert_lldb_repr(42.42, r'42\.42')
    assert_lldb_repr(-42.42, r'-42\.42')


def test_bytes():
    assert_lldb_repr(b'', "b?''")
    assert_lldb_repr(b'hello', "b?'hello'")
    assert_lldb_repr(b'\x42\x42', "b?'BB'")
    assert_lldb_repr(b'\x42\x00\x42', r"b?'B\\x00B'")
    assert_lldb_repr(b'\x00\x00\x00\x00', r"b?'\\x00\\x00\\x00\\x00'")


def test_str():
    assert_lldb_repr('', "u?''")
    assert_lldb_repr('hello', "u?'hello'")
    assert_lldb_repr(u'привет',
                     "(u'\\\\u043f\\\\u0440\\\\u0438\\\\u0432\\\\u0435\\\\u0442')|('привет')")
    assert_lldb_repr(u'𐅐𐅀𐅰',
                     "(u'\\\\U00010150\\\\U00010140\\\\U00010170')|('𐅐𐅀𐅰')")
    assert_lldb_repr(u'æ', "(u'\\\\xe6')|('æ')")


def test_list():
    assert_lldb_repr([], r'\[\]')
    assert_lldb_repr([1, 2, 3], r'\[1, 2, 3\]')
    assert_lldb_repr([1, 3.14159, u'hello', False, None],
                     r'\[1, 3.14159, u?\'hello\', False, None\]')


def test_tuple():
    assert_lldb_repr((), r'\(\)')
    assert_lldb_repr((1, 2, 3), r'\(1, 2, 3\)')
    assert_lldb_repr((1, 3.14159, u'hello', False, None),
                     r'\(1, 3.14159, u?\'hello\', False, None\)')

def test_set():
    assert_lldb_repr(set(), r'set\(\[\]\)')
    assert_lldb_repr(set([1, 2, 3]), r'set\(\[1, 2, 3\]\)')
    assert_lldb_repr(set([1, 3.14159, u'hello', False, None]),
                     r'set\(\[False, 1, 3.14159, None, u\'hello\'\]\)')
    assert_lldb_repr(set(range(16)),
                     r'set\(\[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15\]\)')

def test_frozenset():
    assert_lldb_repr(frozenset(), r'frozenset\(\)')
    assert_lldb_repr(frozenset({1, 2, 3}), r'frozenset\(\{1, 2, 3\}\)')
    assert_lldb_repr(frozenset({1, 3.14159, u'hello', False, None}),
                     r'frozenset\(\[False, 1, 3.14159, None, u\'hello\'\]\)')
    assert_lldb_repr(frozenset(range(16)),
                     r'frozenset\(\{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15\}\)')

def test_dict():
    assert_lldb_repr({}, '{}')
    assert_lldb_repr({1: 2, 3: 4}, '{1: 2, 3: 4}')
    assert_lldb_repr({1: 2, 'a': 'b'}, "{1: 2, u'a': u'b'}")
    assert_lldb_repr({i: i for i in range(16)},
                     ('{0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,'
                      ' 9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14, 15: 15}'))

def test_defaultdict():
    assert_lldb_repr(collections.defaultdict(int), '{}', 'defaultdict(int)')
    assert_lldb_repr(collections.defaultdict(int, {1: 2, 3: 4}),
                     '{1: 2, 3: 4}',
                     'defaultdict(int, {1: 2, 3: 4})')
    assert_lldb_repr(collections.defaultdict(int, {1: 2, 'a': 'b'}),
                     "{1: 2, u'a': u'b'}",
                     "defaultdict(int, {1: 2, 'a': 'b'})")
    assert_lldb_repr(collections.defaultdict(int, {i: i for i in range(16)}),
                     ('{0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,'
                      ' 9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14, 15: 15}'),
                     'defaultdict(int, {i: i for i in range(16)})')


def test_ordered_dict():
    assert_lldb_repr(collections.OrderedDict(), 'OrderedDict()')
    assert_lldb_repr(collections.OrderedDict([(1, 2), (3, 4)]),
                     'OrderedDict([(1, 2), (3, 4)])')
    assert_lldb_repr(collections.OrderedDict([(1, 2), ('a', 'b')]),
                     "OrderedDict([(1, 2), ('a', 'b')])")
    assert_lldb_repr(collections.OrderedDict((i, i) for i in range(16)),
                     ('OrderedDict([(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), '
                      '(5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), '
                      '(11, 11), (12, 12), (13, 13), (14, 14), (15, 15)])'))


def test_userdict():
    assert_lldb_repr(collections.UserDict(), '{}', 'UserDict()')
    assert_lldb_repr(collections.UserDict({1: 2, 3: 4}),
                     '{1: 2, 3: 4}',
                     'UserDict({1: 2, 3: 4})')
    assert_lldb_repr(collections.UserDict({1: 2, 'a': 'b'}),
                     "{1: 2, u?'a': u?'b'}",
                     "UserDict({1: 2, 'a': 'b'})")
    assert_lldb_repr(collections.UserDict({i: i for i in range(16)}),
                     ('{0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,'
                      ' 9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14, 15: 15}'),
                     'UserDict({i: i for i in range(16)})')


def test_userstring():
    assert_lldb_repr(collections.UserString(''), "u?''",
                     'UserString("")')
    assert_lldb_repr(collections.UserString('hello'), "u?'hello'",
                     'UserString("hello")')
    assert_lldb_repr(collections.UserString(u'привет'),
                     "(u'\\\\u043f\\\\u0440\\\\u0438\\\\u0432\\\\u0435\\\\u0442')|('привет')",
                     'UserString(u"привет")')
    assert_lldb_repr(collections.UserString(u'𐅐𐅀𐅰'),
                     "(u'\\\\U00010150\\\\U00010140\\\\U00010170')|('𐅐𐅀𐅰')",
                     'UserString(u"𐅐𐅀𐅰")')
    assert_lldb_repr(collections.UserString(u'æ'),
                     "(u'\\\\xe6')|('æ')",
                     'UserString(u"æ")')


def test_userlist():
    assert_lldb_repr(collections.UserList(), r'\[\]',
                     'UserList()')
    assert_lldb_repr(collections.UserList([1, 2, 3]), r'\[1, 2, 3\]',
                     'UserList([1, 2, 3])')
    assert_lldb_repr(collections.UserList([1, 3.14159, u'hello', False, None]),
                     r'\[1, 3.14159, u?\'hello\', False, None\]',
                     'UserList([1, 3.14159, u"hello", False, None])')


def test_counter():
    assert_lldb_repr(collections.Counter(), 'Counter()')
    assert_lldb_repr(collections.Counter({1: 2, 3: 4}),
                     'Counter({1: 2, 3: 4})')
    assert_lldb_repr(collections.Counter({1: 2, 'a': 'b'}),
                     "Counter({1: 2, u'a': u'b'})")
    assert_lldb_repr(collections.Counter({i: i for i in range(16)}),
                     ('Counter({0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, '
                      '8: 8, 9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14, 15: 15})'))


def test_unsupported():
    assert_lldb_repr(object(), '(\'0x[0-9a-f]+\')|(\'No value\')', code_value='object()')


def test_locals_c_extension():
    code = 'import test_extension; test_extension.spam()'
    response = run_lldb(
        code=code,
        breakpoint='builtin_abs',
        commands=['bt'],
    )
    frame_match = re.search(r'.*frame #(\d+).*_test_extension.*`spam.*',
                            extract_command_output(response, 'bt'))
    if frame_match:
        frame_index = int(frame_match.groups()[0])

    # this could be replaced with a regex, but a plain string seems to be more readable
    expected_py2 = u'''\
(PyBytesObject *) local_bytes = 'eggs'
(PyDictObject *) local_dict = {u'foo': 42}
(PyFloatObject *) local_float = 0.0
(PyListObject *) local_list = [17, 18, 19]
(PyLongObject *) local_long = 17
(PyTupleObject *) local_tuple = (24, 23, 22)
(PyUnicodeObject *) local_unicode = u'hello'
'''.rstrip()

    expected_py3 = u'''\
(PyBytesObject *) local_bytes = b'eggs'
(PyDictObject *) local_dict = {'foo': 42}
(PyFloatObject *) local_float = 0.0
(PyListObject *) local_list = [17, 18, 19]
(PyLongObject *) local_long = 17
(PyTupleObject *) local_tuple = (24, 23, 22)
(PyUnicodeObject *) local_unicode = 'hello'
'''.rstrip()

    response = run_lldb(
        code=code,
        breakpoint='builtin_abs',
        commands=['up'] * frame_index + ['frame variable'],
    )
    actual = u'\n'.join(
        sorted(
            re.sub(r'(0x[0-9a-f]+ )', '', line)
            for line in extract_command_output(response, 'frame variable').splitlines()
            if u'local_' in line
        )
    )

    assert (actual == expected_py2) or (actual == expected_py3)
