from itertools import chain


class GrammarError(Exception):
    pass


def normalize_symbol(symbol):
    if isinstance(symbol, str):
        return symbol
    raise TypeError('str')


def normalize_production(production):
    if isinstance(production, tuple):
        return tuple(map(normalize_symbol, production))
    if isinstance(production, str):
        return (production,)
    raise TypeError('tuple, str')


def normalize_productions(productions):
    if isinstance(productions, set):
        return set(map(normalize_production, productions))
    if isinstance(productions, tuple):
        return {tuple(map(normalize_symbol, productions))}
    if isinstance(productions, str):
        return {(productions,)}
    raise TypeError('set, tuple, str')


def normalize_grammar(grammar):
    if isinstance(grammar, dict):
        return dict(zip(map(normalize_symbol, grammar.keys()), map(normalize_productions, grammar.values())))
    raise TypeError('dict')


def compute_nullables(grammar):
    def should_add(new_symbol, grammar, current_nullables):
        return any(all(symbol in current_nullables for symbol in production) for production in grammar[new_symbol])

    nullables = {symbol for symbol in grammar if () in grammar[symbol]}

    added = True
    while added:
        added = False
        for symbol in grammar:
            if not symbol in nullables and should_add(symbol, grammar, nullables):
                nullables.add(symbol)
                added = True

    return nullables


class Item:
    def __init__(self, base_state, non_terminal, body, progress):
        self.__base_state = base_state
        self.__non_terminal = non_terminal
        self.__body = body
        self.__progress = progress

    @property
    def base_state(self):
        return self.__base_state

    @property
    def non_terminal(self):
        return self.__non_terminal

    @property
    def body(self):
        return self.__body

    @property
    def progress(self):
        return self.__progress

    @property
    def expected_symbol(self):
        if self.progress == len(self.body):
            return None
        return self.body[self.progress]

    @property
    def next(self):
        if self.progress == len(self.body):
            return None
        return Item(self.base_state, self.non_terminal, self.body, self.progress + 1)

    @property
    def __key(self):
        return self.base_state, self.non_terminal, self.body, self.progress

    def __eq__(self, other):
        return isinstance(other, Item) and self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)

    def __repr__(self):
        return str(self.__key)


def parse(tokens, grammar, start=None, get_terminal=None):
    if start is None:
        start = 'start'

    if get_terminal is None:
        get_terminal = lambda x: x.terminal

    grammar = normalize_grammar(grammar)
    nullables = compute_nullables(grammar)

    start_item = Item(0, object(), (start,), 0)
    states = [[start_item]]
    for i, token in enumerate(chain(tokens, [object()])):
        states.append([])
        for item in states[i]:
            if item.expected_symbol is None:
                for base_item in states[item.base_state]:
                    if base_item.expected_symbol == item.non_terminal:
                        if base_item.next not in states[i]:
                            states[i].append(base_item.next)
            elif item.expected_symbol in grammar:
                if item.expected_symbol in nullables:
                    if item.next not in states[i]:
                        states[i].append(item.next)
                for body in grammar[item.expected_symbol]:
                    new_item = Item(i, item.expected_symbol, body, 0)
                    if new_item not in states[i]:
                        states[i].append(new_item)
            elif item.expected_symbol == get_terminal(token):
                if item.next not in states[i + 1]:
                    states[i + 1].append(item.next)
    return start_item.next in states[i]
