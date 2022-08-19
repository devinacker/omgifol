#!/usr/bin/env python

from omg import *
import sys
from PIL import Image, ImageDraw

def drawmap(wad, name, filename, width, format):
    xsize = width - 8

    try:
        edit = UMapEditor(wad.udmfmaps[name])
    except KeyError:
        edit = UMapEditor(wad.maps[name])

    xmin = ymin = float('inf')
    xmax = ymax = float('-inf')
    for v in edit.vertexes:
        xmin = min(xmin, v.x)
        xmax = max(xmax, v.x)
        ymin = min(ymin, -v.y)
        ymax = max(ymax, -v.y)

    scale = xsize / float(xmax - xmin)
    xmax = xmax * scale
    xmin = xmin * scale
    ymax = ymax * scale
    ymin = ymin * scale

    for v in edit.vertexes:
        v.x = v.x * scale
        v.y = -v.y * scale

    im = Image.new('RGB', (int(xmax - xmin) + 8, int(ymax - ymin) + 8), (255,255,255))
    draw = ImageDraw.Draw(im)

    edit.linedefs.sort(key=lambda a: not a.twosided)

    for line in edit.linedefs:
         p1x = edit.vertexes[line.v1].x - xmin + 4
         p1y = edit.vertexes[line.v1].y - ymin + 4
         p2x = edit.vertexes[line.v2].x - xmin + 4
         p2y = edit.vertexes[line.v2].y - ymin + 4

         color = (0, 0, 0)
         if line.twosided:
             color = (144, 144, 144)
         if line.special:
             color = (220, 130, 50)

         draw.line((p1x, p1y, p2x, p2y), fill=color)
         draw.line((p1x+1, p1y, p2x+1, p2y), fill=color)
         draw.line((p1x-1, p1y, p2x-1, p2y), fill=color)
         draw.line((p1x, p1y+1, p2x, p2y+1), fill=color)
         draw.line((p1x, p1y-1, p2x, p2y-1), fill=color)

    del draw

    im.save(filename, format)

if (len(sys.argv) < 5):
    print("\n    Omgifol script: draw maps to image files\n")
    print("    Usage:")
    print("    drawmaps.py source.wad pattern width format\n")
    print("    Draw all maps whose names match the given pattern (eg E?M4 or MAP*)")
    print("    to image files of a given format (PNG, BMP, etc). width specifies the")
    print("    desired width of the output images.")
else:

    print("Loading %s..." % sys.argv[1])
    inwad = WAD()
    inwad.from_file(sys.argv[1])
    width = int(sys.argv[3])
    format = sys.argv[4].upper()
    for name in inwad.maps.find(sys.argv[2]) + inwad.udmfmaps.find(sys.argv[2]):
        print("Drawing %s" % name)
        drawmap(inwad, name, name + "_map" + "." + format.lower(), width, format)
