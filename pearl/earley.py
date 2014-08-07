from collections import namedtuple as _namedtuple
from itertools import chain as _chain
from collections import OrderedDict as _OrderedDict


class _Item(_namedtuple('_Item_', ['origin', 'symbol', 'sequence', 'progress', 'children'])):
    def __new__(cls, origin, symbol, sequence, progress=0, children=()):
        return super(_Item, cls).__new__(cls, origin, symbol, sequence, progress, children)

    @property
    def required_symbol(self):
        return self.sequence[self.progress] if self.progress < len(self.sequence) else None

    def step(self, *subchildren):
        return _Item(self.origin, self.symbol, self.sequence, self.progress + 1, self.children + (subchildren,))


class _State:
    def __init__(self, items=[]):
        self._items = _OrderedDict((item, None) for item in items)

    def __iter__(self):
        return iter(self._items)

    def add(self, item):
        self._items.setdefault(item, None)


class _Sentinel:
    def __init__(self):
        self.symbol = object()


def parse(grammar, tokens):
    start_item = _Item(0, object(), (grammar.start_symbol,))
    states = [_State([start_item])]
    for i, token in enumerate(_chain(tokens, [_Sentinel()])):
        states.append(_State())
        for item in states[i]:
            if item.required_symbol is None:
                for origin_item in states[item.origin]:
                    if origin_item.required_symbol == item.symbol:
                        states[i].add(origin_item.step(*grammar[item.symbol][item.sequence](*item.children)))
            elif item.required_symbol in grammar:
                if grammar[item.required_symbol].nullable:
                    states[i].add(item.step(*grammar[item.required_symbol][()]()))
                for sequence in grammar[item.required_symbol]:
                    states[i].add(_Item(i, item.required_symbol, sequence))
            elif item.required_symbol == token.symbol:
                states[i + 1].add(item.step(token))
    states.pop()
    for item in states[-1]:
        if item[:-1] == start_item.step()[:-1]:
            yield item.children[0]
