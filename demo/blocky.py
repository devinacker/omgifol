#!/usr/bin/python
# generates a PWAD with 256 64x64-sized flat color patches and textures named
# COLORXXX and 256 flats named FOLORXXX where XXX is a decimal index into the
# palette

from omg import *
from omg.txdef import *
import struct

iwad = WAD('doom2.wad')
out  = WAD()
editor = omg.txdef.Textures(iwad.txdefs)

for i in range(0,256):

    # generate raw patch data for palette index i
    topdelta = 0
    length = 128
    unused = 0
    data = i
    post = struct.pack('<BBB{}sB'.format(length), topdelta, length, unused, bytes([data])*length, unused)
    width = 64
    height = 128
    leftoffs = topoffs = 0
    postoffs = 264
    patch = struct.pack('<HHhh', width, height, leftoffs, topoffs) \
            + struct.pack('<L', postoffs) * 64 \
            + post
    gr = Graphic()
    gr.data = patch
    name = "COLOR{:03d}".format(i)
    out.patches[name] = gr

    # generate a texture entry
    editor.simple(name, out.patches[name])

    # generate a flat
    name = "FOLOR{:03d}".format(i)
    flat = Flat()
    flat.load_raw(bytes([i])*4096)
    out.flats[name] = flat

# fix flats in vanilla
out.flats.prefix='FF*_START'

out.txdefs = editor.to_lumps()
out.to_file('out.wad')
