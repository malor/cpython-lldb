What is cpython-lldb?
=====================

`cpython_lldb` is an extension for LLDB for debugging of Python applications
running on CPython, that allows to get meaningful application-level information
(e.g. variable values or stack traces).

While CPython itself provides a similar extension for gdb [out of the box](
https://github.com/python/cpython/blob/master/Tools/gdb/libpython.py),
one might still prefer to use LLDB as a debugger, e.g. on Mac OS.


Features
========

`cpython_lldb` currently targets (== is tested on) CPython 3.5+ and supports
 the following features:

* pretty-priting of built-in types (int, bool, float, bytes, str, none, tuple, list, set, dict)

TODO:

* stack traces
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

All known `PyObject`'s (i.e. built-in types) are automatically pretty-printed
when encountered, as if you tried to get `repr()` of something in Python REPL,
e.g.:

```
(lldb) frame variable v
(PyObject *) v = 0x0000000100793c00 42
(lldb) p v->ob_type->tp_name
(const char *) $3 = 0x000000010017d42a "int"
```
