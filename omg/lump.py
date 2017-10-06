# Import the Python Imaging Library if it is available. On error, ignore
# the problem and continue. PIL being absent should only affect the
# graphic lump loading/saving methods and the user may not be interested
# in installing PIL just to pass this line if not interested in using the
# graphics functionality at all.
try:
    from PIL import Image, ImageDraw, ImageOps
except:
    pass

import os
import omg.palette
from omg.util import *
from omg      import six

class Lump(object):
    """Basic lump class. Instances of Lump (and its subclasses)
    always have the following:

        .data       -- a bytes object holding the lump's data
        .from_file  -- load the data to a file
        .to_file    -- save the data to a file

    The default Lump class merely copies the raw data when
    loading/saving to files, but subclasses may convert data
    appropriately (for example, Graphic supports various image
    formats)."""

    def __init__(self, data=None, from_file=None):
        """Create a new instance. The `data` parameter may be a string
        representing data for the lump. The `source` parameter may be
        a path to a file or a file-like object to load from."""
        self.data = bytes()
        if issubclass(type(data), Lump):
            self.data = data.data
        elif data is not None:
            self.data = data or bytes()
        if from_file:
            self.from_file(from_file)

    def from_file(self, source):
        """Load data from a file. Source may be a path name string
        or a file-like object (with a `write` method)."""
        self.data = readfile(source)

    def to_file(self, target):
        """Write data to a file. Target may be a path name string
        or a file-like object (with a `write` method)."""
        writefile(target, self.data)

    def copy(self):
        return deepcopy(self)


class Music(Lump):
    """Subclass of Lump, for music lumps. Not yet implemented."""
    pass


class Sound(Lump):
    """Subclass of Lump, for sound lumps. Not yet implemented."""
    pass


class Graphic(Lump):
    """Subclass of Lump, for Doom format graphics. Supports
    conversion from/to RAWs (sequences of bytes) and PIL
    Image objects, as well as saving to/loading from various
    file formats (via PIL).

    Useful attributes:
        .dimensions     -- (width, height)
        .width          -- width of the image
        .height         -- height of the image
        .x_offset       -- x offset
        .y_offset       -- y offset
    """

    def __init__(self, data=None, from_file=None, palette=None):
        self.palette = palette or omg.palette.default
        Lump.__init__(self, data, from_file)

    def get_offsets(self):
        """Retrieve the (x, y) offsets of the graphic."""
        return unpack('<hh', self.data[4:8])

    def set_offsets(self, xy):
        """Set the (x, y) offsets of the graphic."""
        self.data = self.data[0:4] + pack('<hh', *xy) + self.data[8:]

    def get_dimensions(self):
        """Retrieve the (width, height) dimensions of the graphic."""
        return unpack('<hh', self.data[0:4])

    offsets = property(get_offsets, set_offsets)
    x_offset = property(lambda self: self.offsets[0],
        lambda self, x: self.set_offsets((x, self.y_offset)))
    y_offset = property(lambda self: self.offsets[1],
        lambda self, y: self.set_offsets((self.x_offset, y)))

    dimensions = property(get_dimensions)
    width  = property(lambda self: self.dimensions[0])
    height = property(lambda self: self.dimensions[1])

    def from_pixels(self, data, width, height, x_offset=0, y_offset=0):
        """Load a list of 8bpp pixels.
        Pixels with a negative value are transparent."""
        # First pass: extract pixel data in column+post format
        columns_in = [data[n:width*height:width] for n in range(width)]
        columns_out = []
        for column in columns_in:
            # Find the y position where each chunk starts
            start_rows = []
            postdata = []
            in_trans = True
            tall = False
            offset = 0
            for y in range(height):
                # split at 128 for vanilla-compatible images without premature tiling
                if height < 256: 
                    if y == 128:
                        in_trans = True
            
                # for tall patch support
                elif offset == 254:
                    in_trans = True
                    tall = True
                    # dummy post
                    start_rows.append(254)
                    postdata.append(bytearray())
                    # start relative offsets
                    offset = 0
            
                if column[y] is None:
                    in_trans = True
                else:
                    if in_trans:
                        # start a new post
                        start_rows.append(offset)
                        postdata.append(bytearray())
                        in_trans = False
                        if tall:
                            # reset relative offset for tall patches
                            offset = 0
                    postdata[-1].append(column[y])
                
                offset += 1
            columns_out.append(zip(start_rows, postdata))
        # Second pass: compile column+post data, adding pointers
        data = []
        columnptrs = []
        pointer = 4*width + 8
        for column in columns_out:
            columnptrs.append(pack('<i', pointer))
            for row, pixels in column:
                data.append(b"%c%c\x00%s\x00" % (row, len(pixels), pixels))
                pointer += 4 + len(pixels)
            data.append(b'\xff')
            pointer += 1
        # Merge everything together
        self.data = bytes().join([pack('4h', width, height, x_offset, y_offset),
                    bytes().join(columnptrs), bytes().join(data)])

    def from_raw(self, data, width, height, x_offset=0, y_offset=0, pal=None):
        """Load a raw 8-bpp image, converting to the Doom picture format
        (used by all graphics except flats)"""
        pal = pal or omg.palette.default
        pixels = [i if i != pal.tran_index else None for i in six.iterbytes(data)]
        self.from_pixels(pixels, width, height, x_offset, y_offset)

    def to_pixels(self):
        """Returns self converted to a list of 8bpp pixels.
        Pixels with value None are transparent."""
        data = self.data
        width, height = self.dimensions
        output = [None] * (width*height)
        pointers = unpack('<%il'%width, data[8 : 8 + width*4])
        for x in range(width):
            y = -1
            pointer = pointers[x]
            if pointer >= len(data):
                continue

            while six.indexbytes(data, pointer) != 0xff:
                offset = six.indexbytes(data, pointer)
                if offset <= y:
                    y += offset # for tall patches
                else:
                    y = offset				
                post_length = six.indexbytes(data, pointer+1)
                op = y*width + x
                for p in range(pointer + 3, pointer + post_length + 3):
                    if op >= len(output) or p >= len(data):
                        break
                    output[op] = six.indexbytes(data, p)
                    op += width
                pointer += post_length + 4
        return output
        
    def to_raw(self, tran_index=None):
        """Returns self converted to a raw (8-bpp) image.

        `tran_index` specifies the palette index to use for
        transparent pixels. The value defaults to that of the
        Graphic object's palette instance."""
        tran_index = tran_index or self.palette.tran_index
        output = [i or tran_index for i in self.to_pixels()]
        return bytes(bytearray(output))

    def to_Image(self, mode='P'):
        """Convert to a PIL Image instance"""
        if mode != 'RGBA' or isinstance(self, Flat):
            # target image has no alpha, 
            # or source image is a flat (which has no transparent pixels)
            im = Image.new('P', self.dimensions, None)
            if isinstance(self, Flat):
                im.frombytes(self.data)
            else:
                im.frombytes(self.to_raw())
            im.putpalette(self.palette.save_bytes)
            return im.convert(mode)
        else:
            # target image is RGBA and source image is not a flat
            im = Image.new('RGBA', self.dimensions, None)
            data = bytes().join([self.palette.bytes[i*3:i*3+3] + b'\xff' if i is not None \
                                 else b'\0\0\0\0' for i in self.to_pixels()])
            im.frombytes(data)
            return im

    def from_Image(self, im, translate=False):
        """Load from a PIL Image instance

        If the input image is 24-bit or 32-bit, the colors will be
        looked up in the current palette.

        If the input image is 8-bit, indices will simply be copied
        from the input image. To properly translate colors between
        palettes, set the `translate` parameter."""

        pixels = im.tobytes()
        width, height = im.size
        xoff, yoff = (width // 2)-1, height-5
        if im.mode == "RGB":
            pixels = join([chr(self.palette.match(unpack('BBB', \
                pixels[i*3:(i+1)*3]))) for i in range(width*height)])

            self.from_raw(pixels, width, height, xoff, yoff, self.palette)
        
        elif im.mode == "RGBA":
            pixels = [unpack('BBBB', pixels[i*4:(i+1)*4]) for i in range(width*height)]
            pixels = [self.palette.match(i[0:3]) if i[3] > 0 else None for i in pixels]
            
            self.from_pixels(pixels, width, height, xoff, yoff)
    
        elif im.mode == 'P':
            srcpal = im.palette.tobytes()
            if im.palette.mode == "RGB":
                palsize = 3
            elif im.palette.mode == "RGBA":
                palsize = 4
            else:
                raise TypeError("palette mode must be 'RGB' or 'RGBA'")
            
            if translate:
                R = [c for c in six.iterbytes(srcpal[0::palsize])]
                G = [c for c in six.iterbytes(srcpal[1::palsize])]
                B = [c for c in six.iterbytes(srcpal[2::palsize])]

                srcpal = zip(R, G, B)
                lexicon = [six.int2byte(self.palette.match(c)) for c in srcpal]
                pixels = join([lexicon[b] for b in six.iterbytes(pixels)])
            else:
                # Simply copy pixels. However, make sure to translate
                # all colors matching the transparency color to the
                # right index. This is necessary because programs
                # aren't consistent in choice of position for the
                # transparent entry.
                packed_color = pack("BBB", *self.palette.tran_color)
                ri = 0
                while ri != -1:
                    ri = srcpal.find(packed_color, ri+palsize)
                    if not ri % palsize and ri//palsize != self.palette.tran_index:
                        pixels = pixels.replace(six.int2byte(ri//palsize),
                            six.int2byte(self.palette.tran_index))

            self.from_raw(pixels, width, height, xoff, yoff, self.palette)
        else:
            raise TypeError("image mode must be 'P', 'RGB', or 'RGBA'")

    def from_file(self, filename, translate=False):
        """Load graphic from an image file."""
        if filename[-4:].lower() == '.lmp':
            self.data = readfile(filename)
        else:
            im = Image.open(filename)
            self.from_Image(im, translate)

    def to_file(self, filename, mode='P'):
        """Save the graphic to an image file.

        The output format is selected based on the filename extension.
        For example, "file.jpg" saves to JPEG format. If the file has
        no extension, PNG format is used.

        Special cases: ".lmp" saves the raw lump data, and ".raw" saves
        the raw pixel data.

        `mode` may be be 'P', 'RGB', or 'RGBA' for palette or 24/32 bit
        output, respectively. However, .raw ignores this parameter and
        always writes in palette mode."""

        format = os.path.splitext(filename)[1][1:].upper()
        if   format == 'LMP': writefile(filename, self.data)
        elif format == 'RAW': writefile(filename, self.to_raw())
        else:
            im = self.to_Image(mode)
            if format:
                im.save(filename)
            else:
                im.save(filename, "PNG")

    def translate(self, pal):
        """Translate (in-place) the graphic to another palette."""
        lexicon = [chr(pal.match(self.palette.colors[i])) for i in range(256)]
        lexicon[self.palette.tran_index] = chr(pal.tran_index)
        if isinstance(self, Flat):
            self.data = join([lexicon[b] for b in self.data])
        else:
            raw = self.to_raw()
            #raw = raw.replace(chr(self.palette.tran_index), chr(pal.tran_index))
            self.load_raw(join([lexicon[b] for b in raw]),
                self.width, self.height,
                self.x_offset, self.y_offset)


class Flat(Graphic):
    """Subclass of Graphic, for flat graphics"""

    def get_dimensions(self):
        sz = len(self.data)
        if sz == 4096: return (64, 64)
        if sz == 4160: return (64, 65)
        root = int(sz**0.5)
        if root**2 != sz:
            raise TypeError("unable to determine size: not a square number")
        return (root, root)

    dimensions = property(get_dimensions)
    width  = property(lambda self: self.dimensions[0])
    height = property(lambda self: self.dimensions[1])

    def load_raw(self, data, *unused):
        self.data = data

    def to_raw(self):
        return self.data
