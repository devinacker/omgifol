#!/usr/bin/python3
# list WAD directory with lump names/sizes or verbose info from Omgifol itself,
# by Frans P. de Vries (Xymph)

import sys, getopt
from omg import *

if len(sys.argv) < 2:
    print("\n    Omgifol script: list WAD directory\n")
    print("    Usage:")
    print("    listdir.py [-v] source.wad\n")
else:
    # process optional flag
    verbose = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'v')
        for o, a in opts:
            if o == '-v':
                verbose = True
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)

    # load WAD
    if os.path.exists(args[0]):
        wadio = WadIO(args[0])
        # comprehensive info or simple list?
        if verbose:
            print(wadio.info_text())
        else:
            for i, entry in enumerate(wadio.entries):
                print("%-8s  %9d" % (entry.name, entry.size))
    else:
        print("%s: no such file" % args[0])
