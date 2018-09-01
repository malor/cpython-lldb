import lldb


class PyObject(object):

    def __init__(self, lldb_value):
        self.lldb_value = lldb_value

    def __repr__(self):
        return repr(self.value)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        assert isinstance(other, PyObject)

        return self.value == other.value

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
            digits.GetChildAtIndex(i, 0, True).unsigned  * 2 ** (shift * i)
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
        size = value.GetValueForExpressionPath('.ob_base.ob_size').unsigned
        addr = value.GetValueForExpressionPath('.ob_sval').GetLoadAddress()

        return bytes(lldb.process.ReadMemory(addr, size, lldb.SBError())) if size else b''


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


class _PySequence(object):

    @property
    def value(self):
        value = self.lldb_value.deref.Cast(self.lldb_type)
        size = value.GetValueForExpressionPath('.ob_base.ob_size').signed
        items = value.GetChildMemberWithName('ob_item')

        return self.python_type(
            PyObject.from_value(items.GetChildAtIndex(i, 0, True))
            for i in range(size)
        )


class PyListObject(_PySequence, PyObject):

    python_type = list
    typename = 'list'

    @property
    def lldb_type(self):
        return lldb.target.FindFirstType('PyListObject')


class PyTupleObject(_PySequence, PyObject):

    python_type = tuple
    typename = 'tuple'

    @property
    def lldb_type(self):
        return lldb.target.FindFirstType('PyTupleObject')


class PySetObject(PyObject):

    typename = 'set'

    @property
    def value(self):
        set_type = lldb.target.FindFirstType('PySetObject')

        value = self.lldb_value.deref.Cast(set_type)
        size = value.GetChildMemberWithName('mask').unsigned + 1
        table = value.GetChildMemberWithName('table')
        array = table.deref.Cast(
            table.type.GetPointeeType().GetArrayType(size)
        )

        rv = set()
        for i in range(size):
            entry = array.GetChildAtIndex(i)
            key = entry.GetChildMemberWithName('key')
            hash_ = entry.GetChildMemberWithName('hash').signed

            # filter out 'dummy' and 'unused' slots
            if hash_ != -1 and (hash_ != 0 or key.unsigned != 0):
                rv.add(PyObject.from_value(key))

        return rv


class PyDictObject(PyObject):

    typename = 'dict'

    @property
    def value(self):
        dict_type = lldb.target.FindFirstType('PyDictObject')
        byte_type = lldb.target.FindFirstType('char')

        value = self.lldb_value.deref.Cast(dict_type)
        keys = value.GetChildMemberWithName('ma_keys')
        values = value.GetChildMemberWithName('ma_values')

        rv = {}

        if values.unsigned == 0:
            # table is "combined": keys and values are stored in ma_keys
            dictentry_type = lldb.target.FindFirstType('PyDictKeyEntry')
            table_size = keys.GetChildMemberWithName('dk_size').unsigned
            num_entries = keys.GetChildMemberWithName('dk_nentries').unsigned

            # hash table effectively stores indexes of entries in the key/value
            # pairs array; the size of an index varies, so that all possible
            # array positions can be addressed
            if table_size < 0xff:
                index_size = 1
            elif table_size < 0xffff:
                index_size = 2
            elif table_size < 0xfffffff:
                index_size = 4
            else:
                index_size = 8
            shift = table_size * index_size

            indices = keys.GetChildMemberWithName("dk_indices")
            if indices.IsValid():
                # CPython version >= 3.6
                # entries are stored in an array right after the indexes table
                entries = indices.Cast(byte_type.GetArrayType(shift)) \
                                 .GetChildAtIndex(shift, 0, True) \
                                 .AddressOf() \
                                 .Cast(dictentry_type.GetPointerType()) \
                                 .deref \
                                 .Cast(dictentry_type.GetArrayType(num_entries))
            else:
                # CPython version < 3.6
                num_entries = table_size
                entries = keys.GetChildMemberWithName("dk_entries") \
                              .Cast(dictentry_type.GetArrayType(num_entries))

            for i in range(num_entries):
                entry = entries.GetChildAtIndex(i)
                k = entry.GetChildMemberWithName('me_key')
                v = entry.GetChildMemberWithName('me_value')
                if k.unsigned != 0 and v.unsigned != 0:
                    rv[PyObject.from_value(k)] = PyObject.from_value(v)
        else:
            # keys and values are stored separately
            # FIXME: implement this
            pass

        return rv


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
