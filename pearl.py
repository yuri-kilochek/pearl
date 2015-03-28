from collections import defaultdict as _defaultdict
from itertools import chain as _chain


def default_transform(grammar, *results):
    return [grammar] + list(results)


class _Rule:
    def __init__(self, head, body, transform):
        self.__head = head
        self.__body = body
        self.__transform = transform

    @property
    def __key(self):
        return self.__head, self.__body

    def __hash__(self):
        return hash(self.__key)

    def __eq__(self, other):
        return self.__key == other.__key

    @property
    def head(self):
        return self.__head

    @property
    def body(self):
        return self.__body

    @property
    def transform(self):
        return self.__transform


class Grammar:
    def __init__(self, rules=()):
        self.__rule_groups = _defaultdict(dict)
        for rule in rules:
            assert type(rule) == _Rule
            self.__rule_groups[rule.head][rule.body] = rule
        self.__nullables = None

    def __getitem__(self, head):
        assert type(head) == str and head
        return self.__rule_groups[head].values()

    def put(self, head, body, transform=default_transform):
        assert type(head) == str
        assert type(body) == list and all(type(s) == str and s for s in body)
        assert callable(transform)
        old = (r for rg in self.__rule_groups.values() for r in rg.values())
        new = [_Rule(head, tuple(body), transform)]
        return Grammar(_chain(old, new))

    def is_terminal(self, symbol):
        assert type(symbol) == str and symbol
        return symbol not in self.__rule_groups or not self.__rule_groups[symbol]

    def is_nullable(self, symbol):
        assert type(symbol) == str and symbol

        if self.__nullables is None:
            self.__nullables = {s for s, rg in self.__rule_groups.items() if () in rg}
            new_nullable = self.__nullables
            while new_nullable:
                new_nullable = False
                for head, rule_group in self.__rule_groups.items():
                    if head in self.__nullables:
                        continue
                    if any(all(s in self.__nullables for s in b) for b in rule_group):
                        self.__nullables.add(head)
                        new_nullable = True

        return symbol in self.__nullables


class _Item:
    def __init__(self, grammar, rule, parents=frozenset(), results=(), progress=0):
        self.__grammar = grammar
        self.__rule = rule
        self.__parents = parents
        self.__results = results
        self.__progress = progress

    @property
    def __key(self):
        return id(self.__grammar), self.__rule, id(self.__parents), self.__results, self.__progress

    def __hash__(self):
        return hash(self.__key)

    def __eq__(self, other):
        return self.__key == other.__key

    @property
    def grammar(self):
        return self.__grammar

    @property
    def rule(self):
        return self.__rule

    @property
    def parents(self):
        return self.__parents

    @property
    def is_complete(self):
        return self.__progress == len(self.__rule.body)

    @property
    def expected_symbol(self):
        assert not self.is_complete
        return self.__rule.body[self.__progress]

    def get_next(self, grammar, results):
        assert not self.is_complete
        return _Item(grammar, self.__rule, self.__parents, self.__results + results, self.__progress + 1)

    def finalize(self):
        assert self.is_complete
        grammar, *results = self.__rule.transform(self.__grammar, *self.__results)
        return grammar, tuple(results)


class _State:
    def __init__(self):
        self.__complete = set()
        self.__expecting = _defaultdict(set)
        self.__order = []

    def __bool__(self):
        return bool(self.__order)

    def __iter__(self):
        i = 0
        while i < len(self.__order):
            yield self.__order[i]
            i += 1

    def __getitem__(self, expected_symbol):
        return self.__expecting[expected_symbol]

    def put(self, item):
        if item.is_complete:
            required_set = self.__complete
        else:
            required_set = self.__expecting[item.expected_symbol]
        if item in required_set:
            return
        required_set.add(item)
        self.__order.append(item)


class ParseError(Exception):
    pass


_END = object()


def _parse(grammar, tokens, **settings):
    match = settings.pop('match')
    allow_partial = settings.pop('allow_partial')

    assert not settings, 'Unknown settings: ' + ', '.join(settings)

    state = _State()

    for rule in grammar['__start__']:
        state.put(_Item(grammar, rule))

    for token in _chain(tokens, [_END]):
        next_state = _State()

        for item in state:
            if item.is_complete:
                grammar, results = item.finalize()
                if item.parents:
                    for parent_item in item.parents:
                        state.put(parent_item.get_next(grammar, results))
                else:
                    if allow_partial or token is _END:
                        yield results
            elif not item.grammar.is_terminal(item.expected_symbol):
                if item.grammar.is_nullable(item.expected_symbol):
                    state.put(item.get_next(item.grammar, ()))
                for rule in item.grammar[item.expected_symbol]:
                    state.put(_Item(item.grammar, rule, state[item.expected_symbol]))
            elif token is not _END:
                result = match(token, item.expected_symbol)
                if result is not None:
                    next_state.put(item.get_next(item.grammar, (result,)))

        if not next_state and token is not _END:
            raise ParseError()

        state = next_state


def parse(grammar, tokens, **settings):
    settings.setdefault('match', lambda token, terminal: token if token == terminal else None)
    settings.setdefault('allow_partial', False)

    return _parse(grammar, tokens, **settings)
