import os, glob
import omg.palette
from omg.lump  import *
from omg.util import *
from omg.wadio import WadIO

class LumpGroup(OrderedDict):
    """A dict-like object for holding a group of lumps."""

    def __init__(self, name='data', lumptype=Lump, config=()):
        OrderedDict.__init__(self)
        self._name   = name
        self.lumptype = lumptype
        self.config = config
        self.__init2__()

    def __init2__(self):
        pass

    def load(self, filename):
        """Load entries from a WAD file. All lumps from the same
        section in that WAD is loaded (e.g. if this is a patch
        section, all patches in the WAD will be loaded."""
        w = WAD(filename)
        self += w.__dict__[self._name].copy()

    def to_file(self, filename, use_free=True):
        """Save group as a separate WAD file.

        If use_free is true, existing free space in the WAD will
        be used, if possible."""
        w = WadIO(filename)
        self.save_wadio(w, use_free=use_free)

    def from_glob(self, globpattern):
        """Create lumps from files matching the glob pattern."""
        for p in glob.glob(globpattern):
            name = fixname(os.path.basename(p[:p.rfind('.')]))
            self[name] = self.lumptype(from_file=p)

    def save_wadio(self, wadio, use_free=True):
        """Save to a WadIO object.

        If use_free is true, existing free space in the WAD will
        be used, if possible."""
        for m in self:
            wadio.insert(m, self[m].data, use_free=use_free)

    def copy(self):
        """Creates a deep copy."""
        a = self.__class__(self._name, self.lumptype, self.config)
        for k in self:
            a[k] = self[k].copy()
        return a

    def __add__(self, other):
        """Adds two dicts, copying items shallowly."""
        c = self.__class__(self._name, self.lumptype, self.config)
        c.update(self)
        c.update(other)
        return c

class MarkerGroup(LumpGroup):
    """Group for lumps found between markers, e.g. sprites."""

    def __init2__(self):
        self.prefix = self.config + "*_START"
        self.suffix = self.config + "*_END"
        # In case group opens with XX_ and ends with X_
        self.abssuffix = self.config + "_END"

    def load_wadio(self, wadio):
        """Load all matching lumps that have not already
        been flagged as read from the given WadIO object."""
        inside = False
        startedwith, endswith = "", ""
        for i in range(len(wadio.entries)):
            if wadio.entries[i].been_read:
                inside = False
                continue
            name = wadio.entries[i].name
            if inside:
                if wccmp(name, endswith) or wccmp(name, self.abssuffix):
                    inside = False
                else:
                    if wadio.entries[i].size != 0:
                        self[name] = self.lumptype(wadio.read(i))
                wadio.entries[i].been_read = True
            else:
                # print name, self.prefix, wccmp(name, self.prefix)
                if wccmp(name, self.prefix):
                    startedwith = name
                    endswith = name.replace("START", "END")
                    inside = True
                    wadio.entries[i].been_read = True

    def save_wadio(self, wadio, use_free=True):
        """Save to a WadIO object.

        If use_free is true, existing free space in the WAD will
        be used, if possible."""
        if len(self) == 0:
            return
        wadio.insert(self.prefix.replace('*', ''), bytes())
        LumpGroup.save_wadio(self, wadio, use_free=use_free)
        wadio.insert(self.suffix.replace('*', ''), bytes())


class HeaderGroup(LumpGroup):
    """Group for lumps arranged header-tail (e.g. maps)."""

    def __init2__(self):
        self.tail = self.config

    def load_wadio(self, wadio):
        """Load all matching lumps that have not already
        been flagged as read from the given WadIO object."""
        numlumps = len(wadio.entries)
        i = 0
        while i < numlumps:
            if wadio.entries[i].been_read:
                i += 1
                continue
            name = wadio.entries[i].name
            added = False
            # now search only using tail lumps so that any map with map lumps is loaded correctly
            # look for at least 2 tail lumps in order to avoid false positives
            if i < numlumps - 2 \
               and wccmp(wadio.entries[i + 1].name, self.tail[0]) \
               and wccmp(wadio.entries[i + 2].name, self.tail[1]):
                added = True
                self[name] = NameGroup()
                self[name]["_HEADER_"] = Lump(wadio.read(i))
                wadio.entries[i].been_read = True
                i += 1
                while i < numlumps and inwclist(wadio.entries[i].name, self.tail):
                    self[name][wadio.entries[i].name] = \
                        self.lumptype(wadio.read(i))
                    wadio.entries[i].been_read = True
                    i += 1
                    if wccmp(wadio.entries[i - 1].name, self.tail[-1]):
                        break
            if not added:
                i += 1

    def save_wadio(self, wadio, use_free=True):
        """Save to a WadIO object.

        If use_free is true, existing free space in the WAD will
        be used, if possible."""
        for h in self:
            hs = copy(self[h]) # temporary shallow copy
            try:
                wadio.insert(h, hs["_HEADER_"].data, use_free=use_free)
                del hs["_HEADER_"]
            except KeyError:
                wadio.insert(h, bytes())
            for t in self.tail:
                try:
                    # for UDMF maps, a wildcard is used to handle anything between 'TEXTMAP' and 'ENDMAP'
                    # after writing lumps, remove them from the shallow copy so the wildcard doesn't include them again
                    for name in wcinlist(hs, t):
                        wadio.insert(name, hs[name].data, use_free=use_free)
                        del hs[name]
                except IndexError:
                    pass


class NameGroup(LumpGroup):
    """Group for lumps recognized by special names."""

    def __init2__(self):
        self.names = self.config

    def load_wadio(self, wadio):
        """Load all matching lumps that have not already
        been flagged as read from the given WadIO object."""
        inside = False
        for i in range(len(wadio.entries)):
            if wadio.entries[i].been_read:
                continue
            name = wadio.entries[i].name
            if inwclist(name, self.names):
                self[name] = self.lumptype(wadio.read(i))
                wadio.entries[i].been_read = True

class TxdefGroup(NameGroup):
    """Group for texture definition lumps."""
    def __init2__(self):
        self.names = ['TEXTURE?', 'PNAMES']
    def __add__(self, other):
        import omg.txdef
        a = omg.txdef.Textures()
        a.from_lumps(self)
        a.from_lumps(other)
        return a.to_lumps()


#---------------------------------------------------------------------
#
# This defines the default structure for WAD files.
#

# First some lists...
_maptail    = ['THINGS',   'LINEDEFS', 'SIDEDEFS', # Must be in order
               'VERTEXES', 'SEGS',     'SSECTORS',
               'NODES',    'SECTORS',  'REJECT',
               'BLOCKMAP', 'BEHAVIOR', 'SCRIPT*']
_udmfmaptail  = ['TEXTMAP', '*', 'ENDMAP']
_glmaptail    = ['GL_VERT', 'GL_SEGS', 'GL_SSECT', 'GL_NODES']
_graphics     = ['TITLEPIC', 'CWILV*', 'WI*', 'M_*',
                 'INTERPIC', 'BRDR*',  'PFUB?', 'ST*',
                 'VICTORY2', 'CREDIT', 'END?',  'WI*',
                 'BOSSBACK', 'ENDPIC', 'HELP',  'BOX??',
                 'AMMNUM?',  'HELP1',  'DIG*']

# The default structure object.
# Must be in order: markers first, ['*'] name group last
defstruct = [
    [MarkerGroup, 'sprites',   Graphic, 'S'],
    [MarkerGroup, 'patches',   Graphic, 'P'],
    [MarkerGroup, 'flats',     Flat,    'F'],
    [MarkerGroup, 'colormaps', Lump,    'C'],
    [MarkerGroup, 'ztextures', Graphic, 'TX'],
    [HeaderGroup, 'maps',   Lump, _maptail],
    [HeaderGroup, 'glmaps', Lump, _glmaptail],
    [HeaderGroup, 'udmfmaps', Lump, _udmfmaptail],
    [NameGroup,   'music',    Music, ['D_*']],
    [NameGroup,   'sounds',   Sound, ['DS*', 'DP*']],
    [TxdefGroup,  'txdefs',   Lump,  ['TEXTURE?', 'PNAMES']],
    [NameGroup,   'graphics', Graphic, _graphics],
    [NameGroup,   'data',     Lump,  ['*']]
]

write_order = ['data', 'colormaps', 'maps', 'glmaps', 'udmfmaps', 'txdefs',
    'sounds', 'music', 'graphics', 'sprites', 'patches', 'flats',
    'ztextures']

class WAD:
    """A memory-resident, abstract representation of a WAD file. Lumps
    are stored in subsections of the WAD. Loading/saving and handling
    the sections follows the structure specification.

    Initialization:
    new = WAD([from_file, structure])

    Source may be a string representing a path to a file to load from.
    By default, an empty WAD is created.

    Structure may be used to specify a custom lump
    categorization/loading configuration.

    Member data:
        .structure     Structure definition.
        .palette       Palette
        .sprites, etc  Sections containing lumps, as specified by
                       the structure definition
    """

    def __init__(self, from_file=None, structure=defstruct):
        """Create a new WAD. The optional `source` argument may be a
        string specifying a path to a file or a WadIO object.
        If omitted, an empty WAD is created. A WADStructure object
        may be passed as the `structure` argument to apply a custom
        section structure. By default, the structure specified in the
        defdata module is used."""
        self.__category = 'root'
        self.palette = omg.palette.default
        self.structure = structure
        self.groups = []
        for group_def in self.structure:
            instance = group_def[0](*tuple(group_def[1:]))
            self.__dict__[group_def[1]] = instance
            self.groups.append(instance)
        if from_file:
            self.from_file(from_file)

    def from_file(self, source):
        """Load contents from a file. `source` may be a string
        specifying a path to a file or a WadIO object."""
        if isinstance(source, WadIO):
            w = source
        elif isinstance(source, str):
            assert os.path.exists(source)
            w = WadIO(source)
        else:
            raise TypeError("Expected WadIO or file path string")
        for group in self.groups:
            group.load_wadio(w)

    def to_file(self, filename):
        """Save contents to a WAD file. Caution: if a file with the given name
        already exists, it will be overwritten. However, the existing file will
        be kept as <filename>.tmp until the operation has finished, to stay safe
        in case of failure."""
        use_backup = os.path.exists(filename)
        tmpfilename = filename + ".tmp"
        if use_backup:
            if os.path.exists(tmpfilename):
                os.remove(tmpfilename)
            os.rename(filename, tmpfilename)
        w = WadIO(filename)
        for group in write_order:
            self.__dict__[group].save_wadio(w, use_free=False)
        w.save()
        if use_backup:
            os.remove(tmpfilename)

    def __add__(self, other):
        assert isinstance(other, WAD)
        w = WAD(structure=self.structure)
        for group_def in self.structure:
            name = group_def[1]
            w.__dict__[name] = self.__dict__[name] + other.__dict__[name]
        return w

    def copy(self):
        return deepcopy(self)
