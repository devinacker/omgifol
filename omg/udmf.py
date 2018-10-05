import re
from omg.mapedit import MapEditor, ZThing
from omg.wad import NameGroup
from omg.lump import Lump

class UBlock:
    @staticmethod
    def serialize(value):
        if isinstance(value, bool):
            return '{0}'.format(value).lower()
        if isinstance(value, (float, int)):
            return '{0}'.format(value)
        if isinstance(value, str):
            return '"{0}"'.format(re.sub(r'"', '\\"', re.sub(r'\\', '\\\\\\\\', value)))
        raise TypeError

    defaults = {}

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __getattr__(self, name):
        return self.__dict__.get(name, None)
    def __setattr__(self, name, value):
        self.__dict__[name] = value
    def __eq__(self, other):
        return isinstance(other, UBlock) and self.__dict__ == other.__dict__
    def to_textmap(self, fallback = None):
        out = '{\n'
        for key, value in self.__dict__.items():
            if value is None:
                continue
            if not isinstance(value, (float, int, bool, str)):
                if fallback:
                    value = fallback(value)
                else:
                    raise TypeError
            key = re.sub(r'^[0-9]', '_', re.sub(r'[^A-Za-z0-9_]', '_', key))
            if key in type(self).defaults and value == type(self).defaults[key]:
                continue
            if isinstance(value, bool) and not value:
                continue
            out += '{0}={1};\n'.format(key, UBlock.serialize(value))

        out += '}\n'
        return out

class UParser:
    IDENTIFIER_RE = r'[A-Za-z_]+[A-Za-z0-9_]*'
    INTEGER_RE = r'([+-]?[1-9]+[0-9]*)|(0[0-7]+)|(0x[0-9A-Fa-f]+)|(0)'
    FLOAT_RE = r'[+-]?[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?'
    QUOTED_STRING_RE = r'"([^"\\]*(\\.[^"\\]*)*)"'
    KEYWORD_RE = r'[^{}();"\'\n\t ]+'
    WHITESPACE_RE = r'(\s|(\n|^)//[^\n]+|/\*(\*(?!\/)|[^*])*\*/)+'
    def __init__(self, blocktypes):
        self.blocktypes = blocktypes
        self.src = None
        self.ptr = 0
        self.line = 1
        self.match = None

    def skip_ws(self):
        while True:
            ws = re.match(UParser.WHITESPACE_RE, self.src[self.ptr:])
            if ws:
                self.line += len([x for x in ws[0] if x == '\n'])
                self.ptr += ws.end()
            else:
                break

    def peek(self, expr):
        return re.match(expr, self.src[self.ptr:])

    def accept(self, expr):
        match = self.peek(expr)
        if match:
            self.match = match
            self.line += len([x for x in match[0] if x == '\n'])
            self.ptr += match.end()
            self.skip_ws()
        return match

    def expect(self, expr):
        match = self.accept(expr)
        if match:
            return match
        if self.ptr == len(self.src):
            got = 'EOF'
        else:
            got = re.search(UParser.WHITESPACE_RE, self.src[self.ptr:])
            if got:
                got = self.src[self.ptr:got.pos]
            else:
                got = self.src[self.ptr:]
        raise Exception('line {0}: expected {1} got {2}'.format(self.line, expr, got))

    def parse(self, src):
        self.src = src
        self.ptr = 0
        self.line = 1
        toplevel = {}
        blocks = {}
        self.skip_ws()
        while self.ptr < len(self.src):
            name = self.identifier().lower()
            if self.accept('='):
                value = self.value()
                self.expect(r';')
                toplevel[name] = value
            elif self.accept('{'):
                fields = self.expr_list()
                self.expect(r'}')
                blockclass = self.blocktypes.get(name, UBlock)
                group = blocks.setdefault(name, [])
                group.append(blockclass(**fields))
        return toplevel, blocks

    def expr_list(self):
        fields = {}
        while self.peek(UParser.IDENTIFIER_RE):
            key, value = self.assignment_expr()
            fields[key] = value
        return fields

    def assignment_expr(self):
        key = self.identifier().lower()
        self.expect(r'=')
        value = self.value()
        self.expect(r';')
        return key, value

    def identifier(self):
        self.expect(UParser.IDENTIFIER_RE)
        return self.match[0]

    def value(self):
        if self.accept(UParser.FLOAT_RE):
            return float(self.match[0])
        if self.accept(UParser.INTEGER_RE):
            if self.match[1]:
                return int(self.match[0], 10)
            if self.match[2]:
                return int(self.match[0], 8)
            if self.match[3]:
                return int(self.match[0], 16)
            if self.match[4]:
                return 0
        if self.accept(UParser.QUOTED_STRING_RE):
            return self.match[1]
        if self.accept(UParser.KEYWORD_RE):
            return self.match[0]
        raise Exception('expected integer, float, string, or bool')

class UVertex(UBlock):
    storage = 'vertexes'
    def __init__(self, x=0.0, y=0.0, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y

class USidedef(UBlock):
    storage = 'sidedefs'
    defaults = {'texturetop': '-', 'texturebottom': '-', 'texturemiddle': '-',
            'offsetx': 0, 'offsety': 0}
    def __init__(self, sector=None, **kwargs):
        super().__init__(**kwargs)
        self.sector = sector

class ULinedef(UBlock):
    storage = 'linedefs'
    defaults = {
            'special': 0, 'arg0': 0, 'arg1': 0, 'arg2': 0, 'arg3': 0, 'arg4': 0,
            'sideback': -1, 'id': -1}
    flags = {'_Base':[
        'blocking','blockmonsters','twosided',
        'dontpegtop','dontpegbottom','secret',
        'blocksound','dontdraw','mapped',]}
    flags['Doom'] = flags['_Base'] + ['passuse']
    flags['Heretic'] = flags['_Base']
    flags['Hexen'] = flags['_Base'] + [
            'repeatspecial',None,None,None,
            'monsteractivate','blockplayers','blockeverything']
    flags['Strife'] = flags['_Base']
    flags['ZDoom'] = flags['Hexen']
    flags['ZDoom'][14] = 'blockplayers'

    moreflags_hexen = [
            'zoneboundary','jumpover','blockfloaters',
            'clipmidtex','wrapmidtex','midtex3d',
            'checkswitchrange','firstsideonly']
    triggers_hexen = [
            'playeruse','monstercross','impact',
            'playerpush','missilecross','blocking']

    def __init__(self, v1=None, v2=None, sidefront=None, **kwargs):
        super().__init__(**kwargs)
        self.v1 = v1
        self.v2 = v2
        self.sidefront = sidefront

class USector(UBlock):
    storage = 'sectors'
    defaults = {
      'heightfloor': 0,
      'heightceiling': 0,
      'lightlevel': 160,
      'special': 0,
      'id': 0
      }
    def __init__(self, texturefloor='-', textureceiling='-', **kwargs):
        super().__init__(**kwargs)
        self.texturefloor = texturefloor
        self.textureceiling = textureceiling

class UThing(UBlock):
    storage = 'things'
    defaults = {
            'id': 0, 'height': 0, 'angle': 0,
            'special': 0, 'arg0': 0, 'arg1': 0, 'arg2': 0, 'arg3': 0, 'arg4': 0}
    flags = {'_Base':
            ['skill1,skill2','skill3','skill4,skill5']}
    flags['Doom'] = flags['_Base'] + [
            'ambush','!single','!dm','!coop','friend']
    flags['Heretic'] = flags['_Base'] + [
            'ambush','!single']
    flags['Hexen'] = flags['_Base'] + [
            'ambush','dormant',
            'class1','class2','class3',
            'single','coop','dm']
    flags['Strife'] = flags['_Base'] + [
            'standing','!single','ambush',
            'strifeally',None,'translucent','invisible']
    flags['ZDoom'] = flags['Hexen'] + [
            'translucent','invisible','strifeally','standing']

    def __init__(self, x=0.0, y=0.0, ednum=0, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.type = ednum

udmf_types = {
        'thing': UThing,
        'vertex': UVertex,
        'sidedef': USidedef,
        'linedef': ULinedef,
        'sector': USector}

udmf_namespaces = ['Doom', 'Heretic', 'Hexen', 'Strife', 'ZDoom']

class UMapEditor:

    def __init__(self, lumpgroup=None, namespace=None):
        self.vertexes = []
        self.sidedefs = []
        self.linedefs = []
        self.sectors = []
        self.things = []
        self.scripts = None
        self.behavior = None
        self.namespace = namespace

        if lumpgroup is not None:
            self.from_lump(lumpgroup, namespace)

    def from_lump(self, lumpgroup, namespace=None):
        if 'TEXTMAP' not in lumpgroup:
            self.from_oldformat(lumpgroup, namespace)
            return

        parser = UParser(udmf_types)
        toplevel, blocks = parser.parse(lumpgroup["TEXTMAP"].data.decode())
        for (t, cls) in udmf_types.items():
            setattr(self, cls.storage, blocks[t] if t in blocks else [])
            if namespace is not None:
                self.namespace = namespace
            elif 'namespace' in toplevel:
                self.namespace = toplevel['namespace']
            else:
                self.namespace = None

        if self.namespace in ('ZDoom', 'Hexen'):
            if 'BEHAVIOR' in lumpgroup:
                self.behavior = lumpgroup['BEHAVIOR']
            if 'SCRIPTS' in lumpgroup:
                self.scripts = lumpgroup['SCRIPTS']

    def from_oldformat(self, lumpgroup, namespace):
        m = MapEditor(lumpgroup)
        self.vertexes = []
        self.sidedefs = []
        self.linedefs = []
        self.sectors = []
        self.things = []
        self.namespace = namespace
        if namespace not in udmf_namespaces:
            namespace = udmf_namespaces[0]
        hexencompat = namespace in ('ZDoom', 'Hexen') and m.Thing == ZThing

        if hexencompat:
            if 'BEHAVIOR' in lumpgroup:
                self.behavior = lumpgroup['BEHAVIOR']
            if 'SCRIPTS' in lumpgroup:
                self.scripts = lumpgroup['SCRIPTS']

        for thing in m.things:
            block = UThing(float(thing.x), float(thing.y), thing.type)
            self.things.append(block)
            if hexencompat and thing.tid != 0:
                block.id = thing.tid
            if hexencompat and thing.height != 0:
                block.height = float(thing.height)
            if thing.angle != 0:
                block.angle = thing.angle

            for f in range(len(UThing.flags[namespace])):
                if not UThing.flags[namespace][f]:
                    continue
                for flag in UThing.flags[namespace][f].split(','):
                    check = flag[0] != '!'
                    setattr(block, flag, bool(thing.flags & (1 << f)) == check)

            if hexencompat and thing.action:
                block.special = thing.action
                for i in range(5):
                    key = 'arg{0}'.format(i)
                    setattr(block, key, getattr(thing, key))

        for linedef in m.linedefs:

            block = ULinedef(linedef.vx_a, linedef.vx_b, linedef.front)
            self.linedefs.append(block)

            if linedef.back != -1:
                block.sideback = linedef.back
            if not hexencompat and linedef.tag:
                block.id = block.arg0 = linedef.tag
            if hexencompat and linedef.action == 121:
                block.id = linedef.arg0 + linedef.arg4 * 256
            if hexencompat and linedef.action and linedef.action != 121:
                block.special = linedef.action
                for i in range(5):
                    key = 'arg{0}'.format(i)
                    setattr(block, key, getattr(linedef, key))

            for f in range(len(ULinedef.flags[namespace])):
                flag = ULinedef.flags[namespace][f]
                if flag:
                    setattr(block, flag, linedef.flags & (1 << f))
            if hexencompat:
                trigger = ((linedef.flags & 0x1c00) >> 10) - 1
                if trigger >= 0 and trigger < len(ULinedef.triggers_hexen):
                    setattr(block, ULinedef.triggers_hexen[trigger], True)
            if hexencompat and linedef.action == 121:
                for f in range(len(ULinedef.moreflags_hexen)):
                    setattr(block, ULinedef.moreflags_hexen[f], linedef.arg1 & (1 << f))

        for sidedef in m.sidedefs:

            block = USidedef(sidedef.sector)
            self.sidedefs.append(block)

            if sidedef.off_x != 0:
                block.offsetx = sidedef.off_x
            if sidedef.off_y != 0:
                block.offsety = sidedef.off_y
            if sidedef.tx_up != '-':
                block.texturetop = sidedef.tx_up
            if sidedef.tx_low != '-':
                block.texturebottom = sidedef.tx_low
            if sidedef.tx_mid != '-':
                block.texturemiddle = sidedef.tx_mid

        for vertex in m.vertexes:

            block = UVertex(float(vertex.x), float(vertex.y))
            self.vertexes.append(block)

        for sector in m.sectors:

            block = USector(sector.tx_floor, sector.tx_ceil)
            self.sectors.append(block)

            if sector.z_floor != 0:
                block.heightfloor = sector.z_floor
            if sector.z_ceil != 0:
                block.heightceiling = sector.z_ceil
            if sector.light != 160:
                block.lightlevel = sector.light
            if sector.type != 0:
                block.special = sector.type
            if sector.tag != 0:
                block.id = sector.tag

    def to_lumps(self):
        m = NameGroup()
        m['_HEADER'] = Lump()
        m['TEXTMAP'] = Lump(str.encode(self.to_textmap()))
        if self.behavior:
            m['BEHAVIOR'] = self.behavior
        if self.scripts:
            m['SCRIPTS'] = self.scripts
        m['ENDMAP'] = Lump()
        return m

    def to_textmap(self):
        fallback = lambda *args: self.serialize_field(*args)
        out = 'namespace="{0}";\n'.format(self.namespace)
        for thing in self.things:
            out += 'thing ' + thing.to_textmap(fallback)
        for vertex in self.vertexes:
            out += 'vertex ' + vertex.to_textmap(fallback)
        for sidedef in self.sidedefs:
            out += 'sidedef ' + sidedef.to_textmap(fallback)
        for linedef in self.linedefs:
            out += 'linedef ' + linedef.to_textmap(fallback)
        for sector in self.sectors:
            out += 'sector ' + sector.to_textmap(fallback)
        return out
    def serialize_field(self, value):
        if isinstance(value, UVertex):
            return self.vertexes.index(value)
        if isinstance(value, USidedef):
            return self.sidedefs.index(value)
        if isinstance(value, ULinedef):
            return self.linedefs.index(value)
        if isinstance(value, USector):
            return self.sectors.index(value)
        if isinstance(value, UThing):
            return self.things.index(value)
