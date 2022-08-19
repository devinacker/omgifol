import re
from omg.mapedit import MapEditor, Linedef
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
        self.__dict__.update(type(self).defaults)
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
            key = re.sub(r'^([0-9])', r'_\1', re.sub(r'[^A-Za-z0-9_]', '_', key))
            if key in type(self).defaults and value == type(self).defaults[key]:
                continue
            if isinstance(value, bool) and not value:
                continue
            out += '{0}={1};\n'.format(key, UBlock.serialize(value))

        out += '}\n'
        return out

class UParser:
   #IDENTIFIER_RE    = re.compile(rb'[A-Za-z_]+[A-Za-z0-9_]*')
    IDENTIFIER_RE    = re.compile(rb'[A-Za-z0-9_]+') # allow leading digits per UDMF 1.0 (will be changed upon saving)
    INTEGER_RE       = re.compile(rb'([+-]?[1-9]+[0-9]*)|(0[0-7]+)|(0x[0-9A-Fa-f]+)|(0)')
    FLOAT_RE         = re.compile(rb'[+-]?[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?')
    QUOTED_STRING_RE = re.compile(rb'"([^"\\]*(\\.[^"\\]*)*)"')
    KEYWORD_RE       = re.compile(rb'[^{}();"\'\n\t ]+')
    WHITESPACE_RE    = re.compile(rb'(\s|(\n|^)//[^\n]+|/\*(\*(?!\/)|[^*])*\*/)+')

    def __init__(self, blocktypes):
        self.blocktypes = blocktypes
        self.src = None
        self.ptr = 0
        self.line = 1
        self.match = None

    def skip_ws(self):
        while True:
            ws = UParser.WHITESPACE_RE.match(self.src[self.ptr:])
            if ws:
                self.line += len([x for x in ws[0] if chr(x) == '\n'])
                self.ptr += ws.end()
            else:
                break

    def peek(self, expr):
        if isinstance(expr, re.Pattern):
            return expr.match(self.src[self.ptr:])
        return re.match(expr, self.src[self.ptr:])

    def error_token(self):
        if self.ptr == len(self.src):
            return 'EOF'
        else:
            got = UParser.WHITESPACE_RE.search(self.src[self.ptr:])
            if got:
                got = self.src[self.ptr:self.ptr+got.start()]
            else:
                got = self.src[self.ptr:]
            return "'{0}'".format(got.tobytes().decode())

    def accept(self, expr):
        match = self.peek(expr)
        if match:
            self.match = match
            self.line += len([x for x in match[0] if chr(x) == '\n'])
            self.ptr += match.end()
            self.skip_ws()
        return match

    def expect(self, expr):
        match = self.accept(expr)
        if match:
            return match
        raise Exception("line {0}: expected '{1}', got {2}".format(self.line, expr.decode(), self.error_token()))

    def parse(self, src):
        self.src = memoryview(src)
        self.ptr = 0
        self.line = 1
        toplevel = {}
        blocks = {}
        self.skip_ws()
        while self.ptr < len(self.src):
            name = self.identifier().lower()
            if self.accept(b'='):
                value = self.value()
                self.expect(rb';')
                toplevel[name] = value
            elif self.accept(b'{'):
                fields = self.expr_list()
                self.expect(rb'}')
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
        self.expect(rb'=')
        value = self.value()
        self.expect(rb';')
        return key, value

    def identifier(self):
        if self.accept(UParser.IDENTIFIER_RE):
            return self.match[0].decode()
        raise Exception("line {0}: expected identifier, got {1}".format(self.line, self.error_token()))

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
            return self.match[1].decode()
        if self.accept(UParser.KEYWORD_RE):
            if not self.match[0] in (b'true', b'false'):
                raise Exception("line {0}: expected bool, got '{1}'".format(self.line, self.match[0].decode()))
            return self.match[0] == b'true'
        raise Exception("line {0}: expected integer, float, string, or bool, got {1}".format(self.line, self.error_token()))

class UVertex(UBlock):
    storage = 'vertexes'

    def __init__(self, x=0.0, y=0.0, **kwargs):
        self.x = x
        self.y = y
        super().__init__(**kwargs)

class USidedef(UBlock):
    storage = 'sidedefs'
    defaults = {'texturetop': '-', 'texturebottom': '-', 'texturemiddle': '-',
            'offsetx': 0, 'offsety': 0}

    def __init__(self, sector=None, **kwargs):
        self.sector = sector
        super().__init__(**kwargs)

class ULinedef(UBlock):
    storage = 'linedefs'
    defaults = {
            'special': 0, 'arg0': 0, 'arg1': 0, 'arg2': 0, 'arg3': 0, 'arg4': 0,
            'sideback': -1, 'id': -1}
    flags = {'_Base': [
            'blocking','blockmonsters','twosided',
            'dontpegtop','dontpegbottom','secret',
            'blocksound','dontdraw','mapped',]}
    flags['Doom'] = flags['_Base'] + ['passuse']
    flags['Heretic'] = flags['_Base']
    flags['Hexen'] = flags['_Base'] + [
            'repeatspecial',None,None,None,
            'monsteractivate',None,'blockeverything']
    flags['Strife'] = flags['_Base'] + [
            'jumpover','blockfloating',
            'translucent','transparent']
    flags['ZDoom'] = flags['Hexen']
    flags['ZDoom'][14] = 'blockplayers'
    flags['Eternity'] = flags['_Base'] + ['midtex3d']

    moreflags_hexen = [
            'zoneboundary','jumpover','blockfloaters',
            'clipmidtex','wrapmidtex','midtex3d',
            'checkswitchrange','firstsideonly']
    triggers_hexen = [
            'playercross','playeruse','monstercross','impact',
            'playerpush','missilecross','blocking']

    def __init__(self, v1=None, v2=None, sidefront=None, **kwargs):
        self.v1 = v1
        self.v2 = v2
        self.sidefront = sidefront
        super().__init__(**kwargs)

class USector(UBlock):
    storage = 'sectors'
    defaults = {
      'heightfloor': 0, 'heightceiling': 0,
      'lightlevel': 160, 'special': 0, 'id': 0}

    def __init__(self, texturefloor='-', textureceiling='-', **kwargs):
        self.texturefloor = texturefloor
        self.textureceiling = textureceiling
        super().__init__(**kwargs)

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
        self.x = x
        self.y = y
        self.type = ednum
        super().__init__(**kwargs)

udmf_types = {
        'thing': UThing,
        'vertex': UVertex,
        'sidedef': USidedef,
        'linedef': ULinedef,
        'sector': USector}

udmf_namespaces = ['Doom', 'Heretic', 'Hexen', 'Strife', 'ZDoom']

class UMapEditor:
    """UDMF map editor.

    Data members:
        vertexes      List containing UVertex objects
        sidedefs      List containing USidedef objects
        linedefs      List containing ULinedef objects
        sectors       List containing USector objects
        things        List containing UThing objects
        behavior      Lump object containing compiled ACS scripts
        scripts       Lump object containing ACS script source
        namespace     Map's UDMF namespace (see omg.udmf_namespaces for recognized values)
        """

    def __init__(self, lumpgroup=None, namespace=None):
        """Create new, optionally from a lump group.

        lumpgroup can be either a UDMF map or a classic Doom or ZDoom/Hexen map.
        Maps using the old format will be converted to UDMF automatically.

        If namespace is not specified, it will use the value stored in lumpgroup,
        if available."""
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
        """Load entries from a lump group.

        lumpgroup can be either a UDMF map or a classic Doom or ZDoom/Hexen map.
        Maps using the old format will be converted to UDMF automatically.

        If namespace is not specified, it will use the value stored in lumpgroup,
        if available."""
        if 'TEXTMAP' not in lumpgroup:
            self.from_oldformat(lumpgroup, namespace)
            return

        parser = UParser(udmf_types)
        toplevel, blocks = parser.parse(lumpgroup["TEXTMAP"].data)
        for (t, cls) in udmf_types.items():
            setattr(self, cls.storage, blocks[t] if t in blocks else [])
            if namespace is not None:
                self.namespace = namespace
            elif 'namespace' in toplevel:
                self.namespace = toplevel['namespace']
            else:
                self.namespace = None

        if 'BEHAVIOR' in lumpgroup:
            self.behavior = lumpgroup['BEHAVIOR']
        if 'SCRIPTS' in lumpgroup:
            self.scripts = lumpgroup['SCRIPTS']

    def from_oldformat(self, lumpgroup, namespace=None):
        """Import a classic format (Doom or ZDoom/Hexen) map.

        For ZDoom maps, deprecated line specials (such as Line_SetIdentification)
        will automatically be translated to the UDMF equivalent.

        If namespace is not specified, it will be given a default value based on
        the map's original format (vanilla or ZDoom/Hexen)."""
        m = MapEditor(lumpgroup)
        self.vertexes = []
        self.sidedefs = []
        self.linedefs = []
        self.sectors = []
        self.things = []
        self.namespace = namespace

        hexencompat = 'BEHAVIOR' in lumpgroup
        if namespace not in udmf_namespaces:
            namespace = 'ZDoom' if hexencompat else udmf_namespaces[0]
        if not self.namespace:
            self.namespace = namespace

        if hexencompat:
            try:
                self.behavior = m.behavior
                self.scripts = m.scripts
            except AttributeError:
                pass

        for thing in m.things:
            block = UThing(float(thing.x), float(thing.y), thing.type)
            self.things.append(block)

            if thing.angle != 0:
                block.angle = thing.angle

            for f in range(len(UThing.flags[namespace])):
                if not UThing.flags[namespace][f]:
                    continue
                for flag in UThing.flags[namespace][f].split(','):
                    if flag[0] != '!':
                        setattr(block, flag, bool(thing.flags & (1 << f)))
                    else:
                        setattr(block, flag[1:], not bool(thing.flags & (1 << f)))

            if hexencompat:
                block.id = thing.tid
                block.height = float(thing.height)
                block.special = thing.action
                for i in range(5):
                    key = 'arg{0}'.format(i)
                    setattr(block, key, getattr(thing, key))

        for linedef in m.linedefs:
            block = ULinedef(linedef.vx_a, linedef.vx_b, linedef.front)
            self.linedefs.append(block)

            if linedef.back != Linedef.NONE:
                block.sideback = linedef.back

            for f in range(len(ULinedef.flags[namespace])):
                flag = ULinedef.flags[namespace][f]
                if flag:
                    setattr(block, flag, bool(linedef.flags & (1 << f)))

            if hexencompat:
                if linedef.action == 121: # Line_SetIdentification
                    block.id = linedef.arg0 + linedef.arg4 * 256
                    for f in range(len(ULinedef.moreflags_hexen)):
                        setattr(block, ULinedef.moreflags_hexen[f], bool(linedef.arg1 & (1 << f)))
                elif linedef.action:
                    block.special = linedef.action
                    for i in range(5):
                        key = 'arg{0}'.format(i)
                        setattr(block, key, getattr(linedef, key))

                    trigger = ((linedef.flags & 0x1c00) >> 10)
                    if trigger < len(ULinedef.triggers_hexen):
                        setattr(block, ULinedef.triggers_hexen[trigger], True)

                    # handle line specials that set a line ID, extended flags, etc. based on the zdoom udmf spec
                    if linedef.action == 1: # Polyobj_StartLine
                        block.id = linedef.arg3
                        block.arg3 = 0
                    elif linedef.action == 5: # Polyobj_ExplicitLine
                        block.id = linedef.arg4
                        block.arg4 = 0
                    elif linedef.action == 160: # Sector_Set3dFloor
                        if linedef.arg1 & 8:
                            block.id = linedef.arg4
                            block.arg1 &= ~8
                        else:
                            block.arg0 += linedef.arg4 * 256
                        block.arg4 = 0
                    elif linedef.action == 181: # Plane_Align
                        block.id = linedef.arg2
                        block.arg2 = 0
                    elif linedef.action == 208: # TranslucentLine
                        block.id = linedef.arg0 # preserve arg0 according to spec
                        for f in range(len(ULinedef.moreflags_hexen)):
                            setattr(block, ULinedef.moreflags_hexen[f], bool(linedef.arg3 & (1 << f)))
                        block.arg3 = 0
                    elif linedef.action == 215: # Teleport_Line
                        block.id = linedef.arg0
                        block.arg0 = 0
                    elif linedef.action == 222: # Scroll_Texture_Model
                        block.id = linedef.arg0 # preserve arg0 according to spec
            else:
                block.special = linedef.action
                block.id = block.arg0 = linedef.tag

        for sidedef in m.sidedefs:
            block = USidedef(sidedef.sector)
            self.sidedefs.append(block)

            block.offsetx = sidedef.off_x
            block.offsety = sidedef.off_y
            block.texturetop = sidedef.tx_up
            block.texturebottom = sidedef.tx_low
            block.texturemiddle = sidedef.tx_mid

        for vertex in m.vertexes:
            block = UVertex(float(vertex.x), float(vertex.y))
            self.vertexes.append(block)

        for sector in m.sectors:
            block = USector(sector.tx_floor, sector.tx_ceil)
            self.sectors.append(block)

            block.heightfloor = sector.z_floor
            block.heightceiling = sector.z_ceil
            block.lightlevel = sector.light
            block.special = sector.type
            block.id = sector.tag

    def to_lumps(self):
        m = NameGroup()
        m['_HEADER_'] = Lump()
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
