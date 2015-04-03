from collections import defaultdict as _defaultdict
from itertools import chain as _chain
from functools import wraps as _wraps
from inspect import getfullargspec as _getfullargspec


class _GrammarMeta(type):
    def __getitem__(cls, rules):
        if type(rules) != tuple:
            rules = rules,
        grammar = cls()
        for rule in rules:
            assert type(rule) == slice
            grammar = grammar.put(rule.start, rule.stop, rule.step)
        return grammar


def default_action(*args):
    if not args:
        return None
    assert len(args) == 1
    return args[0]


class Grammar(metaclass=_GrammarMeta):
    class Rule:
        def __init__(self, head, body, action):
            assert type(head) == str and head
            self.__head = head

            assert type(body) == list
            _body = []
            retained = set()
            for i, element in enumerate(body):
                if type(element) == set:
                    element = element.pop()
                    retained.add(i)
                assert type(element) == str and element
                _body.append(element)
            self.__body = tuple(_body)
            retained = frozenset(retained)

            if action is None:
                action = default_action
            assert callable(action)
            def build_action():
                argspec = _getfullargspec(action)
                @_wraps(action)
                def raw_action(values, tokens, grammar):
                    args = [v for i, v in enumerate(values) if i in retained]
                    kwargs = {}
                    if '_tokens_' in argspec.kwonlyargs:
                        kwargs['_tokens_'] = tokens
                    if '_grammar_' in argspec.kwonlyargs:
                        kwargs['_grammar_'] = grammar
                    result = action(*args, **kwargs)
                    if '_grammar_' in argspec.kwonlyargs:
                        result, grammar = result
                    return result, grammar
                return raw_action
            self.__action = build_action()

        @property
        def head(self):
            return self.__head

        @property
        def body(self):
            return self.__body

        @property
        def action(self):
            return self.__action

    def __init__(self, rules=()):
        rule_sets = _defaultdict(set)
        for rule in rules:
            assert type(rule) == Grammar.Rule
            rule_sets[rule.head].add(rule)
        self.__rule_sets = {h: frozenset(rs) for h, rs in rule_sets.items()}

    def __getitem__(self, head):
        assert type(head) == str and head
        return self.__rule_sets.get(head, frozenset())

    def put(self, head, body, action=default_action):
        old = (r for rs in self.__rule_sets.values() for r in rs)
        new = [Grammar.Rule(head, body, action)]
        return Grammar(_chain(old, new))

    def drop(self, head):
        return Grammar(r for rs in self.__rule_sets.values() for r in rs if r.head != head)

    def is_terminal(self, symbol):
        assert type(symbol) == str and symbol
        return symbol not in self.__rule_sets


class _Item:
    def __init__(self, grammar, rule, parents=frozenset(), values=(), tokens=()):
        self.__grammar = grammar
        self.__rule = rule
        self.__parents = parents
        self.__values = values
        self.__tokens = tokens
        self.__output = None

    @property
    def __key(self):
        return self.__grammar, self.__rule, id(self.__parents), self.__values

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
        return len(self.__values) == len(self.__rule.body)

    @property
    def expected_symbol(self):
        assert not self.is_complete
        return self.__rule.body[len(self.__values)]

    def get_next(self, grammar, value, tokens):
        assert not self.is_complete
        return _Item(grammar, self.__rule, self.__parents, self.__values + (value,), self.__tokens + tokens)

    @property
    def output(self):
        assert self.is_complete
        if self.__output is None:
            result, grammar = self.__rule.action(self.__values, self.__tokens, self.__grammar)
            self.__output = result, self.__tokens, grammar
        return self.__output


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
            return False
        required_set.add(item)
        self.__order.append(item)
        return True


class ParseError(Exception):
    pass


_END = object()


def default_match(token, terminal):
    if token == terminal:
        return token
    return None


def parse(grammar, tokens, *, match=default_match, allow_partial=False):
    state = _State()

    for rule in grammar['_start_']:
        state.put(_Item(grammar, rule))

    for token in _chain(tokens, [_END]):
        next_state = _State()

        while True:
            new_items = False
            for item in state:
                if item.is_complete:
                    result, tokens, grammar = item.output
                    for parent_item in item.parents:
                        new_items |= state.put(parent_item.get_next(grammar, result, tokens))
                elif not item.grammar.is_terminal(item.expected_symbol):
                    for rule in item.grammar[item.expected_symbol]:
                        new_items |= state.put(_Item(item.grammar, rule, state[item.expected_symbol]))
            if not new_items:
                break

        for item in state:
            if item.is_complete:
                result, tokens, grammar = item.output
                if not item.parents and (allow_partial or token is _END):
                    yield result
            elif item.grammar.is_terminal(item.expected_symbol) and token is not _END:
                result = match(token, item.expected_symbol)
                if result is not None:
                    next_state.put(item.get_next(item.grammar, result, (token,)))

        if not next_state and token is not _END:
            raise ParseError()

        state = next_state
