import re
from collections import namedtuple


Token = collections.namedtuple('Token', ['kind', 'value', 'index'])


class Tokenizer:
    def __init__(self, token_spec, string):
        regex = re.compile('|'.join('(?P<{}>{})'.format(*tkn) for tkn in token_spec))
        self.rep = regex.finditer(string)
        self.current_token = None

    def __iter__(self):
        return self

    def __next__(self):
        mo = next(self.rep)
        self.current_token = Token(mo.lastgroup, mo.group(mo.lastgroup), mo.start())
        return self.current_token
