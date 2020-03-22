from .conftest import run_lldb


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


def test_default():
    expected = u'''\
    1    SOME_CONST = u'тест'
    2    
    3    
    4    def fa():
   >5        abs(1)
    6        return 1
    7    
    8    
    9    def fb():
   10        1 + 1
'''
    actual = run_lldb(
        code=CODE,
        breakpoint='builtin_abs',
        command='py-list',
    )

    assert actual == expected


def test_start():
    expected = u'''\
    4    def fa():
   >5        abs(1)
    6        return 1
    7    
    8    
    9    def fb():
   10        1 + 1
   11        fa()
   12    
   13    
   14    def fc():
'''
    actual = run_lldb(
        code=CODE,
        breakpoint='builtin_abs',
        command='py-list 4',
    )

    assert actual == expected


def test_start_end():
    expected = u'''\
    4    def fa():
   >5        abs(1)
    6        return 1
    7    
    8    
    9    def fb():
   10        1 + 1
   11        fa()
'''
    actual = run_lldb(
        code=CODE,
        breakpoint='builtin_abs',
        command='py-list 4 11',
    )

    assert actual == expected


def test_non_default_encoding():
    head = u'# coding: cp1251'
    code = (head + '\n\n' + CODE).encode('cp1251')

    expected = u'''\
    2    
    3    SOME_CONST = u'тест'
    4    
    5    
    6    def fa():
   >7        abs(1)
    8        return 1
    9    
   10    
   11    def fb():
   12        1 + 1
'''
    actual = run_lldb(
        code=code,
        breakpoint='builtin_abs',
        command='py-list',
    )

    assert actual == expected
