from omg.lump import Lump
from omg.util import *
from omg.wad  import TxdefGroup

class TextureDef(WADStruct):
    """Class for texture definitions."""
    _fields_ = [
        ("name",     ctypes.c_char * 8),
        ("dummy1",   ctypes.c_uint32),
        ("width",    ctypes.c_int16),
        ("height",   ctypes.c_int16),
        ("dummy2",   ctypes.c_uint32),
        ("npatches", ctypes.c_int16),
    ]

    def __init__(self, *args, **kwargs):
        self.name = "-"
        self.patches = []
        super().__init__(*args, **kwargs)

class PatchDef(WADStruct):
    """Class for patches."""
    _fields_ = [
        ("x",      ctypes.c_int16),
        ("y",      ctypes.c_int16),
        ("id",     ctypes.c_int16),
        ("dummy1", ctypes.c_uint16),
        ("dummy2", ctypes.c_uint16)
    ]

    def __init__(self, *args, **kwargs):
        self.name = "-"
        self.id = -1
        super().__init__(*args, **kwargs)

# TODO: integrate with textures lump group instead?

class Textures(OrderedDict):
    """An editor for Doom's TEXTURE1, TEXTURE2 and PNAMES lumps."""

    def __init__(self, *args):
        """Create new, optionally loading content from given
        TEXTURE1/2 and PNAMES lumps or a txdefs group. E.g.:

            Textures(texture1, pnames)
            Textures(txdefs)
        """
        OrderedDict.__init__(self)
        if len(args):
            self.from_lumps(*args)

    def from_lumps(self, *args):
        """Load texture definitions from a TEXTURE1/2 lump and its
        associated PNAMES lump, or a lump group containing the lumps."""
        from omg.wad import LumpGroup
        if len(args) == 1:
            g = args[0]
            assert isinstance(g, LumpGroup)
            if "TEXTURE1" in g: self.from_lumps(g["TEXTURE1"], g["PNAMES"])
            if "TEXTURE2" in g: self.from_lumps(g["TEXTURE2"], g["PNAMES"])
        elif len(args) == 2:
            self._from_lumps(args[0], args[1])

    def _from_lumps(self, texture1, pnames):
        # Unpack PNAMES
        numdefs = unpack16(pnames.data[0:2])
        pnames = [zstrip(pnames.data[ptr:ptr+8]) \
            for ptr in range(4, 8*numdefs+4, 8)]

        # Unpack TEXTURE1
        data = texture1.data
        numtextures = unpack('<i', data[0:4])[0]
        pointers = unpack('<%ii'%numtextures, data[4:4+numtextures*4])
        for ptr in pointers:
            texture = TextureDef(bytes=data[ptr:ptr+22])
            for pptr in range(ptr+22, ptr+22+10*texture.npatches, 10):
                x, y, idn = unpack('<hhh', data[pptr:pptr+6])
                texture.patches.append(PatchDef(x, y, name=pnames[idn]))
            self[texture.name] = texture

    def to_lumps(self):
        """Returns two lumps TEXTURE1, PNAMES."""
        textures = self.items()
        textures.sort()

        pnames = []
        # Count unique patch names, assign correct num to each patch
        used_pnames = {}
        for name, data in textures:
            for p in data.patches:
                if p.name not in used_pnames:
                    used_pnames[p.name] = len(used_pnames)
                p.id = used_pnames[p.name]
        pnmap = sorted([(i, name) for (name, i) in used_pnames.items()])
        pnames = pack32(len(pnmap)) + \
            bytes().join(zpad(safe_name(name)) for i, name in pnmap)

        texture1 = []
        pointers = []
        ptr = 4 + len(self)*4
        for name, data in textures:
            data.npatches = len(data.patches)
            texture1.append(data.pack())
            texture1.append(bytes().join(p.pack() for p in data.patches))
            pointers.append(ptr)
            ptr += 22 + data.npatches*10

        a = pack32(len(textures))
        #print "a", len(a)
        b = bytes().join([pack32(p) for p in pointers])
        #print "b", len(b)
        #print "texture1", type(texture1), len(texture1)
        #print texture1
        c = bytes().join(texture1)
        texture1 = bytes().join([a, b, c])

        g = TxdefGroup('txdefs', Lump, ['TEXTURE?', 'PNAMES'])
        g['TEXTURE1'], g['PNAMES'] = Lump(texture1), Lump(pnames)
        return g

    def simple(self, name, plump):
        """Create a simple texture with a given name, from a given lump."""
        self[name] = TextureDef()
        self[name].patches.append(PatchDef())
        self[name].patches[0].name = self[name].name = name
        self[name].width, self[name].height = plump.dimensions
