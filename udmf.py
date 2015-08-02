import re
from itertools import tee

class Symbol:
    eof = "EOF"
    identifier = 'IDENT'
    integer = 'INT'
    float = 'FLOAT'
    string = 'STRING'
    keyword = 'KEYWORD'
    oparen = 'OPAREN'
    cparen = 'CPAREN'
    equal = 'EQUAL'
    scolon = 'SCOLON'

class Lexer:
    textmap = open("textmap.lmp").read()
    textpos = 0

    re_identifier = re.compile(r'[A-Za-z_]+[A-Za-z0-9_]*')
    re_integer = re.compile(r'[+-]?[0-9]+[0-9]*|0[0-9]+|0x[0-9A-Fa-f]+')
    re_float = re.compile(r'[+-]?[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?')
    re_string = re.compile(r'"((?:[^"\\]|\\.)*)"')
    re_keyword = re.compile('[^{}();"\'\n\t ]+')

    def scan(self):
        token = ''

        while True:
            self.consume(token)

            if self.textpos > len(self.textmap):
                raise Exception("textpos off the end of the string")

            if self.textpos == len(self.textmap):
                break # Done

            # Check for literals
            token = self.literal('{')
            if token != False:
                yield (Symbol.oparen,)
                continue

            token = self.literal('}')
            if token != False:
                yield (Symbol.cparen,)
                continue

            token = self.literal('=')
            if token != False:
                yield (Symbol.equal,)
                continue

            token = self.literal(';')
            if token != False:
                yield (Symbol.scolon,)
                continue

            # Check for complex terminals

            # Unknown keywords.  If this is the longest match, we use
            # this instead of any of the below tokens.
            uktoken = self.ukeyword()

            # A number can be a float or an integer, so check for
            # floats first because doing things the opposite way can
            # result in a truncated float as an integer.
            token, value = self.float()
            if token != False:
                if uktoken == False or len(token) >= len(uktoken):
                    yield (Symbol.float, value)
                    continue

            token, value = self.integer()
            if token != False:
                if uktoken == False or len(token) >= len(uktoken):
                    yield (Symbol.integer, value)
                    continue

            # Quoted strings
            token, value = self.string()
            if token != False:
                yield (Symbol.string, value)
                continue

            # Idenfitiers
            token = self.identifier()
            if token != False:
                if uktoken == False or len(token) >= len(uktoken):
                    yield (Symbol.identifier, token)
                    continue

            # Unknown keyword, last resort
            if uktoken != False:
                token = uktoken
                yield (Symbol.keyword, token)
                continue

            raise Exception("invalid syntax")

        yield (Symbol.eof,)

    # Consume the string and skip ahead to the next symbol, ignoring
    # all whitespace and comments.
    def consume(self, string):
        self.textpos += len(string)
        while True:
            char = self.textmap[self.textpos:self.textpos + 1]

            # Skip whitespace.
            if char == ' ' or char == '\t' or char == '\r' or char == '\n':
                self.textpos += 1
                continue

            # Skip comments
            if char == '/':
                nextchar = self.textmap[self.textpos + 1:self.textpos + 2]
                if nextchar == '/':
                    found = self.textmap.find('\n', self.textpos)
                    self.textpos += found - self.textpos + 1
                    continue
                elif nextchar == '*':
                    found = self.textmap.find('*/', self.textpos)
                    self.textpos += found - self.textpos + 1
                    continue

            # We're at our next symbol.
            break

    ## Terminal Symbols ##

    def literal(self, char):
        if self.textmap[self.textpos:self.textpos + 1] == char:
            return char
        else:
            return False

    def keyword(self, string):
        if self.textmap[self.textpos:self.textpos + len(string)] == string:
            return string
        else:
            return False

    def ukeyword(self):
        match = self.re_keyword.match(self.textmap[self.textpos:])
        if match:
            return match.group(0)
        else:
            return False

    def identifier(self):
        match = self.re_identifier.match(self.textmap[self.textpos:])
        if match:
            return match.group(0)
        else:
            return False

    def integer(self):
        match = self.re_integer.match(self.textmap[self.textpos:])
        if match:
            return (match.group(0), int(match.group(0)))
        else:
            return (False, False)

    def float(self):
        match = self.re_float.match(self.textmap[self.textpos:])
        if match:
            return (match.group(0), float(match.group(0)))
        else:
            return (False, False)

    def string(self):
        match = self.re_string.match(self.textmap[self.textpos:])
        if match:
            return (match.group(0), match.group(1).replace('\\"', '"'))
        else:
            return (False, False)

class Parser:
    # Token generator
    tokens = None

    # Current token
    token = None

    def consume(self):
        self.token = next(self.tokens)

    ## Non-terminals ##

    def parse(self, tokens):
        self.tokens = tokens
        self.consume()

        self.global_expr_list()

    def global_expr_list(self):
        while True:
            self.global_expr()

            if self.token[0] == Symbol.identifier:
                continue
            elif self.token[0] == Symbol.eof:
                return
            else:
                raise Exception("expected identifier or EOF")

    def global_expr(self):
        # Look ahead one symbol and see if we have a valid block or
        # assignment_expr.
        self.tokens, lookahead = tee(self.tokens)
        looktoken = next(lookahead)
        if looktoken[0] == Symbol.oparen:
            self.block()
        elif looktoken[0] == Symbol.equal:
            self.assignment_expr()
        else:
            raise Exception('expected block or assignment expression')

    def block(self):
        if self.token[0] != Symbol.identifier:
            raise Exception('expected identifier')
        self.consume()

        if self.token[0] != Symbol.oparen:
            raise Exception('expected "{"')
        self.consume()

        self.expr_list()

        if self.token[0] != Symbol.cparen:
            raise Exception('expected "}"')
        self.consume()

    def expr_list(self):
        while True:
            self.assignment_expr()
            if self.token[0] == Symbol.identifier:
                continue
            else:
                return

    def assignment_expr(self):
        if self.token[0] != Symbol.identifier:
            raise Exception('expected identifier')
        self.consume()

        if self.token[0] != Symbol.equal:
            raise Exception('expected "="')
        self.consume()

        self.value()

        if self.token[0] != Symbol.scolon:
            raise Exception('expected ";"')
        self.consume()

    def value(self):
        if self.token[0] == Symbol.integer:
            self.consume()
            return

        if self.token[0] == Symbol.float:
            self.consume()
            return

        if self.token[0] == Symbol.string:
            self.consume()
            return

        if self.token[0] == Symbol.keyword:
            self.consume()
            return

        # An identifier is a subset of a keyword.
        if self.token[0] == Symbol.identifier:
            self.consume()
            return

        raise Exception("expected value")

lex = Lexer()
parser = Parser()
parser.parse(lex.scan())
