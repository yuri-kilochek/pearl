from collections import defaultdict as _defaultdict
from collections import deque as _deque
from itertools import chain as _chain


class _GrammarMeta(type):
    def __getitem__(cls, rules):
        grammar = cls()

        if type(rules) == slice:
            rules = [rules]

        for rule in rules:
            assert type(rule) == slice

            assert type(rule.start) == str and rule.start
            head = rule.start

            assert type(rule.stop) == list
            body = []
            enabled_map = []
            for element in rule.stop:
                enabled = type(element) != set
                if enabled:
                    symbol = element
                else:
                    symbol = element.pop()
                assert type(symbol == str)
                body.append(symbol)
                enabled_map.append(enabled)

            def _build_fold(user_fold, enabled_map):
                def fold(*vss):
                    assert len(vss) == len(enabled_map)
                    vs = tuple(v for vs, e in zip(vss, enabled_map) if e for v in vs)
                    if user_fold is not None:
                        vs = user_fold(*vs),
                    return vs
                return fold
            assert rule.step is None or callable(rule.step)
            fold = _build_fold(rule.step, enabled_map)

            grammar.put(head, body, fold)

        return grammar


class Grammar(metaclass=_GrammarMeta):
    @staticmethod
    def default_fold(*vss):
        return tuple(v for vs in vss for v in vs)

    def __init__(self):
        self.__start = '__start__'
        self.__rule_sets = _defaultdict(dict)
        self.__nullable_set = None

    @property
    def start(self):
        return self.__start

    @start.setter
    def start(self, start):
        assert type(start) == str and start
        self.__start = start

    def __getitem__(self, head):
        assert type(head) == str and head
        for body, fold in self.__rule_sets[head].items():
            yield head, body, fold

    def is_terminal(self, symbol):
        assert type(symbol) == str and symbol
        return symbol not in self.__rule_sets or not self.__rule_sets[symbol]

    def put(self, head, body, fold=None):
        assert type(head) == str
        body = tuple(body)
        assert all(type(s) == str and s for s in body)
        if fold is None:
            fold = Grammar.default_fold
        assert callable(fold)
        self.__rule_sets[head][body] = fold
        self.__nullable_set = None

    def drop(self, head, body=None):
        assert type(head) == str and head
        if body is None:
            self.__rule_sets.pop(head, None)
        else:
            body = tuple(body)
            assert all(type(s) == str and s for s in body)
            self.__rule_sets[head].pop(body, None)
        self.__nullable_set = None

    def is_nullable(self, symbol):
        assert type(symbol) == str and symbol
        if self.__nullable_set is None:
            self.__nullable_set = set()
            while True:
                new_nullable = False
                for head, rule_set in self.__rule_sets.items():
                    if head in self.__nullable_set:
                        continue
                    if any(all(s in self.__nullable_set for s in b) for b, _ in rule_set.items()):
                        self.__nullable_set.add(head)
                        new_nullable = True
                if not new_nullable:
                    break
        return symbol in self.__nullable_set


class _Item:
    __slots__ = [
        '__dependents',
        '__rule',
        '__body_results'
    ]

    def __init__(self, dependents, rule, body_results=()):
        self.__dependents = dependents
        self.__rule = rule
        self.__body_results = body_results

    @property
    def __key(self):
        return id(self.__dependents), self.__rule, self.__body_results

    def __hash__(self):
        return hash(self.__key)

    def __eq__(self, other):
        return self.__key == other.__key

    @property
    def dependents(self):
        return self.__dependents

    @property
    def rule_head(self):
        return self.__rule[0]

    @property
    def rule_body(self):
        return self.__rule[1]

    @property
    def __rule_fold(self):
        return self.__rule[2]

    @property
    def is_complete(self):
        return len(self.__body_results) == len(self.rule_body)

    @property
    def expected_symbol(self):
        assert not self.is_complete
        return self.rule_body[len(self.__body_results)]

    def advance(self, child_result):
        assert not self.is_complete
        return _Item(self.__dependents, self.__rule, self.__body_results + (child_result,))

    def compute_result(self):
        assert self.is_complete
        return self.__rule_fold(*self.__body_results)


class _State:
    def __init__(self):
        self.__complete = set()
        self.__expecting = _defaultdict(set)
        self.__queue = _deque()

    def __bool__(self):
        return bool(self.__queue)

    def __iter__(self):
        while self.__queue:
            yield self.__queue.popleft()

    def __getitem__(self, symbol):
        return self.__expecting[symbol]

    def push(self, item):
        if item.is_complete:
            item_set = self.__complete
        else:
            item_set = self.__expecting[item.expected_symbol]
        queue = self.__queue
        if item in item_set:
            return
        item_set.add(item)
        queue.append(item)


class ParseError(Exception):
    pass


_END = object()


def _parse(grammar, tokens, **settings):
    match_token = settings.pop('match_token')
    allow_partial = settings.pop('allow_partial')

    assert not settings, 'Illegal settings: ' + ', '.join(settings)

    state = _State()

    for rule in grammar[grammar.start]:
        state.push(_Item(None, rule))

    for token in _chain(tokens, [_END]):
        next_state = _State()

        for item in state:
            if item.is_complete:
                item_result = item.compute_result()
                if item.dependents is None:
                    if allow_partial or token is _END:
                        yield item_result
                else:
                    for dependent_item in item.dependents:
                        state.push(dependent_item.advance(item_result))
            elif not grammar.is_terminal(item.expected_symbol):
                if grammar.is_nullable(item.expected_symbol):
                    state.push(item.advance(()))
                for rule in grammar[item.expected_symbol]:
                    state.push(_Item(state[item.expected_symbol], rule))
            elif token is not _END:
                token_result = match_token(token, item.expected_symbol)
                if token_result is None:
                    continue
                next_state.push(item.advance(tuple(token_result)))

        if not next_state and token is not _END:
            # TODO: error reporting goes here
            break

        state = next_state


def parse(grammar, tokens, **settings):
    settings.setdefault('match_token', lambda token, symbol: [token] if token == symbol else None)
    settings.setdefault('allow_partial', False)

    return _parse(grammar, tokens, **settings)
