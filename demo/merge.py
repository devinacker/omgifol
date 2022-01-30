#!/usr/bin/env python

import omg, sys

if (len(sys.argv) < 3):
    print("\n    Omgifol script: merge WADs\n")
    print("    Usage:")
    print("    merge.py input1.wad input2.wad ... [-o output.wad]\n")
    print("    Default output is merged.wad")
else:
    w = omg.WAD()
    for a in sys.argv[1:]:
        if a == "-o":
            break
        print("Adding %s..." % a)
        w += omg.WAD(a)
    outpath = "merged.wad"
    if "-o" in sys.argv: outpath = sys.argv[-1]
    w.to_file(outpath)
