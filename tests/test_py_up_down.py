from .conftest import extract_command_output, run_lldb


CODE = u'''
SOME_CONST = u'тест'


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


def test_up_down():
    expected = u'''\
  File "test.py", line 11, in fb
    fa()
(lldb) py-up
  File "test.py", line 15, in fc
    fb()
(lldb) py-up
  File "test.py", line 18, in <module>
    fc()
(lldb) py-down
  File "test.py", line 15, in fc
    fb()
(lldb) py-down
  File "test.py", line 11, in fb
    fa()
(lldb) py-up
  File "test.py", line 15, in fc
    fb()
'''
    response = run_lldb(
        code=CODE,
        breakpoint='builtin_abs',
        commands=['py-up', 'py-up', 'py-up', 'py-down', 'py-down', 'py-up'],
    )
    actual = extract_command_output(response, 'py-up')

    assert actual == expected


def test_newest_frame():
    expected = u'*** Newest frame\n'
    response = run_lldb(
        code=CODE,
        breakpoint='builtin_abs',
        commands=['py-down'],
    )
    actual = extract_command_output(response, 'py-down')

    assert actual == expected


def test_oldest_frame():
    expected = u'''\
  File "test.py", line 11, in fb
    fa()
(lldb) py-up
  File "test.py", line 15, in fc
    fb()
(lldb) py-up
  File "test.py", line 18, in <module>
    fc()
(lldb) py-up
*** Oldest frame
'''
    response = run_lldb(
        code=CODE,
        breakpoint='builtin_abs',
        commands=['py-up'] * 4,
    )
    actual = extract_command_output(response, 'py-up')

    assert actual == expected
