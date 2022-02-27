"""
lineinfo.py -- dealing with Doom linedef trigger types.
Provides functions to create a human-readable description
code from a trigger number, and the inverse operation.

Guide to Trigger Description Codes (R):

Example:        "FLOOR SR UP SLOW CRUSH LNC-8"

Categories:
    DOOR       - Doors (regular and locked)
    FLOOR      - Floor movers
    CEIL       - Ceiling movers
    PLAT       - Platforms and lifts
    CRUSHER    - Crushers
    STAIR      - Stair builders
    ELEVATOR   - Boom elevators
    LIGHT      - Light changers
    EXIT       - Exits
    TELEPORT   - Teleports
    DONUT      - Donuts (lower pillar, raise surrounding sector)
    TRANSFER   - Transfer properties (Boom)
    SCROLL     - Scroll lines and sectors (Boom)

Trigger types:
    P1 - Push(door) trigger, works once
    PR - Push(door) trigger, works repeatedly
    S1 - Switch, works once
    SR - Switch, works repeatedly
    W1 - Walk across, works once
    WR - Walk across, works repeatedly
    G1 - Shoot, works once
    GR - Shoot, works repeatedly

Door locks:
    YEL - Yellow key lock
    RED - Red key lock
    BLU - Blue key lock

Door types:
    OWC - Open, Wait, Close
    CWO - Close, Wait, Open
    OSO - Open, Stay Open
    CSC - Close, Stay Closed

Motion speed
    SLOW - Slow
    NORM - Normal
    FAST - Fast
    TURB - Turbo
    INST - Instant

Delay times
    3SEC  - 3 seconds
    4SEC  - 4 seconds
    30SEC - 30 seconds

Sector property changers:
    CPYTEX           - Copy Texture
    CPYTEX+DELTYPE   - Copy Texture, Reset type
    CPYTEX+TYPE      - Copy Texture and Type

Directions:
    DOWN    - Down
    UP      - Up
    NOMOVE  - Stay (only change properties)

Miscellaneous:
    SECRET   - A secret exit
    MONSTER  - Monsters can activate the trigger
    LINE     - Line teleporters
    REVERSE  - Line teleporter, reversed
    SILENT   - Make crushers or teleporters silent
    CRUSH    - Enable crushing (for CEILs and FLOORs,
               not to be confused with CRUSHERs)

Destinations/platforms:
    LNF   - Lowest Neighbor Floor
    LNC   - Lowest Neighbor Ceiling
    HNF   - Highest Neighbor Floor
    HNC   - Highest Neighbor Ceiling
    NNF   - Next Neighbor Floor
    NNC   - Next Neighbor Ceiling
    HNF+8 - 8 above Highest neighbor Floor
    LNC+8 - 8 under Lowest neighbor Ceiling
    F+8   - 8 above floor
    8     - 8 units Absolute  (STAIRs only)
    16    - 16 units Absolute (STAIRs only)
    24    - 24 units Absolute
    32    - 32 units Absolute
    512   - 512 units absolute
    SLT   - Shortest Lower Texture
    SUT   - Shortest Upper Texture
    NLF   - Next Lowest neighbor Floor
    NLC   - Next Lowest neighbor Ceiling
    NHF   - Next Highest neighbor Floor
    CURRF - Current Floor (ELEVATORs)
    FLR   - Floor
    CL    - Ceiling
    NAF   - Next adjacent floor
    PERP  - Perpetual
    STOP  - Stop ongoing motion

Models:
    TRIG  - Use trigger sector as model
    NUM   - Lookup adjacent model numerically

Lighting:
    35    - 35 units
    255   - 255 units
    MAXN  - Maximum Neighbor
    MINN  - Minimum Neighbor
    BLINK - Blinking

Transfers (check boomref.txt for more info):
    FLIGHT       - Transfer floor light level
    CLIGHT       - Transfer ceiling light level
    TRANSLUCENCY - Transfer line translucency
    HEIGHTS      - The famous 242!
    FRICTION     - Transfer friction
    WIND         - Transfer current
    POINTFORCE   - Transfer force point (?)

Scrollers (check boomref.txt for more info):
    CARRY       - Carry objects (conveyor)
    WRTSECTOR   - With respect to 1st side's sector
    ACCEL       - Accelerate scrolling
    RIGHT       - Right direction
    LEFT        - Left direction
    WALL        - Scroll wall
    SYNCED      - Sync scrolling to sector
    OFFSETS     - Scroll by offsets
"""

from fnmatch import fnmatchcase

# Define description codes for the standard triggers
desc2num = \
{
  "": 0,
  "NO ACTION":0,
# Doors
  "DOOR PR SLOW OWC 4SEC MONSTER":1,
  "DOOR PR FAST OWC 4SEC":117,
  "DOOR SR SLOW OWC 4SEC":63,
  "DOOR SR FAST OWC 4SEC":114,
  "DOOR S1 SLOW OWC 4SEC":29,
  "DOOR S1 FAST OWC 4SEC":111,
  "DOOR WR SLOW OWC 4SEC":90,
  "DOOR WR FAST OWC 4SEC":105,
  "DOOR W1 SLOW OWC 4SEC":4,
  "DOOR W1 FAST OWC 4SEC":108,
  "DOOR P1 SLOW OSO":31,
  "DOOR P1 FAST OSO":118,
  "DOOR SR SLOW OSO":61,
  "DOOR SR FAST OSO":114,
  "DOOR S1 SLOW OSO":103,
  "DOOR S1 FAST OSO":112,
  "DOOR WR SLOW OSO":86,
  "DOOR WR FAST OSO":106,
  "DOOR W1 SLOW OSO":2,
  "DOOR W1 FAST OSO":109,
  "DOOR GR FAST OSO":46,
  "DOOR SR SLOW CSC":42,
  "DOOR SR FAST CSC":116,
  "DOOR S1 SLOW CSC":50,
  "DOOR S1 FAST CSC":113,
  "DOOR WR SLOW CSC":75,
  "DOOR WR FAST CSC":107,
  "DOOR W1 SLOW CSC":3,
  "DOOR W1 FAST CSC":110,
  "DOOR SR SLOW CWO 30SEC":196,
  "DOOR S1 SLOW CWO 30SEC":175,
  "DOOR WR SLOW CWO 30SEC":76,
  "DOOR W1 SLOW CWO 30SEC":16,
  "DOOR PR SLOW OWC 4SEC BLU":26,
  "DOOR PR SLOW OWC 4SEC RED":28,
  "DOOR PR SLOW OWC 4SEC YEL":27,
  "DOOR P1 SLOW OSO BLU":32,
  "DOOR P1 SLOW OSO RED":33,
  "DOOR P1 SLOW OSO YEL":34,
  "DOOR SR FAST OSO BLU":99,
  "DOOR SR FAST OSO RED":134,
  "DOOR SR FAST OSO YEL":136,
  "DOOR S1 FAST OSO BLU":133,
  "DOOR S1 FAST OSO RED":135,
  "DOOR S1 FAST OSO YEL":137,
# Floors
  "FLOOR SR DOWN SLOW LNF":60,
  "FLOOR S1 DOWN SLOW LNF":23,
  "FLOOR WR DOWN SLOW LNF":82,
  "FLOOR W1 DOWN SLOW LNF":38,
  "FLOOR SR DOWN SLOW LNF CPYTEX+TYPE NUM":177,
  "FLOOR S1 DOWN SLOW LNF CPYTEX+TYPE NUM":159,
  "FLOOR WR DOWN SLOW LNF CPYTEX+TYPE NUM":84,
  "FLOOR W1 DOWN SLOW LNF CPYTEX+TYPE NUM":37,
  "FLOOR SR UP SLOW NNF":69,
  "FLOOR S1 UP SLOW NNF":18,
  "FLOOR WR UP SLOW NNF":128,
  "FLOOR W1 UP SLOW NNF":119,
  "FLOOR SR UP FAST NNF":132,
  "FLOOR S1 UP FAST NNF":131,
  "FLOOR WR UP FAST NNF":129,
  "FLOOR W1 UP FAST NNF":130,
  "FLOOR SR DOWN SLOW NNF":222,
  "FLOOR S1 DOWN SLOW NNF":221,
  "FLOOR WR DOWN SLOW NNF":220,
  "FLOOR W1 DOWN SLOW NNF":219,
  "FLOOR SR UP SLOW LNC":64,
  "FLOOR S1 UP SLOW LNC":101,
  "FLOOR WR UP SLOW LNC":91,
  "FLOOR W1 UP SLOW LNC":5,
  "FLOOR G1 UP SLOW LNC":24,
  "FLOOR SR UP SLOW LNC-8 CRUSH":65,
  "FLOOR S1 UP SLOW LNC-8 CRUSH":55,
  "FLOOR WR UP SLOW LNC-8 CRUSH":94,
  "FLOOR W1 UP SLOW LNC-8 CRUSH":56,
  "FLOOR SR DOWN SLOW HNF":45,
  "FLOOR S1 DOWN SLOW HNF":102,
  "FLOOR WR DOWN SLOW HNF":83,
  "FLOOR W1 DOWN SLOW HNF":19,
  "FLOOR SR DOWN FAST HNF+8":70,
  "FLOOR S1 DOWN FAST HNF+8":71,
  "FLOOR WR DOWN FAST HNF+8":98,
  "FLOOR W1 DOWN FAST HNF+8":36,
  "FLOOR SR UP SLOW 24":180,
  "FLOOR S1 UP SLOW 24":161,
  "FLOOR WR UP SLOW 24":92,
  "FLOOR W1 UP SLOW 24":58,
  "FLOOR SR UP SLOW 24 CPYTEX+TYPE TRIG":179,
  "FLOOR S1 UP SLOW 24 CPYTEX+TYPE TRIG":160,
  "FLOOR WR UP SLOW 24 CPYTEX+TYPE TRIG":93,
  "FLOOR W1 UP SLOW 24 CPYTEX+TYPE TRIG":59,
  "FLOOR SR UP SLOW SLT":176,
  "FLOOR S1 UP SLOW SLT":158,
  "FLOOR WR UP SLOW SLT":96,
  "FLOOR W1 UP SLOW SLT":30,
  "FLOOR SR UP SLOW 512":178,
  "FLOOR S1 UP SLOW 512":140,
  "FLOOR WR UP SLOW 512":147,
  "FLOOR W1 UP SLOW 512":142,
  "FLOOR SR NOMOVE CPYTEX+TYPE SLT TRIG":190,
  "FLOOR S1 NOMOVE CPYTEX+TYPE SLT TRIG":189,
  "FLOOR WR NOMOVE CPYTEX+TYPE SLT TRIG":154,
  "FLOOR W1 NOMOVE CPYTEX+TYPE SLT TRIG":153,
  "FLOOR SR NOMOVE CPYTEX+TYPE SLT NUM":78,
  "FLOOR S1 NOMOVE CPYTEX+TYPE SLT NUM":241,
  "FLOOR WR NOMOVE CPYTEX+TYPE SLT NUM":240,
  "FLOOR W1 NOMOVE CPYTEX+TYPE SLT NUM":239,
# Ceilings
  "CEIL SR DOWN FAST FLR":43,
  "CEIL S1 DOWN FAST FLR":41,
  "CEIL WR DOWN FAST FLR":152,
  "CEIL W1 DOWN FAST FLR":145,
  "CEIL SR UP SLOW HNC":186,
  "CEIL S1 UP SLOW HNC":166,
  "CEIL WR UP SLOW HNC":151,
  "CEIL W1 UP SLOW HNC":40,
  "CEIL SR DOWN SLOW F+8":187,
  "CEIL S1 DOWN SLOW F+8":167,
  "CEIL WR DOWN SLOW F+8":72,
  "CEIL W1 DOWN SLOW F+8":44,
  "CEIL SR DOWN SLOW LNC":205,
  "CEIL S1 DOWN SLOW LNC":203,
  "CEIL WR DOWN SLOW LNC":201,
  "CEIL W1 DOWN SLOW LNC":199,
  "CEIL SR DOWN SLOW HNF":205,
  "CEIL S1 DOWN SLOW HNF":204,
  "CEIL WR DOWN SLOW HNF":202,
  "CEIL W1 DOWN SLOW HNF":200,
# Platforms and lifts
  "PLAT SR SLOW CPYTEX TRIG 24":66,
  "PLAT S1 SLOW CPYTEX TRIG 24":15,
  "PLAT WR SLOW CPYTEX TRIG 24":148,
  "PLAT W1 SLOW CPYTEX TRIG 24":143,
  "PLAT SR SLOW CPYTEX TRIG 32":67,
  "PLAT S1 SLOW CPYTEX TRIG 32":14,
  "PLAT WR SLOW CPYTEX TRIG 32":149,
  "PLAT W1 SLOW CPYTEX TRIG 32":144,
  "PLAT SR SLOW CPYTEX+DELTYPE TRIG NAF":68,
  "PLAT S1 SLOW CPYTEX+DELTYPE TRIG NAF":20,
  "PLAT WR SLOW CPYTEX+DELTYPE TRIG NAF":95,
  "PLAT W1 SLOW CPYTEX+DELTYPE TRIG NAF":22,
  "PLAT G1 SLOW CPYTEX+DELTYPE TRIG NAF":47,
  "PLAT SR SLOW 3SEC PERP":181,
  "PLAT S1 SLOW 3SEC PERP":162,
  "PLAT WR SLOW 3SEC PERP":87,
  "PLAT W1 SLOW 3SEC PERP":53,
  "PLAT SR STOP":182,
  "PLAT S1 STOP":163,
  "PLAT WR STOP":89,
  "PLAT W1 STOP":54,
  "PLAT SR SLOW 3SEC LNF":62,
  "PLAT S1 SLOW 3SEC LNF":21,
  "PLAT WR SLOW 3SEC LNF":88,
  "PLAT W1 SLOW 3SEC LNF":10,
  "PLAT SR FAST 3SEC LNF":123,
  "PLAT S1 FAST 3SEC LNF":122,
  "PLAT WR FAST 3SEC LNF":120,
  "PLAT W1 FAST 3SEC LNF":121,
  "PLAT SR INST CL":211,
  "PLAT WR INST CL":212,
# Crushers
  "CRUSHER SR SLOW":184,
  "CRUSHER S1 SLOW":49,
  "CRUSHER WR SLOW":73,
  "CRUSHER W1 SLOW":25,
  "CRUSHER SR FAST":183,
  "CRUSHER S1 FAST":164,
  "CRUSHER WR FAST":77,
  "CRUSHER W1 FAST":6,
  "CRUSHER SR SLOW SILENT":185,
  "CRUSHER S1 SLOW SILENT":165,
  "CRUSHER WR SLOW SILENT":150,
  "CRUSHER W1 SLOW SILENT":141,
  "CRUSHER SR STOP":188,
  "CRUSHER S1 STOP":168,
  "CRUSHER WR STOP":74,
  "CRUSHER W1 STOP":57,
# Stairs
  "STAIR SR UP SLOW 8":258,
  "STAIR S1 UP SLOW 8":7,
  "STAIR WR UP SLOW 8":256,
  "STAIR W1 UP SLOW 8":8,
  "STAIR SR UP FAST 16":259,
  "STAIR S1 UP FAST 16":127,
  "STAIR WR UP FAST 16":257,
  "STAIR W1 UP FAST 16":100,
# Boom elevators
  "ELEVATOR SR FAST NHF":230,
  "ELEVATOR S1 FAST NHF":229,
  "ELEVATOR WR FAST NHF":228,
  "ELEVATOR W1 FAST NHF":227,
  "ELEVATOR SR FAST NHF":234,
  "ELEVATOR S1 FAST NLF":233,
  "ELEVATOR WR FAST NLF":232,
  "ELEVATOR W1 FAST NLF":231,
  "ELEVATOR SR FAST CURRF":238,
  "ELEVATOR S1 FAST CURRF":237,
  "ELEVATOR WR FAST CURRF":236,
  "ELEVATOR W1 FAST CURRF":235,
# Lighting
  "LIGHT SR 35":139,
  "LIGHT S1 35":170,
  "LIGHT WR 35":79,
  "LIGHT W1 35":35,
  "LIGHT SR 255":138,
  "LIGHT S1 255":171,
  "LIGHT WR 255":81,
  "LIGHT W1 255":13,
  "LIGHT SR MAXN":192,
  "LIGHT S1 MAXN":169,
  "LIGHT WR MAXN":80,
  "LIGHT W1 MAXN":12,
  "LIGHT SR MINN":194,
  "LIGHT S1 MINN":173,
  "LIGHT WR MINN":157,
  "LIGHT W1 MINN":104,
  "LIGHT SR BLINK":193,
  "LIGHT S1 BLINK":172,
  "LIGHT WR BLINK":156,
  "LIGHT W1 BLINK":17,
# Exits
  "EXIT S1":11,
  "EXIT W1":52,
  "EXIT G1":197,
  "EXIT S1 SECRET":51,
  "EXIT W1 SECRET":124,
  "EXIT G1 SECRET":198,
# Teleports
  "TELEPORT SR":195,
  "TELEPORT S1":174,
  "TELEPORT WR":97,
  "TELEPORT W1":39,
  "TELEPORT WR MONSTER":126,
  "TELEPORT W1 MONSTER":125,
  "TELEPORT SR MONSTER":269,
  "TELEPORT S1 MONSTER":268,
  "TELEPORT SR SILENT":210,
  "TELEPORT S1 SILENT":209,
  "TELEPORT WR SILENT":208,
  "TELEPORT W1 SILENT":207,
  "TELEPORT WR SILENT LINE":244,
  "TELEPORT W1 SILENT LINE":243,
  "TELEPORT WR SILENT LINE REVERSE":263,
  "TELEPORT W1 SILENT LINE REVERSE":262,
  "TELEPORT WR SILENT LINE MONSTER":267,
  "TELEPORT W1 SILENT LINE MONSTER":266,
  "TELEPORT WR SILENT LINE REVERSE MONSTER":265,
  "TELEPORT W1 SILENT LINE REVERSE MONSTER":264,
# Donuts
  "DONUT SR":191,
  "DONUT S1":9,
  "DONUT WR":155,
  "DONUT W1":146,
# Boom property transfer
  "TRANSFER FLIGHT":213,
  "TRANSFER CLIGHT":261,
  "TRANSFER TRANSLUCENCY":260,
  "TRANSFER HEIGHTS":242,
  "TRANSFER FRICTION":223,
  "TRANSFER WIND":224,
  "TRANSFER CURRENT":225,
  "TRANSFER POINTFORCE":226,
# Scrollers
  "SCROLL CL":250,
  "SCROLL FLR":251,
  "SCROLL CARRY":252,
  "SCROLL FLR+CARRY":253,
  "SCROLL WALL SYNCED":254,
  "SCROLL WALL OFFSETS":255,
  "SCROLL WALL RIGHT":85,
  "SCROLL WALL LEFT":48,
  "SCROLL CL WRTSECTOR":245,
  "SCROLL FLR WRTSECTOR":246,
  "SCROLL CARRY WRTSECTOR":247,
  "SCROLL F+CARRY WRTSECTOR":248,
  "SCROLL WALL WRTSECTOR":249,
  "SCROLL CL ACCEL":214,
  "SCROLL FLR ACCEL":215,
  "SCROLL CARRY ACCEL":216,
  "SCROLL FLR+CARRY ACCEL":217,
  "SCROLL WALL ACCEL":218
}

num2desc = {}
for d, n in desc2num.items(): num2desc[n] = d
del(d)
del(n)

trigcompat = \
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
  1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1,
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
  0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
  1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0,
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
  0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]

def check_compat(num):
    """Check the compatibility for a trigger number."""
    if 8192 <= num < 32768:
        return "BOOM GENERALIZED"
    try:
        return ["UNKNOWN", "DOOM19", "BOOM EXTENDED"][trigcompat[num]]
    except:
        return "UNKNOWN"

def decode(n):
    """Generate a description code for a number."""
    d = []
    if n < 8192:
        if n in num2desc:
            return num2desc[n]
        return "UNKNOWN"
    # Boom generalized
    elif 0x2F80 <= n < 0x3000:
        n -= 0x2F80
        d += ["CRUSHER"]
        d += [("W1","WR","S1","SR","G1","GR","P1","PR") [n&0x0007]]
        d += [("SLOW","NORMAL","FAST","TURBO")          [(n&0x0018)>>3]]
        d += [("MONSTER","")                            [(n&0x0020)>>5]]
        d += [("SILENT","")                             [(n&0x00c0)>>6]]
    elif 0x3000 <= n < 0x3400:
        n -= 0x3000
        d += ["STAIR"]
        d += [("W1","WR","S1","SR","G1","GR","P1","PR") [n&0x0007]]
        d += [("SLOW","NORMAL","FAST","TURBO")          [(n&0x0018)>>3]]
        d += [("","MONSTER")                            [(n&0x0020)>>5]]
        d += [("4","8","16","24")                       [(n&0x00c0)>>6]]
        d += [("DOWN","UP")                             [(n&0x0100)>>8]]
        d += [("", "IGNTXT")                            [(n&0x0200)>>9]]
    elif 0x3400 <= n < 0x3800:
        n -= 0x3400
        d += ["PLATFORM"]
        d += [("W1","WR","S1","SR","G1","GR","P1","PR") [n&0x0007]]
        d += [("SLOW","NORMAL","FAST","TURBO")          [(n&0x0018)>>3]]
        d += [("MONSTER","")                            [(n&0x0020)>>5]]
        d += [("1","3","5","10")                        [(n&0x00c0)>>6]]
        d += [("LNF","NNF","LNC","PERP")                [(n&0x0300)>>8]]
    elif 0x3800 <= n < 0x3c00:
        n -= 0x3800
        d += ["DOOR"]
        d += [("W1","WR","S1","SR","G1","GR","P1","PR") [n&0x0007]]
        d += [("SLOW","NORMAL","FAST","TURBO")          [(n&0x0018)>>3]]
        d += [("OWC","OSO")                             [(n&0x0020)>>5]]
        d += [("ANY","RED","YELLOW","BLUE","RED",
               "BLUE","YELLOW","ALL")                   [(n&0x01c0)>>6]]
        d += [("3KEYS","6KEYS")                         [(n&0x0200)>>9]]
    elif 0x3c00 <= n < 0x4000:
        n -= 0x3c00
        d += ["DOOR"]
        d += [("W1","WR","S1","SR","G1","GR","P1","PR") [n&0x0007]]
        d += [("SLOW","NORMAL","FAST","TURBO")          [(n&0x0018)>>3]]
        d += [("OWC","OSO","CWO","CSC")                 [(n&0x0060)>>5]]
        d += [("MONSTER","")                            [(n&0x0080)>>7]]
        d += [("1SECS","4SECS","9SECS","30SECS")        [(n&0x0300)>>8]]
    elif 0x4000 <= n < 0x6000:
        n -= 0x4000
        d += ["CEIL"]
        d += [("W1","WR","S1","SR","G1","GR","P1","PR") [n&0x0007]]
        d += [("SLOW","NORMAL","FAST","TURBO")          [(n&0x0018)>>3]]
        d += [("TRIG","NUM")                            [(n&0x0020)>>5]]
        d += [("DOWN","UP")                             [(n&0x0040)>>6]]
        d += [("HNC","LNC","NNC","HNF","FLR",
               "SUT","24","32")                         [(n&0x0380)>>7]]
        d += [("","CPYTEX+DELTYPE","CPYTEX","CHGTYPE")  [(n&0x0c00)>>10]]
        d += [("CRUSH","")                              [(n&0x1000)>>12]]
    elif 0x6000 <= n < 0x8000:
        n -= 0x6000
        d += ["FLOOR"]
        d += [("W1","WR","S1","SR","G1","GR","P1","PR") [n&0x0007]]
        d += [("SLOW","NORMAL","FAST","TURBO")          [(n&0x0018)>>3]]
        d += [("TRIG","NUM")                            [(n&0x0020)>>5]]
        d += [("DOWN","UP")                             [(n&0x0040)>>6]]
        d += [("HNF","LNF","NNF","LNC","CL",
               "SLT","24","32")                         [(n&0x0380)>>7]]
        d += [("","CPYTEX+DELTYPE","CPYTEX","CHGTYPE")  [(n&0x0c00)>>10]]
        d += [("CRUSH","")                              [(n&0x1000)>>12]]
    # Bit of a hack, but works
    return (" ".join(d)).replace("  "," ").rstrip(" ")

def encode_std(desc):
    """Encode an exact description of a trigger into its corresponding number.
    For inexact descriptions, use find_std."""
    try:
        return desc2num[desc.upper()]
    except:
        raise Exception("Description not recognized")

def encode_gen(desc):
    """Encode a generalized (Boom) trigger description to a trigger
    number. Invalid or incompatible terms get converted to the default
    value."""
    desc = desc.upper()
    num = 0
    def pk(seq, shift):
        for i in range(len(seq)):
            if seq[i] in desc:
                return i << shift
        return 0
    num |= pk(("W1","WR","S1","SR","G1","GR","P1","PR"), 0)
    num |= pk(("SLOW","NORMAL","FAST","TURBO"), 3)
    if ("FLOOR" in desc) or ("CEIL" in desc):
        num |= pk(("TRIG","NUM"), 5)
        num |= pk(("DOWN","UP"), 6)
        num |= pk(("xx","CPYTEX+DELTYPE","CPYTEX","CHGTYPE"), 10)
        num |= pk(("CRUSH",), 12)
        if "FLOOR" in desc:
            num |= pk(("HNF","LNF","NNF","LNC","CL","SLT","24","32"), 7)
            num += 0x6000
        else:
            num |= pk(("HNC","LNC","NNC","HNF","FLR","SUT","24","32"), 7)
            num += 0x4000
    elif "CRUSHER" in desc:
        num |= pk(("MONSTER",), 5)
        num |= pk(("SILENT",), 6)
        num += 0x2F80
    elif "STAIR" in desc:
        num |= pk(("xx","MONSTER"), 5)
        num |= pk(("4","8","16","24"), 6)
        num |= pk(("DOWN","UP"), 8)
        num |= pk(("xx","IGNTXT"), 9)
        num += 0x3000
    elif "PLATFORM" in desc:
        num |= pk(("MONSTER",), 5)
        num |= pk(("1","3","5","10"), 6)
        num |= pk(("LNF","NNF","LNC","PERP"), 8)
        num += 0x3400
    elif "DOOR" in desc:
        num |= pk(("SLOW","NORMAL","FAST","TURBO"), 3)
        if ("BLU" in desc) or ("YEL" in desc) or ("RED" in desc) or\
           ("ALL" in desc) or ("ANY" in desc):
            num |= pk(("OWC","OSO"), 5)
            num |= pk(("ANY","RED","YELLOW","BLUE","RED","BLUE","YELLOW","ALL"), 6)
            num |= pk(("3KEYS","6KEYS"), 9)
            num += 0x3800
        else:
            num |= pk(("OWC","OSO","CWO","CSC"), 5)
            num |= pk(("MONSTER",), 7)
            num |= pk(("1SECS","4SECS","9SECS","30SECS"), 8)
            num += 0x3c00
    else:
        raise LookupError("Insufficient information provided")
    return num

def find_std(desc):
    """Search the standard (non-generalized) triggers. A list of
    matches is returned. All terms must match. Wildcards are allowed.
    Example:

       find_std("CEIL UP S?")        should return:

       ['CEIL S1 UP SLOW HNC', 'CEIL SR UP SLOW HNC']"""
    desc = desc.upper()
    terms = desc.split()
    matches = []
    for dsc in num2desc.values():
        d = dsc.split()
        matchedterms = 0
        for term in terms:
            for key in d:
                if fnmatchcase(key, term):
                    matchedterms += 1
        if matchedterms == len(terms):
            matches.append(dsc)
    return matches

__all__ = [find_std, encode_std, encode_gen, decode, check_compat]
