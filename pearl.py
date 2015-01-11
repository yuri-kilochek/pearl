from collections import defaultdict as _defaultdict
from collections import deque as _deque
from itertools import chain as _chain


class _GrammarMeta(type):
    def __getitem__(cls, rules):
        def build_rules(rules):
            def build_rule(rule):
                def build_nonterminal(nonterminal):
                    assert type(nonterminal) == str and nonterminal
                    return nonterminal

                def build_body(elements):
                    assert type(elements) == list
                    body, discarded_elements = list(), set()
                    for i, element in enumerate(elements):
                        if type(element) == set:
                            assert len(element) == 1
                            element = element.pop()
                            discarded_elements.add(i)
                        assert type(element) == str and element
                        body.append(element)
                    return tuple(body), frozenset(discarded_elements)

                def build_tie(discarded_elements, user_tie):
                    def tie(*vss):
                        vs = (v for i, vs in enumerate(vss) if i not in discarded_elements for v in vs)
                        if user_tie is None:
                            return tuple(vs)
                        return user_tie(*vs),

                    assert user_tie is None or callable(user_tie)
                    return tie

                assert type(rule) == slice

                nonterminal = build_nonterminal(rule.start)
                body, discarded_elements = build_body(rule.stop)
                tie = build_tie(discarded_elements, rule.step)

                return nonterminal, body, tie

            if type(rules) != tuple:
                rules = [rules]

            for rule in rules:
                yield build_rule(rule)

        return cls(build_rules(rules))


def default_tie(*vss):
    return tuple(v for vs in vss for v in vs)


class Grammar(metaclass=_GrammarMeta):
    def __init__(self, rules=()):
        self.__rules = dict()
        for head, body, tie in rules:
            self.put(head, body, tie)
        self.__nullables = None

    def __getitem__(self, nonterminal):
        assert type(nonterminal) == str and nonterminal
        rule_group = self.__rules.get(nonterminal, dict())
        return rule_group.values()

    def put(self, nonterminal, body, tie=default_tie):
        assert type(nonterminal) == str
        assert type(body) == tuple and all(type(s) == str and s for s in body)
        assert callable(tie)
        rule_group = self.__rules.setdefault(nonterminal, dict())
        rule_group[body] = nonterminal, body, tie
        self.__nullables = None

    def drop(self, nonterminal, body=None):
        assert type(nonterminal) == str and nonterminal
        if nonterminal in self.__rules:
            if body is None:
                self.__rules.pop(nonterminal, None)
            else:
                assert type(body) == tuple and all(type(s) == str and s for s in body)
                rule_group = self.__rules[nonterminal]
                rule_group.pop(body, None)
                if not rule_group:
                    del self.__rules[nonterminal]
        self.__nullables = None

    def is_terminal(self, symbol):
        assert type(symbol) == str and symbol
        return symbol not in self.__rules

    def is_nullable(self, symbol):
        assert type(symbol) == str and symbol
        if self.__nullables is None:
            self.__nullables = set()
            while True:
                new_nullable = False
                for head, rule_group in self.__rules.items():
                    if head in self.__nullables:
                        continue
                    if any(all(s in self.__nullables for s in b) for b, _ in rule_group.items()):
                        self.__nullables.add(head)
                        new_nullable = True
                if not new_nullable:
                    break
        return symbol in self.__nullables


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

    for rule in grammar['__start__']:
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
