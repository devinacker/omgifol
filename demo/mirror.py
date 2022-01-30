#!/usr/bin/env python

from sys import argv
from omg import *
from omg.mapedit import *

def mirror(map):
    ed = MapEditor(map)
    for v in ed.vertexes:
        v.x = -v.x
    for l in ed.linedefs:
        l.vx_a, l.vx_b = l.vx_b, l.vx_a
    for t in ed.things:
        t.x = -t.x
        t.angle = (180 - t.angle) % 360
    ed.nodes = []
    return ed.to_lumps()

def main(args):
    if (len(args) < 2):
        print("    Omgifol script: mirror maps\n")
        print("    Usage:")
        print("    mirror.py input.wad output.wad [pattern]\n")
        print("    Mirror all maps or those whose name match the given pattern")
        print("    (eg E?M4 or MAP*).")
        print("    Note: nodes will have to be rebuilt externally.\n")
    else:
        print("Loading %s..." % args[0])
        inwad = WAD()
        outwad = WAD()
        inwad.from_file(args[0])
        pattern = "*"
        if (len(args) == 3):
            pattern = args[2]
        for name in inwad.maps.find(pattern):
            print("Mirroring %s" % name)
            outwad.maps[name] = mirror(inwad.maps[name])
        print("Saving %s..." % args[1])
        outwad.to_file(args[1])

if __name__ == "__main__": main(argv[1:])
