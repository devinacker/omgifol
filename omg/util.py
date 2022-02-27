"""
    Utilities -- common functions and classes, used variously
    by other Omgifol modules.
"""

from __future__  import print_function
from fnmatch     import fnmatchcase as wccmp, filter as wcinlist
from struct      import pack, unpack
from copy        import copy, deepcopy
from collections import OrderedDict as od
import ctypes

class OrderedDict(od):
    """
    Like collections.OrderedDict but with a few helpful extras:

    - dicts can be added together
    - find and rename methods
    - items(), keys(), and values() return normal lists
    """

    def __init__(self, source=None):
        od.__init__(self)
        if source:
            self.update(source)

    def __add__(self, other):
        c = self.__class__(self)
        c.update(other)
        return c

    def __iadd__(self, other):
        self.update(other)
        return self

    def items(self):
        # return list instead of odict_items
        return [i for i in od.items(self)]

    def keys(self):
        # return list instead of odict_keys
        return [i for i in od.keys(self)]

    def values(self):
        # return list instead of odict_values
        return [i for i in od.values(self)]

    def find(self, pattern):
        """Find all items that match the given pattern (supporting
        wildcards). Returns a list of keys."""
        return [k for k in od.keys(self) if wccmp(k, pattern)]

    def rename(self, old, new):
        """Rename an entry"""
        self[new] = self[old]
        del self[old]


#----------------------------------------------------------------------
#
# Miscellaneous convenient function
#

def join(seq):
    """Create a joined string out of a list of substrings."""
    return bytes().join(seq)

def readfile(source):
    """Read data from a file, return data as bytes. Target may
    be a path name string or a file-like object (with a `read` method)."""
    if isinstance(source, str):
        return open(source, 'rb').read()
    else:
        return source.read()

def writefile(target, data):
    """Write data to a file. Target may be a path name string
    or a file-like object (with a `write` method)."""
    if isinstance(target, str):
        open(target,'wb').write(data)
    else:
        target.write(data)

def any(set):
    for e in set:
        if e:
            return True
    return False

def all(set):
    for e in set:
        if not e:
            return False
    return True

def inwclist(elem, seq):
    return any(wccmp(elem, x) for x in seq)

#----------------------------------------------------------------------
#
# Functions for processing lump names and other strings
#

# Table for translating characters to those safe for use
_trans_table = ["_"] * 256
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789[]\\_-":
    _trans_table[ord(c.lower())] = c
    _trans_table[ord(c)] = c
_trans_table[0] = "\0"
_trans_table = "".join(_trans_table)

def zpad(chars):
    """Pad a string with zero bytes, up until a length of 8.
    The string is truncated if longer than 8 bytes."""
    return pack('8s', chars.encode('ascii'))

def zstrip(chars):
    """Return a string representing chars with all trailing null bytes removed.
    chars can be a string or byte string."""
    if isinstance(chars, bytes):
        chars = str(chars.decode('ascii', 'ignore'))

    if '\0' in chars:
        return chars[:chars.index("\0")]
    return chars

def safe_name(chars):
    return str(chars)[:8].translate(_trans_table)

def fixname(chars):
    return zstrip(chars).translate(_trans_table)

def fix_saving_name(name):
    """Neutralizes backslashes in Arch-Vile frame names."""
    return name.rstrip('\0').replace('\\', '`')

def fix_loading_name(name):
    """Restores backslash to Arch-Vile frame names."""
    return fixname(name).replace('`', '\\')

def unpack16(s):
    """Convert a packed signed short (2 bytes) to a Python int."""
    return unpack('<h', s)[0]

def pack16(n):
    """Convert a Python int to a packed signed short (2 bytes)."""
    return pack('<h', n)

def unpack32(s):
    """Convert a packed signed long (4 bytes) to a Python int."""
    return unpack('<i', s)[0]

def pack32(n):
    """Convert a Python int to a packed signed long (4 bytes)."""
    return pack('<i', n)


#----------------------------------------------------------------------
#
# Struct generation stuff (TODO)

def WADFlags(flags):
    """
    This is a helper function to generate flags which can be accessed either
    individually or as an entire 16-bit field.

    The flags argument is a list of (name, size) tuples, where size is in bits.
    See omg.mapedit for usage examples.
    """
    class FlagsUnion(ctypes.Union):
        class Flags(ctypes.LittleEndianStructure):
            _fields_ = [(name, ctypes.c_uint16, size) for (name, size) in flags]

        _fields_ = [("flags", ctypes.c_uint16), ("_flags", Flags)]
        _anonymous_ = ("_flags",)

    return FlagsUnion

class WADStruct(ctypes.LittleEndianStructure):
    """
    Class for creating WAD-related data structures.

    This is a subclass of ctypes.LittleEndianStructure with some additional features:
        - easy initialization from byte strings
        - automatic conversion to/from "Doom-safe" ASCII strings
    """
    _pack_ = 1

    def __init__(self, *args, **kwargs):
        """This works the same as initializing a regular ctypes structure.
        Additionally, if an argument named 'bytes' is provided, the struct instance
        will be initialized from the provided byte string instead."""
        if "bytes" in kwargs:
            buf = ctypes.create_string_buffer(kwargs["bytes"], ctypes.sizeof(self))
            ctypes.memmove(ctypes.byref(self), ctypes.byref(buf), len(buf))
        else:
            super().__init__(*args, **kwargs)

    def pack(self):
        """Helper to maintain API backward compatibility. Returns bytes(self)."""
        return bytes(self)

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if type(value) == bytes:
            return safe_name(zstrip(value))
        return value

    def __setattr__(self, name, value):
        if type(value) == str:
            value = safe_name(value).encode('ascii')
        super().__setattr__(name, value)

    def __hash__(self):
        # needed because this is by default unhashable otherwise
        return hash(bytes(self))
