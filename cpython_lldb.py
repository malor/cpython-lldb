import lldb


class PyObject(object):

    def __init__(self, lldb_value):
        self.lldb_value = lldb_value

    def __repr__(self):
        return repr(self.value)

    @classmethod
    def from_value(cls, v):
        subclasses = {c.typename: c for c in cls.__subclasses__()}
        typename = cls.typename_of(v)
        return subclasses.get(typename, cls)(v)

    @staticmethod
    def typename_of(v):
        addr = v.GetValueForExpressionPath('->ob_type->tp_name').unsigned
        tp_name = lldb.process.ReadCStringFromMemory(addr, 256, lldb.SBError())

        return tp_name

    @property
    def typename(self):
        return self.typename_of(self.lldb_value)

    @property
    def value(self):
        return str(self.lldb_value.addr)


class PyLongObject(PyObject):

    typename = 'int'

    @property
    def value(self):
        '''

        The absolute value of a number is equal to:

            SUM(for i=0 through abs(ob_size)-1) ob_digit[i] * 2**(SHIFT*i)

        Negative numbers are represented with ob_size < 0;
        zero is represented by ob_size == 0.

        where SHIFT can be either:
            #define PyLong_SHIFT        30
        or:
            #define PyLong_SHIFT        15

        '''

        long_type = lldb.target.FindFirstType('PyLongObject')
        digit_type = lldb.target.FindFirstType('digit')

        shift = 15 if digit_type.size == 2 else 30
        value = self.lldb_value.deref.Cast(long_type)
        size = value.GetValueForExpressionPath('.ob_base.ob_size').signed
        if not size:
            return 0

        digits = value.GetChildMemberWithName('ob_digit')
        abs_value = sum(
            digits.GetChildAtIndex(i, 0, 1).unsigned  * 2 ** (shift * i)
            for i in range(0, abs(size))
        )
        return abs_value if size > 0 else -abs_value


class PyBoolObject(PyObject):

    typename = 'bool'

    @property
    def value(self):
        long_type = lldb.target.FindFirstType('PyLongObject')

        value = self.lldb_value.deref.Cast(long_type)
        digits = value.GetChildMemberWithName('ob_digit')
        return bool(digits.GetChildAtIndex(0).unsigned)


class PyFloatObject(PyObject):

    typename = 'float'

    @property
    def value(self):
        float_type = lldb.target.FindFirstType('PyFloatObject')

        value = self.lldb_value.deref.Cast(float_type)
        fval = value.GetChildMemberWithName('ob_fval')
        return float(fval.GetValue())


class PyBytesObject(PyObject):

    typename = 'bytes'

    @property
    def value(self):
        bytes_type = lldb.target.FindFirstType('PyBytesObject')

        value = self.lldb_value.deref.Cast(bytes_type)
        size = value.GetValueForExpressionPath('.ob_base.ob_size').signed
        addr = value.GetChildMemberWithName('ob_sval') \
                    .GetLoadAddress()

        bytes_value = lldb.process.ReadCStringFromMemory(addr, size + 1,
                                                         lldb.SBError())
        return bytes(bytes_value) if bytes_value else b''


class PyUnicodeObject(PyObject):

    typename = 'str'

    U_WCHAR_KIND = 0
    U_1BYTE_KIND = 1
    U_2BYTE_KIND = 2
    U_4BYTE_KIND = 4

    @property
    def value(self):
        str_type = lldb.target.FindFirstType('PyUnicodeObject')

        value = self.lldb_value.deref.Cast(str_type)
        state = value.GetValueForExpressionPath('._base._base.state')
        length = value.GetValueForExpressionPath('._base._base.length').unsigned
        if not length:
            return u''

        compact = bool(state.GetChildMemberWithName('compact').unsigned)
        is_ascii = bool(state.GetChildMemberWithName('ascii').unsigned)
        kind = state.GetChildMemberWithName('kind').unsigned
        ready = bool(state.GetChildMemberWithName('ready').unsigned)

        if is_ascii and compact and ready:
            # content is stored right after the data structure in memory
            ascii_type = lldb.target.FindFirstType('PyASCIIObject')
            value = value.Cast(ascii_type)
            addr = int(value.location, 16) + value.size

            rv = lldb.process.ReadMemory(addr, length, lldb.SBError())
            return rv.decode('ascii')
        elif compact and ready:
            # content is stored right after the data structure in memory
            compact_type = lldb.target.FindFirstType('PyCompactUnicodeObject')
            value = value.Cast(compact_type)
            addr = int(value.location, 16) + value.size

            rv = lldb.process.ReadMemory(addr, length * kind, lldb.SBError())
            if kind == self.U_2BYTE_KIND:
                return rv.decode('utf-16')
            elif kind == self.U_4BYTE_KIND:
                return rv.decode('utf-32')
            else:
                return u''  # FIXME
        else:
            return u''


class PyNoneObject(PyObject):

    typename = 'NoneType'
    value = None


def pretty_printer(value, internal_dict):
    """Provide a type summary for a PyObject instance.

    Try to identify an actual object type and provide a representation for its
    value (similar to repr(something) in Python code).

    """

    return repr(PyObject.from_value(value))


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
        'type summary add -F cpython_lldb.pretty_printer PyObject'
    )
