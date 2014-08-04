from itertools import chain as _chain
from collections import OrderedDict as _OrderedDict

class _Item:
    def __init__(self, origin, symbol, sequence, progress=0, children=()):
        self.origin = origin
        self.symbol = symbol
        self.sequence = sequence
        self.progress = progress
        self.children = children
        self.required_symbol = sequence[progress] if progress < len(sequence) else None

    def _key(self):
        return self.origin, self.symbol, self.sequence, self.progress

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._key() == other._key()

    def __hash__(self):
        return hash(self._key())

    def step(self, subchildren=()):
        return _Item(self.origin, self.symbol, self.sequence, self.progress + 1, self.children + (subchildren,))


class _State:
    def __init__(self, items=[]):
        self._items = _OrderedDict((item, None)for item in items)

    def __iter__(self):
        return iter(self._items)

    def add(self, item):
        self._items.setdefault(item, None)


def parse(grammar, tokens, token_symbol=None):
    if token_symbol is None:
        token_symbol = lambda token: token.symbol

    start_item = _Item(0, '', (grammar.start_symbol,))
    states = [_State([start_item])]
    for i, token in enumerate(_chain(tokens, [object()])):
        states.append(_State())
        for item in states[i]:
            if item.required_symbol is None:
                for origin_item in states[item.origin]:
                    if origin_item.required_symbol == item.symbol:
                        states[i].add(origin_item.step(grammar[item.symbol][item.sequence](item.children)))
            elif item.required_symbol in grammar:
                if grammar[item.required_symbol].nullable:
                    states[i].add(item.step())
                for sequence in grammar[item.required_symbol]:
                    states[i].add(_Item(i, item.required_symbol, sequence))
            elif item.required_symbol == token_symbol(token):
                states[i + 1].add(item.step((token,)))
            if item == start_item.step():
                yield item.children[0][0]
