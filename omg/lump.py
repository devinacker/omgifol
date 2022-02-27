# Import the Python Imaging Library if it is available. On error, ignore
# the problem and continue. PIL being absent should only affect the
# graphic lump loading/saving methods and the user may not be interested
# in installing PIL just to pass this line if not interested in using the
# graphics functionality at all.
try:
    from PIL import Image, ImageDraw, ImageOps
except:
    pass

# Import PySoundFile for sound file loading/saving. Equally optional.
try:
    from soundfile import SoundFile, check_format
    import numpy as np
except:
    pass

import os
import omg.palette
from omg.util import *

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
    """Subclass of Lump, for Doom format sounds. Supports
    conversion from/to RAWs (sequences of bytes), as well as
    saving to/loading from various file formats (via PySoundFile).

    Useful attributes:
        .format         -- DMX sound format
        .length         -- (in frames/samples)
        .sample_rate    --
        .midi_bank      -- MIDI patch bank (format 1/2 only)
        .midi_patch     -- MIDI patch number (format 1/2 only)

    Possible values for the 'format' attribute:

    0: PC speaker sound
       Raw data consists of values 0-127 corresponding to pitch.
       Sample rate is fixed at 140Hz.
    1: MIDI sound sequence
       Raw data consists of MIDI note and pitch bend info.
       Sample rate is fixed at 140Hz.
    2: MIDI note
       Raw data consists of a single MIDI note.
       Sample rate is undefined. Length is MIDI note length.
    3: Digitized sound (default)
       Raw data is 8-bit unsigned PCM.
       Sample rate defaults to 11025 Hz, but can be changed.

    Only format 3 can be exported to an audio file.
    """

    def __init__(self, data=None, from_file=None):
        Lump.__init__(self, data, from_file)
        # default to an empty digitized sound effect if no data loaded
        try:
            if self.format is None:
                self.format = 3
        except TypeError:
            pass

    def get_format(self):
        """Retrieve the format of the sound."""
        if len(self.data) < 2:
            format = None
        else:
            format = unpack('<H', self.data[0:2])[0]
        if format > 3:
            raise TypeError("Unknown or invalid sound format")
        return format

    def set_format(self, format):
        """Change the format of the sound.

        Warning: Changing a sound's format will erase any existing sound data!"""
        try:
            if format == self.format:
                return # don't do anything if format is the same as before
        except TypeError:
            pass

        if format == 0:
            # PC speaker sound
            self.data = pack('<HH', format, 0)
        elif format == 1:
            # MIDI sequence
            self.data = pack('<HHHH', format, 0, 0, 0)
        elif format == 2:
            # single MIDI note
            self.data = pack('<HHHHH', format, 0, 0, 0, 0)
        elif format == 3:
            # digitized sound
            self.data = pack("<HHI32x", format, 11025, 32)
        else:
            raise ValueError("Unknown or invalid sound format")

    format = property(get_format, set_format)

    def get_length(self):
        """Retrieve the length of the sound."""
        format = self.format
        if format == 0 or format == 1:
            # PC speaker or MIDI sequence
            return unpack('<H', self.data[2:4])[0]
        elif format == 2:
            # single MIDI note
            return unpack('<H', self.data[8:10])[0]
        elif format == 3:
            # digitized sound
            return unpack('<I', self.data[4:8])[0] - 32

    def set_length(self, length):
        """Set the length of the sound. This will make the lump larger or smaller."""
        format = self.format

        if length < 0 or length > 65535:
            raise ValueError("sound effect length must be between 0-65535")

        if format == 2:
            # single MIDI note
            self.data = self.data[:8] + pack('<H', length)
        else:
            # grow or shrink existing raw data to new size
            self.from_raw(self.to_raw()[0:length] + b'\0'*(length - self.length))

    length = property(get_length, set_length)

    def get_sample_rate(self):
        """Retrieve the sample rate of the sound. Only useful for digitized sounds."""
        format = self.format
        if format == 0 or format == 1:
            # PC speaker or MIDI sequence
            return 140
        elif format == 2:
            # single MIDI note
            return 0
        elif format == 3:
            # digitized sound
            return unpack('<H', self.data[2:4])[0]

    def set_sample_rate(self, sample_rate):
        """Set the sample rate of the sound. Only supported for digitized sounds."""
        format = self.format
        if format == 3:
            # digitized sound
            self.data = self.data[:2] + pack('<H', sample_rate) + self.data[4:]
        else:
            raise TypeError("set_sample_rate only supported for digitized sounds (format 3)")

    sample_rate = property(get_sample_rate, set_sample_rate)

    def get_midi_bank(self):
        """Retrieve the MIDI bank of the sound. Only useful for MIDI sounds."""
        format = self.format
        if format == 1:
            # MIDI sequence
            return unpack('<H', self.data[4:6])[0]
        elif format == 2:
            # single MIDI note
            return unpack('<H', self.data[2:4])[0]

    def set_midi_bank(self, bank):
        """Set the MIDI bank of the sound. Only supported for MIDI sounds."""
        format = self.format
        if format == 1:
            # MIDI sequence
            self.data = self.data[:4] + pack('<H', bank) + self.data[6:]
        elif format == 2:
            # single MIDI note
            self.data = self.data[:2] + pack('<H', bank) + self.data[4:]
        else:
            raise TypeError("only supported for MIDI sounds (format 1 or 2)")

    midi_bank = property(get_midi_bank, set_midi_bank)

    def get_midi_patch(self):
        """Retrieve the MIDI patch of the sound. Only useful for MIDI sounds."""
        format = self.format
        if format == 1:
            # MIDI sequence
            return unpack('<H', self.data[6:8])[0]
        elif format == 2:
            # single MIDI note
            return unpack('<H', self.data[4:6])[0]

    def set_midi_patch(self, patch):
        """Set the MIDI patch of the sound. Only supported for MIDI sounds."""
        format = self.format
        if format == 1:
            # MIDI sequence
            self.data = self.data[:6] + pack('<H', patch) + self.data[8:]
        elif format == 2:
            # single MIDI note
            self.data = self.data[:4] + pack('<H', patch) + self.data[6:]
        else:
            raise TypeError("only supported for MIDI sounds (format 1 or 2)")

    midi_patch = property(get_midi_patch, set_midi_patch)

    def from_raw(self, data, format=None, sample_rate=None):
        """Replaces the raw values making up the sound.

        If 'format' or 'sample_rate' are not specified, the existing values
        will be used.

        The expected values depend on the value of 'format'.
        For format 2, 'data' is expected to be an int.
        Otherwise it is expected to be a byte string.
        """
        if isinstance(data, bytes):
            length = len(data)
            if length < 0 or length > 65535:
                raise ValueError("sound effect length must be between 0-65535")

        # optionally change format if needed
        if format is None:
            format = self.format
        else:
            self.format = format

        if format == 0:
            # PC speaker sound
            self.data = self.data[:2] + pack('<H', len(data)) + data
        elif format == 1:
            # MIDI sequence
            self.data = self.data[:2] + pack('<H', len(data)) + self.data[4:8] + data
        elif format == 2:
            # single MIDI note
            self.data = self.data[:6] + pack('<H', data) + self.data[8:]
        elif format == 3:
            # digitized sound
            self.data = self.data[:4] + pack('<I', 32 + len(data)) \
                        + b'\0'*16 + data + b'\0'*16
            if sample_rate is not None:
                self.sample_rate = sample_rate
        else:
            raise ValueError("Unknown or invalid sound format")

    def to_raw(self):
        """Returns the raw values making up the sound as a byte string.

        The resulting values depend on the value of 'format'.
        For format 2, the value is returned an int.
        Otherwise the data is returned as a byte string.
        """
        format = self.format
        if format == 0:
            # PC speaker
            return self.data[4:]
        elif format == 1:
            # MIDI sequence
            return self.data[8:]
        elif format == 2:
            # single MIDI note
            return unpack('<H', self.data[6:8])[0]
        elif format == 3:
            # digitized sound
            return self.data[24:-16]

    def from_file(self, filename):
        """Load sound from an audio file."""
        if filename[-4:].lower() == '.lmp':
            self.data = readfile(filename)
        else:
            with SoundFile(filename) as file:
                # get sound data and convert to 8-bit unsigned mono
                sound = (file.read(dtype='int16') >> 8) + 128
                if file.channels > 1:
                    sound = np.mean(sound, axis=1)

                # create new format 3 sound
                self.from_raw(sound.astype('uint8').tobytes(), 3, file.samplerate)

    def to_file(self, filename, subtype='PCM_U8'):
        """Save the sound to an audio file.

        The output format is selected based on the filename extension.
        For example, "file.wav" saves to WAV format. If the file has
        no extension, WAV format is used.

        See the PySoundFile documentation for possible values of 'subtype'.
        Possible values depend on the output format; if the given value is
        not supported, the format's default will be used.

        Special cases: ".lmp" saves the raw lump data, and ".raw" saves
        the raw sound data.
        """
        format = os.path.splitext(filename)[1][1:].upper() or 'WAV'
        if   format == 'LMP': writefile(filename, self.data)
        elif format == 'RAW': writefile(filename, self.to_raw())
        elif self.format == 3:
            if   check_format(format, subtype):  pass
            elif check_format(format, 'PCM_U8'): subtype = 'PCM_U8'
            elif check_format(format, 'PCM_S8'): subtype = 'PCM_S8'
            else: subtype = None # use default for format

            with SoundFile(filename, 'w', self.sample_rate, 1, subtype, format=format) as file:
                # convert to signed 16-bit (since SoundFile doesn't directly support 8-bit input)
                # the result will just be converted back in the file though
                sound = (np.frombuffer(self.to_raw(), dtype='uint8').astype('int16') - 128) << 8
                file.write(sound)
        else:
            raise TypeError("audio file export only supported for digitized sounds (format 3)")


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
        self.data = self.data[:4] + pack('<hh', *xy) + self.data[8:]

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
        Pixels with value None are transparent."""
        if min(width, height) < 0 or max(width, height) > 32767:
            raise ValueError("image width and height must be between 0-32767")

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
        (used by all graphics except flats)."""
        pal = pal or omg.palette.default
        pixels = [i if i != pal.tran_index else None for i in data]
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

            while data[pointer] != 0xff:
                offset = data[pointer]
                if offset <= y:
                    y += offset # for tall patches
                else:
                    y = offset
                post_length = data[pointer + 1]
                op = y*width + x
                for p in range(pointer + 3, pointer + post_length + 3):
                    if op >= len(output) or p >= len(data):
                        break
                    output[op] = data[p]
                    op += width
                pointer += post_length + 4
        return output

    def to_raw(self, tran_index=None):
        """Returns self converted to a raw (8-bpp) image.

        `tran_index` specifies the palette index to use for
        transparent pixels. The value defaults to that of the
        Graphic object's palette instance.
        """
        tran_index = tran_index or self.palette.tran_index
        output = [i if i is not None else tran_index for i in self.to_pixels()]
        return bytes(bytearray(output))

    def to_Image(self, mode='P'):
        """Convert to a PIL Image instance."""
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
        """Load from a PIL Image instance.

        If the input image is 24-bit or 32-bit, the colors will be
        looked up in the current palette.

        If the input image is 8-bit, indices will simply be copied
        from the input image. To properly translate colors between
        palettes, set the `translate` parameter.
        """
        pixels = im.tobytes()
        width, height = im.size
        xoff, yoff = (width // 2)-1, height-5
        if im.mode == "RGB":
            pixels = bytes([self.palette.match(unpack('BBB', \
                pixels[i*3:(i+1)*3])) for i in range(width*height)])

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
                R = [c for c in srcpal[0::palsize]]
                G = [c for c in srcpal[1::palsize]]
                B = [c for c in srcpal[2::palsize]]

                srcpal = zip(R, G, B)
                lexicon = [self.palette.match(c) for c in srcpal]
                pixels = bytes([lexicon[b] for b in pixels])
            else:
                # Simply copy pixels. However, make sure to translate
                # all colors matching the transparency color to the
                # right index. This is necessary because programs
                # aren't consistent in choice of position for the
                # transparent entry.
                packed_color = pack("BBB", *self.palette.tran_color)
                packed_index = pack("B", self.palette.tran_index)
                ri = 0
                while ri != -1:
                    ri = srcpal.find(packed_color, ri+palsize)
                    if not ri % palsize and ri//palsize != self.palette.tran_index:
                        pixels = pixels.replace(pack("B", ri//palsize), packed_index)

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
        always writes in palette mode.
        """
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
        lexicon = [pal.match(self.palette.colors[i]) for i in range(256)]
        lexicon[self.palette.tran_index] = pal.tran_index
        if isinstance(self, Flat):
            self.data = bytes([lexicon[b] for b in self.data])
        else:
            raw = self.to_raw()
            self.load_raw(bytes([lexicon[b] for b in raw]),
                self.width, self.height,
                self.x_offset, self.y_offset)


class Flat(Graphic):
    """Subclass of Graphic, for flat graphics."""

    def get_dimensions(self):
        sz = len(self.data)
        if sz == 4096: return (64, 64)
        if sz == 4160: return (64, 65)
        if sz == 8192: return (64, 128)
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
