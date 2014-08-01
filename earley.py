from itertools import chain


class GrammarError(Exception):
    pass


def compile_body_element(element):
    if isinstance(element, str):
        return element, True
    if isinstance(element, set):
        if len(element) == 0:
            raise GrammarError('Set must contain one string.')
        if len(element) > 1:
            raise GrammarError('Set must contain only one string.')
        element = next(iter(element))
        if not isinstance(element, str):
            raise GrammarError('Set element must be a string, instead got ' + type(element).__name__ + '.')
        return element, False
    if callable(element):
        raise GrammarError('Callable can only be last element of rule body.')
    raise GrammarError('Rule body element bust be a set, string or callable, instead got ' + type(element).__name__ +
                       '.')


def compile_rule_body(body):
    if not isinstance(body, (tuple, set, str)) and not callable(body):
        raise GrammarError('Rule body must be a tuple, set, string, or callable, instead got ' + type(body).__name__ +
                           '.')
    if not isinstance(body, tuple):
        body = body,

    body, combinator = (body[:-1], body[-1]) if len(body) > 0 and callable(body[-1]) else (body, None)
    body, selector = tuple(zip(*map(compile_body_element, body))) or ((), ())

    return body, selector, combinator


def compile_rule_group(non_terminal, body_group):
    if not isinstance(non_terminal, str):
        raise GrammarError('Grammar non-terminal must be a string, instead got ' + type(non_terminal).__name__ + '.')
    if not isinstance(body_group, (list, tuple, set, str)) and not callable(body_group):
        raise GrammarError('Rule body group must be a list, tuple, set, string, or callable, instead got ' +
                           type(body_group).__name__ + '.')

    if not isinstance(body_group, list):
        body_group = [body_group]

    body_group = {body: (selector, combinator) for body, selector, combinator in map(compile_rule_body, body_group)}

    return non_terminal, body_group


def compile_grammar(grammar):
    if not isinstance(grammar, dict):
        raise GrammarError('Grammar must be a dictionary, instead got ' + type(grammar).__name__ + '.')

    return dict(map(compile_rule_group, grammar.keys(), grammar.values()))


def build_nullable_tester(grammar):
    nullable_non_terminals = {non_terminal for non_terminal in grammar if () in grammar[non_terminal]}

    def is_nullable(symbol):
        return symbol in nullable_non_terminals

    def should_be_nullable(non_terminal):
        return any(all(element in nullable_non_terminals for element in body) for body in grammar[non_terminal])

    nullable_added = True
    while nullable_added:
        nullable_added = False
        for non_terminal in grammar:
            if not is_nullable(non_terminal) and should_be_nullable(non_terminal):
                nullable_non_terminals.add(non_terminal)
                nullable_added = True

    return is_nullable


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

    grammar = compile_grammar(grammar)
    is_nullable = build_nullable_tester(grammar)

    start_item = Item(0, None, (start,), 0)
    states = [[start_item]]
    for i, token in enumerate(chain(tokens, [None])):
        states.append([])
        for item in states[i]:
            if item.expected_symbol is None:
                for base_item in states[item.base_state]:
                    if base_item.expected_symbol == item.non_terminal and base_item.next not in states[i]:
                        states[i].append(base_item.next)
            elif item.expected_symbol in grammar:
                if is_nullable(item.expected_symbol):
                    if item.next not in states[i]:
                        states[i].append(item.next)
                for body in grammar[item.expected_symbol]:
                    new_item = Item(i, item.expected_symbol, body, 0)
                    if new_item not in states[i]:
                        states[i].append(new_item)
            elif item.expected_symbol == get_terminal(token):
                states[i + 1].append(item.next)
    return start_item.next in states[i]
