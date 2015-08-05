from omg.util import *
from omg.lump import *
from omg.wad import NameGroup

import omg.lineinfo as lineinfo
import omg.thinginfo as thinginfo

Vertex = make_struct(
  "Vertex", """Represents a map vertex""",
  [["x", "h", 0],
   ["y", "h", 0]]
)

GLVertex = make_struct(
  "GLVertex", """Represents a map GL vertex""",
  [["x", "l", 0],
   ["y", "l", 0]]
)

Sidedef = make_struct(
  "Sidedef", """Represents a map sidedef""",
  [["off_x",  'h',  0  ],
   ["off_y",  'h',  0  ],
   ["tx_up",  '8s', "-"],
   ["tx_low", '8s', "-"],
   ["tx_mid", '8s', "-"],
   ["sector", 'h',  -1 ]]
)

Linedef = make_struct(
  "Linedef", """Represents a map linedef""",
  [["vx_a",   'h', -1],
   ["vx_b",   'h', -1],
   ["flags",  'h',  0],
   ["action", 'h',  0],
   ["tag",    'h',  0],
   ["front",  'h', -1],
   ["back",   'h', -1]],
  ["impassable", "block_monsters", "two_sided",
   "upper_unpeg", "lower_unpeg", "secret",
   "block_sound", "invisible", "automap"]
)

ZLinedef = make_struct(
  "Linedef", """Represents a map linedef (Hexen / ZDoom)""",
  [["vx_a",   'h', -1],
   ["vx_b",   'h', -1],
   ["flags",  'h',  0],
   ["action", 'b',  0],
   ["arg1",   'b',  0],
   ["arg2",   'b',  0],
   ["arg3",   'b',  0],
   ["arg4",   'b',  0],
   ["arg5",   'b',  0],
   ["front",  'h', -1],
   ["back",   'h', -1]],
  ["impassable", "block_monsters", "two_sided",
   "upper_unpeg", "lower_unpeg", "secret",
   "block_sound", "invisible", "automap",
   "repeat", "player_use", "monster_cross",
   "player_hit", "activate_any", "dummy",
   "block_all"]
)

# http://www.doomworld.com/vb/post/1404752
AlphaLinedef = make_struct(
  "Linedef", """Represents a map linedef (Doom alpha 0.3)""",
  [["vx_a",   'h', -1],
   ["vx_b",   'h', -1],
   ["flags",  'h',  0],
   ["dummy1", 'h',  0], #?
   
   ["front",  'h', -1], # this is an unknown value in the original.
                        # i'm reusing it to store sidedef 1
   ["sector1", 'h', -1],
   ["off_x1",  'h', -1],
   ["tx_mid1", 'h', -1], # textures are numbered instead of named
   ["tx_up1",  'h', -1],
   ["tx_low1", 'h', -1],
   
   ["back",  'h', -1], # this is an unknown value in the original.
                       # i'm reusing it to store sidedef 2
   ["sector2", 'h', -1],
   ["off_x2",  'h', -1],
   ["tx_mid2", 'h', -1],
   ["tx_up2",  'h', -1],
   ["tx_low2", 'h', -1]],
  ["impassable", "block_monsters", "two_sided",
   "upper_unpeg", "lower_unpeg", "secret",
   "block_sound", "invisible", "automap"]
)

Thing = make_struct(
  "Thing", """Represents a map thing""",
  [["x",     'h', 0],
   ["y",     'h', 0],
   ["angle", 'h', 0],
   ["type",  'h', 0],
   ["flags", 'h', 0]],
  ["easy", "medium", "hard", "deaf", "multiplayer"]
)

ZThing = make_struct(
  "Thing", """Represents a map thing (Hexen / ZDoom)""",
  [["tid",    'h', 0],
   ["x",      'h', 0],
   ["y",      'h', 0],
   ["height", 'h', 0],
   ["angle",  'h', 0],
   ["type",   'h', 0],
   ["flags",  'h', 0],
   ["action", 'b', 0],
   ["arg1",   'b', 0],
   ["arg2",   'b', 0],
   ["arg3",   'b', 0],
   ["arg4",   'b', 0],
   ["arg5",   'b', 0]],
  ["easy", "medium", "hard", "deaf", "dormant",
   "fighter", "cleric", "mage", "solo", "multiplayer", "deathmatch"]
)

#12 bytes
AlphaThing = make_struct(
  "Thing", """Represents a map thing (Doom alpha 0.4/0.5)""",
  [["x",     'h', 0],
   ["y",     'h', 0],
   ["angle", 'h', 0],
   ["type",  'h', 0],
   ["dummy", 'h', 0], # ?
   ["flags", 'h', 0]],
  ["easy", "medium", "hard", "deaf", "multiplayer"]
)

Sector = make_struct(
  "Sector", """Represents a map sector""",
  [["z_floor",  'h',  0],
   ["z_ceil",   'h',  128],
   ["tx_floor", '8s', "FLOOR4_8"],
   ["tx_ceil",  '8s', "CEIL3_5"],
   ["light",    'h',  160],
   ["type",     'h',  0],
   ["tag",      'h',  0]]
)

Seg = make_struct(
  "Seg", """Represents a map seg""",
  [["vx_a",   'h', 0],
   ["vx_b",   'h', 0],
   ["angle",  'h', 0],
   ["line",   'h', 0],
   ["side",   'h', 0],
   ["offset", 'h', 0]]
)

SubSector = make_struct(
  "SubSector", """Represents a map subsector""",
  [["numsegs", 'h', 0],
   ["seg_a",   'H', 0]]
)

GLSeg = make_struct(
  "GLSeg", """Represents a map GL seg""",
  [["vx_a",    'h', 0],
   ["vx_b",    'h', 0],
   ["line",    'h', 0],
   ["side",    'h', 0],
   ["partner", 'h', 0]]
)

class MapEditor:
    """Doom map editor

    Data members:
        vertexes      List containing Vertex objects
        sidedefs      List containing Sidedef objects
        linedefs      List containing Linedef objects
        sectors       List containing Sector objects
        things        List containing Thing objects"""

    def __init__(self, from_lumps=None):
        """Create new, optionally from a lump group"""
        if from_lumps is not None:
            self.from_lumps(from_lumps)
        else:
            self.vertexes = []
            self.sidedefs = []
            self.linedefs = []
            self.sectors  = []
            self.things   = []
            self.segs     = []
            self.ssectors = []

    def _unpack_lump(self, class_, data):
        s = class_._fmtsize
        return [class_(bytes=data[i:i+s]) for i in xrange(0,len(data),s)]

    def from_lumps(self, lumpgroup):
        """Load entries from a lump group."""
        m = lumpgroup
        try:
            if "FLATNAME" in m: # alpha 0.4/0.5 map
                self.vertexes = self._unpack_lump(Vertex,       m["POINTS"].data[4:])
                self.linedefs = self._unpack_lump(AlphaLinedef, m["LINES"].data[4:])
                self.sectors  = []
                self.things   = self._unpack_lump(AlphaThing,   m["THINGS"].data[4:])
                
                self.sidedefs = []
                #TODO: convert sectors
                
                # make sidedefs from linedefs using repurposed front/back fields
                # TODO: do something about texture numbers (TEXTURES lump)
                for line in self.linedefs:
                    if line.sector1 >= 0:
                        line.front = len(self.sidedefs)
                        self.sidedefs.append(Sidedef(line.off_x1, 0, line.tx_up1, line.tx_low1, line.tx_mid1, line.sector1))
                    else:
                        line.front = -1
                    
                    if line.sector2 >= 0:
                        line.back = len(self.sidedefs)
                        self.sidedefs.append(Sidedef(line.off_x2, 0, line.tx_up2, line.tx_low2, line.tx_mid2, line.sector2))
                    else:
                        line.back = -1
            else:
                self.vertexes = self._unpack_lump(Vertex,    m["VERTEXES"].data)
                self.sidedefs = self._unpack_lump(Sidedef,   m["SIDEDEFS"].data)
                self.sectors  = self._unpack_lump(Sector,    m["SECTORS"].data)
                
                if "BEHAVIOR" in m: # Hexen / ZDoom map
                    self.things   = self._unpack_lump(ZThing,    m["THINGS"].data)
                    self.linedefs = self._unpack_lump(ZLinedef,  m["LINEDEFS"].data)
                else:
                    self.things   = self._unpack_lump(Thing,     m["THINGS"].data)
                    self.linedefs = self._unpack_lump(Linedef,   m["LINEDEFS"].data)
        except KeyError as e:
            raise ValueError("map is missing %s lump" % e)
        
        try:
            self.ssectors = self._unpack_lump(SubSector, m["SSECTORS"].data)
            self.segs     = self._unpack_lump(Seg,       m["SEGS"].data)
            self.blockmap = m["BLOCKMAP"]
            self.reject   = m["REJECT"]
            self.nodes    = m["NODES"]
        except KeyError:
            # nodes failed to build - we don't really care
            self.ssectors = []
            self.segs     = []
            self.blockmap = []
            self.reject   = []
            self.nodes    = []

    def load_gl(self, mapobj):
        """Load GL nodes entries from a map"""
        vxdata = mapobj["GL_VERT"].data[4:]  # s[:4] == "gNd3" ?
        self.gl_vert  = self._unpack_lump(GLVertex,  vxdata)
        self.gl_segs  = self._unpack_lump(GLSeg,     mapobj["GL_SEGS"].data)
        self.gl_ssect = self._unpack_lump(SubSector, mapobj["GL_SSECT"].data)

    def to_lumps(self):
        m = NameGroup()
        m["_HEADER_"] = Lump("")
        m["VERTEXES"] = Lump(join([x.pack() for x in self.vertexes]))
        m["THINGS"  ] = Lump(join([x.pack() for x in self.things  ]))
        m["LINEDEFS"] = Lump(join([x.pack() for x in self.linedefs]))
        m["SIDEDEFS"] = Lump(join([x.pack() for x in self.sidedefs]))
        m["SECTORS" ] = Lump(join([x.pack() for x in self.sectors ]))
        m["NODES"]    = self.nodes
        m["SEGS"]     = Lump(join([x.pack() for x in self.segs    ]))
        m["SSECTORS"] = Lump(join([x.pack() for x in self.ssectors]))
        m["BLOCKMAP"] = self.blockmap
        m["REJECT"]   = self.reject
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
            self.linedefs.append(
              Linedef(vx_a=firstv+((i+1)%len(vertexes)),
              vx_b=firstv+i, front=firsts+i, flags=1))

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
            if z.front != -1: z.front += ilen
            if z.back != -1: z.back += ilen
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

