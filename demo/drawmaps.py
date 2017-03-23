from __future__ import print_function
from omg import *
import sys
from PIL import Image, ImageDraw

def drawmap(wad, name, filename, width, format):
    xsize = width - 8

    edit = MapEditor(wad.maps[name])
    xmin = ymin = 32767
    xmax = ymax = -32768
    for v in edit.vertexes:
        xmin = min(xmin, v.x)
        xmax = max(xmax, v.x)
        ymin = min(ymin, -v.y)
        ymax = max(ymax, -v.y)

    scale = xsize / float(xmax - xmin)
    xmax = int(xmax * scale)
    xmin = int(xmin * scale)
    ymax = int(ymax * scale)
    ymin = int(ymin * scale)

    for v in edit.vertexes:
        v.x = v.x * scale
        v.y = -v.y * scale

    im = Image.new('RGB', ((xmax - xmin) + 8, (ymax - ymin) + 8), (255,255,255))
    draw = ImageDraw.Draw(im)

    edit.linedefs.sort(key=lambda a: not a.two_sided)

    for line in edit.linedefs:
         p1x = edit.vertexes[line.vx_a].x - xmin + 4
         p1y = edit.vertexes[line.vx_a].y - ymin + 4
         p2x = edit.vertexes[line.vx_b].x - xmin + 4
         p2y = edit.vertexes[line.vx_b].y - ymin + 4

         color = (0, 0, 0)
         if line.two_sided:
             color = (144, 144, 144)
         if line.action:
             color = (220, 130, 50)

         draw.line((p1x, p1y, p2x, p2y), fill=color)
         draw.line((p1x+1, p1y, p2x+1, p2y), fill=color)
         draw.line((p1x-1, p1y, p2x-1, p2y), fill=color)
         draw.line((p1x, p1y+1, p2x, p2y+1), fill=color)
         draw.line((p1x, p1y-1, p2x, p2y-1), fill=color)

    del draw

    im.save(filename, format)


#import psyco
#psyco.full()

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
    for name in inwad.maps.find(sys.argv[2]):
        print("Drawing %s" % name)
        drawmap(inwad, name, name + "_map" + "." + format.lower(), width, format)
