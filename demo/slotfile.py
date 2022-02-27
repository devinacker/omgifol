#!/usr/bin/python3
# set WAD's map slot from filename, by Frans P. de Vries (Xymph)

import sys, re
from omg import *

if len(sys.argv) < 2:
    print("\n    Omgifol script: set slot from filename\n")
    print("    Usage:")
    print("    slotfile.py slot##.wad [-s oldslot]\n")
else:

    # compile new slot & old pattern
    newslot = sys.argv[1]
    newslot = os.path.basename(newslot[:newslot.rfind('.')]).upper()
    if "-s" in sys.argv:
        oldslot = sys.argv[-1]
    else:
        oldslot = re.sub(r'\d+$', '', newslot) + '*'

    # load WAD & rename slot
    print("Loading %s..." % sys.argv[1])
    wadio = WadIO(sys.argv[1])
    entry = wadio.find(oldslot)
    if entry is not None:
        wadio.rename(entry, newslot)
        print("Writing %s..." % sys.argv[1])
        wadio.save()
    else:
        print("Not found: %s" % oldslot)
