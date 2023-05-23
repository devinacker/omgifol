from omg.util import *
from omg.lump import *
from omg.wad import NameGroup

import omg.lineinfo as lineinfo
import omg.thinginfo as thinginfo

class Vertex(WADStruct):
    """Represents a map vertex."""
    _fields_ = [
        ("x", ctypes.c_int16),
        ("y", ctypes.c_int16)
    ]

class GLVertex(WADStruct):
    """Represents a map GL vertex."""
    _fields_ = [
        ("x", ctypes.c_int32),
        ("y", ctypes.c_int32)
    ]

class Sidedef(WADStruct):
    """Represents a map sidedef."""
    _fields_ = [
        ("off_x",  ctypes.c_int16),
        ("off_y",  ctypes.c_int16),
        ("tx_up",  ctypes.c_char * 8),
        ("tx_low", ctypes.c_char * 8),
        ("tx_mid", ctypes.c_char * 8),
        ("sector", ctypes.c_uint16)
    ]

    def __init__(self, *args, **kwargs):
        self.tx_up = self.tx_low = self.tx_mid = "-"
        super().__init__(*args, **kwargs)

class Linedef(WADStruct):
    """
    Represents a map linedef.

    Linedef.NONE is the placeholder value for unused sidedefs.
    Using the value -1 is no longer supported.
    """
    NONE = 0xffff

    _flags_ = [
        ("impassable",     1),
        ("block_monsters", 1),
        ("two_sided",      1),
        ("upper_unpeg",    1),
        ("lower_unpeg",    1),
        ("secret",         1),
        ("block_sound",    1),
        ("invisible",      1),
        ("automap",        1)
    ]

    _fields_ = [
        ("vx_a",   ctypes.c_uint16),
        ("vx_b",   ctypes.c_uint16),
        ("flags",  WADFlags(_flags_)),
        ("action", ctypes.c_uint16),
        ("tag",    ctypes.c_uint16),
        ("front",  ctypes.c_uint16),
        ("back",   ctypes.c_uint16)
    ]
    _anonymous_ = ("flags",)

    def __init__(self, *args, **kwargs):
        self.front = self.back = Linedef.NONE
        super().__init__(*args, **kwargs)

# TODO: an enum or something for triggers
class ZLinedef(WADStruct):
    """
    Represents a map linedef (Hexen / ZDoom).

    Linedef.NONE is the placeholder value for unused sidedefs.
    Using the value -1 is no longer supported.
    """
    _flags_ = [
        ("impassable",     1),
        ("block_monsters", 1),
        ("two_sided",      1),
        ("upper_unpeg",    1),
        ("lower_unpeg",    1),
        ("secret",         1),
        ("block_sound",    1),
        ("invisible",      1),
        ("automap",        1),
        ("repeat",         1),
        ("trigger",        3),
        ("activate_any",   1),
        ("dummy",          1),
        ("block_all",      1)
    ]

    _fields_ = [
        ("vx_a",   ctypes.c_uint16),
        ("vx_b",   ctypes.c_uint16),
        ("flags",  WADFlags(_flags_)),
        ("action", ctypes.c_ubyte),
        ("arg0",   ctypes.c_ubyte),
        ("arg1",   ctypes.c_ubyte),
        ("arg2",   ctypes.c_ubyte),
        ("arg3",   ctypes.c_ubyte),
        ("arg4",   ctypes.c_ubyte),
        ("front",  ctypes.c_uint16),
        ("back",   ctypes.c_uint16)
    ]
    _anonymous_ = ("flags",)

    def __init__(self, *args, **kwargs):
        self.front = self.back = Linedef.NONE
        super().__init__(*args, **kwargs)

class Thing(WADStruct):
    """Represents a map thing."""
    _flags_ = [
        ("easy",        1),
        ("medium",      1),
        ("hard",        1),
        ("deaf",        1),
        ("multiplayer", 1)
    ]

    _fields_ = [
        ("x",     ctypes.c_int16),
        ("y",     ctypes.c_int16),
        ("angle", ctypes.c_uint16),
        ("type",  ctypes.c_uint16),
        ("flags", WADFlags(_flags_))
    ]
    _anonymous_ = ("flags",)

class ZThing(WADStruct):
    """Represents a map thing (Hexen / ZDoom)."""
    _flags_ = [
        ("easy",        1),
        ("medium",      1),
        ("hard",        1),
        ("deaf",        1),
        ("dormant",     1),
        ("fighter",     1),
        ("cleric",      1),
        ("mage",        1),
        ("solo",        1),
        ("multiplayer", 1),
        ("deathmatch",  1)
    ]

    _fields_ = [
        ("tid",     ctypes.c_uint16),
        ("x",       ctypes.c_int16),
        ("y",       ctypes.c_int16),
        ("height",  ctypes.c_int16),
        ("angle",   ctypes.c_uint16),
        ("type",    ctypes.c_uint16),
        ("flags",   WADFlags(_flags_)),
        ("action",  ctypes.c_ubyte),
        ("arg0",    ctypes.c_ubyte),
        ("arg1",    ctypes.c_ubyte),
        ("arg2",    ctypes.c_ubyte),
        ("arg3",    ctypes.c_ubyte),
        ("arg4",    ctypes.c_ubyte)
    ]
    _anonymous_ = ("flags",)

class Sector(WADStruct):
    """Represents a map sector."""
    _fields_ = [
        ("z_floor",  ctypes.c_int16),
        ("z_ceil",   ctypes.c_int16),
        ("tx_floor", ctypes.c_char * 8),
        ("tx_ceil",  ctypes.c_char * 8),
        ("light",    ctypes.c_uint16),
        ("type",     ctypes.c_uint16),
        ("tag",      ctypes.c_uint16)
    ]

    def __init__(self, *args, **kwargs):
        self.z_ceil = 128
        self.light = 160
        self.tx_floor = "FLOOR4_8"
        self.tx_ceil = "CEIL3_5"
        super().__init__(*args, **kwargs)

class Node(WADStruct):
    """Represents a BSP tree node."""
    _fields_ = [
        ("x_start",           ctypes.c_int16),
        ("y_start",           ctypes.c_int16),
        ("x_vector",          ctypes.c_int16),
        ("y_vector",          ctypes.c_int16),
        ("right_bbox_top",    ctypes.c_int16),
        ("right_bbox_bottom", ctypes.c_int16),
        ("right_bbox_left",   ctypes.c_int16),
        ("right_bbox_right",  ctypes.c_int16),
        ("left_bbox_top",     ctypes.c_int16),
        ("left_bbox_bottom",  ctypes.c_int16),
        ("left_bbox_left",    ctypes.c_int16),
        ("left_bbox_right",   ctypes.c_int16),
        ("right_index",       ctypes.c_uint16),
        ("left_index",        ctypes.c_uint16)
    ]

class Seg(WADStruct):
    """Represents a map seg."""
    _fields_ = [
        ("vx_a",   ctypes.c_uint16),
        ("vx_b",   ctypes.c_uint16),
        ("angle",  ctypes.c_uint16),
        ("line",   ctypes.c_uint16),
        ("side",   ctypes.c_uint16),
        ("offset", ctypes.c_uint16)
    ]

class GLSeg(WADStruct):
    """Represents a map GL seg."""
    _fields_ = [
        ("vx_a",    ctypes.c_uint16),
        ("vx_b",    ctypes.c_uint16),
        ("line",    ctypes.c_uint16),
        ("side",    ctypes.c_uint16),
        ("partner", ctypes.c_uint16)
    ]

class SubSector(WADStruct):
    """Represents a map subsector."""
    _fields_ = [
        ("numsegs", ctypes.c_uint16),
        ("seg_a",   ctypes.c_uint16)
    ]

class MapEditor:
    """Doom map editor.

    Data members:
        header        Lump object consisting of data in map header (if any)
        vertexes      List containing Vertex objects
        sidedefs      List containing Sidedef objects
        linedefs      List containing Linedef or ZLinedef objects
        sectors       List containing Sector objects
        things        List containing Thing or ZThing objects

    Data members (Hexen/ZDoom formats only):
        behavior      Lump object containing compiled ACS scripts
        scripts       Lump object containing ACS script source

    Other members:
        Thing         alias to Thing or ZThing class, depending on format
        Linedef       alias to Linedef or ZLinedef class, depending on format

    Currently present but unused:
        segs          List containing Seg objects
        ssectors      List containing SubSector objects
        nodes         List containing Node objects
        blockmap      Lump object containing blockmap data
        reject        Lump object containing reject table data
        (These five lumps are not updated when saving; you will need to use
        an external node builder utility)
        """

    def __init__(self, from_lumps=None):
        """Create new, optionally from a lump group."""
        if from_lumps is not None:
            self.from_lumps(from_lumps)
        else:
            self.Thing   = Thing
            self.Linedef = Linedef

            self.header   = Lump()
            self.vertexes = []
            self.sidedefs = []
            self.linedefs = []
            self.sectors  = []
            self.things   = []
            self.segs     = []
            self.ssectors = []
            self.nodes    = []
            self.blockmap = Lump("")
            self.reject   = Lump("")

    def _unpack_lump(self, class_, data):
        s = ctypes.sizeof(class_)
        return [class_(bytes=data[i:i+s]) for i in range(0,len(data),s)]

    def from_lumps(self, lumpgroup):
        """Load entries from a lump group."""
        m = lumpgroup

        try:
            self.header   = m["_HEADER_"]

            self.vertexes = self._unpack_lump(Vertex,    m["VERTEXES"].data)
            self.sidedefs = self._unpack_lump(Sidedef,   m["SIDEDEFS"].data)
            self.sectors  = self._unpack_lump(Sector,    m["SECTORS"].data)

            if "BEHAVIOR" in m:
                # Hexen / ZDoom map
                self.Thing   = ZThing
                self.Linedef = ZLinedef
                self.behavior = m["BEHAVIOR"]
                # optional script sources
                try:
                    self.scripts = m[wcinlist(m, "SCRIPT*")[0]]
                except IndexError:
                    self.scripts = Lump()
            else:
                self.Thing   = Thing
                self.Linedef = Linedef
                try:
                    del self.behavior
                    del self.scripts
                except AttributeError:
                    pass

            self.things   = self._unpack_lump(self.Thing,   m["THINGS"].data)
            self.linedefs = self._unpack_lump(self.Linedef, m["LINEDEFS"].data)
        except KeyError as e:
            raise ValueError("map is missing %s lump" % e)

        from struct import error as StructError
        try:
            self.ssectors = self._unpack_lump(SubSector, m["SSECTORS"].data)
            self.segs     = self._unpack_lump(Seg,       m["SEGS"].data)
            self.nodes    = self._unpack_lump(Node,      m["NODES"].data)
            self.blockmap = m["BLOCKMAP"]
            self.reject   = m["REJECT"]
        except (KeyError, StructError):
            # nodes failed to build - we don't really care
            # TODO: this also "handles" (read: ignores) expanded zdoom nodes)
            self.ssectors = []
            self.segs     = []
            self.nodes    = []
            self.blockmap = Lump()
            self.reject   = Lump()

    def load_gl(self, mapobj):
        """Load GL nodes entries from a map."""
        vxdata = mapobj["GL_VERT"].data[4:]  # s[:4] == "gNd3" ?
        self.gl_vert  = self._unpack_lump(GLVertex,  vxdata)
        self.gl_segs  = self._unpack_lump(GLSeg,     mapobj["GL_SEGS"].data)
        self.gl_ssect = self._unpack_lump(SubSector, mapobj["GL_SSECT"].data)

    def to_lumps(self):
        m = NameGroup()

        m["_HEADER_"] = self.header
        m["VERTEXES"] = Lump(join([x.pack() for x in self.vertexes]))
        m["THINGS"  ] = Lump(join([x.pack() for x in self.things  ]))
        m["LINEDEFS"] = Lump(join([x.pack() for x in self.linedefs]))
        m["SIDEDEFS"] = Lump(join([x.pack() for x in self.sidedefs]))
        m["SECTORS" ] = Lump(join([x.pack() for x in self.sectors ]))
        m["NODES"]    = Lump(join([x.pack() for x in self.nodes   ]))
        m["SEGS"]     = Lump(join([x.pack() for x in self.segs    ]))
        m["SSECTORS"] = Lump(join([x.pack() for x in self.ssectors]))
        m["BLOCKMAP"] = self.blockmap
        m["REJECT"]   = self.reject

        # hexen / zdoom script lumps
        try:
            m["BEHAVIOR"] = self.behavior
            m["SCRIPTS"]  = self.scripts
        except AttributeError:
            pass

        return m

    def draw_sector(self, vertexes, sector=None, sidedef=None):
        """Draw a polygon from a list of vertexes. The vertexes may be
        either Vertex objects or simple (x, y) tuples. A sector object
        and prototype sidedef may be provided."""
        assert len(vertexes) > 2
        firstv = len(self.vertexes)
        firsts = len(self.sidedefs)
        if sector  is None: sector  = Sector()
        if sidedef is None: sidedef = Sidedef()
        self.sectors.append(copy(sector))
        for i, v in enumerate(vertexes):
            if isinstance(v, tuple):
                x, y = v
            else:
                x, y = v.x, v.y
            self.vertexes.append(Vertex(x, y))
        for i in range(len(vertexes)):
            side = copy(sidedef)
            side.sector = len(self.sectors)-1
            self.sidedefs.append(side)

            #check if the new line is being written over an existing
            #and merge them if so.
            new_linedef = Linedef(vx_a=firstv+((i+1)%len(vertexes)),
                                  vx_b=firstv+i, front=firsts+i, flags=1)
            match_existing = False
            for lc in self.linedefs:
                if (self.compare_linedefs(new_linedef,lc) > 0):
                    #remove midtexture and apply it to the upper/lower
                    side.tx_low = self.sidedefs[lc.front].tx_mid
                    side.tx_up = self.sidedefs[lc.front].tx_mid
                    self.sidedefs[lc.front].tx_low = side.tx_mid
                    self.sidedefs[lc.front].tx_up = side.tx_mid
                    side.tx_mid = "-"
                    self.sidedefs[lc.front].tx_mid = "-"
                    lc.back = len(self.sidedefs)-1
                    match_existing = True
                    lc.two_sided = True
                    lc.impassable = False
                    break
            if (match_existing == False):
                self.linedefs.append(new_linedef)

    def compare_vertex_positions(self,vertex1,vertex2):
        """Compares the positions of two vertices."""
        if (vertex1.x == vertex2.x):
            if (vertex1.y == vertex2.y):
                return True
        return False

    def compare_linedefs(self,linedef1,linedef2):
        """Compare the vertex positions of two linedefs.
        Returns 0 for mismatch.
        Returns 1 when the vertex positions are the same.
        Returns 2 when the vertex positions are in the same order.
        Returns 3 when the linedefs use the same vertices, but flipped.
        Returns 4 when the linedefs use the exact same vertices.
        """
        if (linedef1.vx_a == linedef2.vx_a):
            if (linedef1.vx_b == linedef2.vx_b):
                return 4

        if (linedef1.vx_a == linedef2.vx_b):
            if (linedef1.vx_b == linedef2.vx_a):
                return 3

        if (self.compare_vertex_positions(self.vertexes[linedef1.vx_a],
            self.vertexes[linedef2.vx_a])):
            if (self.compare_vertex_positions(self.vertexes[linedef1.vx_b],
                self.vertexes[linedef2.vx_b])):
                return 2

        if (self.compare_vertex_positions(self.vertexes[linedef1.vx_a],
            self.vertexes[linedef2.vx_b])):
            if (self.compare_vertex_positions(self.vertexes[linedef1.vx_b],
                self.vertexes[linedef2.vx_a])):
                return 1

        return 0

    def compare_sectors(self,sect1,sect2):
        """Compare two sectors' data and returns True when they match."""
        if (sect1.z_floor == sect2.z_floor and
            sect1.z_ceil == sect2.z_ceil and
            sect1.tx_floor == sect2.tx_floor and
            sect1.tx_ceil == sect2.tx_ceil and
            sect1.light == sect2.light and
            sect1.type == sect2.type and
            sect1.tag == sect2.tag):
            return True
        return False

    def combine_sectors(self,sector1,sector2,remove_linedefs=True):
        """Combines two sectors together, replacing all references to
        the second with the first. If remove_linedefs is true, any
        linedefs that connect the two sectors will be removed."""
        for sd in self.sidedefs:
            if (self.sectors[sd.sector] == sector2):
                sd.sector = self.sectors.index(sector1)

                if (remove_linedefs):
                    for lc in self.linedefs:
                        if (lc.back != Linedef.NONE):
                            if (self.sectors[self.sidedefs[lc.front].sector] == sector1 and
                                self.sectors[self.sidedefs[lc.back].sector] == sector1):
                                self.linedefs.remove(lc)
        # we can rely on a nodebuilder to remove unused sectors
        # self.sectors[self.sectors.index(sector2)].tx_floor = "_REMOVED"

    def paste(self, other, offset=(0,0)):
        """Insert content of another map."""
        vlen = len(self.vertexes)
        ilen = len(self.sidedefs)
        slen = len(self.sectors)
        for vx in other.vertexes:
            x, y = vx.x, vx.y
            self.vertexes.append(Vertex(x+offset[0], y+offset[1]))
        for line in other.linedefs:
            z = copy(line)
            z.vx_a += vlen
            z.vx_b += vlen
            if z.front != Linedef.NONE: z.front += ilen
            if z.back != Linedef.NONE: z.back += ilen
            self.linedefs.append(z)
        for side in other.sidedefs:
            z = copy(side)
            z.sector += slen
            self.sidedefs.append(z)
        for sector in other.sectors:
            z = copy(sector)
            self.sectors.append(z)
        for thing in other.things:
            z = copy(thing)
            z.x += offset[0]
            z.y += offset[1]
            self.things.append(z)
