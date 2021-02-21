#!/usr/bin/env python

__doc__ = """
Extracts textures and map geometry from a WAD file into an OBJ file,
MTL file and PNG files suitable for use in any 3D modeling program or
modern game engine.
"""

# python
import math, argparse, os, sys

# PIL
from PIL import Image

# local
from omg import txdef, wad, mapedit, util

# Constants
DEFAULT_MTL_TEXT = """Ka 1.000000 1.000000 1.000000
Kd 1.000000 1.000000 1.000000
Ks 0.000000 0.000000 0.000000
Tr 1.000000
illum 1
Ns 0.000000
"""

def linked_a_chain_from(chains, remaining_segments):
    for chain in chains:
        end = chain[-1]
        # compare the actual coordinates of the start of this segment (segment)
        # versus the end of the chain (end)
        for segment in (s for s in remaining_segments if s[1] == end[0]):
            # they match, so extend this chain
            chain.append(segment)
            remaining_segments.remove(segment)
            return True

    return False


class Polygon:
    """
    Not really a polygon. Actually a set of faces that share a texture.
    This is used for floor/ceilings of sectors, which may have disjoint
    polygons.  Also used for wall segments which are actually simple polygons.
    """

    def __init__(self, texture=None):
        self.vertices = []
        self.segments = []
        self.texture = texture
        self.faces = []
        self.textureCoords = []

    def getFaces(self):
        return self.faces

    def getTextureCoords(self):
        return self.textureCoords

    def addFace(self, face, textureCoords):
        self.faces.append(face)
        self.textureCoords.append(textureCoords)

    def addSegment(self, p1, p2, a, b):
        """
        Feed us one line segment at a time, then call combineSegments()
        """

        self.segments.append((p1,p2,a,b))

    def combineSegments(self):
        """
        Take all line segments we were given and try to combine them into faces.
        """

        remaining_segments = list(self.segments)
        if not remaining_segments:
            return []

        chains = []
        # @TODO: Why is count computed this way?
        max_count = len(remaining_segments) * 2
        count = 0
        while remaining_segments and count < max_count:
            if chains and linked_a_chain_from(chains, remaining_segments):
                count += 1
                continue

            chains.append([remaining_segments.pop()])

        # grab the vertex indicies for each chain (aka face)
        newFaces = [[segment[2] for segment in chain] for chain in chains]
        self.faces.extend(newFaces)

        # lets compute some textureCoords for these new faces
        # based on their vertex coords in world space.
        # this works well for floors and ceilings.
        # flats are always 64x64 aligned to world coords
        [self.textureCoords.append(
            [(segment[0].x/64., segment[0].y/64.) for segment in chain])
            for chain in chains]

def objmap(wad, name, filename, textureNames, textureSizes, centerVerts):
    edit = mapedit.MapEditor(wad.maps[name])

    # first lets get into the proper coordinate system
    v = edit.vertexes[0]
    bb_min = mapedit.Vertex(v.x,v.y)
    bb_max = mapedit.Vertex(v.x,v.y)
    for v in edit.vertexes:
        v.x = -v.x
        if bb_max.x > v.x: bb_max.x = v.x
        if bb_max.y > v.y: bb_max.y = v.y
        if bb_min.x < v.x: bb_min.x = v.x
        if bb_min.y < v.y: bb_min.y = v.y

    if centerVerts:
        center = mapedit.Vertex((bb_min.x+bb_max.x)/2, (bb_min.y+bb_max.y)/2)
    else:
        center = mapedit.Vertex(0,0)

    vi = 1  # vertex index (starting at 1 for the 1st vertex)
    vertexes = []
    polys = []

    _sectors_with_floor_and_ceil_added(edit.sectors)

    _polygons_with_line_definitions(edit, vi, vertexes, textureSizes, polys)

    for sector in edit.sectors:
        for poly in (sector.floor, sector.ceil):
            poly.combineSegments()
            polys.append(poly)

    ti = 1  # vertex texture index (starting at 1 for the 1st "vt" statement)

    with open(filename, "w") as out:
        out.write("# %s\n" % name)
        out.write("mtllib doom.mtl\n")
        out.write("o %s\n" % name)

        # here are all the vertices - in order, so you can index them (starting
        # at 1) note that we stretch them to compensate for Doom's non-square
        # pixel display
        for v in vertexes:
            out.write("v %g %g %g\n" % (v[0]-center.x, v[1]*1.2, v[2]-center.y))

        for polyindex, poly in enumerate(polys):
            if not poly.texture:
                print("Polygon with no texture?", poly)
                continue

            if poly.texture == '-' or poly.texture == 'F_SKY1':
                # this was not meant to be rendered
                continue

            # polyindex starts at 1, enumerate starts at 0
            out.write("g %s.%d %s\n" % (poly.texture, polyindex + 1, name))

            texture_name = poly.texture
            if poly.texture not in textureNames:
                print("Missing texture", poly.texture)
                texture_name = "None"
            out.write("usemtl %s\n" % texture_name)

            for vindexes,textureCoords in zip(
                    poly.getFaces(),
                    poly.getTextureCoords()):

                tindexes = []
                for u,v in textureCoords:
                    out.write("vt %g %g\n" % (u, v))
                    tindexes.append(ti)
                    ti += 1
                out.write(
                        "f %s\n" % " ".join([
                            "%s/%s" % (v,t) for v,t in zip(vindexes,tindexes)]))

def _polygons_with_line_definitions(edit, vi, vertexes, textureSizes, polys):
    for line in edit.linedefs:

        p1 = edit.vertexes[line.vx_a]
        p2 = edit.vertexes[line.vx_b]

        width = math.sqrt((p1.x-p2.x)*(p1.x-p2.x) + (p1.y-p2.y)*(p1.y-p2.y))

        if line.front != -1:
            side1 = edit.sidedefs[line.front]
            sector1 = edit.sectors[side1.sector]

            front_lower_left = vi
            front_upper_left = vi+1
            front_lower_right = vi+2
            front_upper_right = vi+3
            vertexes.append((p1.x, sector1.z_floor, p1.y)) # lower left
            vertexes.append((p1.x, sector1.z_ceil,  p1.y)) # upper left
            vertexes.append((p2.x, sector1.z_floor, p2.y)) # lower right
            vertexes.append((p2.x, sector1.z_ceil,  p2.y)) # upper right

            if not line.two_sided and side1.tx_mid!='-': #line.impassable:
                polys.append(_poly_from_components(
                        side1, sector1,
                        textureSizes, width, line,
                        front_lower_left, front_lower_right,
                        front_upper_right, front_upper_left))

            sector1.floor.addSegment(
                    p1, p2, front_lower_left, front_lower_right)
            sector1.ceil.addSegment(
                    p2, p1, front_upper_right, front_upper_left)

            vi += 4

        if line.back != -1:
            side2 = edit.sidedefs[line.back]
            sector2 = edit.sectors[side2.sector]

            back_lower_left = vi
            back_upper_left = vi+1
            back_lower_right = vi+2
            back_upper_right = vi+3
            vertexes.append((p1.x, sector2.z_floor, p1.y)) # lower left
            vertexes.append((p1.x, sector2.z_ceil,  p1.y)) # upper left
            vertexes.append((p2.x, sector2.z_floor, p2.y)) # lower right
            vertexes.append((p2.x, sector2.z_ceil,  p2.y)) # upper right

            if not line.two_sided and side2.tx_mid!='-': #line.impassable:
                polys.append(_poly_from_components(
                        side2, sector2,
                        textureSizes, width, line,
                        back_lower_left,back_lower_right,
                        back_upper_right,back_upper_left))

            sector2.floor.addSegment(p2, p1, back_lower_right, back_lower_left)
            sector2.ceil.addSegment(p1, p2, back_upper_left, back_upper_right)

            vi += 4

        if line.front != -1 and line.back != -1 and line.two_sided:
            # skip the lower texture if it is '-'
            if side1.tx_low != '-':
                # floor1 to floor2
                poly = Polygon(side1.tx_low)
                # the front (sector1) is lower than the back (sector2)
                height = sector2.z_floor - sector1.z_floor
                tsize = textureSizes.get(side1.tx_low, (64,64))
                tw = width/float(tsize[0])
                th = height/float(tsize[1])
                tx = side1.off_x/float(tsize[0])
                if line.lower_unpeg:
                    ty = (tsize[1]-height-side1.off_y)/float(tsize[1])
                else:
                    ty = -side1.off_y/float(tsize[1])
                poly.addFace(
                        (front_lower_left,front_lower_right,
                            back_lower_right,back_lower_left),
                        [(tx,ty),(tw+tx,ty),(tw+tx,th+ty),(tx,th+ty)])
                polys.append(poly)

            # skip the upper texture if it is '-'
            # also skip the upper if the sectors on both sides have sky ceilings
            if (
                    side1.tx_up != '-'
                    and not (
                        sector1.tx_ceil == 'F_SKY1'
                        and sector2.tx_ceil == 'F_SKY1')):

                # ceil1 to ceil2
                poly = Polygon(side1.tx_up)
                # the front (sector1) is higher than the back (sector2)
                height = sector1.z_ceil - sector2.z_ceil
                tsize = textureSizes[side1.tx_up]
                tw = width/float(tsize[0])
                th = height/float(tsize[1])
                tx = side1.off_x/float(tsize[0])
                if line.upper_unpeg:
                    ty = (tsize[1]-height-side1.off_y)/float(tsize[1])
                else:
                    ty = -side1.off_y/float(tsize[1])
                poly.addFace(
                        (back_upper_left,back_upper_right,
                            front_upper_right,front_upper_left), \
                             [(tx,ty),(tw+tx,ty),(tw+tx,th+ty),(tx,th+ty)])
                polys.append(poly)

def _poly_from_components(side1, sector1, textureSizes, width, line,
    lower_left, lower_right, upper_right, upper_left):
    poly = Polygon(side1.tx_mid)
    height = sector1.z_ceil - sector1.z_floor
    tsize = textureSizes.get(side1.tx_mid, (64,64))
    tw = width/float(tsize[0])
    th = height/float(tsize[1])
    tx = side1.off_x/float(tsize[0])
    if line.lower_unpeg: # yes, lower_unpeg applies to the tx_mid also
        ty = -side1.off_y/float(tsize[1])
    else:
        # middle texture is usually top down
        ty = (tsize[1]-height-side1.off_y)/float(tsize[1])
    poly.addFace(
            (lower_left, lower_right, upper_right, upper_left),
            [(tx,ty),(tw+tx,ty),(tw+tx,th+ty),(tx,th+ty)])

    return poly

def _sectors_with_floor_and_ceil_added(sectors):
    for sector in sectors:
        sector.floor = Polygon(texture=sector.tx_floor)
        sector.ceil = Polygon(texture=sector.tx_ceil)

def writemtl(wad):
    out = open("doom.mtl", "w")
    out.write("# doom.mtl\n")

    names = []
    textureSizes = {}

    # + wad.patches.items() # + wad.graphics.items() + wad.sprites.items()
    textures = list(wad.flats.items())

    for name,texture in textures:
        texture.to_file(name+".png")
        _texture_written_to(out, name)
        names.append(name)

    t = txdef.Textures(wad.txdefs)
    for name,texture_definition in list(t.items()):
        image = Image.new(
                'RGB',
                (texture_definition.width, texture_definition.height))
        # print "making %s at %dx%d" % (name, txdef.width, txdef.height)
        for patchdef in texture_definition.patches:
            # sometimes there are lower case letters!?
            patchdef.name = patchdef.name.upper()
            if patchdef.name not in wad.patches:
                print(("ERROR: Cannot find patch named '%s' for "
                        "texture_definition '%s'" % (patchdef.name, name)))
                continue
            patch = wad.patches[patchdef.name]
            stamp = patch.to_Image()
            image.paste(stamp, (patchdef.x,patchdef.y))
        image.save(name+".png")
        textureSizes[name] = image.size

        _texture_written_to(out, name)
        names.append(name)

    return names, textureSizes

def _texture_written_to(out, name):
    out.write("\nnewmtl %s\n" % name)
    out.write(DEFAULT_MTL_TEXT)
    out.write("map_Kd %s.png\n" % name)

def parse_args():
    """ parse arguments out of sys.argv """

    epilog = "Example: wad2obj.py doom.wad -m 'E1*' -o /tmp"

    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog)
    parser.add_argument(
            'source_wad', type=str, help='Path to the input WAD file.')
    parser.add_argument(
            '-l','--list', action='store_true', default=False,
            help="List the names of the maps in the source wad without exporting anything.")
    parser.add_argument(
            '-m','--maps', type=str, default='*', metavar='PATTERN',
            help="Pattern of maps to export (e.g. 'MAP*' or 'E?M1'). Use * as a wildcard or ? as any single character.")
    parser.add_argument(
            '-o','--output', type=str, default='.', metavar='PATH',
            help="Directory path where output files will be written.")
    parser.add_argument(
            '-c','--center', action='store_true', default=False,
            help="Translate the output vertices so the center of the map is at the origin.")
    return parser.parse_args()

def main():
    args = parse_args()

    print("Loading %s..." % args.source_wad)
    inwad = wad.WAD()
    inwad.from_file(args.source_wad)

    if args.list:
        print("Found %d maps:" % len(inwad.maps))
        for mapName in list(inwad.maps.keys()):
            print("  %s" % mapName)
        sys.exit(0)

    # lets make sure all output files are written here
    os.chdir(args.output)

    # export the textures first, so we know all their sizes
    textureNames, textureSizes = writemtl(inwad)

    maps = util.find(inwad.maps, args.maps)
    if len(maps) == 0:
        print("No maps matching pattern '%s' were found." % (args.maps))
    else:
        print("Found %d maps matching pattern '%s'" % (len(maps), args.maps))
        for name in maps:
            objfile = name+".obj"
            print("Writing %s" % objfile)
            objmap(inwad, name, objfile, textureNames, textureSizes, args.center)

"""
Sample code for debugging...
from omg import wad, txdef, mapedit
w = wad.WAD('doom.wad')
t = txdef.Textures(w.txdefs)
flat = w.flats['FLOOR0_1']
map = w.maps['E1M1']
edit = mapedit.MapEditor(map)
"""

if __name__ == "__main__":
    main()

