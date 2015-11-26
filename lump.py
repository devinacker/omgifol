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


class Lump(object):
    """Basic lump class. Instances of Lump (and its subclasses)
    always have the following:

        .data       -- a string holding the lump's data
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
        self.data = ""
        if issubclass(type(data), Lump):
            self.data = data.data
        elif data is not None:
            self.data = data or ""
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
        return unpack('hh', self.data[4:8])

    def set_offsets(self, xy):
        """Set the (x, y) offsets of the graphic."""
        self.data = self.data[0:4] + pack('hh', *xy) + self.data[8:]

    def get_dimensions(self):
        """Retrieve the (width, height) dimensions of the graphic."""
        return unpack('hh', self.data[0:4])

    offsets = property(get_offsets, set_offsets)
    x_offset = property(lambda self: self.offsets[0],
        lambda self, x: self.set_offsets((x, self.y_offset)))
    y_offset = property(lambda self: self.offsets[1],
        lambda self, y: self.set_offsets((self.x_offset, y)))

    dimensions = property(get_dimensions)
    width  = property(lambda self: self.dimensions[0])
    height = property(lambda self: self.dimensions[1])

    def from_raw(self, data, width, height, x_offset=0, y_offset=0, pal=None):
        """Load a raw 8-bpp image, converting to the Doom picture format
        (used by all graphics except flats)"""
        pal = pal or omg.palette.default
        trans = chr(pal.tran_index)
        # First pass: extract pixel data in column+post format
        columns_in = [data[n:width*height:width] for n in range(width)]
        columns_out = []
        for column in columns_in:
            # Split into chunks of continuous non-transparent pixels
            postdata = filter(None, column.split(trans))
            # Find the y position where each chunk starts
            start_rows = []
            in_trans = True
            for y in range(height):
                if column[y] == trans:
                    in_trans = True
                elif in_trans:
                    start_rows.append(y)
                    in_trans = False
            columns_out.append(zip(start_rows, postdata))
        # Second pass: compile column+post data, adding pointers
        data = []
        columnptrs = []
        pointer = 4*width + 8
        for column in columns_out:
            columnptrs.append(pack('l', pointer))
            for row, pixels in column:
                data.append("%c%c\x00%s\x00" % (row, len(pixels), pixels))
                pointer += 4 + len(pixels)
            data.append('\xff')
            pointer += 1
        # Merge everything together
        self.data = ''.join([pack('4h', width, height, x_offset, y_offset),
                    ''.join(columnptrs), ''.join(data)])

    def to_raw(self, tran_index=None):
        """Returns self converted to a raw (8-bpp) image.

        `tran_index` specifies the palette index to use for
        transparent pixels. The value defaults to that of the
        Graphic object's palette instance."""
        data = self.data
        width, height = self.dimensions
        tran_index = tran_index or self.palette.tran_index
        output = [chr(tran_index)] * (width*height)
        pointers = unpack('%il'%width, data[8 : 8 + width*4])
        for x in xrange(width):
            pointer = pointers[x]
            while data[pointer] != '\xff':
                post_length = ord(data[pointer+1])
                op = ord(data[pointer])*width + x
                for p in range(pointer + 3, pointer + post_length + 3):
                    output[op] = data[p]
                    op += width
                pointer += post_length + 4
        return join(output)

    def to_Image(self):
        """Convert to a PIL Image instance"""
        im = Image.new('P', self.dimensions, None)
        if isinstance(self, Flat):
            im.fromstring(self.data)
        else:
            im.fromstring(self.to_raw())
        im.putpalette(self.palette.save_bytes)
        return im

    def from_Image(self, im, translate=False):
        """Load from a PIL Image instance

        If the input image is 24-bit, the colors will be looked up
        in the current palette.

        If the input image is 8-bit, indices will simply be copied
        from the input image. To properly translate colors between
        palettes, set the `translate` parameter."""

        pixels = im.tostring()
        width, height = im.size
        # High resolution graphics not supported yet, so truncate
        height = min(254, height)
        xoff, yoff = (width // 2)-1, height-5
        if im.mode == "RGB":
            pixels = join([chr(self.palette.match(unpack('BBB', \
                pixels[i*3:(i+1)*3]))) for i in range(width*height)])
        elif im.mode == 'P':
            srcpal = im.palette.tostring()
            if translate:
                R = [ord(c) for c in srcpal[0::3]]
                G = [ord(c) for c in srcpal[1::3]]
                B = [ord(c) for c in srcpal[2::3]]
                # Work around PIL bug: "RGB" loads as "BGR" from bmps (?)
                if filename[-4:].lower() == '.bmp':
                    srcpal = zip(B, G, R)
                else:
                    srcpal = zip(R, G, B)
                lexicon = [chr(self.palette.match(c)) for c in srcpal]
                pixels = join([lexicon[ord(b)] for b in pixels])
            else:
                # Simply copy pixels. However, make sure to translate
                # all colors matching the transparency color to the
                # right index. This is necessary because programs
                # aren't consistent in choice of position for the
                # transparent entry.
                packed_color = pack("BBB", *pal.tran_color)
                ri = 0
                while ri != -1:
                    ri = srcpal.find(packed_color, ri+3)
                    if not ri % 3 and ri//3 != self.palette.tran_index:
                        pixels = pixels.replace(chr(ri//3),
                            chr(self.palette.tran_index))
        else:
            raise TypeError, "image mode must be 'P' or 'RGB'"

        self.from_raw(pixels, width, height, xoff, yoff, self.palette)

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

        `mode` may be be 'P' or 'RGB' for palette or 24 bit output,
        respectively. However, .raw ignores this parameter and always
        writes in palette mode."""

        format = os.path.splitext(filename)[1:].upper()
        if   format == 'LMP': writefile(filename, self.data)
        elif format == 'RAW': writefile(filename, self.to_raw())
        else:
            im = self.to_Image()
            om = im.convert(mode)
            if format:
                om.save(filename)
            else:
                om.save(filename, "PNG")

    def translate(self, pal):
        """Translate (in-place) the graphic to another palette."""
        lexicon = [chr(pal.match(self.palette.colors[i])) for i in range(256)]
        lexicon[self.palette.tran_index] = chr(pal.tran_index)
        if isinstance(self, Flat):
            self.data = join([lexicon[ord(b)] for b in self.data])
        else:
            raw = self.to_raw()
            #raw = raw.replace(chr(self.palette.tran_index), chr(pal.tran_index))
            self.load_raw(join([lexicon[ord(b)] for b in raw]),
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
            raise TypeError, "unable to determine size: not a square number"
        return (root, root)

    dimensions = property(get_dimensions)
    width  = property(lambda self: self.dimensions[0])
    height = property(lambda self: self.dimensions[1])

    def load_raw(self, data, *unused):
        self.data = data

    def to_raw(self):
        return self.data
