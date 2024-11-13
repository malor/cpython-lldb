from .conftest import run_lldb


CODE = """
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
""".lstrip()


def test_default(lldb):
    expected = """\
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
""".rstrip()
    response = run_lldb(
        lldb,
        code=CODE,
        breakpoint="builtin_abs",
        commands=["py-list"],
    )[-1]
    actual = response.rstrip()

    assert actual == expected


def test_start(lldb):
    expected = """\
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
""".rstrip()
    response = run_lldb(
        lldb,
        code=CODE,
        breakpoint="builtin_abs",
        commands=["py-list 4"],
    )[-1]
    actual = response.rstrip()

    assert actual == expected


def test_start_end(lldb):
    expected = """\
    4    def fa():
   >5        abs(1)
    6        return 1
    7    
    8    
    9    def fb():
   10        1 + 1
   11        fa()
""".rstrip()
    response = run_lldb(
        lldb,
        code=CODE,
        breakpoint="builtin_abs",
        commands=["py-list 4 11"],
    )[-1]
    actual = response.rstrip()

    assert actual == expected


def test_non_default_encoding(lldb):
    head = "# coding: cp1251"
    code = (head + "\n\n" + CODE).encode("cp1251")

    expected = """\
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
""".rstrip()
    response = run_lldb(
        lldb,
        code=code,
        breakpoint="builtin_abs",
        commands=["py-list"],
    )[-1]
    actual = response.rstrip()

    assert actual == expected


def test_not_the_most_recent_frame(lldb):
    expected = """\
    6        return 1
    7    
    8    
    9    def fb():
   10        1 + 1
  >11        fa()
   12    
   13    
   14    def fc():
   15        fb()
   16    
""".rstrip()
    response = run_lldb(
        lldb,
        code=CODE,
        breakpoint="builtin_abs",
        commands=["py-up", "py-list"],
    )[-1]
    actual = response.rstrip()

    assert actual == expected
