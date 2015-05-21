from collections import namedtuple as _namedtuple


class _CharacterToken(_namedtuple('_CharacterToken', ['symbol', 'position'])):
    @property
    def values(self):
        return [self.symbol]


def tokenize(text):
    line = 1
    column = 1
    for character in text:
        yield _CharacterToken(character, (line, column))
        if character == '\n':
            line += 1
            column = 1
        else:
            column += 1
