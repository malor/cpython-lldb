What is cpython-lldb?
=====================

[![Build Status](https://travis-ci.org/malor/cpython-lldb.svg?branch=master)](https://travis-ci.org/malor/cpython-lldb)

`cpython_lldb` is an extension for LLDB for debugging of Python applications
running on CPython, that allows to get meaningful application-level information
(e.g. variable values or stack traces).

While CPython itself provides a similar extension for gdb [out of the box](
https://github.com/python/cpython/blob/master/Tools/gdb/libpython.py),
one might still prefer to use LLDB as a debugger, e.g. on Mac OS.

**NOTE**: The project is still in early development stage; its functionality is very limited at this point.


Features
========

`cpython_lldb` currently targets (== is tested on) CPython 3.4+ and supports
 the following features:

* pretty-priting of built-in types (int, bool, float, bytes, str, none, tuple, list, set, dict)
* printing of Python-level stack traces

TODO:

* stack traces w/ mixed stacks (e.g. involving calls to clibs)
* local variables
* code listing


Installation
============

```shell
mkdir -p ~/.lldb
cd ~/.lldb && git clone https://github.com/malor/cpython-lldb
echo "command script import ~/.lldb/cpython-lldb/cpython_lldb.py" >> ~/.lldbinit
chmod +x ~/.lldbinit
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

Pretty-printing
---------------

All known `PyObject`'s (i.e. built-in types) are automatically pretty-printed
when encountered, as if you tried to get `repr()` of something in Python REPL,
e.g.:

```
(lldb) frame variable v
(PyObject *) v = 0x0000000100793c00 42
(lldb) p v->ob_type->tp_name
(const char *) $3 = 0x000000010017d42a "int"
```

Stack traces
------------

Use `py-bt` to print a Python-level stack trace of the current thread, e.g.:

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

Potential issues and how to solve them
======================================

CPython 2.7.x
-------------

CPython 2.7.x is not supported yet, but may be in the future.

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

Other distros like Arch Linux do not provide debugging symbols in the package repos. In this case
you would need to build CPython from source. Please refer to official [CPython](https://devguide.python.org/setup/#compiling)
or [distro](https://wiki.archlinux.org/index.php/Debug_-_Getting_Traces) docs for instructions.

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

To run the tests against the *latest* released CPython version do:

```
$ make test
```

To run the tests against a specific CPython version do:

```
$ make test-py34
```

Supported versions are:
* `py34`
* `py35`
* `py36`
* `py37`


Contributors
============

Kudos to everyone who have contributed to this project!

* Marco Neumann
