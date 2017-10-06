import os, hashlib, time
from omg.util import *

Header = make_struct(
  "Header",
  """Class for WAD file headers""",
  [["type",    '4s', "PWAD"],
   ["dir_len", 'i',  0     ],
   ["dir_ptr", 'i',  12    ]]
)

Entry = make_struct(
  "Entry",
  """Class for WAD entries""",
  [["ptr",       'i',  0 ],
   ["size",      'i',  0 ],
   ["name",      '8s', ""],
   ["been_read", 'x',  False]]   # Used by WAD loader
)


# WadIO.open() behaves just like open(). Sometimes it is
# useful to specifically either open an existing file
# or create a new one.

def open_wad():
    """Open an existing WAD, raise IOError if not found"""
    if not os.path.exists(location):
        raise IOError
    return WadIO(location)

def create_wad(location):
    """Create a new WAD, raise IOError if exists"""
    if os.path.exists(location):
        raise IOError
    return WadIO(location)


class WadIO:
    """A WadIO object is used to open a WAD file for direct
    reading and writing.

    IMPORTANT: In case the contents of the file have been modified,
    .save() must be called before exiting, or data will be lost/the
    universe explodes. You can check whether the file is in need of
    saving by reading the value of the boolean attribute .issafe

    WadIO objects work on the WAD directory level. There is
    very little magic available- you can't do things like automatic
    merging or managing sections, and Omgifol is never aware of
    what types lumps are. In other words, you're doing things more
    or less manually, with the hard binary content of lumps and
    the linear order they're stored in.

    Use this for very large WADs and when only performing small/few
    operations. For example, when you need to read a lump or two
    from an IWAD for copying into another WAD. Also use it when
    it is important that the saved file is identical to the opened
    file; that is not guaranteed to work with the higher-level WAD
    class since it sometimes modifies order.

    The benefit of using this class is that you don't have to read
    and write the whole file when opening or closing. The downside
    is that changes can't be undone (so back up first!) and that
    file content will get fragmented when you edit lumps (unused
    space will appear). To get rid of the wasted space, use the
    rewrite() method (which rewrites the entire file)."""

    def __init__(self, openfrom=None):
        self.basefile = None
        self.issafe = True
        self.header = Header()
        self.entries = []
        if openfrom is not None:
            self.open(openfrom)

    def __del__(self):
        if self.basefile:
            self.basefile.close()

    def open(self, filename):
        """Open a WAD file, create a new file if none exists at the path."""
        assert not self.entries
        if self.basefile:
            raise IOError("The handle is already open")
        # Open an existing WAD
        if os.path.exists(filename):
            try:
                self.basefile = open(filename, 'r+b')
            except IOError:
                # assume file is read-only
                self.basefile = open(filename, 'rb')
            
            filesize = os.stat(self.basefile.name)[6]
            self.header = h = Header(bytes=self.basefile.read(Header._fmtsize))
            if (not h.type in ("PWAD", "IWAD")) or filesize < 12:
                raise IOError("The file is not a valid WAD file.")
            if filesize < h.dir_ptr + h.dir_len*Entry._fmtsize:
                raise IOError("Invalid directory information in header.")
            self.basefile.seek(h.dir_ptr)
            self.entries = [Entry(bytes=self.basefile.read(Entry._fmtsize)) \
                for i in range(h.dir_len)]
        # Create new
        else:
            self.basefile = open(filename, 'w+b')
            self.basefile.write(Header().pack())
            self.basefile.flush()

    def close(self):
        """Close the base file"""
        assert self.basefile
        # Unfortunately, a save can't be forced here.
        if not self.issafe:
            raise IOError(\
                "closing a modified file may corrupt it. use save() first")
        self.basefile.close()
        self.basefile = None

    def select(self, id):
        """Return a valid index from a proposed index or entry name, or
        raise LookupError in case of failure."""
        assert self.basefile
        if isinstance(id, int):
            if id < len(self.entries):
                return id
            raise LookupError
        elif isinstance(id, str):
            for i in range(len(self.entries)):
                if wccmp(self.entries[i].name, id):
                    return i
            raise LookupError
        raise TypeError

    def get(self, id):
        return self.entries[self.select(id)]

    def find(self, id):
        """Search for an entry and return the index of the first match
        or None if no matches were found. Wildcards are supported."""
        assert self.basefile
        try:
            return self.select(id)
        except LookupError:
            return None

    def multifind(self, id, start=None, end=None):
        """Search for entries and return a list of matches. Wildcards
        are supported."""
        assert self.basefile
        if start is None: start = 0
        if end   is None: end   = len(self.entries)
        return [i for i in range(start, end) if \
                wccmp(self.entries[i].name, id)]

    def read(self, id):
        """Read an entry and return the data as a binary string."""
        assert self.basefile
        id = self.select(id)
        self.basefile.seek(self.entries[id].ptr)
        return self.basefile.read(self.entries[id].size)

    def remove(self, id):
        """Remove an entry."""
        assert self.basefile
        del (self.entries[self.select(id)])

    def rename(self, id, new):
        """Rename an entry."""
        assert self.basefile
        self.entries[self.select(id)].name = new[0:8].upper()
        self.issafe = False

    def write_at(self, pos, data):
        """Write data at the given position."""
        self.basefile.seek(pos)
        self.basefile.write(data)

    def write_append(self, data):
        """Write data at the end of the file"""
        self.basefile.seek(0, 2)
        self.basefile.write(data)

    def insert(self, name, data, index=None):
        """Insert a new entry at the optional index (defaults to
        appending)."""
        assert self.basefile
        try:
            index = self.select(index)
        except:
            index = None
        self.issafe = False
        self.basefile.seek(0, 2)
        pos = self.basefile.tell()
        self.basefile.write(data)
        if index is None:
            self.entries.append(Entry(pos, len(data), name))
        else:
            self.entries.insert(index, Entry(pos, len(data), name))
        self.basefile.flush()

    def update(self, id, data):
        """Write new data for an existing lump. If the new data is
        bigger than what's present, a new position in the file will be
        allocated for the lump."""
        assert self.basefile
        id = self.select(id)
        if len(data) != self.entries[id].size:
            self.issafe = False
        if len(data) <= self.entries[id].size:
            self.write_at(self.entries[id].ptr, data)
        else:
            # Currently, the lump simply gets placed at the end of the file.
            # Instead, calc_waste() could be used to find empty space
            self.basefile.seek(0, 2)
            self.entries[id].ptr = self.basefile.tell()
            self.basefile.write(data)
        self.entries[id].size = len(data)
        self.basefile.flush()

    def save(self):
        """Save directory and header changes to the WAD file."""
        assert self.basefile
        if self.issafe: return
        self.basefile.seek(0, 2)
        endpos = self.basefile.tell()
        for entry in self.entries:
            self.basefile.write(entry.pack())
        self.header.dir_len = len(self.entries)
        self.header.dir_ptr = endpos
        self.write_at(0, self.header.pack())
        self.basefile.flush()
        self.issafe = True

    def rewrite(self):
        """Rewrite the entire WAD file. This removes all garbage
        (wasted space) from the file."""
        assert self.basefile
        fpath = self.basefile.name
        # Write to a temporary file and rename it when done
        # os.tmpnam works too, but gives a security warning
        tmppath = hashlib.md5(str(time.time())).hexdigest()[:8] + ".tmp"
        tmppath = os.path.join(os.path.dirname(fpath), tmppath)
        outwad = create_wad(tmppath)
        for i in range(len(self.entries)):
            outwad.insert(self.entries[i].name, self.read(i))
        outwad.save()
        outwad.close()
        self.close()
        os.remove(fpath)
        os.rename(tmppath, fpath)
        self.entries = []
        self.open(fpath)
        self.issafe = True

    def calc_waste(self):
        """Returns an (int, list) tuple containing the total amount of
        wasted space in the WAD and a list of (start, end) tuples for
        the spots where the wasted chunks are located."""
        assert self.basefile
        filesize = os.stat(self.basefile.name)[6]
        # Create a list of (start, end) tuples to represent used space
        chunks = []
        # Treat the header and the end of the file as chunks of used space
        chunks.append((0, 12))
        chunks.append((filesize, filesize + 1))
        # Add to the list the chunks that are occupied by lump data
        chunks.append((self.header.dir_ptr, self.header.dir_ptr + \
            len(self.entries)*Entry._fmtsize))
        for entry in self.entries:
            chunks.append((entry.ptr, entry.ptr + entry.size))
        # Sort it so we can go through it linearly and check for gaps
        chunks.sort()
        positions = []
        space = 0
        for i in range(0, len(chunks)-1):
            # Check whether the end of the chunk touches the beginning of the
            # next one. If not, there's wasted space between them.
            if chunks[i][1] < chunks[i+1][0]:
                positions.append((chunks[i][1], chunks[i+1][0]))
                space += positions[-1][1] - positions[-1][0]
        return space, positions

    def info_text(self):
        """Return printable fancy-formatted info about the WAD file."""
        assert self.basefile
        assert self.issafe
        filesize = os.stat(self.basefile.name)[6]
        s = []
        # Main information
        s.append("Info for %s\n\n" % self.basefile.name)
        s.append("Type: %s\n" % self.header.type)
        s.append("Size: %d bytes\n" % filesize)
        s.append("Directory start: 0x%x" % self.header.dir_ptr)
        # List all the lumps and some relevant information
        s.append("\n\nEntries:\n\n     #  Name       Size       Position\n\n")
        for i, entry in enumerate(self.entries):
            s.append("%6i  %s %s 0x%x\n" %
                (i, entry.name.ljust(10), str(entry.size).ljust(10), entry.ptr))
        # Add info about wasted space in the WAD, to find out how much of an
        # improvement a rewrite() would make
        total, wasted = self.calc_waste()
        s.append("\n\nWasted space:\n\n")
        s.append("    %s bytes total\n" % str(total))
        for w in wasted:
            s.append("    %i bytes starting at 0x%x\n" % (w[1]-w[0], w[0]))
        return join(s)
