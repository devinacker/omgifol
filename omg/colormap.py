import omg.palette
import omg.lump

class Colormap:
    """An editor for Doom's COLORMAP lump. The colormap holds 34 tables
    of indices to the game's palette. The first 32 tables hold data
    for different brightness levels, the 33rd holds the indices used
    by the invulnerability powerup, and the 34th is unused."""

    def __init__(self, from_lump=None):
        """Create new, optionally from an existing lump."""
        self.tables = [[0 for x in range(256)] for y in range(34)]
        if from_lump:
            self.from_lump(from_lump)

    def build_fade(self, palette=None, fade=(0,0,0)):
        """Build fade tables. The default fade color is black;
        this may be overriden. Light color is not yet supported."""
        palette = palette or omg.palette.default
        x, y, z = fade
        for n in range(32):
            e = 31-n
            for c in range(256):
                r, g, b = palette.colors[c]
                r = (r*n + x*e) // 32
                g = (g*n + y*e) // 32
                b = (b*n + z*e) // 32
                self.tables[e][c] = palette.match((r,g,b))

    def build_invuln(self, palette=None, start=(0,0,0), end=(255,255,255)):
        """Build range used by the invulnerability powerup."""
        palette = palette or omg.palette.default
        ar, ag, ab = start
        br, bg, bb = end
        for i in range(256):
            bright = sum(palette.colors[i]) // 3
            r = (ar*bright + br*(256-bright)) // 256
            g = (ag*bright + bg*(256-bright)) // 256
            b = (ab*bright + bb*(256-bright)) // 256
            self.tables[32][i] = palette.match((r,g,b))

    def from_lump(self, lump):
        """Load from a COLORMAP lump."""
        assert len(lump.data) == 34*256
        for n in range(34):
            self.tables[n] = [lump.data[i] for i in range(n*256,(n+1)*256)]

    def to_lump(self):
        """Pack to a COLORMAP lump."""
        output = bytes()
        for t in self.tables:
            output += bytes(t)
        return omg.lump.Lump(output)

        # packed = [''.join([chr(c) for c in t]) for t in self.tables]
        # return omg.lump.Lump(''.join(packed))

    def set_position(self,table,index,pal_index):
        """Sets a specified position in the colormap to the specified
        index in the playpal."""
        self.tables[table][index] = pal_index
