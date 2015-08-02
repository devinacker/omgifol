"""
    Utilities -- common functions and classes, used variously
    by other Omgifol modules.
"""

from fnmatch import fnmatchcase as wccmp
from struct  import pack, unpack, calcsize
from copy    import copy, deepcopy

_pack = pack
_unpack = unpack

class OrderedDict:
    """A dict-like container that remembers in which order items
    were added."""

    def __init__(self, source=None):
        """Create new, optionally from contents of given source."""
        self._items = {}
        self._n = 0
        if source:
            self.update(source)

    def __setitem__(self, key, value):
        """Set an item."""
        self._items[key] = self._n, value
        self._n += 1

    def __getitem__(self, key):
        """Retrieven an item."""
        return self._items[key][1]

    def __delitem__(self, key):
        """Delete an item."""
        del self._items[key]

    def __contains__(self, key):
        """Find if the dict holds the given key."""
        return key in self._items

    def __iter__(self):
        """Iterate over keys"""
        return iter(self.keys())

    def __add__(self, other):
        """Adds two dicts, copying items shallowly"""
        c = self.__class__()
        c.update(self)
        c.update(other)
        return c

    def __len__(self):
        """len(self)"""
        return len(self._items)

    def update(self, other):
        """Adds all content from another dictionary."""
        for k in other:
            self[k] = other[k]

    def items(self):
        """Returns a list of (key, value) tuples for all items."""
        data = [(v[0], k, v[1]) for (k, v) in self._items.items()]
        data.sort()
        return [(d[1], d[2]) for d in data]

    def keys(self):
        """Returns a list of all keys."""
        data = [(v[0], k, v[1]) for (k, v) in self._items.items()]
        data.sort()
        return [d[1] for d in data]

    def values(self):
        """Returns a list of all values."""
        data = [(v[0], k, v[1]) for (k, v) in self._items.items()]
        data.sort()
        return [d[2] for d in data]

    def clear(self):
        """Delete all items."""
        self._items.clear()

    def find(self, pattern):
        """Find all items that match the given pattern (supporting
        wildcards). Returns a list of keys."""
        return [k for k in self.keys() if wccmp(k, pattern)]

    def rename(self, old, new):
        """Rename an entry"""
        print old, new
        print old in self
        print "K", self.keys()
        self[new] = self[old]
        print self[new]
        del self[old]

    def __copy__(self):
        """Creates a deep copy."""
        a = self.__class__()
        for k in self:
            a[k] = copy(self[k])
        return a


#----------------------------------------------------------------------
#
# Miscellaneous convenient function
#

def join(seq):
    """Create a joined string out of a list of substrings."""
    return "".join(seq)

def readfile(source):
    """Read data from a file, return data as a string. Target may
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
    return pack('8s', chars)

def zstrip(chars):
    """Strip all data following the first zero in the string"""
    if '\0' in chars:
        return chars[:chars.index("\0")]
    return chars

def safe_name(chars):
    return chars[:8].translate(_trans_table)

def fixname(chars):
    if '\0' in chars:
        chars = chars[:chars.index("\0")]
    chars = chars.translate(_trans_table)
    return chars

def fixpadname(chars):
    """Same as fixname, but returns a string of exactly 8 bytes length,
    using zero (0x00) bytes for padding."""
    print "DEPRECATED!"
    return zpad(fixname(chars))

def fix_saving_name(name):
    """Neutralizes backslashes in Arch-Vile frame names"""
    return name.rstrip('\0').replace('\\', '`')

def fix_loading_name(name):
    """Restores backslash to Arch-Vile frame names"""
    return fixname(name).replace('`', '\\')

def unpack16(s):
    """Convert a packed signed short (2 bytes) to a Python int"""
    return unpack('h', s)[0]

def pack16(n):
    """Convert a Python int to a packed signed short (2 bytes)"""
    return pack('h', n)

def unpack32(s):
    """Convert a packed signed long (4 bytes) to a Python int"""
    return unpack('i', s)[0]

def pack32(n):
    """Convert a Python int to a packed signed long (4 bytes)"""
    return pack('i', n)


#----------------------------------------------------------------------
#
# A tool that can generate "Struct" classes for packing, unpacking, and
# representing the unpacked form of binary data.
#
# If this code looks ugly, be happy you didn't see the
# original version...
#

# Template for struct class generation
_struct_template = '''
class Struct(object):
    """%(doc)s"""

    _fmtsize = %(fmtsize)i
    _fmt  = %(fmt)r

    def __init__(self, %(initargs)s, bytes=None):
        if bytes:
            %(unpackexpr)s
        else:
            %(initbody)s
        %(init_exec)s

    def __getattribute__(self, name):
        return object.__getattribute__(self, name)

    def pack(self):
        return %(packexpr)s

%(flagdefs)s

Struct.__name__ = %(name)r
'''

# Template for struct flag property
_flagproperty = '''
    def get_%s(self):
        return %s((self.%s >> %i) & %i)
    def set_%s(self, value):
        self.%s &= %i
        if value is not None and (isinstance(value, bool) or 0 <= value <= %i):
            self.%s |= (int(value) << %i)
        elif value:
            raise ValueError("%s must be between 0 and %i")
    
    %s = property(get_%s, set_%s)'''

def make_property(name, bit, size=1, type=bool, var="flags"):
    """Helper function for make_struct which defines properties based on
    bit fields. This is called automatically for "flags" when passing a 
    list of flags to make_struct, but can also be added to init_exec to
    handle flags in other variables if needed."""
    
    getmask = (1 << size) - 1
    setmask = 0xFFFF ^ (getmask << bit)
    
    return _flagproperty % (name, type.__name__, var, bit, getmask,
                            name, var, setmask, getmask, var, bit, name, getmask,
                            name, name, name)

def _structdef(name, doc, fields, flags=None, init_exec=""):
    """Helper function for make_struct. Needed because Python doesn't
    like compile() and exec in the place when there are unknown
    variables floating around... (?)"""

    extra  = [f for f in fields if f[1] == 'x']
    fields = [f for f in fields if f[1] != 'x']

    fmt = "".join(f[1] for f in fields)
    fmtsize = calcsize(fmt)

    # properties for easy access to the 'flags' bit field
    flagdefs = ""
    if flags:
        i = 0
        for f in flags:
            if f is None:
                i += 1
                pass
            elif isinstance(f, str):
                flagdefs += make_property(f, i)
                i += 1
            elif isinstance(f, tuple) and len(f) == 2:
                name, size = f
                flagdefs += make_property(name, i, size, int if size > 1 else bool)
                i += size
            else:
                raise TypeError("flag must be a string (name), tuple (name, size), or None")
    
    if init_exec: init_exec += ";"
    init_exec += '; '.join("self.%s=%s" % (f[0], f[0]) for f in extra)

    # example:  x=0, y=0, foo="BAR"
    initargs = ', '.join(f[0] + "=" + repr(f[2]) for f in fields+extra)

    # example:  self.x, self.y, self.foo = unpack('hh8s', bytes);
    #           self.foo = zstrip(safe_name(self.foo))
    unpackexpr =  ', '.join('self.'+f[0] for f in fields)
    unpackexpr += (" = unpack(%r, bytes); " % fmt)
    unpackexpr += "; ".join("self.%s=zstrip(safe_name(self.%s))" % \
        (f[0], f[0]) for f in fields if 's' in f[1])

    # example:  self.x=x; self.y=y; self.foo=foo
    initbody = "; ".join("self.%s=%s" % (f[0], f[0]) for f in fields)

    # example:  pack()
    packs = []
    for f in fields:
        if 's' in f[1]:
            packs.append("zpad(safe_name(self.%s))" % f[0])
        else:
            packs.append("self.%s" % f[0])
    packexpr = ("pack(%r, " % fmt) + ', '.join(packs) + ")"

    s = _struct_template % locals()

    # print s.replace("Struct", name)
    return compile(s, "<struct>", "exec")

def make_struct(*args, **kwargs):
    """Create a Struct class according to the given format"""
    exec _structdef(*args, **kwargs)
    return Struct
