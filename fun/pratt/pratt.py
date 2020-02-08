"""Small but complete example of a Pratt recursive-descent parser for the following
grammar:

    start := expr

    expr := expr op expr | call | LPAREN expr RPAREN | MINUS expr | INT | SYMBOL
    call := SYMBOL LPAREN arglist? RPAREN
    op   := PLUS | ASTERISK | MINUS | SLASH

    arglist := (expr COMMA)* expr

with the usual precedence.


Version: January 2019
"""
from collections import namedtuple


def parse(text):
    return MiniParser(MiniLexer(text)).parse()


class MiniParser:
    """The parser for the expression mini-language.

    All match_* functions assume that self.lexer.tkn is set at the first token of the
    expression to be matched, and they all leave self.lexer.tkn at one token past the
    end of the matched expression.
    """

    def __init__(self, lexer):
        self.lexer = lexer

    def parse(self):
        tree = self.match_expr(PREC_LOWEST)
        self.expect(TOKEN_EOF)
        return tree

    def match_expr(self, prec):
        """Match an expression, assuming that self.lexer.tkn is set at the first token
        of the expression.

        On exit, self.lexer.tkn will be set to the first token of the next expression.
        """
        left = self.match_prefix()

        tkn = self.lexer.tkn
        while tkn.type in PREC_MAP and prec < PREC_MAP[tkn.type]:
            left = self.match_infix(left, PREC_MAP[tkn.type])
            tkn = self.lexer.tkn
        return left

    def match_prefix(self):
        """Match a non-infix expression."""
        tkn = self.lexer.tkn
        if tkn.type == TOKEN_INT:
            left = IntNode(int(tkn.value))
            self.lexer.next_token()
        elif tkn.type == TOKEN_SYMBOL:
            left = SymbolNode(tkn.value)
            self.lexer.next_token()
        elif tkn.type == TOKEN_LPAREN:
            self.lexer.next_token()
            left = self.match_expr(PREC_LOWEST)
            self.expect(TOKEN_RPAREN)
            self.lexer.next_token()
        elif tkn.type == TOKEN_MINUS:
            self.lexer.next_token()
            left = PrefixNode("-", self.match_expr(PREC_PREFIX))

        return left

    def match_infix(self, left, prec):
        """Match the right half of an infix expression."""
        tkn = self.lexer.tkn
        self.lexer.next_token()

        if tkn.type == TOKEN_LPAREN:
            arglist = self.match_arglist()
            self.expect(TOKEN_RPAREN)
            self.lexer.next_token()
            return CallNode(left, arglist)
        else:
            right = self.match_expr(prec)
            return InfixNode(tkn.value, left, right)

    def match_arglist(self):
        """Match the argument list of a call expression."""
        arglist = []
        while True:
            arg = self.match_expr(PREC_LOWEST)
            arglist.append(arg)

            if self.lexer.tkn.type == TOKEN_COMMA:
                self.lexer.next_token()
            else:
                break
        return arglist

    def expect(self, typ):
        """Raise an error if the lexer's current token is not of the given type."""
        if self.lexer.tkn.type != typ:
            if typ == TOKEN_EOF:
                raise SyntaxError("trailing input")
            elif self.lexer.tkn.type == TOKEN_EOF:
                raise SyntaxError("premature end of input")
            else:
                raise SyntaxError(
                    "unexpected token, line {0.line} col {0.col}".format(self.lexer.tkn)
                )


class IntNode(namedtuple("IntNode", ["value"])):
    def __str__(self):
        return str(self.value)


class SymbolNode(namedtuple("SymbolNode", ["value"])):
    def __str__(self):
        return self.value


class CallNode(namedtuple("CallNode", ["f", "arglist"])):
    def __str__(self):
        return "{}({})".format(wrap(self.f), ", ".join(map(str, self.arglist)))


class InfixNode(namedtuple("InfixNode", ["op", "left", "right"])):
    def __str__(self):
        return "{} {} {}".format(wrap(self.left), self.op, wrap(self.right))


class PrefixNode(namedtuple("PrefixNode", ["op", "arg"])):
    def __str__(self):
        return str(self.op) + wrap(self.arg)


class MiniLexer:
    """The lexer for the expression mini-language.

    The parser drives the lexical analysis by calling the next_token method.
    """

    def __init__(self, text):
        self.text = text
        self.position = 0
        self.column = 1
        self.line = 1
        # Set the current token.
        self.next_token()

    def next_token(self):
        self.skip_whitespace()

        if self.position >= len(self.text):
            self.set_token(TOKEN_EOF, 0)
        else:
            ch = self.text[self.position]
            if ch.isalpha() or ch == "_":
                length = self.read_symbol()
                self.set_token(TOKEN_SYMBOL, length)
            elif ch.isdigit():
                length = self.read_int()
                self.set_token(TOKEN_INT, length)
            elif ch == "(":
                self.set_token(TOKEN_LPAREN, 1)
            elif ch == ")":
                self.set_token(TOKEN_RPAREN, 1)
            elif ch == ",":
                self.set_token(TOKEN_COMMA, 1)
            elif ch == "+":
                self.set_token(TOKEN_PLUS, 1)
            elif ch == "*":
                self.set_token(TOKEN_ASTERISK, 1)
            elif ch == "-":
                self.set_token(TOKEN_MINUS, 1)
            elif ch == "/":
                self.set_token(TOKEN_SLASH, 1)
            else:
                self.set_token(TOKEN_UNKNOWN, 1)

        return self.tkn

    def skip_whitespace(self):
        while self.position < len(self.text) and self.text[self.position].isspace():
            self.next_char()

    def read_symbol(self):
        end = self.position + 1
        while end < len(self.text) and is_symbol_char(self.text[end]):
            end += 1
        return end - self.position

    def read_int(self):
        end = self.position + 1
        while end < len(self.text) and self.text[end].isdigit():
            end += 1
        return end - self.position

    def next_char(self):
        if self.text[self.position] == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    def set_token(self, typ, length):
        value = self.text[self.position:self.position+length]
        self.tkn = Token(typ, value, self.line, self.column)

        # We can't just do self.position += length because self.line and self.column
        # would no longer be accurate.
        for _ in range(length):
            self.next_char()


Token = namedtuple("Token", ["type", "value", "line", "column"])


TOKEN_INT      = "TOKEN_INT"
TOKEN_SYMBOL   = "TOKEN_SYMBOL"
TOKEN_LPAREN   = "TOKEN_LPAREN"
TOKEN_RPAREN   = "TOKEN_RPAREN"
TOKEN_COMMA    = "TOKEN_COMMA"
TOKEN_PLUS     = "TOKEN_PLUS"
TOKEN_ASTERISK = "TOKEN_ASTERISK"
TOKEN_MINUS    = "TOKEN_MINUS"
TOKEN_SLASH    = "TOKEN_SLASH"
TOKEN_EOF      = "TOKEN_EOF"
TOKEN_UNKNOWN  = "TOKEN_UNKNOWN"


PREC_LOWEST = 0
PREC_ADD_SUB = 1
PREC_MUL_DIV = 2
PREC_PREFIX = 3
PREC_CALL = 4

PREC_MAP = {
    TOKEN_PLUS:     PREC_ADD_SUB,
    TOKEN_MINUS:    PREC_ADD_SUB,
    TOKEN_ASTERISK: PREC_MUL_DIV,
    TOKEN_SLASH:    PREC_MUL_DIV,
    # The left parenthesis is the "infix operator" for function-call expressions.
    TOKEN_LPAREN:   PREC_CALL,
}


def wrap(node):
    """Stringify the parse tree node and wrap it in parentheses if it might be
    ambiguous.
    """
    if isinstance(node, (IntNode, CallNode, SymbolNode)):
        return str(node)
    else:
        return "(" + str(node) + ")"


def is_symbol_char(c):
    return c.isdigit() or c.isalpha() or c == "_"


assert str(parse("1+1")) == "1 + 1"
assert str(parse("1+2*3")) == "1 + (2 * 3)"
assert str(parse("1*2+3")) == "(1 * 2) + 3"
assert str(parse("(1+2)*3")) == "(1 + 2) * 3"
assert str(parse("f(1, 2, 3)")) == "f(1, 2, 3)"
assert str(parse("-f(1+2, 3)/4")) == "(-f(1 + 2, 3)) / 4"
print("Test suite passed!")
