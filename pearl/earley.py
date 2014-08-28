from collections import namedtuple as _namedtuple
from itertools import chain as _chain
from collections import OrderedDict as _OrderedDict


class _Item(_namedtuple('_Item_', ['origin', 'tag', 'sequence', 'progress', 'value_groups'])):
    def __new__(cls, origin, tag, sequence, progress=0, value_groups=()):
        return super(_Item, cls).__new__(cls, origin, tag, sequence, progress, value_groups)

    @property
    def required_tag(self):
        if self.progress < len(self.sequence):
            return self.sequence[self.progress]
        return None

    def step(self, *value_group):
        return _Item(self.origin, self.tag, self.sequence, self.progress + 1, self.value_groups + (value_group,))


class _State:
    def __init__(self, items=[]):
        self._items = _OrderedDict((item, None) for item in items)

    def __iter__(self):
        return iter(self._items)

    def add(self, item):
        self._items.setdefault(item, None)


class _Sentinel:
    def __init__(self):
        self.tag = object()


def _transform(selector, fold, value_groups):
    value_groups = (value_group for value_group, selected in zip(value_groups, selector) if selected)
    values = (value for value_group in value_groups for value in value_group)
    if fold is not None:
        values = [fold(*values)]
    return tuple(values)


def parse(grammar, tokens):
    start_item = _Item(0, object(), (grammar.start_rule.tag,))
    states = [_State([start_item])]
    for i, token in enumerate(_chain(tokens, [_Sentinel()])):
        states.append(_State())
        for item in states[i]:
            if item.required_tag is None:
                for origin_item in states[item.origin]:
                    if origin_item.required_tag == item.tag:
                        body = grammar[item.tag][item.sequence]
                        states[i].add(origin_item.step(*_transform(body.selector, body.fold, item.value_groups)))
            elif item.required_tag in grammar:
                if grammar[item.required_tag].nullable:
                    states[i].add(item.step())
                for body in grammar[item.required_tag]:
                    states[i].add(_Item(i, item.required_tag, body.sequence))
            elif item.required_tag == token.tag:
                states[i + 1].add(item.step(token.value))
    states.pop()
    for item in states[-1]:
        if item[:-1] == start_item.step()[:-1]:
            yield list(item.value_groups[0])
