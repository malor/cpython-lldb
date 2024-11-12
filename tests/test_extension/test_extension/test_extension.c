#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject* spam(PyObject* self, PyObject* args) {
    PyLongObject* local_long = (PyLongObject*) Py_BuildValue("l", 17);
    PyFloatObject* local_float = (PyFloatObject*) Py_BuildValue("f", 0.0);
    PyBytesObject* local_bytes = (PyBytesObject*) Py_BuildValue("y", "eggs");
    PyUnicodeObject* local_unicode = (PyUnicodeObject*) Py_BuildValue("s", "hello");
    PyListObject* local_list = (PyListObject*) Py_BuildValue("[lll]", 17, 18, 19);
    PyTupleObject* local_tuple = (PyTupleObject*) Py_BuildValue("(lll)", 24, 23, 22);
    PyDictObject* local_dict = (PyDictObject*) Py_BuildValue("{s:l}", "foo", 42);

    PyObject* builtins = PyEval_GetBuiltins();
    PyObject* abs = PyDict_GetItemString(builtins, "abs");
    PyObject* argslist = Py_BuildValue("(l)", 42);
    if (argslist == NULL)
        return NULL;
    PyObject* result = PyObject_CallObject(abs, argslist);
    if (result == NULL)
        return NULL;

    Py_DECREF(result);
    Py_DECREF(argslist);
    Py_DECREF(local_long);
    Py_DECREF(local_float);
    Py_DECREF(local_bytes);
    Py_DECREF(local_unicode);
    Py_DECREF(local_list);
    Py_DECREF(local_tuple);
    Py_DECREF(local_dict);

    return Py_None;
}

static PyObject* eggs(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* f = NULL;
    if (!PyArg_ParseTuple(args, "O", &f) || f == NULL) {
        return NULL;
    }

    PyObject* v = PyDict_GetItemString(kwargs, "v");
    if (v == NULL) {
        return NULL;
    }

    PyObject* argslist = Py_BuildValue("(O)", v);
    if (argslist == NULL) {
        return NULL;
    }

    return PyObject_CallObject(f, argslist);
}

// Helper functions for testing pretty-printing of Python objects. The problem
// with using functions built into CPython (e.g. id()) is that breakpoints may
// not trigger if such function is inlined. And with this C-extension we have
// full control of the compiler options and can disable optimizations.
static PyObject* _identity(PyObject* v) {
    return v;
}
static PyObject* identity(PyObject* self, PyObject* args) {
    PyObject* v = NULL;
    if (!PyArg_ParseTuple(args, "O", &v) || v == NULL) {
        return NULL;
    }

    return _identity(v);
}

static PyMethodDef methods[] = {
    { "spam", spam, METH_NOARGS, "Test Extension Function" },
    { "eggs", eggs, METH_VARARGS | METH_KEYWORDS, "Test Extension Function" },
    { "identity", identity, METH_VARARGS, "Returns the passed value. Used in testing." },
    { NULL, NULL, 0, NULL }
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "test_extension",
    "Test CPython Extension Module",
    -1,
    methods
};

PyMODINIT_FUNC PyInit__test_extension(void) {
    return PyModule_Create(&module);
}
