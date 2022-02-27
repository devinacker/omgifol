# Map thing types... this needs to be expanded


# Map descriptions to numbers and vice versa
all_desc2num = {}
all_num2desc = {}

class ThingCategory:
    def __init__(self, table):
        global all_desc2num
        global all_num2desc
        rev = dict([(b, a) for a, b in table.items()])
        all_desc2num.update(table)
        all_num2desc.update(rev)
        self.table = dict([(x, None) for x in table])
    def __contains__(self, item):
        global all_desc2num
        global all_num2desc
        if isinstance(item, str):
            return item in self.table
        elif isinstance(item, int):
            return all_num2desc[item] in self.table
        else:
            raise TypeError

monsters = ThingCategory({
  "zombie":3004,
  "sergeant":9,
  "commando":65,
  "imp":3001,
  "demon":3002,
  "spectre":58,
  "lost soul":3006,
  "cacodemon":3005,
  "hell knight":69,
  "baron of hell":3003,
  "revenant":66,
  "mancubus":67,
  "arachnotron":68,
  "pain elemental":71,
  "archvile":64,
  "cyberdemon":16,
  "spider mastermind":7,
  "ss guy":84,
  "spawn target":87,
  "spawn shooter":89,
  "romero head":88,
  "commander keen":72
})

weapons = ThingCategory({
  "shotgun":2001,
  "super shotgun":82,
  "chaingun":2002,
  "rocket launcher":2003,
  "plasma gun":2004,
  "chainsaw":2005,
  "bfg 9000":2006
})

ammo = ThingCategory({
  "ammo clip":2007,
  "ammo box":2048,
  "shells":2008,
  "shell box":2049,
  "rocket":2010,
  "rocket box":2046,
  "cell charge":2047,
  "cell pack":17,
  "backpack":8
})

powerups = ThingCategory({
  "stimpack":2011,
  "medikit":2012,
  "supercharge":2013,
  "health bonus":2014,
  "armor bonus":2015,
  "green armor":2018,
  "blue armor":2019,
  "invulnerability":2022,
  "berserk":2023,
  "invisibility":2024,
  "radiation suit":2025,
  "computer map":2026,
  "goggles":2048,
  "megasphere":83
})

keys = ThingCategory({
  "red keycard":13,
  "yellow keycard":6,
  "blue keycard":5,
  "red skull key":38,
  "yellow skull key":39,
  "blue skull key":40
})

starts = ThingCategory({
  "player 1 start":1,
  "player 2 start":2,
  "player 3 start":3,
  "player 4 start":4,
  "deathmatch start":11,
  "teleport destination":14
})

"""
doom2_only = ThingCategory([
  "super shotgun",
  "megasphere",
  "archvile",
  "chaingunner",
  "revenant",
  "mancubus",
  "arachnotron",
  "hell knight",
  "pain elemental",
  "ss guy",
  "spawn target",
  "spawn shooter",
  "romero head",
  "commander keen"
  "flaming barrel",
])
"""

corpses = ThingCategory({
  "gibs 1":10,
  "gibs 2":12,
  "dead marine":15,
  "dead zombie":18,
  "dead sergeant":19,
  "dead imp":20,
  "dead demon":21,
  "dead cacodemon":22,
  "dead lost soul":23,
  "pool of blood":24,
  "impaled human 1":25,
  "impaled human 2":26,
  "skull on pole":27,
  "five skulls":28,
  "skull pile":29,
  "hangman 1":49,
  "hangman 2":50,
  "hangman 3":51,
  "hangman 4":52,
  "hangman 5":53,
  "hangman 2 (passable)":59,
  "hangman 4 (passable)":60,
  "hangman 3 (passable)":61,
  "hangman 5 (passable)":62,
  "hangman 1 (passable)":63
})

decorations = ThingCategory({
  "green pillar":30,
  "short green pillar":31,
  "red pillar":32,
  "short red pillar":33,
  "candle":34,
  "candelabra":35,
  "green pillar with heart":36,
  "red pillar with skull":37,
  "eye":41,
  "skull rock":42,
  "gray tree":43,
  "blue torch":44,
  "green torch":45,
  "red torch":46,
  "scrub":47,
  "tech column":48,
  "brown tree":54,
  "short blue torch":55,
  "short green torch":56,
  "short red torch":57,
  "floor lamp":2028,
  "barrel":2035
})
