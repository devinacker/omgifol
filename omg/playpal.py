from omg.lump import Lump
from omg.util import *
import omg.palette

class Playpal:
    """An editor for Doom's PLAYPAL lump. The PLAYPAL lump contains 14
    palettes: the game's base palette, the palettes used when the
    player is in pain or uses the berserk powerup, the palettes used
    when the player picks up an item, and the palette used when the
    player is wearing the radiation suit.

    The palettes are located in a member list called 'palettes'. Each
    palette is a Palette instance."""

    def __init__(self, source=None):
        """Construct a new EditPlaypal object. Source may be a PLAYPAL
        lump or a Palette instance. If a Palette instance, all 14
        palettes are set to copies of it. If no source is specified,
        the default palette is used."""
        if isinstance(source, Lump):
            self.from_lump(source)
        else:
            self.set_base(source)

    def build_defaults(self):
        """Build all 13 extra palettes, using default values (red for
        pain, yellow for item pickups, green for the radiation suit).
        The values used here are not exactly the same as those in
        Doom's PLAYPAL, but decent approximations."""
        self.build_pain()
        self.build_item()
        self.build_suit()

    def build_suit (self, color=(0,255,0), intensity=0.2):
        """Set the color and intensity for the radiation suit palette."""
        self.palettes[13].blend(color, intensity)

    def build_pain (self, color=(255,0,0), minintensity=0.1, maxintensity=0.8):
        """Set the color and intensities for the player-in-pain (also
        used by the berserk powerup) palettes."""
        step = (maxintensity - minintensity) / 8.0
        for i in range(8):
            self.palettes[i+1].blend(color, step*i + minintensity)

    def build_item (self, color=(255,255,64), minintensity=0.1, maxintensity=0.3):
        """Set color and intensity for the item pick-up palettes."""
        step = (maxintensity - minintensity) / 3.0
        for i in range(3):
            self.palettes[i+10].blend(color, step * i + minintensity)

    def from_lump(self, lump):
        """Load data from a PLAYPAL lump."""
        self.palettes = [omg.palette.Palette(lump.data[i*768:(i+1)*768], 0, 0)
            for i in range(14)]

    def to_lump(self):
        """Compile to a Doom-ready PLAYPAL Lump."""
        return Lump(join([p.bytes for p in self.palettes]))

    def set_base(self, palette=None):
        """Set all palettes to copies of a given Palette object. If the
        palette parameter is not provided, the default palette is used."""
        palette = palette or omg.palette.default
        self.palettes = [deepcopy(palette) for i in range(14)]
