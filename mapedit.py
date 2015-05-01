from omg.util import *
from omg.lump import *
from omg.wad import NameGroup

import omg.lineinfo as lineinfo
import omg.thinginfo as thinginfo

import math

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
   ["sector", 'H',   0 ]]
)

Linedef = make_struct(
  "Linedef", """Represents a map linedef""",
  [["vx_a",   'H',  0],
   ["vx_b",   'H',  0],
   ["flags",  'H',  0],
   ["action", 'H',  0],
   ["tag",    'H',  0],
   ["front",  'H', -1],
   ["back",   'H', -1]],
  ["impassable", "block_monsters", "two_sided",
   "upper_unpeg", "lower_unpeg", "secret",
   "block_sound", "invisible", "automap"]
)

# TODO: an enum or something for triggers
ZLinedef = make_struct(
  "ZLinedef", """Represents a map linedef (Hexen / ZDoom)""",
  [["vx_a",   'H',  0],
   ["vx_b",   'H',  0],
   ["flags",  'H',  0],
   ["action", 'B',  0],
   ["arg0",   'B',  0],
   ["arg1",   'B',  0],
   ["arg2",   'B',  0],
   ["arg3",   'B',  0],
   ["arg4",   'B',  0],
   ["front",  'H', -1],
   ["back",   'H', -1]],
  ["impassable", "block_monsters", "two_sided",
   "upper_unpeg", "lower_unpeg", "secret",
   "block_sound", "invisible", "automap",
   "repeat", ("trigger", 3),
   "activate_any", None, "block_all"]
)

Thing = make_struct(
  "Thing", """Represents a map thing""",
  [["x",     'h', 0],
   ["y",     'h', 0],
   ["angle", 'H', 0],
   ["type",  'H', 0],
   ["flags", 'H', 0]],
  ["easy", "medium", "hard", "deaf", "multiplayer"]
)

ZThing = make_struct(
  "ZThing", """Represents a map thing (Hexen / ZDoom)""",
  [["tid",    'H', 0],
   ["x",      'h', 0],
   ["y",      'h', 0],
   ["height", 'h', 0],
   ["angle",  'H', 0],
   ["type",   'H', 0],
   ["flags",  'H', 0],
   ["action", 'B', 0],
   ["arg0",   'B', 0],
   ["arg1",   'B', 0],
   ["arg2",   'B', 0],
   ["arg3",   'B', 0],
   ["arg4",   'B', 0]],
  ["easy", "medium", "hard", "deaf", "dormant",
   "fighter", "cleric", "mage", "solo", "multiplayer", "deathmatch"]
)

Sector = make_struct(
  "Sector", """Represents a map sector""",
  [["z_floor",  'h',  0],
   ["z_ceil",   'h',  128],
   ["tx_floor", '8s', "FLOOR4_8"],
   ["tx_ceil",  '8s', "CEIL3_5"],
   ["light",    'H',  160],
   ["type",     'H',  0],
   ["tag",      'H',  0]]
)

Seg = make_struct(
  "Seg", """Represents a map seg""",
  [["vx_a",   'H', 0],
   ["vx_b",   'H', 0],
   ["angle",  'H', 0],
   ["line",   'H', 0],
   ["side",   'H', 0],
   ["offset", 'H', 0]]
)

SubSector = make_struct(
  "SubSector", """Represents a map subsector""",
  [["numsegs", 'H', 0],
   ["seg_a",   'H', 0]]
)

GLSeg = make_struct(
  "GLSeg", """Represents a map GL seg""",
  [["vx_a",    'H', 0],
   ["vx_b",    'H', 0],
   ["line",    'H', 0],
   ["side",    'H', 0],
   ["partner", 'H', 0]]
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
            self.nodes    = Lump("")
            self.blockmap = Lump("")
            self.reject   = Lump("")

    def _unpack_lump(self, class_, data):
        s = class_._fmtsize
        return [class_(bytes=data[i:i+s]) for i in xrange(0,len(data),s)]

    def from_lumps(self, lumpgroup):
        """Load entries from a lump group."""
        m = lumpgroup
        try:
            self.vertexes = self._unpack_lump(Vertex,    m["VERTEXES"].data)
            self.sidedefs = self._unpack_lump(Sidedef,   m["SIDEDEFS"].data)
            self.sectors  = self._unpack_lump(Sector,    m["SECTORS"].data)
            
            if "BEHAVIOR" in m: # Hexen / ZDoom map
                self.things   = self._unpack_lump(ZThing,    m["THINGS"].data)
                self.linedefs = self._unpack_lump(ZLinedef,  m["LINEDEFS"].data)
                
                self.behavior = m["BEHAVIOR"].data
                if "SCRIPTS" in m:
                    self.scripts = m["SCRIPTS"].data
                else:
                    self.scripts = []
            else:
                self.things   = self._unpack_lump(Thing,     m["THINGS"].data)
                self.linedefs = self._unpack_lump(Linedef,   m["LINEDEFS"].data)
        except KeyError as e:
            raise ValueError("map is missing %s lump" % e)
        
        # use -1 for unused sidedefs instead of 0xFFFF
        for line in self.linedefs:
            if line.front == 0xFFFF: line.front = -1
            if line.back  == 0xFFFF: line.back  = -1
        
        from struct import error as StructError
        try:
            self.ssectors = self._unpack_lump(SubSector, m["SSECTORS"].data)
            self.segs     = self._unpack_lump(Seg,       m["SEGS"].data)
            self.blockmap = m["BLOCKMAP"]
            self.reject   = m["REJECT"]
            self.nodes    = m["NODES"]
        except (KeyError, StructError):
            # nodes failed to build - we don't really care
            # TODO: this also "handles" (read: ignores) expanded zdoom nodes)
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
        
        # change -1 to 0xFFFF so linedefs pack correctly
        linedefs = self.linedefs[:]
        for line in linedefs:
            if line.front == -1: line.front = 0xFFFF
            if line.back  == -1: line.back  = 0xFFFF
        
        m["_HEADER_"] = Lump("")
        m["VERTEXES"] = Lump(join([x.pack() for x in self.vertexes]))
        m["THINGS"  ] = Lump(join([x.pack() for x in self.things  ]))
        m["LINEDEFS"] = Lump(join([x.pack() for x in linedefs     ]))
        m["SIDEDEFS"] = Lump(join([x.pack() for x in self.sidedefs]))
        m["SECTORS" ] = Lump(join([x.pack() for x in self.sectors ]))
        m["NODES"]    = self.nodes
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
        
        new_lines = []
            
        for i in range(len(vertexes)):
            side = copy(sidedef)
            side.sector = len(self.sectors)-1
            self.sidedefs.append(side)
            
            new_linedef = Linedef(vx_a=firstv+((i+1)%len(vertexes)),
                                  vx_b=firstv+i, front=firsts+i, flags=1)
                                  
            new_lines.append(new_linedef)
            
        #find overlapping lines and split them
        
        def split_linedef(l,v):
            #if (self.check_vertex_on_linedef(l,self.vertexes[v])):
            nl = copy(l)
            l.vx_b = v
            nl.vx_a = v
            new_lines.append(nl)

        got_one = True
        
        while(got_one == True):
            got_one = False
            for l1 in self.linedefs:
                for l2 in new_lines:
                    if (self.check_vertex_on_linedef(l2,self.vertexes[l1.vx_a])):
                        split_linedef(l2,l1.vx_a)
                        got_one = True
                    if (self.check_vertex_on_linedef(l2,self.vertexes[l1.vx_b])):
                        split_linedef(l2,l1.vx_b)
                        got_one = True
                    if (self.check_vertex_on_linedef(l1,self.vertexes[l2.vx_a])):
                        split_linedef(l1,l2.vx_a)
                        got_one = True
                    if (self.check_vertex_on_linedef(l1,self.vertexes[l2.vx_b])):
                        split_linedef(l1,l2.vx_b)
                        got_one = True
                
        
        for l1 in new_lines:
            match_existing = False
            for l2 in self.linedefs:
                if (self.compare_linedefs(l1,l2) > 0):
                    #remove midtexture and apply it to the 
                    #upper/lower texture
                    front = self.sidedefs[l1.front]
                    back = self.sidedefs[l2.front]
                    front.tx_low = back.tx_mid
                    front.tx_up = back.tx_mid
                    back.tx_low = front.tx_mid
                    back.tx_up = front.tx_mid
                    front.tx_mid = "-"
                    back.tx_mid = "-"
                    l2.back = self.sidedefs.index(front)
                    l2.two_sided = True
                    l2.impassable = False
                    l2.invisible = True
                    match_existing = True
                    break
            if (match_existing == False):
                self.linedefs.append(l1)

    def line_angle(self,line):
        v1 = self.vertexes[line.vx_a]
        v2 = self.vertexes[line.vx_b]
        return math.atan2(v2.x-v1.x,v2.y-v1.y)
    
    def check_vertex_on_linedef(self,line,vertex):
        """Checks if a vertex is on a linedef
        
        Does NOT return true if the vertex is equal to the ends."""
        
        a = self.vertexes[line.vx_a]
        b = self.vertexes[line.vx_b]
        c = vertex
        
        if (self.compare_vertex_positions(a,b)): return False
        if (self.compare_vertex_positions(a,c)): return False
        if (self.compare_vertex_positions(b,c)): return False
        
        output = self.vertex_distance(a,c) + self.vertex_distance(c,b) == self.vertex_distance(a,b)
        
        return output
    
    def vertex_distance(self,i,j):
        return math.sqrt((i.x - j.x)**2 + (i.y - j.y)**2)
    
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
        Returns 4 when the linedefs use the exact same vertices."""
        
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
        """Compare two sectors' data and returns True when they match.
        """
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
                        if (lc.back != -1):
                            if (self.sectors[self.sidedefs[lc.front].sector] == sector1 and 
                                self.sectors[self.sidedefs[lc.back].sector] == sector1):
                                self.linedefs.remove(lc)
        # we can rely on a nodebuilder to remove unused sectors for now
        # TODO: not rely on a nodebuilder :)
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

