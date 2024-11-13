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


def test_up_down(lldb):
    expected = """\
  File "test.py", line 11, in fb
    fa()
  File "test.py", line 15, in fc
    fb()
  File "test.py", line 18, in <module>
    fc()
  File "test.py", line 15, in fc
    fb()
  File "test.py", line 11, in fb
    fa()
  File "test.py", line 15, in fc
    fb()
""".rstrip()
    response = run_lldb(
        lldb,
        code=CODE,
        breakpoint="builtin_abs",
        commands=["py-up", "py-up", "py-up", "py-down", "py-down", "py-up"],
    )
    actual = "".join(response).rstrip()

    assert actual == expected


def test_newest_frame(lldb):
    expected = "*** Newest frame"
    response = run_lldb(
        lldb,
        code=CODE,
        breakpoint="builtin_abs",
        commands=["py-down"],
    )
    actual = "".join(response).rstrip()

    assert actual == expected


def test_oldest_frame(lldb):
    expected = """\
  File "test.py", line 11, in fb
    fa()
  File "test.py", line 15, in fc
    fb()
  File "test.py", line 18, in <module>
    fc()
*** Oldest frame
""".rstrip()
    response = run_lldb(
        lldb,
        code=CODE,
        breakpoint="builtin_abs",
        commands=["py-up"] * 4,
    )
    actual = "".join(response).rstrip()

    assert actual == expected
