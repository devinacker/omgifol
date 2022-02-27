from struct   import pack, unpack
from omg.util import *

class Palette:

    """Used for storing a list of colors and doing things with them
    (such as looking up the best match for arbitrary RGB values).

    Palette is distinct from Colormap and Playpal; these two provide
    lump- and WAD-related operations while delegating (some of) their
    color processing to Palette.

    Fields containing useful public data (modifying them directly
    probably isn't a good idea, however):

        .colors       List of (r, g, b) tuples
        .bytes        Palette's colors as a bytes object (rgbrgbrgb...)
        .save_bytes   Same as above, but with the transparency color set;
                      useful when saving files
        .tran_color   (r, g, b) value for transparency
        .tran_index   Index in palette of transparency color

    The following fields are intended for internal use:

        .memo         Table for RGB lookup memoization
        .grays        List of indices of colors with zero saturation
        .bright_lut   Brightness LUT, used internally to speed up
                      lookups (when not memoized).
    """

    def __init__(self, colors=None, tran_index=None, tran_color=None):
        """Creates a new Palette object. The 'colors' argument may be
        either a list of (r,g,b) tuples or an RGBRGBRGB... string/bytes.
        'tran_index' specifies the index in the palette where the
        transparent color should be placed. Note that this is only used
        when saving images, and thus doesn't affect color lookups.
        'tran_color' is the color to use for transparency."""

        colors = colors or default_colors
        tran_index = tran_index or default_tran_index
        tran_color = tran_color or default_tran_color

        if isinstance(colors, str):
            colors = colors.encode('latin-1')

        if isinstance(colors, list):
            self.colors = colors[:]
        elif isinstance(colors, bytes):
            self.colors = [unpack('BBB', colors[i:i+3]) for i in range(0,768,3)]
        else:
            raise TypeError("Argument 'colors' must be list or string or bytes")

        # Doom graphics don't actually use indices for transparency; the
        # following data is only used when converting between image formats.
        self.tran_index = tran_index
        self.tran_color = tran_color
        self.make_bytes()
        self.make_grays()

        # Memoizing color translations can speed up RGB-to-palette
        # conversions significantly, in particular when converting
        # lots of graphics in one session. See docstring for build_lut
        # below for description of what bright_lut does.
        self.memo = {}
        self.bright_lut = []
        self.reset_memo()

    def make_bytes(self):
        """Create/update 'bytes' and 'save_bytes' from the current set of
        colors and the 'tran_index' and 'tran_color' fields."""
        self.bytes = bytes().join([pack('BBB', *rgb) for rgb in self.colors])
        self.save_bytes = \
            self.bytes[:self.tran_index*3] + \
            pack('BBB', *self.tran_color) + \
            self.bytes[(self.tran_index+1)*3:]

    def make_grays(self):
        """Create 'grays' table containing the indices of all grays
        in the current set of colors."""
        self.grays = [i for i, rgb in enumerate(self.colors) \
            if (rgb[0]==rgb[1]==rgb[2])]

    def reset_memo(self):
        """Clear the memo table (but (re)add the palette's colors)"""
        self.memo = {}
        for i in range(len(self.colors)):
            if i != self.tran_index:
                self.memo[self.colors[i]] = i

    def build_lut(self, distance=16):
        """Build 256-entry LUT for looking up colors in the palette
        close to a given brightness (range 0-255). Each entry is a
        list of indices. No position is empty; in the worst case,
        the closest gray can be used.

        The 'distance' parameter defines what "close" is, and should
        be an integer 0-256. Lower distance means faster lookups,
        but worse precision.

        A good value for Doom is 10. Anything over 32 only wastes time.
        """
        self.bright_lut = []
        assert 0 <= distance <= 256
        for level in range(256):
            candidates = []
            for j, rgb in enumerate(self.colors):
                if abs(level - (sum(rgb) // 3)) < distance:
                    candidates.append(j)
            # Make sure each entry contains at least one gray
            # color that can be relied on in the worst case
            best_d = 256
            best_i = 0
            for gray_index in self.grays:
                r, g, b = self.colors[gray_index]
                dist = abs(r - level)
                if dist < best_d:
                    best_i = gray_index
                    if dist == 0:
                        break
                    best_d = dist
            if best_i not in candidates:
                candidates.append(best_i)
            self.bright_lut.append(candidates)

    def match(self, color):
        """Find the closest match in the palette for a color.
        Takes an (r,g,b) tuple as argument and returns a palette index."""
        if color == self.tran_color:
            return self.tran_index
        if color in self.memo:
            return self.memo[color]
        if len(self.bright_lut) == 0:
            self.build_lut()
        best_dist = 262144
        best_i = 0
        ar, ag, ab = color
        candidates = self.bright_lut[int(sum(color)) // 3]
        for i in candidates:
            br, bg, bb = self.colors[i]
            dr = ar-br
            dg = ag-bg
            db = ab-bb
            dist = dr*dr + dg*dg + db*db
            if dist < best_dist:
                if dist == 0:
                    return i
                best_dist = dist
                best_i = i
        self.memo[color] = best_i
        return best_i

    def blend(self, color, intensity=0.5):
        """Blend the entire palette against a color (given as an RGB triple).
        Intensity must be a floating-point number in the range 0-1."""
        assert 0.0 <= intensity <= 1.0
        nr = color[0] * intensity
        ng = color[1] * intensity
        nb = color[2] * intensity
        remain = 1.0 - intensity
        for i in range(len(self.colors)):
            ar, ag, ab = self.colors[i]
            self.colors[i] = (int(ar*remain + nr),
                              int(ag*remain + ng),
                              int(ab*remain + nb))
        self.make_bytes()
        self.make_grays()
        self.reset_memo()
        self.bright_lut = []

# Colors of the Doom palette, used by default
default_colors = b"\
\x00\x00\x00\x1f\x17\x0b\x17\x0f\x07\x4b\x4b\x4b\xff\xff\xff\x1b\
\x1b\x1b\x13\x13\x13\x0b\x0b\x0b\x07\x07\x07\x2f\x37\x1f\x23\x2b\
\x0f\x17\x1f\x07\x0f\x17\x00\x4f\x3b\x2b\x47\x33\x23\x3f\x2b\x1b\
\xff\xb7\xb7\xf7\xab\xab\xf3\xa3\xa3\xeb\x97\x97\xe7\x8f\x8f\xdf\
\x87\x87\xdb\x7b\x7b\xd3\x73\x73\xcb\x6b\x6b\xc7\x63\x63\xbf\x5b\
\x5b\xbb\x57\x57\xb3\x4f\x4f\xaf\x47\x47\xa7\x3f\x3f\xa3\x3b\x3b\
\x9b\x33\x33\x97\x2f\x2f\x8f\x2b\x2b\x8b\x23\x23\x83\x1f\x1f\x7f\
\x1b\x1b\x77\x17\x17\x73\x13\x13\x6b\x0f\x0f\x67\x0b\x0b\x5f\x07\
\x07\x5b\x07\x07\x53\x07\x07\x4f\x00\x00\x47\x00\x00\x43\x00\x00\
\xff\xeb\xdf\xff\xe3\xd3\xff\xdb\xc7\xff\xd3\xbb\xff\xcf\xb3\xff\
\xc7\xa7\xff\xbf\x9b\xff\xbb\x93\xff\xb3\x83\xf7\xab\x7b\xef\xa3\
\x73\xe7\x9b\x6b\xdf\x93\x63\xd7\x8b\x5b\xcf\x83\x53\xcb\x7f\x4f\
\xbf\x7b\x4b\xb3\x73\x47\xab\x6f\x43\xa3\x6b\x3f\x9b\x63\x3b\x8f\
\x5f\x37\x87\x57\x33\x7f\x53\x2f\x77\x4f\x2b\x6b\x47\x27\x5f\x43\
\x23\x53\x3f\x1f\x4b\x37\x1b\x3f\x2f\x17\x33\x2b\x13\x2b\x23\x0f\
\xef\xef\xef\xe7\xe7\xe7\xdf\xdf\xdf\xdb\xdb\xdb\xd3\xd3\xd3\xcb\
\xcb\xcb\xc7\xc7\xc7\xbf\xbf\xbf\xb7\xb7\xb7\xb3\xb3\xb3\xab\xab\
\xab\xa7\xa7\xa7\x9f\x9f\x9f\x97\x97\x97\x93\x93\x93\x8b\x8b\x8b\
\x83\x83\x83\x7f\x7f\x7f\x77\x77\x77\x6f\x6f\x6f\x6b\x6b\x6b\x63\
\x63\x63\x5b\x5b\x5b\x57\x57\x57\x4f\x4f\x4f\x47\x47\x47\x43\x43\
\x43\x3b\x3b\x3b\x37\x37\x37\x2f\x2f\x2f\x27\x27\x27\x23\x23\x23\
\x77\xff\x6f\x6f\xef\x67\x67\xdf\x5f\x5f\xcf\x57\x5b\xbf\x4f\x53\
\xaf\x47\x4b\x9f\x3f\x43\x93\x37\x3f\x83\x2f\x37\x73\x2b\x2f\x63\
\x23\x27\x53\x1b\x1f\x43\x17\x17\x33\x0f\x13\x23\x0b\x0b\x17\x07\
\xbf\xa7\x8f\xb7\x9f\x87\xaf\x97\x7f\xa7\x8f\x77\x9f\x87\x6f\x9b\
\x7f\x6b\x93\x7b\x63\x8b\x73\x5b\x83\x6b\x57\x7b\x63\x4f\x77\x5f\
\x4b\x6f\x57\x43\x67\x53\x3f\x5f\x4b\x37\x57\x43\x33\x53\x3f\x2f\
\x9f\x83\x63\x8f\x77\x53\x83\x6b\x4b\x77\x5f\x3f\x67\x53\x33\x5b\
\x47\x2b\x4f\x3b\x23\x43\x33\x1b\x7b\x7f\x63\x6f\x73\x57\x67\x6b\
\x4f\x5b\x63\x47\x53\x57\x3b\x47\x4f\x33\x3f\x47\x2b\x37\x3f\x27\
\xff\xff\x73\xeb\xdb\x57\xd7\xbb\x43\xc3\x9b\x2f\xaf\x7b\x1f\x9b\
\x5b\x13\x87\x43\x07\x73\x2b\x00\xff\xff\xff\xff\xdb\xdb\xff\xbb\
\xbb\xff\x9b\x9b\xff\x7b\x7b\xff\x5f\x5f\xff\x3f\x3f\xff\x1f\x1f\
\xff\x00\x00\xef\x00\x00\xe3\x00\x00\xd7\x00\x00\xcb\x00\x00\xbf\
\x00\x00\xb3\x00\x00\xa7\x00\x00\x9b\x00\x00\x8b\x00\x00\x7f\x00\
\x00\x73\x00\x00\x67\x00\x00\x5b\x00\x00\x4f\x00\x00\x43\x00\x00\
\xe7\xe7\xff\xc7\xc7\xff\xab\xab\xff\x8f\x8f\xff\x73\x73\xff\x53\
\x53\xff\x37\x37\xff\x1b\x1b\xff\x00\x00\xff\x00\x00\xe3\x00\x00\
\xcb\x00\x00\xb3\x00\x00\x9b\x00\x00\x83\x00\x00\x6b\x00\x00\x53\
\xff\xff\xff\xff\xeb\xdb\xff\xd7\xbb\xff\xc7\x9b\xff\xb3\x7b\xff\
\xa3\x5b\xff\x8f\x3b\xff\x7f\x1b\xf3\x73\x17\xeb\x6f\x0f\xdf\x67\
\x0f\xd7\x5f\x0b\xcb\x57\x07\xc3\x4f\x00\xb7\x47\x00\xaf\x43\x00\
\xff\xff\xff\xff\xff\xd7\xff\xff\xb3\xff\xff\x8f\xff\xff\x6b\xff\
\xff\x47\xff\xff\x23\xff\xff\x00\xa7\x3f\x00\x9f\x37\x00\x93\x2f\
\x00\x87\x23\x00\x4f\x3b\x27\x43\x2f\x1b\x37\x23\x13\x2f\x1b\x0b\
\x00\x00\x53\x00\x00\x47\x00\x00\x3b\x00\x00\x2f\x00\x00\x23\x00\
\x00\x17\x00\x00\x0b\x00\x00\x00\xff\x9f\x43\xff\xe7\x4b\xff\x7b\
\xff\xff\x00\xff\xcf\x00\xcf\x9f\x00\x9b\x6f\x00\x6b\xa7\x6b\x6b\
"

# Defaults for image transparency
default_tran_index = 247
default_tran_color = (255, 0, 255)

# Default palette object, using the default values
default = Palette()
