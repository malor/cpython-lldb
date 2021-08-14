Overview
========

[![Build Status](https://travis-ci.org/malor/cpython-lldb.svg?branch=master)](https://travis-ci.org/malor/cpython-lldb)

`cpython_lldb` is an LLDB extension for debugging Python programs.

It may be useful for troubleshooting stuck threads and crashes in the interpreter,
or external libraries. Unlike most Python debuggers, LLDB allows you to attach to
a running process w/o instrumenting it in advance, or load a coredump and do a
post-mortem analysis of a problem.

When analyzing the state of a Python process, normally you would only have
access to the *intepreter-level* information: every variable would be of type
PyObject\*, and stack traces would only contain CPython internal calls and
calls to external libraries. Unless you are a CPython developer troubleshooting
some bug in the implementation of the interpreter, that is typically not
very useful. This extension, however, allows you to extract the *application-level*
information about execution of a program: print the values of variables,
list the source code, display Python stack traces, etc.

While CPython itself provides a similar extension for gdb [out of the box](
https://github.com/python/cpython/blob/master/Tools/gdb/libpython.py),
one might still prefer to use LLDB as a debugger, e.g. on Mac OS.

`cpython_lldb` requires CPython to be built with debugging symbols, which is
not the case for some Linux distros (most notably Arch Linux). CPython official
[Docker images](https://hub.docker.com/_/python) are known to work correctly,
as they are used for integration testing.


Features
========

`cpython_lldb` targets CPython 3.5+ and supports the following features:

* pretty-priting of built-in types (int, bool, float, bytes, str, none, tuple, list, set, frozenset, dict)
* printing of Python-level stack traces
* printing of local variables
* listing the source code
* walking up and down the Python call stack

TODO:

* stack traces w/ mixed stacks (e.g. involving calls to clibs)


Installation
============

If your version of LLDB is linked against system libpython, it's recommended
that you install the extension to the user site packages directory and allow
it to be loaded automatically on start of a new LLDB session:

```shell
$ python -m pip install --user cpython-lldb
$ echo "command script import cpython_lldb" >> ~/.lldbinit
$ chmod +x ~/.lldbinit
```

Alternatively, you can install the extension to some other location on disk
and tell LLDB to load it from there, e.g. ~/.lldb:

```shell
$ mkdir -p ~/.lldb/cpython_lldb
$ python -m pip install --target ~/.lldb/cpython_lldb cpython-lldb
$ echo "command script import ~/.lldb/cpython_lldb/cpython_lldb.py" >> ~/.lldbinit
$ chmod +x ~/.lldbinit
```

Usage
=====

Start a new LLDB session:

```shell
$ lldb /usr/bin/python
```

or attach to an existing CPython process:

```shell
$ lldb /usr/bin/python -p $PID
```

If you've followed the installation steps, the extension will now be automatically
loaded on start of a new LLDB session and register some Python-specific commands:

```
(lldb) help
...
Current user-defined commands:
  py-bt     -- Print a Python-level call trace of the selected thread.
  py-down   -- Select a newer Python stack frame.
  py-list   -- List the source code of the Python module that is currently being executed.
  py-locals -- Print the values of local variables in the selected Python frame.
  py-up     -- Select an older Python stack frame.
For more information on any command, type 'help <command-name>'.
```

Pretty-printing
---------------

All known `PyObject`'s (i.e. built-in types) are automatically pretty-printed
when encountered, as if you tried to get a `repr()` of something in Python REPL,
e.g.:

```
(lldb) frame variable v
(PyObject *) v = 0x0000000100793c00 42
(lldb) p v->ob_type->tp_name
(const char *) $3 = 0x000000010017d42a "int"
```

Stack traces
------------

Use `py-bt` to print a full application-level stack trace of the current thread, e.g.:

```
(lldb) py-bt
Traceback (most recent call last):
  File "test.py", line 15, in <module>
    fc()
  File "test.py", line 12, in fc
    fb()
  File "test.py", line 8, in fb
    fa()
  File "test.py", line 2, in fa
    abs(1)
```

Walking up and down the call stack
----------------------------------

Use `py-up` and `py-down` to select an older or a newer Python call stack frame, e.g.:

```
(lldb) py-up
  File "/Users/malor/src/cpython/test.py", line 6, in cb
    self.ca()
(lldb) py-up
  File "/Users/malor/src/cpython/test.py", line 20, in f_static
    c.cb()
(lldb) py-down
  File "/Users/malor/src/cpython/test.py", line 6, in cb
    self.ca()
(lldb) py-down
  File "/Users/malor/src/cpython/test.py", line 3, in ca
    abs(1)
(lldb) py-down
*** Newest frame
```

Printing of local variables
---------------------------

Use `py-locals` to print the values of local variables in the selected frame:

```
(lldb) py-locals
a = 42
args = (1, 2, 3)
b = [1, u'hello', u'\\u0442\\u0435\\u0441\\u0442']
c = ([1], 2, [[3]])
d = u'test'
e = {u'a': -1, u'b': 0, u'c': 1}
eggs = 42
kwargs = {u'foo': 'spam'}
spam = u'foobar'
```

Listing the source code
-----------------------

Use `py-list` to list the source code that is currently being executed in the selected
Python frame, e.g.:

```
(lldb) py-list
    1    SOME_CONST = 42
    2
    3
    4    def fa():
   >5        abs(1)
    6        return 1
    7
    8
    9    def fb():
   10        1 + 1
```

The command also accepts optional `start` and `end` arguments that allow to
list the source code within a specific range of lines, e.g.:

```
(lldb) py-list 4
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
```

or:

```
(lldb) py-list 4 11
    4    def fa():
   >5        abs(1)
    6        return 1
    7
    8
    9    def fb():
   10        1 + 1
   11        fa()
```

Potential issues and how to solve them
======================================

CPython 2.7.x
-------------

CPython 2.7.x is not supported. There are currently no plans to support it in the future.

Missing debugging symbols
-------------------------

CPython debugging symbols are required. You can check if they are available as follows:

```shell
$ lldb /usr/bin/python
$ (lldb) type lookup PyObject
```

If debugging symbols are not available, you'll see something like:

```shell
no type was found matching 'PyObject'
```

Some Linux distros ship debugging symbols separately. To fix the problem on Debian / Ubuntu do:

```shell
$ sudo apt-get install python-dbg
```

on CentOS / Fedora / RHEL do:

```shell
$ sudo yum install python-debuginfo
```

Other distros, like Arch Linux, do not provide debugging symbols in the package repos. In this case,
you would need to build CPython from source. Please refer to official [CPython](https://devguide.python.org/setup/#compiling)
or [distro](https://wiki.archlinux.org/index.php/Debug_-_Getting_Traces) docs for instructions.

Alternatively, you can use official CPython [Docker images](https://hub.docker.com/_/python).


Broken LLDB scripting
---------------------

Some Linux distros (most notably Debian Stretch) are shipped with a version of LLDB in which Python scripting
triggers a segmentation fault when executing any non-trivial operation:

```shell
$ lldb
(lldb) script
Python Interactive Interpreter. To exit, type 'quit()', 'exit()' or Ctrl-D.
>>> import io
>>> Segmentation fault
```

It's recommended that you use the latest LLDB release from the official [APT repo](https://apt.llvm.org/) instead
of the one shipped with your distro.

Conflicting Python versions on Mac OS
-------------------------------------

If you see an error like this:

```
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File "/usr/local/Cellar/python/2.7.13/Frameworks/Python.framework/Versions/2.7/lib/python2.7/io.py", line 51, in <module>
    import _io
ImportError: dlopen(/usr/local/Cellar/python/2.7.13/Frameworks/Python.framework/Versions/2.7/lib/python2.7/lib-dynload/_io.so, 2): Symbol not found: __PyCodecInfo_GetIncrementalDecoder
  Referenced from: /usr/local/Cellar/python/2.7.13/Frameworks/Python.framework/Versions/2.7/lib/python2.7/lib-dynload/_io.so
  Expected in: flat namespace
 in /usr/local/Cellar/python/2.7.13/Frameworks/Python.framework/Versions/2.7/lib/python2.7/lib-dynload/_io.so
```

then the version of LLDB, that is shipped with Mac OS and linked against the system CPython,
is trying to use CPython installed via Homebrew. This won't work. You need to make sure LLDB
picks up the correct CPython version on start. One way to achieve that would be modifying
`$PATH`, e.g. by creating a wrapper for `lldb`:

```
#!/bin/sh

export PATH=/usr/bin:$PATH
exec lldb "$@"
```

and putting it to `/usr/local/bin`.

See this [page](https://github.com/vadimcn/vscode-lldb/wiki/Troubleshooting) for advice on
troubleshooting of LLDB.

Development
===========

Running tests
-------------

Tests currently require `make` and `docker` to be installed.

To run the tests against the *latest* released CPython version, do:

```
$ make test
```

To run the tests against a specific CPython (or LLDB) version, do:

```
$ PY_VERSION=X.Y LLDB_VERSION=Z make test
```

Supported CPython versions are:
* `3.5`
* `3.6`
* `3.7`
* `3.8`
* `3.9`

Supported LLDB versions:
* `7`
* `8`
* `9`
* `10`
* `11`

Contributors
============

Kudos to everyone who have contributed to this project!

* Marco Neumann
